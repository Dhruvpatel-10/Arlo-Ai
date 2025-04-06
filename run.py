from asyncio import run
from dotenv import load_dotenv
load_dotenv() 

from src.assistant.main import Assistant


async def main():
    await Assistant.create()

if __name__ == "__main__":
    run(main())