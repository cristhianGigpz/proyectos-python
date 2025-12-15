#import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI()
app = FastAPI(title= "Chatbot API con FastAPI y OpenAI")

class ChatRequest(BaseModel):
    message: str
    history: list | None = None

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message.strip()

    history = req.history or [
        {"role": "system", "content": "Eres un asistente útil que habla en español."},
    ]

    if not user_msg:
        return {"error": "El mensaje no puede estar vacío."}
    
    history.append({"role": "user", "content": user_msg})

    response = await client.responses.create(
        model="gpt-4o",
        input=history,
        max_output_tokens=2048,
    )

    assintant_replay = response.output_text
    history.append({"role": "assistant", "content": assintant_replay})

    return {
        "reply": assintant_replay
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)