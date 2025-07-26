"""
Agentic Workflow Orchestrator

This module provides enhanced orchestration of the multi-agent workflow
with detailed logging, progress tracking, and tight integration between
planner, executor, and memory components.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from .memory import get_memory_system, MemoryType, MemoryScope
from .executor import LyricLawyerExecutor
from .tools.error_handler import handle_error


class WorkflowStatus(Enum):
    """Workflow execution status"""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    EXECUTING = "executing"
    COORDINATING = "coordinating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Individual task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class WorkflowTask:
    """Individual workflow task with enhanced tracking"""
    task_id: str
    task_name: str
    agent_name: str
    description: str
    status: TaskStatus
    progress_percentage: float
    start_time: Optional[float]
    end_time: Optional[float]
    execution_time: float
    result: Optional[Any]
    error: Optional[str]
    retry_count: int
    dependencies: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not hasattr(self, 'created_at'):
            self.created_at = time.time()
    
    def mark_started(self):
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = time.time()
        self.progress_percentage = 0.0
    
    def update_progress(self, percentage: float, message: str = ""):
        """Update task progress"""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        if message:
            self.metadata['progress_message'] = message
            self.metadata['last_update'] = time.time()
    
    def mark_completed(self, result: Any):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.end_time = time.time()
        self.result = result
        self.progress_percentage = 100.0
        if self.start_time:
            self.execution_time = self.end_time - self.start_time


@dataclass 
class WorkflowExecution:
    """Complete workflow execution context"""
    workflow_id: str
    status: WorkflowStatus
    start_time: float
    end_time: Optional[float]
    execution_time: float
    tasks: List[WorkflowTask]
    current_task_index: int
    progress_percentage: float
    error: Optional[str]
    result: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = time.time()


class ProgressTracker:
    """Progress tracking for workflow execution"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.callbacks: List[Callable] = []
        self.progress_history: List[Dict[str, Any]] = []
    
    def add_callback(self, callback: Callable[[str, float, str], None]):
        """Add progress callback function"""
        self.callbacks.append(callback)
    
    def update_progress(self, task_name: str, percentage: float, message: str = ""):
        """Update progress and notify callbacks"""
        progress_data = {
            'timestamp': time.time(),
            'task_name': task_name,
            'percentage': percentage,
            'message': message
        }
        
        self.progress_history.append(progress_data)
        
        # Notify all callbacks
        for callback in self.callbacks:
            try:
                callback(task_name, percentage, message)
            except Exception as e:
                logging.warning(f"Progress callback failed: {e}")
    
    def get_overall_progress(self) -> float:
        """Calculate overall workflow progress"""
        if not self.progress_history:
            return 0.0
        
        # Simple average of all task progress
        total_progress = sum(p['percentage'] for p in self.progress_history)
        return total_progress / len(self.progress_history)


class WorkflowLogger:
    """Enhanced logging for workflow execution"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.logger = logging.getLogger(f"workflow.{workflow_id}")
        self.setup_logging()
        self.log_entries: List[Dict[str, Any]] = []
    
    def setup_logging(self):
        """Setup logging configuration"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log(self, level: str, message: str, extra_data: Dict[str, Any] = None):
        """Log workflow event"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'workflow_id': self.workflow_id,
            'extra_data': extra_data or {}
        }
        
        self.log_entries.append(log_entry)
        
        # Log to standard logger
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(f"[{self.workflow_id}] {message}")
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log('INFO', message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log('WARNING', message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log('ERROR', message, kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log('DEBUG', message, kwargs)
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all log entries"""
        return self.log_entries.copy()


class AgenticWorkflowOrchestrator:
    """
    Enhanced orchestrator for the complete agentic workflow
    """
    
    def __init__(self, agent_system):
        self.agent_system = agent_system
        self.memory_system = get_memory_system()
        self.executor = LyricLawyerExecutor(agent_system)
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("orchestrator")
    
    def execute_lyric_analysis_workflow(self, lyrics: str, user_preferences: Dict = None, 
                                      progress_callback: Callable = None) -> Dict[str, Any]:
        """
        Execute the complete lyric analysis workflow with enhanced tracking
        
        Args:
            lyrics: Lyrics to analyze
            user_preferences: User settings
            progress_callback: Optional progress callback function
            
        Returns:
            Complete workflow results with tracking data
        """
        # Initialize workflow
        workflow_id = str(uuid.uuid4())[:8]
        workflow = self._initialize_workflow(workflow_id, lyrics, user_preferences)
        
        # Setup progress tracking
        progress_tracker = ProgressTracker(workflow_id)
        if progress_callback:
            progress_tracker.add_callback(progress_callback)
        
        # Setup logging
        workflow_logger = WorkflowLogger(workflow_id)
        workflow_logger.info("Starting lyric analysis workflow", {
            'lyrics_length': len(lyrics),
            'user_preferences': user_preferences
        })
        
        try:
            # Store workflow context in memory
            self._store_workflow_context(workflow, workflow_logger)
            
            # Execute workflow phases
            results = self._execute_workflow_phases(
                workflow, progress_tracker, workflow_logger
            )
            
            # Mark workflow as completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.end_time = time.time()
            workflow.execution_time = workflow.end_time - workflow.start_time
            workflow.result = results
            
            workflow_logger.info("Workflow completed successfully", {
                'execution_time': workflow.execution_time,
                'total_tasks': len(workflow.tasks)
            })
            
            # Store final results in memory
            analysis_id = self.memory_system.store_analysis_result(lyrics, results)
            
            return {
                'workflow_id': workflow_id,
                'analysis_id': analysis_id,
                'status': 'completed',
                'execution_time': workflow.execution_time,
                'results': results,
                'workflow_tracking': {
                    'tasks_completed': len([t for t in workflow.tasks if t.status == TaskStatus.COMPLETED]),
                    'total_tasks': len(workflow.tasks),
                    'overall_progress': progress_tracker.get_overall_progress(),
                    'progress_history': progress_tracker.progress_history
                },
                'logs': workflow_logger.get_logs()
            }
            
        except Exception as e:
            # Handle workflow failure
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.end_time = time.time()
            workflow.execution_time = workflow.end_time - workflow.start_time
            
            workflow_logger.error("Workflow failed", {
                'error': str(e),
                'execution_time': workflow.execution_time
            })
            
            error_result = handle_error(e, {
                'context': 'workflow_orchestration',
                'workflow_id': workflow_id
            })
            
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': error_result,
                'execution_time': workflow.execution_time,
                'partial_results': self._get_partial_results(workflow),
                'logs': workflow_logger.get_logs()
            }
    
    def _initialize_workflow(self, workflow_id: str, lyrics: str, user_preferences: Dict) -> WorkflowExecution:
        """Initialize workflow execution context"""
        
        # Define workflow tasks
        tasks = [
            WorkflowTask(
                task_id=f"{workflow_id}_planning",
                task_name="Planning & Analysis Preparation",
                agent_name="planner_agent",
                description="Break down lyrics analysis into systematic tasks",
                status=TaskStatus.PENDING,
                progress_percentage=0.0,
                start_time=None,
                end_time=None,
                execution_time=0.0,
                result=None,
                error=None,
                retry_count=0,
                dependencies=[],
                metadata={'phase': 'planning'}
            ),
            WorkflowTask(
                task_id=f"{workflow_id}_similarity",
                task_name="Similarity Analysis",
                agent_name="similarity_agent",
                description="Analyze phrases for copyright similarities",
                status=TaskStatus.PENDING,
                progress_percentage=0.0,
                start_time=None,
                end_time=None,
                execution_time=0.0,
                result=None,
                error=None,
                retry_count=0,
                dependencies=[f"{workflow_id}_planning"],
                metadata={'phase': 'analysis'}
            ),
            WorkflowTask(
                task_id=f"{workflow_id}_risk_assessment",
                task_name="Risk Assessment",
                agent_name="risk_agent",
                description="Evaluate overall copyright risk",
                status=TaskStatus.PENDING,
                progress_percentage=0.0,
                start_time=None,
                end_time=None,
                execution_time=0.0,
                result=None,
                error=None,
                retry_count=0,
                dependencies=[f"{workflow_id}_similarity"],
                metadata={'phase': 'assessment'}
            ),
            WorkflowTask(
                task_id=f"{workflow_id}_alternatives",
                task_name="Alternative Generation",
                agent_name="alternatives_agent",
                description="Generate creative alternatives for flagged content",
                status=TaskStatus.PENDING,
                progress_percentage=0.0,
                start_time=None,
                end_time=None,
                execution_time=0.0,
                result=None,
                error=None,
                retry_count=0,
                dependencies=[f"{workflow_id}_risk_assessment"],
                metadata={'phase': 'generation'}
            ),
            WorkflowTask(
                task_id=f"{workflow_id}_coordination",
                task_name="Final Coordination",
                agent_name="coordinator",
                description="Synthesize results into comprehensive report",
                status=TaskStatus.PENDING,
                progress_percentage=0.0,
                start_time=None,
                end_time=None,
                execution_time=0.0,
                result=None,
                error=None,
                retry_count=0,
                dependencies=[f"{workflow_id}_alternatives"],
                metadata={'phase': 'coordination'}
            )
        ]
        
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            status=WorkflowStatus.INITIALIZED,
            start_time=time.time(),
            end_time=None,
            execution_time=0.0,
            tasks=tasks,
            current_task_index=0,
            progress_percentage=0.0,
            error=None,
            result=None,
            metadata={
                'lyrics': lyrics,
                'user_preferences': user_preferences,
                'total_tasks': len(tasks)
            }
        )
        
        self.active_workflows[workflow_id] = workflow
        return workflow
    
    def _execute_workflow_phases(self, workflow: WorkflowExecution, 
                                progress_tracker: ProgressTracker,
                                workflow_logger: WorkflowLogger) -> Dict[str, Any]:
        """Execute all workflow phases with tracking"""
        
        workflow.status = WorkflowStatus.EXECUTING
        results = {}
        
        # Execute tasks in dependency order
        for i, task in enumerate(workflow.tasks):
            workflow.current_task_index = i
            
            # Check dependencies
            if not self._dependencies_satisfied(task, results):
                workflow_logger.warning(f"Skipping {task.task_name} - dependencies not satisfied")
                task.status = TaskStatus.SKIPPED
                continue
            
            # Execute task
            workflow_logger.info(f"Starting task: {task.task_name}")
            task.mark_started()
            
            progress_tracker.update_progress(
                task.task_name, 
                0.0, 
                f"Starting {task.task_name}"
            )
            
            try:
                # Execute based on task type
                if task.metadata['phase'] == 'planning':
                    result = self._execute_planning_phase(
                        workflow, task, progress_tracker, workflow_logger
                    )
                elif task.metadata['phase'] == 'analysis':
                    result = self._execute_analysis_phase(
                        workflow, task, progress_tracker, workflow_logger, results
                    )
                elif task.metadata['phase'] == 'assessment':
                    result = self._execute_assessment_phase(
                        workflow, task, progress_tracker, workflow_logger, results
                    )
                elif task.metadata['phase'] == 'generation':
                    result = self._execute_generation_phase(
                        workflow, task, progress_tracker, workflow_logger, results
                    )
                elif task.metadata['phase'] == 'coordination':
                    result = self._execute_coordination_phase(
                        workflow, task, progress_tracker, workflow_logger, results
                    )
                else:
                    raise ValueError(f"Unknown task phase: {task.metadata['phase']}")
                
                # Mark task completed
                task.mark_completed(result)
                results[task.task_id] = result
                
                progress_tracker.update_progress(
                    task.task_name, 
                    100.0, 
                    f"Completed {task.task_name}"
                )
                
                workflow_logger.info(f"Completed task: {task.task_name}", {
                    'execution_time': task.execution_time
                })
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.end_time = time.time()
                if task.start_time:
                    task.execution_time = task.end_time - task.start_time
                
                workflow_logger.error(f"Task failed: {task.task_name}", {
                    'error': str(e),
                    'execution_time': task.execution_time
                })
                
                # Decide whether to continue or fail workflow
                if task.metadata['phase'] in ['planning', 'coordination']:
                    # Critical tasks - fail workflow
                    raise e
                else:
                    # Non-critical tasks - continue with warning
                    results[task.task_id] = {'error': str(e), 'skipped': True}
        
        # Calculate overall progress
        workflow.progress_percentage = progress_tracker.get_overall_progress()
        
        return self._compile_final_results(results, workflow_logger)
    
    def _execute_planning_phase(self, workflow: WorkflowExecution, task: WorkflowTask,
                               progress_tracker: ProgressTracker, workflow_logger: WorkflowLogger) -> Dict[str, Any]:
        """Execute planning phase"""
        
        from .tools.lyric_analyzer import sanitize_lyrics, extract_phrases
        
        lyrics = workflow.metadata['lyrics']
        
        # Step 1: Sanitize lyrics
        progress_tracker.update_progress(task.task_name, 25.0, "Sanitizing lyrics")
        sanitization_result = sanitize_lyrics(lyrics)
        
        if not sanitization_result['success']:
            raise ValueError(f"Lyrics validation failed: {sanitization_result['error_message']}")
        
        # Step 2: Extract phrases
        progress_tracker.update_progress(task.task_name, 50.0, "Extracting phrases")
        phrases = extract_phrases(sanitization_result['sanitized_lyrics'])
        
        # Step 3: Prioritize phrases
        progress_tracker.update_progress(task.task_name, 75.0, "Prioritizing analysis")
        
        # Use planner agent for intelligent prioritization
        planning_prompt = f"""
        Plan the analysis for these {len(phrases)} extracted phrases:
        
        Phrases: {[p['text'] for p in phrases[:10]]}...
        
        Prioritize phrases for copyright analysis and create an execution strategy.
        """
        
        planning_response = self.agent_system.planner_agent.run(planning_prompt)
        
        return {
            'sanitized_lyrics': sanitization_result['sanitized_lyrics'],
            'extracted_phrases': phrases,
            'planning_response': planning_response,
            'phrases_count': len(phrases),
            'validation_warnings': sanitization_result['processing_metadata']['warnings']
        }
    
    def _execute_analysis_phase(self, workflow: WorkflowExecution, task: WorkflowTask,
                               progress_tracker: ProgressTracker, workflow_logger: WorkflowLogger,
                               previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute similarity analysis phase"""
        
        from .tools.lyric_analyzer import analyze_similarity
        
        planning_result = previous_results[f"{workflow.workflow_id}_planning"]
        phrases = planning_result['extracted_phrases']
        
        similarity_results = []
        
        # Analyze phrases with progress tracking
        for i, phrase_data in enumerate(phrases[:10]):  # Limit for demo
            progress = (i / min(10, len(phrases))) * 100
            progress_tracker.update_progress(
                task.task_name, 
                progress, 
                f"Analyzing phrase {i+1}/10: '{phrase_data['text'][:30]}...'"
            )
            
            result = analyze_similarity(phrase_data)
            similarity_results.append(result)
            
            if result['flagged']:
                workflow_logger.info(f"Flagged phrase detected", {
                    'phrase': phrase_data['text'],
                    'risk_level': result['similarity_analysis']['risk_level']
                })
        
        return {
            'similarity_results': similarity_results,
            'total_analyzed': len(similarity_results),
            'flagged_count': len([r for r in similarity_results if r['flagged']])
        }
    
    def _execute_assessment_phase(self, workflow: WorkflowExecution, task: WorkflowTask,
                                 progress_tracker: ProgressTracker, workflow_logger: WorkflowLogger,
                                 previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk assessment phase"""
        
        from .tools.risk_assessor import assess_copyright_risk
        
        analysis_result = previous_results[f"{workflow.workflow_id}_similarity"]
        similarity_results = analysis_result['similarity_results']
        
        progress_tracker.update_progress(task.task_name, 50.0, "Assessing copyright risk")
        
        risk_assessment = assess_copyright_risk(similarity_results)
        
        workflow_logger.info("Risk assessment completed", {
            'overall_risk': risk_assessment['overall_risk'],
            'flagged_phrases': risk_assessment['flagged_phrases']
        })
        
        return risk_assessment
    
    def _execute_generation_phase(self, workflow: WorkflowExecution, task: WorkflowTask,
                                 progress_tracker: ProgressTracker, workflow_logger: WorkflowLogger,
                                 previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute alternative generation phase"""
        
        from .tools.alternative_generator import generate_alternatives
        
        risk_result = previous_results[f"{workflow.workflow_id}_risk_assessment"]
        
        if risk_result['flagged_phrases'] == 0:
            progress_tracker.update_progress(task.task_name, 100.0, "No alternatives needed")
            return {
                'alternatives_generated': 0,
                'message': 'No high-risk phrases detected - no alternatives needed'
            }
        
        progress_tracker.update_progress(task.task_name, 50.0, "Generating alternatives")
        
        flagged_phrases = risk_result['flagged_details']
        alternatives_result = generate_alternatives(flagged_phrases, preserve_rhyme=True)
        
        workflow_logger.info("Alternatives generated", {
            'alternatives_count': alternatives_result['alternatives_generated']
        })
        
        return alternatives_result
    
    def _execute_coordination_phase(self, workflow: WorkflowExecution, task: WorkflowTask,
                                   progress_tracker: ProgressTracker, workflow_logger: WorkflowLogger,
                                   previous_results: Dict[str, Any]) -> str:
        """Execute final coordination phase"""
        
        progress_tracker.update_progress(task.task_name, 50.0, "Synthesizing final report")
        
        # Gather all results for coordination
        planning_result = previous_results.get(f"{workflow.workflow_id}_planning", {})
        analysis_result = previous_results.get(f"{workflow.workflow_id}_similarity", {})
        risk_result = previous_results.get(f"{workflow.workflow_id}_risk_assessment", {})
        alternatives_result = previous_results.get(f"{workflow.workflow_id}_alternatives", {})
        
        coordination_prompt = f"""
        Synthesize this complete lyric analysis into a comprehensive final report:
        
        ANALYSIS SUMMARY:
        - Phrases analyzed: {analysis_result.get('total_analyzed', 0)}
        - Flagged phrases: {risk_result.get('flagged_phrases', 0)}
        - Overall risk: {risk_result.get('overall_risk', 'UNKNOWN')}
        - Alternatives generated: {alternatives_result.get('alternatives_generated', 0)}
        
        Create a user-friendly report with:
        1. Executive summary of findings
        2. Specific concerns and recommendations
        3. Next steps for the songwriter
        
        Be encouraging but honest about risks. Focus on actionable advice.
        """
        
        final_report = self.agent_system.coordinator.run(coordination_prompt)
        
        workflow_logger.info("Final report generated", {
            'report_length': len(final_report)
        })
        
        return final_report
    
    def _compile_final_results(self, results: Dict[str, Any], workflow_logger: WorkflowLogger) -> Dict[str, Any]:
        """Compile all results into final output"""
        
        # Extract key results
        planning_result = results.get(f"{list(results.keys())[0].split('_')[0]}_planning", {})
        analysis_result = results.get(f"{list(results.keys())[0].split('_')[0]}_similarity", {})
        risk_result = results.get(f"{list(results.keys())[0].split('_')[0]}_risk_assessment", {})
        alternatives_result = results.get(f"{list(results.keys())[0].split('_')[0]}_alternatives", {})
        final_report = results.get(f"{list(results.keys())[0].split('_')[0]}_coordination", "Analysis completed.")
        
        compiled_results = {
            'overall_risk': risk_result.get('overall_risk', 'LOW'),
            'phrases_analyzed': analysis_result.get('total_analyzed', 0),
            'flagged_phrases': risk_result.get('flagged_phrases', 0),
            'similarity_results': analysis_result.get('similarity_results', []),
            'risk_assessment': risk_result,
            'alternatives': alternatives_result,
            'final_report': final_report,
            'agentic_workflow': {
                'planner_agent': f"Analyzed {planning_result.get('phrases_count', 0)} phrases",
                'similarity_agent': f"Checked {analysis_result.get('total_analyzed', 0)} phrases",
                'risk_agent': f"Risk assessment: {risk_result.get('overall_risk', 'UNKNOWN')}",
                'alternatives_agent': f"Generated {alternatives_result.get('alternatives_generated', 0)} alternatives",
                'coordinator_agent': 'Final report synthesis completed'
            }
        }
        
        workflow_logger.info("Results compiled successfully", {
            'total_components': len(compiled_results)
        })
        
        return compiled_results
    
    def _dependencies_satisfied(self, task: WorkflowTask, results: Dict[str, Any]) -> bool:
        """Check if task dependencies are satisfied"""
        return all(dep_id in results for dep_id in task.dependencies)
    
    def _store_workflow_context(self, workflow: WorkflowExecution, workflow_logger: WorkflowLogger):
        """Store workflow context in memory"""
        
        context_data = {
            'workflow_id': workflow.workflow_id,
            'status': workflow.status.value,
            'tasks': [asdict(task) for task in workflow.tasks],
            'metadata': workflow.metadata
        }
        
        self.memory_system.store(
            key=f"workflow_context_{workflow.workflow_id}",
            value=context_data,
            memory_type=MemoryType.SESSION,
            scope=MemoryScope.TEMPORARY,
            ttl=3600  # 1 hour
        )
        
        workflow_logger.debug("Workflow context stored in memory")
    
    def _get_partial_results(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Get partial results when workflow fails"""
        
        completed_tasks = [t for t in workflow.tasks if t.status == TaskStatus.COMPLETED]
        
        return {
            'completed_tasks': [t.task_name for t in completed_tasks],
            'failed_tasks': [t.task_name for t in workflow.tasks if t.status == TaskStatus.FAILED],
            'workflow_progress': workflow.progress_percentage,
            'execution_time': workflow.execution_time
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        
        if workflow_id not in self.active_workflows:
            return None
        
        workflow = self.active_workflows[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'status': workflow.status.value,
            'progress_percentage': workflow.progress_percentage,
            'current_task': workflow.tasks[workflow.current_task_index].task_name if workflow.current_task_index < len(workflow.tasks) else None,
            'completed_tasks': len([t for t in workflow.tasks if t.status == TaskStatus.COMPLETED]),
            'total_tasks': len(workflow.tasks),
            'execution_time': workflow.execution_time
        }


def create_workflow_orchestrator(agent_system) -> AgenticWorkflowOrchestrator:
    """Factory function to create orchestrator"""
    return AgenticWorkflowOrchestrator(agent_system)