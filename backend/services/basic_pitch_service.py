import logging
from pathlib import Path
from typing import Optional
import numpy as np
from basic_pitch.inference import predict
from music21 import stream, instrument, note, meter
import os

logger = logging.getLogger(__name__)

class BasicPitchService:
    """
    Wrapper around basic-pitch for extracting monophonic MIDI from audio.
    
    basic-pitch is a Meta model that predicts pitch, onset, and contour from audio.
    We use it to get a rough MIDI representation that agents will then refine.
    
    Key insight: basic-pitch returns (note_events, midi_data, contours).
    We parse note_events (onset, duration, pitch_midi) and convert to music21 Note objects.
    """
    @staticmethod
    def extract_midi_from_audio(
        audio_path: str,
        model_path: Optional[str] = None,
    ) -> stream.Score:
        """
        Extract monophonic MIDI from audio using basic-pitch.
        
        Args:
            audio_path: Path to audio file (mp3, wav, flac, m4a, etc.)
            model_path: Optional path to custom basic-pitch model. 
                       If None, uses the default pretrained model.
        
        Returns:
            A music21 Score object containing Note objects with pitch and duration.
        
        Raises:
            FileNotFoundError: If audio_path doesn't exist.
            RuntimeError: If basic-pitch inference fails.
        
        Technical note:
            basic-pitch.predict() uses a Keras/TensorFlow neural network to estimate
            pitch contours from spectrogram. The model was trained on monophonic vocals
            but works reasonably well on guitar. Output is (note_events, midi_data, contours)
            where note_events is a list of (onset_sec, duration_sec, midi_pitch, confidence).
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            logger.info(f"Running basic-pitch inference on {audio_path}")
            
            # basic-pitch returns (note_events, midi_data, contours)
            # note_events: list of (onset_sec, duration_sec, midi_pitch, confidence)
            note_events, midi_data, contours = predict(audio_path)

            logger.info(f"basic-pitch extracted notes")
            
            # Convert to music21 Score
            score = stream.Score()
            part = stream.Part()
            part.instrument = instrument.Guitar()
            
            # Add time signature (4/4 for now — can be refined later)
            part.append(meter.TimeSignature('4/4'))
            
            # note_events is a dict with 'note', 'onset', 'contour' keys
            # Each value is a numpy array of shape (time_frames, frequency_bins)
            # This is raw spectrogram data, not parsed note events
            # We need to use midi_data instead, which is the actual MIDI representation

            # For now, use a simpler approach: just convert midi_data to notes
            if midi_data is not None:
                for note_obj in midi_data.instruments[0].notes:
                    n = note.Note(midi=note_obj.pitch)
                    n.quarterLength = note_obj.duration
                    part.append(n)

            score.append(part)
            return score
        
        except Exception as e:
            logger.error(f"basic-pitch inference failed: {e}")
            raise RuntimeError(f"Failed to extract MIDI from {audio_path}: {e}") from e
        
    @staticmethod
    def score_to_dict(score: stream.Score) -> dict:
        """
        Convert a music21 Score to a serializable dict for agent pipelines.
        
        Returns:
            {
                "notes": [
                    {"pitch": 69, "duration_quarters": 2.0, "onset_quarter": 0.0},
                    ...
                ],
                "time_signature": "4/4",
                "instrument": "Guitar"
            }
        
        This format is easier for agents to reason about than music21 objects.
        """
        notes = []
        onset_quarter = 0.0

        for element in score.flatten().notesAndRests:
            if isinstance(element, note.Note):
                notes.append({
                    "pitch": element.pitch.midi,
                    "duration_quarters": element.quarterLength,
                    "onset_quarter": onset_quarter
                })
            onset_quarter += element.quarterLength

        return {
            "notes": notes,
            "time_signature": "4/4", # Could parse this from score if needed
            "instrument": "Guitar"
        }