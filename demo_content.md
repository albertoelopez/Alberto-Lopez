# LyricLawyer Demo Content

This file contains test lyrics specifically designed to demonstrate the LyricLawyer system's capabilities during the hackathon presentation.

## Demo Test Cases

### Test Case 1: High Risk - Clear Copyright Similarities
**Purpose**: Demonstrate HIGH/CRITICAL risk detection and alternative generation

```
Song Title: "Shake It Away"
Lyrics:
I shake it off, shake it off
The haters gonna hate, hate, hate
But I'm a player gonna play, play, play  
And baby I'm just gonna shake, shake, shake

Under the bright lights tonight
Dancing like it's 1989
This is our song, our moment
Shake it off and just move on
```

**Expected Results**:
- HIGH RISK flags for "shake it off" (Taylor Swift - "Shake It Off")
- MEDIUM/HIGH RISK for "haters gonna hate" (Taylor Swift - "Shake It Off")  
- Reference matches to Taylor Swift songs
- Alternative suggestions preserving rhyme scheme

---

### Test Case 2: Medium Risk - Partial Similarities
**Purpose**: Show nuanced similarity detection and risk assessment

```
Song Title: "City Dreams"
Lyrics:
Walking down the street at night
Concrete jungle where dreams are made
The city never sleeps, never fades
Bright lights, big city calling me

Empire state of mind tonight
In New York, New York so grand
Where ambition meets the sky
This concrete paradise, my homeland
```

**Expected Results**:
- MEDIUM RISK for "concrete jungle where dreams are made" (Alicia Keys - "Empire State of Mind")
- MEDIUM RISK for "empire state of mind" (Alicia Keys - "Empire State of Mind")
- LOW/MEDIUM for "the city never sleeps" (Frank Sinatra - "New York, New York")
- Alternatives maintaining urban theme

---

### Test Case 3: Low Risk - Original Content with Minor Similarities
**Purpose**: Demonstrate system handling mostly original content

```
Song Title: "Morning Coffee Blues"
Lyrics:
Sunrise through my window pane
Coffee brewing, start the day
Yesterday's troubles wash away
In this quiet morning hour

Steam rises from my favorite mug
Memories of you still linger here
But morning light brings hope so clear
Time to write a brand new chapter
```

**Expected Results**:
- LOW RISK overall assessment
- Few or no flagged phrases
- Minimal reference matches
- System shows it can identify original content

---

### Test Case 4: Mixed Risk - Combination Scenario
**Purpose**: Show complex analysis with varying risk levels

```
Song Title: "Young and Free"
Lyrics:
We are young, so let's set the world on fire
Dancing queen, only seventeen  
Living like we're dying tonight
Young hearts run free in the moonlight

Sweet Caroline, good times never seemed so good
But we are the champions of our destiny
Tonight we party like it's 1999
Young and wild and free to be
```

**Expected Results**:
- HIGH RISK: "we are young" (Fun - "We Are Young")
- HIGH RISK: "dancing queen" (ABBA - "Dancing Queen")  
- MEDIUM RISK: "sweet caroline" (Neil Diamond - "Sweet Caroline")
- MEDIUM RISK: "we are the champions" (Queen - "We Are The Champions")
- Multiple reference matches across different eras
- Comprehensive alternative suggestions

---

### Test Case 5: Edge Case - Very Short Input
**Purpose**: Test minimum viable input handling

```
Lyrics:
Hello darkness my old friend
Silence speaks to me again
```

**Expected Results**:
- CRITICAL RISK: Direct match to Simon & Garfunkel - "The Sound of Silence"
- Clear copyright violation warning
- Strong alternative suggestions
- System handles short input gracefully

---

## Demo Script Integration

### For Video Demo (Following DEMO.md timestamps):

**00:30–01:30 (User Input → Planning)**: Use **Test Case 1** to show:
- Clear input with obvious similarities
- Planner Agent breaking down analysis
- Tool selection and phrase extraction

**01:30–02:30 (Tool Calls & Memory)**: Continue with **Test Case 1** to demonstrate:
- Multi-agent collaboration
- Gemini API calls for similarity analysis
- Database lookups and risk assessment
- Memory system storing intermediate results

**02:30–03:30 (Final Output & Edge Cases)**: Show **Test Case 1** results, then quickly demo **Test Case 5** for edge case handling:
- Comprehensive risk assessment
- Creative alternatives with quality scores
- Error handling with very short input
- System recovery and user guidance

## Interactive Demo Features

### Quick Test Buttons (Optional Enhancement)
Add buttons to the web interface for instant demo loading:

```html
<div class="demo-content mt-4">
    <h6>🎬 Demo Content</h6>
    <div class="btn-group-vertical w-100">
        <button class="btn btn-outline-secondary btn-sm" onclick="loadDemo(1)">
            📊 High Risk Example (Taylor Swift similarities)
        </button>
        <button class="btn btn-outline-secondary btn-sm" onclick="loadDemo(2)">
            ⚖️ Mixed Risk Example (Multiple artists)
        </button>
        <button class="btn btn-outline-secondary btn-sm" onclick="loadDemo(3)">
            ✅ Low Risk Example (Mostly original)
        </button>
    </div>
</div>
```

## Expected System Performance

| Test Case | Expected Analysis Time | Risk Level | Flagged Phrases | Alternatives Generated |
|-----------|----------------------|------------|-----------------|----------------------|
| Test Case 1 | 15-25 seconds | HIGH | 3-4 phrases | 12-15 alternatives |
| Test Case 2 | 12-20 seconds | MEDIUM | 2-3 phrases | 6-9 alternatives |
| Test Case 3 | 8-15 seconds | LOW | 0-1 phrases | 0-3 alternatives |
| Test Case 4 | 20-30 seconds | MIXED | 4-5 phrases | 15-20 alternatives |
| Test Case 5 | 5-10 seconds | CRITICAL | 2 phrases | 6-8 alternatives |

## Key Demo Points to Highlight

### Agentic AI Characteristics:
1. **Autonomous Decision Making**: Each agent independently chooses analysis approach
2. **Specialized Expertise**: Different agents handle planning, similarity, risk, alternatives, coordination
3. **Tool Usage**: Agents select appropriate tools based on analysis needs
4. **Collaborative Intelligence**: Agents build upon each other's results
5. **Adaptive Workflow**: System adjusts based on risk levels found

### Technical Excellence:
1. **Multi-Algorithm Analysis**: 8 different similarity detection methods
2. **Gemini API Integration**: Real-time AI-powered semantic analysis
3. **Performance**: Sub-30-second comprehensive analysis
4. **User Experience**: Professional interface with real-time feedback
5. **Error Handling**: Graceful degradation and recovery

### Practical Value:
1. **Real Problem Solving**: Addresses actual songwriter copyright concerns
2. **Creative Assistance**: Maintains artistic vision while ensuring originality  
3. **Educational Tool**: Teaches about copyright similarity patterns
4. **Professional Quality**: Production-ready system architecture

This demo content ensures comprehensive testing of all system capabilities while providing engaging examples that clearly demonstrate the value and sophistication of the LyricLawyer agentic AI system.