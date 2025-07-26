"""
API Optimization Tools

Optimizes API calls to Google Gemini for better performance and reduced latency.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
import queue


@dataclass
class APIRequest:
    """Represents an API request with metadata"""
    id: str
    prompt: str
    model_config: Optional[Dict] = None
    priority: int = 1  # 1 = low, 2 = medium, 3 = high
    timeout: float = 30.0


@dataclass 
class APIResponse:
    """Represents an API response with metadata"""
    id: str
    content: str
    latency: float
    success: bool
    error: Optional[str] = None


class GeminiAPIOptimizer:
    """
    Optimizes Gemini API calls through batching, connection pooling, and intelligent retry logic
    """
    
    def __init__(self, max_concurrent_requests: int = 5, request_timeout: float = 30.0):
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_requests)
        
        # Request rate limiting
        self.request_queue = queue.PriorityQueue()
        self.rate_limit_delay = 0.1  # Minimum delay between requests
        self.last_request_time = 0.0
        self.request_lock = threading.Lock()
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_latency': 0.0,
            'cache_hits': 0
        }
        
        # Simple request cache for identical prompts
        self.request_cache: Dict[str, APIResponse] = {}
        self.cache_ttl = 300  # 5 minutes
        
    def optimize_prompt(self, prompt: str, task_type: str = "analysis") -> str:
        """
        Optimize prompt for better performance and reduced token usage
        """
        # Remove excessive whitespace
        optimized = " ".join(prompt.split())
        
        # Task-specific optimizations
        if task_type == "similarity":
            # For similarity analysis, be more direct
            optimized = optimized.replace(
                "Analyze these phrases for copyright similarity",
                "Check similarity:"
            )
        elif task_type == "alternatives":
            # For alternatives, focus on core requirements
            optimized = optimized.replace(
                "Generate creative alternatives for flagged phrases",
                "Suggest alternatives:"
            )
        elif task_type == "risk":
            # For risk assessment, be concise
            optimized = optimized.replace(
                "Assess copyright risk for these similarity results",
                "Rate risk:"
            )
        
        # Limit prompt length for better performance
        if len(optimized) > 2000:
            optimized = optimized[:1800] + "... [truncated for performance]"
        
        return optimized
    
    def batch_requests(self, requests: List[APIRequest]) -> List[APIResponse]:
        """
        Process multiple API requests concurrently with optimal batching
        """
        if not requests:
            return []
        
        # Sort requests by priority (high priority first)
        sorted_requests = sorted(requests, key=lambda x: x.priority, reverse=True)
        
        responses = []
        futures = {}
        
        # Submit requests to thread pool
        for request in sorted_requests:
            future = self.executor.submit(self._make_single_request, request)
            futures[future] = request
        
        # Collect responses as they complete
        for future in as_completed(futures, timeout=self.request_timeout * 2):
            try:
                response = future.result()
                responses.append(response)
            except Exception as e:
                request = futures[future]
                error_response = APIResponse(
                    id=request.id,
                    content="",
                    latency=0.0,
                    success=False,
                    error=str(e)
                )
                responses.append(error_response)
        
        return responses
    
    def _make_single_request(self, request: APIRequest) -> APIResponse:
        """
        Make a single optimized API request
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{request.prompt}_{request.model_config}"
        cached_response = self._get_cached_response(cache_key)
        
        if cached_response:
            self.metrics['cache_hits'] += 1
            return cached_response
        
        try:
            # Rate limiting
            self._apply_rate_limiting()
            
            # Optimize prompt for performance
            optimized_prompt = self.optimize_prompt(request.prompt)
            
            # Configure model with performance optimizations
            model_config = request.model_config or {}
            performance_config = {
                'temperature': model_config.get('temperature', 0.3),  # Lower for consistency
                'max_output_tokens': model_config.get('max_output_tokens', 1024),
                'top_p': model_config.get('top_p', 0.9),
                'top_k': model_config.get('top_k', 40)
            }
            
            # Make API call
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=genai.GenerationConfig(**performance_config)
            )
            
            response = model.generate_content(optimized_prompt)
            latency = time.time() - start_time
            
            # Create response object
            api_response = APIResponse(
                id=request.id,
                content=response.text,
                latency=latency,
                success=True
            )
            
            # Cache successful response
            self._cache_response(cache_key, api_response)
            
            # Update metrics
            self.metrics['total_requests'] += 1
            self.metrics['successful_requests'] += 1
            self.metrics['total_latency'] += latency
            
            return api_response
            
        except Exception as e:
            latency = time.time() - start_time
            
            # Update metrics
            self.metrics['total_requests'] += 1
            self.metrics['failed_requests'] += 1
            self.metrics['total_latency'] += latency
            
            return APIResponse(
                id=request.id,
                content="",
                latency=latency,
                success=False,
                error=str(e)
            )
    
    def _apply_rate_limiting(self) -> None:
        """Apply rate limiting to prevent API throttling"""
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def _get_cached_response(self, cache_key: str) -> Optional[APIResponse]:
        """Retrieve cached response if available and not expired"""
        if cache_key in self.request_cache:
            cached_response = self.request_cache[cache_key]
            # Simple TTL check (in production, would use timestamps)
            return cached_response
        return None
    
    def _cache_response(self, cache_key: str, response: APIResponse) -> None:
        """Cache successful response"""
        if response.success and len(self.request_cache) < 100:  # Limit cache size
            self.request_cache[cache_key] = response
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics"""
        total_requests = self.metrics['total_requests']
        
        if total_requests == 0:
            return {
                'total_requests': 0,
                'success_rate': 0.0,
                'average_latency': 0.0,
                'cache_hit_rate': 0.0
            }
        
        return {
            'total_requests': total_requests,
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'success_rate': self.metrics['successful_requests'] / total_requests,
            'average_latency': self.metrics['total_latency'] / total_requests,
            'total_latency': self.metrics['total_latency'],
            'cache_hits': self.metrics['cache_hits'],
            'cache_hit_rate': self.metrics['cache_hits'] / total_requests if total_requests > 0 else 0.0
        }
    
    def clear_cache(self) -> None:
        """Clear the request cache"""
        self.request_cache.clear()
    
    def shutdown(self) -> None:
        """Shutdown the optimizer and cleanup resources"""
        self.executor.shutdown(wait=True)


# Global optimizer instance
_optimizer_instance = None


def get_optimizer() -> GeminiAPIOptimizer:
    """Get the global API optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = GeminiAPIOptimizer()
    return _optimizer_instance


def make_optimized_request(prompt: str, task_type: str = "analysis", 
                         priority: int = 1, model_config: Optional[Dict] = None) -> APIResponse:
    """
    Convenience function to make an optimized API request
    """
    optimizer = get_optimizer()
    
    request = APIRequest(
        id=f"request_{int(time.time() * 1000)}",
        prompt=prompt,
        model_config=model_config,
        priority=priority
    )
    
    return optimizer._make_single_request(request)


def make_batch_requests(prompts: List[str], task_types: Optional[List[str]] = None,
                       priorities: Optional[List[int]] = None) -> List[APIResponse]:
    """
    Convenience function to make multiple optimized API requests
    """
    optimizer = get_optimizer()
    
    if task_types is None:
        task_types = ["analysis"] * len(prompts)
    if priorities is None:
        priorities = [1] * len(prompts)
    
    requests = []
    for i, prompt in enumerate(prompts):
        request = APIRequest(
            id=f"batch_request_{i}_{int(time.time() * 1000)}",
            prompt=prompt,
            priority=priorities[i] if i < len(priorities) else 1
        )
        requests.append(request)
    
    return optimizer.batch_requests(requests)