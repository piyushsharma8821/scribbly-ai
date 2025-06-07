from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

notes_collection = db["notes_with_tags"]
users_collection = db["users"]
chats_collection = db["chats"]

async def get_notes_by_ids(note_ids: list[str]) -> list[str]:
    obj_ids = [ObjectId(nid) for nid in note_ids]
    notes_cursor = notes_collection.find({"_id": {"$in": obj_ids}})
    return [note["content"] for note in await notes_cursor.to_list()]

async def start_chat(owner: str, note_ids: list[str], ques: str, reply: str):
    result = await chats_collection.insert_one({
        "owner": owner,
        "created_at": datetime.utcnow(),
        "note_ids": note_ids,
        "messages": [
            {"role": "user", "content": ques},
            {"role": "assistant", "content": reply}
        ]
    })
    return str(result.inserted_id)

async def append_to_chat(chat_id: str, ques: str, reply: str):
    await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$push": {
            "messages": {
                "$each": [
                    {"role": "user", "content": ques},
                    {"role": "assistant", "content": reply}
                ]
            }
        }}
    )

async def get_chat_by_id(chat_id: str) -> dict | None:
    return await chats_collection.find_one({"_id": ObjectId(chat_id)})

async def replace_summary(chat_id: str, new_summary: str, new_msgs: list[dict]):
    await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {
            "$set": {
                "summary": new_summary,
                "messages": new_msgs
            }
        }
    )