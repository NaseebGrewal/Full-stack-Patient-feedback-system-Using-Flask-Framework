"""
Professional FastAPI Application for Feedback Analysis

This application collects patient feedback, stores it in MongoDB and Redis,
and generates various charts (bar graphs and pie charts) for analysis.
"""

import json
import os
import re

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from db_clients import create_mongo_db_client, create_redis_client

# Configure matplotlib to use a backend suitable for environments without a display server.
matplotlib.use("agg")


# ----------------------------
# Database Client Initialization
# ----------------------------
def set_db_clients() -> tuple:
    """
    Initialize and return MongoDB and Redis clients.
    """
    username = os.getenv("USER_NAME")
    password = os.getenv("PASSWORD_MONGODB")
    MongoDB_Client = create_mongo_db_client(username, password)

    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT"))
    redis_password = None  # Update if a Redis password is required
    redis_client = create_redis_client(redis_host=redis_host, redis_port=redis_port, redis_password=redis_password)

    return MongoDB_Client, redis_client


MONGODB_CLIENT, redis_client = set_db_clients()
db = MONGODB_CLIENT["Naseeb"]
collection = db["Feedback"]

# ----------------------------
# FastAPI Application Setup
# ----------------------------
app = FastAPI()
# Use a secret key for session management. (The secret should be kept safe.)
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24).hex())

# Mount the "static" directory to serve images and other static files.
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ----------------------------
# Routes for Feedback Handling
# ----------------------------
@app.get("/feedback", response_class=HTMLResponse)
async def get_feedback(request: Request):
    """
    Render the feedback form.
    """
    return templates.TemplateResponse("feedback.html", {"request": request})


@app.post("/feedback")
async def post_feedback(request: Request):
    """
    Process submitted feedback. It stores the data in Redis and MongoDB.
    """
    form = await request.form()
    try:
        patient_id = int(form.get("patient_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid patient ID.")

    # Check session and MongoDB for duplicate submissions.
    if request.session.get("patient_id") or collection.find_one({"patient_id": patient_id}):
        return RedirectResponse(url="/feedback_error", status_code=status.HTTP_303_SEE_OTHER)

    # Mark submission in session.
    request.session["patient_id"] = patient_id

    # Retrieve additional feedback details.
    try:
        feedback_data = {
            "patient_id": patient_id,
            "name": form.get("name"),
            "age": int(form.get("age")),
            "email": form.get("email"),
            "date": form.get("date"),
            "overall_exp": int(form.get("overall_exp")),
            "doc_care": int(form.get("doc_care")),
            "doc_comm": int(form.get("doc_comm")),
            "nurse_care": int(form.get("nurse_care")),
            "food_quality": int(form.get("food_quality")),
            "accommodation": int(form.get("accommodation")),
            "sanitization": int(form.get("sanitization")),
            "safety": int(form.get("safety")),
            "staff_support": int(form.get("staff_support")),
            "doc_involvement": form.get("doc_involvement"),
            "nurse_promptness": form.get("nurse_promptness"),
            "cleanliness": form.get("cleanliness"),
            "timely_info": form.get("timely_info"),
            "med_info": form.get("med_info"),
            "other_comments": form.get("other_comments"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid form data: {e}")

    # Save data in Redis as a JSON string.
    data_json = json.dumps(feedback_data)
    redis_client.set(f"data:{feedback_data['patient_id']}", data_json)

    # Insert data into MongoDB.
    collection.insert_one(feedback_data)

    return RedirectResponse(url="/feedback_thankyou", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/feedback_thankyou", response_class=HTMLResponse)
async def feedback_thankyou(request: Request):
    """Render the thank-you page after successful submission."""
    return templates.TemplateResponse("feedback_thankyou.html", {"request": request})


@app.get("/feedback_error", response_class=HTMLResponse)
async def feedback_error(request: Request):
    """Render an error page if feedback has already been submitted."""
    return templates.TemplateResponse("feedback_error.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("home.html", {"request": request})


# ----------------------------
# Routes for Graph Generation
# ----------------------------
@app.get("/bargraphs", response_class=HTMLResponse)
async def bargraphs(request: Request):
    """
    Generate bar graphs for rating and yes/no responses and display them.
    """
    rating_cols = [
        "overall_exp",
        "doc_care",
        "doc_comm",
        "nurse_care",
        "food_quality",
        "accommodation",
        "sanitization",
        "safety",
        "staff_support",
    ]
    bargraph_paths = []

    def bar_graph_rating(col_name):
        ratings = collection.find({}, {"_id": 0, col_name: 1})
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for rating in ratings:
            star = rating.get(col_name)
            if star in counts:
                counts[star] += 1

        x_labels = ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"]
        y_values = [counts[1], counts[2], counts[3], counts[4], counts[5]]

        plt.figure()
        plt.bar(x_labels, y_values)
        for i, count in enumerate(y_values):
            plt.text(i, count, str(count), ha="center", va="bottom")
        plt.title(col_name)
        plt.xlabel("Rating")
        plt.ylabel("Number of Patients")

        if not os.path.exists("static"):
            os.makedirs("static")
        image_path = f"static/bar_graph_{col_name}.png"
        plt.savefig(image_path)
        plt.close()
        return sum(y_values), image_path

    total_ratings = 0
    # Generate bar graphs for each rating column.
    for col in rating_cols:
        count, path = bar_graph_rating(col)
        total_ratings += count
        bargraph_paths.append(path)

    # Generate a stacked bar graph for yes/no responses.
    yes_no_paths = []

    def bar_graph_yes_no():
        yes_no_cols = ["doc_involvement", "nurse_promptness", "cleanliness", "timely_info", "med_info"]
        counts_yes = [0] * len(yes_no_cols)
        counts_no = [0] * len(yes_no_cols)

        for doc in collection.find():
            for i, col in enumerate(yes_no_cols):
                if doc.get(col) == "yes":
                    counts_yes[i] += 1
                elif doc.get(col) == "no":
                    counts_no[i] += 1

        plt.figure()
        x_indices = range(len(yes_no_cols))
        plt.bar(x_indices, counts_yes, label="Yes")
        plt.bar(x_indices, counts_no, bottom=counts_yes, label="No")
        for i, count in enumerate(counts_yes):
            plt.text(i, count, str(count), ha="center", va="bottom")
        for i, count in enumerate(counts_no):
            plt.text(i, count + counts_yes[i], str(count), ha="center", va="bottom")
        plt.title("Responses to Yes/No Questions")
        plt.xlabel("Question")
        plt.ylabel("Count")
        plt.xticks(x_indices, yes_no_cols)
        plt.legend()
        plt.gcf().set_size_inches(15, 8)

        if not os.path.exists("static"):
            os.makedirs("static")
        image_path = "static/bar_graph_yes_no.png"
        plt.savefig(image_path, dpi=100, bbox_inches="tight")
        plt.close()
        yes_no_paths.append(image_path)

    bar_graph_yes_no()

    title = f"Bar Graph Analysis (Total Ratings = {total_ratings})"
    # Pass the first few image paths for demonstration.
    context = {
        "request": request,
        "title": title,
        "bargraphs": bargraph_paths,
        "yes_no": yes_no_paths[0] if yes_no_paths else "",
    }
    return templates.TemplateResponse("bargraph.html", context)


@app.get("/piecharts", response_class=HTMLResponse)
async def piecharts(request: Request):
    """
    Generate pie charts for rating and yes/no responses and display them.
    """
    rating_cols = [
        "overall_exp",
        "doc_care",
        "doc_comm",
        "nurse_care",
        "food_quality",
        "accommodation",
        "sanitization",
        "safety",
        "staff_support",
    ]
    piechart_paths = []

    def piechart_rating(col_name):
        one_star = collection.count_documents({col_name: 1})
        two_star = collection.count_documents({col_name: 2})
        three_star = collection.count_documents({col_name: 3})
        four_star = collection.count_documents({col_name: 4})
        five_star = collection.count_documents({col_name: 5})
        total = one_star + two_star + three_star + four_star + five_star

        labels = ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"]
        sizes = [one_star, two_star, three_star, four_star, five_star]
        plt.figure()
        patches, _ = plt.pie(sizes, startangle=90)
        plt.axis("equal")
        plt.title(f"{col_name} Rating")
        percentages = [f"{size} ({size / total * 100:.1f}%)" if total > 0 else "0" for size in sizes]
        legend_labels = [f"{label}\n{perc}" for label, perc in zip(labels, percentages)]
        plt.legend(patches, legend_labels, title="Star Ratings")

        if not os.path.exists("static"):
            os.makedirs("static")
        image_path = f"static/piechart_{col_name}.png"
        plt.savefig(image_path)
        plt.close()
        piechart_paths.append(image_path)
        return total

    yes_no_paths = []

    def piechart_yes_no():
        def count_yes_no(question):
            yes_count = collection.count_documents({question: "yes"})
            no_count = collection.count_documents({question: "no"})
            return yes_count, no_count

        def plot_pie(question):
            yes_count, no_count = count_yes_no(question)
            total_count = yes_count + no_count if (yes_count + no_count) > 0 else 1
            labels = ["Yes", "No"]
            values = [yes_count, no_count]
            percentages = [f"{count} ({count / total_count * 100:.1f}%)" for count in values]
            plt.figure()
            patches, _ = plt.pie(values, startangle=90)
            plt.axis("equal")
            plt.title(question)
            legend_labels = [f"{label}\n{perc}" for label, perc in zip(labels, percentages)]
            plt.legend(patches, legend_labels)
            if not os.path.exists("static"):
                os.makedirs("static")
            image_path = f"static/piechart_yes_no_{question}.png"
            plt.savefig(image_path)
            plt.close()
            yes_no_paths.append(image_path)

        questions = ["doc_involvement", "nurse_promptness", "cleanliness", "timely_info", "med_info"]
        for question in questions:
            plot_pie(question)

    total_ratings = 0
    count_val = 0
    for col in rating_cols:
        total_ratings += piechart_rating(col)
        count_val += 1
    piechart_yes_no()
    average_ratings = total_ratings // count_val if count_val else 0

    title = f"Pie Chart Analysis (Average Total Ratings = {average_ratings})"
    context = {
        "request": request,
        "title": title,
        "piecharts": piechart_paths,
        "yes_no": yes_no_paths,
    }
    return templates.TemplateResponse("piechart.html", context)


@app.get("/overall_bargraphs", response_class=HTMLResponse)
async def overall_bargraphs(request: Request):
    """
    Generate overall bar graphs combining star ratings and yes/no responses.
    """

    def save_bar_graphs_():
        star_ratings = [1, 2, 3, 4, 5]
        rating_cols = [
            "overall_exp",
            "doc_care",
            "doc_comm",
            "nurse_care",
            "food_quality",
            "accommodation",
            "sanitization",
            "safety",
            "staff_support",
        ]
        yes_no_cols = ["doc_involvement", "nurse_promptness", "cleanliness", "timely_info", "med_info"]

        ratings_counts = [[] for _ in range(len(star_ratings))]
        yes_no_counts = [[], []]
        x_labels = []

        for col in rating_cols:
            for i, star in enumerate(star_ratings):
                count = collection.count_documents({col: star})
                ratings_counts[i].append(count)
            x_labels.append(col)

        for col in yes_no_cols:
            yes_count = collection.count_documents({col: "yes"})
            no_count = collection.count_documents({col: "no"})
            yes_no_counts[0].append(yes_count)
            yes_no_counts[1].append(no_count)
            x_labels.append(f"{col} (Yes/No)")

        sorted_counts = []
        sorted_labels = []
        for i in range(len(star_ratings)):
            indices = np.argsort(ratings_counts[i])[::-1]
            sorted_counts.append([ratings_counts[i][j] for j in indices])
            sorted_labels.append([x_labels[j] for j in indices])

        yes_indices = np.argsort(yes_no_counts[0])[::-1]
        no_indices = np.argsort(yes_no_counts[1])[::-1]
        sorted_counts.append([yes_no_counts[0][j] for j in yes_indices])
        sorted_counts.append([yes_no_counts[1][j] for j in no_indices])
        sorted_labels.append([x_labels[j] for j in yes_indices])
        sorted_labels.append([x_labels[j] for j in no_indices])

        image_paths = []
        # Create bar graphs for star ratings.
        for i, star in enumerate(star_ratings):
            plt.figure(figsize=(10, 6))
            bars = plt.bar(range(len(sorted_counts[i])), sorted_counts[i])
            plt.xlabel("Column")
            plt.ylabel("Count")
            plt.title(f"Count of {star}-Star Ratings by Column")
            plt.xticks(range(len(sorted_counts[i])), sorted_labels[i], rotation="vertical")
            plt.tight_layout()
            for bar in bars:
                plt.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height(), int(bar.get_height()), ha="center", va="bottom"
                )
            if not os.path.exists("static"):
                os.makedirs("static")
            image_path = f"static/bargraph_{star}_star_ratings.png"
            plt.savefig(image_path)
            plt.close()
            image_paths.append(image_path)

        # Create bar graphs for yes/no responses.
        for i in range(2):
            plt.figure(figsize=(10, 6))
            bars = plt.bar(range(len(sorted_counts[i + len(star_ratings)])), sorted_counts[i + len(star_ratings)])
            plt.xlabel("Column")
            plt.ylabel("Count")
            plt.title("Count of Yes/No Responses by Column")
            plt.xticks(
                range(len(sorted_counts[i + len(star_ratings)])),
                sorted_labels[i + len(star_ratings)],
                rotation="vertical",
            )
            plt.tight_layout()
            for bar in bars:
                plt.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height(), int(bar.get_height()), ha="center", va="bottom"
                )
            path_img = "static/bargraph_yes_responses.png" if i == 0 else "static/bargraph_no_responses.png"
            plt.savefig(path_img)
            plt.close()
            image_paths.append(path_img)

        return image_paths

    title = "Overall Bar Graph Analysis"
    image_paths = save_bar_graphs_()
    context = {
        "request": request,
        "title": title,
        "bargraphs": image_paths,
    }
    return templates.TemplateResponse("overall_bargraph.html", context)


# ----------------------------
# Routes for Data Management
# ----------------------------
@app.get("/manage", response_class=HTMLResponse)
async def manage_get(request: Request):
    """
    Render the management page for administrative operations.
    """
    return templates.TemplateResponse("home_manage.html", {"request": request})


@app.post("/manage", response_class=HTMLResponse)
async def manage_post(request: Request):
    """
    Process management form submissions for showing, updating, or deleting entries.
    """
    form = await request.form()
    if "show" in form:
        entries = retrieve_entries(form)
        search_criteria = get_search_criteria(form)
        return templates.TemplateResponse(
            "manage.html", {"request": request, "search_criteria": search_criteria, "entries": entries}
        )
    elif "update" in form:
        if not any(form.values()):
            message = "Invalid operation: Nothing to update."
            return templates.TemplateResponse("manage.html", {"request": request, "message": message})
        try:
            patient_id = int(form.get("patient_id"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid patient ID.")
        new_data = {
            "name": form.get("name"),
            "age": form.get("age"),
            "email": form.get("email"),
            # Add additional fields if needed.
        }
        updated_count = update_entry(patient_id, new_data)
        message = (
            f"Entry with Patient ID {patient_id} successfully updated."
            if updated_count == 1
            else f"Failed to update entry with Patient ID {patient_id}."
        )
        return templates.TemplateResponse("manage.html", {"request": request, "message": message})
    elif "delete" in form:
        if not any(form.values()):
            message = "Invalid operation: Nothing to delete."
            return templates.TemplateResponse("manage.html", {"request": request, "message": message})
        try:
            patient_id = int(form.get("patient_id"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid patient ID.")
        deleted_count = delete_entry(patient_id)
        message = (
            f"Entry with Patient ID {patient_id} successfully deleted."
            if deleted_count == 1
            else f"Failed to delete entry with Patient ID {patient_id}."
        )
        return templates.TemplateResponse("manage.html", {"request": request, "message": message})
    else:
        return templates.TemplateResponse("manage.html", {"request": request})


def get_search_criteria(form_data) -> str:
    """
    Construct a search criteria string from form data.
    """
    search_criteria = []
    for field, value in form_data.items():
        if value and field != "show":
            search_criteria.append(f"{field}: {value}")
    return " and ".join(search_criteria)


def retrieve_entries(form_data):
    """
    Retrieve database entries based on form input criteria.
    """
    query = {}
    for field, value in form_data.items():
        if value:
            if field in ["patient_id", "age"]:
                query[field] = int(value)
            elif field == "name":
                query[field] = re.compile(re.escape(value), re.IGNORECASE)
            else:
                query[field] = value
    entries = collection.find(query)
    return list(entries)


def update_entry(patient_id, new_data) -> int:
    """
    Update an entry in the database.
    """
    existing_data = collection.find_one({"patient_id": patient_id})
    for key, value in new_data.items():
        if value:
            existing_data[key] = value
    result = collection.update_one({"patient_id": patient_id}, {"$set": existing_data})
    return result.modified_count


def delete_entry(patient_id) -> int:
    """
    Delete an entry from the database.
    """
    result = collection.delete_one({"patient_id": patient_id})
    return result.deleted_count


# if __name__ == "__main__":
#     # Run the FastAPI application in debug mode on port 5002.
#     uvicorn.run(app, host="0.0.0.0", port=5002, reload=True)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=5002, reload=True)

# from asgiref.wsgi import WsgiToAsgi
# from app import app  # your Flask app instance

# asgi_app = WsgiToAsgi(app)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:asgi_app", host="0.0.0.0", port=5002, reload=True)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=5002, reload=True)
