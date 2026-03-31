# SafeGuard360 — System Architecture

## Overview

SafeGuard360 is an MCP server exposing two AI-powered clinical tools, deployed on the Prompt Opinion platform.

## Data Flow

```
FHIR Patient Data (mock JSON)
        ↓
  MCP Server (FastAPI)
        ↓
  ┌─────────────────────┐
  │   Groq API          │
  │   Llama 3.3 70B     │
  └─────────────────────┘
        ↓
  ┌──────────────┬──────────────────┐
  │ Polypharmacy │  ICU Warning     │
  │ Risk Checker │  System          │
  └──────────────┴──────────────────┘
        ↓
  Unified Safety Dashboard (React)
        ↓
  Prompt Opinion Marketplace
```

## MCP Tools

### Tool 1: check_polypharmacy_risk
- Input: FHIR MedicationRequest bundle
- Process: Groq AI analyzes all drug combinations
- Output: Risk level, interactions list, patient explanation

### Tool 2: check_icu_vitals
- Input: FHIR Observation bundle (real-time vitals)
- Process: NEWS2 scoring + Groq AI pattern detection
- Output: Deterioration score, sepsis risk, nurse alert

## Standards Used

- **FHIR R4** — Patient, MedicationRequest, Observation resources
- **MCP** — Model Context Protocol for tool exposure
- **A2A** — Agent-to-Agent communication via Prompt Opinion
- **SHARP** — Context propagation for patient ID + FHIR tokens

## Why Groq?

In clinical settings, response time is a safety requirement.
Groq's LPU architecture delivers sub-second inference — critical
for real-time ICU monitoring where every second matters.
