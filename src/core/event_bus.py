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
        self._queue = asyncio.Queue()
        self.logger = setup_logging(module_name="EventBus")
        self._topic_stats: Dict[str, Dict] = defaultdict(lambda: {'publish_count': 0, 'last_publish': 0})
        self._cleanup_threshold = 1000  # Number of empty topic checks before cleanup
        self._empty_topic_count = 0

    async def get(self):
        """Get the next event from the queue"""
        try:
            return await self._queue.get()
        except Exception as e:
            self.logger.error(f"Error getting event from queue: {e}")
            return None

    async def put(self, event):
        """Put an event into the queue"""
        try:
            await self._queue.put(event)
        except Exception as e:
            self.logger.error(f"Error putting event in queue: {e}")

    async def shutdown(self) -> None:
        """
        Cleanup and shutdown the event bus.
        This method should be called when the event bus is no longer needed.
        """
        self._cleanup_empty_topics()
        self._topics.clear()
        if self.logger:
            self.logger.debug("Event bus shut down")

    async def publish(self, topic_name: str, *args, **kwargs):
        """Publish an event to a topic"""
        try:
            await self.put(kwargs)
            with self._lock:
                if topic_name not in self._topics:
                    self._topics[topic_name] = Topic(name=topic_name)
                topic = self._topics[topic_name]
                
            with topic._lock:
                topic.last_published = time.time()
                self._topic_stats[topic_name]['publish_count'] += 1
                self._topic_stats[topic_name]['last_publish'] = time.time()
                for sub_id in topic.subscriber_order:
                    subscriber = topic.subscribers.get(sub_id)
                    if subscriber:
                        try:
                            if subscriber.async_handler:
                                await subscriber.callback(*args, **kwargs)
                            else:
                                subscriber.callback(*args, **kwargs)
                            subscriber.last_called = time.time()
                            subscriber.call_count += 1
                        except Exception as e:
                            self.logger.error(f"Error in subscriber callback: {e}")
        except Exception as e:
            self.logger.error(f"Error publishing to topic {topic_name}: {e}")

    def subscribe(self, topic_name: str, callback: Callable, async_handler: bool = False) -> int:
        """Subscribe to a topic"""
        with self._lock:
            if topic_name not in self._topics:
                self._topics[topic_name] = Topic(name=topic_name)
            topic = self._topics[topic_name]
            
        with topic._lock:
            sub_id = len(topic.subscriber_order)
            subscriber = Subscriber(callback=callback, async_handler=async_handler)
            topic.subscribers[sub_id] = subscriber
            topic.subscriber_order.append(sub_id)
            self.logger.event(f"Subscribed to topic '{topic_name}' and subscribed in {GenericUtils.caller_info()}")
            return sub_id

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