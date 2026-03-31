import os
import json
from groq import AsyncGroq

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are SafeGuard360's Polypharmacy Risk Checker — a clinical AI assistant.

Your job is to analyze a patient's medication list and identify dangerous drug-drug interactions.

Always respond in valid JSON with this exact structure:
{
  "risk_level": "CRITICAL" | "HIGH" | "MODERATE" | "LOW" | "SAFE",
  "interactions_found": [
    {
      "drug_a": "...",
      "drug_b": "...",
      "severity": "CRITICAL" | "HIGH" | "MODERATE",
      "mechanism": "...",
      "clinical_consequence": "...",
      "recommendation": "..."
    }
  ],
  "overall_summary": "...",
  "action_required": "...",
  "patient_explanation": "..."
}

Rules:
- Be conservative: flag potential risks even if not confirmed
- Never say it is safe if you are uncertain
- Always recommend clinical verification
- Keep patient_explanation in simple, non-technical language
- The patient_explanation should be understandable by a non-medical person
"""

async def check_polypharmacy_risk(patient: dict, medications: dict) -> dict:
    """
    Uses Groq Llama 3.3 to analyze medication list for dangerous interactions.
    """
    patient_name = patient.get("name", [{}])[0].get("text", "Patient")
    conditions = [c["display"] for c in patient.get("conditions", [])]
    med_list = medications.get("medications", [])

    med_summary = "\n".join([
        f"- {m['name']} {m['dose']} {m['frequency']} (for {m.get('indication', 'unspecified')})"
        for m in med_list
    ])

    user_message = f"""
Patient: {patient_name}, Age: {patient.get('age', 'unknown')}
Conditions: {', '.join(conditions)}

Current Medications:
{med_summary}

Please analyze all drug combinations for dangerous interactions and return your assessment as JSON.
"""

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        result["tool"] = "polypharmacy_checker"
        result["patient_id"] = patient.get("id")
        result["medications_analyzed"] = len(med_list)
        return result

    except Exception as e:
        return {
            "tool": "polypharmacy_checker",
            "error": str(e),
            "risk_level": "UNKNOWN",
            "message": "Analysis failed — please retry or escalate manually."
        }
