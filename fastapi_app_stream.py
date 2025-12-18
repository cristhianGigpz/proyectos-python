import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI()
app = FastAPI(title= "Chatbot API con FastAPI y OpenAI (streaming)")

# Habilitar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list | None = None


async def stream_chat_response(history: list):
    async with client.responses.stream(
        model="gpt-4.1",
        prompt={
            "id": "pmpt_69039a0eca4c8193b8387ef187112b3c0b7c145f0376397d",
            "version": "2"
        },
        input=history,
        text={
            "format": {
            "type": "text"
            }
        },
        reasoning={},
        tools=[
            {
            "type": "file_search",
            "vector_store_ids": [
                "vs_69039889c3e48191aa4ea7cba52f1d06"
            ]
            }
        ],
        max_output_tokens=2048,
        store=True,
        include=["web_search_call.action.sources"]
    ) as stream:
        async for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
                await asyncio.sleep(0)  # Yield control to the event loop
            

@app.post("/chat/stream")
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message.strip()

    history = req.history or [
        {"role": "system", "content": "Eres un asistente legal especializado en derechos constitucionales. Basa tu respuestas ÚNICAMENTE en el documento adjunto \"constitución política del Perú\" y documentos adjuntos. Si la información no esta disponible en los documentos, responde que no se encuentra disponible."},
    ]

    if not user_msg:
        return {"error": "El mensaje no puede estar vacío."}
    
    history.append({"role": "user", "content": "muestra el articulo o ley donde especifica lo consultado"})
    history.append({"role": "user", "content": user_msg})

    return StreamingResponse(
        stream_chat_response(history),
        media_type="text/plain"
    )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app_stream:app", host="0.0.0.0", port=8000, reload=True)

"""
curl -N -X POST http://localhost:8000/chat/stream \
-H "Content-Type: application/json" \
-d '{"message": "Explícame async y await en Python"}'
"""