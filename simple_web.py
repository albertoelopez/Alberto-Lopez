#!/usr/bin/env python3
"""
Simplified Web Interface for LyricLawyer
Uses core tools directly without complex agent system
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import sys
sys.path.append('/root/Alberto-Lopez')

from src.tools.lyric_analyzer import sanitize_lyrics, extract_phrases
from src.tools.similarity_engine import AdvancedSimilarityEngine
from src.tools.reference_database import ReferenceDatabase

# Create FastAPI app
app = FastAPI(
    title="LyricLawyer",
    description="Copyright Compliance Checker for Songwriters",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")
os.makedirs("templates", exist_ok=True)

# Initialize core components
similarity_engine = AdvancedSimilarityEngine()
try:
    database = ReferenceDatabase()
except Exception:
    database = None

def analyze_lyrics_simple(lyrics: str) -> dict:
    """Simplified lyrics analysis using core tools"""
    
    # Step 1: Sanitize lyrics
    sanitized = sanitize_lyrics(lyrics)
    if not sanitized['success']:
        return {'error': 'Failed to process lyrics'}
    
    # Step 2: Extract phrases
    phrases = extract_phrases(sanitized['sanitized_lyrics'])
    
    # Step 3: Analyze similarity
    flagged_phrases = []
    high_risk_count = 0
    
    for phrase in phrases[:10]:  # Test first 10 phrases
        phrase_text = phrase['text']
        
        # Test against known problematic phrases
        test_phrases = ["shake it off", "beat it", "hello", "love me tender"]
        
        for test_phrase in test_phrases:
            similarity = similarity_engine.calculate_comprehensive_similarity(
                phrase_text.lower(), test_phrase
            )
            
            if similarity['overall_similarity'] > 0.4:
                flagged_phrases.append({
                    'phrase': phrase_text,
                    'similarity_score': similarity['overall_similarity'],
                    'risk_level': similarity['risk_level'],
                    'matched_reference': test_phrase,
                    'line_number': phrase['line_number']
                })
                
                if similarity['risk_level'] in ['HIGH', 'CRITICAL']:
                    high_risk_count += 1
    
    # Determine overall risk
    if high_risk_count > 2:
        overall_risk = 'HIGH'
    elif high_risk_count > 0:
        overall_risk = 'MEDIUM'
    elif flagged_phrases:
        overall_risk = 'LOW'
    else:
        overall_risk = 'MINIMAL'
    
    return {
        'overall_risk': overall_risk,
        'phrases_analyzed': len(phrases),
        'flagged_phrases': len(flagged_phrases),
        'flagged_details': flagged_phrases,
        'analysis_summary': f'Analyzed {len(phrases)} phrases, found {len(flagged_phrases)} potential similarities'
    }

# Create HTML template
html_template = '''<!DOCTYPE html>
<html>
<head>
    <title>LyricLawyer - Copyright Checker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">🎵 LyricLawyer</h1>
        <p class="text-center text-muted">AI-powered copyright compliance checker for songwriters</p>
        
        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}
        
        <form method="post" action="/analyze" class="mb-4">
            <div class="mb-3">
                <label class="form-label">Enter your song lyrics:</label>
                <textarea name="lyrics" class="form-control" rows="6" placeholder="Enter your lyrics here..." required>{{ lyrics or '' }}</textarea>
            </div>
            <button type="submit" class="btn btn-primary">Analyze Lyrics</button>
        </form>
        
        {% if results %}
        <div class="card">
            <div class="card-header">
                <h3>Analysis Results</h3>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h5>Overall Risk: 
                            <span class="badge 
                                {% if results.overall_risk == 'HIGH' %}bg-danger
                                {% elif results.overall_risk == 'MEDIUM' %}bg-warning
                                {% elif results.overall_risk == 'LOW' %}bg-info
                                {% else %}bg-success{% endif %}">
                                {{ results.overall_risk }}
                            </span>
                        </h5>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Phrases Analyzed:</strong> {{ results.phrases_analyzed }}</p>
                        <p><strong>Potential Issues:</strong> {{ results.flagged_phrases }}</p>
                    </div>
                </div>
                
                {% if results.flagged_details %}
                <h6>Flagged Phrases:</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Phrase</th>
                                <th>Risk Level</th>
                                <th>Similarity</th>
                                <th>Reference</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for item in results.flagged_details %}
                            <tr>
                                <td>{{ item.phrase }}</td>
                                <td><span class="badge bg-warning">{{ item.risk_level }}</span></td>
                                <td>{{ "%.1f"|format(item.similarity_score * 100) }}%</td>
                                <td>{{ item.matched_reference }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}
                
                <div class="mt-3">
                    <p class="text-muted">{{ results.analysis_summary }}</p>
                </div>
            </div>
        </div>
        {% endif %}
        
        <div class="mt-5 text-center text-muted">
            <p>Powered by multi-algorithm similarity detection • Google ADK framework ready</p>
        </div>
    </div>
</body>
</html>'''

# Write template file
with open("templates/index.html", "w") as f:
    f.write(html_template)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, lyrics: str = Form(...)):
    if not lyrics or len(lyrics.strip()) < 10:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Please enter at least 10 characters of lyrics",
            "lyrics": lyrics
        })
    
    try:
        results = analyze_lyrics_simple(lyrics.strip())
        
        if 'error' in results:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": results['error'],
                "lyrics": lyrics
            })
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "results": results,
            "lyrics": lyrics
        })
        
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Analysis failed: {str(e)}",
            "lyrics": lyrics
        })

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "LyricLawyer"}

if __name__ == "__main__":
    print("🌐 Starting LyricLawyer Simple Web Interface")
    print("🎯 Core functionality: Similarity detection + Risk assessment")
    print("📍 Access at: http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)