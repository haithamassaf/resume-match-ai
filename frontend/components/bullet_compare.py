"""Side-by-side original vs rewritten bullet comparison."""

import streamlit as st


def render_bullet_comparison(rewrites: list):
    """Render side-by-side comparison of original and rewritten bullets.

    Args:
        rewrites: List of dicts with 'original', 'rewritten',
                  and optionally 'validation' and 'error' keys.
    """
    if not rewrites:
        st.info("No bullet points were extracted from the resume.")
        return

    for i, item in enumerate(rewrites):
        original = item["original"]
        rewritten = item["rewritten"]
        validation = item.get("validation", {})
        error = item.get("error")

        with st.container():
            st.markdown(f"**Bullet {i + 1}**")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f'<div style="padding:12px;border-radius:8px;'
                    f'background:rgba(128,128,128,0.1);border-left:3px solid #666;'
                    f'font-size:0.9em;">{original}</div>',
                    unsafe_allow_html=True,
                )

            with col2:
                if error:
                    border_color = "#f97316"
                    badge = ' <span style="color:#f97316;font-size:0.75em;">(rewrite failed)</span>'
                elif not validation.get("is_faithful", True):
                    border_color = "#eab308"
                    badge = ' <span style="color:#eab308;font-size:0.75em;">(flagged)</span>'
                else:
                    border_color = "#22c55e"
                    badge = ""

                st.markdown(
                    f'<div style="padding:12px;border-radius:8px;'
                    f"background:rgba(34,197,94,0.07);border-left:3px solid {border_color};"
                    f'font-size:0.9em;">{rewritten}{badge}</div>',
                    unsafe_allow_html=True,
                )

            # Show validation issues if any
            if validation.get("issues"):
                severity = validation.get("severity", "minor")
                icon = "🔴" if severity == "major" else "🟡"
                with st.expander(f"{icon} Validation notes"):
                    for issue in validation["issues"]:
                        st.markdown(f"- {issue}")

            st.markdown("---")
