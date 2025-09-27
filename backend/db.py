from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")  # replace with your URI
    db = client["ml_db"]
    collection = db["processed_data"]
    return collection
