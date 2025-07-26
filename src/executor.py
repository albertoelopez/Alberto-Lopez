"""
LyricLawyer Executor Module

This module implements the execution layer that orchestrates calls between 
our multi-agent ADK system and external APIs (Gemini). It serves as the 
interface between planning and actual task execution.
"""

import os
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import google.generativeai as genai

from .tools.error_handler import handle_error, ErrorCategory
from .tools.input_validator import validate_lyrics_input


class ExecutionStatus(Enum):
    """Status of task execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(Enum):
    """Types of tasks that can be executed"""
    SANITIZE_LYRICS = "sanitize_lyrics"
    EXTRACT_PHRASES = "extract_phrases"
    ANALYZE_SIMILARITY = "analyze_similarity"
    ASSESS_RISK = "assess_risk"
    GENERATE_ALTERNATIVES = "generate_alternatives"
    COORDINATE_WORKFLOW = "coordinate_workflow"


class ExecutionTask:
    """Represents a single execution task"""
    
    def __init__(self, task_id: str, task_type: TaskType, agent_name: str, 
                 input_data: Dict[str, Any], dependencies: List[str] = None):
        self.task_id = task_id
        self.task_type = task_type
        self.agent_name = agent_name
        self.input_data = input_data
        self.dependencies = dependencies or []
        self.status = ExecutionStatus.PENDING
        self.result = None
        self.error = None
        self.execution_time = 0.0
        self.retry_count = 0
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
    
    def mark_started(self):
        """Mark task as started"""
        self.status = ExecutionStatus.IN_PROGRESS
        self.started_at = time.time()
    
    def mark_completed(self, result: Any):
        """Mark task as completed with result"""
        self.status = ExecutionStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()
        if self.started_at:
            self.execution_time = self.completed_at - self.started_at
    
    def mark_failed(self, error: Exception):
        """Mark task as failed with error"""
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.completed_at = time.time()
        if self.started_at:
            self.execution_time = self.completed_at - self.started_at


class LyricLawyerExecutor:
    """
    Main executor that coordinates task execution across the multi-agent system
    """
    
    def __init__(self, agent_system):
        """
        Initialize executor with reference to the multi-agent system
        
        Args:
            agent_system: The LyricLawyerAgent instance with all sub-agents
        """
        self.agent_system = agent_system
        self.execution_queue = []
        self.completed_tasks = []
        self.execution_context = {}
        self.max_retries = 3
        self.timeout_seconds = 30
        
        # Configure Gemini client
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
    
    def execute_workflow(self, lyrics: str, user_preferences: Dict = None) -> Dict[str, Any]:
        """
        Execute the complete lyric analysis workflow
        
        Args:
            lyrics: Raw lyrics to analyze
            user_preferences: Optional user settings
            
        Returns:
            Complete workflow execution results
        """
        workflow_id = f"workflow_{hash(lyrics[:50])}"
        
        print("🚀 Executor: Starting workflow execution...")
        
        try:
            # Create execution plan
            execution_plan = self._create_execution_plan(lyrics, user_preferences)
            
            # Execute tasks in order
            execution_results = self._execute_plan(execution_plan, workflow_id)
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'execution_results': execution_results,
                'execution_summary': self._generate_execution_summary()
            }
            
        except Exception as e:
            error_result = handle_error(e, {'context': 'workflow_execution', 'lyrics_length': len(lyrics)})
            
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': error_result,
                'partial_results': self._get_partial_results()
            }
    
    def _create_execution_plan(self, lyrics: str, user_preferences: Dict) -> List[ExecutionTask]:
        """Create ordered execution plan for the workflow"""
        
        plan = []
        
        # Task 1: Input Validation & Sanitization
        plan.append(ExecutionTask(
            task_id="task_1_sanitize",
            task_type=TaskType.SANITIZE_LYRICS,
            agent_name="planner_agent",
            input_data={'lyrics': lyrics, 'user_preferences': user_preferences}
        ))
        
        # Task 2: Phrase Extraction
        plan.append(ExecutionTask(
            task_id="task_2_extract", 
            task_type=TaskType.EXTRACT_PHRASES,
            agent_name="planner_agent",
            input_data={'source': 'sanitized_lyrics'},
            dependencies=["task_1_sanitize"]
        ))
        
        # Task 3: Similarity Analysis
        plan.append(ExecutionTask(
            task_id="task_3_similarity",
            task_type=TaskType.ANALYZE_SIMILARITY,
            agent_name="similarity_agent", 
            input_data={'source': 'extracted_phrases'},
            dependencies=["task_2_extract"]
        ))
        
        # Task 4: Risk Assessment
        plan.append(ExecutionTask(
            task_id="task_4_risk",
            task_type=TaskType.ASSESS_RISK,
            agent_name="risk_agent",
            input_data={'source': 'similarity_results'},
            dependencies=["task_3_similarity"]
        ))
        
        # Task 5: Alternative Generation (conditional)
        plan.append(ExecutionTask(
            task_id="task_5_alternatives",
            task_type=TaskType.GENERATE_ALTERNATIVES,
            agent_name="alternatives_agent",
            input_data={'source': 'risk_assessment', 'condition': 'if_high_risk'},
            dependencies=["task_4_risk"]
        ))
        
        # Task 6: Final Coordination
        plan.append(ExecutionTask(
            task_id="task_6_coordinate",
            task_type=TaskType.COORDINATE_WORKFLOW,
            agent_name="coordinator",
            input_data={'source': 'all_results'},
            dependencies=["task_5_alternatives"]
        ))
        
        return plan
    
    def _execute_plan(self, plan: List[ExecutionTask], workflow_id: str) -> Dict[str, Any]:
        """Execute the planned tasks in dependency order"""
        
        results = {}
        
        for task in plan:
            try:
                # Check dependencies
                if not self._dependencies_satisfied(task, results):
                    print(f"⏳ Waiting for dependencies: {task.task_id}")
                    continue
                
                # Execute the task
                print(f"⚡ Executing: {task.task_id} ({task.task_type.value})")
                task.mark_started()
                
                result = self._execute_single_task(task, results)
                
                task.mark_completed(result)
                results[task.task_id] = result
                
                print(f"✅ Completed: {task.task_id} ({task.execution_time:.1f}s)")
                
            except Exception as e:
                task.mark_failed(e)
                
                # Handle error and decide whether to continue
                error_result = handle_error(e, {
                    'task_id': task.task_id,
                    'task_type': task.task_type.value,
                    'workflow_id': workflow_id
                })
                
                if error_result['recovery_result'].get('should_retry') and task.retry_count < self.max_retries:
                    print(f"🔄 Retrying: {task.task_id} (attempt {task.retry_count + 1})")
                    task.retry_count += 1
                    task.status = ExecutionStatus.PENDING
                    continue
                
                # If critical task fails and no recovery, fail workflow
                if task.task_type in [TaskType.SANITIZE_LYRICS, TaskType.COORDINATE_WORKFLOW]:
                    raise e
                
                # Otherwise skip non-critical tasks
                print(f"⏭️ Skipping: {task.task_id} due to error")
                task.status = ExecutionStatus.SKIPPED
                results[task.task_id] = {'error': str(e), 'skipped': True}
        
        return results
    
    def _execute_single_task(self, task: ExecutionTask, previous_results: Dict) -> Any:
        """Execute a single task using the appropriate agent"""
        
        # Get the appropriate agent
        agent = self._get_agent_for_task(task)
        
        # Prepare input data based on dependencies
        input_data = self._prepare_task_input(task, previous_results)
        
        # Execute based on task type
        if task.task_type == TaskType.SANITIZE_LYRICS:
            return self._execute_sanitization(input_data)
        
        elif task.task_type == TaskType.EXTRACT_PHRASES:
            return self._execute_phrase_extraction(input_data)
        
        elif task.task_type == TaskType.ANALYZE_SIMILARITY:
            return self._execute_similarity_analysis(agent, input_data)
        
        elif task.task_type == TaskType.ASSESS_RISK:
            return self._execute_risk_assessment(agent, input_data)
        
        elif task.task_type == TaskType.GENERATE_ALTERNATIVES:
            return self._execute_alternative_generation(agent, input_data)
        
        elif task.task_type == TaskType.COORDINATE_WORKFLOW:
            return self._execute_coordination(agent, input_data)
        
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    def _get_agent_for_task(self, task: ExecutionTask):
        """Get the appropriate ADK agent for the task"""
        
        agent_mapping = {
            'planner_agent': self.agent_system.planner_agent,
            'similarity_agent': self.agent_system.similarity_agent,
            'risk_agent': self.agent_system.risk_agent,
            'alternatives_agent': self.agent_system.alternatives_agent,
            'coordinator': self.agent_system.coordinator
        }
        
        return agent_mapping.get(task.agent_name)
    
    def _prepare_task_input(self, task: ExecutionTask, previous_results: Dict) -> Dict[str, Any]:
        """Prepare input data for task execution"""
        
        input_data = task.input_data.copy()
        
        # Resolve data dependencies
        for key, value in input_data.items():
            if isinstance(value, str) and value.startswith('$'):
                # Reference to previous result
                result_key = value[1:]  # Remove $
                if result_key in previous_results:
                    input_data[key] = previous_results[result_key]
        
        return input_data
    
    def _execute_sanitization(self, input_data: Dict) -> Dict[str, Any]:
        """Execute lyrics sanitization"""
        from .tools.lyric_analyzer import sanitize_lyrics
        
        lyrics = input_data['lyrics']
        return sanitize_lyrics(lyrics)
    
    def _execute_phrase_extraction(self, input_data: Dict) -> List[Dict[str, Any]]:
        """Execute phrase extraction"""
        from .tools.lyric_analyzer import extract_phrases
        
        sanitized_lyrics = input_data.get('sanitized_lyrics', '')
        return extract_phrases(sanitized_lyrics)
    
    def _execute_similarity_analysis(self, agent, input_data: Dict) -> List[Dict[str, Any]]:
        """Execute similarity analysis using the similarity agent"""
        
        phrases = input_data.get('phrases', [])
        results = []
        
        for phrase_data in phrases[:10]:  # Limit for demo
            # Use the similarity agent to analyze
            analysis_prompt = f"""
            Analyze this lyric phrase for copyright similarity: "{phrase_data['text']}"
            
            Provide similarity score and any potential matches to known songs.
            """
            
            agent_response = agent.run(analysis_prompt)
            
            results.append({
                'phrase': phrase_data,
                'similarity_analysis': agent_response,
                'flagged': 'high' in agent_response.lower() or 'critical' in agent_response.lower()
            })
        
        return results
    
    def _execute_risk_assessment(self, agent, input_data: Dict) -> Dict[str, Any]:
        """Execute risk assessment using the risk agent"""
        
        similarity_results = input_data.get('similarity_results', [])
        
        risk_prompt = f"""
        Assess the overall copyright risk based on these similarity analysis results:
        
        Total phrases analyzed: {len(similarity_results)}
        Flagged phrases: {len([r for r in similarity_results if r.get('flagged')])}
        
        Provide overall risk level and recommendations.
        """
        
        risk_response = agent.run(risk_prompt)
        
        return {
            'overall_risk': 'MEDIUM',  # Would be parsed from response
            'flagged_phrases': len([r for r in similarity_results if r.get('flagged')]),
            'assessment': risk_response,
            'similarity_results': similarity_results
        }
    
    def _execute_alternative_generation(self, agent, input_data: Dict) -> Dict[str, Any]:
        """Execute alternative generation using the alternatives agent"""
        
        risk_assessment = input_data.get('risk_assessment', {})
        
        if risk_assessment.get('flagged_phrases', 0) == 0:
            return {
                'alternatives_generated': 0,
                'message': 'No alternatives needed - low risk detected'
            }
        
        alternatives_prompt = f"""
        Generate creative alternatives for the flagged phrases from this risk assessment:
        
        {risk_assessment.get('assessment', '')}
        
        Provide original alternatives that maintain artistic intent.
        """
        
        alternatives_response = agent.run(alternatives_prompt)
        
        return {
            'alternatives_generated': risk_assessment.get('flagged_phrases', 0),
            'alternatives': alternatives_response
        }
    
    def _execute_coordination(self, agent, input_data: Dict) -> str:
        """Execute final coordination using the coordinator agent"""
        
        coordination_prompt = """
        Synthesize all analysis results into a comprehensive final report for the user.
        Include overall risk assessment, specific concerns, and actionable recommendations.
        """
        
        return agent.run(coordination_prompt)
    
    def _dependencies_satisfied(self, task: ExecutionTask, results: Dict) -> bool:
        """Check if task dependencies are satisfied"""
        
        for dep_id in task.dependencies:
            if dep_id not in results:
                return False
        
        return True
    
    def _generate_execution_summary(self) -> Dict[str, Any]:
        """Generate execution summary"""
        
        completed = len([t for t in self.completed_tasks if t.status == ExecutionStatus.COMPLETED])
        failed = len([t for t in self.completed_tasks if t.status == ExecutionStatus.FAILED])
        skipped = len([t for t in self.completed_tasks if t.status == ExecutionStatus.SKIPPED])
        
        total_time = sum(t.execution_time for t in self.completed_tasks)
        
        return {
            'total_tasks': len(self.completed_tasks),
            'completed': completed,
            'failed': failed,
            'skipped': skipped,
            'total_execution_time': round(total_time, 2),
            'success_rate': round(completed / len(self.completed_tasks) * 100, 1) if self.completed_tasks else 0
        }
    
    def _get_partial_results(self) -> Dict[str, Any]:
        """Get partial results when workflow fails"""
        
        return {
            'completed_tasks': [t.task_id for t in self.completed_tasks if t.status == ExecutionStatus.COMPLETED],
            'failed_tasks': [t.task_id for t in self.completed_tasks if t.status == ExecutionStatus.FAILED],
            'last_error': str(self.completed_tasks[-1].error) if self.completed_tasks and self.completed_tasks[-1].error else None
        }


def create_executor(agent_system) -> LyricLawyerExecutor:
    """
    Factory function to create executor instance
    
    Args:
        agent_system: The multi-agent system instance
        
    Returns:
        Configured executor instance
    """
    return LyricLawyerExecutor(agent_system)