from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json, os, logging

from .tools.polypharmacy import check_polypharmacy_risk
from .tools.icu_warning import check_icu_warning

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = FastAPI(
    title="SafeGuard360 — Patient Safety Agent",
    description="Dual-function AI patient safety MCP server: Polypharmacy Risk Checker + ICU Early Warning System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.promptopinion.ai", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FHIR_SERVER_URL = os.environ.get("FHIR_SERVER_URL", "http://localhost:8000/fhir")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)

def get_sharp_context(request: Request):
    """Extract patient_id and fhir_token from SHARP context header."""
    sharp_header = request.headers.get("X-SHARP-Context")
    if sharp_header:
        try:
            context = json.loads(sharp_header)
            patient_id = context.get("patient_id")
            fhir_token = context.get("fhir_token")
            logging.info(f"SHARP context extracted: patient_id={patient_id}, fhir_token={'present' if fhir_token else 'none'}")
            return patient_id, fhir_token
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse SHARP context header: {e}")
    return None, None

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
async def polypharmacy_tool(request: Request):
    """
    MCP Tool: check_polypharmacy_risk
    Ingests FHIR medication list and returns AI-powered drug interaction analysis.
    """
    # Optional API key check - allow requests without it for testing
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Parse request body
    try:
        req_body = await request.json()
    except:
        req_body = {}
    patient_id = req_body.get("patient_id", "patient-001")
    
    # Extract SHARP context
    sharp_patient_id, fhir_token = get_sharp_context(request)
    patient_id = sharp_patient_id or patient_id
    
    # Load data (mock for now; in production, fetch from FHIR server using token)
    medications = load_json("medications.json")
    patient = load_json("patient.json")
    
    result = await check_polypharmacy_risk(patient, medications)
    result["patient_id_used"] = patient_id  # Log which patient ID was used
    return result


@app.post("/tools/icu-warning")
async def icu_warning_tool(request: Request):
    """
    MCP Tool: check_icu_vitals
    Ingests FHIR vitals observations and returns deterioration risk assessment.
    """
    # Optional API key check - allow requests without it for testing
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Parse request body
    try:
        req_body = await request.json()
    except:
        req_body = {}
    patient_id = req_body.get("patient_id", "patient-001")
    
    # Extract SHARP context
    sharp_patient_id, fhir_token = get_sharp_context(request)
    patient_id = sharp_patient_id or patient_id
    
    # Load data (mock for now; in production, fetch from FHIR server using token)
    observations = load_json("observations.json")
    patient = load_json("patient.json")
    
    result = await check_icu_warning(patient, observations)
    result["patient_id_used"] = patient_id  # Log which patient ID was used
    return result


@app.api_route("/mcp/manifest", methods=["GET", "POST", "HEAD", "OPTIONS"])
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
                "method": "POST",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "The ID of the patient to analyze"
                        }
                    },
                    "required": ["patient_id"]
                }
            },
            {
                "name": "check_icu_vitals",
                "description": "Monitors ICU vitals and detects early sepsis / deterioration patterns",
                "endpoint": "/tools/icu-warning",
                "method": "POST",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "The ID of the patient to analyze"
                        }
                    },
                    "required": ["patient_id"]
                }
            }
        ]
    }
