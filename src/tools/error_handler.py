"""
Error Handling System

Comprehensive error handling and recovery for the LyricLawyer processing pipeline.
"""

import traceback
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors that can occur"""
    INPUT_VALIDATION = "input_validation"
    API_ERROR = "api_error"
    PROCESSING_ERROR = "processing_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"


class LyricLawyerError(Exception):
    """Base exception for LyricLawyer specific errors"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR, 
                 severity: ErrorSeverity = ErrorSeverity.ERROR, details: Dict = None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class ErrorHandler:
    """
    Centralized error handling and recovery system
    """
    
    def __init__(self):
        self.error_log = []
        self.recovery_strategies = {
            ErrorCategory.API_ERROR: self._handle_api_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorCategory.PROCESSING_ERROR: self._handle_processing_error,
            ErrorCategory.INPUT_VALIDATION: self._handle_validation_error,
            ErrorCategory.MEMORY_ERROR: self._handle_memory_error,
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an error with appropriate recovery strategy
        
        Args:
            error: The exception that occurred
            context: Additional context about where/when the error occurred
            
        Returns:
            Error handling result with recovery actions
        """
        context = context or {}
        
        # Categorize the error
        category = self._categorize_error(error)
        severity = self._assess_severity(error, category)
        
        # Create structured error information
        error_info = {
            'error_id': f"err_{hash(str(error)):.8x}",
            'message': str(error),
            'category': category.value,
            'severity': severity.value,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'traceback': traceback.format_exc() if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL] else None
        }
        
        # Log the error
        self._log_error(error_info)
        
        # Apply recovery strategy
        recovery_result = self._apply_recovery_strategy(category, error, context)
        
        return {
            'error_info': error_info,
            'recovery_result': recovery_result,
            'user_message': self._generate_user_message(error_info, recovery_result),
            'should_retry': recovery_result.get('should_retry', False),
            'fallback_available': recovery_result.get('fallback_available', False)
        }
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize the error based on its type and message"""
        
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # API-related errors
        if 'api' in error_str or 'gemini' in error_str or 'quota' in error_str:
            return ErrorCategory.API_ERROR
        
        # Network errors
        if 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
            if 'timeout' in error_str:
                return ErrorCategory.TIMEOUT_ERROR
            return ErrorCategory.NETWORK_ERROR
        
        # Memory errors
        if 'memory' in error_str or error_type in ['memoryerror', 'outofmemoryerror']:
            return ErrorCategory.MEMORY_ERROR
        
        # Input validation errors
        if 'validation' in error_str or error_type in ['validationerror', 'valueerror']:
            return ErrorCategory.INPUT_VALIDATION
        
        # Processing errors
        if error_type in ['processingerror', 'runtimeerror', 'attributeerror']:
            return ErrorCategory.PROCESSING_ERROR
        
        return ErrorCategory.UNKNOWN_ERROR
    
    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Assess the severity of the error"""
        
        # Critical errors that break the entire system
        if category in [ErrorCategory.MEMORY_ERROR]:
            return ErrorSeverity.CRITICAL
        
        # Errors that prevent processing but don't break the system
        if category in [ErrorCategory.API_ERROR, ErrorCategory.NETWORK_ERROR]:
            return ErrorSeverity.ERROR
        
        # Warnings that might affect quality but don't prevent processing
        if category in [ErrorCategory.TIMEOUT_ERROR, ErrorCategory.PROCESSING_ERROR]:
            return ErrorSeverity.WARNING
        
        # Input validation is usually recoverable
        if category == ErrorCategory.INPUT_VALIDATION:
            return ErrorSeverity.INFO
        
        return ErrorSeverity.ERROR
    
    def _apply_recovery_strategy(self, category: ErrorCategory, error: Exception, context: Dict) -> Dict[str, Any]:
        """Apply appropriate recovery strategy based on error category"""
        
        if category in self.recovery_strategies:
            return self.recovery_strategies[category](error, context)
        
        return {
            'strategy': 'no_recovery',
            'should_retry': False,
            'fallback_available': False,
            'message': 'No specific recovery strategy available'
        }
    
    def _handle_api_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle API-related errors"""
        
        error_str = str(error).lower()
        
        if 'quota' in error_str or 'rate limit' in error_str:
            return {
                'strategy': 'rate_limit_backoff',
                'should_retry': True,
                'retry_delay': 60,
                'fallback_available': True,
                'fallback_strategy': 'use_simplified_analysis',
                'message': 'API rate limit reached. Will retry with backoff or use simplified analysis.'
            }
        
        if 'api key' in error_str or 'authentication' in error_str:
            return {
                'strategy': 'check_configuration',
                'should_retry': False,
                'fallback_available': False, 
                'message': 'API authentication failed. Please check your API key configuration.'
            }
        
        return {
            'strategy': 'api_fallback',
            'should_retry': True,
            'max_retries': 3,
            'fallback_available': True,
            'message': 'API error occurred. Will retry or use fallback analysis.'
        }
    
    def _handle_network_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle network-related errors"""
        
        return {
            'strategy': 'network_retry',
            'should_retry': True,
            'max_retries': 3,
            'retry_delay': 5,
            'fallback_available': True,
            'fallback_strategy': 'offline_analysis',
            'message': 'Network error occurred. Will retry or use offline analysis.'
        }
    
    def _handle_timeout_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle timeout errors"""
        
        return {
            'strategy': 'reduce_scope',
            'should_retry': True,
            'modifications': {
                'reduce_phrase_count': True,
                'increase_timeout': True,
                'simplify_analysis': True
            },
            'fallback_available': True,
            'message': 'Analysis timed out. Will retry with reduced scope.'
        }
    
    def _handle_processing_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle processing errors"""
        
        return {
            'strategy': 'skip_problematic_content',
            'should_retry': True,
            'modifications': {
                'skip_current_phrase': True,
                'continue_with_rest': True
            },
            'fallback_available': True,
            'message': 'Processing error occurred. Will skip problematic content and continue.'
        }
    
    def _handle_validation_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle input validation errors"""
        
        return {
            'strategy': 'user_correction_required',
            'should_retry': False,
            'fallback_available': False,
            'user_action_required': True,
            'suggestions': self._get_validation_suggestions(error),
            'message': 'Input validation failed. Please correct the input and try again.'
        }
    
    def _handle_memory_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle memory errors"""
        
        return {
            'strategy': 'reduce_memory_usage',
            'should_retry': True,
            'modifications': {
                'process_in_chunks': True,
                'reduce_batch_size': True,
                'clear_cache': True
            },
            'fallback_available': True,
            'message': 'Memory limit reached. Will retry with reduced memory usage.'
        }
    
    def _get_validation_suggestions(self, error: Exception) -> List[str]:
        """Generate helpful suggestions for validation errors"""
        
        error_str = str(error).lower()
        suggestions = []
        
        if 'too short' in error_str:
            suggestions.append("Please provide more lyrics text (at least 10 characters)")
        
        if 'too long' in error_str:
            suggestions.append("Please shorten your lyrics (maximum 10,000 characters)")
        
        if 'few words' in error_str:
            suggestions.append("Please provide more meaningful lyric content")
        
        if 'invalid characters' in error_str:
            suggestions.append("Please remove any special characters or code from your lyrics")
        
        if not suggestions:
            suggestions.append("Please check your lyrics format and try again")
        
        return suggestions
    
    def _generate_user_message(self, error_info: Dict, recovery_result: Dict) -> str:
        """Generate a user-friendly error message"""
        
        severity = error_info['severity']
        category = error_info['category']
        
        base_message = recovery_result.get('message', 'An error occurred during processing.')
        
        if severity == 'critical':
            return f"🚨 Critical Error: {base_message} Please try again later or contact support."
        
        elif severity == 'error':
            if recovery_result.get('fallback_available'):
                return f"⚠️ Error: {base_message} We'll try an alternative approach."
            else:
                return f"❌ Error: {base_message}"
        
        elif severity == 'warning':
            return f"⚠️ Warning: {base_message} Processing will continue with limitations."
        
        else:  # info
            return f"ℹ️ Notice: {base_message}"
    
    def _log_error(self, error_info: Dict) -> None:
        """Log error information"""
        
        self.error_log.append(error_info)
        
        # Keep only last 50 errors to prevent memory issues
        if len(self.error_log) > 50:
            self.error_log = self.error_log[-50:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        
        if not self.error_log:
            return {'message': 'No errors logged'}
        
        total_errors = len(self.error_log)
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_log:
            category = error['category']
            severity = error['severity']
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_errors': total_errors,
            'error_categories': category_counts,
            'error_severities': severity_counts,
            'recent_errors': self.error_log[-5:] if len(self.error_log) >= 5 else self.error_log
        }


# Global error handler instance
_error_handler = ErrorHandler()

def handle_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Public function for error handling
    
    Args:
        error: The exception that occurred
        context: Additional context information
        
    Returns:
        Error handling result
    """
    return _error_handler.handle_error(error, context)

def get_error_statistics() -> Dict[str, Any]:
    """Get error statistics"""
    return _error_handler.get_error_statistics()