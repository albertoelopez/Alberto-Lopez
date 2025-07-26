# LyricLawyer Architecture Overview

## System Design Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LyricLawyer System Architecture                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    HTTP POST     ┌─────────────────────────────────────────────┐
│   Web Interface │ ────────────────→ │              Agent System                   │
│  (FastAPI + UI) │                  │        (Google ADK Framework)              │
└─────────────────┘                  └─────────────────────────────────────────────┘
                                                           │
                                     ┌─────────────────────┼─────────────────────┐
                                     │                     │                     │
                                     ▼                     ▼                     ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Planner Agent   │    │Similarity Agent │    │ Risk Agent      │    │Alternatives     │
│                 │    │                 │    │                 │    │Agent            │
│ • Task breakdown│    │ • Phrase        │    │ • Copyright     │    │                 │
│ • Prioritization│    │   analysis      │    │   risk levels   │    │ • Creative      │
│ • Workflow      │    │ • Reference     │    │ • Legal         │    │   alternatives  │
│   orchestration │    │   matching      │    │   guidance      │    │ • Rhyme         │
└─────────────────┘    └─────────────────┘    └─────────────────┘    │   preservation  │
          │                       │                       │          └─────────────────┘
          │                       │                       │                     │
          └───────────────────────┼───────────────────────┼─────────────────────┘
                                  │                       │
                                  ▼                       ▼
                    ┌─────────────────────────────────────────────┐
                    │         Coordinator Agent                    │
                    │                                             │
                    │ • Synthesizes all agent results             │
                    │ • Generates final comprehensive report      │
                    │ • Ensures workflow completion               │
                    └─────────────────────────────────────────────┘
                                            │
    ┌───────────────────────────────────────┼───────────────────────────────────────┐
    │                                       │                                       │
    ▼                                       ▼                                       ▼
┌─────────────────┐         ┌─────────────────────────────┐         ┌─────────────────┐
│ Memory System   │         │       Tool Ecosystem        │         │  External APIs  │
│                 │         │                             │         │                 │
│ • Session data  │         │ • Similarity Engine         │         │ • Google Gemini │
│ • Analysis      │         │ • Reference Database        │         │   API (2.0)     │
│   history       │         │ • Risk Assessor             │         │ • Content       │
│ • User          │         │ • Alternative Generator     │         │   analysis      │
│   preferences   │         │ • Input Validator           │         │ • Semantic      │
│ • Workflow      │         │ • Error Handler             │         │   matching      │
│   state         │         │                             │         │                 │
└─────────────────┘         └─────────────────────────────┘         └─────────────────┘
```

## Component Breakdown

### 1. Web Interface (FastAPI + Bootstrap)
**File**: `src/web_interface.py`, `src/templates/`

- **FastAPI Backend**: REST endpoints for lyric analysis
- **Responsive UI**: Bootstrap-based templates for desktop/mobile
- **Real-time Processing**: Shows agent workflow progress
- **Error Handling**: User-friendly error messages and validation

### 2. Multi-Agent System (Google ADK)
**File**: `src/agent.py`

The core of our agentic architecture using Google's Agent Development Kit:

#### **Planner Agent**
- **Role**: Task decomposition and workflow orchestration
- **Tools**: `sanitize_lyrics()`, `extract_phrases()`
- **Prompt**: Systematic analysis planning and phrase prioritization
- **Output**: Structured analysis plan and phrase extraction strategy

#### **Similarity Agent** 
- **Role**: Copyright similarity detection
- **Tools**: `analyze_similarity()`
- **Prompt**: Expert-level copyright similarity analysis
- **Output**: Detailed similarity scores and potential matches

#### **Risk Agent**
- **Role**: Legal risk assessment and strategic guidance
- **Tools**: `assess_copyright_risk()`
- **Prompt**: Music copyright advisory with risk levels
- **Output**: Risk levels (LOW/MEDIUM/HIGH/CRITICAL) with explanations

#### **Alternatives Agent**
- **Role**: Creative alternative generation
- **Tools**: `generate_alternatives()`
- **Prompt**: Creative songwriting assistant maintaining artistic intent
- **Output**: Multiple original alternatives preserving rhyme/rhythm

#### **Coordinator Agent**
- **Role**: Result synthesis and final report generation
- **Tools**: None (orchestration only)
- **Prompt**: Synthesizes multi-agent results into coherent analysis
- **Output**: Comprehensive final report with recommendations

### 3. Tool Ecosystem
**Files**: `src/tools/*.py`

#### **Similarity Engine** (`similarity_engine.py`)
- **Advanced Algorithms**: 8 different similarity detection methods
- **Weighted Scoring**: Edit Distance, Jaccard, Cosine, N-gram, Semantic, Rhyme
- **Gemini Integration**: Semantic analysis for contextual similarity
- **Performance**: Handles batch processing efficiently

#### **Reference Database** (`reference_database.py`)
- **SQLite Storage**: 10+ popular songs with metadata
- **Structured Data**: Artist, title, phrases, copyright info
- **Query Interface**: Fast phrase lookup and similarity matching
- **Legal Compliance**: Only reference phrases, no full lyrics

#### **Risk Assessor** (`risk_assessor.py`)
- **Multi-factor Analysis**: Similarity score + song popularity + legal history
- **Dynamic Thresholds**: Adaptive risk levels based on context
- **Explanations**: Plain-English risk reasoning
- **Actionable Guidance**: Specific recommendations per risk level

#### **Alternative Generator** (`alternative_generator.py`)
- **Gemini-Powered**: Uses advanced language model for creativity
- **Rhyme Preservation**: Maintains original song structure
- **Quality Scoring**: Ranks alternatives by creativity and safety
- **Fallback System**: Ensures alternatives even if API fails

### 4. Memory System (ADK Integration)
**File**: `src/memory.py`

- **Session Memory**: Temporary analysis data and user preferences
- **Persistent Memory**: Cross-session learning and pattern recognition  
- **Global Memory**: System-wide insights and optimization data
- **Workflow State**: Tracks agent execution progress and results

### 5. Executor & Orchestration
**Files**: `src/executor.py`, `src/workflow_orchestrator.py`

- **Task Management**: Dependency tracking and execution order
- **Progress Monitoring**: Real-time workflow status updates
- **Error Recovery**: Retry logic and graceful degradation
- **Performance Logging**: Detailed execution metrics

### 6. External Integrations

#### **Google Gemini API**
- **Model**: `gemini-2.0-flash-exp` for optimal performance
- **Use Cases**: Semantic similarity, creative alternatives, contextual analysis
- **Rate Limiting**: Built-in throttling and error handling
- **Security**: API key management through environment variables

## Data Flow

1. **Input Processing**: User lyrics → Input validation → Sanitization
2. **Planning Phase**: Planner Agent → Task breakdown → Phrase extraction
3. **Analysis Phase**: Similarity Agent → Reference matching → Scoring
4. **Assessment Phase**: Risk Agent → Legal evaluation → Risk levels
5. **Generation Phase**: Alternatives Agent → Creative alternatives → Quality ranking
6. **Synthesis Phase**: Coordinator Agent → Final report → User presentation

## Observability & Monitoring

### **Logging System**
- **Agent Activities**: Each agent logs decisions and reasoning
- **Performance Metrics**: Response times, API calls, success rates
- **Error Tracking**: Detailed error context and recovery attempts
- **User Analytics**: Usage patterns and system performance

### **Error Handling**
- **Graceful Degradation**: System continues with reduced functionality
- **User Communication**: Clear error messages and recovery suggestions
- **Automatic Retry**: Transient failures handled transparently
- **Fallback Systems**: Alternative approaches when primary tools fail

## Security & Compliance

### **Data Protection**
- **No Lyrics Storage**: Only analysis results stored temporarily
- **API Security**: Secure key management and rate limiting
- **Input Validation**: Comprehensive sanitization and validation
- **Error Sanitization**: No sensitive data in error messages

### **Copyright Compliance**
- **Reference Only**: Database contains phrases, not full lyrics
- **Fair Use**: Analysis for educational/advisory purposes
- **Legal Disclaimers**: Clear limitations and legal advice requirements
- **User Responsibility**: Emphasizes user ownership of creative decisions

## Scalability Considerations

### **Performance Optimization**
- **Asynchronous Processing**: Non-blocking agent execution
- **Caching Strategy**: Reference database and common analyses
- **Batch Processing**: Efficient handling of multiple phrases
- **Resource Management**: Memory cleanup and connection pooling

### **Future Enhancements**
- **Database Expansion**: Larger reference song database
- **Advanced Analytics**: Machine learning for pattern recognition
- **Multi-language Support**: International copyright analysis
- **Real-time Collaboration**: Multiple users, shared sessions

This architecture demonstrates a truly agentic system where multiple specialized AI agents collaborate autonomously to solve complex copyright analysis challenges, each contributing unique expertise while maintaining system cohesion through the coordinator pattern.