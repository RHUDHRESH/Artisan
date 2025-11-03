"""
Dual Model Router - Enhanced routing logic for 4B vs 1B model selection
"""
from typing import Dict, Optional
from backend.core.ollama_client import OllamaClient
from loguru import logger


class DualModelRouter:
    """
    Intelligent router that decides which model (4B or 1B) to use
    based on query complexity and task type
    """
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    async def route_query(
        self,
        query: str,
        context: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> str:
        """
        Route query to appropriate model
        
        Args:
            query: User query
            context: Additional context
            task_type: Explicit task type (optional)
        
        Returns:
            Model name to use: "gemma3:4b" or "gemma3:1b"
        """
        # Explicit task type overrides everything
        if task_type:
            task_type_lower = task_type.lower()
            if "complex" in task_type_lower or "reasoning" in task_type_lower or "analysis" in task_type_lower:
                return OllamaClient.REASONING_MODEL
            elif "simple" in task_type_lower or "fast" in task_type_lower or "classify" in task_type_lower:
                return OllamaClient.FAST_MODEL
        
        # Classify query complexity
        complexity_score = await self._assess_complexity(query)
        
        # Use 4B for complex queries, 1B for simple ones
        if complexity_score > 0.6:
            logger.debug(f"Routing to 4B (complexity: {complexity_score:.2f})")
            return OllamaClient.REASONING_MODEL
        else:
            logger.debug(f"Routing to 1B (complexity: {complexity_score:.2f})")
            return OllamaClient.FAST_MODEL
    
    async def _assess_complexity(self, query: str) -> float:
        """
        Assess query complexity on scale of 0-1
        
        Returns:
            Complexity score (0 = simple, 1 = complex)
        """
        # Quick heuristics
        complex_keywords = [
            "analyze", "explain", "compare", "evaluate", "design", "plan",
            "strategy", "calculate", "recommend", "suggest", "optimize"
        ]
        
        simple_keywords = [
            "yes", "no", "what", "where", "when", "who", "classify", "identify"
        ]
        
        query_lower = query.lower()
        
        # Check for complex keywords
        complex_count = sum(1 for keyword in complex_keywords if keyword in query_lower)
        simple_count = sum(1 for keyword in simple_keywords if keyword in query_lower)
        
        # Length heuristic
        length_score = min(len(query) / 200, 0.3)  # Longer queries tend to be more complex
        
        # Question count (multiple questions = more complex)
        question_count = query.count("?")
        question_score = min(question_count * 0.2, 0.3)
        
        # Calculate final score
        complexity = 0.2  # Base complexity
        complexity += complex_count * 0.15
        complexity -= simple_count * 0.1
        complexity += length_score
        complexity += question_score
        
        return max(0.0, min(1.0, complexity))
    
    async def execute(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> Dict:
        """
        Execute query with automatic routing
        
        Returns:
            Dictionary with response, model_used, and metadata
        """
        model = await self.route_query(query, context, task_type)
        
        if model == OllamaClient.REASONING_MODEL:
            response = await self.ollama.reasoning_task(
                prompt=query,
                system=system_prompt
            )
        else:
            response = await self.ollama.fast_task(
                prompt=query,
                system=system_prompt
            )
        
        return {
            "response": response,
            "model_used": model,
            "task_type": task_type or "auto-routed"
        }

