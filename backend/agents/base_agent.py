from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import logging

@dataclass(frozen=True)
class AgentResult:
    """
    Immutable result object returned by every agent.
    
    Attributes:
        input_data: The raw data fed to the agent (dict or object).
        output_data: The processed/analyzed data produced by the agent.
        confidence: Float between 0.0 and 1.0 indicating agent confidence.
                   0.0 = no confidence, 1.0 = very confident.
        notes: Human-readable explanation of the result or any caveats.
    """
    input_data: Any
    output_data: Any
    confidence: float
    notes: str

    def __post_init__(self):
        """Validate confidence is in [0.0, 1.0] range"""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    def to_dict(self):
        return {
            "input_data": self.input_data,
            "output_data": self.output_data,
            "confidence": self.confidence,
            "notes": self.notes,
        }
    
class BaseAgent(ABC):
    """
    Abstract base class for all transcription pipeline agents.
    
    Every agent in the pipeline (Pitch Correction, Rhythm Quantizer, etc.)
    must inherit from BaseAgent and implement the `process()` method.

    This ensures:
    - Consistent input/output shapes (AgentResult)
    - Confidence scoring across the pipeline
    - Human-readable notes for debugging and UI display
    - Composability: agents can be chained together predictably
    
    Attributes:
        name: A descriptive name for the agent (e.g., "PitchCorrection").
              Set this in __init__ of subclasses.
    """

    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def process(self, input_data: Any) -> AgentResult:
        """
        Process the input data and return an AgentResult.
        
        Args:
            input_data: The raw data to be processed (e.g., audio features).
        
        Returns:
            An AgentResult containing the output data, confidence score, and notes.
        
        Raises:
            Should raise descriptive exceptions on failure (not silently return low confidence).
            The pipeline coordinator will catch and log these.
        """
        pass

    def log_result(self, result: AgentResult) -> None:
        """
        Log the agent's result for debugging and audit trails.
        
        This is called automatically by the pipeline coordinator.
        Override if you need custom logging behavior.
        
        Args:
            result: The AgentResult returned by process().
        """
        self.logger.info(
            f"{self.name} completed | confidence={result.confidence:.2f} | {result.notes}"
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
