"""
LyricLawyer Memory Module

This module implements memory and context management for the LyricLawyer system,
working alongside ADK's built-in conversation memory to provide persistent
storage, user preferences, and analysis history.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta  
from enum import Enum
import hashlib


class MemoryType(Enum):
    """Types of memory storage"""
    SESSION = "session"          # Current session data
    USER_PREFERENCES = "user_preferences"  # User settings and preferences  
    ANALYSIS_HISTORY = "analysis_history"  # Past analysis results
    FLAGGED_PHRASES = "flagged_phrases"    # Previously flagged content
    LEARNING_DATA = "learning_data"        # System learning and improvements


class MemoryScope(Enum):
    """Scope of memory persistence"""
    TEMPORARY = "temporary"      # Session only
    PERSISTENT = "persistent"    # Saved to disk
    GLOBAL = "global"           # Shared across all users


class MemoryEntry:
    """Individual memory entry"""
    
    def __init__(self, key: str, value: Any, memory_type: MemoryType, 
                 scope: MemoryScope = MemoryScope.TEMPORARY, ttl: int = None):
        self.key = key
        self.value = value
        self.memory_type = memory_type
        self.scope = scope
        self.created_at = time.time()
        self.accessed_at = time.time()
        self.modified_at = time.time()
        self.access_count = 0
        self.ttl = ttl  # Time to live in seconds
        self.expired = False
    
    def access(self) -> Any:
        """Access the memory entry value"""
        if self.is_expired():
            self.expired = True
            return None
        
        self.accessed_at = time.time()
        self.access_count += 1
        return self.value
    
    def update(self, new_value: Any) -> None:
        """Update the memory entry value"""
        self.value = new_value
        self.modified_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if memory entry has expired"""
        if self.ttl is None:
            return False
        
        return time.time() - self.created_at > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'key': self.key,
            'value': self.value,
            'memory_type': self.memory_type.value,
            'scope': self.scope.value,
            'created_at': self.created_at,
            'accessed_at': self.accessed_at,
            'modified_at': self.modified_at,
            'access_count': self.access_count,
            'ttl': self.ttl,
            'expired': self.expired
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        entry = cls(
            key=data['key'],
            value=data['value'],
            memory_type=MemoryType(data['memory_type']),
            scope=MemoryScope(data['scope']),
            ttl=data.get('ttl')
        )
        entry.created_at = data['created_at']
        entry.accessed_at = data['accessed_at']
        entry.modified_at = data['modified_at']
        entry.access_count = data['access_count']
        entry.expired = data.get('expired', False)
        return entry


class LyricLawyerMemory:
    """
    Main memory management system for LyricLawyer
    """
    
    def __init__(self, storage_dir: str = "./data/memory"):
        self.storage_dir = storage_dir
        self.session_memory = {}  # In-memory storage for current session
        self.persistent_cache = {}  # Cache for persistent memory
        self.adk_memory_integration = {}  # Integration with ADK conversation memory
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load persistent memory
        self._load_persistent_memory()
    
    def store(self, key: str, value: Any, memory_type: MemoryType, 
              scope: MemoryScope = MemoryScope.TEMPORARY, ttl: int = None, 
              user_id: str = None) -> bool:
        """
        Store a value in memory
        
        Args:
            key: Memory key identifier
            value: Value to store
            memory_type: Type of memory
            scope: Persistence scope
            ttl: Time to live in seconds
            user_id: Optional user identifier
            
        Returns:
            True if stored successfully
        """
        try:
            # Create namespaced key
            namespaced_key = self._create_namespaced_key(key, memory_type, user_id)
            
            # Create memory entry
            entry = MemoryEntry(namespaced_key, value, memory_type, scope, ttl)
            
            # Store based on scope
            if scope == MemoryScope.TEMPORARY:
                self.session_memory[namespaced_key] = entry
            
            elif scope == MemoryScope.PERSISTENT:
                self.persistent_cache[namespaced_key] = entry
                self._save_persistent_entry(entry)
            
            elif scope == MemoryScope.GLOBAL:
                # Global memory is persistent but shared
                global_key = f"global_{key}"
                entry.key = global_key
                self.persistent_cache[global_key] = entry
                self._save_persistent_entry(entry)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Memory storage failed: {e}")
            return False
    
    def retrieve(self, key: str, memory_type: MemoryType, user_id: str = None) -> Optional[Any]:
        """
        Retrieve a value from memory
        
        Args:
            key: Memory key identifier
            memory_type: Type of memory
            user_id: Optional user identifier
            
        Returns:
            Retrieved value or None if not found
        """
        # Try different key variations
        keys_to_try = [
            self._create_namespaced_key(key, memory_type, user_id),
            f"global_{key}",  # Try global scope
            key  # Try raw key
        ]
        
        for namespaced_key in keys_to_try:
            # Check session memory first
            if namespaced_key in self.session_memory:
                entry = self.session_memory[namespaced_key]
                value = entry.access()
                if value is not None:
                    return value
                else:
                    # Clean up expired entries
                    del self.session_memory[namespaced_key]
            
            # Check persistent cache
            if namespaced_key in self.persistent_cache:
                entry = self.persistent_cache[namespaced_key]
                value = entry.access()
                if value is not None:
                    return value
                else:
                    # Clean up expired entries
                    del self.persistent_cache[namespaced_key]
                    self._delete_persistent_entry(namespaced_key)
            
            # Try loading from disk
            loaded_entry = self._load_persistent_entry(namespaced_key)
            if loaded_entry:
                value = loaded_entry.access()
                if value is not None:
                    # Cache it for faster access
                    self.persistent_cache[namespaced_key] = loaded_entry
                    return value
        
        return None
    
    def store_analysis_result(self, lyrics: str, analysis_result: Dict[str, Any], 
                            user_id: str = None) -> str:
        """
        Store analysis result for future reference
        
        Args:
            lyrics: Original lyrics analyzed
            analysis_result: Complete analysis result
            user_id: Optional user identifier
            
        Returns:
            Analysis ID for future reference
        """
        # Create unique analysis ID
        lyrics_hash = hashlib.md5(lyrics.encode()).hexdigest()[:8]
        analysis_id = f"analysis_{lyrics_hash}_{int(time.time())}"
        
        # Prepare analysis record
        analysis_record = {
            'analysis_id': analysis_id,
            'lyrics_preview': lyrics[:100] + ('...' if len(lyrics) > 100 else ''),
            'overall_risk': analysis_result.get('overall_risk', 'UNKNOWN'),
            'flagged_phrases': analysis_result.get('flagged_phrases', 0),
            'phrases_analyzed': analysis_result.get('phrases_analyzed', 0),
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'full_result': analysis_result
        }
        
        # Store in analysis history
        self.store(
            key=analysis_id,
            value=analysis_record,
            memory_type=MemoryType.ANALYSIS_HISTORY,
            scope=MemoryScope.PERSISTENT,
            ttl=30*24*3600,  # Keep for 30 days
            user_id=user_id
        )
        
        # Update flagged phrases database
        if analysis_result.get('similarity_results'):
            self._update_flagged_phrases(analysis_result['similarity_results'], user_id)
        
        return analysis_id
    
    def get_analysis_history(self, user_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent analysis history
        
        Args:
            user_id: Optional user identifier
            limit: Maximum number of results
            
        Returns:
            List of recent analysis records
        """
        history = []
        
        # Search through persistent cache
        for key, entry in self.persistent_cache.items():
            if (entry.memory_type == MemoryType.ANALYSIS_HISTORY and 
                not entry.is_expired() and
                (user_id is None or user_id in key)):
                
                history.append(entry.value)
        
        # Sort by timestamp and limit
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return history[:limit]
    
    def store_user_preferences(self, preferences: Dict[str, Any], user_id: str) -> bool:
        """
        Store user preferences
        
        Args:
            preferences: User preference dictionary
            user_id: User identifier
            
        Returns:
            True if stored successfully
        """
        return self.store(
            key="preferences",
            value=preferences,
            memory_type=MemoryType.USER_PREFERENCES,
            scope=MemoryScope.PERSISTENT,
            user_id=user_id
        )
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences with defaults
        
        Args:
            user_id: User identifier
            
        Returns:
            User preferences dictionary
        """
        preferences = self.retrieve("preferences", MemoryType.USER_PREFERENCES, user_id)
        
        if preferences is None:
            # Return default preferences
            preferences = {
                'similarity_threshold': 0.7,
                'preserve_rhyme': True,
                'analysis_depth': 'standard',
                'show_warnings': True,
                'auto_save_results': True
            }
        
        return preferences
    
    def integrate_with_adk_memory(self, agent_name: str, conversation_data: Dict[str, Any]) -> None:
        """
        Integrate with ADK's conversation memory
        
        Args:
            agent_name: Name of the ADK agent
            conversation_data: Conversation memory data from ADK
        """
        integration_key = f"adk_{agent_name}_context"
        
        self.adk_memory_integration[integration_key] = {
            'agent_name': agent_name,
            'conversation_data': conversation_data,
            'last_updated': time.time()
        }
        
        # Store important context persistently
        if conversation_data.get('important_context'):
            self.store(
                key=integration_key,
                value=conversation_data,
                memory_type=MemoryType.SESSION,
                scope=MemoryScope.TEMPORARY,
                ttl=3600  # 1 hour
            )
    
    def get_context_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Get relevant context for an ADK agent
        
        Args:
            agent_name: Name of the ADK agent
            
        Returns:
            Context dictionary for the agent
        """
        integration_key = f"adk_{agent_name}_context"
        
        # Get from integration cache
        if integration_key in self.adk_memory_integration:
            return self.adk_memory_integration[integration_key]
        
        # Try retrieving from memory
        context = self.retrieve(integration_key, MemoryType.SESSION)
        return context or {}
    
    def cleanup_expired_memory(self) -> int:
        """
        Clean up expired memory entries
        
        Returns:
            Number of entries cleaned up
        """
        cleaned_count = 0
        
        # Clean session memory
        expired_session_keys = []
        for key, entry in self.session_memory.items():
            if entry.is_expired():
                expired_session_keys.append(key)
        
        for key in expired_session_keys:
            del self.session_memory[key]
            cleaned_count += 1
        
        # Clean persistent cache
        expired_persistent_keys = []
        for key, entry in self.persistent_cache.items():
            if entry.is_expired():
                expired_persistent_keys.append(key)
        
        for key in expired_persistent_keys:
            del self.persistent_cache[key]
            self._delete_persistent_entry(key)
            cleaned_count += 1
        
        return cleaned_count
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        
        stats = {
            'session_entries': len(self.session_memory),
            'persistent_entries': len(self.persistent_cache),
            'adk_integrations': len(self.adk_memory_integration),
            'memory_types': {},
            'total_size_estimate': 0
        }
        
        # Count by memory type
        all_entries = list(self.session_memory.values()) + list(self.persistent_cache.values())
        
        for entry in all_entries:
            memory_type = entry.memory_type.value
            stats['memory_types'][memory_type] = stats['memory_types'].get(memory_type, 0) + 1
            
            # Rough size estimate
            stats['total_size_estimate'] += len(str(entry.value))
        
        return stats
    
    def _create_namespaced_key(self, key: str, memory_type: MemoryType, user_id: str = None) -> str:
        """Create namespaced key for storage"""
        
        namespace_parts = [memory_type.value]
        
        if user_id:
            namespace_parts.append(f"user_{user_id}")
        
        namespace_parts.append(key)
        
        return "_".join(namespace_parts)
    
    def _save_persistent_entry(self, entry: MemoryEntry) -> None:
        """Save entry to persistent storage"""
        
        file_path = os.path.join(self.storage_dir, f"{entry.key}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(entry.to_dict(), f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save persistent entry: {e}")
    
    def _load_persistent_entry(self, key: str) -> Optional[MemoryEntry]:
        """Load entry from persistent storage"""
        
        file_path = os.path.join(self.storage_dir, f"{key}.json")
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return MemoryEntry.from_dict(data)
        except Exception as e:
            print(f"⚠️ Failed to load persistent entry: {e}")
            return None
    
    def _delete_persistent_entry(self, key: str) -> None:
        """Delete entry from persistent storage"""
        
        file_path = os.path.join(self.storage_dir, f"{key}.json")
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Failed to delete persistent entry: {e}")
    
    def _load_persistent_memory(self) -> None:
        """Load all persistent memory from disk"""
        
        if not os.path.exists(self.storage_dir):
            return
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                key = filename[:-5]  # Remove .json extension
                entry = self._load_persistent_entry(key)
                if entry and not entry.is_expired():
                    self.persistent_cache[key] = entry
    
    def _update_flagged_phrases(self, similarity_results: List[Dict], user_id: str = None) -> None:
        """Update the flagged phrases database"""
        
        flagged_phrases = self.retrieve("flagged_phrases", MemoryType.FLAGGED_PHRASES) or []
        
        for result in similarity_results:
            if result.get('flagged'):
                phrase_data = result['phrase']
                flagged_entry = {
                    'phrase': phrase_data['text'],
                    'flagged_at': datetime.now().isoformat(),
                    'similarity_score': result.get('similarity_score', 0),
                    'user_id': user_id
                }
                
                # Avoid duplicates
                if not any(fp['phrase'] == flagged_entry['phrase'] for fp in flagged_phrases):
                    flagged_phrases.append(flagged_entry)
        
        # Keep only recent flagged phrases (last 1000)
        flagged_phrases = flagged_phrases[-1000:]
        
        self.store(
            key="flagged_phrases",
            value=flagged_phrases,
            memory_type=MemoryType.FLAGGED_PHRASES,
            scope=MemoryScope.GLOBAL,
            ttl=90*24*3600  # Keep for 90 days
        )


# Global memory instance
_memory_system = LyricLawyerMemory()

def get_memory_system() -> LyricLawyerMemory:
    """Get the global memory system instance"""
    return _memory_system

def store_analysis_result(lyrics: str, analysis_result: Dict[str, Any], user_id: str = None) -> str:
    """Store analysis result (convenience function)"""
    return _memory_system.store_analysis_result(lyrics, analysis_result, user_id)

def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get user preferences (convenience function)"""
    return _memory_system.get_user_preferences(user_id)

def cleanup_memory() -> int:
    """Cleanup expired memory (convenience function)"""
    return _memory_system.cleanup_expired_memory()