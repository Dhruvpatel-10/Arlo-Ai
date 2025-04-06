# core/event_bus.py
import time
import asyncio
from threading import Lock
from collections import defaultdict
from typing import Dict, List, Callable, Optional
from src.utils.helpers import GenericUtils, TimeUtils
from dataclasses import dataclass, field
from src.utils.logger import setup_logging

@dataclass
class Subscriber:
    callback: Callable
    async_handler: bool = False
    last_called: float = field(default_factory=lambda: 0.0)
    call_count: int = 0

@dataclass
class Topic:
    name: str
    subscribers: Dict[int, Subscriber] = field(default_factory=dict)
    subscriber_order: List[int] = field(default_factory=list)
    last_published: float = field(default_factory=lambda: 0.0)
    
    def __post_init__(self):
        self._lock = Lock()  # Per-topic lock for better granularity

class EventBus:
    def __init__(self):
        self._topics: Dict[str, Topic] = {}
        self._lock = Lock()
        self.logger = None
        self._topic_stats: Dict[str, Dict] = defaultdict(lambda: {'publish_count': 0, 'last_publish': 0})
        self._cleanup_threshold = 1000  # Number of empty topic checks before cleanup
        self._empty_topic_count = 0
        self.logger = setup_logging(module_name="Event_Bus")

    
    async def shutdown(self) -> None:
        """
        Cleanup and shutdown the event bus.
        This method should be called when the event bus is no longer needed.
        """
        self._cleanup_empty_topics()
        self._topics.clear()
        if self.logger:
            self.logger.debug("Event bus shut down")

    def subscribe(self, topic_name: str, callback: Callable, async_handler: bool = False) -> None:
        with self._lock:
            if topic_name not in self._topics:
                self._topics[topic_name] = Topic(topic_name)
            
            topic = self._topics[topic_name]
            
        # Use topic-specific lock for better concurrency
        with topic._lock:
            callback_id = id(callback)
            subscriber = Subscriber(callback, async_handler)
            
            # Store the subscriber
            topic.subscribers[callback_id] = subscriber
            
            # Simply append to the subscriber order list
            topic.subscriber_order.append(callback_id)
            
            self.logger.event(f"Subscribed to topic '{topic_name}' and subscribed in {GenericUtils.caller_info()}")

    def unsubscribe(self, topic_name: str, callback: Callable) -> None:
        with self._lock:
            if topic_name not in self._topics:
                return
            
            topic = self._topics[topic_name]
            
        with topic._lock:
            callback_id = id(callback)
            
            if callback_id in topic.subscribers:
                del topic.subscribers[callback_id]
                if callback_id in topic.subscriber_order:
                    topic.subscriber_order.remove(callback_id)
                
                # Check if topic is empty and mark for potential cleanup
                if not topic.subscribers:
                    self._empty_topic_count += 1
                    if self._empty_topic_count >= self._cleanup_threshold:
                        self._cleanup_empty_topics()
                
                if self.logger:
                    self.logger.debug(f"Unsubscribed from topic '{topic_name}'")

    def _cleanup_empty_topics(self) -> None:
        """Remove topics with no subscribers to prevent memory leaks."""
        with self._lock:
            empty_topics = [name for name, topic in self._topics.items() 
                          if not topic.subscribers]
            for topic_name in empty_topics:
                del self._topics[topic_name]
                if self.logger:
                    self.logger.debug(f"Cleaned up empty topic '{topic_name}'")
            self._empty_topic_count = 0

    async def publish(self, topic_name: str, *args, **kwargs) -> List[Exception]:
        """
        Publish an event to a topic with optimized concurrent execution.
        """
        current_time = TimeUtils.get_timestamp()
        caller_info = GenericUtils.caller_info(skip_one_more=True)
        self.logger.event(f"EVENT Publish by '{caller_info}' and '{topic_name}'")
        # Fast path for non-existent topics
        if topic_name not in self._topics:
            if self.logger:
                self.logger.warning(f"No subscribers for topic '{topic_name}'")
            return None

        topic = self._topics[topic_name]

        # Get subscribers with topic-specific lock
        with topic._lock:
            if not topic.subscribers:
                return None
            
            # Update topic statistics
            topic.last_published = current_time
            self._topic_stats[topic_name]['publish_count'] += 1
            self._topic_stats[topic_name]['last_publish'] = current_time
            
            # Create a snapshot of current subscribers
            subscribers = [topic.subscribers[sub_id] for sub_id in topic.subscriber_order]

        # Process subscribers concurrently with optimized task creation
        tasks = []
        for subscriber in subscribers:
            subscriber.last_called = current_time
            subscriber.call_count += 1
            
            if subscriber.async_handler:
                tasks.append(self._execute_async_handler(subscriber, topic_name, *args, **kwargs))
            else:
                tasks.append(self._execute_sync_handler(subscriber, topic_name, *args, **kwargs))

        # Optimized gathering of results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Efficient exception handling
        exceptions = [e for e in results if isinstance(e, Exception)]
        
        if exceptions and self.logger:
            self.logger.error(f"{len(exceptions)} errors occurred while publishing to '{topic_name}'")
            for exception in exceptions:
                self.logger.error(f"Error in subscriber for topic '{topic_name}': {str(exception)}")
        
        return exceptions

    async def _execute_async_handler(self, subscriber: Subscriber, topic_name: str, *args, **kwargs):
        try:
            return await subscriber.callback(*args, **kwargs)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in async subscriber for topic '{topic_name}': {str(e)}")
            return e

    async def _execute_sync_handler(self, subscriber: Subscriber, topic_name: str, *args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, lambda: subscriber.callback(*args, **kwargs)
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in sync subscriber for topic '{topic_name}': {str(e)}")
            return e

    def get_topic_stats(self, topic_name: Optional[str] = None) -> Dict:
        """Get statistics for a specific topic or all topics."""
        if topic_name:
            return self._topic_stats.get(topic_name, {})
        return dict(self._topic_stats)
    
if __name__ == "__main__":

    async def you_are_not():
        pass

    eb = EventBus()

    sub = Subscriber(callback=you_are_not, async_handler=True)
    print("== Subscriber ==")
    print(sub)
    sub_id = id(you_are_not)

    gg = Topic(name="you_are_not", subscribers={sub_id: sub}, subscriber_order=[sub_id])
    print("\n== Topic ==")
    print(gg)
    gg.subscriber_order.append(str(sub_id) + " This is added")
    print("\n== Topic ==")
    print(gg)
    states= eb.get_topic_stats()
    print(f"\n== States ==\n{states}")