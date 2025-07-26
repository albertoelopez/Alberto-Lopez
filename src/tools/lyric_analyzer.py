"""
Lyric Analysis Tools

These tools handle the core text processing and similarity detection
for the LyricLawyer agent using real Gemini API analysis.
"""

import re
import string
from typing import List, Dict, Any
import google.generativeai as genai
import os

from .input_validator import validate_lyrics_input, LyricValidationError


def sanitize_lyrics(lyrics: str, user_id: str = None) -> Dict[str, Any]:
    """
    Clean and prepare lyrics text for analysis with comprehensive validation
    
    Args:
        lyrics: Raw lyric text input
        user_id: Optional user identifier for tracking
        
    Returns:
        Dictionary with sanitized lyrics and validation results
    """
    # First, validate the input
    validation_result = validate_lyrics_input(lyrics, user_id)
    
    if not validation_result['valid']:
        return {
            'success': False,
            'sanitized_lyrics': '',
            'validation_result': validation_result,
            'error_message': '; '.join(validation_result['errors'])
        }
    
    # Use the pre-sanitized lyrics from validation
    sanitized = validation_result['sanitized_lyrics']
    
    # Additional music-specific cleaning
    # Remove common music notation that might have been missed
    sanitized = re.sub(r'\[.*?\]', '', sanitized)  # Remove [Verse], [Chorus] etc.
    sanitized = re.sub(r'\(.*?\)', '', sanitized)  # Remove (x2), (repeat) etc.
    
    # Remove timestamps if present (e.g., [0:30])
    sanitized = re.sub(r'\[\d+:\d+\]', '', sanitized)
    
    # Final cleanup
    lines = sanitized.split('\n')
    cleaned_lines = [' '.join(line.split()) for line in lines]
    final_cleaned = '\n'.join(line for line in cleaned_lines if line.strip())
    
    return {
        'success': True,
        'sanitized_lyrics': final_cleaned,
        'validation_result': validation_result,
        'processing_metadata': {
            'original_length': len(lyrics),
            'cleaned_length': len(final_cleaned),
            'warnings': validation_result['warnings'],
            'estimated_processing_time': validation_result['metadata']['estimated_processing_time']
        }
    }


def extract_phrases(lyrics: str, min_length: int = 2, max_length: int = 8) -> List[Dict[str, Any]]:
    """
    Extract meaningful phrases from lyrics for analysis
    
    Args:
        lyrics: Sanitized lyric text
        min_length: Minimum phrase length in words
        max_length: Maximum phrase length in words
        
    Returns:
        List of phrase dictionaries with metadata
    """
    if not lyrics:
        return []
    
    phrases = []
    lines = lyrics.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        words = line.split()
        
        # Extract phrases of different lengths
        for length in range(min_length, min(max_length + 1, len(words) + 1)):
            for start_idx in range(len(words) - length + 1):
                phrase_words = words[start_idx:start_idx + length]
                phrase_text = ' '.join(phrase_words)
                
                # Skip generic phrases
                if _is_generic_phrase(phrase_text):
                    continue
                
                phrase_data = {
                    'text': phrase_text,
                    'line_number': line_num,
                    'start_position': start_idx,
                    'length': length,
                    'word_count': len(phrase_words),
                    'original_line': line
                }
                
                phrases.append(phrase_data)
    
    # Remove duplicates and sort by potential importance
    unique_phrases = []
    seen_phrases = set()
    
    for phrase in phrases:
        phrase_key = phrase['text'].lower()
        if phrase_key not in seen_phrases:
            seen_phrases.add(phrase_key)
            unique_phrases.append(phrase)
    
    # Sort by length (longer phrases first) and then alphabetically
    unique_phrases.sort(key=lambda p: (-p['word_count'], p['text'].lower()))
    
    # Limit to top 20 phrases to avoid API overuse
    return unique_phrases[:20]


def analyze_similarity(phrase_data: Dict[str, Any], known_phrases: List[str] = None) -> Dict[str, Any]:
    """
    Analyze a single phrase for similarity using advanced algorithms + Gemini
    
    Args:
        phrase_data: Phrase dictionary from extract_phrases
        known_phrases: Optional list of known copyrighted phrases to check against
        
    Returns:
        Comprehensive analysis result with similarity assessment
    """
    from .similarity_engine import get_similarity_engine
    
    phrase_text = phrase_data['text']
    
    # Get known phrases to compare against
    if known_phrases is None:
        known_phrases = _get_default_known_phrases()
    
    # Use advanced similarity engine for algorithmic analysis
    similarity_engine = get_similarity_engine()
    best_match = None
    highest_similarity = 0.0
    
    # Compare against known phrases using multiple algorithms
    for known_phrase in known_phrases:
        similarity_result = similarity_engine.calculate_comprehensive_similarity(
            phrase_text, known_phrase
        )
        
        if similarity_result['overall_similarity'] > highest_similarity:
            highest_similarity = similarity_result['overall_similarity']
            best_match = {
                'matched_phrase': known_phrase,
                'similarity_score': similarity_result['overall_similarity'],
                'risk_level': similarity_result['risk_level'],
                'algorithm_details': similarity_result['algorithm_results'],
                'explanation': similarity_result['explanation'],
                'confidence': similarity_result['confidence']
            }
    
    # Enhance with Gemini analysis for context and song identification
    gemini_analysis = _get_gemini_context_analysis(phrase_text, best_match)
    
    # Combine algorithmic and AI analysis
    final_risk_level = _determine_final_risk_level(best_match, gemini_analysis)
    
    return {
        'phrase': phrase_data,
        'similarity_analysis': {
            'risk_level': final_risk_level,
            'similarity_found': highest_similarity >= 0.5,
            'similarity_score': highest_similarity,
            'matched_song': gemini_analysis.get('matched_song'),
            'matched_artist': gemini_analysis.get('matched_artist'),
            'matched_phrase': best_match['matched_phrase'] if best_match else None,
            'explanation': _generate_combined_explanation(best_match, gemini_analysis),
            'confidence': best_match['confidence'] if best_match else 0.0,
            'algorithm_breakdown': best_match['algorithm_details'] if best_match else {},
            'gemini_context': gemini_analysis
        },
        'flagged': final_risk_level in ['HIGH', 'CRITICAL'],
        'processing_method': 'advanced_algorithms_plus_gemini'
    }


def _get_default_known_phrases() -> List[str]:
    """Get default database of known copyrighted phrases"""
    
    return [
        # Pop/Rock classics
        "shake it off shake it off",
        "i got a blank space baby",
        "hello is it me you're looking for",
        "i will always love you",
        "billie jean is not my lover",
        "don't stop believing",
        "we are the champions my friends",
        "bohemian rhapsody",
        "yesterday all my troubles seemed so far away",
        "imagine all the people living life in peace",
        "hotel california on a dark desert highway",
        "stairway to heaven and she's buying",
        "sweet child o mine",
        "smells like teen spirit",
        
        # Modern hits
        "baby one more time",
        "call me maybe",
        "rolling in the deep",
        "somebody that i used to know",
        "uptown funk you up",
        "shape of you",
        "despacito quiero respirar tu cuello",
        "bad guy i'm the bad guy",
        "blinding lights i've been trying to feel",
        "watermelon sugar high",
        "drivers license got my driver's license",
        "levitating i got you moonlight",
        
        # R&B/Hip-Hop
        "crazy in love got me looking so crazy",
        "single ladies put a ring on it",
        "empire state of mind",
        "lose yourself in the music",
        "in da club go shorty",
        "hey ya shake it like a picture",
        "i like it like that",
        "god's plan i only love",
        
        # Dance/Electronic
        "titanium i am titanium",
        "levels oh sometimes",
        "wake me up when it's all over",
        "closer pull the sheets right over",
        "one more time celebrate and dance",
        
        # Country
        "friends in low places",
        "sweet caroline touching hands",
        "country roads take me home",
        "ring of fire burns burns",
        "jolene jolene jolene jolene",
        
        # Common patterns and themes
        "dance all night long",
        "love you forever and always",
        "never gonna give you up",
        "take me home tonight",
        "party like it's 1999",
        "living on a prayer",
        "don't worry be happy",
        "i can't get no satisfaction",
        "we will rock you",
        "another one bites the dust"
    ]


def _get_gemini_context_analysis(phrase_text: str, best_match: Dict = None) -> Dict[str, Any]:
    """Get Gemini analysis for song identification and context"""
    
    # Configure Gemini client
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    
    context_info = f" (algorithmically similar to: '{best_match['matched_phrase']}')" if best_match else ""
    
    gemini_prompt = f"""
    As a music copyright expert, analyze this lyric phrase for potential song matches:

    PHRASE: "{phrase_text}"{context_info}

    Please identify:
    1. Does this match or closely resemble any specific famous song?
    2. Song title and artist if identified
    3. Your confidence in this identification
    4. Any additional context about potential copyright concerns

    Respond in JSON format:
    {{
        "matched_song": "Song Title or null",
        "matched_artist": "Artist Name or null", 
        "identification_confidence": "LOW|MEDIUM|HIGH",
        "additional_context": "Brief context or concerns",
        "gemini_risk_assessment": "LOW|MEDIUM|HIGH|CRITICAL"
    }}
    
    Focus on well-known commercial songs. Be conservative - only identify matches you're confident about.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(gemini_prompt)
        response_text = response.text.strip()
        
        # Parse JSON response
        import json
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Fallback parsing
        return _parse_gemini_response_fallback(response_text)
        
    except Exception as e:
        return {
            'matched_song': None,
            'matched_artist': None,
            'identification_confidence': 'LOW',
            'additional_context': f'Analysis failed: {str(e)}',
            'gemini_risk_assessment': 'LOW'
        }


def _determine_final_risk_level(algorithmic_match: Dict, gemini_analysis: Dict) -> str:
    """Determine final risk level combining algorithmic and AI analysis"""
    
    algorithmic_risk = algorithmic_match['risk_level'] if algorithmic_match else 'LOW'
    gemini_risk = gemini_analysis.get('gemini_risk_assessment', 'LOW')
    
    # Risk level hierarchy
    risk_hierarchy = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
    
    # Take the higher of the two assessments
    final_risk_level = max(algorithmic_risk, gemini_risk, key=lambda x: risk_hierarchy[x])
    
    # Boost risk if both systems agree on medium+ risk
    if (risk_hierarchy[algorithmic_risk] >= 1 and 
        risk_hierarchy[gemini_risk] >= 1 and
        final_risk_level != 'CRITICAL'):
        
        # Increase risk level by one step
        current_level = risk_hierarchy[final_risk_level]
        if current_level < 3:
            risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            final_risk_level = risk_levels[current_level + 1]
    
    return final_risk_level


def _generate_combined_explanation(algorithmic_match: Dict, gemini_analysis: Dict) -> str:
    """Generate combined explanation from both analysis methods"""
    
    explanations = []
    
    # Add algorithmic insights
    if algorithmic_match:
        explanations.append(f"Algorithmic analysis: {algorithmic_match['explanation']}")
        if algorithmic_match['similarity_score'] >= 0.8:
            explanations.append(f"High similarity score: {algorithmic_match['similarity_score']:.2f}")
    
    # Add Gemini insights
    if gemini_analysis.get('matched_song'):
        song_info = f"{gemini_analysis['matched_song']} by {gemini_analysis['matched_artist']}"
        explanations.append(f"Potentially matches: {song_info}")
    
    if gemini_analysis.get('additional_context'):
        explanations.append(f"Context: {gemini_analysis['additional_context']}")
    
    return "; ".join(explanations) if explanations else "No significant similarity detected"


def _parse_gemini_response_fallback(response_text: str) -> Dict[str, Any]:
    """
    Fallback parser for Gemini responses that don't return proper JSON
    """
    response_lower = response_text.lower()
    
    # Determine risk level
    if 'critical' in response_lower:
        risk_level = 'CRITICAL'
    elif 'high' in response_lower:
        risk_level = 'HIGH'
    elif 'medium' in response_lower:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    # Check for similarity indicators
    similarity_indicators = ['matches', 'similar', 'resembles', 'identical', 'like']
    similarity_found = any(indicator in response_lower for indicator in similarity_indicators)
    
    return {
        'risk_level': risk_level,
        'similarity_found': similarity_found,
        'matched_song': 'Unknown',
        'matched_artist': 'Unknown',
        'explanation': response_text[:200] + '...' if len(response_text) > 200 else response_text,
        'confidence': 'MEDIUM'
    }


def _is_generic_phrase(phrase: str) -> bool:
    """
    Check if a phrase is too generic to be copyrightable
    
    Args:
        phrase: Text phrase to check
        
    Returns:
        True if phrase is generic, False otherwise
    """
    phrase_lower = phrase.lower().strip()
    
    # Common articles, prepositions, and generic phrases
    generic_patterns = {
        # Articles and prepositions
        "in the", "on the", "to the", "at the", "of the", "for the", "with the",
        "and the", "but the", "or the", "from the", "by the",
        
        # Common verb phrases
        "i am", "you are", "we are", "they are", "it is", "that is", "this is",
        "i will", "you will", "we will", "i can", "you can", "we can",
        "i have", "you have", "we have", "i want", "you want", "we want",
        
        # Time references
        "all day", "all night", "right now", "tonight", "today", "yesterday",
        
        # Generic emotions (single word combinations)  
        "so good", "so bad", "so sad", "so happy", "very good", "very bad",
        
        # Common connectors
        "and then", "but then", "so then", "and now", "but now", "so now"
    }
    
    # Check exact matches
    if phrase_lower in generic_patterns:
        return True
    
    # Check for very short phrases (2 words or less with common words)
    words = phrase_lower.split()
    if len(words) <= 2:
        common_words = {
            'i', 'you', 'we', 'they', 'he', 'she', 'it', 'me', 'us', 'them',
            'a', 'an', 'the', 'and', 'or', 'but', 'so', 'if', 'when', 'where',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should',
            'my', 'your', 'our', 'their', 'his', 'her', 'its', 'this', 'that'
        }
        
        if all(word in common_words for word in words):
            return True
    
    return False