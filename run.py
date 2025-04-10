import asyncio
import argparse
import sys
from dotenv import load_dotenv
load_dotenv()
from src.assistant.main import Assistant

async def run_assistant_only():
    """Run the assistant without the web server"""
    assistant = await Assistant.create()
    # Make sure the assistant keeps running
    try:
        # Get the processing task and await it to keep the assistant running
        processing_task = await assistant.start_processing()
        await processing_task
    except KeyboardInterrupt:
        print("Shutting down assistant...")

def run_server(host="0.0.0.0", port=8000, reload=True):
    """Start the uvicorn server directly in the current shell"""
    reload_flag = "--reload" if reload else ""
    cmd = f"uvicorn src.api.server:app --host {host} --port {port} {reload_flag}"
    print(f"Starting server with command: {cmd}")
    
    # Use os.system or subprocess.call to run in the foreground
    import os
    try:
        # This will block until the command completes or is interrupted
        os.system(cmd)
    except KeyboardInterrupt:
        print("Shutting down server...")
        sys.exit(0)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the assistant with or without the server")
    parser.add_argument("--no-server", action="store_true", help="Run the assistant without starting the server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload of the server")
    
    args = parser.parse_args()
    
    if args.no_server:
        # Run only the assistant
        print("Running assistant without server...")
        asyncio.run(run_assistant_only())
    else:
        # Run the server with the assistant
        print("Starting server with assistant...")
        run_server(host=args.host, port=args.port, reload=not args.no_reload)

if __name__ == "__main__":
    main()