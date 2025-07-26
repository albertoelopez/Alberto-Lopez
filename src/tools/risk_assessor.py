"""
Risk Assessment Tools

This agent evaluates overall copyright risk based on similarity analysis results
and provides strategic recommendations.
"""

from typing import List, Dict, Any
import google.generativeai as genai
import os


def assess_copyright_risk(analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Assess overall copyright risk based on individual phrase analyses
    
    Args:
        analysis_results: List of similarity analysis results from analyze_similarity
        
    Returns:
        Overall risk assessment with recommendations
    """
    if not analysis_results:
        return {
            'overall_risk': 'LOW',
            'total_phrases_analyzed': 0,
            'flagged_phrases': 0,
            'high_risk_phrases': 0,
            'recommendations': ['No lyrics provided for analysis']
        }
    
    # Count risk levels
    risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
    flagged_phrases = []
    
    for result in analysis_results:
        risk_level = result['similarity_analysis']['risk_level']
        risk_counts[risk_level] += 1
        
        if result['flagged']:
            flagged_phrases.append({
                'phrase': result['phrase']['text'],
                'risk_level': risk_level,
                'line_number': result['phrase']['line_number'],
                'matched_song': result['similarity_analysis'].get('matched_song'),
                'matched_artist': result['similarity_analysis'].get('matched_artist'),
                'explanation': result['similarity_analysis'].get('explanation')
            })
    
    # Determine overall risk
    if risk_counts['CRITICAL'] > 0:
        overall_risk = 'CRITICAL'
    elif risk_counts['HIGH'] > 2:
        overall_risk = 'HIGH'
    elif risk_counts['HIGH'] > 0 or risk_counts['MEDIUM'] > 3:
        overall_risk = 'HIGH'
    elif risk_counts['MEDIUM'] > 0:
        overall_risk = 'MEDIUM'
    else:
        overall_risk = 'LOW'
    
    # Generate strategic recommendations using Gemini
    recommendations = _generate_strategic_recommendations(
        overall_risk, flagged_phrases, risk_counts
    )
    
    return {
        'overall_risk': overall_risk,
        'total_phrases_analyzed': len(analysis_results),
        'flagged_phrases': len(flagged_phrases),
        'high_risk_phrases': risk_counts['HIGH'] + risk_counts['CRITICAL'],
        'risk_breakdown': risk_counts,
        'flagged_details': flagged_phrases,
        'recommendations': recommendations,
        'priority_actions': _get_priority_actions(overall_risk, flagged_phrases)
    }


def _generate_strategic_recommendations(overall_risk: str, flagged_phrases: List[Dict], risk_counts: Dict) -> List[str]:
    """
    Generate strategic recommendations using Gemini based on risk assessment
    """
    if not flagged_phrases:
        return [
            "✅ Your lyrics appear to have low copyright risk",
            "Consider a final review with fresh eyes before recording",
            "Remember this is guidance only - consult legal counsel for commercial releases"
        ]
    
    # Configure Gemini if needed
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
    
    # Create context for recommendations
    flagged_summary = []
    for phrase_data in flagged_phrases[:5]:  # Top 5 to avoid token limits
        flagged_summary.append(
            f"'{phrase_data['phrase']}' - {phrase_data['risk_level']} risk "
            f"(similar to {phrase_data.get('matched_song', 'unknown song')})"
        )
    
    recommendations_prompt = f"""
    As a music copyright advisor, provide strategic recommendations for a songwriter based on this analysis:

    OVERALL RISK: {overall_risk}
    TOTAL FLAGGED PHRASES: {len(flagged_phrases)}
    RISK BREAKDOWN: {risk_counts}

    TOP FLAGGED PHRASES:
    {chr(10).join(flagged_summary)}

    Provide 3-5 practical, actionable recommendations in a supportive tone. Focus on:
    1. Immediate actions needed
    2. Revision strategies
    3. Legal considerations
    4. Creative alternatives approach

    Format as a numbered list. Be encouraging but honest about risks.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(recommendations_prompt)
        
        # Parse recommendations from response
        recommendations_text = response.text.strip()
        
        # Split into individual recommendations
        recommendations = []
        lines = recommendations_text.split('\n')
        current_rec = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a number (new recommendation)
            if line[0].isdigit() and '.' in line[:3]:
                if current_rec:
                    recommendations.append(current_rec.strip())
                current_rec = line
            else:
                current_rec += " " + line
        
        # Add the last recommendation
        if current_rec:
            recommendations.append(current_rec.strip())
        
        # Fallback if parsing fails
        if not recommendations:
            recommendations = [recommendations_text[:500] + "..."]
            
        return recommendations[:5]  # Limit to 5 recommendations
        
    except Exception as e:
        # Fallback recommendations
        return _get_fallback_recommendations(overall_risk, len(flagged_phrases))


def _get_fallback_recommendations(overall_risk: str, flagged_count: int) -> List[str]:
    """
    Provide fallback recommendations when Gemini API fails
    """
    base_recommendations = [
        "⚖️ This analysis provides guidance only - not legal advice",
        "🎵 Consider consulting a music attorney for commercial releases",
        "✍️ Focus on expressing your unique artistic voice and experiences"
    ]
    
    if overall_risk == 'CRITICAL':
        return [
            "🚨 URGENT: Multiple phrases closely match copyrighted songs",
            "✏️ Immediate revision recommended before any public use",
            "⚖️ Strongly consider legal consultation before proceeding"
        ] + base_recommendations
    
    elif overall_risk == 'HIGH':
        return [
            "⚠️ Several phrases may pose copyright concerns",
            "✏️ Recommend revising flagged phrases before recording",
            f"🔍 Focus on the {flagged_count} flagged phrases identified"
        ] + base_recommendations
    
    elif overall_risk == 'MEDIUM':
        return [
            "⚡ Some phrases worth reconsidering for originality",
            "✏️ Minor revisions could strengthen your copyright position",
            "🎯 Review flagged phrases and consider alternatives"
        ] + base_recommendations
    
    else:  # LOW risk
        return [
            "✅ Overall low copyright risk detected",
            "🎵 Your writing shows good originality",
            "👀 Consider one final review before finalizing"
        ] + base_recommendations


def _get_priority_actions(overall_risk: str, flagged_phrases: List[Dict]) -> List[str]:
    """
    Get specific priority actions based on risk level
    """
    actions = []
    
    if overall_risk in ['CRITICAL', 'HIGH']:
        # Sort flagged phrases by risk level
        critical_phrases = [p for p in flagged_phrases if p['risk_level'] == 'CRITICAL']
        high_phrases = [p for p in flagged_phrases if p['risk_level'] == 'HIGH']
        
        if critical_phrases:
            actions.append(f"🔥 IMMEDIATE: Revise {len(critical_phrases)} CRITICAL phrases")
            
        if high_phrases:
            actions.append(f"⚠️ HIGH PRIORITY: Address {len(high_phrases)} HIGH-risk phrases")
            
        actions.append("📝 Generate alternative phrasings for flagged content")
        actions.append("⚖️ Consider legal review before commercial use")
        
    elif overall_risk == 'MEDIUM':
        medium_phrases = [p for p in flagged_phrases if p['risk_level'] == 'MEDIUM']
        actions.append(f"📝 RECOMMENDED: Review {len(medium_phrases)} flagged phrases")
        actions.append("🎨 Explore more original expressions for flagged content")
        
    else:  # LOW risk
        actions.append("✅ No immediate actions required")
        actions.append("👀 Optional: Final creative review")
    
    return actions