from enum import Enum
from typing import Protocol, List
import asyncio
from src.utils.logger import setup_logging

class AssistantState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    PAUSED = "paused"

class StateObserver(Protocol):
    async def on_state_change(self, new_state: AssistantState, *args) -> None:
        """Handle state change events"""
        pass

class StateManager:
    def __init__(self):
        self.current_state = AssistantState.IDLE
        self.observers: List[StateObserver] = []
        self._lock = asyncio.Lock()
        self.logger = None
        # Define valid state transitions
        self.valid_transitions = {
            AssistantState.IDLE: [AssistantState.LISTENING, AssistantState.PAUSED],
            AssistantState.LISTENING: [AssistantState.PROCESSING, AssistantState.IDLE, AssistantState.PAUSED],
            AssistantState.PROCESSING: [AssistantState.SPEAKING, AssistantState.IDLE, AssistantState.PAUSED],
            AssistantState.SPEAKING: [AssistantState.IDLE, AssistantState.LISTENING, AssistantState.PAUSED],
            AssistantState.PAUSED: [AssistantState.IDLE, AssistantState.LISTENING, AssistantState.PROCESSING, AssistantState.SPEAKING]
        }
    
    async def get_state(self) -> AssistantState:
        """Return the current state"""
        return self.current_state
    
    async def set_state(self, new_state: AssistantState) -> bool:
        """
        Change the current state if the transition is valid
        Returns True if state was changed, False otherwise
        """
        async with self._lock:
            if new_state not in self.valid_transitions[self.current_state]:
                self.logger.warning(f"Invalid state transition from {self.current_state} to {new_state}")
                return False
                
            self.current_state = new_state
            self.logger.debug(f"State changed to {self.current_state}")
            await self._notify_observers()
            return True
    
    def add_observer(self, observer: StateObserver) -> None:
        """Add an observer to be notified of state changes"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: StateObserver) -> None:
        """Remove an observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    async def _notify_observers(self) -> None:
        """Notify all observers of state change"""
        for observer in self.observers:
            try:
                await observer.on_state_change(self.current_state)
            except Exception as e:
                print(f"Error notifying observer {observer}: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        self.logger = setup_logging()
        import time
        start_time = time.time()
        # Your initialization logic here
        self.logger.debug(f"Initialization took {time.time() - start_time:.2f} seconds")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass