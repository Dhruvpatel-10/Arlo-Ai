# Revised APIHandler class
import asyncio
from fastapi import FastAPI, WebSocket
from src.utils.logger import setup_logging
from src.api.websocket_conn import AssistantBackend
from src.utils.shared_resources import EVENT_BUS

def create_app():
    app = FastAPI()
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    # Initialize the API handler with the app
    APIHandler(app, EVENT_BUS)
    
    return app

class APIHandler:
    def __init__(self, app: FastAPI, event_bus):
        self.app = app
        self.event_bus = event_bus
        self.logger = setup_logging(module_name="API_Handler")
        self.assistant_backend = AssistantBackend(event_bus=event_bus)
        
        # Register WebSocket route
        self.app.add_api_websocket_route("/ws", self.websocket_endpoint)
        self.logger.info("WebSocket endpoint registered at /ws")

    async def websocket_endpoint(self, websocket: WebSocket) -> None:
        """WebSocket endpoint to manage connections"""
        await websocket.accept()
        self.logger.info("New WebSocket connection accepted")
        await websocket.send_json({"message": "Connected"})
        self.assistant_backend.active_connections.append(websocket)
        
        try:
            while True:
                # Wait for messages from the client
                data = await websocket.receive_text()
                self.logger.info(f"Received message: {data}")
                # You could process messages here or forward them via event_bus
                
                # Keep connection alive
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            self.logger.info("WebSocket connection closed")
            if websocket in self.assistant_backend.active_connections:
                self.assistant_backend.active_connections.remove(websocket)