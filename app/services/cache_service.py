"""
ChronoRift Cache Service
Redis-based distributed caching with invalidation strategies
"""

import json
import hashlib
from enum import Enum
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class CacheStrategy(Enum):
    """Cache invalidation strategy"""
    TTL = "ttl"                 # Time-to-live expiration
    WRITE_THROUGH = "write_through"  # Update DB first, then cache
    WRITE_BEHIND = "write_behind"    # Update cache first, then DB
    READ_THROUGH = "read_through"    # Cache handles DB reads
    EVENT_BASED = "event_based"      # Invalidate on specific events
    HYBRID = "hybrid"                # Combination of strategies


class CacheNamespace(Enum):
    """Cache key namespaces for organization"""
    USER = "user"              # User profiles, settings
    ECHO = "echo"              # Echo data, stats
    BATTLE = "battle"          # Active battles, results
    WORLD = "world"            # World state, zones
    BONDING = "bonding"        # Echo bonding data
    LEADERBOARD = "leaderboard"  # Rankings, scores
    SESSION = "session"        # Session tokens
    INVENTORY = "inventory"    # Player inventory
    MARKET = "market"          # Trading market data
    ACHIEVEMENT = "achievement"  # Achievement tracking


class CachePattern(Enum):
    """Cache key pattern types"""
    SINGLE = "single"          # Single object: user:123
    HASH = "hash"              # Hash map: user:123:*
    LIST = "list"              # List data: battle:123:log
    SET = "set"                # Set data: team:123:members
    SORTED = "sorted_set"      # Ranked data: leaderboard:global


# Default TTL values (seconds)
DEFAULT_TTL = 3600            # 1 hour
USER_TTL = 1800               # 30 minutes
BATTLE_TTL = 600              # 10 minutes
WORLD_TTL = 300               # 5 minutes
SESSION_TTL = 86400           # 24 hours
LEADERBOARD_TTL = 60          # 1 minute (frequently updated)

# Cache key prefixes
CACHE_PREFIX = "chronorift:"
KEY_SEPARATOR = ":"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CacheEntry:
    """Cached data entry with metadata"""
    key: str
    value: Any
    namespace: CacheNamespace
    ttl: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    is_dirty: bool = False  # For write-behind strategy


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired_entries: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


@dataclass
class DependencyLink:
    """Cache key dependency tracking"""
    parent_key: str
    child_keys: List[str]
    created_at: datetime


# ============================================================================
# CACHE SERVICE
# ============================================================================

class CacheService:
    """Redis-based distributed caching service"""
    
    def __init__(self, redis_client=None, strategy: CacheStrategy = CacheStrategy.HYBRID):
        """
        Initialize cache service
        
        Args:
            redis_client: Redis client instance (optional, for testing)
            strategy: Cache invalidation strategy
        """
        self.redis = redis_client
        self.strategy = strategy
        self.stats = CacheStats()
        self.dependencies: Dict[str, DependencyLink] = {}
        self.logger = logging.getLogger(__name__)
        
        # Local cache for testing (if no Redis)
        self.local_cache: Dict[str, CacheEntry] = {}
    
    
    def _make_key(self, namespace: CacheNamespace, *parts: str) -> str:
        """
        Create cache key from namespace and parts
        
        Args:
            namespace: Cache namespace
            *parts: Key components (e.g., user_id, field_name)
            
        Returns:
            str: Formatted cache key
        """
        parts_str = KEY_SEPARATOR.join(str(p) for p in parts)
        return f"{CACHE_PREFIX}{namespace.value}{KEY_SEPARATOR}{parts_str}"
    
    
    def set(
        self,
        namespace: CacheNamespace,
        key_parts: List[str],
        value: Any,
        ttl: Optional[int] = None,
        dependencies: Optional[List[str]] = None
    ) -> bool:
        """
        Set cache value with optional TTL
        
        Args:
            namespace: Cache namespace
            key_parts: Components of cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
            dependencies: Parent keys this entry depends on
            
        Returns:
            bool: Success
        """
        key = self._make_key(namespace, *key_parts)
        ttl = ttl or self._get_default_ttl(namespace)
        
        try:
            # Serialize value
            serialized = json.dumps(value) if not isinstance(value, str) else value
            
            if self.redis:
                # Store in Redis with TTL
                self.redis.setex(key, ttl, serialized)
            else:
                # Store in local cache
                self.local_cache[key] = CacheEntry(
                    key=key,
                    value=value,
                    namespace=namespace,
                    ttl=ttl,
                    created_at=datetime.utcnow(),
                    last_accessed=datetime.utcnow(),
                )
            
            # Track dependencies
            if dependencies:
                for parent_key in dependencies:
                    if parent_key not in self.dependencies:
                        self.dependencies[parent_key] = DependencyLink(
                            parent_key=parent_key,
                            child_keys=[key],
                            created_at=datetime.utcnow(),
                        )
                    else:
                        if key not in self.dependencies[parent_key].child_keys:
                            self.dependencies[parent_key].child_keys.append(key)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Cache set error for {key}: {e}")
            return False
    
    
    def get(
        self,
        namespace: CacheNamespace,
        key_parts: List[str],
        deserialize: bool = True
    ) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            namespace: Cache namespace
            key_parts: Components of cache key
            deserialize: Parse JSON if True
            
        Returns:
            Any: Cached value, or None if not found
        """
        key = self._make_key(namespace, *key_parts)
        
        try:
            if self.redis:
                value = self.redis.get(key)
                if value:
                    self.stats.hits += 1
                    if deserialize and isinstance(value, bytes):
                        return json.loads(value.decode('utf-8'))
                    return value
                else:
                    self.stats.misses += 1
                    return None
            else:
                # Local cache lookup
                if key in self.local_cache:
                    entry = self.local_cache[key]
                    entry.last_accessed = datetime.utcnow()
                    entry.access_count += 1
                    self.stats.hits += 1
                    return entry.value
                else:
                    self.stats.misses += 1
                    return None
        
        except Exception as e:
            self.logger.error(f"Cache get error for {key}: {e}")
            self.stats.misses += 1
            return None
    
    
    def delete(
        self,
        namespace: CacheNamespace,
        key_parts: List[str],
        cascade: bool = False
    ) -> bool:
        """
        Delete cache entry
        
        Args:
            namespace: Cache namespace
            key_parts: Components of cache key
            cascade: Delete dependent keys
            
        Returns:
            bool: Success
        """
        key = self._make_key(namespace, *key_parts)
        
        try:
            if self.redis:
                self.redis.delete(key)
            else:
                if key in self.local_cache:
                    del self.local_cache[key]
            
            # Cascade delete dependencies
            if cascade and key in self.dependencies:
                for child_key in self.dependencies[key].child_keys:
                    self.delete_by_key(child_key, cascade=True)
                del self.dependencies[key]
            
            self.stats.evictions += 1
            return True
        
        except Exception as e:
            self.logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    
    def delete_by_key(self, key: str, cascade: bool = False) -> bool:
        """Delete using full cache key"""
        try:
            if self.redis:
                self.redis.delete(key)
            else:
                if key in self.local_cache:
                    del self.local_cache[key]
            
            if cascade and key in self.dependencies:
                for child_key in self.dependencies[key].child_keys:
                    self.delete_by_key(child_key, cascade=True)
                del self.dependencies[key]
            
            return True
        except Exception as e:
            self.logger.error(f"Delete error for {key}: {e}")
            return False
    
    
    def invalidate_namespace(self, namespace: CacheNamespace) -> int:
        """
        Invalidate all keys in namespace
        
        Args:
            namespace: Namespace to clear
            
        Returns:
            int: Number of keys invalidated
        """
        pattern = f"{CACHE_PREFIX}{namespace.value}{KEY_SEPARATOR}*"
        count = 0
        
        try:
            if self.redis:
                keys = self.redis.keys(pattern)
                if keys:
                    count = self.redis.delete(*keys)
            else:
                keys_to_delete = [k for k in self.local_cache.keys() 
                                if k.startswith(pattern.replace('*', ''))]
                for key in keys_to_delete:
                    del self.local_cache[key]
                    count += 1
            
            self.stats.evictions += count
            return count
        
        except Exception as e:
            self.logger.error(f"Namespace invalidation error: {e}")
            return 0
    
    
    def invalidate_pattern(self, namespace: CacheNamespace, pattern: str) -> int:
        """
        Invalidate keys matching pattern
        
        Args:
            namespace: Namespace to search
            pattern: Key pattern (supports *)
            
        Returns:
            int: Number of keys invalidated
        """
        search_pattern = self._make_key(namespace, pattern)
        count = 0
        
        try:
            if self.redis:
                keys = self.redis.keys(search_pattern)
                if keys:
                    count = self.redis.delete(*keys)
            else:
                prefix = search_pattern.replace('*', '')
                keys_to_delete = [k for k in self.local_cache.keys() 
                                if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.local_cache[key]
                    count += 1
            
            self.stats.evictions += count
            return count
        
        except Exception as e:
            self.logger.error(f"Pattern invalidation error: {e}")
            return 0
    
    
    def get_or_set(
        self,
        namespace: CacheNamespace,
        key_parts: List[str],
        loader: Callable,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get cached value or load if missing (read-through)
        
        Args:
            namespace: Cache namespace
            key_parts: Key components
            loader: Function to load value from source
            ttl: Time-to-live for cache
            
        Returns:
            Any: Cached or loaded value
        """
        # Try cache first
        cached = self.get(namespace, key_parts)
        if cached is not None:
            return cached
        
        # Cache miss - load from source
        try:
            value = loader()
            if value is not None:
                self.set(namespace, key_parts, value, ttl=ttl)
            return value
        except Exception as e:
            self.logger.error(f"Loader error for {key_parts}: {e}")
            return None
    
    
    def increment(
        self,
        namespace: CacheNamespace,
        key_parts: List[str],
        amount: int = 1
    ) -> Optional[int]:
        """
        Increment numeric cache value
        
        Args:
            namespace: Cache namespace
            key_parts: Key components
            amount: Increment amount
            
        Returns:
            int: New value, or None if error
        """
        key = self._make_key(namespace, *key_parts)
        
        try:
            if self.redis:
                return self.redis.incrby(key, amount)
            else:
                if key in self.local_cache:
                    entry = self.local_cache[key]
                    entry.value = int(entry.value) + amount
                    return entry.value
                else:
                    self.local_cache[key] = CacheEntry(
                        key=key,
                        value=amount,
                        namespace=namespace,
                        ttl=DEFAULT_TTL,
                        created_at=datetime.utcnow(),
                        last_accessed=datetime.utcnow(),
                    )
                    return amount
        except Exception as e:
            self.logger.error(f"Increment error for {key}: {e}")
            return None
    
    
    def push_to_list(
        self,
        namespace: CacheNamespace,
        key_parts: List[str],
        *values: Any
    ) -> Optional[int]:
        """
        Push values to cache list
        
        Args:
            namespace: Cache namespace
            key_parts: Key components
            *values: Values to push
            
        Returns:
            int: New list length, or None if error
        """
        key = self._make_key(namespace, *key_parts)
        
        try:
            if self.redis:
                serialized = [json.dumps(v) for v in values]
                return self.redis.rpush(key, *serialized)
            else:
                if key not in self.local_cache:
                    self.local_cache[key] = CacheEntry(
                        key=key,
                        value=[],
                        namespace=namespace,
                        ttl=DEFAULT_TTL,
                        created_at=datetime.utcnow(),
                        last_accessed=datetime.utcnow(),
                    )
                
                entry = self.local_cache[key]
                entry.value.extend(values)
                return len(entry.value)
        except Exception as e:
            self.logger.error(f"Push error for {key}: {e}")
            return None
    
    
    def add_to_set(
        self,
        namespace: CacheNamespace,
        key_parts: List[str],
        *members: str
    ) -> Optional[int]:
        """
        Add members to cache set
        
        Args:
            namespace: Cache namespace
            key_parts: Key components
            *members: Members to add
            
        Returns:
            int: Number of new members, or None if error
        """
        key = self._make_key(namespace, *key_parts)
        
        try:
            if self.redis:
                return self.redis.sadd(key, *members)
            else:
                if key not in self.local_cache:
                    self.local_cache[key] = CacheEntry(
                        key=key,
                        value=set(),
                        namespace=namespace,
                        ttl=DEFAULT_TTL,
                        created_at=datetime.utcnow(),
                        last_accessed=datetime.utcnow(),
                    )
                
                entry = self.local_cache[key]
                before = len(entry.value)
                entry.value.update(members)
                return len(entry.value) - before
        except Exception as e:
            self.logger.error(f"Set add error for {key}: {e}")
            return None
    
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        if not self.redis:
            # Update local cache stats
            self.stats.entry_count = len(self.local_cache)
            self.stats.total_size_bytes = sum(
                len(json.dumps(e.value))
                for e in self.local_cache.values()
            )
        return self.stats
    
    
    def clear(self) -> bool:
        """Clear entire cache"""
        try:
            if self.redis:
                self.redis.flushdb()
            else:
                self.local_cache.clear()
                self.dependencies.clear()
            
            self.stats = CacheStats()
            return True
        except Exception as e:
            self.logger.error(f"Clear error: {e}")
            return False
    
    
    @staticmethod
    def _get_default_ttl(namespace: CacheNamespace) -> int:
        """Get default TTL for namespace"""
        ttl_map = {
            CacheNamespace.USER: USER_TTL,
            CacheNamespace.SESSION: SESSION_TTL,
            CacheNamespace.BATTLE: BATTLE_TTL,
            CacheNamespace.WORLD: WORLD_TTL,
            CacheNamespace.LEADERBOARD: LEADERBOARD_TTL,
        }
        return ttl_map.get(namespace, DEFAULT_TTL)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_cache_key(namespace: str, *parts: str) -> str:
    """Generate cache key from components"""
    parts_str = ":".join(str(p) for p in parts)
    return f"{CACHE_PREFIX}{namespace}:{parts_str}"


def hash_cache_key(key: str) -> str:
    """Create hash of cache key for consistency"""
    return hashlib.md5(key.encode()).hexdigest()


def estimate_cache_size(value: Any) -> int:
    """Estimate memory size of cached value in bytes"""
    try:
        return len(json.dumps(value).encode('utf-8'))
    except:
        return 0


def create_dependency_graph(
    cache_service: CacheService,
    key: str
) -> Dict[str, List[str]]:
    """
    Get dependency graph for a cache key
    
    Args:
        cache_service: Cache service instance
        key: Cache key to analyze
        
    Returns:
        Dict: Dependency relationships
    """
    graph = {}
    
    if key in cache_service.dependencies:
        link = cache_service.dependencies[key]
        graph['parents'] = [link.parent_key]
        graph['children'] = link.child_keys
    else:
        graph['parents'] = []
        graph['children'] = []
    
    return graph
