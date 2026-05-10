"""
Quality Evaluation Service
Uses LLM-as-a-judge to evaluate response quality on a sample basis.
"""

import random
import asyncio
from typing import Optional, Dict, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.llm_factory import LLMFactory
from app.services.prometheus_metrics import metrics_tracker
from app.core.structured_logger import logger
import json
import re
import time


class QualityEvaluator:
    """Evaluates response quality using LLM-as-a-judge"""
    
    def __init__(self, sample_rate: float = 0.1):
        """
        Initialize quality evaluator
        
        Args:
            sample_rate: Fraction of queries to evaluate (0.0-1.0)
        """
        self.sample_rate = sample_rate
        self.evaluation_count = 0
        self.quality_scores: Dict[str, list] = {
            'researcher': [],
            'evaluator': []
        }
    
    def should_evaluate(self) -> bool:
        """Determine if this query should be evaluated"""
        return random.random() < self.sample_rate
    
    async def evaluate_response(
        self,
        query: str,
        response: str,
        agent_role: str = 'evaluator'
    ) -> Tuple[float, str]:
        """
        Evaluate a response using LLM-as-a-judge
        
        Args:
            query: Original user query
            response: Generated response to evaluate
            agent_role: Role of agent that generated response
        
        Returns:
            Tuple of (score: 0-100, reasoning: str)
        """
        if not self.should_evaluate():
            return None, None
        
        try:
            start_time = time.time()
            
            # Get evaluation LLM
            llm = LLMFactory.get_model(query, purpose="evaluation")
            
            # Create evaluation prompt
            eval_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert quality evaluator for market research responses.
Evaluate the given response on the following criteria:
1. Relevance: Does it directly address the query?
2. Accuracy: Is the information correct and up-to-date?
3. Comprehensiveness: Are key points covered?
4. Clarity: Is the response well-structured and easy to understand?
5. Actionability: Can the reader use this information?

Provide a score from 0-100 where:
- 0-20: Poor (irrelevant, inaccurate, or incomplete)
- 21-40: Fair (some issues but partially useful)
- 41-60: Good (mostly accurate and relevant)
- 61-80: Very Good (comprehensive and well-structured)
- 81-100: Excellent (exceptional quality, all criteria met)

Format your response as JSON:
{"score": <0-100>, "reasoning": "<brief explanation>"}
"""),
                ("user", f"""Query: {query}

Response: {response}

Evaluate this response.""")
            ])
            
            chain = eval_prompt | llm | StrOutputParser()
            result_text = chain.invoke({})
            
            # Parse JSON response
            try:
                # Extract JSON from response (may have additional text)
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    score = float(result.get('score', 0))
                    reasoning = result.get('reasoning', '')
                else:
                    score = 50.0  # Default fallback
                    reasoning = result_text
            except (json.JSONDecodeError, ValueError):
                score = 50.0
                reasoning = result_text
            
            # Ensure score is in valid range
            score = max(0, min(100, score))
            
            # Record metrics
            metrics_tracker.record_response_quality(score, agent_role)
            
            # Track scores
            self.quality_scores[agent_role].append(score)
            self.evaluation_count += 1
            
            duration = time.time() - start_time
            logger.info(
                f"Quality evaluation: score={score:.1f}, agent={agent_role}, duration={duration:.2f}s",
                extra={'duration_ms': duration * 1000}
            )
            
            return score, reasoning
            
        except Exception as e:
            logger.error(f"Failed to evaluate response quality: {e}")
            return None, None
    
    def get_average_quality(self, agent_role: Optional[str] = None) -> float:
        """Get average quality score"""
        if agent_role:
            scores = self.quality_scores.get(agent_role, [])
        else:
            scores = []
            for role_scores in self.quality_scores.values():
                scores.extend(role_scores)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_quality_summary(self) -> Dict:
        """Get quality evaluation summary"""
        return {
            'evaluation_count': self.evaluation_count,
            'average_quality': self.get_average_quality(),
            'researcher_avg': self.get_average_quality('researcher'),
            'evaluator_avg': self.get_average_quality('evaluator'),
            'sample_rate': self.sample_rate,
        }


# Global quality evaluator instance
quality_evaluator = QualityEvaluator(sample_rate=0.1)
