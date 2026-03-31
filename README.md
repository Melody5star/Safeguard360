# SafeGuard360 — AI Patient Safety Agent

> *"Catch the danger before it becomes a disaster."*

SafeGuard360 is a dual-function AI patient safety agent built on the **Prompt Opinion** platform, combining two critical clinical tools into one interoperable MCP server.

---

## 🏆 Hackathon Submission

**Agents Assemble — The Healthcare AI Endgame**
- Platform: [Devpost](https://agents-assemble.devpost.com)
- Prize Pool: $25,000
- Deadline: May 11, 2026

---

## 🔍 What It Does

### 💊 Polypharmacy Risk Checker
Ingests a patient's FHIR medication list and uses AI to detect dangerous drug-drug interactions. Flags them with severity scores and plain-language explanations for both clinicians and patients.

### 🏥 ICU Early Warning System
Monitors real-time FHIR vitals observations (heart rate, blood pressure, temperature, SpO2, respiratory rate), scores deterioration patterns, and detects early sepsis indicators — triggering nurse escalation before a patient crashes.

### ✨ What Makes SafeGuard360 Different

What makes SafeGuard360 different is not just what it catches, but how fast and how accessibly it communicates risk. Powered by Groq's ultra-fast inference and fully compliant with FHIR and SHARP standards, it plugs directly into any clinician's workspace through the Prompt Opinion Marketplace — no custom integration required.

This is AI doing what rule-based software never could: reasoning across complex, interconnected clinical data to protect patients at the exact moment it matters most.

---

## 🛠 Tech Stack

| Category | Technology |
|---|---|
| AI / LLM | Groq API — Llama 3.3 70B |
| Agent Platform | Prompt Opinion (MCP + A2A) |
| Data Standard | FHIR R4 (HL7) |
| Context Protocol | SHARP Extension Specs |
| Backend / MCP Server | Python 3.11, FastAPI |
| Frontend / Dashboard | React 18, TailwindCSS |
| Deployment | Prompt Opinion Marketplace + Vercel |

---

## 📁 Project Structure

```
safeguard360/
├── backend/
│   ├── main.py              # FastAPI + MCP server entry point
│   ├── tools/
│   │   ├── polypharmacy.py  # Drug interaction checker tool
│   │   └── icu_warning.py   # ICU early warning tool
│   └── data/
│       ├── patient.json     # Mock FHIR patient profile
│       ├── medications.json # Mock FHIR medication list
│       └── observations.json# Mock FHIR vitals observations
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React dashboard
│   │   └── main.jsx         # React entry point
│   ├── index.html
│   └── package.json
├── demo/
│   └── safeguard360-teaser.html  # Animated teaser presentation
├── docs/
│   └── architecture.md      # System architecture notes
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR-USERNAME/safeguard360.git
cd safeguard360
```

### 2. Set up environment
```bash
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

### 3. Install backend dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the MCP server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Install & run frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 Environment Variables

```
GROQ_API_KEY=your_groq_api_key_here
PROMPT_OPINION_API_KEY=your_prompt_opinion_key_here
FHIR_SERVER_URL=http://localhost:8000/fhir  # or real FHIR endpoint
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/tools/polypharmacy` | Check drug interactions for a patient |
| POST | `/tools/icu-warning` | Assess ICU vitals for deterioration |
| GET  | `/patient/{id}` | Fetch mock patient FHIR bundle |
| GET  | `/health` | Health check |

---

## 🎥 Demo

[Watch Demo Video](https://youtube.com/YOUR-VIDEO-LINK)

[Live on Prompt Opinion Marketplace](https://app.promptopinion.ai/marketplace/safeguard360)

---

## ⚠️ Disclaimer

This project uses **mock FHIR data only**. It is a proof-of-concept built for a hackathon. It is not intended for use in real clinical settings without proper validation, regulatory approval, and integration with certified EHR systems.

---

## 📄 License

MIT License — see LICENSE file for details.
