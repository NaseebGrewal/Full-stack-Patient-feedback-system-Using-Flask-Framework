from flask_wtf import FlaskForm  
from wtforms import StringField, IntegerField  
from wtforms.validators import DataRequired, Email, NumberRange  
  
class FeedbackForm(FlaskForm):  
    patient_id = IntegerField('Patient ID', validators=[DataRequired()])  
    name = StringField('Name', validators=[DataRequired()])  
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)])  
    email = StringField('Email', validators=[DataRequired(), Email()])  
    # ... add other fields and validators ...  


app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')  
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS.  
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookies.  
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Control when cookies are sent with requests from external sites.  