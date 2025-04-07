# In src/api/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from src.api.websocket_conn import AssistantBackend
from src.api.transcription_handler import TranscriptionHandler
from src.audio.central_manager import CentralAudioManager
from src.utils.shared_resources import EVENT_BUS
from src.utils.logger import setup_logging

# Create the FastAPI app
app = FastAPI()

# Add CORS middleware with more permissive settings for development
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the handlers
assistant_backend = AssistantBackend(event_bus=EVENT_BUS)
transcription_handler = TranscriptionHandler(event_bus=EVENT_BUS)
central_manager = CentralAudioManager()  # Initialize here
logger = setup_logging(module_name="API_Handler")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming {request.method} request to {request.url}")
    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    try:
        logger.info("Starting up backend server...")
        
        # Initialize components
        await central_manager._initialize()
        logger.info("Backend setup completed")
        
        # Start wake word detection
        await EVENT_BUS.publish("wakeword.start")
        logger.info("Wake word detection initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down backend server...")
        await central_manager.shutdown()
        logger.info("Backend shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Add WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    try:
        await websocket.accept()
        logger.info("New WebSocket connection received")
        logger.info("WebSocket connection accepted")
        
        # Add connection to active connections
        await assistant_backend.connect(websocket)
        logger.info(f"New WebSocket connection added to active connections")
        logger.info(f"Active connections: {len(assistant_backend.active_connections)}")
        
        # Start wake word detection
        await EVENT_BUS.publish("wakeword.start")
        logger.info("Wake word detection started for new connection")
        
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data}")
                
                # Handle the message
                await assistant_backend.handle_client_message(data)
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
            await assistant_backend.disconnect(websocket)
            logger.info(f"WebSocket connection removed. Active connections: {len(assistant_backend.active_connections)}")
            
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        try:
            await websocket.close()
        except:
            pass