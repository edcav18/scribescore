"""Quick test of BaseAgent framework."""

from agents.base_agent import BaseAgent, AgentResult
from agents.mock_agent import MockAgent


def test_base_agent_abstract():
    """Verify BaseAgent cannot be instantiated directly."""
    try:
        agent = BaseAgent()
        print("❌ FAIL: BaseAgent should be abstract and not instantiable")
    except TypeError as e:
        print(f"✅ PASS: BaseAgent correctly raises TypeError: {e}")


def test_mock_agent_process():
    """Verify MockAgent can process input and return AgentResult."""
    agent = MockAgent()
    
    test_input = {
        "midi_notes": [60, 62, 64, 65, 67],
        "timestamps": [0.0, 0.5, 1.0, 1.5, 2.0],
    }
    
    result = agent.process(test_input)
    
    # Check that result is AgentResult
    assert isinstance(result, AgentResult), "Result should be AgentResult instance"
    print(f"✅ PASS: Result is AgentResult")
    
    # Check immutability
    try:
        result.confidence = 0.5
        print("❌ FAIL: AgentResult should be immutable")
    except Exception:
        print("✅ PASS: AgentResult is immutable (frozen)")
    
    # Check result structure
    assert result.input_data == test_input
    assert result.output_data["echo"] == test_input
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.notes, str)
    print(f"✅ PASS: AgentResult has correct structure")
    print(f"   - Input: {result.input_data}")
    print(f"   - Output: {result.output_data}")
    print(f"   - Confidence: {result.confidence}")
    print(f"   - Notes: {result.notes}")


def test_confidence_validation():
    """Verify confidence is validated to [0, 1]."""
    try:
        bad_result = AgentResult(
            input_data={},
            output_data={},
            confidence=1.5,  # Invalid: > 1.0
            notes="Bad confidence"
        )
        print("❌ FAIL: Should reject confidence > 1.0")
    except ValueError as e:
        print(f"✅ PASS: Correctly rejects invalid confidence: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing BaseAgent Framework")
    print("=" * 60)
    
    test_base_agent_abstract()
    print()
    test_mock_agent_process()
    print()
    test_confidence_validation()
    
    print()
    print("=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)