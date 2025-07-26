#!/usr/bin/env python3
"""
Simple test to verify web interface analysis method
"""

import sys
import os
sys.path.append('/root/Alberto-Lopez')

def test_web_analysis():
    print("🌐 Testing Web Interface Analysis")
    print("=" * 50)
    
    try:
        # Test direct agent analysis first
        print("1️⃣ Testing agent directly...")
        from src.agent import LyricLawyerAgent
        agent = LyricLawyerAgent()
        
        test_lyrics = "I shake it off, shake it off"
        result = agent.analyze_lyrics(test_lyrics, {})
        print(f"   ✅ Agent analysis: {result.get('overall_risk', 'Success')}")
        
        # Test web interface creation
        print("\n2️⃣ Testing web interface...")
        from src.web_interface import LyricLawyerWebApp
        web_app = LyricLawyerWebApp()
        print(f"   ✅ Web app created: {web_app.app.title}")
        
        # Test the analysis through web app
        print("\n3️⃣ Testing web app analysis...")
        web_result = web_app.agent_system.analyze_lyrics(test_lyrics, {})
        print(f"   ✅ Web analysis: {web_result.get('overall_risk', 'Success')}")
        
        print(f"\n🎯 Web Interface Test: SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_web_analysis()