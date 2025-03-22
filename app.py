import json
import os
import re
from urllib.parse import quote_plus

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import redis
from flask import Flask, redirect, render_template, request, session, url_for
from pymongo import MongoClient

# Use 'agg' backend for matplotlib to work without a display server
matplotlib.use("agg")

# REDIS DATABASE CONNECTION
# ---------------------------------------------------------------
# Replace the values with your own Redis configuration
redis_host = "localhost"
redis_port = 6379
redis_password = None

# Connect to Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)

# MONGODB DATABASE CONNECTION
#  ----------------------------------------------------------------
# Create a MongoClient instance
# mongobd_password = os.getenv("mongodb_password")
# client = MongoClient(f"mongodb+srv://ngrewal240:{mongobd_password}@cluster1.1bdcxqo.mongodb.net/")
password = quote_plus("Ng@.1234567890")
client = MongoClient(f"mongodb+srv://ngrewal240:{password}@cluster1.1bdcxqo.mongodb.net/")

# Select the database and collection
db = client["Naseeb"]
collection = db["Feedback"]
#  ----------------------------------------------------------------

app = Flask(__name__)

# Define the route for the feedback form
#  -----------------------------------------------------------------
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        # Get the form data
        patient_id = int(request.form["patient_id"])
        
        # Check if the patient ID exists in the session
        if "patient_id" in session:
            # Patient ID already exists in session, indicating feedback already submitted
            return redirect(url_for("feedback_error"))

        # Check if the patient ID exists in the database
        if collection.find_one({"patient_id": patient_id}):
            # Patient ID already exists in the database, indicating feedback already submitted
            return redirect(url_for("feedback_error"))

        # Add the patient ID to the session
        session["patient_id"] = patient_id
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

        # Inserting data into Redis
        # Convert the dictionary to a JSON string
        data_json = json.dumps(feedback_data)
        redis_client.set(f"data:{feedback_data['patient_id']}", data_json)

        # Inserting data into MongoDB
        collection.insert_one(feedback_data)

        return redirect(url_for("feedback_thankyou"))

    else:
        return render_template("feedback.html")

# Define the route for the feedback thank-you page
@app.route("/feedback-thankyou")
def feedback_thankyou():
    return render_template("feedback_thankyou.html")

# Define the route for already submitted feedback
@app.route("/feedback_error")
def feedback_error():
    return render_template("feedback_error.html")

# Define the route for home page
@app.route("/")
def home():
    return render_template("home.html")

# Define the route for bargraphs page
@app.route("/bargraphs", methods=["GET", "POST"])
def bargraphs():
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
    path = ["Not a String"]

    def bar_graph_rating(var):
        ratings = collection.find({}, {"_id": 0, var: 1})

        # Calculate the number of patients in each rating category
        one_star = 0
        two_star = 0
        three_star = 0
        four_star = 0
        five_star = 0

        for rating in ratings:
            if rating[var] == 1:
                one_star += 1
            elif rating[var] == 2:
                two_star += 1
            elif rating[var] == 3:
                three_star += 1
            elif rating[var] == 4:
                four_star += 1
            elif rating[var] == 5:
                five_star += 1

        total_ratings2 = one_star + two_star + three_star + four_star + five_star

        # Plot the bar graph
        x_labels = ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"]
        y_values = [one_star, two_star, three_star, four_star, five_star]

        # Add count labels on top of each bar
        for i, count in enumerate(y_values):
            plt.text(i, count, str(count), ha="center", va="bottom")

        plt.bar(x_labels, y_values)
        plt.title(var)
        plt.xlabel("Rating")
        plt.ylabel("Number of Patients")
        if not os.path.exists("static"):
            os.makedirs("static")
        path_ = "static/bar_graph_" + var + ".png"
        path.append(path_)
        plt.savefig(path_)
        plt.close()
        return total_ratings2

    path2 = ["Not a string"]

    def bar_graph_yes_no():
        questions = ["doc_involvement", "nurse_promptness", "cleanliness", "timely_info", "med_info"]
        counts_yes = [0] * len(questions)
        counts_no = [0] * len(questions)

        # Retrieve the data from the database
        for doc in collection.find():
            for i, q in enumerate(questions):
                if doc[q] == "yes":
                    counts_yes[i] += 1
                elif doc[q] == "no":
                    counts_no[i] += 1

        # Plot the bar graph
        x_labels = questions
        x_indices = range(len(x_labels))

        plt.bar(x_indices, counts_yes, label="Yes")
        plt.bar(x_indices, counts_no, bottom=counts_yes, label="No")

        # Add count labels on top of each bar
        for i, count in enumerate(counts_yes):
            plt.text(i, count, str(count), ha="center", va="bottom")

        for i, count in enumerate(counts_no):
            plt.text(i, count + counts_yes[i], str(count), ha="center", va="bottom")

        plt.title("Responses to Yes/No Questions")
        plt.xlabel("Question")
        plt.ylabel("Count")
        plt.legend()
        plt.xticks(x_indices, x_labels)  # Set the x-axis tick labels

        if not os.path.exists("static"):
            os.makedirs("static")

        path_ = "static/bar_graph_yes_no.png"
        path2.append(path_)

        plt.gcf().set_size_inches(15, 8)  # Set figure size to 15x8 inches

        # Save the figure with customized size
        plt.savefig(path_, dpi=100, bbox_inches="tight")
        plt.close()  # Close the plot to release resources

    for var in rating_cols:
        Total_ratings = bar_graph_rating(var)

    bar_graph_yes_no()
    title = "Bar Graph Analysis" + " (Total Ratings = " + str(Total_ratings) + ")"

    return render_template(
        "bargraph.html",
        image_path1=path[1],
        image_path2=path[2],
        image_path3=path[3],
        image_path4=path[4],
        image_path5=path[5],
        image_path6=path[6],
        image_path7=path[7],
        image_path8=path[8],
        image_path9=path[9],
        image_path11=path2[1],
        title=title,
    )

# Define the route for piecharts page
@app.route("/piecharts", methods=["GET", "POST"])
def piecharts():
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
    path = ["Not a String"]

    def piechart_rating(var):
        val = "{}".format(var)
        # Get count of patients for each star rating
        one_star = collection.count_documents({val: 1})
        two_star = collection.count_documents({val: 2})
        three_star = collection.count_documents({val: 3})
        four_star = collection.count_documents({val: 4})
        five_star = collection.count_documents({val: 5})

        total_ratings = one_star + two_star + three_star + four_star + five_star

        # Create a pie chart
        labels = ["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"]
        sizes = [one_star, two_star, three_star, four_star, five_star]

        plt.clf()
        patches, _ = plt.pie(sizes, startangle=90)
        plt.axis("equal")
        plt.title(var + " Rating")

        # Calculate percentages and format count and percentage labels for the legend
        percentages = [f"{size} ({size / total_ratings * 100:.1f}%)" for size in sizes]
        legend_labels = [f"{label}\n{percentage}" for label, percentage in zip(labels, percentages)]

        plt.legend(patches, legend_labels, title="Star Ratings")

        if not os.path.exists("static"):
            os.makedirs("static")
        path_ = "static/piechart_" + var + ".png"
        path.append(path_)
        plt.savefig(path_)
        plt.close()

        return total_ratings

    path2 = ["Not a string"]

    def piechart_yes_no():
        # Count the number of yes and no responses for a question
        def count_yes_no(question):
            yes_count = collection.count_documents({question: "yes"})
            no_count = collection.count_documents({question: "no"})
            return yes_count, no_count

        # Plot a pie chart of the yes/no responses for a question
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

            # Add count and percentage labels to the legend
            legend_labels = [f"{label}\n{percentage}" for label, percentage in zip(labels, percentages)]
            ax.legend(patches, legend_labels)

            if not os.path.exists("static"):
                os.makedirs("static")
            path_ = "static/piechart_yes_no" + question + ".png"
            path2.append(path_)
            plt.savefig(path_)
            plt.close()

        # Example usage
        questions = ["doc_involvement", "nurse_promptness", "cleanliness", "timely_info", "med_info"]
        for var in questions:
            plot_pie(var)

    Total_ratings = 0
    count_val = 0
    for var in rating_cols:
        Total_ratings += piechart_rating(var)
        count_val += 1
    piechart_yes_no()

    Total_ratings //= count_val

    title = "Pie Chart Analysis" + " (Total Ratings = " + str(Total_ratings) + ")"

    return render_template(
        "piechart.html",
        image_path1=path[1],
        image_path2=path[2],
        image_path3=path[3],
        image_path4=path[4],
        image_path5=path[5],
        image_path6=path[6],
        image_path7=path[7],
        image_path8=path[8],
        image_path9=path[9],
        image_path11=path2[1],
        image_path12=path2[2],
        image_path13=path2[3],
        image_path14=path2[4],
        image_path15=path2[5],
        title=title,
    )

# Define the route for overall bargraphs page
@app.route("/overall_bargraphs", methods=["GET", "POST"])
def overall_bargraphs():
    def save_bar_graphs_():
        star_ratings = [1, 2, 3, 4, 5]
        ratings_counts = [[] for _ in range(len(star_ratings))]
        yes_no_counts = [[], []]
        x_labels = []

        # Count the number of occurrences for each column and star rating
        for col in rating_cols:
            for i, star in enumerate(star_ratings):
                star_count = collection.count_documents({col: star})
                ratings_counts[i].append(star_count)

            x_labels.append(col)

        # Count the number of occurrences for each yes/no column
        for col in yes_no_cols:
            yes_count = collection.count_documents({col: "yes"})
            no_count = collection.count_documents({col: "no"})
            yes_no_counts[0].append(yes_count)
            yes_no_counts[1].append(no_count)

            x_labels.append(col + " (Yes/No)")

        # Sort the counts and x labels for each star rating in decreasing order
        sorted_counts = []
        sorted_labels = []
        for i in range(len(star_ratings)):
            sorted_indices = np.argsort(ratings_counts[i])[::-1]
            sorted_counts.append([ratings_counts[i][j] for j in sorted_indices])
            sorted_labels.append([x_labels[j] for j in sorted_indices])

        # Sort the counts and x labels for yes/no columns in decreasing order
        yes_indices = np.argsort(yes_no_counts[0])[::-1]
        no_indices = np.argsort(yes_no_counts[1])[::-1]

        sorted_counts.append([yes_no_counts[0][j] for j in yes_indices])
        sorted_counts.append([yes_no_counts[1][j] for j in no_indices])
        sorted_labels.append([x_labels[j] for j in yes_indices])
        sorted_labels.append([x_labels[j] for j in no_indices])

        # Create bar graphs for each star rating
        for i in range(len(star_ratings)):
            plt.clf()
            fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
            # Plot the bar graph
            bars = plt.bar(range(len(sorted_counts[i])), sorted_counts[i])
            plt.xlabel("Column")
            plt.ylabel("Count")
            plt.title("Count of " + str(star_ratings[i]) + "-Star Ratings by Column")
            plt.xticks(range(len(sorted_counts[i])), sorted_labels[i], rotation="vertical")
            plt.tight_layout()  # Adjust the spacing between subplots

            # Add count labels on top of each bar
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2, height, height, ha="center", va="bottom")

            if not os.path.exists("static"):
                os.makedirs("static")
            path = "static/bargraph_" + str(star_ratings[i]) + "_star_ratings.png"
            plt.savefig(path)
            plt.close()

        # Create bar graphs for yes/no columns
        for i in range(2):
            plt.clf()
            fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
            # Plot the bar graph
            bars = plt.bar(range(len(sorted_counts[i + len(star_ratings)])), sorted_counts[i + len(star_ratings)])
            plt.xlabel("Column")
            plt.ylabel("Count")
            plt.title("Count of Yes/No Responses by Column")
            plt.xticks(
                range(len(sorted_counts[i + len(star_ratings)])),
                sorted_labels[i + len(star_ratings)],
                rotation="vertical",
            )
            plt.tight_layout()  # Adjust the spacing between subplots

            # Add count labels on top of each bar
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2, height, height, ha="center", va="bottom")

            path = "static/bargraph_yes_no_responses.png" if i == 0 else "static/bargraph_no_responses.png"
            plt.savefig(path)
            plt.close()

        return [f"static/bargraph_{star}_star_ratings.png" for star in star_ratings] + [
            "static/bargraph_yes_no_responses.png",
            "static/bargraph_no_responses.png",
        ]

    title = "Over Rating Bar Graph Analysis"
    path3 = save_bar_graphs_()
    return render_template(
        "overall_bargraph.html",
        image_path16=path3[0],
        image_path17=path3[1],
        image_path18=path3[2],
        image_path19=path3[3],
        image_path20=path3[4],
        image_path21=path3[5],
        image_path22=path3[6],
        title=title,
    )

# Define the route for manage page
@app.route("/manage", methods=["GET"])
def manage():
    return render_template("home_manage.html")

# Process the form submission
@app.route("/manage", methods=["POST"])
def process_form():
    if "show" in request.form:
        # Retrieve entries from the database based on the form input values
        entries = retrieve_entries(request.form)
        search_criteria = get_search_criteria(request.form)
        return render_template("manage.html", search_criteria=search_criteria, entries=entries)

    elif "update" in request.form:
        if not any(request.form.values()):
            message = "Invalid operation: Nothing to update."
            return render_template("manage.html", message=message)
        # Update an entry in the database
        patient_id = int(request.form["patient_id"])
        new_data = {
            "name": request.form["name"],
            "age": request.form["age"],
            "email": request.form["email"],
            # Add more fields as needed
        }
        updated_count = update_entry(patient_id, new_data)
        if updated_count == 1:
            message = f"Entry with Patient ID {patient_id} successfully updated."
        else:
            message = f"Failed to update entry with Patient ID {patient_id}."
        return render_template("manage.html", message=message)

    elif "delete" in request.form:
        if not any(request.form.values()):
            message = "Invalid operation: Nothing to delete."
            return render_template("manage.html", message=message)
        # Delete an entry from the database
        patient_id = int(request.form["patient_id"])
        deleted_count = delete_entry(patient_id)
        if deleted_count == 1:
            message = f"Entry with Patient ID {patient_id} successfully deleted."
        else:
            message = f"Failed to delete entry with Patient ID {patient_id}."
        return render_template("manage.html", message=message)

    else:
        return render_template("manage.html")

# Retrieve search criteria from the form input values
def get_search_criteria(form_data):
    search_criteria = []

    for field, value in form_data.items():
        if value and field != "show":
            search_criteria.append(f"{field}: {value}")

    return " and ".join(search_criteria)

# Retrieve entries from the database based on the form input values
def retrieve_entries(form_data):
    """
    This function returns list of entries
    """
    query = {}

    for field, value in form_data.items():
        if value and field in ["patient_id", "age"]:
            query[field] = int(value)
        elif value and field == "name":
            regex = re.compile(re.escape(value), re.IGNORECASE)
            query[field] = regex
        elif value:
            query[field] = value

    entries = collection.find(query)
    return list(entries)

# Update an entry in the database
def update_entry(patient_id, new_data):
    existing_data = collection.find_one({"patient_id": patient_id})

    for key, value in new_data.items():
        if value:
            existing_data[key] = value

    result = collection.update_one({"patient_id": patient_id}, {"$set": existing_data})
    return result.modified_count

# Delete an entry from the database
def delete_entry(patient_id):
    result = collection.delete_one({"patient_id": patient_id})
    return result.deleted_count

if __name__ == "__main__":
    app.run(debug=True, port=5002)
