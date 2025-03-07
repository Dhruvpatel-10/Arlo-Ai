# core/event_bus.py
from typing import Dict, List, Callable
from dataclasses import dataclass, field
from threading import Lock
import asyncio
from enum import Enum, auto
from src.utils.logger import setup_logging
from src.core.error import AssistantError, EventBusError

class EventPriority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()

@dataclass
class Subscriber:
    callback: Callable
    priority: EventPriority = EventPriority.MEDIUM
    async_handler: bool = False

@dataclass
class Topic:
    name: str
    subscribers: List[Subscriber] = field(default_factory=list)

class EventBus:
    def __init__(self):
        self._topics: Dict[str, Topic] = {}
        self._lock = Lock()
        self.logger = None
    
    def subscribe(self, topic_name: str, callback: Callable, 
                 priority: EventPriority = EventPriority.MEDIUM,
                 async_handler: bool = False) -> None:
        """
        Subscribe to a topic with a callback function.
        
        Args:
            topic_name: Name of the topic to subscribe to
            callback: Function to be called when an event is published
            priority: Priority level of the subscriber
            async_handler: Whether the callback is an async function
        """
        with self._lock:
            if topic_name not in self._topics:
                self._topics[topic_name] = Topic(topic_name)
            
            subscriber = Subscriber(callback, priority, async_handler)
            topic = self._topics[topic_name]
            
            # Insert subscriber based on priority
            for i, existing in enumerate(topic.subscribers):
                if existing.priority.value < priority.value:
                    topic.subscribers.insert(i, subscriber)
                    break
            else:
                topic.subscribers.append(subscriber)
            
            self.logger.debug(f"Subscribed to topic '{topic_name}' with priority {priority.name}")

    def unsubscribe(self, topic_name: str, callback: Callable) -> None:
        """
        Unsubscribe a callback from a topic.
        
        Args:
            topic_name: Name of the topic to unsubscribe from
            callback: Function to unsubscribe
        """
        with self._lock:
            if topic_name in self._topics:
                topic = self._topics[topic_name]
                topic.subscribers = [s for s in topic.subscribers if s.callback != callback]
                self.logger.debug(f"Unsubscribed from topic '{topic_name}'")

    async def publish(self, topic_name: str, *args, **kwargs) -> None:
        with self._lock:
            if topic_name not in self._topics:
                raise EventBusError(f"No subscribers for topic '{topic_name}'") 

            subscribers = list(self._topics[topic_name].subscribers)

        for subscriber in subscribers:
            try:
                if subscriber.async_handler:
                    await subscriber.callback(*args, **kwargs)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, subscriber.callback, *args, **kwargs
                    )
            except AssistantError as e:
                raise EventBusError(f"Error in subscriber for topic '{topic_name}'", e) 
            except Exception as e:
                raise EventBusError("Unexpected error in EventBus", e) 

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

# Example usage:
async def example_usage():
    # Create event bus
    event_bus = EventBus()
    
    # Define some handlers
    async def async_handler(message: str):
        print(f"Async handler received: {message}")
    
    def sync_handler(message: str):
        print(f"Sync handler received: {message}")
    
    # Subscribe to topics
    event_bus.subscribe("audio", async_handler, 
                       priority=EventPriority.HIGH, 
                       async_handler=True)
    event_bus.subscribe("command", sync_handler, 
                       priority=EventPriority.MEDIUM)
    await event_bus.publish("audio", "Audio data received")

if __name__ == "__main__":
    asyncio.run(example_usage())