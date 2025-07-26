"""
Performance Cache Manager

Implements intelligent caching for LyricLawyer to optimize API calls and response times.
"""

import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import sqlite3
import os


@dataclass
class CacheEntry:
    """Represents a cached analysis result"""
    key: str
    value: Dict[str, Any]
    timestamp: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0.0


class LyricLawyerCache:
    """
    High-performance caching system for LyricLawyer analysis results
    """
    
    def __init__(self, cache_dir: str = "cache", max_size: int = 1000):
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.memory_cache: Dict[str, CacheEntry] = {}
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize persistent cache database
        self.db_path = os.path.join(cache_dir, "lyric_cache.db")
        self._init_cache_db()
        
        # Load frequently accessed items into memory
        self._load_hot_cache()
    
    def _init_cache_db(self):
        """Initialize SQLite database for persistent caching"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    ttl INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL DEFAULT 0.0
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_access_count ON cache_entries(access_count DESC)")
    
    def _generate_cache_key(self, lyrics: str, preferences: Optional[Dict] = None) -> str:
        """Generate consistent cache key for lyrics and preferences"""
        # Normalize lyrics for consistent caching
        normalized_lyrics = lyrics.lower().strip()
        
        # Include relevant preferences in cache key
        cache_data = {
            'lyrics': normalized_lyrics,
            'preferences': preferences or {}
        }
        
        # Generate SHA-256 hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode('utf-8')).hexdigest()
    
    def get(self, lyrics: str, preferences: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis result"""
        cache_key = self._generate_cache_key(lyrics, preferences)
        current_time = time.time()
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            
            # Check if entry is still valid
            if current_time - entry.timestamp < entry.ttl:
                entry.access_count += 1
                entry.last_accessed = current_time
                self._update_cache_stats(cache_key, entry)
                return entry.value
            else:
                # Remove expired entry
                del self.memory_cache[cache_key]
        
        # Check persistent cache
        return self._get_from_db(cache_key, current_time)
    
    def set(self, lyrics: str, analysis_result: Dict[str, Any], 
            preferences: Optional[Dict] = None, ttl: int = 3600) -> None:
        """Cache analysis result with TTL (default 1 hour)"""
        cache_key = self._generate_cache_key(lyrics, preferences)
        current_time = time.time()
        
        entry = CacheEntry(
            key=cache_key,
            value=analysis_result,
            timestamp=current_time,
            ttl=ttl,
            access_count=1,
            last_accessed=current_time
        )
        
        # Store in memory cache
        self.memory_cache[cache_key] = entry
        
        # Store in persistent cache
        self._store_to_db(entry)
        
        # Manage cache size
        self._cleanup_cache()
    
    def _get_from_db(self, cache_key: str, current_time: float) -> Optional[Dict[str, Any]]:
        """Retrieve entry from persistent cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, timestamp, ttl, access_count FROM cache_entries WHERE key = ?",
                    (cache_key,)
                )
                result = cursor.fetchone()
                
                if result:
                    value_json, timestamp, ttl, access_count = result
                    
                    # Check if entry is still valid
                    if current_time - timestamp < ttl:
                        # Update access statistics
                        conn.execute(
                            "UPDATE cache_entries SET access_count = ?, last_accessed = ? WHERE key = ?",
                            (access_count + 1, current_time, cache_key)
                        )
                        
                        # Parse and return cached value
                        return json.loads(value_json)
                    else:
                        # Remove expired entry
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (cache_key,))
        
        except Exception as e:
            print(f"Cache retrieval error: {e}")
        
        return None
    
    def _store_to_db(self, entry: CacheEntry) -> None:
        """Store entry in persistent cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache_entries 
                       (key, value, timestamp, ttl, access_count, last_accessed) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        entry.key,
                        json.dumps(entry.value),
                        entry.timestamp,
                        entry.ttl,
                        entry.access_count,
                        entry.last_accessed
                    )
                )
        except Exception as e:
            print(f"Cache storage error: {e}")
    
    def _update_cache_stats(self, cache_key: str, entry: CacheEntry) -> None:
        """Update cache statistics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE cache_entries SET access_count = ?, last_accessed = ? WHERE key = ?",
                    (entry.access_count, entry.last_accessed, cache_key)
                )
        except Exception as e:
            print(f"Cache stats update error: {e}")
    
    def _load_hot_cache(self) -> None:
        """Load frequently accessed items into memory cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT key, value, timestamp, ttl, access_count, last_accessed 
                       FROM cache_entries 
                       ORDER BY access_count DESC 
                       LIMIT ?""",
                    (min(100, self.max_size // 2),)  # Load top 100 or half of max size
                )
                
                current_time = time.time()
                for row in cursor.fetchall():
                    key, value_json, timestamp, ttl, access_count, last_accessed = row
                    
                    # Only load non-expired entries
                    if current_time - timestamp < ttl:
                        entry = CacheEntry(
                            key=key,
                            value=json.loads(value_json),
                            timestamp=timestamp,
                            ttl=ttl,
                            access_count=access_count,
                            last_accessed=last_accessed
                        )
                        self.memory_cache[key] = entry
        
        except Exception as e:
            print(f"Hot cache loading error: {e}")
    
    def _cleanup_cache(self) -> None:
        """Remove expired entries and manage cache size"""
        current_time = time.time()
        
        # Clean memory cache of expired entries
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if current_time - entry.timestamp >= entry.ttl
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # If memory cache is too large, remove least recently used items
        if len(self.memory_cache) > self.max_size:
            # Sort by last_accessed time and remove oldest
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            items_to_remove = len(self.memory_cache) - self.max_size
            for key, _ in sorted_items[:items_to_remove]:
                del self.memory_cache[key]
        
        # Clean persistent cache of expired entries (run periodically)
        if int(current_time) % 300 == 0:  # Every 5 minutes
            self._cleanup_persistent_cache(current_time)
    
    def _cleanup_persistent_cache(self, current_time: float) -> None:
        """Clean expired entries from persistent cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove expired entries
                conn.execute(
                    "DELETE FROM cache_entries WHERE timestamp + ttl < ?",
                    (current_time,)
                )
                
                # Keep only the most accessed entries if database is too large
                conn.execute("""
                    DELETE FROM cache_entries 
                    WHERE key NOT IN (
                        SELECT key FROM cache_entries 
                        ORDER BY access_count DESC 
                        LIMIT ?
                    )
                """, (self.max_size * 10,))  # Keep 10x memory cache size in persistent storage
        
        except Exception as e:
            print(f"Persistent cache cleanup error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(access_count) as total_accesses,
                        AVG(access_count) as avg_accesses,
                        MAX(access_count) as max_accesses
                    FROM cache_entries
                """)
                stats = cursor.fetchone()
                
                return {
                    'memory_cache_size': len(self.memory_cache),
                    'persistent_cache_size': stats[0] if stats[0] else 0,
                    'total_accesses': stats[1] if stats[1] else 0,
                    'avg_accesses_per_entry': stats[2] if stats[2] else 0,
                    'max_accesses': stats[3] if stats[3] else 0,
                    'cache_hit_potential': min(1.0, len(self.memory_cache) / max(1, self.max_size))
                }
        
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {
                'memory_cache_size': len(self.memory_cache),
                'error': str(e)
            }
    
    def clear_expired(self) -> int:
        """Clear all expired entries and return count of removed items"""
        current_time = time.time()
        removed_count = 0
        
        # Clear from memory cache
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if current_time - entry.timestamp >= entry.ttl
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
            removed_count += 1
        
        # Clear from persistent cache
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM cache_entries WHERE timestamp + ttl < ?",
                    (current_time,)
                )
                db_expired_count = cursor.fetchone()[0]
                
                conn.execute(
                    "DELETE FROM cache_entries WHERE timestamp + ttl < ?",
                    (current_time,)
                )
                
                removed_count += db_expired_count
        
        except Exception as e:
            print(f"Cache cleanup error: {e}")
        
        return removed_count
    
    def clear_all(self) -> None:
        """Clear all cache entries"""
        self.memory_cache.clear()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries")
        except Exception as e:
            print(f"Cache clear error: {e}")


# Global cache instance
_cache_instance = None


def get_cache() -> LyricLawyerCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LyricLawyerCache()
    return _cache_instance


def cache_analysis_result(lyrics: str, result: Dict[str, Any], 
                         preferences: Optional[Dict] = None, ttl: int = 3600) -> None:
    """Convenience function to cache analysis result"""
    cache = get_cache()
    cache.set(lyrics, result, preferences, ttl)


def get_cached_analysis(lyrics: str, preferences: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to retrieve cached analysis"""
    cache = get_cache()
    return cache.get(lyrics, preferences)