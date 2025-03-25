# Import necessary libraries
import json
import os
from urllib.parse import quote_plus

import redis
from flask import Flask, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from mongo_db_client import client
# Use environment variables for configuration
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT"))
redis_password = os.getenv("REDIS_PASSWORD")

# Connect to Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)

# connect to MongoDB using the client from mongo_db_client.py
MONGODB_CLIENT = client
db = MONGODB_CLIENT["Naseeb"]
collection = db["Feedback"]

app = Flask(__name__)


# Refactor repetitive code blocks into a function
def get_feedback_data_from_form(form):
    feedback_data = {
        "patient_id": int(form["patient_id"]),
        "name": form["name"],
        "age": int(form["age"]),
        "email": form["email"],
        "date": form["date"],
        "overall_exp": int(form["overall_exp"]),
        "doc_care": int(form["doc_care"]),
        # ... add other form fields ...
    }
    return feedback_data


# Define the route for the feedback error page
@app.route("/feedback_error")
def feedback_error():
    print("Testing error page")
    return "Testing error page"

# Define the route for the feedback form
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        patient_id = int(request.form["patient_id"])
        if "patient_id" in session or collection.find_one({"patient_id": patient_id}):
            return redirect(url_for("feedback_error"))

        session["patient_id"] = patient_id
        feedback_data = get_feedback_data_from_form(request.form)

        # Inserting data into Redis and MongoDB
        redis_client.set(f"data:{patient_id}", json.dumps(feedback_data))
        collection.insert_one(feedback_data)

        return redirect(url_for("feedback_thankyou"))
    return render_template("feedback.html")


# ... other routes and functions ...

if __name__ == "__main__":
    app.run(debug=True, port=5002)
