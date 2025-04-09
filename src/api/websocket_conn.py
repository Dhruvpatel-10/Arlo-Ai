from fastapi import WebSocket
from typing import List
from src.utils.logger import setup_logging
from src.core.event_bus import EventBus
import asyncio
import json

class AssistantBackend:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = setup_logging(module_name="API_Handler")
        self.active_connections: List[WebSocket] = []
        self.message_queue = asyncio.Queue()
        # Start event subscriber in the background
        asyncio.create_task(self.event_subscriber())
        asyncio.create_task(self.message_handler())
        self.logger.info("AssistantBackend initialized")

    async def event_subscriber(self):
        """Subscribe to events and handle them"""
        self.logger.info("Starting event subscriber")
        try:
            while True:
                event = await self.event_bus.get()
                if event:
                    self.logger.info(f"Received event: {event}")
                    await self._get_result(**event)
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
        except Exception as e:
            self.logger.error(f"Event subscriber error: {e}")
            # Restart the subscriber
            asyncio.create_task(self.event_subscriber())

    async def _get_result(self, transcript: str = None, response: str = None) -> None:
        """Handles event data and sends it to active WebSocket clients"""
        try:
            if response is not None:
                self.logger.info(f"Processing response: {response}")
                # First notify we're responding
                await self.message_queue.put({"type": "responding"})
                # Send the response
                await self.message_queue.put({"type": "response", "data": response})
                # Notify response is complete and back to listening
                await self.message_queue.put({"type": "response_complete"})
                self.logger.info("Response processing complete")
            
            if transcript is not None:
                self.logger.info(f"Processing transcript: {transcript}")
                await self.message_queue.put({"type": "transcription", "data": transcript})
        except Exception as e:
            self.logger.error(f"Error in _get_result: {e}")

    async def message_handler(self):
        """Send messages from the queue to all connected clients"""
        self.logger.info("Starting message handler")
        while True:
            try:
                message = await self.message_queue.get()
                self.logger.info(f"Sending message to clients: {message}")
                await self.send_to_clients(message)
                self.message_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error in message handler: {e}")
                await asyncio.sleep(1)  # Wait before retrying

    async def send_to_clients(self, message: dict) -> None:
        """Send message to all connected clients"""
        self.logger.info(f"Sending to {len(self.active_connections)} clients: {message}")
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                self.logger.debug(f"Message sent successfully: {message}")
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for dead_conn in dead_connections:
            try:
                await dead_conn.close()
                self.active_connections.remove(dead_conn)
                self.logger.info("Removed dead connection")
            except Exception as e:
                self.logger.error(f"Error closing dead connection: {e}")

    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"New WebSocket connection accepted. Total connections: {len(self.active_connections)}")
        # Send initial state as listening
        await websocket.send_json({"type": "listening"})
        self.logger.info("Sent initial listening state")

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        try:
            self.active_connections.remove(websocket)
            await websocket.close()
            self.logger.info(f"WebSocket connection closed. Remaining connections: {len(self.active_connections)}")
        except Exception as e:
            self.logger.error(f"Error in disconnect: {e}")

    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming messages from clients"""
        try:
            self.logger.info(f"Received message from client: {message}")
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "connection_check":
                self.logger.info("Received connection check, sending listening state")
                await websocket.send_json({"type": "listening"})
            else:
                self.logger.info(f"Publishing message to event bus: {data}")
                await self.event_bus.publish("send.api", **data)
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
