import asyncio
from fastapi import WebSocket
from typing import List
from src.utils.logger import setup_logging
from src.core.event_bus import EventBus

class AssistantBackend:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = setup_logging(module_name="API_Handler")
        self.active_connections: List[WebSocket] = []
        asyncio.create_task(self.event_subscriber())

    async def _get_result(self, transcription: str = None, response: str = None) -> None:
        """Handles event data and sends it to active WebSocket clients"""
        if response is not None:
            self.logger.info(f"Got the response: {response}")
            # Send transcription to all connected clients
            await self.send_to_clients({"type": "response", "data": response})
        
        if transcription is not None:
            self.logger.info(f"Got the transcript: {transcription}")
            # Send transcription to all connected clients
            await self.send_to_clients({"type": "transcription", "data": transcription})

    async def send_to_clients(self, message: dict):
        """Send message to all active WebSocket connections"""
        for connection in self.active_connections:
            try:
                # Convert the message format to match what frontend expects
                if message["type"] == "response":
                    await connection.send_json({"response": message["data"]})
                elif message["type"] == "transcription":
                    await connection.send_json({"transcript": message["data"]})
            except Exception as e:
                self.logger.error("Failed to send message: %s", e)

    async def event_subscriber(self) -> None:
        """Subscribe to events and handle them asynchronously"""
        self.event_bus.subscribe(
            topic_name="send.api",
            callback=self._get_result,
            async_handler=True
        )

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        await websocket.close()
