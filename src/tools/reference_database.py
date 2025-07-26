"""
Reference Database System

This module manages the reference database of copyrighted songs and lyrics
for similarity comparison and matching.
"""

import json
import os
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum


class Genre(Enum):
    """Music genres for categorization"""
    POP = "pop"
    ROCK = "rock"
    HIP_HOP = "hip_hop"
    RNB = "rnb"
    COUNTRY = "country"
    ELECTRONIC = "electronic"
    ALTERNATIVE = "alternative"
    JAZZ = "jazz"
    FOLK = "folk"
    CLASSICAL = "classical"
    OTHER = "other"


class Era(Enum):
    """Musical eras for temporal categorization"""
    CLASSIC_50S_60S = "1950s-1960s"
    GOLDEN_70S_80S = "1970s-1980s"
    ALTERNATIVE_90S = "1990s"
    DIGITAL_2000S = "2000s"
    STREAMING_2010S = "2010s"
    MODERN_2020S = "2020s"


@dataclass
class SongRecord:
    """Individual song record in the database"""
    song_id: str
    title: str
    artist: str
    album: str
    release_year: int
    genre: Genre
    era: Era
    lyrics_sample: str  # Key lyrical phrases
    full_lyrics: str    # Complete lyrics (if available)
    popularity_score: float  # 0.0-1.0 based on commercial success
    litigation_history: bool  # Has this song been involved in copyright disputes?
    similar_songs: List[str]  # IDs of similar songs
    key_phrases: List[str]    # Most memorable/distinctive phrases
    rhyme_scheme: str         # ABAB, AABA, etc.
    created_at: str
    updated_at: str
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


class ReferenceDatabase:
    """
    Main reference database class for managing copyrighted song data
    """
    
    def __init__(self, db_path: str = "./data/reference_songs.db"):
        self.db_path = db_path
        self.connection = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
        # Load default songs if database is empty
        if self._is_database_empty():
            self._populate_default_songs()
    
    def _initialize_database(self):
        """Initialize SQLite database with proper schema"""
        
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        
        cursor = self.connection.cursor()
        
        # Create main songs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                song_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                album TEXT,
                release_year INTEGER,
                genre TEXT,
                era TEXT,
                lyrics_sample TEXT,
                full_lyrics TEXT,
                popularity_score REAL,
                litigation_history BOOLEAN,
                rhyme_scheme TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Create phrases table for fast phrase lookup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS key_phrases (
                phrase_id TEXT PRIMARY KEY,
                song_id TEXT,
                phrase_text TEXT NOT NULL,
                phrase_importance REAL,
                phrase_length INTEGER,
                FOREIGN KEY (song_id) REFERENCES songs (song_id)
            )
        """)
        
        # Create similarity relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS song_similarities (
                similarity_id TEXT PRIMARY KEY,
                song_id_1 TEXT,
                song_id_2 TEXT,
                similarity_score REAL,
                similarity_type TEXT,
                FOREIGN KEY (song_id_1) REFERENCES songs (song_id),
                FOREIGN KEY (song_id_2) REFERENCES songs (song_id)
            )
        """)
        
        # Create indexes for fast searching
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_artist ON songs (artist)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_genre ON songs (genre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_era ON songs (era)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_popularity ON songs (popularity_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_phrase_text ON key_phrases (phrase_text)")
        
        self.connection.commit()
    
    def _is_database_empty(self) -> bool:
        """Check if database is empty"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM songs")
        count = cursor.fetchone()[0]
        return count == 0
    
    def _populate_default_songs(self):
        """Populate database with default well-known songs"""
        
        default_songs = self._get_default_song_data()
        
        print(f"📚 Populating reference database with {len(default_songs)} songs...")
        
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        for song_data in default_songs:
            # Add timestamp fields required by SongRecord
            song_data['created_at'] = timestamp
            song_data['updated_at'] = timestamp
            song_record = SongRecord(**song_data)
            self.add_song(song_record)
        
        print("✅ Reference database populated successfully")
    
    def add_song(self, song: SongRecord) -> bool:
        """
        Add a song to the database
        
        Args:
            song: SongRecord instance
            
        Returns:
            True if added successfully
        """
        try:
            cursor = self.connection.cursor()
            
            # Insert main song record
            cursor.execute("""
                INSERT OR REPLACE INTO songs 
                (song_id, title, artist, album, release_year, genre, era, 
                 lyrics_sample, full_lyrics, popularity_score, litigation_history,
                 rhyme_scheme, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                song.song_id, song.title, song.artist, song.album, song.release_year,
                song.genre.value, song.era.value, song.lyrics_sample, song.full_lyrics,
                song.popularity_score, song.litigation_history, song.rhyme_scheme,
                song.created_at, song.updated_at
            ))
            
            # Insert key phrases
            for i, phrase in enumerate(song.key_phrases):
                phrase_id = f"{song.song_id}_phrase_{i}"
                cursor.execute("""
                    INSERT OR REPLACE INTO key_phrases
                    (phrase_id, song_id, phrase_text, phrase_importance, phrase_length)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    phrase_id, song.song_id, phrase.lower(), 
                    1.0 - (i * 0.1), len(phrase.split())
                ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to add song {song.title}: {e}")
            return False
    
    def search_songs(self, query: str, search_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search songs in the database
        
        Args:
            query: Search query
            search_type: "title", "artist", "phrase", "all"
            limit: Maximum results to return
            
        Returns:
            List of matching song records
        """
        cursor = self.connection.cursor()
        query_lower = query.lower()
        
        if search_type == "title":
            cursor.execute("""
                SELECT * FROM songs 
                WHERE LOWER(title) LIKE ? 
                ORDER BY popularity_score DESC
                LIMIT ?
            """, (f"%{query_lower}%", limit))
            
        elif search_type == "artist":
            cursor.execute("""
                SELECT * FROM songs 
                WHERE LOWER(artist) LIKE ? 
                ORDER BY popularity_score DESC
                LIMIT ?
            """, (f"%{query_lower}%", limit))
            
        elif search_type == "phrase":
            cursor.execute("""
                SELECT DISTINCT s.* FROM songs s
                JOIN key_phrases p ON s.song_id = p.song_id
                WHERE LOWER(p.phrase_text) LIKE ?
                ORDER BY s.popularity_score DESC
                LIMIT ?
            """, (f"%{query_lower}%", limit))
            
        else:  # search_type == "all"
            cursor.execute("""
                SELECT DISTINCT s.*, 
                       CASE 
                           WHEN LOWER(s.title) LIKE ? THEN 3
                           WHEN LOWER(s.artist) LIKE ? THEN 2
                           ELSE 1
                       END as relevance_score
                FROM songs s
                LEFT JOIN key_phrases p ON s.song_id = p.song_id
                WHERE LOWER(s.title) LIKE ? 
                   OR LOWER(s.artist) LIKE ?
                   OR LOWER(s.lyrics_sample) LIKE ?
                   OR LOWER(p.phrase_text) LIKE ?
                ORDER BY relevance_score DESC, s.popularity_score DESC
                LIMIT ?
            """, (f"%{query_lower}%", f"%{query_lower}%", f"%{query_lower}%", 
                  f"%{query_lower}%", f"%{query_lower}%", f"%{query_lower}%", limit))
        
        results = []
        for row in cursor.fetchall():
            song_dict = dict(row)
            # Convert back to proper types
            song_dict['genre'] = Genre(song_dict['genre'])
            song_dict['era'] = Era(song_dict['era'])
            song_dict['key_phrases'] = self._get_song_phrases(song_dict['song_id'])
            results.append(song_dict)
        
        return results
    
    def find_similar_phrases(self, phrase: str, similarity_threshold: float = 0.7, 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find phrases similar to the input phrase
        
        Args:
            phrase: Input phrase to match against
            similarity_threshold: Minimum similarity score
            limit: Maximum results
            
        Returns:
            List of similar phrases with metadata
        """
        from .similarity_engine import get_similarity_engine
        
        cursor = self.connection.cursor()
        cursor.execute("SELECT phrase_text, song_id, phrase_importance FROM key_phrases")
        
        similarity_engine = get_similarity_engine()
        similar_phrases = []
        
        for row in cursor.fetchall():
            db_phrase = row[0]
            song_id = row[1]
            importance = row[2]
            
            # Calculate similarity
            similarity_result = similarity_engine.calculate_comprehensive_similarity(phrase, db_phrase)
            
            if similarity_result['overall_similarity'] >= similarity_threshold:
                # Get song information
                song_info = self.get_song_by_id(song_id)
                
                similar_phrases.append({
                    'matched_phrase': db_phrase,
                    'similarity_score': similarity_result['overall_similarity'],
                    'risk_level': similarity_result['risk_level'],
                    'phrase_importance': importance,
                    'song_info': song_info,
                    'algorithm_details': similarity_result['algorithm_results']
                })
        
        # Sort by similarity score and return top matches
        similar_phrases.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_phrases[:limit]
    
    def get_song_by_id(self, song_id: str) -> Optional[Dict[str, Any]]:
        """Get song by ID"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM songs WHERE song_id = ?", (song_id,))
        row = cursor.fetchone()
        
        if row:
            song_dict = dict(row)
            song_dict['genre'] = Genre(song_dict['genre'])
            song_dict['era'] = Era(song_dict['era'])
            song_dict['key_phrases'] = self._get_song_phrases(song_id)
            return song_dict
        
        return None
    
    def get_songs_by_genre(self, genre: Genre, limit: int = 20) -> List[Dict[str, Any]]:
        """Get songs by genre"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM songs 
            WHERE genre = ? 
            ORDER BY popularity_score DESC 
            LIMIT ?
        """, (genre.value, limit))
        
        results = []
        for row in cursor.fetchall():
            song_dict = dict(row)
            song_dict['genre'] = Genre(song_dict['genre'])
            song_dict['era'] = Era(song_dict['era'])
            song_dict['key_phrases'] = self._get_song_phrases(song_dict['song_id'])
            results.append(song_dict)
        
        return results
    
    def get_high_risk_songs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get songs with litigation history or high popularity (high risk for infringement)"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM songs 
            WHERE litigation_history = 1 OR popularity_score >= 0.8
            ORDER BY popularity_score DESC, litigation_history DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            song_dict = dict(row)
            song_dict['genre'] = Genre(song_dict['genre'])
            song_dict['era'] = Era(song_dict['era'])
            song_dict['key_phrases'] = self._get_song_phrases(song_dict['song_id'])
            results.append(song_dict)
        
        return results
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        cursor = self.connection.cursor()
        
        # Total songs
        cursor.execute("SELECT COUNT(*) FROM songs")
        total_songs = cursor.fetchone()[0]
        
        # Songs by genre
        cursor.execute("SELECT genre, COUNT(*) FROM songs GROUP BY genre")
        genre_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Songs by era
        cursor.execute("SELECT era, COUNT(*) FROM songs GROUP BY era")
        era_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total phrases
        cursor.execute("SELECT COUNT(*) FROM key_phrases")
        total_phrases = cursor.fetchone()[0]
        
        # High risk songs (litigation history)
        cursor.execute("SELECT COUNT(*) FROM songs WHERE litigation_history = 1")
        litigation_songs = cursor.fetchone()[0]
        
        # Average popularity
        cursor.execute("SELECT AVG(popularity_score) FROM songs")
        avg_popularity = cursor.fetchone()[0] or 0.0
        
        return {
            'total_songs': total_songs,
            'total_phrases': total_phrases,
            'genre_distribution': genre_counts,
            'era_distribution': era_counts,
            'high_risk_songs': litigation_songs,
            'average_popularity': round(avg_popularity, 2),
            'database_file': self.db_path
        }
    
    def _get_song_phrases(self, song_id: str) -> List[str]:
        """Get key phrases for a song"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT phrase_text FROM key_phrases 
            WHERE song_id = ? 
            ORDER BY phrase_importance DESC
        """, (song_id,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def _get_default_song_data(self) -> List[Dict[str, Any]]:
        """Get default song data for initial population"""
        
        return [
            # Pop Classics
            {
                'song_id': 'taylor_swift_shake_it_off',
                'title': 'Shake It Off',
                'artist': 'Taylor Swift',
                'album': '1989',
                'release_year': 2014,
                'genre': Genre.POP,
                'era': Era.STREAMING_2010S,
                'lyrics_sample': 'shake it off shake it off heartbreakers gonna break',
                'full_lyrics': '',
                'popularity_score': 0.95,
                'litigation_history': False,
                'similar_songs': [],
                'key_phrases': ['shake it off shake it off', 'heartbreakers gonna break', 'players gonna play', 'haters gonna hate'],
                'rhyme_scheme': 'ABAB'
            },
            {
                'song_id': 'taylor_swift_blank_space',
                'title': 'Blank Space',
                'artist': 'Taylor Swift',
                'album': '1989',
                'release_year': 2014,
                'genre': Genre.POP,
                'era': Era.STREAMING_2010S,
                'lyrics_sample': 'i got a blank space baby and i write your name',
                'full_lyrics': '',
                'popularity_score': 0.93,
                'litigation_history': False,
                'similar_songs': [],
                'key_phrases': ['i got a blank space baby', 'write your name', 'long list of ex lovers', 'nightmare dressed like a daydream'],
                'rhyme_scheme': 'ABAB'
            },
            {
                'song_id': 'adele_rolling_in_the_deep',
                'title': 'Rolling in the Deep',
                'artist': 'Adele',
                'album': '21',
                'release_year': 2010,
                'genre': Genre.POP,
                'era': Era.STREAMING_2010S,
                'lyrics_sample': 'rolling in the deep you had my heart inside',
                'full_lyrics': '',
                'popularity_score': 0.92,
                'litigation_history': False,
                'similar_songs': [],
                'key_phrases': ['rolling in the deep', 'you had my heart inside', 'we could have had it all', 'tears are gonna fall'],
                'rhyme_scheme': 'ABCB'
            },
            
            # Classic Rock
            {
                'song_id': 'queen_bohemian_rhapsody',
                'title': 'Bohemian Rhapsody',
                'artist': 'Queen',
                'album': 'A Night at the Opera',
                'release_year': 1975,
                'genre': Genre.ROCK,
                'era': Era.GOLDEN_70S_80S,
                'lyrics_sample': 'is this the real life is this just fantasy',
                'full_lyrics': '',
                'popularity_score': 0.98,
                'litigation_history': True,
                'similar_songs': [],
                'key_phrases': ['is this the real life', 'is this just fantasy', 'caught in a landslide', 'no escape from reality'],
                'rhyme_scheme': 'ABCD'
            },
            {
                'song_id': 'led_zeppelin_stairway_to_heaven',
                'title': 'Stairway to Heaven',
                'artist': 'Led Zeppelin',
                'album': 'Led Zeppelin IV',
                'release_year': 1971,
                'genre': Genre.ROCK,
                'era': Era.GOLDEN_70S_80S,
                'lyrics_sample': 'stairway to heaven and she buying a stairway',
                'full_lyrics': '',
                'popularity_score': 0.97,
                'litigation_history': True,
                'similar_songs': [],
                'key_phrases': ['stairway to heaven', 'and she buying a stairway', 'all that glitters is gold', 'when all are one and one is all'],
                'rhyme_scheme': 'ABCB'
            },
            
            # Hip-Hop/R&B
            {
                'song_id': 'beyonce_crazy_in_love',
                'title': 'Crazy in Love',
                'artist': 'Beyoncé',
                'album': 'Dangerously in Love',
                'release_year': 2003,
                'genre': Genre.RNB,
                'era': Era.DIGITAL_2000S,
                'lyrics_sample': 'crazy in love got me looking so crazy right now',
                'full_lyrics': '',
                'popularity_score': 0.89,
                'litigation_history': False,
                'similar_songs': [],
                'key_phrases': ['crazy in love', 'got me looking so crazy', 'right now your love', 'uh oh uh oh uh oh'],
                'rhyme_scheme': 'AABA'
            },
            {
                'song_id': 'eminem_lose_yourself',
                'title': 'Lose Yourself',
                'artist': 'Eminem',
                'album': '8 Mile Soundtrack',
                'release_year': 2002,
                'genre': Genre.HIP_HOP,
                'era': Era.DIGITAL_2000S,
                'lyrics_sample': 'lose yourself in the music the moment you own it',
                'full_lyrics': '',
                'popularity_score': 0.94,
                'litigation_history': False,
                'similar_songs': [],
                'key_phrases': ['lose yourself in the music', 'the moment you own it', 'you only get one shot', 'do not miss your chance to blow'],
                'rhyme_scheme': 'AABB'
            },
            
            # Modern Hits
            {
                'song_id': 'ed_sheeran_shape_of_you',
                'title': 'Shape of You',
                'artist': 'Ed Sheeran',
                'album': '÷',
                'release_year': 2017,
                'genre': Genre.POP,
                'era': Era.MODERN_2020S,
                'lyrics_sample': 'shape of you i in love with your body',
                'full_lyrics': '',
                'popularity_score': 0.91,
                'litigation_history': True,
                'similar_songs': [],
                'key_phrases': ['shape of you', 'i in love with your body', 'every day discovering something', 'brand new push and pull like a magnet'],
                'rhyme_scheme': 'ABAB'
            },
            {
                'song_id': 'billie_eilish_bad_guy',
                'title': 'bad guy',
                'artist': 'Billie Eilish',
                'album': 'When We All Fall Asleep, Where Do We Go?',
                'release_year': 2019,
                'genre': Genre.ALTERNATIVE,
                'era': Era.MODERN_2020S,
                'lyrics_sample': 'i am the bad guy duh',
                'full_lyrics': '',
                'popularity_score': 0.88,
                'litigation_history': False,
                'similar_songs': [],
                'key_phrases': ['i am the bad guy', 'white shirt now red', 'my bloody nose', 'sleeping you on your tippy toes'],
                'rhyme_scheme': 'ABCB'
            },
            
            # Country
            {
                'song_id': 'dolly_parton_jolene',
                'title': 'Jolene',
                'artist': 'Dolly Parton',
                'album': 'Jolene',
                'release_year': 1973,
                'genre': Genre.COUNTRY,
                'era': Era.GOLDEN_70S_80S,
                'lyrics_sample': 'jolene jolene jolene jolene i begging you please',
                'full_lyrics': '',
                'popularity_score': 0.85,
                'litigation_history': False,
                'similar_songs': [],
                'key_phrases': ['jolene jolene jolene jolene', 'i begging you please', 'dont take my man', 'just because you can'],
                'rhyme_scheme': 'AAAA'
            }
        ]
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


# Global database instance
_reference_db = None

def get_reference_database() -> ReferenceDatabase:
    """Get the global reference database instance"""
    global _reference_db
    if _reference_db is None:
        _reference_db = ReferenceDatabase()
    return _reference_db

def search_reference_songs(query: str, search_type: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
    """Search reference songs (convenience function)"""
    return get_reference_database().search_songs(query, search_type, limit)

def find_similar_phrases(phrase: str, similarity_threshold: float = 0.7, limit: int = 10) -> List[Dict[str, Any]]:
    """Find similar phrases in reference database (convenience function)"""
    return get_reference_database().find_similar_phrases(phrase, similarity_threshold, limit)

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics (convenience function)"""
    return get_reference_database().get_database_statistics()