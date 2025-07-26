#!/bin/bash

# LyricLawyer GitHub Issues Creation Script
# Run this after: gh auth login

echo "Creating GitHub issues for LyricLawyer sprint plan..."

# Sprint 1: Foundation & Setup
echo "Creating Sprint 1 issues..."

gh issue create --title "Sprint 1: Core Architecture - Implement planner.py" \
--body "**Sprint 1 Task (Part of 3-hour Core Architecture block)**

Implement \`src/planner.py\` with task decomposition logic for breaking down lyrics into analyzable segments.

## Requirements:
- Break lyrics into lines and phrases
- Prioritize risky phrases for analysis
- Create task decomposition logic for agentic workflow

## Acceptance Criteria:
- [ ] \`src/planner.py\` file created
- [ ] Task decomposition logic implemented
- [ ] Integration points defined for executor module

**Estimated Time:** 1 hour
**Sprint:** 1 (Hours 1-8)
**Priority:** High" \
--label "enhancement,sprint-1,core-architecture"

gh issue create --title "Sprint 1: Core Architecture - Implement executor.py" \
--body "**Sprint 1 Task (Part of 3-hour Core Architecture block)**

Implement \`src/executor.py\` with Gemini API integration and LLM prompt logic.

## Requirements:
- Integrate with Google Gemini API
- Implement LLM prompt and tool-calling logic
- Handle API responses and error cases

## Acceptance Criteria:
- [ ] \`src/executor.py\` file created
- [ ] Gemini API integration implemented
- [ ] Basic error handling for API calls

**Estimated Time:** 1 hour
**Sprint:** 1 (Hours 1-8)
**Priority:** High" \
--label "enhancement,sprint-1,core-architecture"

gh issue create --title "Sprint 1: Core Architecture - Implement memory.py" \
--body "**Sprint 1 Task (Part of 3-hour Core Architecture block)**

Implement basic \`src/memory.py\` for session storage and flagged phrases.

## Requirements:
- Store user session data
- Cache flagged phrases and user rewrites
- Implement basic memory retrieval functions

## Acceptance Criteria:
- [ ] \`src/memory.py\` file created
- [ ] Session storage implemented
- [ ] Memory retrieval functions working

**Estimated Time:** 1 hour
**Sprint:** 1 (Hours 1-8)
**Priority:** High" \
--label "enhancement,sprint-1,core-architecture"

gh issue create --title "Sprint 1: Gemini API Integration Setup" \
--body "**Sprint 1 Task (2 hours)**

Set up Google Gemini API integration and test basic functionality.

## Requirements:
- Set up Google AI Studio API key
- Create API client wrapper
- Test basic text analysis functionality

## Acceptance Criteria:
- [ ] API key configured in .env file
- [ ] API client wrapper created
- [ ] Basic text analysis test working
- [ ] Error handling for API failures

**Estimated Time:** 2 hours
**Sprint:** 1 (Hours 1-8)
**Priority:** High" \
--label "enhancement,sprint-1,api-integration"

# Sprint 2: Core Functionality
echo "Creating Sprint 2 issues..."

gh issue create --title "Sprint 2: Lyric Processing Engine" \
--body "**Sprint 2 Task (4 hours)**

Implement core lyric processing engine for text analysis.

## Requirements:
- Text sanitization and line segmentation
- Phrase extraction and tokenization
- Input validation and error handling

## Acceptance Criteria:
- [ ] Text sanitization functions implemented
- [ ] Line segmentation working correctly
- [ ] Phrase extraction logic implemented
- [ ] Input validation with proper error messages

**Estimated Time:** 4 hours
**Sprint:** 2 (Hours 9-20)
**Priority:** High" \
--label "enhancement,sprint-2,core-functionality"

gh issue create --title "Sprint 2: Similarity Detection System" \
--body "**Sprint 2 Task (5 hours)**

Implement similarity detection algorithms and risk assessment.

## Requirements:
- Implement basic string similarity algorithms
- Integrate Gemini API for semantic analysis
- Create scoring and risk assessment logic

## Acceptance Criteria:
- [ ] String similarity algorithms implemented
- [ ] Gemini API semantic analysis integrated
- [ ] Risk scoring algorithm created
- [ ] Similarity threshold configuration

**Estimated Time:** 5 hours
**Sprint:** 2 (Hours 9-20)
**Priority:** High" \
--label "enhancement,sprint-2,core-functionality"

gh issue create --title "Sprint 2: Reference Database Creation" \
--body "**Sprint 2 Task (3 hours)**

Create sample database of popular song lyrics for demo purposes.

## Requirements:
- Create sample database of popular song lyrics
- Focus on 50-100 well-known songs for demo
- Implement basic search and matching functions

## Acceptance Criteria:
- [ ] Database with 50-100 popular songs created
- [ ] Search functionality implemented
- [ ] Matching algorithms working
- [ ] Database loading and initialization

**Estimated Time:** 3 hours
**Sprint:** 2 (Hours 9-20)
**Priority:** Medium" \
--label "enhancement,sprint-2,database"

# Sprint 3: User Interface & Integration
echo "Creating Sprint 3 issues..."

gh issue create --title "Sprint 3: Simple Web Interface" \
--body "**Sprint 3 Task (4 hours)**

Create basic web interface for lyric input and results display.

## Requirements:
- Basic HTML/CSS form for lyric input
- Results display page with highlighted matches
- Simple styling for demo presentation

## Acceptance Criteria:
- [ ] Input form created and functional
- [ ] Results page displays matches clearly
- [ ] Basic responsive styling implemented
- [ ] User-friendly interface design

**Estimated Time:** 4 hours
**Sprint:** 3 (Hours 21-32)
**Priority:** High" \
--label "enhancement,sprint-3,frontend"

gh issue create --title "Sprint 3: Agentic Workflow Integration" \
--body "**Sprint 3 Task (4 hours)**

Connect planner → executor → memory flow for complete agentic workflow.

## Requirements:
- Connect planner → executor → memory flow
- Implement task breakdown for lyric analysis
- Add logging and progress tracking

## Acceptance Criteria:
- [ ] Complete workflow integration working
- [ ] Task breakdown properly implemented
- [ ] Logging system in place
- [ ] Progress tracking functional

**Estimated Time:** 4 hours
**Sprint:** 3 (Hours 21-32)
**Priority:** High" \
--label "enhancement,sprint-3,integration"

gh issue create --title "Sprint 3: Alternative Suggestions System" \
--body "**Sprint 3 Task (4 hours)**

Implement AI-powered alternative lyric suggestions.

## Requirements:
- Use Gemini to generate alternative phrasings
- Maintain rhyme scheme and meter
- Present multiple options to user

## Acceptance Criteria:
- [ ] Alternative generation using Gemini API
- [ ] Rhyme scheme preservation logic
- [ ] Multiple options presented clearly
- [ ] User interface for alternatives

**Estimated Time:** 4 hours
**Sprint:** 3 (Hours 21-32)
**Priority:** High" \
--label "enhancement,sprint-3,ai-features"

# Sprint 4: Polish & Demo Preparation
echo "Creating Sprint 4 issues..."

gh issue create --title "Sprint 4: Error Handling & Edge Cases" \
--body "**Sprint 4 Task (3 hours)**

Implement comprehensive error handling and edge case management.

## Requirements:
- Handle empty input, very long lyrics
- API failure fallbacks
- Input sanitization edge cases

## Acceptance Criteria:
- [ ] Empty input handling implemented
- [ ] Long lyrics processing optimized
- [ ] API failure fallbacks working
- [ ] Edge case testing completed

**Estimated Time:** 3 hours
**Sprint:** 4 (Hours 33-44)
**Priority:** Medium" \
--label "enhancement,sprint-4,testing"

gh issue create --title "Sprint 4: Demo Content Preparation" \
--body "**Sprint 4 Task (4 hours)**

Create compelling demo content and test cases.

## Requirements:
- Create 3-5 test lyric samples
- Include known similar phrases for demonstration
- Prepare examples showing clear copyright issues

## Acceptance Criteria:
- [ ] 3-5 test lyric samples created
- [ ] Clear copyright similarity examples prepared
- [ ] Demo script and flow documented
- [ ] Edge cases for demo included

**Estimated Time:** 4 hours
**Sprint:** 4 (Hours 33-44)
**Priority:** High" \
--label "enhancement,sprint-4,demo"

gh issue create --title "Sprint 4: Documentation Updates" \
--body "**Sprint 4 Task (2 hours)**

Complete all required hackathon documentation.

## Requirements:
- Complete README.md with setup instructions
- Write ARCHITECTURE.md with system diagram
- Draft EXPLANATION.md with reasoning process

## Acceptance Criteria:
- [ ] README.md completed with clear setup instructions
- [ ] ARCHITECTURE.md includes system diagram
- [ ] EXPLANATION.md covers reasoning process
- [ ] All documentation reviewed and polished

**Estimated Time:** 2 hours
**Sprint:** 4 (Hours 33-44)
**Priority:** High" \
--label "documentation,sprint-4"

gh issue create --title "Sprint 4: Performance Optimization" \
--body "**Sprint 4 Task (3 hours)**

Optimize system performance for demo requirements.

## Requirements:
- Optimize API calls to Gemini
- Implement basic caching for repeated queries
- Ensure < 30 second response times

## Acceptance Criteria:
- [ ] API call optimization implemented
- [ ] Caching system for repeated queries
- [ ] Response time under 30 seconds verified
- [ ] Performance testing completed

**Estimated Time:** 3 hours
**Sprint:** 4 (Hours 33-44)
**Priority:** Medium" \
--label "enhancement,sprint-4,performance"

# Sprint 5: Final Demo & Submission
echo "Creating Sprint 5 issues..."

gh issue create --title "Sprint 5: Video Recording & Demo" \
--body "**Sprint 5 Task (2 hours)**

Record professional demo video for hackathon submission.

## Requirements:
- Record 3-5 minute demo video
- Show complete user workflow
- Highlight agentic AI components and Gemini integration
- Upload to YouTube/Google Drive

## Acceptance Criteria:
- [ ] 3-5 minute video recorded
- [ ] Complete user workflow demonstrated
- [ ] Agentic AI components highlighted
- [ ] Gemini integration clearly shown
- [ ] Video uploaded to public hosting

**Estimated Time:** 2 hours
**Sprint:** 5 (Hours 45-48)
**Priority:** Critical" \
--label "demo,sprint-5"

gh issue create --title "Sprint 5: Final Documentation & Submission" \
--body "**Sprint 5 Task (1.5 hours)**

Complete final documentation and submit to hackathon.

## Requirements:
- Complete DEMO.md with video link and timestamps
- Final review of all documentation
- Ensure all requirements met
- Submit via hackathon form

## Acceptance Criteria:
- [ ] DEMO.md completed with video link
- [ ] All documentation reviewed and finalized
- [ ] Hackathon requirements checklist completed
- [ ] Form submission completed before deadline

**Estimated Time:** 1.5 hours
**Sprint:** 5 (Hours 45-48)
**Priority:** Critical" \
--label "documentation,submission,sprint-5"

echo "All GitHub issues created successfully!"
echo ""
echo "To run this script:"
echo "1. First authenticate: gh auth login"
echo "2. Then run: ./create_github_issues.sh"