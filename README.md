# ForOne — AI-Personalized Education Platform 🎓⚡

> **One Master Lecture in. Infinitely Personalized Lectures out.**  
> An end-to-end autonomous education engine that synthesizes personalized, neural-lip-synced video lectures tailored to every student's cognitive style, learning pace, and personal interests—backed by a **100% Factual Fidelity Failsafe Verifier**.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB.svg?style=flat&logo=react)](https://reactjs.org)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini%20Flash-4285F4.svg?style=flat&logo=google)](https://deepmind.google/technologies/gemini/)
[![Groq](https://img.shields.io/badge/Inference-Groq%20Llama%203.3-F05A28.svg?style=flat)](https://groq.com)
[![Sync Labs](https://img.shields.io/badge/Lip--Sync-Sync%20Labs-9333EA.svg?style=flat)](https://sync.so)
[![ElevenLabs](https://img.shields.io/badge/Voice-ElevenLabs%20%2B%20Edge--TTS-orange.svg?style=flat)](https://elevenlabs.io)

---

## 🌟 Key Highlights & Innovations

### 1. 🎭 4 Adaptive Learner Personas
* **Supportive Mentor**: Socratic, encouraging tone with step-by-step scaffolding and real-world intuition.
* **Exam Cram Specialist**: Rapid, high-yield, formula-first delivery highlighting exam traps and scoring criteria.
* **Witty & Pop-Culture**: Energetic, meme/gaming analogies (e.g., Minecraft, superhero metaphors) for conceptual stickiness.
* **Intuitive Visualist**: Geometric, first-principles approach emphasizing visual mental models and architectural diagrams.

### 2. 🛡️ Dual-STT Factual Fidelity Failsafe Verifier
* **The Problem**: Traditional generative AI can hallucinate or omit critical formula constants and edge cases.
* **The Solution**: Extracts atomic syllabus propositions from the master lecture transcript ($T_{master}$). After generating the personalized video, the platform runs independent Speech-to-Text on the synthesized video ($T_{gen}$) and performs bidirectional proposition auditing.
* If fidelity drops below threshold or any critical proposition is missing, generation is **halted and flagged for human review**.

### 3. 🎬 Seamless Neural Video & Lip-Sync Engine
* Integrates **Sync Labs Neural Lip-Sync API** (`lipsync-2` / `sync-3`) for photorealistic mouth movement aligned with synthetic speech.
* Fallback continuous Presentation Timestamp (`setpts`) scaling ensures exact audio-visual synchronization without looping artifacts.

### 4. 🧠 Dynamic Contextual Micro-Quizzes
* 100% dynamically generated multiple-choice and conceptual assessment checkpoints tailored directly to the specific lecture content and student persona.

---

## 🏛️ System Architecture

```text
 ┌──────────────────────┐
 │ Master Video Lecture │ (MP4 / Audio)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Faster-Whisper (STT) │ ──► Master Transcript & Atomic Propositions
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Persona Rewriter     │ ──► Gemini Flash 2.5 / Groq Llama-3.3 70B
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Neural Voice Engine  │ ──► ElevenLabs / Edge-TTS
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Neural Lip-Sync &    │ ──► Sync Labs API + FFmpeg Audio-Video Muxing
 │ Video Compositor     │
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Failsafe STT Audit   │ ──► Dual-STT Semantic Fact Verification
 └──────────┬───────────┘
            │ [Pass: 100% Fidelity]
            ▼
 ┌──────────────────────┐
 │ Interactive Player   │ ──► Real-Time Persona Switching + Dynamic Quizzes
 └──────────────────────┘
```

---

## 📁 Repository Structure

```text
ForOne/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & routing configuration
│   │   ├── config.py            # Environment & storage paths
│   │   ├── database.py          # SQLite schema & seed loader
│   │   ├── routes/
│   │   │   ├── lectures.py      # Master lecture upload & retrieval
│   │   │   ├── personalization.py # Persona variant trigger & streaming
│   │   │   └── failsafe.py      # STT fact audit verification endpoints
│   │   └── services/
│   │       ├── transcription_service.py # Faster-Whisper pipeline
│   │       ├── rewriter_service.py      # Persona script generator (Gemini/Groq)
│   │       ├── tts_service.py           # Neural voice cloning
│   │       ├── video_service.py         # Sync Labs lip-sync & FFmpeg compositor
│   │       ├── failsafe_verifier.py     # Dual-STT fact fidelity auditor
│   │       └── quiz_service.py          # Dynamic assessment generator
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment variable template
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main application container & views
│   │   ├── components/
│   │   │   ├── StudentPlayer.jsx       # Interactive player with persona selector
│   │   │   ├── LectureUploadModal.jsx  # Video ingestion & processing modal
│   │   │   ├── FailsafeAuditModal.jsx  # Side-by-side proposition audit table
│   │   │   ├── QuizModal.jsx           # Dynamic micro-assessment quiz
│   │   │   └── PersonaSelector.jsx     # Persona cards & cognitive customization
│   │   └── index.css            # Modern glassmorphic dark theme
│   ├── package.json
│   └── vite.config.js
│
├── storage/                     # Local storage (media, database)
│   ├── database/.gitkeep
│   ├── lectures/master/.gitkeep
│   └── lectures/personalized/.gitkeep
│
├── docs/                        # Architecture & specifications
│   ├── forone.pdf
│   └── forone.docx
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python 3.10+**
* **Node.js 18+** & `npm`
* **FFmpeg** installed and accessible in your system `PATH` (`brew install ffmpeg` on macOS)

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and supply your free-tier API keys:
# GEMINI_API_KEY=...
# GROQ_API_KEY=...
# ELEVENLABS_API_KEY=...
# SYNCLABS_API_KEY=...

# Start backend server
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API will be available at: **`http://127.0.0.1:8000`**
* Interactive Swagger docs at: **`http://127.0.0.1:8000/docs`**

---

### 2. Frontend Setup

```bash
# In a separate terminal, navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Start Vite dev server
npm run dev -- --host 127.0.0.1 --port 5174
```
* Frontend application will be available at: **`http://127.0.0.1:5174`**

---

## 🔒 Security & Privacy Notice
* Sensitive API keys and credentials are stored strictly in local `.env` files that are **git-ignored** by default.
* Never commit `.env` or production credentials to source control.
* Generated user video artifacts are persisted locally in `storage/` and excluded from repository commits.

---

## 📄 License
This project is licensed under the MIT License.
