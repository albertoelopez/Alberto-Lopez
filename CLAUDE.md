# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **LyricLawyer** project for the Agentic AI App Hackathon - a copyright compliance checker for songwriters that uses AI to identify potential copyright infringement in original song lyrics.

## Hackathon Requirements

This project MUST fulfill these specific hackathon requirements:

### Required Architecture Components
- **Planner** (`src/planner.py`): Breaks down lyrics into analyzable segments and prioritizes risky phrases
- **Executor** (`src/executor.py`): Contains LLM prompt logic and tool-calling functionality using Gemini API
- **Memory** (`src/memory.py`): Stores flagged phrases, user rewrites, and session data (optional but recommended)

### Mandatory API Integration
- **Google Gemini API**: Must be used for similarity analysis and alternative lyric generation
- Store API key securely in `.env` file (never commit to repo)
- Demonstrate clear Gemini usage in code and documentation

### Required Documentation
- **ARCHITECTURE.md**: System design diagram and component explanation
- **EXPLANATION.md**: Agent reasoning process, memory usage, planning style, tool integration
- **DEMO.md**: Public video link (3-5 minutes) with specific timestamps:
  - 00:00–00:30: Intro & setup
  - 00:30–01:30: User input → Planning
  - 01:30–02:30: Tool calls & memory
  - 02:30–03:30: Final output & edge cases

## Core Functionality

### User Workflow
1. User inputs song lyrics (plain text)
2. System analyzes for copyright similarity using Gemini API
3. Provides plain-English explanations of potential issues
4. Suggests alternative phrasings that maintain meaning and rhyme scheme

### Technical Implementation
- Text processing: sanitization, line segmentation, phrase extraction
- Similarity detection: exact matching + semantic analysis via Gemini
- Risk scoring: weighted algorithm considering song popularity and litigation history
- Alternative generation: maintain rhyme scheme and syllable count while changing expression

## Development Commands

Since this is a hackathon template, specific build/test commands will depend on the technology stack chosen. Common patterns include:

```bash
# Python projects
python -m pip install -r requirements.txt
python src/main.py

# Node.js projects  
npm install
npm start
npm test
```

## Key Design Constraints

### Hackathon Limitations (48 hours)
- Use simplified reference database (50-100 popular songs for demo)
- In-memory storage instead of persistent database
- Basic UI focusing on core functionality
- Skip user authentication for MVP

### Legal Considerations
- Tool provides guidance only, not legal advice
- Include clear disclaimers about limitations
- Cannot check against all copyrighted material
- Focus on obvious similarity detection

## Submission Checklist

Before final submission ensure:
- [ ] All code in `src/` runs without errors
- [ ] Gemini API integration is clearly demonstrated
- [ ] Video demo is hosted publicly (YouTube/Loom/Google Drive)
- [ ] All required documentation files are complete
- [ ] Repository is public and named after team name
- [ ] Form submission completed before deadline (July 26th, 9 AM PT)

## Architecture Notes

The agentic workflow should follow this pattern:
1. **Input Processing**: Receive and sanitize user lyrics
2. **Planning**: Break down lyrics into analyzable components
3. **Execution**: Use Gemini API for similarity detection and analysis
4. **Memory**: Store results and user preferences for session
5. **Output**: Generate final report with alternatives

Focus on demonstrating clear separation between planner, executor, and memory components as judges will specifically look for agentic AI patterns.