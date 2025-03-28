# Full Stack Patient Feedback System Using Flask Framework

This repository contains the implementation of a **Full Stack Patient Feedback System** built with the **Flask Framework**. The system allows healthcare institutions to collect feedback from patients, analyze the results, and improve the quality of their services.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Project Structure](#project-structure)
5. [Usage](#usage)
6. [Testing](#testing)
7. [Contributing](#contributing)
8. [License](#license)
9. [Acknowledgements](#acknowledgements)

---

## Project Overview

The **Patient Feedback System** is designed to simplify the collection and analysis of feedback from patients. Built with Flask, it provides a user-friendly web interface where patients can submit their feedback about the healthcare services they received. The system is structured to scale and is easy to deploy, making it suitable for both small clinics and large hospitals.

---

## Features

- **Patient Feedback Form**: Allows patients to submit their experiences.
- **Admin Dashboard**: Provides insights into collected feedback.
- **Secure Communication**: Ensures that all data is transmitted securely.
- **Feedback Analysis**: Provides a mechanism to analyze patient feedback.
- **User Authentication**: Secure login for admin and users.
- **Responsive Design**: Optimized for mobile and desktop usage.

---

## Installation

Follow these steps to get your environment set up:

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Full_stack_Patient_feedback_system_Using_Flask_Framework.git
cd Full_stack_Patient_feedback_system_Using_Flask_Framework
```

### 2. Set up the virtual environment
It is recommended to use a Python virtual environment to manage dependencies.

```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate     # For Windows
```

### 3. Install dependencies
Install the necessary dependencies by running the following:

```bash
pip install -r requirements.txt
```

If you're working on development or testing, you can install dependencies from the `requirements-dev.txt` or `requirements-ci.txt`.

```bash
pip install -r requirements-dev.txt   # For development dependencies
pip install -r requirements-ci.txt    # For CI-specific dependencies
```

## To execute the project locally

## Step 1: Clone the Repository on your local system.
 
## Step 2: Install the required dependencies using "pip install -r requirements-dev.txt"

## Step 3: Execute the app.py file.

---

## Project Structure

This is a quick overview of the repository structure:

```
Full_stack_Patient_feedback_system_Using_Flask_Framework/
│
├── securitycheck/
│   ├── connection.py     # Database connection handler
│   └── main.py           # Security features implementation
│
├── templates/            # HTML templates for the application
│
├── .gitignore            # Git ignore file to exclude unnecessary files
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── README.md             # Project documentation (this file)
├── app.py                # Main Flask app entry point
├── main.py               # Core application logic
├── metadata.txt          # Metadata for the project
├── requirements-ci.txt   # CI-related dependencies
├── requirements-dev.txt  # Development dependencies
├── requirements.txt      # Production dependencies
├── ruff.toml             # Configuration for Ruff (static analysis tool)
└── test.ipynb            # Jupyter Notebook for testing and exploration
```

---

## Usage

1. **Step to Run the Flask app**:
   Start the application by running the following command:

  
   Make sure MongoDB connection is established.
   Create a free MongoDB account. Copy your connection key and set the env variable for password.
   connection string looks like this:
   ```bash
   "mongodb+srv://{encoded_username}:{encoded_password}@cluster1.somestring.mongodb.net/?appName=yourClusterName"
   ```
   Set the envionment variable for MongoDB and Redis in your .env file and load them using python-dotenv

   ```bash
   from dotenv import load_dotenv
   # Load the .env file
   load_dotenv()
   ```

   ## Make sure Redis Connection is established.
   
   ## (For MAC)

   ### list if redis is running already
   ```bash
   brew services list
   ```
   ### start redis server
   ```bash
   brew services start redis
   ```
   ### stop redis server
   ```bash
   brew services stop redis
   ```

   Finally after successfully connecting to both Mongo DB and Redis 

   install all requirements from requirements.txt

   ```bash
   pip install -r requirements.txt
   ```

   Run the Flask Server

   ```bash
   python app.py
   ```

2. **Access the Application**:
   Open your browser and go to `http://127.0.0.1:5000` to access the system.

3. **Admin Dashboard**:
   Log in as an admin to manage feedback and view analytics.

4. **Feedback Form**:
   Patients can visit the homepage and submit their feedback on the services provided.

---

## Testing

To run the tests, follow these steps:

1. Install testing dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   You can run unit tests using `pytest` or run the Jupyter notebook (`test.ipynb`) for interactive testing.

   ```bash
   pytest
   ```

---

## Contributing

We welcome contributions to improve the project! If you'd like to contribute, follow these steps:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Submit a pull request.

Please ensure that your code follows the project style and passes all tests.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
