# server.py
import asyncio
import signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from src.utils.shared_resources import EVENT_BUS
from src.utils.logger import setup_logging
from src.api.websocket_conn import AssistantBackend
from src.assistant.main import Assistant
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logger = setup_logging(module_name="API_Handler")

# Create the assistant backend
assistant_backend = AssistantBackend(event_bus=EVENT_BUS)

# Track background tasks
background_tasks = set()
assistant_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global assistant_instance
    
    # Create the assistant but modify to run user_input_loop as a background task
    assistant_instance = await Assistant.create()
    
    processing_task = await assistant_instance.start_processing()
    background_tasks.add(processing_task)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler():
        logger.info("Shutdown signal received")
        asyncio.create_task(shutdown())
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, signal_handler)
        
    logger.info("Assistant initialized successfully")
    yield
    
    # Cleanup code
    logger.info("Server shutting down")
    await shutdown()

async def shutdown():
    """Clean shutdown of all resources"""
    global assistant_instance
    logger.info("Executing shutdown sequence")
    
    # Cancel all background tasks
    for task in background_tasks:
        task.cancel()
    
    # If assistant has a shutdown method
    if assistant_instance and hasattr(assistant_instance, "central_manager"):
        await assistant_instance.central_manager.shutdown()
    
    logger.info("Shutdown complete")

# Create the FastAPI app with lifespan handler
app = FastAPI(lifespan=lifespan)

# Add WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Add this connection to the assistant_backend
    assistant_backend.active_connections.append(websocket)
    try:
        # Wait for messages from the client
        while True:
            await asyncio.sleep(1)  # Keep connection alive
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Remove connection when done
        if websocket in assistant_backend.active_connections:
            assistant_backend.active_connections.remove(websocket)
        await websocket.close()
        
# This file can be run with: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload