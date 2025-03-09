from enum import Enum
import asyncio
import traceback
from typing import Protocol, List
from src.utils.logger import setup_logging

class AssistantState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    PAUSED = "paused"

class StateObserver(Protocol):
    """Protocol for state change observers"""
    async def on_state_change(self, old_state: AssistantState, new_state: AssistantState) -> None:
        """Called when the state changes"""
        ...

class StateManager:
    # Define valid state transitions as a class variable since it's constant
    _valid_transitions = {
        AssistantState.IDLE: [AssistantState.LISTENING, AssistantState.PAUSED],
        AssistantState.LISTENING: [AssistantState.PROCESSING, AssistantState.IDLE, AssistantState.PAUSED],
        AssistantState.PROCESSING: [AssistantState.SPEAKING, AssistantState.IDLE, AssistantState.PAUSED],
        AssistantState.SPEAKING: [AssistantState.IDLE, AssistantState.LISTENING, AssistantState.PAUSED],
        AssistantState.PAUSED: [AssistantState.IDLE, AssistantState.LISTENING, AssistantState.PROCESSING, AssistantState.SPEAKING]
    }

    def __init__(self):
        self.current_state = AssistantState.IDLE
        self._lock = asyncio.Lock()
        self.logger = setup_logging()
        self._observers: List[StateObserver] = []
    
    def add_observer(self, observer: StateObserver) -> None:
        """Add an observer to be notified of state changes"""
        if observer not in self._observers:
            self._observers.append(observer)
            self.logger.debug(f"Added state observer: {observer.__class__.__name__}")
    
    def remove_observer(self, observer: StateObserver) -> None:
        """Remove an observer from the notification list"""
        if observer in self._observers:
            self._observers.remove(observer)
            self.logger.debug(f"Removed state observer: {observer.__class__.__name__}")

    async def _notify_observers(self, old_state: AssistantState, new_state: AssistantState) -> None:
        """Notify all observers of a state change"""
        for observer in self._observers:
            try:
                await observer.on_state_change(old_state, new_state)
            except Exception as e:
                self.logger.error(f"Error notifying observer {observer.__class__.__name__}: {e}")

    async def get_state(self) -> AssistantState:
        """Return the current state"""
        return self.current_state
    
    def caller_info(self):
        # Get the caller's stack trace
        stack = traceback.extract_stack()
        caller = stack[-3]
        caller_info = f"{caller.filename}:{caller.lineno}"
        return caller_info
    
    async def set_state(self, new_state: AssistantState) -> bool:
        """
        Change the current state if the transition is valid
        Returns True if state was changed, False otherwise
        """
        caller_info = self.caller_info()
        async with self._lock:
            
            if self.current_state == new_state:
                self.logger.warning(f"Attempted same state transition to {new_state} from {caller_info}")
                return False
                
            if new_state not in self._valid_transitions[self.current_state]:
                self.logger.warning(f"Invalid state transition from {self.current_state} to {new_state} requested by {caller_info}")
                return False
            
            old_state = self.current_state    
            self.current_state = new_state
            self.logger.debug(f"State changed to {self.current_state} by {caller_info}")
            
            # Notify observers of the state change
            await self._notify_observers(old_state, new_state)
            return True