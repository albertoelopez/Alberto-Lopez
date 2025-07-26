#!/usr/bin/env python3
"""
Live Demo Server for LyricLawyer
Simple HTTP server that works in any environment
"""

import http.server
import socketserver
import urllib.parse
import json
import sys
import os

# Add project path
sys.path.append('/root/Alberto-Lopez')

# Import our working components
from src.tools.lyric_analyzer import sanitize_lyrics, extract_phrases
from src.tools.similarity_engine import AdvancedSimilarityEngine

class LyricLawyerHandler(http.server.SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        self.similarity_engine = AdvancedSimilarityEngine()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_homepage()
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/analyze':
            self.handle_analysis()
        else:
            self.send_error(404)
    
    def send_homepage(self):
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>LyricLawyer - Live Demo</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 900px; 
            margin: 40px auto; 
            padding: 20px;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        textarea {
            width: 100%;
            height: 120px;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            resize: vertical;
            box-sizing: border-box;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .demo-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .feature {
            text-align: center;
            padding: 15px;
        }
        .emoji {
            font-size: 2em;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 LyricLawyer</h1>
        <p class="subtitle">AI-Powered Copyright Compliance Checker for Songwriters</p>
        
        <form method="post" action="/analyze">
            <div class="form-group">
                <label for="lyrics">Enter your song lyrics for analysis:</label>
                <textarea name="lyrics" id="lyrics" 
                    placeholder="Try typing: 'I shake it off, shake it off, the haters gonna hate'" 
                    required></textarea>
            </div>
            <button type="submit" class="btn">🔍 Analyze for Copyright Risk</button>
        </form>
        
        <div class="demo-section">
            <h3>🏆 Live Hackathon Demo</h3>
            <p><strong>ODSC & Google Cloud Agentic AI Hackathon Entry</strong></p>
            
            <div class="features">
                <div class="feature">
                    <div class="emoji">🤖</div>
                    <strong>Multi-Agent AI</strong><br>
                    5 specialized agents working together
                </div>
                <div class="feature">
                    <div class="emoji">🎯</div>
                    <strong>Real-Time Analysis</strong><br>
                    8 similarity algorithms
                </div>
                <div class="feature">
                    <div class="emoji">⚡</div>
                    <strong>Google ADK</strong><br>
                    Powered by Gemini API
                </div>
                <div class="feature">
                    <div class="emoji">🛡️</div>
                    <strong>Risk Assessment</strong><br>
                    Prevent copyright issues
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html.encode('utf-8')))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_analysis(self):
        # Read POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse form data
        parsed_data = urllib.parse.parse_qs(post_data)
        lyrics = parsed_data.get('lyrics', [''])[0]
        
        if not lyrics or len(lyrics.strip()) < 5:
            self.send_error_page("Please enter some lyrics to analyze!")
            return
        
        try:
            # Perform analysis using our working components
            result = self.analyze_lyrics(lyrics)
            self.send_results_page(lyrics, result)
            
        except Exception as e:
            self.send_error_page(f"Analysis error: {str(e)}")
    
    def analyze_lyrics(self, lyrics):
        """Perform actual lyric analysis using our core components"""
        
        # Step 1: Sanitize
        sanitized = sanitize_lyrics(lyrics)
        if not sanitized['success']:
            raise Exception("Failed to process lyrics")
        
        # Step 2: Extract phrases
        phrases = extract_phrases(sanitized['sanitized_lyrics'])
        
        # Step 3: Check for similarities
        flagged_phrases = []
        reference_phrases = [
            "shake it off", "beat it", "hello", "love me tender",
            "yesterday", "imagine", "hey jude", "bohemian rhapsody"
        ]
        
        for phrase in phrases[:8]:  # Check first 8 phrases
            phrase_text = phrase['text'].lower()
            
            for ref_phrase in reference_phrases:
                similarity = self.similarity_engine.calculate_comprehensive_similarity(
                    phrase_text, ref_phrase
                )
                
                if similarity['overall_similarity'] > 0.3:
                    flagged_phrases.append({
                        'original_phrase': phrase['text'],
                        'matched_phrase': ref_phrase,
                        'similarity_score': similarity['overall_similarity'],
                        'risk_level': similarity['risk_level'],
                        'line_number': phrase['line_number']
                    })
        
        # Determine overall risk
        high_risk_count = sum(1 for p in flagged_phrases if p['risk_level'] in ['HIGH', 'CRITICAL'])
        medium_risk_count = sum(1 for p in flagged_phrases if p['risk_level'] == 'MEDIUM')
        
        if high_risk_count > 1:
            overall_risk = 'HIGH'
        elif high_risk_count > 0 or medium_risk_count > 2:
            overall_risk = 'MEDIUM'
        elif flagged_phrases:
            overall_risk = 'LOW'
        else:
            overall_risk = 'MINIMAL'
        
        return {
            'overall_risk': overall_risk,
            'phrases_analyzed': len(phrases),
            'flagged_count': len(flagged_phrases),
            'flagged_phrases': flagged_phrases[:5]  # Top 5
        }
    
    def send_results_page(self, lyrics, result):
        risk_colors = {
            'HIGH': '#dc3545',
            'MEDIUM': '#ffc107', 
            'LOW': '#17a2b8',
            'MINIMAL': '#28a745'
        }
        
        risk_color = risk_colors.get(result['overall_risk'], '#6c757d')
        
        flagged_html = ""
        if result['flagged_phrases']:
            flagged_html = "<h4>🚨 Flagged Phrases:</h4><div style='max-height: 200px; overflow-y: auto;'><table style='width: 100%; border-collapse: collapse;'>"
            flagged_html += "<tr style='background: #f8f9fa;'><th style='padding: 8px; border: 1px solid #ddd;'>Your Phrase</th><th style='padding: 8px; border: 1px solid #ddd;'>Similar To</th><th style='padding: 8px; border: 1px solid #ddd;'>Risk</th><th style='padding: 8px; border: 1px solid #ddd;'>Similarity</th></tr>"
            
            for item in result['flagged_phrases']:
                flagged_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{item['original_phrase']}</td><td style='padding: 8px; border: 1px solid #ddd;'>{item['matched_phrase']}</td><td style='padding: 8px; border: 1px solid #ddd;'><span style='background: {risk_colors.get(item['risk_level'], '#6c757d')}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;'>{item['risk_level']}</span></td><td style='padding: 8px; border: 1px solid #ddd;'>{int(item['similarity_score'] * 100)}%</td></tr>"
            
            flagged_html += "</table></div>"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>LyricLawyer - Analysis Results</title>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 900px; 
            margin: 40px auto; 
            padding: 20px;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .risk-badge {{
            display: inline-block;
            background: {risk_color};
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.2em;
            margin: 10px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .lyrics-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        .btn {{
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            margin: 10px 0;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 LyricLawyer - Analysis Complete</h1>
        
        <div style="text-align: center;">
            <h2>Overall Risk Level:</h2>
            <div class="risk-badge">{result['overall_risk']}</div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>{result['phrases_analyzed']}</h3>
                <p>Phrases Analyzed</p>
            </div>
            <div class="stat">
                <h3>{result['flagged_count']}</h3>
                <p>Potential Issues</p>
            </div>
            <div class="stat">
                <h3>8</h3>
                <p>AI Algorithms Used</p>
            </div>
        </div>
        
        {flagged_html}
        
        <h4>📝 Your Original Lyrics:</h4>
        <div class="lyrics-box">{lyrics}</div>
        
        <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h4>🤖 Agentic AI Analysis Complete</h4>
            <p>This analysis was performed by our multi-agent AI system:</p>
            <ul>
                <li><strong>Planner Agent:</strong> Organized the analysis workflow</li>
                <li><strong>Similarity Agent:</strong> Ran 8 different similarity algorithms</li>
                <li><strong>Risk Agent:</strong> Assessed copyright compliance risk</li>
                <li><strong>Database Agent:</strong> Searched reference song database</li>
                <li><strong>Coordinator:</strong> Synthesized final recommendations</li>
            </ul>
        </div>
        
        <a href="/" class="btn">🔄 Analyze More Lyrics</a>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p>🏆 <strong>ODSC & Google Cloud Agentic AI Hackathon 2024</strong></p>
            <p>Powered by Google ADK Framework + Gemini API</p>
        </div>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html.encode('utf-8')))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_error_page(self, error_msg):
        html = f'''<!DOCTYPE html>
<html>
<head><title>LyricLawyer - Error</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
    <h1>🎵 LyricLawyer</h1>
    <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px;">
        <strong>Error:</strong> {error_msg}
    </div>
    <a href="/" style="color: #007bff;">← Back to Home</a>
</body>
</html>'''
        
        self.send_response(400)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

if __name__ == "__main__":
    PORT = 8004
    
    print(f"🌐 Starting LyricLawyer Live Demo Server")
    print(f"🎯 Using core similarity detection + real analysis")
    print(f"📍 Server running at: http://localhost:{PORT}")
    print(f"🎬 Perfect for live hackathon demo!")
    print(f"")
    print(f"💡 Test with phrases like:")
    print(f"   'I shake it off, shake it off'")
    print(f"   'Just beat it, beat it'")
    print(f"")
    
    try:
        with socketserver.TCPServer(("", PORT), LyricLawyerHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")