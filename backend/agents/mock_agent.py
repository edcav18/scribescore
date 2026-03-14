from agents.base_agent import BaseAgent, AgentResult
from typing import Any


class MockAgent(BaseAgent):
    """
    Test agent that simply echoes input and returns a high-confidence result.
    
    Used to verify BaseAgent contract is working correctly.
    """
    def __init__(self):
        super().__init__()

    def process(self, input_data: Any) -> AgentResult:
        """
        Echo the input and return a dummy result.
        """
        output = {"echo": input_data, "processed_by": self.name}
        
        result = AgentResult(
            input_data=input_data,
            output_data=output,
            confidence=0.95,
            notes="Mock agent processed input successfully"
        )
        
        self.log_result(result)
        return result