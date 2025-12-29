import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smartagridoctor-secret-key-2024'
    
    # Use SQLite instead of MySQL
    SQLALCHEMY_DATABASE_URI = 'sqlite:///smartagridoctor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads/'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Kaggle configuration
    KAGGLE_USERNAME = 'mbthimma'
    KAGGLE_KEY = 'a602783497ca800ac5941e349fbe3e5e'