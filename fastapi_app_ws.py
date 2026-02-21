#import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from openai import AsyncOpenAI
from dotenv import load_dotenv

from auth import create_access_token
from models import LoginRequest, TokenResponse
from jose import jwt, JWTError

load_dotenv()

app = FastAPI()
client = AsyncOpenAI()

security = HTTPBearer()

SYSTEM_PROMPT = """
Eres un asistente legal especializado en derecho peruano.
Responde únicamente usando la Constitución del Perú y normas legales vigentes.
Si no hay información, responde que no se encuentra disponible.
"""


@app.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    # ⚠️ SIMULACIÓN DE VALIDACIÓN
    if data.email != "admin@gigpz.com" or data.password != "123456":
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_access_token({"sub": data.email, "role": "user"})

    return {"access_token": token, "token_type": "bearer"}


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, "mi_super_secret_key_gigpz", algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Token inválido")


@app.get("/protected")
def protected_route(user=Depends(verify_token)):
    return {"message": "Ruta protegida", "user": user}


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
        await websocket.close()

    except WebSocketDisconnect:
        print("🔴 Cliente desconectado")

    except Exception as e:
        await websocket.send_text(f"❌ Error: {str(e)}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_app_ws:app", host="0.0.0.0", port=8000, reload=True)
