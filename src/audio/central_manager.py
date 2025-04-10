import asyncio
from typing import Optional, Any
from src.audio.record import AudioRecorder
from src.speech.stt.whisper_engine import WhisperEngine
from src.wake_word.porcupine_detector import WakeWordDetector
from src.wake_word.wake_manager import WakeWordManager
from src.utils.shared_resources import EVENT_BUS, STATE_MANAGER
from src.core.state import StateManager, AssistantState
from src.speech.tts.tts_manager import TTSManager
from src.utils.logger import setup_logging

class CentralAudioManager():
    def __init__(self):
        """
        Initialize the central audio manager
        
        Args:
            event_bus (EventBus): Event bus for system-wide communication
            state_manager (StateManager): State manager for tracking assistant state
        """
        self.event_bus = EVENT_BUS
        self.state_manager = STATE_MANAGER
        self.logger = setup_logging(module_name="CentralAudioManager")

        # Initialize components
        self.wake_detector = WakeWordDetector(event_bus=self.event_bus, state_manager=self.state_manager)
        self.audio_recorder = AudioRecorder(sample_rate=16000, channels=1, pre_roll_duration=2, max_queue_size=10)
        self.whisper_engine = WhisperEngine()
        self.wake_manager = WakeWordManager(event_bus=self.event_bus, state_manager=self.state_manager)

        # Create TTS components
        self.tts_manager = TTSManager(event_bus=self.event_bus, state_manager=self.state_manager)
        self.ServerConnected = False
        self.transcription = None

    @classmethod
    async def create(cls, server_connected: bool = False) -> 'CentralAudioManager':
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
        instance = cls()
        instance.ServerConnected = server_connected
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
        self.logger.info("Shutting down CentralAudioManager...")
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

        self.event_bus.subscribe(
            "start.wakeword.detection", 
            self._handle_wake_word_detected,   
            async_handler=True)
        
        self.event_bus.subscribe(
            "start.audio.recording", 
            self._handle_audio_recorded, 
            async_handler=True)
        
        self.event_bus.subscribe(
            "utterance_ready", 
            self._handle_transcription_complete, 
            async_handler=True)

        self.event_bus.subscribe(
            "start.tts.playback",
            self._handle_tts_playback,       
            async_handler=True
        )

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
            self.logger.info("Get the 'start.audio.recording' event")
            await self.event_bus.publish("audio.record.request")

            try:
                timeout = 10
                start_time = asyncio.get_event_loop().time()
                
                utterance = None
                while utterance is None:
                    utterance = await self.audio_recorder.get_audio_data()
                    
                    # Check if we've exceeded the timeout
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        self.logger.warning(f"Timeout waiting for audio data after {timeout} seconds")
                        # Force stop recording if we time out
                        await self.audio_recorder.stop_recording()
                        await self.state_manager.set_state(AssistantState.IDLE)
                        break
                    await asyncio.sleep(0.2)

                if utterance is not None:
                    self.logger.info("Audio data received, stopping recording")
                    # Ensure recording is stopped before processing
                    await self.event_bus.publish("utterance_ready", utterance)
                else:
                    self.logger.warning("No audio data received")
                    
            except Exception as e:
                self.logger.error(f"Error while handling audio recording: {e}")
                await self.audio_recorder.stop_recording()

    async def _handle_transcription_complete(self, utterance: Optional[Any] = None):
        """Handle completed transcription"""
        self.logger.state("State: PROCESSING – Transcribing audio...")
        transcription = await self.whisper_engine.transcribe_audio(utterance)
        await self.event_bus.publish("get.result", transcript=transcription)
        if self.ServerConnected:
            await self.event_bus.publish("send.api",transcription=transcription)
        self.logger.debug(f"Transcription completed: {transcription}")


    ###############################################################################
    #######                                                                 #######
    #######                     TTS Control Handlers                        #######
    #######                                                                 #######
    ###############################################################################

    async def _handle_tts_playback(self, text: str, voice_name: str = "Ava_Edge") -> None:
        self.logger.debug(f"Publishing 'generate.and.play.audio' event with text: {text[:20]}...")
        await self.event_bus.publish("generate.and.play.audio", text, voice_name)
