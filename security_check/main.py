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
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired, Email, NumberRange
from pymongo.collection import ReturnDocument
from flask_talisman import Talisman
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
# # create a MongoClient instance
# mongobd_password = os.getenv("mongodb_password")
# client = MongoClient(f"mongodb+srv://ngrewal240:{mongobd_password}@cluster1.1bdcxqo.mongodb.net/")
password = quote_plus("Ng@.1234567890")
client = MongoClient(f"mongodb+srv://ngrewal240:{password}@cluster1.1bdcxqo.mongodb.net/")


# select the database and collection
db = client["Naseeb"]
collection = db["Feedback"]
#  ----------------------------------------------------------------

app = Flask(__name__)




# Hashing Sensitive Data

bcrypt = Bcrypt(app)


# Hash a password before saving
hashed_password = bcrypt.generate_password_hash("mysecretpassword").decode("utf-8")


# Limit Payload Size: To protect against denial-of-service (DoS) attacks,
# limit the size of the request payload.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_default_secret_key")
app.config["SESSION_COOKIE_SECURE"] = True  # Only send cookies over HTTPS.
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access to session cookies.
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Control when cookies are sent with requests from external sites.




#Input Validator
class FeedbackForm(FlaskForm):
    patient_id = IntegerField("Patient ID", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    age = IntegerField("Age", validators=[DataRequired(), NumberRange(min=0, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    # ... add other fields and validators ...






# Sanitize Data
# When updating an entry in MongoDB, sanitize the input data
def update_entry(patient_id, new_data):
    sanitized_data = {key: sanitize(value) for key, value in new_data.items() if value}
    result = collection.find_one_and_update(
        {"patient_id": patient_id}, {"$set": sanitized_data}, return_document=ReturnDocument.AFTER
    )
    return result



#Security Headers
Talisman(app, content_security_policy=None)  # Configure CSP according to your needs

#Error Handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500