import json
import os
from typing import Any

import streamlit as st
from google import genai


# ------------------------------------------------------------
# API KEY
# ------------------------------------------------------------

API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    API_KEY = os.environ.get("GEMINI_API_KEY")


if not API_KEY:
    st.error(
        "⚠️ GEMINI_API_KEY not found.\n\n"
        "Add your Gemini API key to:\n"
        ".streamlit/secrets.toml"
    )
    st.stop()


# ------------------------------------------------------------
# GEMINI CLIENT
# ------------------------------------------------------------

client = genai.Client(
    api_key=API_KEY
)


# ------------------------------------------------------------
# MODEL
# ------------------------------------------------------------

MODEL_NAME = os.environ.get(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


# ------------------------------------------------------------
# PROMPT
# ------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = r"""
You are "Coach Roast", a savage but genuinely knowledgeable
strength and conditioning coach.

Analyze the user's STARTING posture for this exercise.

Exercise: {exercise}

Experience level: {experience}

Roast intensity: {intensity}/5

Analyze ONLY what is visible in the image.

Check:

- Spine alignment
- Joint stacking
- Foot placement
- Hand placement
- Hip position
- Neck position
- Exercise-specific posture problems

Do not invent flaws that are not visible.

Return STRICT JSON ONLY.

Use exactly this structure:

{{
    "score": 0,

    "roast": "",

    "flaws": [
        {{
            "name": "",
            "detail": "",
            "severity": "low"
        }}
    ],

    "fixes": [
        ""
    ]
}}

Rules:

- score must be an integer from 0 to 100
- roast should be 2 to 4 sentences
- roast the FORM, never the person's body
- flaws should contain 2 to 5 items when visible
- fixes should contain 3 to 5 actionable tips
- severity must be low, medium, or high
- analyze only visible information
- return JSON only
"""


# ------------------------------------------------------------
# NORMALISE RESPONSE
# ------------------------------------------------------------

def _normalise(data: Any) -> dict:

    if not isinstance(
        data,
        dict,
    ):

        raise ValueError(
            "Gemini returned JSON, "
            "but it was not an object."
        )


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    try:

        score = int(
            data.get(
                "score",
                50,
            )
        )

    except (
        ValueError,
        TypeError,
    ):

        score = 50


    score = max(
        0,
        min(
            100,
            score,
        ),
    )


    # --------------------------------------------------------
    # ROAST
    # --------------------------------------------------------

    roast = str(
        data.get(
            "roast",
            "Coach is speechless. Try again.",
        )
    )


    # --------------------------------------------------------
    # FLAWS
    # --------------------------------------------------------

    flaws = data.get(
        "flaws",
        [],
    )

    if not isinstance(
        flaws,
        list,
    ):

        flaws = []


    clean_flaws = []


    for flaw in flaws:

        if not isinstance(
            flaw,
            dict,
        ):
            continue


        severity = str(
            flaw.get(
                "severity",
                "low",
            )
        ).lower()


        if severity not in {
            "low",
            "medium",
            "high",
        }:

            severity = "low"


        clean_flaws.append(
            {
                "name": str(
                    flaw.get(
                        "name",
                        "Unknown",
                    )
                ),

                "detail": str(
                    flaw.get(
                        "detail",
                        "",
                    )
                ),

                "severity": severity,
            }
        )


    # --------------------------------------------------------
    # FIXES
    # --------------------------------------------------------

    fixes = data.get(
        "fixes",
        [],
    )

    if not isinstance(
        fixes,
        list,
    ):

        fixes = []


    clean_fixes = [
        str(fix).strip()
        for fix in fixes
        if str(fix).strip()
    ]


    return {
        "score": score,
        "roast": roast,
        "flaws": clean_flaws,
        "fixes": clean_fixes,
    }


# ------------------------------------------------------------
# MAIN GEMINI FUNCTION
# ------------------------------------------------------------

def get_form_roast(
    image,
    exercise: str,
    experience: str,
    intensity: int,
) -> dict:

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        exercise=exercise,
        experience=experience,
        intensity=intensity,
    )


    try:

        response = client.models.generate_content(
            model=MODEL_NAME,

            contents=[
                prompt,
                image,
            ],

            config={
                "response_mime_type": "application/json",
            },
        )


        raw_text = (
            response.text or ""
        ).strip()


        if not raw_text:

            raise ValueError(
                "Gemini returned an empty response."
            )


        data = json.loads(
            raw_text
        )


        return _normalise(data)


    except json.JSONDecodeError as exc:

        return {
            "score": 0,

            "roast": (
                "Gemini returned invalid JSON. "
                f"Parser error: {exc}"
            ),

            "flaws": [],

            "fixes": [
                "Try taking the photo again.",
                "Make sure your entire starting posture is visible.",
                "Use a clearer, well-lit image.",
            ],

            "error": True,
        }


    except Exception as exc:

        return {
            "score": 0,

            "roast": (
                "Coach dropped the clipboard. "
                f"Gemini error: {exc}"
            ),

            "flaws": [],

            "fixes": [
                "Check your GEMINI_API_KEY.",
                "Make sure google-genai is installed.",
                "Check that the selected Gemini model is available.",
                "Try uploading the image again.",
            ],

            "error": True,
        }
