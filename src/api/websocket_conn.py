from fastapi import WebSocket
from typing import List
from src.utils.logger import setup_logging
from src.core.event_bus import EventBus

class AssistantBackend:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = setup_logging(module_name="API_Handler")
        self.event_subscriber()
        self.active_connections: List[WebSocket] = []

    async def _get_result(self, transcript: str = None, response: str = None) -> None:
        """Handles event data and sends it to active WebSocket clients"""
        if response is not None:
            self.logger.info(f"Got the response: {response}")
            # Send transcription to all connected clients
            await self.send_to_clients({"type": "response", "data": response})
        
        if transcript is not None:
            self.logger.info(f"Got the transcript: {transcript}")
            # Send transcription to all connected clients
            await self.send_to_clients({"type": "transcription", "data": transcript})

    async def send_to_clients(self, message: dict):
        """Send message to all active WebSocket connections"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.error("Failed to send message: %s", e)

    async def event_subscriber(self) -> None:
        """Subscribe to events and handle them asynchronously"""
        self.event_bus.subscribe(
            topic_name="send.api",
            callback=self._get_result,
            async_handler=True
        )


