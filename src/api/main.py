# In src/api/main.py
from fastapi import FastAPI, WebSocket
import asyncio
from src.api.websocket_conn import AssistantBackend
from src.utils.shared_resources import EVENT_BUS
from src.utils.logger import setup_logging

# Create the FastAPI app
app = FastAPI()

# Create the assistant backend
assistant_backend = AssistantBackend(event_bus=EVENT_BUS)
logger = setup_logging(module_name="API_Handler")

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Add WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to manage connections"""
    await websocket.accept()
    logger.info("New WebSocket connection accepted")
    await websocket.send_json({"message": "Connected"})
    assistant_backend.active_connections.append(websocket)
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            logger.info(f"Received message: {data}")
            # Process messages or forward them via event_bus
            
            # Keep connection alive with minimal sleep
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")
        if websocket in assistant_backend.active_connections:
            assistant_backend.active_connections.remove(websocket)