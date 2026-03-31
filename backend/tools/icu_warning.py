import os
import json
from groq import AsyncGroq

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are SafeGuard360's ICU Early Warning System — a clinical AI assistant.

Your job is to analyze a patient's real-time vitals and detect deterioration patterns including early sepsis, respiratory failure, and cardiovascular collapse.

Always respond in valid JSON with this exact structure:
{
  "risk_level": "CRITICAL" | "HIGH" | "MODERATE" | "LOW" | "STABLE",
  "deterioration_score": 0-10,
  "sepsis_risk": "HIGH" | "MODERATE" | "LOW" | "NONE",
  "abnormal_vitals": [
    {
      "vital": "...",
      "value": "...",
      "normal_range": "...",
      "concern": "..."
    }
  ],
  "pattern_detected": "...",
  "escalation_required": true | false,
  "escalation_message": "...",
  "recommended_actions": ["...", "..."],
  "nurse_alert": "..."
}

Rules:
- Be conservative: when in doubt, escalate
- A deterioration_score >= 6 should always trigger escalation_required: true
- Sepsis criteria: 2+ of (HR>90, Temp>38 or <36, RR>20, suspected infection)
- nurse_alert must be short, clear, actionable — max 2 sentences
- Never suggest definitive diagnoses — always recommend clinical confirmation
"""

def calculate_news2_score(vitals: dict) -> int:
    """Simplified NEWS2 early warning score calculation."""
    score = 0
    hr = vitals.get("heartRate", {}).get("value", 0)
    temp = vitals.get("temperature", {}).get("value", 0)
    rr = vitals.get("respiratoryRate", {}).get("value", 0)
    spo2 = vitals.get("spO2", {}).get("value", 100)
    bp_sys = vitals.get("bloodPressure", {}).get("systolic", 120)

    if hr > 130 or hr < 40: score += 3
    elif hr > 110: score += 2
    elif hr > 90 or hr < 50: score += 1

    if rr > 24 or rr < 8: score += 3
    elif rr > 20: score += 2
    elif rr > 11: score += 1

    if spo2 < 91: score += 3
    elif spo2 < 94: score += 2
    elif spo2 < 96: score += 1

    if temp > 39 or temp < 35: score += 2
    elif temp > 38 or temp < 36: score += 1

    if bp_sys < 90: score += 3
    elif bp_sys < 100: score += 2
    elif bp_sys > 220: score += 3

    return min(score, 10)


async def check_icu_warning(patient: dict, observations: dict) -> dict:
    """
    Uses Groq Llama 3.3 to analyze ICU vitals for deterioration patterns.
    """
    patient_name = patient.get("name", [{}])[0].get("text", "Patient")
    vitals = observations.get("vitals", {})
    news2 = calculate_news2_score(vitals)
    sepsis = observations.get("sepsisIndicators", {})

    vitals_summary = f"""
Heart Rate: {vitals.get('heartRate', {}).get('value')} bpm (normal: 60-100)
Blood Pressure: {vitals.get('bloodPressure', {}).get('systolic')}/{vitals.get('bloodPressure', {}).get('diastolic')} mmHg (normal: 90-120/60-80)
Temperature: {vitals.get('temperature', {}).get('value')}°C (normal: 36.5-37.5)
Respiratory Rate: {vitals.get('respiratoryRate', {}).get('value')} breaths/min (normal: 12-20)
SpO2: {vitals.get('spO2', {}).get('value')}% (normal: 95-100%)
Consciousness: {vitals.get('consciousnessLevel', {}).get('value', 'Unknown')}
Calculated NEWS2 Score: {news2}/10
Sepsis Indicators Active: {sepsis.get('score', 0)} of {sepsis.get('maxScore', 5)}
"""

    user_message = f"""
Patient: {patient_name}, Age: {patient.get('age', 'unknown')}
Timestamp: {observations.get('timestamp')}

Current ICU Vitals:
{vitals_summary}

Please analyze these vitals for deterioration patterns and return your risk assessment as JSON.
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
        result["tool"] = "icu_early_warning"
        result["patient_id"] = patient.get("id")
        result["news2_score"] = news2
        result["timestamp"] = observations.get("timestamp")
        return result

    except Exception as e:
        return {
            "tool": "icu_early_warning",
            "error": str(e),
            "risk_level": "UNKNOWN",
            "escalation_required": True,
            "message": "Analysis failed — escalate manually as precaution."
        }
