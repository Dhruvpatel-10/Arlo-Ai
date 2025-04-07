from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Set
from src.utils.logger import setup_logging
from src.core.event_bus import EventBus
from src.api.audio_handler import AudioHandler
from src.core.state import AssistantState, StateManager
import asyncio

class AssistantBackend:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = setup_logging(module_name="Assistant_Backend")
        self.active_connections: Set[WebSocket] = set()
        self.audio_handler = None
        self.is_initialized = False
        self.state_manager = StateManager()
        self.setup_event_handlers()

    async def setup(self):
        """Setup the backend - call this after event loop is running"""
        try:
            self.audio_handler = AudioHandler(self.event_bus)
            self.is_initialized = True
            self.logger.info("AudioHandler initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AudioHandler: {e}")
            self.is_initialized = False

    def setup_event_handlers(self):
        """Set up event handlers for different message types"""
        self.event_bus.subscribe(
            topic_name="transcription.result",
            callback=self._handle_transcription,
            async_handler=True
        )
        self.event_bus.subscribe(
            topic_name="assistant.response",
            callback=self._handle_assistant_response,
            async_handler=True
        )
        self.event_bus.subscribe(
            topic_name="error",
            callback=self._handle_error,
            async_handler=True
        )
        self.event_bus.subscribe(
            topic_name="status",
            callback=self._handle_status,
            async_handler=True
        )
        # Subscribe to wake word events
        self.event_bus.subscribe(
            topic_name="wakeword.detected.manager",
            callback=self._handle_wake_word,
            async_handler=True
        )
        # Subscribe to state changes
        self.event_bus.subscribe(
            topic_name="state.changed",
            callback=self._handle_state_change,
            async_handler=True
        )
        # Subscribe to TTS completion
        self.event_bus.subscribe(
            topic_name="tts.completed",
            callback=self._handle_tts_completed,
            async_handler=True
        )

    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        try:
            # Add to active connections
            self.active_connections.add(websocket)
            self.logger.info("New WebSocket connection added to active connections")
            
            # Send initial status
            await self.send_to_client(websocket, {
                "type": "status",
                "message": "Connected to server",
                "state": "IDLE"
            })
            
        except Exception as e:
            self.logger.error(f"Failed to establish WebSocket connection: {e}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            try:
                await websocket.close()
            except:
                pass

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                self.logger.info("WebSocket connection removed from active connections")
                
            # Notify other clients about disconnection
            await self.send_to_clients({
                "type": "status",
                "message": "Client disconnected",
                "connections": len(self.active_connections)
            })
            
        except Exception as e:
            self.logger.error(f"Error during WebSocket disconnection: {e}")

    async def send_to_client(self, websocket: WebSocket, message: dict) -> bool:
        """Send message to a specific client, return success status"""
        try:
            if websocket in self.active_connections:
                await websocket.send_json(message)
                return True
            return False
        except WebSocketDisconnect:
            await self.disconnect(websocket)
            return False
        except Exception as e:
            self.logger.error(f"Failed to send message to client: {e}")
            await self.disconnect(websocket)
            return False

    async def handle_client_message(self, message: dict) -> None:
        """Handle messages from the client"""
        try:
            if not self.is_initialized:
                self.logger.error("Backend not initialized")
                await self.send_to_clients({
                    "type": "error",
                    "message": "Server not ready"
                })
                return

            if message.get("type") == "start_listening":
                self.logger.info("Starting audio recording")
                await self.audio_handler.start_recording()
                await self.send_to_clients({
                    "type": "status",
                    "message": "Started listening"
                })
            elif message.get("type") == "stop_listening":
                self.logger.info("Stopping audio recording")
                self.audio_handler.stop_recording()
                await self.send_to_clients({
                    "type": "status",
                    "message": "Stopped listening"
                })
        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")
            await self.send_to_clients({
                "type": "error",
                "message": f"Error handling request: {str(e)}"
            })

    async def _handle_wake_word(self, command: str) -> None:
        """Handle wake word detection events"""
        try:
            current_state = await self.state_manager.get_state()
            self.logger.info(f"Wake word detected: {command} (current state: {current_state})")
            
            if current_state != AssistantState.IDLE:
                self.logger.info(f"Ignoring wake word in state: {current_state}")
                return
                
            # Send status to clients first
            await self.send_to_clients({
                "type": "status",
                "message": f"Wake word detected: {command}",
                "state": "LISTENING"
            })
            
            # Let the wake word manager handle the state transition and recording
            # It will trigger state changes and start recording
            
        except Exception as e:
            self.logger.error(f"Error handling wake word: {e}")
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.restart_wake_word_detection()

    async def restart_wake_word_detection(self):
        """Helper method to safely restart wake word detection"""
        try:
            self.logger.info("Restarting wake word detection...")
            # Only stop if not already in IDLE state
            current_state = await self.state_manager.get_state()
            if current_state != AssistantState.IDLE:
                await self.event_bus.publish("wakeword.stop_detection")
                await asyncio.sleep(0.2)  # Small delay to ensure cleanup
            
            await self.event_bus.publish("start.wakeword.detection")
            self.logger.info("Wake word detection restarted")
        except Exception as e:
            self.logger.error(f"Error restarting wake word detection: {e}")

    async def _handle_state_change(self, state: AssistantState) -> None:
        """Handle assistant state changes"""
        try:
            self.logger.info(f"State changing to: {state}")
            message = ""
            
            if state == AssistantState.IDLE:
                message = "Waiting for wake word..."
                # Ensure wake word detection is started
                await self.restart_wake_word_detection()
                
            elif state == AssistantState.LISTENING:
                message = "Listening..."
                # Wake word detection should be stopped by wake manager
                
            elif state == AssistantState.PROCESSING:
                message = "Processing..."
                # Make sure recording is stopped
                if self.audio_handler:
                    self.audio_handler.stop_recording()
                
            elif state == AssistantState.SPEAKING:
                message = "Speaking..."
                
            elif state == AssistantState.PAUSED:
                message = "Paused..."

            # Send status update to clients
            await self.send_to_clients({
                "type": "status",
                "message": message,
                "state": state.value
            })
            
        except Exception as e:
            self.logger.error(f"Error handling state change: {e}")
            # Try to recover by going back to IDLE state
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.restart_wake_word_detection()

    async def _handle_tts_completed(self) -> None:
        """Handle TTS completion"""
        try:
            self.logger.info("TTS completed")
            current_state = await self.state_manager.get_state()
            self.logger.info(f"Current state before TTS completion: {current_state}")
            
            # Set state to IDLE
            await self.state_manager.set_state(AssistantState.IDLE)
            
            # Notify clients
            await self.send_to_clients({
                "type": "status",
                "message": "Waiting for wake word...",
                "state": "IDLE"
            })
            
            # Restart wake word detection
            await self.restart_wake_word_detection()
            
        except Exception as e:
            self.logger.error(f"Error handling TTS completion: {e}")
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.restart_wake_word_detection()

    async def _handle_transcription(self, data: str) -> None:
        """Handle transcription results from the event bus"""
        if data and isinstance(data, str) and data.strip():
            self.logger.info(f"Sending transcription: {data}")
            await self.send_to_clients({
                "type": "transcription",
                "text": data
            })

    async def _handle_assistant_response(self, data: str) -> None:
        """Handle assistant responses"""
        if data and data.strip():
            self.logger.info(f"Sending assistant response: {data}")
            await self.send_to_clients({
                "type": "assistant_response",
                "text": data
            })

    async def _handle_error(self, data: str) -> None:
        """Handle error messages"""
        self.logger.error(f"Error occurred: {data}")
        await self.send_to_clients({
            "type": "error",
            "message": data
        })

    async def _handle_status(self, data: str) -> None:
        """Handle status messages"""
        self.logger.info(f"Status update: {data}")
        await self.send_to_clients({
            "type": "status",
            "message": data
        })

    async def send_to_clients(self, message: dict) -> None:
        """Send message to all active WebSocket connections"""
        if not self.active_connections:
            self.logger.debug("No active WebSocket connections")
            return

        # Create a copy of the set to avoid modification during iteration
        connections = self.active_connections.copy()
        dead_connections = set()

        for websocket in connections:
            try:
                if websocket in self.active_connections:  # Double check it's still active
                    await websocket.send_json(message)
            except WebSocketDisconnect:
                dead_connections.add(websocket)
            except Exception as e:
                self.logger.error(f"Error sending message to client: {e}")
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(websocket)


