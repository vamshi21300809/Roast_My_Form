import html
import re
from pathlib import Path

import streamlit as st
from PIL import Image

from components import gauge_html
from gemini_engine import get_form_roast


# ------------------------------------------------------------
# PAGE CONFIG
# Must be the first Streamlit command.
# ------------------------------------------------------------

st.set_page_config(
    page_title="Roast My Form | AI Biomechanics Coach",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

CSS_FILE = BASE_DIR / "style.css"
HTML_FILE = BASE_DIR / "ui.html"


# ------------------------------------------------------------
# LOAD CSS
# ------------------------------------------------------------

def load_css(path: Path):
    try:
        css = path.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        st.warning("⚠️ style.css not found.")


# ------------------------------------------------------------
# LOAD HTML
# ------------------------------------------------------------

def load_html(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        st.error("❌ ui.html not found.")
        return ""


load_css(CSS_FILE)

HTML_CONTENT = load_html(HTML_FILE)


# ------------------------------------------------------------
# HTML TEMPLATE HELPERS
# ------------------------------------------------------------

def get_template(template_id: str) -> str:
    pattern = (
        rf'<template\s+id=["\']{re.escape(template_id)}["\'][^>]*>'
        r"(.*?)"
        r"</template>"
    )

    match = re.search(
        pattern,
        HTML_CONTENT,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return ""


def get_hero_html() -> str:
    return re.sub(
        r"<template\b[^>]*>.*?</template>",
        "",
        HTML_CONTENT,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()


HERO_HTML = get_hero_html()

FIX_TEMPLATE = get_template("fix-template")
FLAW_TEMPLATE = get_template("flaw-template")
ROAST_TEMPLATE = get_template("roast-template")


# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------

st.session_state.setdefault("roast_result", None)
st.session_state.setdefault("captured_image", None)
st.session_state.setdefault("history", [])


# ------------------------------------------------------------
# HERO
# ------------------------------------------------------------

if HERO_HTML:
    st.html(HERO_HTML)


# ------------------------------------------------------------
# MAIN LAYOUT
# ------------------------------------------------------------

left, right = st.columns(
    [1, 1.15],
    gap="large",
)


# ============================================================
# LEFT SIDE
# ============================================================

with left:

    st.markdown(
        '<div class="panel-label">01 · SET UP</div>',
        unsafe_allow_html=True,
    )

    with st.form(
        "roast_form",
        clear_on_submit=False,
    ):

        exercise = st.selectbox(
            "Exercise",
            [
                "Push-up",
                "Squat",
                "Plank",
                "Deadlift (starting stance)",
            ],
        )

        experience = st.select_slider(
            "Experience level",
            options=[
                "Beginner",
                "Intermediate",
                "Advanced",
            ],
            value="Beginner",
        )

        camera_photo = st.camera_input(
            "📷 Take a photo"
        )

        uploaded_photo = st.file_uploader(
            "OR upload a workout photo",
            type=[
                "jpg",
                "jpeg",
                "png",
            ],
        )

        roast_intensity = st.slider(
            "Roast intensity 🔥",
            min_value=1,
            max_value=5,
            value=3,
            help="1 = gentle coach, 5 = brutal coach",
        )

        submitted = st.form_submit_button(
            "🔥 ROAST MY FORM",
            use_container_width=True,
        )


# ------------------------------------------------------------
# SELECT IMAGE
# ------------------------------------------------------------

if uploaded_photo is not None:
    photo = uploaded_photo

elif camera_photo is not None:
    photo = camera_photo

else:
    photo = None


# ------------------------------------------------------------
# PROCESS FORM
# ------------------------------------------------------------

if submitted:

    if photo is None:

        st.error(
            "❌ Please take or upload a photo first."
        )

    else:

        try:

            img = Image.open(photo).convert("RGB")

            st.session_state.captured_image = img.copy()

            with st.spinner(
                "🔥 Coach Roast is analyzing your form..."
            ):

                result = get_form_roast(
                    image=img,
                    exercise=exercise,
                    experience=experience,
                    intensity=roast_intensity,
                )

            st.session_state.roast_result = result

            try:
                score = int(
                    result.get("score", 0)
                )
            except (
                ValueError,
                TypeError,
            ):
                score = 0

            st.session_state.history.insert(
                0,
                {
                    "exercise": exercise,
                    "score": score,
                },
            )

            st.session_state.history = (
                st.session_state.history[:5]
            )

            if result.get("error"):

                st.warning(
                    "⚠️ Gemini returned an error. "
                    "Check the verdict panel."
                )

            else:

                st.success(
                    "✅ Analysis complete!"
                )

        except Exception as exc:

            st.error(
                f"❌ Error processing the image: {exc}"
            )


# ============================================================
# RIGHT SIDE
# ============================================================

with right:

    st.markdown(
        '<div class="panel-label">02 · VERDICT</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # EMPTY STATE
    # --------------------------------------------------------

    if st.session_state.roast_result is None:

        st.html(
            """
            <div class="empty-state">
                <div class="empty-icon">🦴</div>

                <p>
                    Your roast will appear here.
                    <br>
                    No mercy. No blue theme.
                    <br>
                    Just biomechanics.
                </p>
            </div>
            """
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    else:

        result = st.session_state.roast_result

        image_col, score_col = st.columns(
            [1, 1]
        )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        with image_col:

            if (
                st.session_state.captured_image
                is not None
            ):

                st.image(
                    st.session_state.captured_image,
                    use_container_width=True,
                )

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        with score_col:

            try:

                score = int(
                    result.get(
                        "score",
                        0,
                    )
                )

            except (
                ValueError,
                TypeError,
            ):

                score = 0

            score = max(
                0,
                min(
                    100,
                    score,
                ),
            )

            delta = score - 70

            st.metric(
                "FORM SCORE",
                f"{score}/100",
                f"{delta:+d} vs baseline",
            )

            st.components.v1.html(
                gauge_html(score),
                height=180,
                scrolling=False,
            )

        # ----------------------------------------------------
        # ROAST
        # ----------------------------------------------------

        st.markdown(
            "#### 🔥 The Roast"
        )

        roast = str(
            result.get(
                "roast",
                "No roast returned.",
            )
        )

        if ROAST_TEMPLATE:

            roast_html = ROAST_TEMPLATE.replace(
                "{{ROAST}}",
                html.escape(roast),
            )

            st.html(roast_html)

        else:

            st.write(roast)

        # ----------------------------------------------------
        # FLAWS
        # ----------------------------------------------------

        st.markdown(
            "#### 🩻 Flaws Detected"
        )

        flaws = result.get(
            "flaws",
            [],
        )

        if not isinstance(
            flaws,
            list,
        ):
            flaws = []

        if not flaws:

            st.info(
                "No flaws were returned."
            )

        else:

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

                name = html.escape(
                    str(
                        flaw.get(
                            "name",
                            "Unknown",
                        )
                    )
                )

                detail = html.escape(
                    str(
                        flaw.get(
                            "detail",
                            "",
                        )
                    )
                )

                if FLAW_TEMPLATE:

                    flaw_html = (
                        FLAW_TEMPLATE
                        .replace(
                            "{{SEVERITY}}",
                            severity,
                        )
                        .replace(
                            "{{SEVERITY_UPPER}}",
                            severity.upper(),
                        )
                        .replace(
                            "{{NAME}}",
                            name,
                        )
                        .replace(
                            "{{DETAIL}}",
                            detail,
                        )
                    )

                    st.html(
                        flaw_html
                    )

                else:

                    st.write(
                        f"**{name}** — {detail}"
                    )

        # ----------------------------------------------------
        # FIXES
        # ----------------------------------------------------

        st.markdown(
            "#### ✅ Fix-It Plan"
        )

        fixes = result.get(
            "fixes",
            [],
        )

        if not isinstance(
            fixes,
            list,
        ):
            fixes = []

        if not fixes:

            st.info(
                "No fixes were returned."
            )

        else:

            for i, tip in enumerate(
                fixes,
                start=1,
            ):

                safe_tip = html.escape(
                    str(tip)
                )

                if FIX_TEMPLATE:

                    fix_html = (
                        FIX_TEMPLATE
                        .replace(
                            "{{NUMBER}}",
                            f"{i:02d}",
                        )
                        .replace(
                            "{{TIP}}",
                            safe_tip,
                        )
                    )

                    st.html(
                        fix_html
                    )

                else:

                    st.write(
                        f"{i}. {tip}"
                    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### 📜 Recent Roasts"
    )

    if not st.session_state.history:

        st.caption(
            "Nothing yet. Get roasted."
        )

    else:

        for item in st.session_state.history:

            exercise_name = item.get(
                "exercise",
                "Unknown",
            )

            score = item.get(
                "score",
                "-",
            )

            st.write(
                f"**{exercise_name}** — "
                f"{score}/100"
            )