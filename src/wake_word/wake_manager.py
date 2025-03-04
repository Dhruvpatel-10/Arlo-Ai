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

class WakeWordManager:
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.logger = setup_logging()
        
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

    async def _on_wake_word_detected(self, command: str) -> None:
        """Handle wake word detection events"""
        try:
            # Find the matching command enum
            wake_command = next((cmd for cmd in WakeWordCommand if cmd.value == command), None)
            if not wake_command:
                self.logger.warning(f"Invalid wake word command received: {command}")
                return
                
            handler = self.command_handlers.get(wake_command)
            await handler()
        except Exception as e:
            self.logger.error(f"Error handling wake word command: {e}")

    async def _handle_wake(self) -> None:
        current_state = self.state_manager.get_state()
        if current_state in [AssistantState.IDLE, AssistantState.PAUSED]:
            await self.state_manager.set_state(AssistantState.LISTENING)
            await self.event_bus.publish("hey_arlo_detected")

    async def _handle_stop(self) -> None:
        """Handle 'Stop Arlo' command"""
        current_state = self.state_manager.get_state()
        if current_state != AssistantState.IDLE:
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.event_bus.publish("stop_arlo_detected")

    async def _handle_pause(self) -> None:
        """Handle 'Arlo Pause' command"""
        current_state = self.state_manager.get_state()
        if current_state != AssistantState.PAUSED and current_state != AssistantState.IDLE:
            await self.state_manager.set_state(AssistantState.PAUSED)
            await self.event_bus.publish("arlo_pause_detected")

    async def _handle_continue(self) -> None:
        """Handle 'Arlo Continue' command"""
        current_state = self.state_manager.get_state()
        if current_state == AssistantState.PAUSED:
            await self.state_manager.set_state(AssistantState.SPEAKING)
            await self.event_bus.publish("arlo_continue_detected")

if __name__ == '__main__':
    async def hey():
        print("Yes hey Arlo detected") 
    async def stop():
        print("Yes stop Arlo detected") 
    async def pause():
        print("Yes pause Arlo detected") 
    async def continue1():
        print("Yes cotninue Arlo detected") 

    async def main_loop():
        e = EventBus()
        s = StateManager()
        WakeWordManager(event_bus=e, state_manager=s)

        e.subscribe("hey_arlo_detected", callback=hey, priority=EventPriority.HIGH, async_handler=True)
        e.subscribe("stop_arlo_detected", callback=stop, priority=EventPriority.HIGH, async_handler=True)
        e.subscribe("arlo_pause_detected", callback=pause, priority=EventPriority.HIGH, async_handler=True)
        e.subscribe("arlo_continue_detected", callback=continue1, priority=EventPriority.HIGH, async_handler=True)

        commands = ["hey_arlo", "stop_arlo", "arlo_pause", "arlo_continue"]
        async def publish_command(command: str):
            if command == "arlo_pause":
                await s.set_state(AssistantState.PAUSED)
                await s.set_state(AssistantState.SPEAKING)
            await e.publish("wake_word_detected", command)

        async with asyncio.TaskGroup() as tg:
            for command in commands:
                tg.create_task(publish_command(command))

    import asyncio
    asyncio.run(main_loop())