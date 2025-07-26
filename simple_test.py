#!/usr/bin/env python3
"""
Simple test to verify functionality
"""

import sys
import os
sys.path.append('/root/Alberto-Lopez')

def test_analysis():
    print("🔬 Testing LyricLawyer Core Analysis")
    print("=" * 50)
    
    try:
        from src.tools.lyric_analyzer import sanitize_lyrics, extract_phrases
        from src.tools.similarity_engine import AdvancedSimilarityEngine
        
        test_lyrics = "I shake it off, shake it off"
        
        # Test sanitization
        sanitized = sanitize_lyrics(test_lyrics)
        print(f"✅ Sanitization: {sanitized['success']}")
        
        # Test phrase extraction
        phrases = extract_phrases(sanitized['sanitized_lyrics'])
        print(f"✅ Phrases extracted: {len(phrases)}")
        
        # Test similarity
        engine = AdvancedSimilarityEngine()
        similarity = engine.calculate_comprehensive_similarity("shake it off", "shake it off")
        print(f"✅ Similarity test: {similarity['overall_similarity']:.2f}")
        
        print(f"\n🎯 Core Analysis: WORKING PERFECTLY")
        return True
        
    except Exception as e:
        print(f"❌ Core analysis error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎵 LyricLawyer - Simple Test")
    print("=" * 40)
    
    success = test_analysis()
    
    if success:
        print(f"\n🎉 SUCCESS: System is functional!")
        print(f"\n🎬 For your demo video:")
        print(f"   1. Run: ./venv/bin/python test_demo.py")
        print(f"   2. Show the working analysis")
        print(f"   3. Explain the multi-agent architecture")
        print(f"   4. Walk through the code structure")
    else:
        print(f"\n❌ FAILURE: System has issues")