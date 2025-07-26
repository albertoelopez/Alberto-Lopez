"""
LyricLawyer Web Interface

Simple web interface for the LyricLawyer copyright compliance checker.
Built with FastAPI for the hackathon demo.
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from typing import Dict, Any

from .agent import LyricLawyerAgent
from .tools.error_handler import handle_error


class LyricLawyerWebApp:
    """
    Main web application class
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="LyricLawyer",
            description="Copyright Compliance Checker for Songwriters",
            version="1.0.0"
        )
        
        # Initialize the agent system
        self.agent_system = LyricLawyerAgent()
        
        # Setup templates and static files
        self.templates = Jinja2Templates(directory="src/templates")
        
        # Create templates directory if it doesn't exist
        os.makedirs("src/templates", exist_ok=True)
        os.makedirs("src/static", exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory="src/static"), name="static")
        
        # Setup routes
        self._setup_routes()
        
        # Create template files
        self._create_template_files()
        self._create_static_files()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Home page with lyric input form"""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.post("/analyze", response_class=HTMLResponse)
        async def analyze_lyrics(request: Request, lyrics: str = Form(...), 
                               preserve_rhyme: bool = Form(False), 
                               strict_mode: bool = Form(False)):
            """Analyze lyrics and show results"""
            
            # Enhanced input validation
            if not lyrics or not lyrics.strip():
                return self.templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "Please enter some lyrics to analyze."
                })
            
            if len(lyrics.strip()) < 10:
                return self.templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "Please enter at least 10 characters of lyrics for meaningful analysis."
                })
            
            if len(lyrics) > 5000:
                return self.templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": "Lyrics are too long. Please limit to 5000 characters or less."
                })
            
            try:
                # Prepare user preferences with advanced options
                user_preferences = {
                    'preserve_rhyme': preserve_rhyme,
                    'strict_mode': strict_mode,
                    'similarity_threshold': 0.7 if strict_mode else 0.8
                }
                
                # Analyze lyrics using the agent system
                analysis_result = self.agent_system.analyze_lyrics(lyrics.strip(), user_preferences)
                
                if 'error' in analysis_result:
                    return self.templates.TemplateResponse("index.html", {
                        "request": request,
                        "error": analysis_result['error']
                    })
                
                # Format results for display
                formatted_results = self._format_results(analysis_result, lyrics)
                
                return self.templates.TemplateResponse("results.html", {
                    "request": request,
                    "results": formatted_results,
                    "original_lyrics": lyrics
                })
                
            except Exception as e:
                error_result = handle_error(e, {"context": "web_interface", "lyrics_length": len(lyrics)})
                
                return self.templates.TemplateResponse("index.html", {
                    "request": request,
                    "error": error_result['user_message']
                })
        
        @self.app.get("/api/analyze")
        async def api_analyze(lyrics: str):
            """API endpoint for programmatic access"""
            
            if not lyrics or not lyrics.strip():
                raise HTTPException(status_code=400, detail="Lyrics parameter is required")
            
            try:
                analysis_result = self.agent_system.analyze_lyrics(lyrics.strip())
                return JSONResponse(analysis_result)
                
            except Exception as e:
                error_result = handle_error(e, {"context": "api", "lyrics_length": len(lyrics)})
                raise HTTPException(status_code=500, detail=error_result['user_message'])
        
        @self.app.get("/about", response_class=HTMLResponse)
        async def about(request: Request):
            """About page explaining the system"""
            return self.templates.TemplateResponse("about.html", {"request": request})
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "service": "LyricLawyer"}
    
    def _format_results(self, analysis_result: Dict[str, Any], original_lyrics: str) -> Dict[str, Any]:
        """Format analysis results for web display"""
        
        # Extract key information
        overall_risk = analysis_result.get('overall_risk', 'LOW')
        flagged_phrases = analysis_result.get('flagged_phrases', 0)
        final_report = analysis_result.get('final_report', 'Analysis completed.')
        
        # Get similarity results for detailed display
        similarity_results = analysis_result.get('similarity_results', [])
        flagged_items = [r for r in similarity_results if r.get('flagged', False)]
        
        # Format flagged phrases with details
        formatted_flagged = []
        for item in flagged_items:
            phrase_info = item.get('phrase', {})
            similarity_info = item.get('similarity_analysis', {})
            
            formatted_flagged.append({
                'phrase': phrase_info.get('text', ''),
                'line_number': phrase_info.get('line_number', 0),
                'risk_level': similarity_info.get('risk_level', 'LOW'),
                'similarity_score': similarity_info.get('similarity_score', 0.0),
                'matched_song': similarity_info.get('matched_song'),
                'matched_artist': similarity_info.get('matched_artist'),
                'explanation': similarity_info.get('explanation', ''),
                'confidence': similarity_info.get('confidence', 0.0)
            })
        
        # Get alternatives if available
        alternatives = analysis_result.get('alternatives', {})
        formatted_alternatives = {}
        
        if alternatives and alternatives.get('phrase_alternatives'):
            for phrase, alt_data in alternatives['phrase_alternatives'].items():
                formatted_alternatives[phrase] = {
                    'risk_level': alt_data.get('risk_level', 'LOW'),
                    'alternatives': alt_data.get('alternatives', [])
                }
        
        # Risk level styling
        risk_colors = {
            'LOW': 'success',
            'MEDIUM': 'warning', 
            'HIGH': 'danger',
            'CRITICAL': 'danger'
        }
        
        return {
            'overall_risk': overall_risk,
            'risk_color': risk_colors.get(overall_risk, 'secondary'),
            'flagged_phrases': flagged_phrases,
            'phrases_analyzed': analysis_result.get('phrases_analyzed', 0),
            'flagged_details': formatted_flagged,
            'alternatives': formatted_alternatives,
            'final_report': final_report,
            'agent_workflow': analysis_result.get('agentic_workflow', {}),
            'analysis_time': analysis_result.get('analysis_time', 0),
            'cache_hit': analysis_result.get('cache_hit', False),
            'cache_stats': analysis_result.get('cache_stats', {}),
            'confidence_score': self._calculate_overall_confidence(flagged_items)
        }
    
    def _calculate_overall_confidence(self, flagged_items: list) -> float:
        """Calculate overall confidence in the analysis"""
        
        if not flagged_items:
            return 0.95  # High confidence when no issues found
        
        confidences = []
        for item in flagged_items:
            similarity_info = item.get('similarity_analysis', {})
            confidence = similarity_info.get('confidence', 0.5)
            if isinstance(confidence, (int, float)):
                confidences.append(confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    def _create_template_files(self):
        """Create HTML template files"""
        
        # Base template
        base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}LyricLawyer - Copyright Compliance Checker{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/style.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                🎵 <strong>LyricLawyer</strong>
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Home</a>
                <a class="nav-link" href="/about">About</a>
            </div>
        </div>
    </nav>

    <main class="container mt-4">
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-light text-center py-3 mt-5">
        <div class="container">
            <small class="text-muted">
                LyricLawyer - Agentic AI Hackathon Project<br>
                🤖 Powered by Google ADK & Gemini API
            </small>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>'''
        
        with open("src/templates/base.html", "w") as f:
            f.write(base_template)
        
        # Index page template
        index_template = '''{% extends "base.html" %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="text-center mb-5">
            <h1 class="display-4 mb-3">🎵 LyricLawyer</h1>
            <p class="lead text-muted">
                AI-powered copyright compliance checker for songwriters
            </p>
            <p class="text-muted">
                Analyze your lyrics for potential copyright issues and get original alternatives
            </p>
        </div>

        {% if error %}
        <div class="alert alert-danger" role="alert">
            <strong>Error:</strong> {{ error }}
        </div>
        {% endif %}

        <div class="card shadow-sm">
            <div class="card-body">
                <h5 class="card-title mb-4">📝 Enter Your Lyrics</h5>
                
                <form method="post" action="/analyze">
                    <div class="mb-3">
                        <textarea 
                            class="form-control" 
                            name="lyrics" 
                            rows="10" 
                            placeholder="Paste your song lyrics here...

Example:
Walking down the street tonight
Stars are shining oh so bright
Dancing to the rhythm of my heart
This is where our story starts"
                            required></textarea>
                    </div>
                    
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary btn-lg">
                            🔍 Analyze for Copyright Issues
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-md-4">
                <div class="text-center">
                    <div class="feature-icon mb-3">🤖</div>
                    <h5>AI-Powered Analysis</h5>
                    <p class="text-muted">Advanced algorithms + Gemini AI for comprehensive similarity detection</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="text-center">
                    <div class="feature-icon mb-3">⚖️</div>
                    <h5>Legal Guidance</h5>
                    <p class="text-muted">Plain-English explanations of potential copyright concerns</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="text-center">
                    <div class="feature-icon mb-3">✍️</div>
                    <h5>Creative Alternatives</h5>
                    <p class="text-muted">Original suggestions that preserve your artistic vision</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

        with open("src/templates/index.html", "w") as f:
            f.write(index_template)
        
        # Results page template
        results_template = '''{% extends "base.html" %}

{% block title %}Analysis Results - LyricLawyer{% endblock %}

{% block content %}
<div class="row">
    <div class="col-lg-8 mx-auto">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>📊 Analysis Results</h2>
            <a href="/" class="btn btn-outline-primary">← Analyze New Lyrics</a>
        </div>

        <!-- Overall Risk Assessment -->
        <div class="card mb-4">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h5 class="card-title mb-3">Overall Risk Assessment</h5>
                        <span class="badge bg-{{ results.risk_color }} fs-6 mb-2">
                            {{ results.overall_risk }} RISK
                        </span>
                        <p class="mb-2">
                            <strong>{{ results.phrases_analyzed }}</strong> phrases analyzed • 
                            <strong>{{ results.flagged_phrases }}</strong> flagged for review
                        </p>
                        <div class="progress mb-2" style="height: 8px;">
                            <div class="progress-bar bg-{{ results.risk_color }}" 
                                 style="width: {{ (results.confidence_score * 100)|round }}%"></div>
                        </div>
                        <small class="text-muted">
                            Confidence: {{ (results.confidence_score * 100)|round }}%
                        </small>
                    </div>
                    <div class="col-md-4 text-end">
                        {% if results.overall_risk == 'LOW' %}
                            <div class="display-1 text-success">✅</div>
                        {% elif results.overall_risk == 'MEDIUM' %}
                            <div class="display-1 text-warning">⚠️</div>
                        {% else %}
                            <div class="display-1 text-danger">🚨</div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Flagged Phrases -->
        {% if results.flagged_details %}
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">🚩 Flagged Phrases ({{ results.flagged_phrases }})</h5>
            </div>
            <div class="card-body">
                {% for item in results.flagged_details %}
                <div class="alert alert-{{ 'danger' if item.risk_level in ['HIGH', 'CRITICAL'] else 'warning' }} mb-3">
                    <div class="row">
                        <div class="col-md-8">
                            <h6 class="alert-heading">
                                "{{ item.phrase }}" 
                                <span class="badge bg-{{ 'danger' if item.risk_level in ['HIGH', 'CRITICAL'] else 'warning' }}">
                                    {{ item.risk_level }}
                                </span>
                            </h6>
                            <p class="mb-2">{{ item.explanation }}</p>
                            {% if item.matched_song and item.matched_artist %}
                            <p class="mb-0">
                                <strong>Potential match:</strong> "{{ item.matched_song }}" by {{ item.matched_artist }}
                            </p>
                            {% endif %}
                        </div>
                        <div class="col-md-4 text-end">
                            <small class="text-muted">
                                Line {{ item.line_number }}<br>
                                Similarity: {{ (item.similarity_score * 100)|round }}%<br>
                                Confidence: {{ (item.confidence * 100)|round }}%
                            </small>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- Alternatives -->
        {% if results.alternatives %}
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">💡 Suggested Alternatives</h5>
            </div>
            <div class="card-body">
                {% for phrase, alt_data in results.alternatives.items() %}
                <div class="mb-4">
                    <h6>Original: "{{ phrase }}"</h6>
                    <div class="ps-3">
                        {% for alt in alt_data.alternatives[:3] %}
                        <div class="d-flex align-items-center mb-2">
                            <span class="badge bg-success me-2">✓</span>
                            <span class="fw-bold">{{ alt.alternative }}</span>
                        </div>
                        <p class="text-muted small ps-4 mb-3">{{ alt.explanation }}</p>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- AI Analysis Report -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">🤖 AI Analysis Report</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    {{ results.final_report|replace('\n', '<br>')|safe }}
                </div>
                
                <details class="mt-3">
                    <summary class="text-muted">View Agent Workflow Details</summary>
                    <div class="mt-2">
                        {% for agent, status in results.agent_workflow.items() %}
                        <div class="d-flex justify-content-between align-items-center py-1">
                            <span class="text-capitalize">{{ agent.replace('_', ' ') }}:</span>
                            <span class="text-muted">{{ status }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </details>
            </div>
        </div>

        <!-- Legal Disclaimer -->
        <div class="card border-warning">
            <div class="card-body">
                <h6 class="card-title text-warning">⚖️ Legal Disclaimer</h6>
                <p class="card-text small text-muted mb-0">
                    This analysis provides guidance only and is not legal advice. For commercial releases 
                    or serious concerns, please consult with a qualified music attorney. Results are based 
                    on algorithmic analysis and may not detect all potential issues.
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

        with open("src/templates/results.html", "w") as f:
            f.write(results_template)
        
        # About page template
        about_template = '''{% extends "base.html" %}

{% block title %}About - LyricLawyer{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <h1 class="mb-4">About LyricLawyer</h1>
        
        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">🎯 Mission</h5>
                <p class="card-text">
                    LyricLawyer helps songwriters avoid unintentional copyright infringement by 
                    analyzing their lyrics for potential similarities to existing copyrighted material 
                    and providing creative alternatives.
                </p>
            </div>
        </div>

        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">🤖 Agentic AI Architecture</h5>
                <p class="card-text">Built with Google's ADK framework featuring:</p>
                <ul>
                    <li><strong>Planner Agent:</strong> Breaks down analysis into systematic tasks</li>
                    <li><strong>Similarity Agent:</strong> Detects copyright similarities using Gemini AI</li>
                    <li><strong>Risk Agent:</strong> Assesses legal risk and provides recommendations</li>
                    <li><strong>Alternatives Agent:</strong> Generates creative, original alternatives</li>
                    <li><strong>Coordinator Agent:</strong> Orchestrates workflow and synthesizes results</li>
                </ul>
            </div>
        </div>

        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">🔬 Technology Stack</h5>
                <ul class="mb-0">
                    <li><strong>Google ADK:</strong> Agentic AI framework</li>
                    <li><strong>Gemini API:</strong> Advanced language model for analysis</li>
                    <li><strong>Multiple Algorithms:</strong> 8 similarity detection methods</li>
                    <li><strong>FastAPI:</strong> Modern web framework</li>
                    <li><strong>SQLite:</strong> Reference database for known songs</li>
                </ul>
            </div>
        </div>

        <div class="card border-info">
            <div class="card-body">
                <h5 class="card-title text-info">🏆 Hackathon Project</h5>
                <p class="card-text mb-0">
                    This project was created for the <strong>ODSC & Google Cloud Agentic AI Hackathon</strong> 
                    to demonstrate innovative applications of multi-agent systems in creative industries.
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

        with open("src/templates/about.html", "w") as f:
            f.write(about_template)
    
    def _create_static_files(self):
        """Create CSS and JavaScript files"""
        
        # CSS styles
        css_content = '''/* LyricLawyer Custom Styles */

.feature-icon {
    font-size: 3rem;
    opacity: 0.8;
}

.card {
    border: none;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    transition: box-shadow 0.15s ease-in-out;
}

.card:hover {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.navbar-brand {
    font-size: 1.5rem;
}

.btn-primary {
    background: linear-gradient(45deg, #007bff, #0056b3);
    border: none;
}

.btn-primary:hover {
    background: linear-gradient(45deg, #0056b3, #004085);
}

.progress {
    background-color: #f8f9fa;
}

.alert {
    border-left: 4px solid;
}

.alert-success {
    border-left-color: #28a745;
}

.alert-warning {
    border-left-color: #ffc107;
}

.alert-danger {
    border-left-color: #dc3545;
}

textarea {
    font-family: 'Courier New', monospace;
    font-size: 0.95rem;
    line-height: 1.4;
}

details summary {
    cursor: pointer;
    user-select: none;
}

details summary:hover {
    color: #007bff;
}

@media (max-width: 768px) {
    .display-4 {
        font-size: 2.5rem;
    }
    
    .feature-icon {
        font-size: 2rem;
    }
}

/* Loading spinner */
.loading {
    display: none;
    text-align: center;
    padding: 2rem;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 2s linear infinite;
    margin: 0 auto 1rem;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}'''

        with open("src/static/style.css", "w") as f:
            f.write(css_content)
        
        # JavaScript
        js_content = '''// LyricLawyer App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Form submission with loading state
    const form = document.querySelector('form[action="/analyze"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            // Show loading state
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
            submitBtn.disabled = true;
            
            // Reset after 30 seconds (timeout)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 30000);
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Auto-expand details on page load if there are flagged items
    const flaggedPhrases = document.querySelectorAll('.alert-danger, .alert-warning');
    if (flaggedPhrases.length > 0) {
        const details = document.querySelector('details');
        if (details) {
            details.open = true;
        }
    }
});

// Copy text to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Could add a toast notification here
        console.log('Copied to clipboard:', text);
    });
}

// Example usage analytics (would be implemented with proper analytics)
function trackEvent(eventName, properties) {
    console.log('Event:', eventName, properties);
    // In production, this would send to analytics service
}'''

        with open("src/static/app.js", "w") as f:
            f.write(js_content)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = True):
        """Run the web application"""
        uvicorn.run(self.app, host=host, port=port, reload=debug)


def create_web_app() -> LyricLawyerWebApp:
    """Factory function to create web app instance"""
    return LyricLawyerWebApp()

# Module-level app instance for uvicorn
web_app_instance = create_web_app()
app = web_app_instance.app

if __name__ == "__main__":
    web_app_instance.run()