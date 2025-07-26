# LyricLawyer Demo Video

## Problem Statement
**LyricLawyer** solves a critical problem for songwriters: **accidental copyright infringement**. With millions of songs published, creators often unknowingly write phrases similar to existing copyrighted material, leading to expensive legal disputes. Our AI-powered system provides instant copyright compliance checking with creative alternatives to help songwriters stay original while maintaining their artistic vision.

## Demo Overview
This demo showcases our **multi-agent agentic AI system** that autonomously collaborates to analyze lyrics, assess legal risks, and generate creative alternatives - all powered by Google's ADK framework and Gemini API.

---

## 📺 **Demo Video Link:**
**[RECORD YOUR VIDEO AND REPLACE THIS LINK]**
`https://your-actual-video-link-here`

*Note: Video will be recorded showing the complete multi-agent workflow with live Gemini API integration*

---

## Demo Script & Timestamps

### **00:00–00:30 — Introduction & Setup**

**Demo Content:**
- **Problem Introduction**: "Today I'll show you LyricLawyer, which solves copyright compliance for songwriters"
- **System Overview**: "This is a true agentic AI system with 5 specialized agents working collaboratively"
- **Tech Stack Highlight**: "Built with Google ADK framework and Gemini API integration"
- **Interface Walkthrough**: Show the clean web interface at `http://localhost:8000`

**Screen Actions:**
- Open browser to LyricLawyer homepage
- Show responsive Bootstrap interface
- Highlight the "Analyze Lyrics" input area
- Brief overview of the multi-agent system architecture

**Voice Script:**
> "LyricLawyer is an AI copyright compliance checker for songwriters. Instead of a single AI model, it uses five specialized agents that work together autonomously - a planner, similarity analyzer, risk assessor, alternatives generator, and coordinator. Let me show you how they collaborate to analyze lyrics in real-time."

---

### **00:30–01:30 — User Input → Planning Step**

**Demo Content:**
- **Live Lyrics Input**: Use a test song with known similarities (e.g., phrases inspired by "Shake It Off")
- **Planner Agent in Action**: Show real-time console output of agent planning
- **Agentic Decision Making**: Highlight how the planner autonomously breaks down the task
- **Tool Selection**: Show the planner calling `sanitize_lyrics()` and `extract_phrases()` tools

**Example Input:**
```
"I shake it off, shake it off
The haters gonna hate, hate, hate
But I just wanna dance all night
Under the bright city lights"
```

**Screen Actions:**
- Paste lyrics into the web interface
- Submit for analysis
- Switch to terminal/console to show live agent activity:
  ```
  🧠 Planner Agent: Breaking down analysis tasks...
  🔧 Using tool: sanitize_lyrics()
  🔧 Using tool: extract_phrases()
  📋 Analysis plan created with 4 prioritized phrases
  ```

**Voice Script:**
> "I'm inputting lyrics that might have copyright concerns. Watch the console - you can see our Planner Agent autonomously starting its work. It's not just following a script - it's making decisions about how to break down this analysis task, which tools to use, and how to prioritize the phrases for checking."

---

### **01:30–02:30 — Tool Calls & Memory Integration**

**Demo Content:**
- **Multi-Agent Collaboration**: Show similarity, risk, and alternatives agents working in sequence
- **Gemini API Integration**: Highlight real API calls to Google's Gemini model
- **Tool Ecosystem**: Demonstrate the advanced similarity engine with 8 algorithms
- **Memory System**: Show how agents store and retrieve analysis context
- **Database Queries**: Reference database lookups for similar phrases

**Screen Actions:**
- Show continued console output from multiple agents:
  ```
  🔍 Similarity Agent: Analyzing phrase similarities...
  🤖 Calling Gemini API for semantic analysis...
  🎯 8 similarity algorithms processing: "shake it off"
  📊 High similarity found: Taylor Swift - "Shake It Off" (89%)
  
  ⚖️ Risk Agent: Assessing copyright risk levels...
  🚨 HIGH RISK: "shake it off" - Popular song match
  
  ✍️ Alternatives Agent: Generating creative alternatives...
  🤖 Calling Gemini API for creative alternatives...
  💡 Generated 5 alternatives preserving rhyme scheme
  ```

- Switch back to web interface showing real-time progress
- Highlight memory system storing intermediate results

**Voice Script:**
> "Now you see true agentic collaboration. The Similarity Agent is making its own decisions about which algorithms to use and calling the Gemini API for semantic analysis. The Risk Agent independently assesses legal implications. The Alternatives Agent creatively generates options while preserving the original's artistic intent. Each agent has autonomy within its expertise domain."

---

### **02:30–03:30 — Final Output & Edge Case Handling**

**Demo Content:**
- **Coordinator Agent Synthesis**: Show final report generation
- **Comprehensive Results**: Display risk levels, similarity scores, and creative alternatives
- **User Experience**: Highlight the clear, actionable recommendations
- **Edge Case Demo**: Show how system handles unusual inputs or API failures
- **Alternative Quality**: Demonstrate rhyme preservation and creativity scoring

**Screen Actions:**
- Show final web interface results with:
  - Overall risk assessment (HIGH)
  - Flagged phrases with detailed explanations
  - Creative alternatives for "shake it off":
    - "brush it away" ✓
    - "let it slide" ✓  
    - "push it aside" ✓
  - Agent workflow status showing all 5 agents completed
- Demonstrate error handling with invalid input
- Show fallback alternatives when API is limited

**Voice Script:**
> "The Coordinator Agent synthesizes everything into this comprehensive report. You can see specific risk levels, similarity percentages, and most importantly - creative alternatives that maintain the original's rhyme and rhythm. This isn't just similarity detection - it's a complete creative writing assistant that helps maintain originality while preserving artistic vision."

**Final Demo Points:**
- Show responsive design on mobile
- Highlight the legal disclaimer emphasizing this is guidance, not legal advice
- Demonstrate the system's speed (10-30 seconds for complete analysis)
- Point out the agent workflow tracking for transparency

---

## Key Agentic Behaviors Highlighted

### **Autonomous Decision Making**
- Each agent independently chooses its approach and tools
- Dynamic workflow adjustment based on analysis results
- Context-aware parameter selection for API calls

### **Inter-Agent Collaboration**
- Planner → Similarity → Risk → Alternatives → Coordinator pipeline
- Shared memory and context passing between agents
- Emergent intelligence from specialized agent interaction

### **Adaptive Tool Usage**
- Agents autonomously select from 8+ available tools
- Context-aware API parameter adjustment
- Fallback mechanisms when primary tools fail

### **Memory-Driven Learning**
- Session memory influences subsequent agent decisions
- Workflow optimization based on previous analysis patterns
- User preference adaptation for personalized results

## Technical Demo Highlights

- **Live API Integration**: Real Gemini API calls with actual responses
- **Multi-Algorithm Analysis**: 8 different similarity detection methods
- **Database Integration**: SQLite reference database with 10+ songs
- **Error Recovery**: Graceful handling of API limits and network issues
- **Performance**: Sub-30-second analysis with comprehensive results

## Edge Cases Demonstrated

1. **API Rate Limiting**: Show fallback alternatives when Gemini API is throttled
2. **Invalid Input**: Demonstrate error handling with malformed lyrics
3. **No Similarities Found**: Show system behavior with completely original content
4. **Network Issues**: Graceful degradation when external APIs fail

This demo showcases a production-ready agentic AI system that solves real-world problems through autonomous agent collaboration, demonstrating the future of AI-powered creative tools.