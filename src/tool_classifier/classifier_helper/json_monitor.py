import json
import asyncio
from pathlib import Path
from typing import Callable, Awaitable, Union


class JSONMonitor:
    def __init__(self, file_path: Union[str, Path], callback: Callable[[int], Awaitable[None]] = None, check_interval: int = 20, data_length: int = 50):
        """
        :param file_path: Path to the JSON file.
        :param check_interval: Time interval (in seconds) between checks.
        :param callback: Async function to execute when the condition is met.
        """
        self.file_path = Path(file_path)
        self.callback = callback
        self.check_interval = check_interval
        self.data_length = data_length
        self.running = True
        self.interval_event = asyncio.Event()

    async def check_json(self):
        """Check if JSON file has more than 50 items and trigger the callback."""
        try:
            if self.file_path.exists():
                with self.file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > self.data_length:
                        await self.callback(len(data))  # Call user-defined function
        except Exception as e:
            print(f"Error reading JSON: {e}")

    async def monitor_json(self):
        """Continuously checks JSON file every X seconds."""
        while self.running:
            await self.check_json()

            try:
                await asyncio.wait_for(self.interval_event.wait(), timeout=self.check_interval)
            except asyncio.TimeoutError:
                pass  # Timeout reached, continue looping
            self.interval_event.clear()  # Reset event after timeout

    def adjust_interval(self, new_interval: int):
        """Dynamically adjust the check interval at runtime."""
        self.check_interval = new_interval
        self.interval_event.set()  # Wake up loop to apply new interval

    def stop(self):
        """Stop monitoring."""
        self.running = False
        self.interval_event.set()  # Wake up loop to allow exit
