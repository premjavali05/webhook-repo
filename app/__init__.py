from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    client = MongoClient(os.getenv("MONGO_URI"))
    app.db = client.webhookdb
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app