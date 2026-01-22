import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
client = AsyncOpenAI()

SYSTEM_PROMPT = """
Eres un asistente legal especializado en derecho peruano.
Responde únicamente usando la Constitución del Perú y normas legales vigentes.
Si no hay información, responde que no se encuentra disponible.
"""


@app.websocket("/chat/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        user_message = data.get("message")

        history = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "muestra el articulo o ley donde especifica lo consultado",
            },
            {"role": "user", "content": user_message},
        ]

        async with client.responses.stream(
            model="gpt-4.1",
            prompt={
                "id": "pmpt_69039a0eca4c8193b8387ef187112b3c0b7c145f0376397d",
                "version": "2",
            },
            input=history,
            text={"format": {"type": "text"}},
            reasoning={},
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": ["vs_69039889c3e48191aa4ea7cba52f1d06"],
                }
            ],
            max_output_tokens=2048,
            store=True,
            include=["web_search_call.action.sources"],
        ) as stream:
            async for event in stream:
                if event.type == "response.output_text.delta":
                    await websocket.send_text(event.delta)

        await websocket.send_text("[DONE]")

    except WebSocketDisconnect:
        print("🔴 Cliente desconectado")

    except Exception as e:
        await websocket.send_text(f"❌ Error: {str(e)}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_app_ws:app", host="0.0.0.0", port=8000, reload=True)
