from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
import json, os, logging
import httpx

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

async def fetch_fhir_resource(fhir_url: str, token: str, resource_type: str, patient_id: str):
    """Fetch a FHIR R4 resource from a real server using PromptOpinion-provided credentials."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/fhir+json"}
    async with httpx.AsyncClient(timeout=10) as client:
        if resource_type == "Patient":
            resp = await client.get(f"{fhir_url}/Patient/{patient_id}", headers=headers)
        else:
            resp = await client.get(f"{fhir_url}/{resource_type}?patient={patient_id}", headers=headers)
        resp.raise_for_status()
        return resp.json()

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


MCP_TOOLS = [
    {
        "name": "check_polypharmacy_risk",
        "description": "Analyzes a patient FHIR medication list for dangerous drug interactions and polypharmacy risks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to analyze (default: patient-001)"
                }
            }
        }
    },
    {
        "name": "check_icu_vitals",
        "description": "Monitors ICU vitals and detects early sepsis or patient deterioration using NEWS2 scoring",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID to analyze (default: patient-001)"
                }
            }
        }
    }
]


@app.api_route("/mcp/manifest", methods=["GET", "POST", "HEAD", "OPTIONS"])
def mcp_manifest():
    """Legacy static manifest — kept for reference."""
    return {
        "name": "safeguard360",
        "description": "AI patient safety agent — polypharmacy checker + ICU early warning",
        "version": "1.0.0",
        "tools": MCP_TOOLS
    }


@app.api_route("/mcp", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def mcp_endpoint(request: Request):
    """MCP Streamable HTTP transport — JSON-RPC 2.0 handler for Prompt Opinion."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return {"name": "safeguard360", "version": "1.0.0", "protocolVersion": "2024-11-05"}

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
        )

    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "extensions": {
                        "ai.promptopinion/fhir-context": {
                            "scopes": [
                                {"name": "patient/Patient.rs", "required": True},
                                {"name": "patient/MedicationRequest.rs", "required": True},
                                {"name": "patient/Observation.rs", "required": True},
                                {"name": "patient/Condition.rs"}
                            ]
                        }
                    }
                },
                "serverInfo": {"name": "safeguard360", "version": "1.0.0"}
            }
        }

    if method in ("notifications/initialized", "ping"):
        return Response(status_code=204)

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS}}

    if method == "tools/call":
        tool_name = params.get("name")
        patient_id = params.get("arguments", {}).get("patient_id", "patient-001")

        if tool_name not in ("check_polypharmacy_risk", "check_icu_vitals"):
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}

        # Read PromptOpinion FHIR context headers
        fhir_url = request.headers.get("X-FHIR-Server-URL")
        fhir_token = request.headers.get("X-FHIR-Access-Token")
        fhir_patient_id = request.headers.get("X-Patient-ID") or patient_id

        try:
            patient = medications = observations = None
            data_source = "mock"

            if fhir_url and fhir_token:
                try:
                    patient = await fetch_fhir_resource(fhir_url, fhir_token, "Patient", fhir_patient_id)
                    if tool_name == "check_polypharmacy_risk":
                        medications = await fetch_fhir_resource(fhir_url, fhir_token, "MedicationRequest", fhir_patient_id)
                    else:
                        observations = await fetch_fhir_resource(fhir_url, fhir_token, "Observation", fhir_patient_id)
                    data_source = "fhir_server"
                except Exception as fhir_err:
                    logging.warning(f"FHIR fetch failed, using mock data: {fhir_err}")

            # Fall back to mock data for any missing resources
            if patient is None:
                patient = load_json("patient.json")
            if medications is None:
                medications = load_json("medications.json")
            if observations is None:
                observations = load_json("observations.json")

            if tool_name == "check_polypharmacy_risk":
                result = await check_polypharmacy_risk(patient, medications)
            else:
                result = await check_icu_warning(patient, observations)

            result["patient_id_used"] = fhir_patient_id
            result["data_source"] = data_source
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            }
        except Exception as e:
            logging.error(f"MCP tool error: {e}")
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
