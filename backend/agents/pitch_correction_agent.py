import os
import json
import logging
from typing import Any, Dict, List
from agents.base_agent import BaseAgent, AgentResult
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class PitchCorrectionAgent(BaseAgent):
    """
    Corrects pitch detection errors in raw MIDI from basic-pitch.
    
    **What it does:**
    - Takes raw MIDI notes (onset, pitch, duration) from basic-pitch
    - Uses Claude API to identify suspicious pitches (octave errors, outliers, jumps)
    - Returns corrected MIDI + confidence score + reasoning
    
    **Confidence scoring:**
    - 0.9+: MIDI looks clean, minimal corrections needed
    - 0.7-0.9: Some noise detected but corrections are straightforward
    - 0.5-0.7: Multiple suspicious patterns; later agents should scrutinize
    - <0.5: Heavy noise; this section may need human review
    
    **Design choice: Mock vs. Real Claude API**
    - For development, this agent works with a hardcoded mock response
    - To enable real Claude API, set ANTHROPIC_API_KEY in .env
    - This lets you test the full pipeline without API calls during development
    
    **Why Haiku for this agent:**
    - Pitch correction is a straightforward task (pattern matching on note sequences)
    - Haiku is 10x cheaper than Sonnet with minimal quality loss for this use case
    - Saves budget for more complex agents (Music Theory Validator uses Sonnet)
    """
    def __init__(self, use_mock: bool = False):
        """
        Initialize the Pitch Correction Agent.
        
        Args:
            use_mock: If True, return a hardcoded mock response (useful for testing).
                     If False, call Claude API (requires ANTHROPIC_API_KEY in .env).
        
        Note on initialization:
            We create the Anthropic client once in __init__ rather than in process()
            to avoid re-initializing on every call (this would be wasteful).
            The client reads ANTHROPIC_API_KEY from environment automatically.
        """
        super().__init__()
        self.use_mock = use_mock

        if not use_mock:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not found in environment. "
                    "Set it in .env or use use_mock=True for testing."
                )
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None
            logger.info("PitchCorrectionAgent initialized in mock mode")

    def process(self, input_data: Any) -> AgentResult:
        """
        Process raw MIDI and return pitch corrections.
        
        Args:
            input_data: Dict with structure:
                {
                    "notes": [
                        {"pitch": 69, "duration_quarters": 2.0, "onset_quarter": 0.0},
                        ...
                    ],
                    "instrument": "Guitar"
                }
                This comes from BasicPitchService.score_to_dict().
        
        Returns:
            AgentResult with:
                output_data: {
                    "corrected_notes": [...same format as input notes...],
                    "corrections": [
                        {
                            "index": 0,
                            "original_pitch": 69,
                            "corrected_pitch": 69,
                            "reason": "Within normal range, no correction needed"
                        },
                        ...
                    ]
                }
                confidence: 0.0-1.0 reflecting how clean the MIDI is
                notes: Summary of corrections applied
        """
        try:
            notes = input_data.get("notes", [])
            if not notes:
                # Empty input — still valid, just return empty output
                return AgentResult(
                    input_data=input_data,
                    output_data={
                        "corrected_notes": [],
                        "corrections": []
                    },
                    confidence=1.0,
                    notes="No notes to correct"
                )
            
            # Call Claude to analyze the MIDI
            corrections = self._get_pitch_corrections(notes, input_data.get("instrument", "Guitar"))

            # Apply corrections to create corrected_notes
            corrected_notes = self._apply_corrections(notes, corrections)
            
            # Calculate confidence based on how much correction was needed
            confidence = self._calculate_confidence(corrections, len(notes))

            summary = f"Analyzed {len(notes)} notes, made {len([c for c in corrections if c['corrected_pitch'] != c['original_pitch']])} corrections"

            return AgentResult(
                input_data=input_data,
                output_data={
                    "corrected_notes": corrected_notes,
                    "corrections": corrections
                },
                confidence=confidence,
                notes=summary
            )
        
        except Exception as e:
            logger.error(f"PitchCorrectionAgent failed: {e}")
            raise
    
    def _get_pitch_corrections(self, notes: List[Dict], instrument: str) -> List[Dict]:
        """
        Call Claude API (or mock) to suggest pitch corrections.
        
        Returns a list of correction dicts with structure:
            {
                "index": 0,
                "original_pitch": 69,
                "corrected_pitch": 69,
                "reason": "..."
            }
        
        This is where the LLM reasoning happens. Claude sees the full note sequence
        and can spot patterns like systematic octave errors or outliers.
        """
        if self.use_mock:
             return self._mock_pitch_corrections(notes, instrument)
        
        # Build prompt for Claude
        # Guitar pitch range: typically 40 (E2, low E string) to 84 (E6, high e string)
        system_prompt = f"""You are a pitch correction specialist for {instrument} transcription.
        Your job is to identify and correct pitch detection errors in MIDI output from a neural network model.
        The model (basic-pitch) predicts pitch from audio spectrogram, so common errors include:
        - Octave errors (e.g., predicting C3 instead of C4)
        - Outliers (single note way out of range)
        - Pitch jumps > 12 semitones (unrealistic for {instrument} single-note lines)

        {instrument} typical pitch range: MIDI 40-84 (E2 to E6).

        Respond ONLY with a valid JSON array of correction objects."""

        user_prompt = f"""Analyze these {len(notes)} notes and suggest corrections:

        {json.dumps(notes[:20], indent=2)}  # Show first 20 notes to stay within token limits

        For each note, provide:
        - index: position in the list
        - original_pitch: MIDI note number from input
        - corrected_pitch: your suggested correction (or same if no correction needed)
        - reason: brief explanation

        Respond ONLY with a valid JSON array. Example:
        [
        {{"index": 0, "original_pitch": 69, "corrected_pitch": 69, "reason": "A4, in range"}},
        {{"index": 1, "original_pitch": 20, "corrected_pitch": 60, "reason": "Octave error, too low"}}
        ]"""

        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",  # Use Haiku for cost efficiency
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_text = message.content[0].text
            corrections = json.loads(response_text)
            
            logger.info(f"Claude API returned {len(corrections)} pitch corrections")
            return corrections
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Claude response as JSON: {e}. Using mock.")
            return self._mock_pitch_corrections(notes, instrument)
        except Exception as e:
            logger.error(f"Claude API call failed: {e}. Falling back to mock.")
            return self._mock_pitch_corrections(notes, instrument)

    def _mock_pitch_corrections(self, notes: List[Dict], instrument: str) -> List[Dict]:
        """
        Hardcoded mock response for testing without API calls.
        
        This is useful for:
        - Testing the full pipeline during development
        - Avoiding API costs during testing
        - Verifying data flows correctly before real LLM integration
        """
        corrections = []
        for i, note_obj in enumerate(notes):
            original_pitch = note_obj["pitch"]
            
            # Simple heuristics for mock:
            # - If pitch < 40 or > 84, it's probably an octave error
            corrected_pitch = original_pitch
            reason = "In range, no correction needed"
            
            if original_pitch < 40:
                corrected_pitch = original_pitch + 12
                reason = f"Octave error: {original_pitch} too low, correcting to {corrected_pitch}"
            elif original_pitch > 84:
                corrected_pitch = original_pitch - 12
                reason = f"Octave error: {original_pitch} too high, correcting to {corrected_pitch}"
            
            corrections.append({
                "index": i,
                "original_pitch": original_pitch,
                "corrected_pitch": corrected_pitch,
                "reason": reason
            })
        
        return corrections

    def _apply_corrections(self, notes: List[Dict], corrections: List[Dict]) -> List[Dict]:
        """Apply correction suggestions to create the corrected note list."""
        corrected = []
        correction_map = {c["index"]: c["corrected_pitch"] for c in corrections}
        
        for i, note_obj in enumerate(notes):
            corrected_note = note_obj.copy()
            if i in correction_map:
                corrected_note["pitch"] = correction_map[i]
            corrected.append(corrected_note)
        
        return corrected

    def _calculate_confidence(self, corrections: List[Dict], total_notes: int) -> float:
        """
        Calculate confidence based on how much correction was needed.
        
        Logic:
        - 0 corrections / total notes → 1.0 (perfect)
        - < 10% corrections → 0.9
        - 10-25% corrections → 0.7
        - 25-50% corrections → 0.5
        - > 50% corrections → 0.3
        
        Rationale: If the raw MIDI needed heavy corrections, later agents
        should be more skeptical of the output.
        """
        if total_notes == 0:
            return 1.0
        
        corrections_made = len([c for c in corrections if c["corrected_pitch"] != c["original_pitch"]])
        correction_rate = corrections_made / total_notes
        
        if correction_rate == 0:
            return 1.0
        elif correction_rate < 0.1:
            return 0.9
        elif correction_rate < 0.25:
            return 0.7
        elif correction_rate < 0.5:
            return 0.5
        else:
            return 0.3
