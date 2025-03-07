from enum import Enum
from typing import Dict, Callable
from src.core.event_bus import EventBus, EventPriority
from src.core.state import StateManager, AssistantState
from src.utils.logger import setup_logging

class WakeWordCommand(Enum):
    WAKE = "hey_arlo"
    STOP = "stop_arlo"
    PAUSE = "arlo_pause"
    CONTINUE = "arlo_continue"

class WakeWordManager():
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.logger = setup_logging()
        self.command = None
        
        # Map wake word commands to their handler methods
        self.command_handlers: Dict[WakeWordCommand, Callable] = {
            WakeWordCommand.WAKE: self._handle_wake,
            WakeWordCommand.STOP: self._handle_stop,
            WakeWordCommand.PAUSE: self._handle_pause,
            WakeWordCommand.CONTINUE: self._handle_continue
        }
        
        # Subscribe to wake word detection events
        self.event_bus.subscribe(
            "wake_word_detected",
            self._on_wake_word_detected,
            priority=EventPriority.HIGH,
            async_handler=True
        )
        
        # Subscribe to TTS completion events to update state
        self.event_bus.subscribe(
            "tts_completed",
            self._on_tts_completed,
            priority=EventPriority.MEDIUM,
            async_handler=True
        )

    async def _on_wake_word_detected(self, command: str) -> None:
        """Handle wake word detection events"""
        try:
            # Find the matching command enum
            wake_command = next((cmd for cmd in WakeWordCommand if cmd.value == command), None)
            self.command = wake_command
            if not wake_command:
                self.logger.warning(f"Invalid wake word command received: {command}")
                return
            
            # Get current state before handling command
            current_state = await self.state_manager.get_state()
            self.logger.info(f"Wake word '{command}' detected while in state: {current_state}")
            
            # Only process the command if it's valid for the current state
            if self._is_command_valid_for_state(wake_command, current_state):
                handler = self.command_handlers.get(wake_command)
                await handler()
            else:
                self.logger.info(f"Ignoring '{command}' command in current state: {current_state}")
                
        except Exception as e:
            self.logger.error(f"Error handling wake word command: {e}")
    
    def _is_command_valid_for_state(self, command: WakeWordCommand, state: AssistantState) -> bool:
        """Check if a wake word command is valid for the current state"""
        # State-specific command validation
        if command == WakeWordCommand.WAKE:
            # Hey Arlo is only valid when IDLE or PAUSED
            return state in [AssistantState.IDLE, AssistantState.PAUSED]
        
        elif command == WakeWordCommand.STOP:
            # Stop is valid in any active state
            return state not in [AssistantState.IDLE]
        
        elif command == WakeWordCommand.PAUSE:
            # Pause is only valid when actively speaking
            return state == AssistantState.SPEAKING
        
        elif command == WakeWordCommand.CONTINUE:
            # Continue is only valid when paused
            return state == AssistantState.PAUSED
        
        return False
                
    async def _handle_wake(self) -> None:
        """Handle 'Hey Arlo' command"""
        current_state = await self.state_manager.get_state()
        if current_state in [AssistantState.IDLE, AssistantState.PAUSED]:
            await self.state_manager.set_state(AssistantState.LISTENING)
            await self.event_bus.publish("hey_arlo_detected")
            self.logger.info("Activated assistant with 'Hey Arlo'")

    async def _handle_stop(self) -> None:
        """Handle 'Stop Arlo' command"""
        current_state = await self.state_manager.get_state()
        if current_state != AssistantState.IDLE:
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.event_bus.publish("stop_arlo_detected")
            self.logger.info("Stopped assistant with 'Stop Arlo'")

    async def _handle_pause(self) -> None:
        """Handle 'Arlo Pause' command"""
        current_state = await self.state_manager.get_state()
        if current_state == AssistantState.SPEAKING:
            await self.state_manager.set_state(AssistantState.PAUSED)
            await self.event_bus.publish("arlo_pause_detected")
            self.logger.info("Paused assistant with 'Arlo Pause'")

    async def _handle_continue(self) -> None:
        """Handle 'Arlo Continue' command"""
        current_state = await self.state_manager.get_state()
        if current_state == AssistantState.PAUSED:
            await self.state_manager.set_state(AssistantState.SPEAKING)
            await self.event_bus.publish("arlo_continue_detected")
            self.logger.info("Continued assistant with 'Arlo Continue'")
    
    async def _on_tts_completed(self) -> None:
        """Handle TTS completion by transitioning back to IDLE state"""
        current_state = await self.state_manager.get_state()
        if current_state == AssistantState.SPEAKING:
            await self.state_manager.set_state(AssistantState.IDLE)
            self.logger.info("TTS completed, returning to IDLE state")