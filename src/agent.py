"""
LyricLawyer Agent - Copyright Compliance Checker for Songwriters

This agent uses Google's ADK framework with a true agentic architecture featuring
specialized sub-agents for planning, analysis, risk assessment, and alternative generation.
"""

import os
import re
import time
from typing import List, Dict, Any, Optional
from google.adk.agents import Agent
import google.generativeai as genai

# Import our custom tools  
from .tools.lyric_analyzer import sanitize_lyrics, extract_phrases, analyze_similarity
from .tools.alternative_generator import generate_alternatives
from .tools.risk_assessor import assess_copyright_risk
from .tools.cache_manager import get_cached_analysis, cache_analysis_result, get_cache
from .prompt import LYRIC_LAWYER_PROMPT, PLANNER_PROMPT, COORDINATOR_PROMPT


class LyricLawyerAgent:
    """
    Main LyricLawyer agent using Google ADK framework with agentic architecture
    """
    
    def __init__(self):
        self.setup_agents()
        self.analysis_memory = {}  # Stores analysis state and results
    
    def setup_agents(self) -> None:
        """Initialize the multi-agent system with specialized roles"""
        
        # Planner Agent - Breaks down analysis into subtasks
        self.planner_agent = Agent(
            name="lyric_planner",
            model="gemini-2.0-flash-exp", 
            instruction=PLANNER_PROMPT,
            tools=[sanitize_lyrics, extract_phrases]
        )
        
        # Similarity Analysis Agent - Specialized in copyright detection
        self.similarity_agent = Agent(
            name="similarity_analyzer",
            model="gemini-2.0-flash-exp",
            instruction="You are a copyright similarity expert. Analyze phrases for potential matches to known songs with high accuracy.",
            tools=[analyze_similarity]
        )
        
        # Risk Assessment Agent - Evaluates legal risk
        self.risk_agent = Agent(
            name="risk_assessor",
            model="gemini-2.0-flash-exp",
            instruction="You are a music copyright advisor. Evaluate risk levels and provide practical legal guidance.",
            tools=[assess_copyright_risk]
        )
        
        # Alternative Generation Agent - Creates original alternatives
        self.alternatives_agent = Agent(
            name="alternative_generator",
            model="gemini-2.0-flash-exp",
            instruction="You are a creative songwriting assistant. Generate original alternatives that maintain rhyme, rhythm, and meaning.",
            tools=[generate_alternatives]
        )
        
        # Coordinator Agent - Orchestrates the workflow
        self.coordinator = Agent(
            name="lyric_coordinator",
            model="gemini-2.0-flash-exp",
            instruction=COORDINATOR_PROMPT,
            tools=[]  # Coordinator doesn't use tools directly
        )
    
    def analyze_lyrics(self, lyrics: str, user_preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main entry point for agentic lyric analysis workflow
        
        Args:
            lyrics: Raw song lyrics to analyze
            user_preferences: Optional user settings (similarity threshold, etc.)
            
        Returns:
            Comprehensive analysis results from multi-agent collaboration
        """
        if user_preferences is None:
            user_preferences = {}
        
        print("🎵 Starting multi-agent lyric analysis...")
        
        # Check cache first for performance optimization
        start_time = time.time()
        cached_result = get_cached_analysis(lyrics, user_preferences)
        
        if cached_result:
            print("⚡ Cache hit! Returning cached analysis result")
            cache_stats = get_cache().get_cache_stats()
            cached_result['cache_hit'] = True
            cached_result['analysis_time'] = time.time() - start_time
            cached_result['cache_stats'] = cache_stats
            return cached_result
        
        print("💾 Cache miss - performing full analysis")
        
        # Initialize analysis memory
        analysis_id = f"analysis_{hash(lyrics[:50])}"
        self.analysis_memory[analysis_id] = {
            'status': 'in_progress',
            'original_lyrics': lyrics,
            'user_preferences': user_preferences,
            'workflow_steps': [],
            'start_time': start_time
        }
        
        try:
            # STEP 1: Planner Agent - Break down the analysis task
            print("🧠 Planner Agent: Breaking down analysis tasks...")
            planning_prompt = f"""
            Plan the analysis for these lyrics:
            
            LYRICS:
            {lyrics}
            
            USER PREFERENCES:
            {user_preferences}
            
            Create a systematic analysis plan and extract prioritized phrases for checking.
            """
            
            planning_result = self.planner_agent.run_live(planning_prompt)
            self.analysis_memory[analysis_id]['workflow_steps'].append({
                'agent': 'planner',
                'result': planning_result,
                'status': 'completed'
            })
            
            # Extract phrases using planner's approach with validation
            sanitization_result = sanitize_lyrics(lyrics)
            
            if not sanitization_result['success']:
                # Handle validation errors
                return {
                    'error': f'Input validation failed: {sanitization_result["error_message"]}',
                    'validation_details': sanitization_result['validation_result'],
                    'analysis_id': analysis_id,
                    'status': 'validation_failed'
                }
            
            sanitized_lyrics = sanitization_result['sanitized_lyrics']
            processing_metadata = sanitization_result['processing_metadata']
            
            # Show validation warnings if any
            if processing_metadata['warnings']:
                for warning in processing_metadata['warnings']:
                    print(f"⚠️ Warning: {warning}")
            
            extracted_phrases = extract_phrases(sanitized_lyrics)
            
            print(f"📝 Extracted {len(extracted_phrases)} phrases for analysis")
            
            # STEP 2: Similarity Agent - Analyze each phrase
            print("🔍 Similarity Agent: Checking for copyright matches...")
            similarity_results = []
            
            # Analyze top phrases (limit to avoid API overuse)
            for phrase_data in extracted_phrases[:10]:
                similarity_result = analyze_similarity(phrase_data)
                similarity_results.append(similarity_result)
                
                if similarity_result['flagged']:
                    print(f"⚠️ Flagged: '{phrase_data['text']}' - {similarity_result['similarity_analysis']['risk_level']} risk")
            
            self.analysis_memory[analysis_id]['similarity_results'] = similarity_results
            
            # STEP 3: Risk Assessment Agent - Evaluate overall risk
            print("⚖️ Risk Agent: Assessing overall copyright risk...")
            risk_assessment = assess_copyright_risk(similarity_results)
            
            self.analysis_memory[analysis_id]['risk_assessment'] = risk_assessment
            print(f"📊 Overall Risk Level: {risk_assessment['overall_risk']}")
            
            # STEP 4: Alternative Generation Agent - Create alternatives for flagged content
            alternatives_result = None
            if risk_assessment['flagged_phrases'] > 0:
                print("✍️ Alternatives Agent: Generating creative alternatives...")
                
                flagged_phrases = risk_assessment['flagged_details']
                alternatives_result = generate_alternatives(flagged_phrases, preserve_rhyme=True)
                
                self.analysis_memory[analysis_id]['alternatives'] = alternatives_result
                print(f"💡 Generated alternatives for {alternatives_result['alternatives_generated']} phrases")
            
            # STEP 5: Coordinator Agent - Synthesize final report
            print("🎯 Coordinator Agent: Synthesizing final report...")
            
            coordinator_prompt = f"""
            Synthesize the complete analysis results into a comprehensive report:
            
            PLANNING RESULT: {planning_result}
            SIMILARITY ANALYSIS: Found {len([r for r in similarity_results if r['flagged']])} flagged phrases
            RISK ASSESSMENT: {risk_assessment['overall_risk']} risk level
            ALTERNATIVES: {'Generated' if alternatives_result else 'Not needed'}
            
            Create a final user-friendly report with:
            1. Executive summary of findings
            2. Specific concerns and recommendations
            3. Next steps for the songwriter
            
            Be encouraging but honest about risks. Focus on actionable advice.
            """
            
            final_report = self.coordinator.run_live(coordinator_prompt)
            
            # Complete analysis and measure performance
            analysis_time = time.time() - start_time
            self.analysis_memory[analysis_id]['status'] = 'completed'
            self.analysis_memory[analysis_id]['analysis_time'] = analysis_time
            
            # Prepare final result
            final_result = {
                'analysis_id': analysis_id,
                'overall_risk': risk_assessment['overall_risk'],
                'phrases_analyzed': len(extracted_phrases),
                'flagged_phrases': risk_assessment['flagged_phrases'],
                'similarity_results': similarity_results,
                'risk_assessment': risk_assessment,
                'alternatives': alternatives_result,
                'final_report': final_report,
                'analysis_time': analysis_time,
                'cache_hit': False,
                'agentic_workflow': {
                    'planner_agent': 'Task breakdown and phrase extraction',
                    'similarity_agent': f'Analyzed {len(extracted_phrases)} phrases',
                    'risk_agent': 'Overall risk assessment completed',
                    'alternatives_agent': 'Creative alternatives generated' if alternatives_result else 'No alternatives needed',
                    'coordinator_agent': 'Final report synthesis'
                }
            }
            
            # Cache the result for future use (1 hour TTL)
            cache_analysis_result(lyrics, final_result, user_preferences, ttl=3600)
            print(f"📊 Analysis completed in {analysis_time:.2f} seconds - result cached")
            
            return final_result
            
        except Exception as e:
            self.analysis_memory[analysis_id]['status'] = 'error'
            self.analysis_memory[analysis_id]['error'] = str(e)
            
            return {
                'error': f'Analysis failed: {str(e)}',
                'analysis_id': analysis_id,
                'status': 'error'
            }
    
    def interactive_session(self):
        """
        Start an interactive session for continuous lyric analysis
        """
        print("🎵 LyricLawyer - Copyright Compliance Checker")
        print("Paste your lyrics below and I'll check for potential copyright issues.\n")
        
        while True:
            try:
                print("\n" + "="*60)
                print("Enter your song lyrics (or 'quit' to exit):")
                print("="*60)
                
                # Get multi-line input
                lyrics_lines = []
                while True:
                    line = input()
                    if line.lower() == 'quit':
                        return
                    if line.strip() == '' and lyrics_lines:
                        break
                    lyrics_lines.append(line)
                
                lyrics = '\n'.join(lyrics_lines)
                
                if not lyrics.strip():
                    print("Please enter some lyrics to analyze.")
                    continue
                
                # Analyze lyrics using ADK agent
                print("\n🔍 Analyzing lyrics for copyright compliance...\n")
                result = self.analyze_lyrics(lyrics)
                
                print("📊 ANALYSIS RESULTS:")
                print("-" * 40)
                print(result["agent_response"])
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 🎵")
                break
            except Exception as e:
                print(f"Error during analysis: {e}")
                print("Please try again with different lyrics.")


def create_lyric_lawyer_agent() -> LyricLawyerAgent:
    """Factory function to create and return a LyricLawyer agent instance"""
    return LyricLawyerAgent()


# CLI entry point
if __name__ == "__main__":
    agent = create_lyric_lawyer_agent()
    agent.interactive_session()