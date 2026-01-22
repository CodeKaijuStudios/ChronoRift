"""
ChronoRift Event Service
Global event broadcasting, pub/sub system, and event routing
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import threading
from uuid import uuid4


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class EventCategory(Enum):
    """Event classification categories"""
    PLAYER = "player"               # Player actions (login, logout, level up)
    BATTLE = "battle"               # Battle events (start, end, damage)
    ECHO = "echo"                   # Echo-related (capture, evolution, fainting)
    WORLD = "world"                 # World events (anomalies, mutations)
    BONDING = "bonding"             # Bonding events (level up, milestone)
    SOCIAL = "social"               # Social events (chat, guilds, trading)
    ACHIEVEMENT = "achievement"     # Achievement unlocked
    ECONOMY = "economy"             # Market, currency changes
    SYSTEM = "system"               # Server events
    MATCHMAKING = "matchmaking"     # Queue, match events


class EventPriority(Enum):
    """Event processing priority"""
    CRITICAL = 5                    # Must be processed immediately (battle events)
    HIGH = 4                        # Important (player actions)
    NORMAL = 3                      # Standard (most events)
    LOW = 2                         # Non-urgent (social)
    BACKGROUND = 1                  # Can be deferred (logging, analytics)


class EventScope(Enum):
    """Event broadcast scope"""
    PRIVATE = "private"             # Only specific recipient
    PLAYER = "player"               # To specific player
    ZONE = "zone"                   # To all players in zone
    TEAM = "team"                   # To team members
    GUILD = "guild"                 # To guild members
    GLOBAL = "global"               # To all connected players


class EventStatus(Enum):
    """Event processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"


# Maximum event queue size
MAX_EVENT_QUEUE = 10000
# Event retention time (seconds)
EVENT_RETENTION_TIME = 3600
# Max listeners per event
MAX_LISTENERS = 1000


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Event:
    """Game event"""
    id: str
    category: EventCategory
    event_type: str
    source_user_id: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    scope: EventScope = EventScope.GLOBAL
    target_user_id: Optional[str] = None
    zone_id: Optional[str] = None
    team_id: Optional[str] = None
    guild_id: Optional[str] = None
    
    # Metadata
    status: EventStatus = EventStatus.QUEUED
    processed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    delivery_count: int = 0


@dataclass
class EventListener:
    """Registered event listener"""
    listener_id: str
    category: EventCategory
    event_type: Optional[str]  # None = listen to all types in category
    callback: Callable
    priority: int = 0
    is_active: bool = True
    registered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EventSubscription:
    """Player event subscription"""
    player_id: str
    subscribed_categories: List[EventCategory] = field(default_factory=list)
    subscribed_events: Dict[str, List[str]] = field(default_factory=dict)  # category -> event types
    scope_filter: Optional[EventScope] = None
    zone_id: Optional[str] = None
    is_active: bool = True


@dataclass
class EventStats:
    """Event system statistics"""
    total_events_processed: int = 0
    events_by_category: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    events_by_priority: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    failed_events: int = 0
    average_processing_time_ms: float = 0.0
    listeners_count: int = 0
    subscriptions_count: int = 0
    queue_size: int = 0


# ============================================================================
# EVENT SERVICE
# ============================================================================

class EventService:
    """Global event broadcasting and pub/sub system"""
    
    def __init__(self):
        """Initialize event service"""
        self.listeners: Dict[str, List[EventListener]] = defaultdict(list)  # category -> listeners
        self.subscriptions: Dict[str, EventSubscription] = {}  # player_id -> subscription
        self.event_queue: List[Event] = []
        self.event_history: List[Event] = []
        self.stats = EventStats()
        self.lock = threading.RLock()
    
    
    def emit_event(
        self,
        category: EventCategory,
        event_type: str,
        source_user_id: str,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        scope: EventScope = EventScope.GLOBAL,
        target_user_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        team_id: Optional[str] = None,
        guild_id: Optional[str] = None,
    ) -> Event:
        """
        Emit event to system
        
        Args:
            category: Event category
            event_type: Specific event type
            source_user_id: Player who triggered event
            data: Event payload
            priority: Processing priority
            scope: Broadcast scope
            target_user_id: Target player (if PRIVATE scope)
            zone_id: Zone ID (if ZONE scope)
            team_id: Team ID (if TEAM scope)
            guild_id: Guild ID (if GUILD scope)
            
        Returns:
            Event: Created event
        """
        with self.lock:
            event = Event(
                id=str(uuid4()),
                category=category,
                event_type=event_type,
                source_user_id=source_user_id,
                timestamp=datetime.utcnow(),
                data=data,
                priority=priority,
                scope=scope,
                target_user_id=target_user_id,
                zone_id=zone_id,
                team_id=team_id,
                guild_id=guild_id,
            )
            
            # Add to queue
            if len(self.event_queue) < MAX_EVENT_QUEUE:
                self.event_queue.append(event)
            else:
                event.status = EventStatus.FAILED
                event.failed_reason = "Queue overflow"
                self.stats.failed_events += 1
                return event
            
            # Process immediately (critical priority)
            if priority == EventPriority.CRITICAL:
                self._process_event(event)
            
            return event
    
    
    def process_queue(self) -> int:
        """
        Process pending events in queue
        
        Returns:
            int: Number of events processed
        """
        with self.lock:
            processed = 0
            remaining = []
            
            # Sort by priority
            self.event_queue.sort(key=lambda e: e.priority.value, reverse=True)
            
            for event in self.event_queue:
                if event.status == EventStatus.QUEUED:
                    if self._process_event(event):
                        processed += 1
                    else:
                        remaining.append(event)
                else:
                    remaining.append(event)
            
            self.event_queue = remaining
            return processed
    
    
    def _process_event(self, event: Event) -> bool:
        """
        Process single event (internal)
        
        Args:
            event: Event to process
            
        Returns:
            bool: Success
        """
        try:
            event.status = EventStatus.PROCESSING
            start_time = datetime.utcnow()
            
            # Broadcast to listeners
            listeners = self.listeners.get(event.category.value, [])
            delivered_to = 0
            
            for listener in listeners:
                # Check if listener wants this event type
                if listener.event_type and listener.event_type != event.event_type:
                    continue
                
                if not listener.is_active:
                    continue
                
                # Call listener callback
                try:
                    listener.callback(event)
                    delivered_to += 1
                except Exception as e:
                    # Log listener error but continue
                    pass
            
            # Check scope eligibility for subscriptions
            recipients = self._get_delivery_recipients(event)
            
            # Deliver to subscribed players
            for player_id in recipients:
                subscription = self.subscriptions.get(player_id)
                if subscription and self._should_deliver_to_subscription(event, subscription):
                    event.delivery_count += 1
            
            event.status = EventStatus.DELIVERED
            event.processed_at = datetime.utcnow()
            
            # Update stats
            processing_time = (event.processed_at - start_time).total_seconds() * 1000
            self.stats.total_events_processed += 1
            self.stats.events_by_category[event.category.value] += 1
            self.stats.events_by_priority[event.priority.name] += 1
            
            # Update average processing time
            total_time = self.stats.average_processing_time_ms * (self.stats.total_events_processed - 1)
            self.stats.average_processing_time_ms = (total_time + processing_time) / self.stats.total_events_processed
            
            # Add to history
            self.event_history.append(event)
            
            # Keep history size manageable
            if len(self.event_history) > 10000:
                self.event_history = self.event_history[-10000:]
            
            return True
        
        except Exception as e:
            event.status = EventStatus.FAILED
            event.failed_reason = str(e)
            self.stats.failed_events += 1
            return False
    
    
    def register_listener(
        self,
        category: EventCategory,
        callback: Callable,
        event_type: Optional[str] = None,
        priority: int = 0
    ) -> str:
        """
        Register event listener
        
        Args:
            category: Listen to category
            callback: Function to call when event occurs
            event_type: Specific event type (None = all types)
            priority: Listener priority
            
        Returns:
            str: Listener ID
        """
        with self.lock:
            listener_id = str(uuid4())
            listener = EventListener(
                listener_id=listener_id,
                category=category,
                event_type=event_type,
                callback=callback,
                priority=priority,
            )
            
            self.listeners[category.value].append(listener)
            self.stats.listeners_count += 1
            
            return listener_id
    
    
    def unregister_listener(self, listener_id: str) -> bool:
        """Unregister event listener"""
        with self.lock:
            for category_listeners in self.listeners.values():
                for i, listener in enumerate(category_listeners):
                    if listener.listener_id == listener_id:
                        listener.is_active = False
                        self.stats.listeners_count -= 1
                        return True
        return False
    
    
    def subscribe_player(
        self,
        player_id: str,
        categories: Optional[List[EventCategory]] = None,
        scope: Optional[EventScope] = None,
        zone_id: Optional[str] = None
    ) -> EventSubscription:
        """
        Subscribe player to events
        
        Args:
            player_id: Player's ID
            categories: Categories to subscribe to (None = all)
            scope: Scope filter
            zone_id: Zone filter
            
        Returns:
            EventSubscription: Subscription object
        """
        with self.lock:
            subscription = EventSubscription(
                player_id=player_id,
                subscribed_categories=categories or list(EventCategory),
                scope_filter=scope,
                zone_id=zone_id,
            )
            
            self.subscriptions[player_id] = subscription
            self.stats.subscriptions_count += 1
            
            return subscription
    
    
    def unsubscribe_player(self, player_id: str) -> bool:
        """Unsubscribe player from events"""
        with self.lock:
            if player_id in self.subscriptions:
                self.subscriptions[player_id].is_active = False
                self.stats.subscriptions_count -= 1
                return True
        return False
    
    
    def _get_delivery_recipients(self, event: Event) -> List[str]:
        """Get list of players who should receive event"""
        recipients = []
        
        if event.scope == EventScope.PRIVATE:
            if event.target_user_id:
                recipients.append(event.target_user_id)
        elif event.scope == EventScope.PLAYER:
            if event.target_user_id:
                recipients.append(event.target_user_id)
        elif event.scope == EventScope.ZONE:
            # In real system, would lookup players in zone
            # For now, return empty (would be populated from world state)
            pass
        elif event.scope == EventScope.TEAM:
            # Would lookup team members
            pass
        elif event.scope == EventScope.GUILD:
            # Would lookup guild members
            pass
        elif event.scope == EventScope.GLOBAL:
            # All subscribed players
            recipients = list(self.subscriptions.keys())
        
        return recipients
    
    
    def _should_deliver_to_subscription(
        self,
        event: Event,
        subscription: EventSubscription
    ) -> bool:
        """Check if event should be delivered to subscription"""
        if not subscription.is_active:
            return False
        
        # Check category
        if event.category not in subscription.subscribed_categories:
            return False
        
        # Check scope filter
        if subscription.scope_filter:
            if subscription.scope_filter != event.scope:
                return False
        
        # Check zone filter
        if subscription.zone_id:
            if event.zone_id != subscription.zone_id:
                return False
        
        return True
    
    
    def get_event_history(
        self,
        category: Optional[EventCategory] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get recent event history"""
        with self.lock:
            history = self.event_history
            
            if category:
                history = [e for e in history if e.category == category]
            
            return history[-limit:]
    
    
    def get_stats(self) -> EventStats:
        """Get event system statistics"""
        with self.lock:
            self.stats.queue_size = len(self.event_queue)
            return self.stats
    
    
    def clear_old_events(self, seconds: int = EVENT_RETENTION_TIME) -> int:
        """
        Clear events older than specified time
        
        Args:
            seconds: Retention time in seconds
            
        Returns:
            int: Events removed
        """
        with self.lock:
            now = datetime.utcnow()
            cutoff = datetime.fromtimestamp(now.timestamp() - seconds)
            
            before = len(self.event_history)
            self.event_history = [e for e in self.event_history if e.timestamp > cutoff]
            
            return before - len(self.event_history)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_event_scope_description(scope: EventScope) -> str:
    """Get human-readable scope description"""
    descriptions = {
        EventScope.PRIVATE: "Direct message",
        EventScope.PLAYER: "Player only",
        EventScope.ZONE: "Everyone in zone",
        EventScope.TEAM: "Team members",
        EventScope.GUILD: "Guild members",
        EventScope.GLOBAL: "All players",
    }
    return descriptions.get(scope, "Unknown")


def get_event_category_description(category: EventCategory) -> str:
    """Get human-readable category description"""
    descriptions = {
        EventCategory.PLAYER: "Player action",
        EventCategory.BATTLE: "Battle event",
        EventCategory.ECHO: "Echo management",
        EventCategory.WORLD: "World event",
        EventCategory.BONDING: "Bonding progress",
        EventCategory.SOCIAL: "Social interaction",
        EventCategory.ACHIEVEMENT: "Achievement unlocked",
        EventCategory.ECONOMY: "Economy change",
        EventCategory.SYSTEM: "System event",
        EventCategory.MATCHMAKING: "Matchmaking",
    }
    return descriptions.get(category, "Unknown")


def filter_events_by_criteria(
    events: List[Event],
    category: Optional[EventCategory] = None,
    priority: Optional[EventPriority] = None,
    status: Optional[EventStatus] = None,
    source_user_id: Optional[str] = None,
) -> List[Event]:
    """
    Filter events by various criteria
    
    Args:
        events: List of events to filter
        category: Filter by category
        priority: Filter by priority
        status: Filter by status
        source_user_id: Filter by source user
        
    Returns:
        List[Event]: Filtered events
    """
    result = events
    
    if category:
        result = [e for e in result if e.category == category]
    
    if priority:
        result = [e for e in result if e.priority == priority]
    
    if status:
        result = [e for e in result if e.status == status]
    
    if source_user_id:
        result = [e for e in result if e.source_user_id == source_user_id]
    
    return result
