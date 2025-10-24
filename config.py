import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/mockup_db')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'mockup_db')
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'funnytees-uploader')
    AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-2')
    
    # Flask Configuration
    DEBUG = os.getenv('DEBUG', False)
    TESTING = os.getenv('TESTING', False)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    PORT = int(os.getenv("PORT", os.getenv("FLASK_PORT", 8080)))
    
    # Image Processing
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_FORMATS = {'PNG', 'JPEG', 'JPG', 'GIF', 'BMP'}
    
    # Temporary file storage
    TEMP_UPLOAD_DIR = os.getenv('TEMP_UPLOAD_DIR', './temp_uploads')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MONGODB_URI = 'mongodb://localhost:27017/mockup_db_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


