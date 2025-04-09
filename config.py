import os

class Config:
    SECRET_KEY = 'nehapankaj'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///bloodconnect.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    UPLOAD_FOLDER = 'static/pdf'
    UPLOAD_EXTENSIONS = ['.pdf']
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    DEBUG = True