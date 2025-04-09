# In src/api/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from src.api.websocket_conn import AssistantBackend
from src.utils.shared_resources import EVENT_BUS
from src.utils.logger import setup_logging

# Create the FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Create the assistant backend
assistant_backend = AssistantBackend(event_bus=EVENT_BUS)
logger = setup_logging(module_name="API_Handler")

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Add WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    try:
        await assistant_backend.connect(websocket)
        while True:
            try:
                # Wait for messages from the client
                data = await websocket.receive_text()
                await assistant_backend.handle_message(websocket, data)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await assistant_backend.disconnect(websocket)