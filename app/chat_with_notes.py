import os
from openai import AsyncOpenAI
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.get_user import get_current_user
from app.db import get_notes_by_ids, start_chat, append_to_chat, get_chat_by_id, replace_summary

router = APIRouter()

client = AsyncOpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
MAX_MESSAGES = os.getenv("MAX_MESSAGES")
TRIM_KEEP_LAST = os.getenv("TRIM_KEEP_LAST")

class ChatRequest(BaseModel):
    note_ids: list[str]
    question: str

class FollowUpRequest(BaseModel):
    chat_id: str
    question: str

@router.post("/chat_with_notes")
async def chat_with_notes(payload: ChatRequest, user: str = Depends(get_current_user)):
    messages = [{"role": "system", "content": "You are a reflective journaling assistant."}]

    if not payload.note_ids:
        messages.append(
            {"role": "user", "content": f"I dont't have any notes, but here's my question:\n{payload.question}"}
        )
    else:
        notes = await get_notes_by_ids(payload.note_ids)
        notes_str = "\n".join(f"- {note}" for note in notes)
        messages.extend([
            {"role": "user", "content": f"Here are my notes: \n{notes_str}"},
            {"role": "user", "content": payload.question}
        ])

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )

        reply = response.choices[0].message.content.strip()
        chat_id = await start_chat(user, payload.note_ids, payload.question, reply)

        return {"chat_id": chat_id, "reply": reply}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/follow_up")
async def follow_up(payload: FollowUpRequest, user: str = Depends(get_current_user)):
    try:
        chat = await get_chat_by_id(payload.chat_id)

        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        if chat["owner"] != user:
            raise HTTPException(status_code=403, detail="User not authorized")
        
        messages = chat["messages"]

        if len(messages) > int(MAX_MESSAGES):
            old_messages = messages[:-int(TRIM_KEEP_LAST)]
            new_messages = messages[-int(TRIM_KEEP_LAST):]

            new_summary = await summarize_messages(old_messages)

            if "summary" in chat and chat["summary"]:
                combined_summary = await summarize_messages([
                    {"role": "user", "content": f"Earlier summary:\n{chat['summary']}"},
                    {"role": "user", "content": f"New context:\n{new_summary}"}
                ])
            else:
                combined_summary = new_summary

            await replace_summary(payload.chat_id, combined_summary, new_messages)
            messages = new_messages

        messages.append({"role": "user", "content": payload.question})

        gpt_input = []
        if "summary" in chat and chat["summary"]:
            gpt_input.append({"role": "user", "content": f"Here's a summary of our earlier conversastion:\n{chat['summary']}"})
        gpt_input.extend(messages)

        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=gpt_input,
            temperature=0.7,
            max_tokens=800
        )

        reply = response.choices[0].message.content.strip()
        await append_to_chat(payload.chat_id, payload.question, reply)

        return {"chat_id": payload.chat_id, "reply": reply}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get_chat_history/{chat_id}")
async def get_chat_history(chat_id: str, user: str = Depends(get_current_user)):
    chat = await get_chat_by_id(chat_id)

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")  
    if chat["owner"] != user:
        raise HTTPException(status_code=403, detail="User not authorized to access this chat")
    
    return {"chat_id": chat_id, "note_ids": chat["note_ids"], "created_at": chat["created_at"], "messages": chat["messages"]}

async def summarize_messages(messages: list[dict]) -> str:
    formatted = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)
    summary_prompt = [
        {"role": "system", "content": "You are an assistant that summarizes reflective journal conversations."},
        {"role": "user", "content": f"Summarize this conversation briefly:\n\n{formatted}"}
    ]

    response = await client.chat.completions.create(
        model = MODEL_NAME,
        messages = summary_prompt,
        temperature = 0.3,
        max_tokens = 300
    )
    return response.choices[0].message.content.strip()