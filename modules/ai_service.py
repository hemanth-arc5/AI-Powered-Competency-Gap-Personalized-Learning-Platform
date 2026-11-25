"""AI layer (Member 3).

Public functions (agreed contract with Member 1):
    generate_learning_plan(target_role, hours_per_week, skill_scores, resources, prerequisites=None)
    generate_practice_questions(skill_name, difficulty="medium", n=5, target_role="")

Both return: {"ok": bool, "data": dict | None, "error": str | None, "source": "ai" | "fallback"}
They never raise. The app stays usable if AI fails.

skill_scores: list of {"skill_id","skill_name","current","target","gap","priority"}
resources:    list of {"resource_id","skill_id","title","url","level","type","duration"}  (duration in minutes)
"""
import json
import os
import re
import time

from modules.prompts import plan_prompt, quiz_prompt

MODEL = "gemini-3.5-flash-lite"
TIMEOUT_MS = 30000
PLAN_KEYS = {"week", "skill_id", "topic", "objective", "activity",
             "resource_id", "estimated_minutes", "checkpoint"}


class AIError(Exception):
    pass


def get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def _call_llm(prompt, retries=2):
    key = get_api_key()
    if not key:
        raise AIError("AI key not found. Set GEMINI_API_KEY.")
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise AIError("Package missing. Run: pip install google-genai")

    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
    config = types.GenerateContentConfig(response_mime_type="application/json")
    last = "Unknown AI error."
    for attempt in range(retries + 1):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt, config=config)
            return _parse_json(resp.text)
        except json.JSONDecodeError:
            last = "Model returned invalid JSON."
        except Exception as e:
            msg = str(e)
            if "429" in msg or "quota" in msg.lower():
                raise AIError("AI quota reached. Try again later.")
            if "401" in msg or "403" in msg or "API key" in msg:
                raise AIError("AI key rejected. Check GEMINI_API_KEY.")
            last = f"AI request failed: {msg[:120]}"
        time.sleep(1.5 * (attempt + 1))
    raise AIError(last)


# ---------- validation ----------

def validate_plan(plan, resources, hours_per_week):
    if not isinstance(plan, dict) or "summary" not in plan or "weeks" not in plan:
        raise AIError("Plan missing summary or weeks.")
    if not isinstance(plan["weeks"], list) or not plan["weeks"]:
        raise AIError("Plan has no weeks.")
    valid_ids = {r["resource_id"] for r in resources}
    max_minutes = hours_per_week * 60 * 1.1
    for w in plan["weeks"]:
        missing = PLAN_KEYS - set(w)
        if missing:
            raise AIError(f"Week missing fields: {sorted(missing)}")
        if w["resource_id"] is not None and w["resource_id"] not in valid_ids:
            w["resource_id"] = None  # drop invented resource
        
        # --- REPLACE THE OLD 2 LINES WITH THIS ---
        est = w["estimated_minutes"]
        if not isinstance(est, (int, float)) or est <= 0 or est > max_minutes * 3:
            raise AIError("Week exceeds available study time.")
        if est > max_minutes:
            w["estimated_minutes"] = int(hours_per_week * 60)
        # -----------------------------------------

    plan.setdefault("disclaimer", "Recommendations are guidance. Verify resource links.")
    return plan


def validate_questions(data, n):
    qs = data.get("questions") if isinstance(data, dict) else None
    if not qs:
        raise AIError("No questions returned.")
    clean = []
    for q in qs:
        opts = q.get("options")
        if (isinstance(opts, list) and len(opts) == 4 and len(set(opts)) == 4
                and q.get("correct_answer") in opts and q.get("question") and q.get("explanation")):
            clean.append(q)
    if not clean:
        raise AIError("All generated questions were invalid.")
    return {"questions": clean[:n]}


# ---------- fallback (no AI) ----------

def fallback_plan(target_role, hours_per_week, skill_scores, resources):
    order = {"High": 0, "Medium": 1}
    gaps = sorted((s for s in skill_scores if s.get("priority") in order),
                  key=lambda s: (order[s["priority"]], -s["gap"]))
    weeks = []
    for i, s in enumerate(gaps, 1):
        match = next((r for r in resources if r["skill_id"] == s["skill_id"]), None)
        weeks.append({
            "week": i, "skill_id": s["skill_id"], "topic": s["skill_name"],
            "objective": f"Close the {s['skill_name']} gap.",
            "activity": "Study the resource and practise." if match else "No curated resource available.",
            "resource_id": match["resource_id"] if match else None,
            "estimated_minutes": int(min(hours_per_week * 60, (match or {}).get("duration", 120))),
            "checkpoint": f"Take a short {s['skill_name']} quiz.",
        })
    names = ", ".join(s["skill_name"] for s in gaps) or "none"
    return {"summary": f"Priority gaps for {target_role}: {names}. (Rule-based plan, AI unavailable.)",
            "weeks": weeks,
            "disclaimer": "Recommendations are guidance. Verify resource links."}


# ---------- public API ----------

def generate_learning_plan(target_role, hours_per_week, skill_scores, resources, prerequisites=None):
    if not skill_scores:
        return {"ok": False, "data": None, "error": "No scores provided.", "source": None}

    active_gaps = [s for s in skill_scores if s.get("gap", 0) > 0]
    if not active_gaps:
        return {
            "ok": True,
            "data": {
                "summary": f"Congratulations! You already meet all target competencies for {target_role}.",
                "weeks": [],
                "disclaimer": "Recommendations are guidance. Verify resource links."
            },
            "error": None,
            "source": "ai"
        }
    
    try:
        prompt = plan_prompt(target_role, hours_per_week, skill_scores, resources, prerequisites)
        plan = validate_plan(_call_llm(prompt), resources, hours_per_week)
        return {"ok": True, "data": plan, "error": None, "source": "ai"}
    except AIError as e:
        return {"ok": True, "data": fallback_plan(target_role, hours_per_week, skill_scores, resources),
                "error": str(e), "source": "fallback"}


def generate_practice_questions(skill_name, difficulty="medium", n=5, target_role=""):
    try:
        data = validate_questions(_call_llm(quiz_prompt(skill_name, difficulty, n, target_role)), n)
        return {"ok": True, "data": data, "error": None, "source": "ai"}
    except AIError as e:
        return {"ok": False, "data": None, "error": str(e), "source": None}