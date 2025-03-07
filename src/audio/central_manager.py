import asyncio
from typing import Optional, Dict, Any
from src.wake_word.porcupine_detector import WakeWordDetector
from wake_word.wake_manager import WakeWordManager
from src.core.event_bus import EventBus
from src.core.state import StateManager
from src.utils.logger import setup_logging

class CentralAudioManager:
    def __init__(self, 
                 event_bus: EventBus,
                 state_manager: StateManager):
        """
        Initialize the central audio manager
        
        Args:
            event_bus (EventBus): Event bus for system-wide communication
            state_manager (StateManager): State manager for tracking assistant state
        """
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.wake_detector = None
        self.logger = setup_logging()
        
        # Initialize wake word components
        WakeWordDetector()
        WakeWordManager(event_bus, state_manager)
        
        # Audio stream states
        self.is_stt_active = False
        self.is_tts_active = False
        
        # Set up event subscriptions
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """Set up handlers for various audio-related events"""
        self.event_bus.subscribe("start_listening", self._on_start_listening)
        self.event_bus.subscribe("stop_listening", self._on_stop_listening)
        self.event_bus.subscribe("start_speaking", self._on_start_speaking)
        self.event_bus.subscribe("stop_speaking", self._on_stop_speaking)
        
    
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
