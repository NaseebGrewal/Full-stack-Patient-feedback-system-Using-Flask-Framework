from flask_bcrypt import Bcrypt  
  
bcrypt = Bcrypt(app)  
  
# Hash a password before saving  
hashed_password = bcrypt.generate_password_hash('mysecretpassword').decode('utf-8')  


#Limit Payload Size: To protect against denial-of-service (DoS) attacks,
# limit the size of the request payload.
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit  





