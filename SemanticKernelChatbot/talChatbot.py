# main.py
import asyncio
from dotenv import load_dotenv
from chatPlugin import LampChatService

load_dotenv()

async def main():
    chat_service = LampChatService()
    history = []
    
    while True:
        try:
            query = input("User: ")
            if query.lower() in ["exit", "quit"]:
                break
        
            response = await chat_service.get_response(query, history)
            print(f"\nAssistant: {response}\n")
            
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": str(response)})
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(main())
