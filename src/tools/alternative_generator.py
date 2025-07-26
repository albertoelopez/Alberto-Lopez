"""
Alternative Generation Tools

This agent creates original alternatives for flagged phrases while maintaining
artistic intent, rhyme scheme, and emotional impact.
"""

from typing import List, Dict, Any
import google.generativeai as genai
import os
import re
from .api_optimizer import make_optimized_request


def generate_alternatives(flagged_phrases: List[Dict[str, Any]], preserve_rhyme: bool = True) -> Dict[str, Any]:
    """
    Generate creative alternatives for flagged phrases using Gemini
    
    Args:
        flagged_phrases: List of flagged phrase data from risk assessment
        preserve_rhyme: Whether to maintain rhyme scheme compatibility
        
    Returns:
        Dictionary with alternatives for each flagged phrase
    """
    if not flagged_phrases:
        return {
            'alternatives_generated': 0,
            'phrase_alternatives': {},
            'summary': 'No flagged phrases require alternatives'
        }
    
    # Configure Gemini API
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    
    phrase_alternatives = {}
    
    # Process each flagged phrase
    for phrase_data in flagged_phrases:
        phrase_text = phrase_data['phrase']
        risk_level = phrase_data['risk_level']
        original_line = phrase_data.get('original_line', phrase_text)
        matched_song = phrase_data.get('matched_song', 'unknown song')
        
        # Generate alternatives for this specific phrase
        alternatives = _generate_phrase_alternatives(
            phrase_text, original_line, risk_level, matched_song, preserve_rhyme
        )
        
        phrase_alternatives[phrase_text] = {
            'original_phrase': phrase_text,
            'risk_level': risk_level,
            'original_line': original_line,
            'matched_reference': matched_song,
            'alternatives': alternatives,
            'line_number': phrase_data.get('line_number', 0)
        }
    
    return {
        'alternatives_generated': len(phrase_alternatives),
        'phrase_alternatives': phrase_alternatives,
        'summary': f'Generated alternatives for {len(phrase_alternatives)} flagged phrases',
        'usage_tips': _get_usage_tips(preserve_rhyme)
    }


def _generate_phrase_alternatives(phrase: str, original_line: str, risk_level: str, 
                                matched_song: str, preserve_rhyme: bool) -> List[Dict[str, Any]]:
    """
    Generate alternatives for a single phrase using Gemini
    """
    # Analyze rhyme pattern if needed
    rhyme_info = ""
    if preserve_rhyme:
        rhyme_info = _analyze_rhyme_pattern(original_line)
    
    alternatives_prompt = f"""
    As a creative songwriting assistant, help rewrite this potentially problematic lyric phrase:

    ORIGINAL PHRASE: "{phrase}"
    FULL LINE CONTEXT: "{original_line}"
    RISK LEVEL: {risk_level}
    SIMILAR TO: {matched_song}
    RHYME REQUIREMENTS: {rhyme_info if preserve_rhyme else "No specific rhyme requirements"}

    Generate 4-5 creative alternatives that:
    1. Express a similar emotion/meaning to the original
    2. Are completely original and avoid copyright issues
    3. {"Maintain compatible rhyme scheme" if preserve_rhyme else "Focus on natural expression"}
    4. Keep similar syllable count and rhythm
    5. Sound natural and authentic

    For each alternative, provide:
    - The alternative phrase
    - Brief explanation of why it's safer
    - How it preserves the original meaning

    Format your response as:
    ALTERNATIVE 1: "[new phrase]"
    EXPLANATION: [why it's better/safer]

    ALTERNATIVE 2: "[new phrase]"
    EXPLANATION: [why it's better/safer]

    ... (continue for 4-5 alternatives)

    Focus on creativity and originality while maintaining the songwriter's artistic intent.
    """
    
    try:
        # Use optimized API request for better performance
        api_response = make_optimized_request(
            alternatives_prompt, 
            task_type="alternatives", 
            priority=2  # Medium priority
        )
        
        if not api_response.success:
            raise Exception(f"API request failed: {api_response.error}")
        
        # Parse the alternatives from the response
        alternatives = _parse_alternatives_response(api_response.content)
        
        # Add quality scores
        for alt in alternatives:
            alt['quality_score'] = _assess_alternative_quality(
                alt['alternative'], phrase, original_line
            )
        
        # Sort by quality score
        alternatives.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return alternatives[:5]  # Return top 5 alternatives
        
    except Exception as e:
        # Fallback alternatives
        return _generate_fallback_alternatives(phrase, original_line)


def _parse_alternatives_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse Gemini's response to extract alternatives and explanations
    """
    alternatives = []
    lines = response_text.split('\n')
    
    current_alt = None
    current_explanation = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for alternative patterns
        if line.startswith('ALTERNATIVE') and ':' in line:
            # Save previous alternative if exists
            if current_alt and current_explanation:
                alternatives.append({
                    'alternative': current_alt,
                    'explanation': current_explanation,
                    'quality_score': 0.0  # Will be calculated later
                })
            
            # Extract new alternative
            alt_text = line.split(':', 1)[1].strip().strip('"\'')
            current_alt = alt_text
            current_explanation = None
            
        elif line.startswith('EXPLANATION') and ':' in line:
            current_explanation = line.split(':', 1)[1].strip()
        
        elif current_alt and not current_explanation and not line.startswith('ALTERNATIVE'):
            # Continuation of explanation
            current_explanation = line
    
    # Add the last alternative
    if current_alt and current_explanation:
        alternatives.append({
            'alternative': current_alt,
            'explanation': current_explanation,
            'quality_score': 0.0
        })
    
    return alternatives


def _assess_alternative_quality(alternative: str, original: str, original_line: str) -> float:
    """
    Assess the quality of an alternative phrase
    """
    quality_score = 0.0
    
    # Length similarity (prefer similar syllable count)
    original_words = len(original.split())
    alt_words = len(alternative.split())
    length_similarity = 1.0 - abs(original_words - alt_words) * 0.1
    quality_score += length_similarity * 0.3
    
    # Avoid being too similar to original
    similarity_penalty = 0.0
    if alternative.lower() == original.lower():
        similarity_penalty = -1.0
    elif len(set(alternative.lower().split()) & set(original.lower().split())) > len(original.split()) * 0.5:
        similarity_penalty = -0.5
    
    quality_score += similarity_penalty
    
    # Creativity bonus (presence of interesting words)
    creative_words = ['dream', 'light', 'fire', 'soul', 'heart', 'story', 'journey', 'moment']
    if any(word in alternative.lower() for word in creative_words):
        quality_score += 0.2
    
    # Natural language bonus (avoid awkward constructions)
    if not re.search(r'\b(very|really|quite|just)\s+(very|really|quite|just)\b', alternative.lower()):
        quality_score += 0.1
    
    return max(0.0, min(1.0, quality_score))


def _analyze_rhyme_pattern(line: str) -> str:
    """
    Analyze the rhyme pattern of a line to help maintain consistency
    """
    words = line.split()
    if not words:
        return "No rhyme pattern detected"
    
    last_word = words[-1].lower().strip('.,!?;:')
    
    # Common ending sounds
    if last_word.endswith('ing'):
        return f"Rhymes with '-ing' sound (like {last_word})"
    elif last_word.endswith('ight'):
        return f"Rhymes with '-ight' sound (like {last_word})"
    elif last_word.endswith('ay'):
        return f"Rhymes with '-ay' sound (like {last_word})"
    elif last_word.endswith('ove'):
        return f"Rhymes with '-ove' sound (like {last_word})"
    else:
        return f"Should rhyme with '{last_word}' or similar ending sound"


def _generate_fallback_alternatives(phrase: str, original_line: str) -> List[Dict[str, Any]]:
    """
    Generate basic fallback alternatives when Gemini API fails
    """
    # Simple word substitutions for common problematic phrases
    substitutions = {
        'shake it off': ['brush it away', 'let it go', 'move ahead', 'push it aside'],
        'baby': ['honey', 'darling', 'sweetheart', 'my love'],
        'love you': ['adore you', 'cherish you', 'treasure you', 'need you'],
        'dance all night': ['party till dawn', 'celebrate together', 'move until morning', 'groove forever'],
        'hold me tight': ['embrace me close', 'keep me near', 'pull me closer', 'stay with me']
    }
    
    phrase_lower = phrase.lower()
    alternatives = []
    
    # Look for direct substitutions
    for key, subs in substitutions.items():
        if key in phrase_lower:
            for i, sub in enumerate(subs):
                alternatives.append({
                    'alternative': phrase_lower.replace(key, sub).title(),
                    'explanation': f'Replaces potentially problematic phrase with original expression',
                    'quality_score': 0.7 - (i * 0.1)
                })
    
    # Generic alternatives if no specific substitutions found
    if not alternatives:
        alternatives = [
            {
                'alternative': f'[Original expression for: {phrase}]',
                'explanation': 'Consider rewriting with your own unique perspective',
                'quality_score': 0.5
            },
            {
                'alternative': f'[Creative alternative to: {phrase}]',
                'explanation': 'Focus on your personal experience and voice',
                'quality_score': 0.4
            }
        ]
    
    return alternatives[:3]


def _get_usage_tips(preserve_rhyme: bool) -> List[str]:
    """
    Provide tips for using the generated alternatives
    """
    tips = [
        "🎵 Try singing each alternative to test the flow and rhythm",
        "✍️ Feel free to modify suggestions to match your personal style",
        "🎯 Focus on alternatives that feel authentic to your artistic voice",
        "📝 Consider combining elements from multiple alternatives"
    ]
    
    if preserve_rhyme:
        tips.insert(1, "🎼 Rhyme-compatible alternatives are prioritized for your song structure")
    
    tips.append("⚖️ Remember: Originality is your best copyright protection")
    
    return tips