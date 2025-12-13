import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI()


messages = [
    {"role": "system", "content": "Eres un asistente útil que habla en español."},
]

async def main():
    while True:
        prompt = input("Tú: ").strip()
        if not prompt:
            continue

        if prompt.lower() in {"salir", "exit", "quit", "bye"}:
            print("Saliendo del chat. ¡Hasta luego!")
            break
    
        messages.append({"role": "user", "content": prompt})
        print("Esperando respuesta del asistente...")
    
        stream = await client.responses.create(
            model="gpt-4o",
            input=messages,
            max_output_tokens=2048,
            stream=True,
        )
        print("Asistente: \n")
        
        async for event in stream:
            if event.type == "response.output_text.delta":
                print(event.delta, flush=True, end="")

            elif event.type == "response.output_text.done":
                print()

            elif event.type == "response.done":
                break


        # assistant_message = response.output_text
        # messages.append({"role": "assistant", "content": assistant_message})

        # print("Asistente:", assistant_message)

if __name__ == "__main__":
    asyncio.run(main())