"""
Professional Flask Application for Feedback Analysis

This application collects patient feedback, stores it in MongoDB and Redis,
and generates various charts (bar graphs and pie charts) for analysis.
"""

import json
import os
import re

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, redirect, render_template, request, session, url_for

from db_clients import create_mongo_db_client, create_redis_client

# Configure matplotlib to use a backend suitable for environments without a display server.
matplotlib.use("agg")


def set_db_clients() -> tuple:
    """
    Initialize and return MongoDB and Redis clients.

    Returns:
        tuple: (MongoDB_Client, redis_client)
    """
    # Retrieve MongoDB credentials from environment variables
    username = os.getenv("USER_NAME")
    password = os.getenv("PASSWORD_MONGODB")
    MongoDB_Client = create_mongo_db_client(username, password)

    # Retrieve Redis configuration from environment variables (with defaults)
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = None  # Update if a Redis password is required
    redis_client = create_redis_client(redis_host=redis_host, redis_port=redis_port, redis_password=redis_password)

    return MongoDB_Client, redis_client


# Initialize database clients
MONGODB_CLIENT, redis_client = set_db_clients()

# Select the MongoDB database and collection
db = MONGODB_CLIENT["Naseeb"]
collection = db["Feedback"]

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management


# ----------------------------
# Routes for Feedback Handling
# ----------------------------
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    """
    Render the feedback form and process submissions.
    Stores feedback data in both Redis and MongoDB.
    """
    if request.method == "POST":
        # Retrieve and process form data
        patient_id = int(request.form["patient_id"])

        # Prevent duplicate submissions by checking session and database
        if "patient_id" in session or collection.find_one({"patient_id": patient_id}):
            return redirect(url_for("feedback_error"))

        # Store patient_id in session to mark submission
        session["patient_id"] = patient_id

        # Extract additional feedback details from the form
        name = request.form["name"]
        age = int(request.form["age"])
        email = request.form["email"]
        date = request.form["date"]

        overall_exp = int(request.form["overall_exp"])
        doc_care = int(request.form["doc_care"])
        doc_comm = int(request.form["doc_comm"])
        nurse_care = int(request.form["nurse_care"])
        food_quality = int(request.form["food_quality"])
        accommodation = int(request.form["accommodation"])
        sanitization = int(request.form["sanitization"])
        safety = int(request.form["safety"])
        staff_support = int(request.form["staff_support"])
        doc_involvement = request.form["doc_involvement"]
        nurse_promptness = request.form["nurse_promptness"]
        cleanliness = request.form["cleanliness"]
        timely_info = request.form["timely_info"]
        med_info = request.form["med_info"]
        other_comments = request.form["other_comments"]

        # Build a dictionary with the feedback data
        feedback_data = {
            "patient_id": patient_id,
            "name": name,
            "age": age,
            "email": email,
            "date": date,
            "overall_exp": overall_exp,
            "doc_care": doc_care,
            "doc_comm": doc_comm,
            "nurse_care": nurse_care,
            "food_quality": food_quality,
            "accommodation": accommodation,
            "sanitization": sanitization,
            "safety": safety,
            "staff_support": staff_support,
            "doc_involvement": doc_involvement,
            "nurse_promptness": nurse_promptness,
            "cleanliness": cleanliness,
            "timely_info": timely_info,
            "med_info": med_info,
            "other_comments": other_comments,
        }

        # Save data in Redis (as a JSON string)
        data_json = json.dumps(feedback_data)
        redis_client.set(f"data:{feedback_data['patient_id']}", data_json)

        # Insert data into MongoDB
        collection.insert_one(feedback_data)

        return redirect(url_for("feedback_thankyou"))
    else:
        return render_template("feedback.html")


@app.route("/feedback-thankyou")
def feedback_thankyou():
    """Render the thank-you page after successful feedback submission."""
    return render_template("feedback_thankyou.html")


@app.route("/feedback_error")
def feedback_error():
    """Render an error page if feedback has already been submitted."""
    return render_template("feedback_error.html")


@app.route("/")
def home():
    """Render the home page."""
    return render_template("home.html")


# ----------------------------
# Routes for Graph Generation
# ----------------------------
@app.route("/bargraphs", methods=["GET", "POST"])
def bargraphs():
    """
    Generate bar graphs for rating and yes/no responses.
    Returns a page displaying the generated graphs.
    """
    # Define rating columns for star ratings
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
    # Container to store paths for generated bar graph images
    bargraph_paths = ["Not a String"]

    def bar_graph_rating(col_name):
        """
        Generate a bar graph for a specific rating column.
        Returns the total number of ratings.
        """
        ratings = collection.find({}, {"_id": 0, col_name: 1})
        # Initialize star counters
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for rating in ratings:
            star = rating.get(col_name)
            if star in counts:
                counts[star] += 1

        # Bar graph data
        x_labels = ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"]
        y_values = [counts[1], counts[2], counts[3], counts[4], counts[5]]

        # Plot the bar graph with count labels
        plt.bar(x_labels, y_values)
        for i, count in enumerate(y_values):
            plt.text(i, count, str(count), ha="center", va="bottom")
        plt.title(col_name)
        plt.xlabel("Rating")
        plt.ylabel("Number of Patients")

        # Ensure static directory exists
        if not os.path.exists("static"):
            os.makedirs("static")
        image_path = f"static/bar_graph_{col_name}.png"
        bargraph_paths.append(image_path)
        plt.savefig(image_path)
        plt.close()
        return sum(y_values)

    # Generate bar graphs for rating columns
    total_ratings = 0
    for col in rating_cols:
        total_ratings = bar_graph_rating(col)

    # Generate bar graph for yes/no responses
    yes_no_paths = ["Not a string"]

    def bar_graph_yes_no():
        """
        Generate a stacked bar graph for yes/no questions.
        """
        # Define yes/no columns
        yes_no_cols = ["doc_involvement", "nurse_promptness", "cleanliness", "timely_info", "med_info"]
        counts_yes = [0] * len(yes_no_cols)
        counts_no = [0] * len(yes_no_cols)

        # Count yes/no responses for each question
        for doc in collection.find():
            for i, col in enumerate(yes_no_cols):
                if doc.get(col) == "yes":
                    counts_yes[i] += 1
                elif doc.get(col) == "no":
                    counts_no[i] += 1

        # Plot the stacked bar graph for yes/no responses
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

        if not os.path.exists("static"):
            os.makedirs("static")
        image_path = "static/bar_graph_yes_no.png"
        yes_no_paths.append(image_path)
        plt.gcf().set_size_inches(15, 8)
        plt.savefig(image_path, dpi=100, bbox_inches="tight")
        plt.close()

    bar_graph_yes_no()

    title = f"Bar Graph Analysis (Total Ratings = {total_ratings})"
    return render_template(
        "bargraph.html",
        image_path1=bargraph_paths[1],
        image_path2=bargraph_paths[2],
        image_path3=bargraph_paths[3],
        image_path4=bargraph_paths[4],
        image_path5=bargraph_paths[5],
        image_path6=bargraph_paths[6],
        image_path7=bargraph_paths[7],
        image_path8=bargraph_paths[8],
        image_path9=bargraph_paths[9],
        image_path11=yes_no_paths[1],
        title=title,
    )


@app.route("/piecharts", methods=["GET", "POST"])
def piecharts():
    """
    Generate pie charts for rating and yes/no responses.
    Returns a page displaying the generated pie charts.
    """
    # Define rating columns for pie charts
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
    piechart_paths = ["Not a String"]

    def piechart_rating(col_name):
        """
        Generate a pie chart for a rating column.
        Returns the total ratings for that column.
        """
        one_star = collection.count_documents({col_name: 1})
        two_star = collection.count_documents({col_name: 2})
        three_star = collection.count_documents({col_name: 3})
        four_star = collection.count_documents({col_name: 4})
        five_star = collection.count_documents({col_name: 5})
        total_ratings = one_star + two_star + three_star + four_star + five_star

        # Pie chart details
        labels = ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"]
        sizes = [one_star, two_star, three_star, four_star, five_star]
        plt.clf()
        patches, _ = plt.pie(sizes, startangle=90)
        plt.axis("equal")
        plt.title(f"{col_name} Rating")

        # Create legend with counts and percentages
        percentages = [f"{size} ({size / total_ratings * 100:.1f}%)" for size in sizes]
        legend_labels = [f"{label}\n{perc}" for label, perc in zip(labels, percentages)]
        plt.legend(patches, legend_labels, title="Star Ratings")

        if not os.path.exists("static"):
            os.makedirs("static")
        image_path = f"static/piechart_{col_name}.png"
        piechart_paths.append(image_path)
        plt.savefig(image_path)
        plt.close()
        return total_ratings

    yes_no_paths = ["Not a string"]

    def piechart_yes_no():
        """
        Generate pie charts for yes/no questions.
        """

        def count_yes_no(question):
            yes_count = collection.count_documents({question: "yes"})
            no_count = collection.count_documents({question: "no"})
            return yes_count, no_count

        def plot_pie(question):
            yes_count, no_count = count_yes_no(question)
            total_count = yes_count + no_count
            labels = ["Yes", "No"]
            values = [yes_count, no_count]
            percentages = [f"{count} ({count / total_count * 100:.1f}%)" for count in values]
            plt.clf()
            fig, ax = plt.subplots()
            patches, _ = ax.pie(values)
            ax.set_title(question)
            legend_labels = [f"{label}\n{perc}" for label, perc in zip(labels, percentages)]
            ax.legend(patches, legend_labels)
            if not os.path.exists("static"):
                os.makedirs("static")
            image_path = f"static/piechart_yes_no_{question}.png"
            yes_no_paths.append(image_path)
            plt.savefig(image_path)
            plt.close()

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

    title = f"Pie Chart Analysis (Total Ratings = {average_ratings})"
    return render_template(
        "piechart.html",
        image_path1=piechart_paths[1],
        image_path2=piechart_paths[2],
        image_path3=piechart_paths[3],
        image_path4=piechart_paths[4],
        image_path5=piechart_paths[5],
        image_path6=piechart_paths[6],
        image_path7=piechart_paths[7],
        image_path8=piechart_paths[8],
        image_path9=piechart_paths[9],
        image_path11=yes_no_paths[1],
        image_path12=yes_no_paths[2],
        image_path13=yes_no_paths[3],
        image_path14=yes_no_paths[4],
        image_path15=yes_no_paths[5],
        title=title,
    )


@app.route("/overall_bargraphs", methods=["GET", "POST"])
def overall_bargraphs():
    """
    Generate overall bar graphs combining star ratings and yes/no responses.
    Returns a page displaying the generated bar graphs.
    """

    def save_bar_graphs_():
        """
        Generate and save bar graphs for star ratings and yes/no responses.
        Returns:
            list: Paths of the generated bar graph images.
        """
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
        # Define yes/no columns
        yes_no_cols = ["doc_involvement", "nurse_promptness", "cleanliness", "timely_info", "med_info"]

        # Initialize counters for star ratings and yes/no responses
        ratings_counts = [[] for _ in range(len(star_ratings))]
        yes_no_counts = [[], []]
        x_labels = []

        # Count occurrences for each rating column
        for col in rating_cols:
            for i, star in enumerate(star_ratings):
                count = collection.count_documents({col: star})
                ratings_counts[i].append(count)
            x_labels.append(col)

        # Count occurrences for each yes/no column
        for col in yes_no_cols:
            yes_count = collection.count_documents({col: "yes"})
            no_count = collection.count_documents({col: "no"})
            yes_no_counts[0].append(yes_count)
            yes_no_counts[1].append(no_count)
            x_labels.append(f"{col} (Yes/No)")

        # Sort counts and labels for each star rating in decreasing order
        sorted_counts = []
        sorted_labels = []
        for i in range(len(star_ratings)):
            indices = np.argsort(ratings_counts[i])[::-1]
            sorted_counts.append([ratings_counts[i][j] for j in indices])
            sorted_labels.append([x_labels[j] for j in indices])

        # Sort counts and labels for yes/no columns in decreasing order
        yes_indices = np.argsort(yes_no_counts[0])[::-1]
        no_indices = np.argsort(yes_no_counts[1])[::-1]
        sorted_counts.append([yes_no_counts[0][j] for j in yes_indices])
        sorted_counts.append([yes_no_counts[1][j] for j in no_indices])
        sorted_labels.append([x_labels[j] for j in yes_indices])
        sorted_labels.append([x_labels[j] for j in no_indices])

        image_paths = []

        # Create bar graphs for each star rating
        for i, star in enumerate(star_ratings):
            plt.clf()
            fig, ax = plt.subplots(figsize=(10, 6))
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

        # Create bar graphs for yes/no responses
        for i in range(2):
            plt.clf()
            fig, ax = plt.subplots(figsize=(10, 6))
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
            path_img = "static/bargraph_yes_no_responses.png" if i == 0 else "static/bargraph_no_responses.png"
            plt.savefig(path_img)
            plt.close()
            image_paths.append(path_img)

        return image_paths

    title = "Overall Bar Graph Analysis"
    image_paths = save_bar_graphs_()
    return render_template(
        "overall_bargraph.html",
        image_path16=image_paths[0],
        image_path17=image_paths[1],
        image_path18=image_paths[2],
        image_path19=image_paths[3],
        image_path20=image_paths[4],
        image_path21=image_paths[5],
        image_path22=image_paths[6],
        title=title,
    )


# ----------------------------
# Routes for Data Management
# ----------------------------
@app.route("/manage", methods=["GET"])
def manage():
    """
    Render the manage page for administrative operations.
    """
    return render_template("home_manage.html")


@app.route("/manage", methods=["POST"])
def process_form():
    """
    Process management form submissions for showing, updating, or deleting entries.
    """
    if "show" in request.form:
        entries = retrieve_entries(request.form)
        search_criteria = get_search_criteria(request.form)
        return render_template("manage.html", search_criteria=search_criteria, entries=entries)
    elif "update" in request.form:
        if not any(request.form.values()):
            message = "Invalid operation: Nothing to update."
            return render_template("manage.html", message=message)
        patient_id = int(request.form["patient_id"])
        new_data = {
            "name": request.form["name"],
            "age": request.form["age"],
            "email": request.form["email"],
            # Add additional fields if needed
        }
        updated_count = update_entry(patient_id, new_data)
        message = (
            f"Entry with Patient ID {patient_id} successfully updated."
            if updated_count == 1
            else f"Failed to update entry with Patient ID {patient_id}."
        )
        return render_template("manage.html", message=message)
    elif "delete" in request.form:
        if not any(request.form.values()):
            message = "Invalid operation: Nothing to delete."
            return render_template("manage.html", message=message)
        patient_id = int(request.form["patient_id"])
        deleted_count = delete_entry(patient_id)
        message = (
            f"Entry with Patient ID {patient_id} successfully deleted."
            if deleted_count == 1
            else f"Failed to delete entry with Patient ID {patient_id}."
        )
        return render_template("manage.html", message=message)
    else:
        return render_template("manage.html")


def get_search_criteria(form_data) -> str:
    """
    Construct a search criteria string from form data.

    Args:
        form_data (dict): The submitted form data.

    Returns:
        str: A concatenated string of search criteria.
    """
    search_criteria = []
    for field, value in form_data.items():
        if value and field != "show":
            search_criteria.append(f"{field}: {value}")
    return " and ".join(search_criteria)


def retrieve_entries(form_data):
    """
    Retrieve database entries based on form input criteria.

    Args:
        form_data (dict): The submitted form data.

    Returns:
        list: A list of entries matching the criteria.
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

    Args:
        patient_id (int): The patient ID.
        new_data (dict): The new data for the entry.

    Returns:
        int: The number of modified documents.
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

    Args:
        patient_id (int): The patient ID.

    Returns:
        int: The number of deleted documents.
    """
    result = collection.delete_one({"patient_id": patient_id})
    return result.deleted_count


if __name__ == "__main__":
    # Run the Flask application in debug mode on port 5002.
    app.run(debug=True, port=5002)
