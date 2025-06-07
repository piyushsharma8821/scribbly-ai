import strawberry
from fastapi import Depends
from strawberry.fastapi import GraphQLRouter
from dateutil.parser import parse
from typing import List, Optional
from app.db import notes_collection
from app.get_user import get_current_user

@strawberry.type
class NoteType:
    id: str
    time: str
    tags: List[str]
    title: str
    content: str

@strawberry.type
class NotesResult:
    total_count: int
    notes: List[NoteType]

async def get_context(user=Depends(get_current_user)):
    return {"user": user}

@strawberry.type
class Query:
    @strawberry.field
    async def notes(self, info, start_time: Optional[str] = None, end_time: Optional[str] = None, tag: Optional[str] = None, limit: int = 10, offset: int = 0) -> NotesResult:
        user = info.context["user"]
        query = {"owner": user}

        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = parse(start_time)
            if end_time:
                time_filter["$lte"] = parse(end_time)
            query["time"] = time_filter

        if tag:
            query["tags"] = {
                "$elemMatch": {
                    "$regex": f"{tag}",
                    "$options": "i"
                }
            }

        total = await notes_collection.count_documents(query)

        notes = []
        async for note in notes_collection.find(query).sort("time", -1).skip(offset).limit(limit):
            notes.append(NoteType(
                id = str(note["_id"]),
                time = note["time"],
                tags = note.get("tags", []),
                title = note["title"],
                content = note["content"]
            ))
        return NotesResult(total_count=total, notes=notes)
    
    @strawberry.field
    async def top_tags(self, info, limit: int = 10) -> List[str]:
        user = info.context["user"]
        pipeline = [
            {"$match": {"owner": user}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        result = await notes_collection.aggregate(pipeline).to_list(length=limit)
        return [item["__id"] for item in result]
    
schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
