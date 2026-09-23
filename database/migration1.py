from pymongo import MongoClient
from pymongo.errors import CollectionInvalid


# --------------------------------------------------
# Database Configuration
# --------------------------------------------------

import os
import ssl
import certifi

from datetime import datetime, timezone

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


# --------------------------------------------------
# Connect to MongoDB
# --------------------------------------------------

# client = MongoClient(MONGO_URI)
db = client['deliora']


# --------------------------------------------------
# Users Collection Schema
# --------------------------------------------------

users_validator = {
    "$jsonSchema": {
        "bsonType": "object",

        "required": [
            "firstName",
            "lastName",
            "email",
            "passwordHash",
            "role",
            "status",
            "createdAt",
        ],

        "properties": {

            # -----------------------------
            # Basic Information
            # -----------------------------

            "firstName": {
                "bsonType": "string",
                "description": "User first name"
            },

            "lastName": {
                "bsonType": "string",
                "description": "User last name"
            },

            "email": {
                "bsonType": "string",
                "description": "User email address"
            },

            "phone": {
                "bsonType": "string",
                "description": "User phone number"
            },


            # -----------------------------
            # Authentication
            # -----------------------------

            "passwordHash": {
                "bsonType": "string",
                "description": "Hashed user password"
            },

            "role": {
                "bsonType": "string",
                "enum": [
                    "customer",
                    "admin"
                ]
            },

            "status": {
                "bsonType": "string",
                "enum": [
                    "active",
                    "inactive",
                    "blocked"
                ]
            },


            # -----------------------------
            # Profile
            # -----------------------------

            "dateOfBirth": {
                "bsonType": "date"
            },

            "gender": {
                "bsonType": "string",
                "enum": [
                    "male",
                    "female",
                    "other",
                    "prefer_not_to_say"
                ]
            },

            "profileImage": {
                "bsonType": "string"
            },


            # -----------------------------
            # Addresses
            # -----------------------------

            "addresses": {
                "bsonType": "array",

                "items": {
                    "bsonType": "object",

                    "properties": {

                        "type": {
                            "bsonType": "string",
                            "enum": [
                                "home",
                                "work",
                                "other"
                            ]
                        },

                        "fullName": {
                            "bsonType": "string"
                        },

                        "phone": {
                            "bsonType": "string"
                        },

                        "addressLine1": {
                            "bsonType": "string"
                        },

                        "addressLine2": {
                            "bsonType": "string"
                        },

                        "landmark": {
                            "bsonType": "string"
                        },

                        "city": {
                            "bsonType": "string"
                        },

                        "state": {
                            "bsonType": "string"
                        },

                        "postalCode": {
                            "bsonType": "string"
                        },

                        "country": {
                            "bsonType": "string"
                        },

                        "isDefault": {
                            "bsonType": "bool"
                        }
                    }
                }
            },


            # -----------------------------
            # Wishlist
            # -----------------------------

            "wishlist": {
                "bsonType": "array",

                "items": {
                    "bsonType": "objectId"
                }
            },


            # -----------------------------
            # Perfume Preferences
            # -----------------------------

            "preferences": {
                "bsonType": "object",

                "properties": {

                    "preferredGender": {
                        "bsonType": "string",
                        "enum": [
                            "male",
                            "female",
                            "unisex",
                            "all"
                        ]
                    },

                    "preferredCategories": {
                        "bsonType": "array",

                        "items": {
                            "bsonType": "string"
                        }
                    },

                    "preferredNotes": {
                        "bsonType": "array",

                        "items": {
                            "bsonType": "string"
                        }
                    },

                    "preferredBrands": {
                        "bsonType": "array",

                        "items": {
                            "bsonType": "string"
                        }
                    }
                }
            },


            # -----------------------------
            # Marketing Preferences
            # -----------------------------

            "marketingPreferences": {
                "bsonType": "object",

                "properties": {

                    "emailMarketing": {
                        "bsonType": "bool"
                    },

                    "smsMarketing": {
                        "bsonType": "bool"
                    },

                    "pushNotifications": {
                        "bsonType": "bool"
                    }
                }
            },


            # -----------------------------
            # Login Information
            # -----------------------------

            "lastLoginAt": {
                "bsonType": "date"
            },


            # -----------------------------
            # Timestamps
            # -----------------------------

            "createdAt": {
                "bsonType": "date"
            },

            "updatedAt": {
                "bsonType": "date"
            }
        }
    }
}


# --------------------------------------------------
# Create Users Collection
# --------------------------------------------------

def create_users_collection():

    if "users" in db.list_collection_names():

        print("users collection already exists.")

        return

    try:

        db.create_collection(
            "users",
            validator=users_validator,
            validationLevel="strict",
            validationAction="error"
        )

        print("users collection created successfully.")

    except CollectionInvalid as error:

        print(f"Collection creation failed: {error}")


# --------------------------------------------------
# Create Indexes
# --------------------------------------------------

def create_users_indexes():

    users = db["users"]

    # Email must be unique
    users.create_index(
        [("email", 1)],
        unique=True,
        name="unique_email"
    )

    # Phone lookup
    users.create_index(
        [("phone", 1)],
        name="phone_index"
    )

    # User role
    users.create_index(
        [("role", 1)],
        name="role_index"
    )

    # Account status
    users.create_index(
        [("status", 1)],
        name="status_index"
    )

    # Newest users
    users.create_index(
        [("createdAt", -1)],
        name="created_at_index"
    )

    print("User indexes created successfully.")


# --------------------------------------------------
# Insert User
# --------------------------------------------------

def insert_user():

    users = db["users"]

    user = {
        "firstName": "Nikita",
        "lastName": "Patidar",
        "email": "nikita@example.com",
        "passwordHash": "hashed_password_here",

        "role": "customer",
        "status": "active",

        "phone": "9876543210",

        "dateOfBirth": datetime(2003, 8, 1, tzinfo=timezone.utc),

        "gender": "female",

        "profileImage": "",

        "addresses": [
            {
                "type": "home",
                "fullName": "Nikita Patidar",
                "phone": "9876543210",
                "addressLine1": "123 Main Street",
                "addressLine2": "",
                "landmark": "",
                "city": "Indore",
                "state": "Madhya Pradesh",
                "postalCode": "452001",
                "country": "India",
                "isDefault": True
            }
        ],

        "wishlist": [],

        "preferences": {
            "preferredGender": "unisex",
            "preferredCategories": [],
            "preferredNotes": [],
            "preferredBrands": []
        },

        "marketingPreferences": {
            "emailMarketing": True,
            "smsMarketing": False,
            "pushNotifications": True
        },

        "lastLoginAt": None,

        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }

    try:
        result = users.insert_one(user)

        print("User inserted successfully!")
        print("User ID:", result.inserted_id)

    except Exception as error:
        print(f"User insertion failed: {error}")

# --------------------------------------------------
# Run Migration
# --------------------------------------------------

def migrate():

    print("Starting users migration...")

    create_users_collection()

    create_users_indexes()

    print("Users migration completed successfully.")

    insert_user()

    print("dummy data inserted successfully")


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    migrate()

    client.close()