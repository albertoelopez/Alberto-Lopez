"""
LyricLawyer Main Entry Point

Run this file to start the LyricLawyer web application.
"""

import sys
import os

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.web_interface import create_web_app

def main():
    """Main entry point"""
    print("🎵 Starting LyricLawyer - Copyright Compliance Checker")
    print("🤖 Powered by Google ADK & Gemini API")
    print("-" * 50)
    
    # Create and run the web application
    app = create_web_app()
    
    print("🚀 Starting web server...")
    print("📝 Open your browser to: http://localhost:8000")
    print("⚠️  Make sure to set your GOOGLE_API_KEY in .env file")
    print("-" * 50)
    
    # Run the application
    app.run(host="0.0.0.0", port=8000, debug=True)

if __name__ == "__main__":
    main()