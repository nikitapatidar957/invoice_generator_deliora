# import os
# from pymongo import MongoClient
# from dotenv import load_dotenv

# load_dotenv()

# uri = os.getenv("MONGODB_URI")

# client = MongoClient(uri)

# db = client["learning_platform"]

# collection = db["users"]

# collection.insert_one({
#     "name": "Neha"
# })

# # print("Connected and data inserted!")

import os
import ssl
import certifi

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")

client = MongoClient(
    uri,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
)

try:
    result = client.admin.command("ping")
    print("MongoDB Atlas connected successfully!")
    print(result)

    db = client["learning_platform"]
    collection = db["users"]

    result = collection.insert_one({
        "name": "Neha"
    })

    print("Data inserted!")
    print("Inserted ID:", result.inserted_id)

except Exception as e:
    print("MongoDB connection failed:")
    print(repr(e))