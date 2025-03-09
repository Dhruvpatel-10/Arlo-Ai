import asyncio
from typing import Optional, Any
from src.audio.record import AudioRecorder
from src.speech.stt.whisper_engine import WhisperEngine
from src.wake_word.porcupine_detector import WakeWordDetector
from src.wake_word.wake_manager import WakeWordManager
from src.core.event_bus import EventBus, EventPriority
from src.core.state import StateManager, AssistantState
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
        self.logger = setup_logging()
        
        # Initialize components
        self.wake_detector = WakeWordDetector(event_bus=event_bus, state_manager=state_manager)
        self.audio_recorder = AudioRecorder(event_bus=event_bus, sample_rate=16000, channels=1, pre_roll_duration=2, max_queue_size=10)
        self.whisper_engine = WhisperEngine()
        self.wake_manager = WakeWordManager(event_bus, state_manager)
        self.transcription = None

    @classmethod
    async def create(cls, event_bus: EventBus, state_manager: StateManager) -> 'CentralAudioManager':
        """
        Create and initialize a new CentralAudioManager instance.
        
        Args:
            event_bus (EventBus): Event bus for system-wide communication
            state_manager (StateManager): State manager for tracking assistant state
            
        Returns:
            CentralAudioManager: An initialized instance of CentralAudioManager
            
        Raises:
            Exception: If initialization fails
        """
        instance = cls(event_bus, state_manager)
        await instance._initialize()
        return instance

    async def _initialize(self):
        """Initialize all components with proper error handling"""
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(
                    self.wake_detector.initialize(),
                    name="init_wake_detector"
                )
                tg.create_task(
                    self.audio_recorder.initialize(),
                    name="init_audio_recorder"
                )
                tg.create_task(
                    self.whisper_engine.initialize(),
                    name="init_whisper_engine"
                )
                
            # Set up event handlers after components are initialized
            self._setup_event_handlers()
            self.logger.info("All components initialized successfully")
            
        except* Exception as eg:
            self.logger.error(f"Failed to initialize components: {eg}")
            await self.shutdown()
            raise

    async def shutdown(self):
        """Shutdown and cleanup all components safely"""
        components = [
            self.wake_detector,
            self.audio_recorder,
            self.whisper_engine,
            self.wake_manager,
            self.event_bus,
            self.state_manager
        ]
        
        cleanup_tasks = [
            asyncio.create_task(
                component.shutdown(),
                name=f"shutdown_{component.__class__.__name__}"
            )
            for component in components
            if component is not None and hasattr(component, 'shutdown')
        ]
        
        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                self.logger.error(f"Error during component cleanup: {e}")

    def _setup_event_handlers(self):
        """Set up event handlers for coordinating audio processing flow"""

        self.event_bus.subscribe("start.wakeword.detection", self._handle_wake_word_detected, priority=EventPriority.HIGH, async_handler=True)
        self.event_bus.subscribe("start.audio.recording", self._handle_audio_recorded, priority=EventPriority.HIGH, async_handler=True)
        self.event_bus.subscribe("utterance_ready", self._handle_transcription_complete, priority=EventPriority.HIGH, async_handler=True)

    async def _handle_wake_word_detected(self):
        """Handle wake word detection by starting audio recording"""
        try:
            self.logger.info("Starting wake word detection...")
            await self.event_bus.publish("wakeword.start_detection")
        except Exception as e:
            raise e
        
    async def _handle_audio_recorded(self):
        """Handle recorded audio by sending it for transcription"""
        if await self.state_manager.get_state() == AssistantState.LISTENING:
            self.logger.info("State: LISTENING - Recording audio...")
            await self.event_bus.publish("audio.record.request")
            utterance = None
            while utterance is None:
                utterance = await self.audio_recorder.get_audio_data()
                await asyncio.sleep(0.2)
            await self.event_bus.publish("utterance_ready", utterance)

    async def _handle_transcription_complete(self, utterance: Optional[Any] = None):
        """Handle completed transcription"""
        self.logger.info("State: PROCESSING – Transcribing audio...")
        transcription = await self.whisper_engine.transcribe_audio(utterance)
        await self.event_bus.publish("transcription_complete", transcription)
        self.logger.debug(f"Transcription completed: {transcription}")