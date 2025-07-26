# LyricLawyer - Data Model & Architecture

## Core Data Structures

### 1. User Input Model
```python
class UserLyrics:
    id: str
    user_id: str (optional)
    raw_text: str
    title: str (optional)
    artist: str (optional)
    timestamp: datetime
    session_id: str
```

### 2. Lyric Analysis Model
```python
class LyricAnalysis:
    id: str
    lyrics_id: str
    lines: List[LyricLine]
    overall_risk_score: float (0.0-1.0)
    risk_level: RiskLevel (LOW, MEDIUM, HIGH)
    analysis_timestamp: datetime
    processing_time: float
```

### 3. Individual Line Analysis
```python
class LyricLine:
    line_number: int
    text: str
    risk_score: float (0.0-1.0)
    flagged: bool
    potential_matches: List[CopyrightMatch]
    suggested_alternatives: List[str]
```

### 4. Copyright Match Model
```python
class CopyrightMatch:
    id: str
    reference_song: str
    reference_artist: str
    matching_phrase: str
    similarity_score: float (0.0-1.0)
    confidence_level: ConfidenceLevel (LOW, MEDIUM, HIGH)
    source_database: str
    match_type: MatchType (EXACT, SIMILAR, CONCEPTUAL)
```

### 5. Reference Database Model
```python
class CopyrightedSong:
    id: str
    title: str
    artist: str
    album: str (optional)
    release_year: int
    lyrics_text: str
    protected_phrases: List[str]
    litigation_history: bool
    popularity_score: float
    last_updated: datetime
```

## Data Flow Architecture

### Input Processing Flow
```
User Input → Text Sanitization → Line Segmentation → Phrase Extraction
```

### Analysis Pipeline
```
Phrase Extraction → Similarity Detection → Risk Assessment → Alternative Generation
```

### Detailed Data Flow

#### 1. Input Processing
- **Sanitization**: Remove special characters, normalize spacing
- **Segmentation**: Split lyrics into individual lines and verses
- **Tokenization**: Extract meaningful phrases (2-8 words)

#### 2. Similarity Detection Engine
- **Exact Match**: Direct string comparison with known lyrics
- **Semantic Similarity**: Gemini API for contextual similarity
- **Structural Analysis**: Rhyme scheme and meter comparison
- **Weighted Scoring**: Combine multiple similarity metrics

#### 3. Risk Assessment Algorithm
```python
def calculate_risk_score(matches: List[CopyrightMatch]) -> float:
    base_score = max([match.similarity_score for match in matches])
    popularity_weight = get_song_popularity_weight(matches)
    litigation_weight = get_litigation_history_weight(matches)
    return min(1.0, base_score * popularity_weight * litigation_weight)
```

#### 4. Alternative Generation
- **Context Preservation**: Maintain rhyme scheme and syllable count
- **Semantic Similarity**: Keep original meaning while changing expression
- **Multiple Options**: Generate 3-5 alternatives per flagged line

## Database Schema

### Primary Tables
```sql
-- User sessions (optional for anonymous usage)
users (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255),
    created_at TIMESTAMP
);

-- Lyric submissions
lyrics_submissions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    raw_text TEXT,
    title VARCHAR(255),
    created_at TIMESTAMP
);

-- Analysis results
lyric_analyses (
    id UUID PRIMARY KEY,
    submission_id UUID REFERENCES lyrics_submissions(id),
    overall_risk_score FLOAT,
    risk_level VARCHAR(20),
    processing_time FLOAT,
    created_at TIMESTAMP
);

-- Individual line analysis
line_analyses (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES lyric_analyses(id),
    line_number INTEGER,
    text TEXT,
    risk_score FLOAT,
    flagged BOOLEAN
);

-- Copyright matches
copyright_matches (
    id UUID PRIMARY KEY,
    line_analysis_id UUID REFERENCES line_analyses(id),
    reference_song VARCHAR(255),
    reference_artist VARCHAR(255),
    matching_phrase TEXT,
    similarity_score FLOAT,
    confidence_level VARCHAR(20)
);

-- Reference song database
reference_songs (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    artist VARCHAR(255),
    lyrics_text TEXT,
    popularity_score FLOAT,
    litigation_history BOOLEAN,
    last_updated TIMESTAMP
);
```

## API Response Models

### Analysis Response
```json
{
  "analysis_id": "uuid",
  "overall_risk": {
    "score": 0.75,
    "level": "HIGH",
    "summary": "Multiple high-similarity matches found"
  },
  "line_results": [
    {
      "line_number": 1,
      "text": "Original lyric line",
      "flagged": true,
      "risk_score": 0.85,
      "matches": [
        {
          "reference_song": "Song Title",
          "reference_artist": "Artist Name",
          "similarity_score": 0.92,
          "confidence": "HIGH",
          "explanation": "Nearly identical phrasing"
        }
      ],
      "alternatives": [
        "Alternative phrasing option 1",
        "Alternative phrasing option 2",
        "Alternative phrasing option 3"
      ]
    }
  ],
  "processing_time": 12.5,
  "disclaimer": "This tool provides guidance only..."
}
```

## Memory & Caching Strategy

### Session Memory
- Store user's current analysis session
- Cache Gemini API responses for identical queries
- Remember user's preferred alternative suggestions

### Reference Database Caching
- Cache frequently accessed song lyrics
- Pre-compute similarity vectors for popular songs
- Update cache based on usage patterns

### Performance Optimization
- Index reference songs by key phrases
- Use similarity hashing for fast initial filtering
- Implement result pagination for large analyses