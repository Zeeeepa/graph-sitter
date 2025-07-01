"""
Strands Think Tool

Advanced reasoning and decision-making capabilities for Strands agents.
Based on: https://github.com/strands-agents/tools/blob/main/src/strands_tools/think.py
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
import json

logger = logging.getLogger(__name__)


class ThinkingMode(Enum):
    """Different modes of thinking."""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CRITICAL = "critical"
    STRATEGIC = "strategic"
    REFLECTIVE = "reflective"


class ReasoningStep(Enum):
    """Steps in the reasoning process."""
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    CONCLUSION = "conclusion"


@dataclass
class ThoughtProcess:
    """Represents a single thought or reasoning step."""
    id: str
    step_type: ReasoningStep
    content: str
    confidence: float  # 0.0 to 1.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # IDs of prerequisite thoughts


@dataclass
class ThinkingSession:
    """A complete thinking session with multiple thought processes."""
    session_id: str
    mode: ThinkingMode
    context: str
    goal: str
    thoughts: List[ThoughtProcess] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    conclusion: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ThinkingEngine:
    """Advanced thinking and reasoning engine for agents."""
    
    def __init__(self):
        """Initialize the thinking engine."""
        self.sessions: Dict[str, ThinkingSession] = {}
        self.thinking_strategies: Dict[ThinkingMode, Callable] = {
            ThinkingMode.ANALYTICAL: self._analytical_thinking,
            ThinkingMode.CREATIVE: self._creative_thinking,
            ThinkingMode.CRITICAL: self._critical_thinking,
            ThinkingMode.STRATEGIC: self._strategic_thinking,
            ThinkingMode.REFLECTIVE: self._reflective_thinking
        }
        
        # Reasoning patterns
        self.reasoning_patterns = {
            "deductive": self._deductive_reasoning,
            "inductive": self._inductive_reasoning,
            "abductive": self._abductive_reasoning,
            "analogical": self._analogical_reasoning
        }
        
        logger.info("Initialized thinking engine")
    
    async def think(self, 
                   context: str,
                   goal: str,
                   mode: ThinkingMode = ThinkingMode.ANALYTICAL,
                   session_id: Optional[str] = None) -> ThinkingSession:
        """Start a thinking session.
        
        Args:
            context: Context or problem to think about
            goal: What we're trying to achieve
            mode: Mode of thinking to use
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Thinking session with results
        """
        if session_id is None:
            session_id = f"think_{int(time.time() * 1000)}"
        
        session = ThinkingSession(
            session_id=session_id,
            mode=mode,
            context=context,
            goal=goal
        )
        
        self.sessions[session_id] = session
        
        logger.info(f"Starting thinking session: {session_id} ({mode.value})")
        
        try:
            # Apply thinking strategy
            strategy = self.thinking_strategies[mode]
            await strategy(session)
            
            # Generate conclusion
            await self._generate_conclusion(session)
            
            session.end_time = time.time()
            
            logger.info(f"Completed thinking session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error in thinking session {session_id}: {e}")
            session.metadata["error"] = str(e)
        
        return session
    
    async def add_thought(self,
                         session_id: str,
                         step_type: ReasoningStep,
                         content: str,
                         confidence: float = 0.5,
                         dependencies: Optional[List[str]] = None) -> str:
        """Add a thought to a thinking session.
        
        Args:
            session_id: ID of the thinking session
            step_type: Type of reasoning step
            content: Content of the thought
            confidence: Confidence level (0.0 to 1.0)
            dependencies: IDs of prerequisite thoughts
            
        Returns:
            ID of the created thought
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        thought_id = f"thought_{len(self.sessions[session_id].thoughts)}"
        
        thought = ThoughtProcess(
            id=thought_id,
            step_type=step_type,
            content=content,
            confidence=confidence,
            dependencies=dependencies or []
        )
        
        self.sessions[session_id].thoughts.append(thought)
        
        logger.debug(f"Added thought to session {session_id}: {step_type.value}")
        
        return thought_id
    
    async def _analytical_thinking(self, session: ThinkingSession):
        """Analytical thinking strategy."""
        # Break down the problem
        await self.add_thought(
            session.session_id,
            ReasoningStep.OBSERVATION,
            f"Analyzing the context: {session.context}",
            confidence=0.8
        )
        
        # Identify key components
        await self.add_thought(
            session.session_id,
            ReasoningStep.ANALYSIS,
            "Breaking down the problem into key components and relationships",
            confidence=0.7
        )
        
        # Apply logical reasoning
        await self.add_thought(
            session.session_id,
            ReasoningStep.HYPOTHESIS,
            "Forming hypotheses based on available evidence and logical deduction",
            confidence=0.6
        )
        
        # Evaluate evidence
        await self.add_thought(
            session.session_id,
            ReasoningStep.EVALUATION,
            "Evaluating the strength of evidence and logical consistency",
            confidence=0.7
        )
    
    async def _creative_thinking(self, session: ThinkingSession):
        """Creative thinking strategy."""
        # Divergent thinking
        await self.add_thought(
            session.session_id,
            ReasoningStep.OBSERVATION,
            "Exploring multiple perspectives and unconventional approaches",
            confidence=0.6
        )
        
        # Generate alternatives
        await self.add_thought(
            session.session_id,
            ReasoningStep.HYPOTHESIS,
            "Generating diverse and novel solutions through brainstorming",
            confidence=0.5
        )
        
        # Combine ideas
        await self.add_thought(
            session.session_id,
            ReasoningStep.SYNTHESIS,
            "Combining different ideas and concepts in innovative ways",
            confidence=0.6
        )
        
        # Refine concepts
        await self.add_thought(
            session.session_id,
            ReasoningStep.EVALUATION,
            "Refining and developing the most promising creative solutions",
            confidence=0.7
        )
    
    async def _critical_thinking(self, session: ThinkingSession):
        """Critical thinking strategy."""
        # Question assumptions
        await self.add_thought(
            session.session_id,
            ReasoningStep.OBSERVATION,
            "Identifying and questioning underlying assumptions",
            confidence=0.8
        )
        
        # Evaluate sources
        await self.add_thought(
            session.session_id,
            ReasoningStep.ANALYSIS,
            "Critically evaluating the credibility and reliability of information sources",
            confidence=0.7
        )
        
        # Identify biases
        await self.add_thought(
            session.session_id,
            ReasoningStep.EVALUATION,
            "Recognizing potential biases and logical fallacies",
            confidence=0.6
        )
        
        # Construct arguments
        await self.add_thought(
            session.session_id,
            ReasoningStep.SYNTHESIS,
            "Building well-reasoned arguments with strong evidence",
            confidence=0.8
        )
    
    async def _strategic_thinking(self, session: ThinkingSession):
        """Strategic thinking strategy."""
        # Analyze environment
        await self.add_thought(
            session.session_id,
            ReasoningStep.OBSERVATION,
            "Analyzing the strategic environment and key stakeholders",
            confidence=0.7
        )
        
        # Identify opportunities
        await self.add_thought(
            session.session_id,
            ReasoningStep.ANALYSIS,
            "Identifying opportunities, threats, and competitive advantages",
            confidence=0.6
        )
        
        # Develop scenarios
        await self.add_thought(
            session.session_id,
            ReasoningStep.HYPOTHESIS,
            "Developing multiple scenarios and strategic options",
            confidence=0.5
        )
        
        # Plan implementation
        await self.add_thought(
            session.session_id,
            ReasoningStep.SYNTHESIS,
            "Creating actionable strategic plans with clear objectives",
            confidence=0.7
        )
    
    async def _reflective_thinking(self, session: ThinkingSession):
        """Reflective thinking strategy."""
        # Self-examination
        await self.add_thought(
            session.session_id,
            ReasoningStep.OBSERVATION,
            "Examining personal experiences, beliefs, and mental models",
            confidence=0.6
        )
        
        # Identify patterns
        await self.add_thought(
            session.session_id,
            ReasoningStep.ANALYSIS,
            "Identifying patterns in thinking and decision-making processes",
            confidence=0.5
        )
        
        # Learn from experience
        await self.add_thought(
            session.session_id,
            ReasoningStep.EVALUATION,
            "Extracting lessons learned and insights from past experiences",
            confidence=0.7
        )
        
        # Plan improvements
        await self.add_thought(
            session.session_id,
            ReasoningStep.SYNTHESIS,
            "Developing plans for improved thinking and decision-making",
            confidence=0.6
        )
    
    async def _generate_conclusion(self, session: ThinkingSession):
        """Generate a conclusion for the thinking session."""
        thoughts = session.thoughts
        
        if not thoughts:
            session.conclusion = "No thoughts generated during this session."
            session.confidence_score = 0.0
            return
        
        # Calculate average confidence
        avg_confidence = sum(t.confidence for t in thoughts) / len(thoughts)
        
        # Find the most confident conclusion-type thought
        conclusion_thoughts = [t for t in thoughts if t.step_type == ReasoningStep.CONCLUSION]
        
        if conclusion_thoughts:
            best_conclusion = max(conclusion_thoughts, key=lambda t: t.confidence)
            session.conclusion = best_conclusion.content
            session.confidence_score = best_conclusion.confidence
        else:
            # Generate conclusion based on synthesis and evaluation thoughts
            synthesis_thoughts = [t for t in thoughts if t.step_type == ReasoningStep.SYNTHESIS]
            evaluation_thoughts = [t for t in thoughts if t.step_type == ReasoningStep.EVALUATION]
            
            if synthesis_thoughts or evaluation_thoughts:
                relevant_thoughts = synthesis_thoughts + evaluation_thoughts
                best_thought = max(relevant_thoughts, key=lambda t: t.confidence)
                
                session.conclusion = f"Based on {session.mode.value} thinking: {best_thought.content}"
                session.confidence_score = avg_confidence
            else:
                session.conclusion = f"Completed {session.mode.value} thinking process with {len(thoughts)} reasoning steps."
                session.confidence_score = avg_confidence
        
        # Add conclusion as final thought
        await self.add_thought(
            session.session_id,
            ReasoningStep.CONCLUSION,
            session.conclusion,
            confidence=session.confidence_score
        )
    
    async def _deductive_reasoning(self, premises: List[str], session_id: str) -> str:
        """Apply deductive reasoning."""
        await self.add_thought(
            session_id,
            ReasoningStep.ANALYSIS,
            f"Applying deductive reasoning to premises: {premises}",
            confidence=0.8
        )
        
        # Simplified deductive reasoning
        conclusion = "If the premises are true, then the conclusion follows logically."
        return conclusion
    
    async def _inductive_reasoning(self, observations: List[str], session_id: str) -> str:
        """Apply inductive reasoning."""
        await self.add_thought(
            session_id,
            ReasoningStep.ANALYSIS,
            f"Applying inductive reasoning to observations: {observations}",
            confidence=0.6
        )
        
        # Simplified inductive reasoning
        conclusion = "Based on the observed patterns, we can infer a general principle."
        return conclusion
    
    async def _abductive_reasoning(self, observations: List[str], session_id: str) -> str:
        """Apply abductive reasoning."""
        await self.add_thought(
            session_id,
            ReasoningStep.HYPOTHESIS,
            f"Applying abductive reasoning to find best explanation for: {observations}",
            confidence=0.5
        )
        
        # Simplified abductive reasoning
        conclusion = "The most likely explanation for these observations is..."
        return conclusion
    
    async def _analogical_reasoning(self, source_case: str, target_case: str, session_id: str) -> str:
        """Apply analogical reasoning."""
        await self.add_thought(
            session_id,
            ReasoningStep.ANALYSIS,
            f"Drawing analogies between {source_case} and {target_case}",
            confidence=0.6
        )
        
        # Simplified analogical reasoning
        conclusion = "By analogy with the source case, we can infer similar properties in the target case."
        return conclusion
    
    def get_session(self, session_id: str) -> Optional[ThinkingSession]:
        """Get a thinking session by ID.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Thinking session or None if not found
        """
        return self.sessions.get(session_id)
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of a thinking session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session summary
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session.session_id,
            "mode": session.mode.value,
            "context": session.context,
            "goal": session.goal,
            "thought_count": len(session.thoughts),
            "conclusion": session.conclusion,
            "confidence_score": session.confidence_score,
            "duration": (session.end_time - session.start_time) if session.end_time else None,
            "reasoning_steps": [
                {
                    "step": thought.step_type.value,
                    "confidence": thought.confidence,
                    "content": thought.content[:100] + "..." if len(thought.content) > 100 else thought.content
                }
                for thought in session.thoughts
            ]
        }
    
    def clear_session(self, session_id: str):
        """Clear a thinking session.
        
        Args:
            session_id: ID of the session to clear
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared thinking session: {session_id}")


# Global thinking engine instance
thinking_engine = ThinkingEngine()


async def think(context: str, 
               goal: str, 
               mode: ThinkingMode = ThinkingMode.ANALYTICAL) -> ThinkingSession:
    """Convenience function for thinking.
    
    Args:
        context: Context or problem to think about
        goal: What we're trying to achieve
        mode: Mode of thinking to use
        
    Returns:
        Thinking session with results
    """
    return await thinking_engine.think(context, goal, mode)

