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
import numpy as np

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
        
        self.transcription = None

    @classmethod
    async def create(cls) -> 'CentralAudioManager':
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
            
            # Start wake word detection
            await self._handle_wake_word_start()
            
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
        # Wake word detection events
        self.event_bus.subscribe(
            "wakeword.detected", 
            self._handle_wake_word_detected,   
            async_handler=True)
        
        self.event_bus.subscribe(
            "start.wakeword.detection", 
            self._handle_wake_word_start, 
            async_handler=True)
        
        self.event_bus.subscribe(
            "wakeword.stop_detection", 
            self._handle_wake_word_stop, 
            async_handler=True)

        # Audio recording events
        self.event_bus.subscribe(
            "start.audio.recording", 
            self._handle_audio_recorded, 
            async_handler=True)
        
        self.event_bus.subscribe(
            "audio.transcribe",
            self._handle_audio_transcribe,
            async_handler=True
        )

        # Transcription events
        self.event_bus.subscribe(
            "transcription.result", 
            self._handle_transcription_complete, 
            async_handler=True)

        # TTS events
        self.event_bus.subscribe(
            "start.tts.playback",
            self._handle_tts_playback,       
            async_handler=True
        )

        self.event_bus.subscribe(
            "tts.completed",
            self._handle_tts_completed,
            async_handler=True
        )

    async def _handle_wake_word_start(self):
        """Handle wake word detection start"""
        try:
            self.logger.info("Starting wake word detection...")
            await self.event_bus.publish("start.wakeword.detection")
            self.logger.info("Wake word detection started successfully")
        except Exception as e:
            self.logger.error(f"Error starting wake word detection: {e}")

    async def _handle_wake_word_stop(self):
        """Handle wake word detection stop"""
        try:
            self.logger.info("Stopping wake word detection...")
            await self.event_bus.publish("wakeword.stop_detection")
            self.logger.info("Wake word detection stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping wake word detection: {e}")

    async def restart_wake_word_detection(self):
        """Helper method to restart wake word detection"""
        try:
            current_state = await self.state_manager.get_state()
            if current_state != AssistantState.IDLE:
                await self.state_manager.set_state(AssistantState.IDLE)
                await asyncio.sleep(0.1)  # Small delay to ensure state is updated
            
            self.logger.info("Restarting wake word detection...")
            await self._handle_wake_word_start()
            self.logger.info("Wake word detection restarted")
        except Exception as e:
            self.logger.error(f"Error restarting wake word detection: {e}")

    async def _handle_wake_word_detected(self):
        """Handle wake word detection by starting audio recording"""
        try:
            self.logger.info("Wake word detected...")
            current_state = await self.state_manager.get_state()
            self.logger.info(f"Current state: {current_state}")
            
            if current_state == AssistantState.IDLE:
                # Stop wake word detection first
                await self._handle_wake_word_stop()
                await asyncio.sleep(0.1)  # Small delay to ensure state is updated
                
                # Set state to LISTENING before starting recording
                await self.state_manager.set_state(AssistantState.LISTENING)
                await self.event_bus.publish("start.audio.recording")
                self.logger.info("Audio recording started")
            else:
                self.logger.info(f"Not starting wake word detection in state: {current_state}")
                
        except Exception as e:
            self.logger.error(f"Error in wake word detection: {e}")
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.restart_wake_word_detection()

    async def _handle_tts_completed(self, *args):
        """Handle TTS completion by restarting wake word detection"""
        try:
            self.logger.info("TTS playback completed")
            current_state = await self.state_manager.get_state()
            self.logger.info(f"Current state before TTS completion: {current_state}")
            
            # Only handle TTS completion if we're in SPEAKING state
            if current_state == AssistantState.SPEAKING:
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()
            else:
                self.logger.warning(f"Unexpected TTS completion in state: {current_state}")
                await self.state_manager.set_state(AssistantState.IDLE)
                
        except Exception as e:
            self.logger.error(f"Error handling TTS completion: {e}")
            await self.state_manager.set_state(AssistantState.IDLE)

    async def _handle_audio_recorded(self):
        """Handle recorded audio by sending it for transcription"""
        try:
            current_state = await self.state_manager.get_state()
            if current_state != AssistantState.LISTENING:
                self.logger.warning(f"Ignoring audio recording in state: {current_state}")
                return

            self.logger.info("Starting audio recording...")
            await self.audio_recorder.start_recording()
            
            # Get audio data with timeout
            timeout = 10  # 10 seconds timeout
            start_time = asyncio.get_event_loop().time()
            
            while True:
                current_state = await self.state_manager.get_state()
                if current_state != AssistantState.LISTENING:
                    self.logger.info(f"Stopped listening - state changed to {current_state}")
                    break
                    
                audio_data = await self.audio_recorder.get_audio_data()
                if audio_data is not None:
                    # Log audio data properties
                    if isinstance(audio_data, bytes):
                        self.logger.info(f"Received audio data: {len(audio_data)} bytes")
                        # Convert bytes to numpy array
                        audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    elif isinstance(audio_data, np.ndarray):
                        self.logger.info(f"Received audio data: shape={audio_data.shape}, dtype={audio_data.dtype}")
                        audio_array = audio_data
                    else:
                        self.logger.error(f"Unsupported audio data type: {type(audio_data)}")
                        continue
                        
                    # Send for transcription
                    self.logger.info("Sending audio data for transcription...")
                    await self.event_bus.publish("audio.transcribe", audio_array)
                    break  # Exit after sending audio data
                
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    self.logger.info(f"Audio recording timeout reached after {elapsed:.2f}s")
                    break
                    
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Error in audio recording: {e}", exc_info=True)
        finally:
            self.logger.info("Stopping audio recording...")
            await self.audio_recorder.stop_recording()
            current_state = await self.state_manager.get_state()
            if current_state == AssistantState.LISTENING:
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()

    async def _handle_audio_transcribe(self, audio_data: np.ndarray) -> None:
        """Handle audio transcription"""
        try:
            if audio_data is None or len(audio_data) == 0:
                self.logger.warning("Empty audio data received")
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()
                return

            # Get current state
            current_state = await self.state_manager.get_state()
            if current_state != AssistantState.LISTENING:
                self.logger.warning(f"Ignoring audio in state: {current_state}")
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()
                return

            # Process audio data
            self.logger.info(f"Processing audio data: shape={audio_data.shape}, dtype={audio_data.dtype}")
            transcription = await self.whisper_engine.transcribe_audio(audio_data)
            
            if transcription:
                self.logger.info(f"Transcription successful: {transcription}")
                await self.state_manager.set_state(AssistantState.PROCESSING)
                await self.event_bus.publish("transcription.result", transcription)
            else:
                self.logger.warning("No transcription result")
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()
            
        except Exception as e:
            self.logger.error(f"Error in audio transcription: {e}")
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.restart_wake_word_detection()

    async def _handle_transcription_complete(self, utterance: Optional[Any] = None):
        """Handle completed transcription"""
        try:
            if not utterance:
                self.logger.warning("Empty utterance received")
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()
                return
                
            self.logger.info(f"Processing transcription: {utterance}")
            
            # Only proceed if we're in PROCESSING state
            current_state = await self.state_manager.get_state()
            if current_state != AssistantState.PROCESSING:
                self.logger.warning(f"Ignoring transcription in state: {current_state}")
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()
                return
            
            # Ensure we have a string for processing
            if isinstance(utterance, dict):
                utterance = utterance.get('text', '')
            elif not isinstance(utterance, str):
                utterance = str(utterance)

            if not utterance:
                self.logger.warning("Empty transcription text")
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.restart_wake_word_detection()
                return
            
            # Send for processing
            await self.event_bus.publish("transcription.result", utterance)
            
        except Exception as e:
            self.logger.error(f"Error in transcription handling: {e}")
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.restart_wake_word_detection()

    async def _handle_tts_playback(self, text: str) -> None:
        """Handle TTS playback"""
        try:
            current_state = await self.state_manager.get_state()
            self.logger.info(f"Starting TTS playback in state {current_state}")
            
            # Only proceed if we're in PROCESSING state
            if current_state != AssistantState.PROCESSING:
                self.logger.warning(f"Cannot start TTS in state: {current_state}")
                await self.state_manager.set_state(AssistantState.IDLE)
                return

            # Ensure we have a string for TTS
            if isinstance(text, dict):
                text = text.get('text', '')
            elif not isinstance(text, str):
                text = str(text)

            if not text:
                self.logger.warning("Empty text received for TTS")
                await self.state_manager.set_state(AssistantState.IDLE)
                return

            # Set state to SPEAKING before starting playback
            await self.state_manager.set_state(AssistantState.SPEAKING)
            self.logger.info(f"Starting TTS playback: {text[:50]}...")
            
            # Publish event with just the text
            await self.event_bus.publish("generate.and.play.audio", text)
                
        except Exception as e:
            self.logger.error(f"Error in TTS playback: {e}")
            await self.state_manager.set_state(AssistantState.IDLE)
