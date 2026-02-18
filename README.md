# ScribeScore

AI-powered music transcription tool that converts audio into guitar tablature using a multi-agent validation pipeline.

> **Work in progress.** Currently in active development — MVP targeting ~4 weeks.

---

## What it does

Upload a song, and ScribeScore isolates the guitar track and transcribes single-note lines (solos, riffs, melodic passages) into readable guitar tab. Rather than relying on a single AI model, it uses a pipeline of specialized agents that check and correct each other's work before producing output.

---

## How it works

1. **Stem Separation** — Demucs isolates the guitar track from the full mix
2. **Audio-to-MIDI** — basic-pitch converts the isolated audio to raw MIDI
3. **Pitch Correction Agent** — smooths pitch detection noise and errors
4. **Rhythm Quantizer Agent** — aligns notes to a musical grid
5. **Music Theory Validator** — checks notes against key and scale
6. **Harmonic Context Agent** — validates ambiguous notes against chord progressions
7. **Performance Reality Check** — ensures output is physically playable (fret spans, string positions, position shifts)
8. **Quality Assessor** — coordinates agents, scores confidence per section
9. **Human-in-the-loop review** — flags low-confidence sections for user correction
10. **Notation Generator** — exports final guitar tab as PDF via LilyPond

All agent decisions are logged in real-time in the UI, showing reasoning at each step.

---

## Tech stack

| Layer | Tools |
|---|---|
| Backend | FastAPI, uvicorn, SQLite |
| Frontend | React, Vite |
| Audio | Demucs, basic-pitch, librosa |
| Music processing | music21, mido |
| Notation | LilyPond |
| AI | Anthropic Claude API (Haiku + Sonnet) |

---

## MVP scope

- ✅ Monophonic guitar transcription (single-note lines only)
- ✅ Guitar tab output (PDF via LilyPond)
- ✅ Multi-agent correction pipeline
- ✅ Real-time activity log
- ✅ Human-in-the-loop review for low-confidence sections
- ❌ Chord transcription (out of scope for MVP)
- ❌ Drum transcription
- ❌ Live deployment

---

## Project structure

```
scoresribe/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agents/          # Individual transcription agents
│   │   ├── services/        # Audio, MIDI, LLM utilities
│   │   ├── api/             # FastAPI routes
│   │   └── models/          # Pydantic schemas, state
│   └── prompts/             # Agent prompt templates
├── frontend/
│   └── src/
│       └── components/      # React UI components
└── README.md
```

---

## Running locally

> Setup instructions coming once the foundation is in place.

---

## Background

Built by someone with a sound engineering and music production background who got tired of existing transcription tools producing mediocre results. The multi-agent approach is the core bet: audio-to-MIDI is inherently noisy, and a single model correcting its own errors doesn't work well. Specialized agents with different areas of expertise — music theory, harmonic context, physical playability — catch different classes of errors.

---

## Status

| Week | Goal | Status |
|---|---|---|
| 1 | FastAPI, file upload, Demucs, basic-pitch | In progress |
| 2 | BaseAgent, Pitch Correction, Rhythm Quantizer, activity log | Upcoming |
| 3 | Theory Validator, Harmonic Context, Reality Check, coordinator | Upcoming |
| 4 | LilyPond tab export, HITL review UI, demo video | Upcoming |