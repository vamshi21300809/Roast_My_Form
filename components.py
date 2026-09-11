def gauge_html(score: int) -> str:
    """
    Return an animated SVG score gauge.

    Score is safely clamped to 0-100.
    """

    try:
        pct = int(score)

    except (
        ValueError,
        TypeError,
    ):
        pct = 0

    pct = max(
        0,
        min(
            100,
            pct,
        ),
    )

    circumference = 2 * 3.14159 * 52

    offset = circumference * (
        1 - pct / 100
    )

    if pct < 40:
        color = "#FF3B3B"

    elif pct < 75:
        color = "#FFB020"

    else:
        color = "#3DDC97"

    # Unique ID prevents collisions if Streamlit renders
    # the component more than once.
    gauge_id = f"gauge-ring-{pct}"

    return f"""
    <div
        style="
            display:flex;
            align-items:center;
            justify-content:center;
        "
    >

        <svg
            width="160"
            height="160"
            viewBox="0 0 140 140"
            role="img"
            aria-label="Form score {pct} out of 100"
        >

            <defs>

                <filter
                    id="{gauge_id}-glow"
                    x="-50%"
                    y="-50%"
                    width="200%"
                    height="200%"
                >

                    <feGaussianBlur
                        stdDeviation="4"
                        result="blur"
                    />

                    <feMerge>

                        <feMergeNode in="blur"/>

                        <feMergeNode in="SourceGraphic"/>

                    </feMerge>

                </filter>

            </defs>


            <circle
                cx="70"
                cy="70"
                r="52"
                stroke="#2b2b2b"
                stroke-width="12"
                fill="none"
            />


            <circle
                id="{gauge_id}"
                cx="70"
                cy="70"
                r="52"
                stroke="{color}"
                stroke-width="12"
                fill="none"
                stroke-linecap="round"
                filter="url(#{gauge_id}-glow)"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{circumference}"
                transform="rotate(-90 70 70)"
            />


            <text
                x="70"
                y="78"
                text-anchor="middle"
                font-size="28"
                font-weight="700"
                fill="#F5F5F0"
                font-family="'JetBrains Mono', monospace"
            >
                {pct}
            </text>

        </svg>

    </div>


    <script>

        (() => {{

            const ring =
                document.getElementById(
                    "{gauge_id}"
                );

            if (!ring) {{
                return;
            }}

            const target = {offset};

            const circumference =
                {circumference};

            let current =
                circumference;


            function step() {{

                current +=
                    (target - current)
                    * 0.12;

                ring.setAttribute(
                    "stroke-dashoffset",
                    current
                );


                if (
                    Math.abs(
                        current - target
                    ) > 0.5
                ) {{

                    requestAnimationFrame(
                        step
                    );

                }} else {{

                    ring.setAttribute(
                        "stroke-dashoffset",
                        target
                    );

                }}

            }}


            requestAnimationFrame(step);

        }})();

    </script>
    """
