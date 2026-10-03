"""Shared editorial presentation. Chart values and units remain untouched."""
from base64 import b64encode
from pathlib import Path
import streamlit as st
from config.settings import COLOR_PALETTE

ASSETS = Path(__file__).resolve().parents[2] / "assets"

@st.cache_data
def _stylesheet():
    css = (ASSETS / "editorial.css").read_text()
    for family, filename, weight in [
        ("Manrope", "manrope-latin-wght-normal.woff2", "200 800"),
        ("Instrument Serif", "instrument-serif-latin-400-normal.woff2", "400"),
    ]:
        font = b64encode((ASSETS / "fonts" / filename).read_bytes()).decode()
        css += f"\n@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{font}) format('woff2');font-weight:{weight};font-style:normal;font-display:swap;}}"
    return css


def apply_theme():
    st.html("<style>" + _stylesheet() + "</style>")


def page_intro(title, description):
    st.markdown('<div class="report-eyebrow">CVM / INTELIGÊNCIA FINANCEIRA</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(description)


def plot_chart(fig, **kwargs):
    """Apply only presentation, preserving traces, labels, hover units and data."""
    fig.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Manrope, sans-serif", color="#20384b", size=12),
        colorway=COLOR_PALETTE,
        title=dict(font=dict(family="Manrope, sans-serif", size=15, color="#20384b"), x=0, xanchor="left"),
        margin=dict(l=28, r=28, t=64, b=48),
        legend=dict(font=dict(size=11), bgcolor="rgba(255,255,255,0)"),
        hoverlabel=dict(bgcolor="#102f42", font=dict(color="white", family="Manrope, sans-serif", size=12)),
    )
    # A uniform bar color avoids a redundant continuous legend for sector ranks.
    for trace in fig.data:
        if trace.type == "bar" and trace.marker.colorscale:
            trace.marker.update(color="#14796E", showscale=False)
    fig.update_xaxes(gridcolor="#edf0ed", linecolor="#d7dfdc", zerolinecolor="#d7dfdc", automargin=True)
    fig.update_yaxes(gridcolor="#edf0ed", linecolor="#d7dfdc", zerolinecolor="#d7dfdc", automargin=True)
    return st.plotly_chart(fig, **kwargs)
