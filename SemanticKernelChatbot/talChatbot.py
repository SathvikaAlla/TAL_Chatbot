# main.py
import asyncio
import logging
from dotenv import load_dotenv
from lampPlugin import LampCompatibilityPlugin
from chatPlugin import LampChatService

load_dotenv()

async def main():
    logging.basicConfig(
    format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
    
    logging.getLogger("kernel").setLevel(logging.DEBUG)

    chat_service = LampChatService()
    history = chat_service.history
    history.clear()  # Clear any previous history
    
    while True:
        try:
            query = input("User: ")
            if query.lower() in ["exit", "quit"]:
                break

            history.add_user_message(query)
        
            response = await chat_service.get_response(query)
            print(f"\nAssistant: {response}\n")
            
            history.add_message({"role": "assistant", "content": str(response)})
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(main())

