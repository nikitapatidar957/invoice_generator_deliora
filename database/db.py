from pymongo import ReturnDocument

from database.mongodb import COLLECTIONS, get_mongo_database


def get_database():
    return get_mongo_database()


def get_collection(name: str):
    return get_database()[COLLECTIONS[name]]


def next_id(sequence_name: str, session=None) -> int:
    result = get_collection("sequences").find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        session=session,
    )
    return result["value"]


def init_db() -> None:
    database = get_database()
    database[COLLECTIONS["settings"]].create_index("key", unique=True)
    database[COLLECTIONS["products"]].create_index("sku", unique=True)
    database[COLLECTIONS["products"]].create_index([("name", 1)])
    database[COLLECTIONS["invoices"]].create_index("invoice_number", unique=True)
    database[COLLECTIONS["invoices"]].create_index([("created_at", -1)])
    database[COLLECTIONS["invoices"]].create_index("customer_name")
    database[COLLECTIONS["invoice_items"]].create_index([("invoice_id", 1), ("id", 1)])

    from database.seed import seed_if_needed

    seed_if_needed(database)
