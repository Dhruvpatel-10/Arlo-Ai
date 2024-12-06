import os
import sys
from asyncio import run
from dotenv import load_dotenv
load_dotenv() 

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_path)

from assistant.main import main

if __name__ == "__main__":
    run(main())