from fastapi import Depends, APIRouter, HTTPException
from datetime import datetime
from pydantic import BaseModel
from app.db import notes_collection
from bson import ObjectId
from app.get_user import get_current_user
from app.azure_client import get_text_analytics_client

router = APIRouter()

class Note(BaseModel):
    title: str
    content: str

def note_helper(note) -> dict:
    return{
        "id": str(note["_id"]),
        "time": note.get("time", ""),
        "tags": note.get("tags", []),
        "title": note["title"],
        "content": note["content"]
    }

async def extract_tags(text: str):
    client = get_text_analytics_client()
    response = client.extract_key_phrases([text])[0]
    return response.key_phrases if not response.is_error else []

@router.post("/notes")
async def create_note(note: Note, user: str = Depends(get_current_user)):
    tags = await extract_tags(note.content + " " + note.title)
    note_dict = {"owner": user, "time": datetime.utcnow().isoformat(), "tags": tags}
    note_dict.update(note.model_dump())
    result = await notes_collection.insert_one(note_dict)
    saved_note = await notes_collection.find_one({"_id": result.inserted_id})
    return note_helper(saved_note)

@router.get("/notes")
async def get_notes(user: str = Depends(get_current_user)):
    notes = []
    async for note in notes_collection.find({"owner": user}).sort("time", -1):
        notes.append(note_helper(note))
    return notes

@router.put("/notes/{note_id}")
async def update_note(note_id: str, updated: Note, user: str = Depends(get_current_user)):
    note = await notes_collection.find_one({"_id": ObjectId(note_id)})
    if not note or note.get("owner") != user:
        raise HTTPException(status_code=403, detail="Not authorized to update this note")

    result = await notes_collection.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": updated.model_dump()}
    )
    if result.modified_count == 1:
        updated_note = await notes_collection.find_one({"_id": ObjectId(note_id)})
        return note_helper(updated_note)
    raise HTTPException(status_code=404, detail="Note not found")

@router.delete("/notes/{note_id}")
async def delete_note(note_id: str, user: str = Depends(get_current_user)):
    note = await notes_collection.find_one({"_id": ObjectId(note_id)})
    if not note or note.get("owner") != user:
        raise HTTPException(status_code=403, detail="Not authorized to delete this note")
    
    result = await notes_collection.delete_one({"_id": ObjectId(note_id)})
    if result.deleted_count == 1:
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="Note not found")

