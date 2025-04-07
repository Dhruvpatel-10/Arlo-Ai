from faster_whisper import WhisperModel
import numpy as np
from src.utils.logger import setup_logging
from src.llm.model import groq_prompt, sys_msg
from src.speech.tts.tts_manager import TTSManager
from src.core.state import AssistantState, StateManager
import os
import io

class TranscriptionHandler:
    def __init__(self, event_bus):
        self.logger = setup_logging(module_name="Transcription_Handler")
        self.event_bus = event_bus
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        self.state_manager = StateManager()
        self.tts_manager = TTSManager(event_bus=self.event_bus, state_manager=self.state_manager)
        self.setup_handlers()
        self.logger.info("Transcription handler initialized with base model")

    def setup_handlers(self):
        """Set up event handlers"""
        self.event_bus.subscribe(
            topic_name="audio.transcribe",
            callback=self._handle_audio,
            async_handler=True
        )
        self.event_bus.subscribe(
            topic_name="transcription.result",
            callback=self._handle_transcription_result,
            async_handler=True
        )

    async def _handle_audio(self, audio_data: np.ndarray) -> None:
        """Handle incoming audio data"""
        try:
            if audio_data is None or len(audio_data) == 0:
                self.logger.warning("Received empty audio data")
                return

            # Convert bytes to numpy array if needed
            if isinstance(audio_data, bytes):
                self.logger.debug("Converting bytes to numpy array")
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
            elif isinstance(audio_data, np.ndarray):
                self.logger.debug("Using numpy array directly")
                audio_array = audio_data
            else:
                self.logger.error(f"Unsupported audio data type: {type(audio_data)}")
                return

            # Convert to float32 and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0

            # Log audio data properties
            self.logger.info(f"Processing audio: shape={audio_float.shape}, dtype={audio_float.dtype}")

            # Only proceed if we're in LISTENING state
            current_state = await self.state_manager.get_state()
            if current_state != AssistantState.LISTENING:
                self.logger.warning(f"Ignoring audio in state: {current_state}")
                return

            # Transcribe
            segments, info = self.model.transcribe(
                audio_float,
                language="en",
                vad_filter=True,
                without_timestamps=True
            )

            # Log simplified transcription info
            self.logger.info(
                f"Transcription stats: duration={info.duration:.2f}s, "
                f"duration_after_vad={info.duration_after_vad:.2f}s, "
                f"language={info.language}"
            )

            # Get transcription text
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                self.logger.info(f"Transcribed text: {text}")
                await self.state_manager.set_state(AssistantState.PROCESSING)
                
                # Send user's transcription to frontend
                await self.event_bus.publish(
                    topic_name="transcription.result",
                    data=text
                )
            else:
                self.logger.info("No speech detected in audio")
                # Only go back to IDLE if we're still in LISTENING state
                current_state = await self.state_manager.get_state()
                if current_state == AssistantState.LISTENING:
                    await self.state_manager.set_state(AssistantState.IDLE)
                    await self.event_bus.publish("start.wakeword.detection")
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}", exc_info=True)
            await self.event_bus.publish(
                topic_name="error",
                data=f"Transcription error: {str(e)}"
            )
            # Only go back to IDLE if we're in LISTENING state
            current_state = await self.state_manager.get_state()
            if current_state == AssistantState.LISTENING:
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.event_bus.publish("start.wakeword.detection")

    async def _handle_transcription_result(self, text: str) -> None:
        """Handle transcription result and get assistant response"""
        try:
            if not text or not isinstance(text, str):
                self.logger.warning("Invalid transcription text")
                current_state = await self.state_manager.get_state()
                if current_state == AssistantState.PROCESSING:
                    await self.state_manager.set_state(AssistantState.IDLE)
                    await self.event_bus.publish("start.wakeword.detection")
                return
                
            self.logger.info(f"Processing transcription result: {text}")
            # State should already be PROCESSING from _handle_audio
                
            # Get assistant response
            response = await self._get_assistant_response(text)
            if response:
                self.logger.info(f"Assistant response: {response}")
                # Send response to frontend
                await self.event_bus.publish(
                    topic_name="assistant.response",
                    data=response
                )
                # Trigger TTS playback
                await self.state_manager.set_state(AssistantState.SPEAKING)
                await self.event_bus.publish(
                    topic_name="start.tts.playback",
                    data=response
                )
            else:
                self.logger.warning("No response from assistant")
                await self.state_manager.set_state(AssistantState.IDLE)
                await self.event_bus.publish("start.wakeword.detection")
                
        except Exception as e:
            self.logger.error(f"Error getting assistant response: {e}")
            await self.event_bus.publish(
                topic_name="error",
                data=f"Assistant error: {str(e)}"
            )
            await self.state_manager.set_state(AssistantState.IDLE)
            await self.event_bus.publish("start.wakeword.detection")

    async def _get_assistant_response(self, text: str) -> str:
        """Get response from the assistant using the existing groq_prompt function"""
        try:
            # Use the same system message and configuration as the original assistant
            response = await groq_prompt(
                prompt=text,
                img_context=None,
                function_execution=None
            )
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error in assistant response: {e}")
            raise 