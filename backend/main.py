from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json, os

from tools.polypharmacy import check_polypharmacy_risk
from tools.icu_warning import check_icu_warning

load_dotenv()

app = FastAPI(
    title="SafeGuard360 — Patient Safety Agent",
    description="Dual-function AI patient safety MCP server: Polypharmacy Risk Checker + ICU Early Warning System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


class PatientRequest(BaseModel):
    patient_id: str = "patient-001"


@app.get("/health")
def health_check():
    return {"status": "ok", "agent": "SafeGuard360", "version": "1.0.0"}


@app.get("/patient/{patient_id}")
def get_patient(patient_id: str):
    """Return full mock FHIR bundle for a patient."""
    try:
        patient = load_json("patient.json")
        medications = load_json("medications.json")
        observations = load_json("observations.json")
        return {
            "patient": patient,
            "medications": medications,
            "observations": observations
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Patient not found")


@app.post("/tools/polypharmacy")
async def polypharmacy_tool(req: PatientRequest):
    """
    MCP Tool: check_polypharmacy_risk
    Ingests FHIR medication list and returns AI-powered drug interaction analysis.
    """
    medications = load_json("medications.json")
    patient = load_json("patient.json")
    result = await check_polypharmacy_risk(patient, medications)
    return result


@app.post("/tools/icu-warning")
async def icu_warning_tool(req: PatientRequest):
    """
    MCP Tool: check_icu_vitals
    Ingests FHIR vitals observations and returns deterioration risk assessment.
    """
    observations = load_json("observations.json")
    patient = load_json("patient.json")
    result = await check_icu_warning(patient, observations)
    return result


@app.get("/mcp/manifest")
def mcp_manifest():
    """Prompt Opinion MCP tool manifest."""
    return {
        "name": "safeguard360",
        "description": "AI patient safety agent — polypharmacy checker + ICU early warning",
        "version": "1.0.0",
        "tools": [
            {
                "name": "check_polypharmacy_risk",
                "description": "Analyzes a patient FHIR medication list for dangerous drug interactions",
                "endpoint": "/tools/polypharmacy",
                "method": "POST"
            },
            {
                "name": "check_icu_vitals",
                "description": "Monitors ICU vitals and detects early sepsis / deterioration patterns",
                "endpoint": "/tools/icu-warning",
                "method": "POST"
            }
        ]
    }
