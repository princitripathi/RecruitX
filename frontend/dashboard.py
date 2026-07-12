"""
frontend/dashboard.py — RecruitX Streamlit Dashboard (Premium SaaS Redesign)

Modern AI recruitment dashboard with a professional dark theme.
All business logic lives in the FastAPI backend (api/). This dashboard
only calls API endpoints and displays results.

Usage:
    streamlit run frontend/dashboard.py
"""

import io
import os
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ============================================================
# Configuration
# ============================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "RecruitX")

# ============================================================
# Premium Dark Theme — CSS Injection
# ============================================================


def inject_theme() -> None:
    """Inject custom CSS for a premium SaaS dark theme."""
    st.markdown("""<style>
    /* ── Root Variables ── */
    :root {
        --bg-primary: #0F172A;
        --bg-card: #1E293B;
        --bg-card-hover: #1E293B;
        --border: #334155;
        --border-light: rgba(51,65,85,0.5);
        --accent: #3B82F6;
        --accent-hover: #2563EB;
        --accent-glow: rgba(59,130,246,0.25);
        --success: #22C55E;
        --success-bg: rgba(34,197,94,0.12);
        --warning: #F59E0B;
        --warning-bg: rgba(245,158,11,0.12);
        --danger: #EF4444;
        --danger-bg: rgba(239,68,68,0.12);
        --text-primary: #FFFFFF;
        --text-secondary: #CBD5E1;
        --text-muted: #64748B;
        --radius: 10px;
        --radius-sm: 6px;
        --radius-lg: 14px;
        --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
        --shadow-lg: 0 4px 24px rgba(0,0,0,0.4);
        --transition: all 0.2s ease;
    }

    /* ── Base ── */
    .stApp, .main > div {
        background: var(--bg-primary);
    }
    #MainMenu, footer, header { display: none !important; }
    .stApp { background: var(--bg-primary); }
    .block-container { padding: 2rem 2rem !important; max-width: 1400px; }

    /* ── Typography ── */
    h1 {
        color: var(--text-primary) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 0.25rem !important;
    }
    h2 {
        color: var(--text-primary) !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }
    h3 {
        color: var(--text-primary) !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    p, li, .stMarkdown, .stCaption {
        color: var(--text-secondary) !important;
        line-height: 1.6 !important;
    }
    .stCaption {
        color: var(--text-muted) !important;
        font-size: 0.8rem !important;
    }
    a {
        color: var(--accent) !important;
        text-decoration: none !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: var(--bg-card) !important;
        border-right: 1px solid var(--border) !important;
        padding: 1.5rem 1rem !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--text-secondary) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary) !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: var(--border) !important;
        margin: 1rem 0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
    }

    /* ── Cards & Containers ── */
    div[data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        margin-bottom: 1rem !important;
        overflow: hidden;
        transition: var(--transition) !important;
    }
    div[data-testid="stExpander"]:hover {
        border-color: var(--accent) !important;
        box-shadow: var(--shadow-lg) !important;
    }
    div[data-testid="stExpander"] > details > summary {
        padding: 1rem 1.25rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] > details > div {
        padding: 0 1.25rem 1.25rem !important;
    }

    /* Expander first-child (top rank glow) */
    .top-match div[data-testid="stExpander"] {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent), var(--shadow-lg) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: var(--radius-lg) !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid var(--border) !important;
        margin-bottom: 1.5rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm) !important;
        padding: 0.6rem 1.2rem !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: var(--transition) !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background: rgba(59,130,246,0.08) !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--accent) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* Nested tabs (inside Candidate DB) */
    .stTabs .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid var(--border) !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin-bottom: 1rem !important;
    }
    .stTabs .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: var(--transition) !important;
        border: 1px solid var(--border) !important;
        background: transparent !important;
        color: var(--text-secondary) !important;
    }
    .stButton > button:hover {
        color: var(--text-primary) !important;
        border-color: var(--accent) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
        box-shadow: 0 4px 16px var(--accent-glow) !important;
        border: none !important;
    }
    .stButton > button[kind="primaryFormSubmit"] {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primaryFormSubmit"]:hover {
        background: var(--accent-hover) !important;
        box-shadow: 0 4px 16px var(--accent-glow) !important;
    }
    .stDownloadButton > button {
        border-radius: var(--radius-sm) !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 500 !important;
        transition: var(--transition) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
    }
    .stDownloadButton > button:hover {
        color: var(--text-primary) !important;
        border-color: var(--accent) !important;
        transform: translateY(-1px);
    }

    /* Button row spacing */
    div.row-widget.stButton {
        margin-bottom: 0 !important;
    }

    /* ── Text Inputs & Text Areas ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        padding: 0.6rem 0.9rem !important;
        font-size: 0.9rem !important;
        transition: var(--transition) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* ── Number Input ── */
    .stNumberInput input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }
    .stNumberInput button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
    }

    /* ── Slider ── */
    .stSlider div[data-baseweb="slider"] {
        background: transparent !important;
    }
    .stSlider div[role="slider"] {
        background: var(--accent) !important;
    }
    .stSlider .stMarkdown {
        color: var(--text-secondary) !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }
    div[data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1rem 1.25rem !important;
        transition: var(--transition) !important;
    }
    div[data-testid="metric-container"]:hover {
        border-color: var(--accent) !important;
        box-shadow: var(--shadow) !important;
    }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] {
        background: var(--bg-card) !important;
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] table {
        font-size: 0.85rem !important;
    }
    [data-testid="stDataFrame"] thead tr th {
        background: #0F172A !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid var(--border) !important;
    }
    [data-testid="stDataFrame"] tbody tr td {
        padding: 0.6rem 1rem !important;
        border-bottom: 1px solid var(--border-light) !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(even) td {
        background: rgba(15,23,42,0.4) !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover td {
        background: rgba(59,130,246,0.06) !important;
    }

    /* ── File Uploader ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 2.5rem 2rem !important;
        text-align: center !important;
        transition: var(--transition) !important;
        cursor: pointer !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent) !important;
        background: rgba(59,130,246,0.03) !important;
    }
    [data-testid="stFileUploader"] section {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }
    [data-testid="stFileUploader"] [data-testid="stMarkdown"] {
        color: var(--text-muted) !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stFileUploader"] button {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background: var(--accent-hover) !important;
    }

    /* ── Progress Bars ── */
    .stProgress > div {
        background: var(--border) !important;
        border-radius: 9999px !important;
        height: 6px !important;
    }
    .stProgress > div > div > div {
        background: var(--accent) !important;
        border-radius: 9999px !important;
        transition: width 0.4s ease !important;
    }

    /* ── Alerts ── */
    div[data-testid="stAlert"] {
        border-radius: var(--radius-sm) !important;
        border: none !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.9rem !important;
    }
    .stAlert-success {
        background: var(--success-bg) !important;
        border: 1px solid rgba(34,197,94,0.3) !important;
        color: var(--success) !important;
    }
    .stAlert-error {
        background: var(--danger-bg) !important;
        border: 1px solid rgba(239,68,68,0.3) !important;
        color: var(--danger) !important;
    }
    .stAlert-warning {
        background: var(--warning-bg) !important;
        border: 1px solid rgba(245,158,11,0.3) !important;
        color: var(--warning) !important;
    }
    .stAlert-info {
        background: rgba(59,130,246,0.1) !important;
        border: 1px solid rgba(59,130,246,0.25) !important;
        color: var(--accent) !important;
    }

    /* ── Chat ── */
    [data-testid="stChatMessage"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: var(--radius) !important;
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stChatMessage"]:hover {
        border-color: var(--border) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        color: var(--text-secondary) !important;
    }
    [data-testid="stChatMessage"][aria-label="user"] {
        border-left: 3px solid var(--accent) !important;
    }
    [data-testid="stChatMessage"][aria-label="assistant"] {
        border-left: 3px solid var(--success) !important;
    }
    [data-testid="stChatInput"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 0.5rem 0.75rem !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    [data-testid="stChatInput"] input {
        color: var(--text-primary) !important;
    }
    [data-testid="stChatInput"] input::placeholder {
        color: var(--text-muted) !important;
    }

    /* ── Info / Warning / Error bare elements ── */
    .stInfo {
        background: rgba(59,130,246,0.08) !important;
        border: 1px solid rgba(59,130,246,0.2) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.75rem 1rem !important;
        color: var(--accent) !important;
    }
    .stWarning {
        background: var(--warning-bg) !important;
        border: 1px solid rgba(245,158,11,0.2) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.75rem 1rem !important;
        color: var(--warning) !important;
    }
    .stError {
        background: var(--danger-bg) !important;
        border: 1px solid rgba(239,68,68,0.2) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.75rem 1rem !important;
        color: var(--danger) !important;
    }
    .stSuccess {
        background: var(--success-bg) !important;
        border: 1px solid rgba(34,197,94,0.2) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.75rem 1rem !important;
        color: var(--success) !important;
    }

    /* ── Dividers ── */
    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Form ── */
    [data-testid="stForm"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1.5rem !important;
        background: var(--bg-card) !important;
    }

    /* ── Spinner ── */
    .stSpinner {
        color: var(--accent) !important;
    }

    /* ── Checkbox / Radio ── */
    .stCheckbox label, .stRadio label {
        color: var(--text-secondary) !important;
    }
    .stCheckbox input:checked ~ div {
        background: var(--accent) !important;
    }

    /* ── Selectbox dropdown ── */
    div[data-baseweb="select"] [data-baseweb="popover"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    div[data-baseweb="select"] [data-baseweb="popover"] li {
        color: var(--text-secondary) !important;
    }
    div[data-baseweb="select"] [data-baseweb="popover"] li:hover {
        background: rgba(59,130,246,0.1) !important;
    }

    /* ── Plotly Chart containers ── */
    .stPlotlyChart {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1rem !important;
        margin-bottom: 1.5rem !important;
    }

    /* ── Balloons override ── */
    .balloon {
        opacity: 0.7 !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }

    /* ── Utility: subtle fade-in ── */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stApp > div {
        animation: fadeIn 0.3s ease;
    }
    </style>""", unsafe_allow_html=True)


# ============================================================
# HTML Utility Components
# ============================================================


def skill_badge(skill: str, badge_type: str = "matched") -> str:
    """
    Render a coloured pill badge for a skill.

    Args:
        skill: The skill name.
        badge_type: One of "matched", "missing", "bonus".

    Returns:
        HTML string for the badge.
    """
    colors = {
        "matched": {"bg": "rgba(34,197,94,0.12)", "text": "#22C55E", "border": "rgba(34,197,94,0.3)"},
        "missing": {"bg": "rgba(245,158,11,0.12)", "text": "#F59E0B", "border": "rgba(245,158,11,0.3)"},
        "bonus": {"bg": "rgba(59,130,246,0.12)", "text": "#3B82F6", "border": "rgba(59,130,246,0.3)"},
    }
    c = colors.get(badge_type, colors["matched"])
    return (
        f'<span style="display:inline-block;background:{c["bg"]};'
        f'color:{c["text"]};border:1px solid {c["border"]};'
        f'border-radius:9999px;padding:2px 12px;font-size:0.78rem;'
        f'font-weight:500;margin:2px 4px 2px 0;'
        f'white-space:nowrap;line-height:1.6;">{skill}</span>'
    )


def score_progress_bar(value: float, max_val: float = 100, color: str = "#3B82F6", label: str = "") -> str:
    """
    Render a thin progress bar with an optional label.

    Args:
        value: Current score value.
        max_val: Maximum possible score.
        color: CSS colour for the bar fill.
        label: Optional label text displayed left of the value.

    Returns:
        HTML string.
    """
    pct = min(value / max_val * 100, 100)
    bar = (
        f'<div style="background:#334155;border-radius:9999px;height:6px;'
        f'overflow:hidden;margin:4px 0;">'
        f'<div style="width:{pct:.0f}%;background:{color};height:100%;'
        f'border-radius:9999px;transition:width 0.5s ease;"></div></div>'
    )
    if label:
        header = (
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;font-size:0.85rem;color:#CBD5E1;margin-bottom:2px;">'
            f'<span>{label}</span>'
            f'<span style="font-weight:600;color:white;">{value:.1f}</span></div>'
        )
        return header + bar
    return bar


def question_card(question: str, q_type: str = "technical", index: int = 1) -> str:
    """
    Render a single interview question inside a styled card.

    Args:
        question: The question text.
        q_type: Category — "technical", "behavioral", or "experience".
        index: 1-based question number.

    Returns:
        HTML string for the card.
    """
    icons = {"technical": "💻", "behavioral": "🧠", "experience": "🔍"}
    colors = {"technical": "#3B82F6", "behavioral": "#8B5CF6", "experience": "#F59E0B"}
    icon = icons.get(q_type, "📋")
    color = colors.get(q_type, "#3B82F6")
    return f"""
    <div style="background:#1E293B;border:1px solid #334155;border-radius:10px;
                padding:1rem 1.25rem;margin-bottom:0.75rem;
                border-left:4px solid {color};
                transition:all 0.2s ease;">
        <div style="display:flex;align-items:flex-start;gap:0.75rem;">
            <span style="font-size:1.2rem;line-height:1.5;">{icon}</span>
            <div style="flex:1;">
                <span style="color:{color};font-size:0.7rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.06em;">
                    {q_type.title()} &mdash; Question #{index}
                </span>
                <p style="color:#CBD5E1;margin:0.3rem 0 0 0;line-height:1.6;font-size:0.95rem;">
                    {question}
                </p>
            </div>
        </div>
    </div>
    """


def status_indicator(connected: bool) -> str:
    """
    Render a coloured dot for connection status.

    Args:
        connected: True if API is connected.

    Returns:
        HTML string.
    """
    if connected:
        return (
            '<span style="display:inline-block;width:8px;height:8px;'
            'background:#22C55E;border-radius:50%;margin-right:6px;'
            'box-shadow:0 0 6px rgba(34,197,94,0.6);"></span>'
        )
    return (
        '<span style="display:inline-block;width:8px;height:8px;'
        'background:#EF4444;border-radius:50%;margin-right:6px;"></span>'
    )


# ============================================================
# Plotly Theme Helper
# ============================================================


def apply_dark_theme(fig: go.Figure) -> go.Figure:
    """
    Apply the RecruitX dark theme to a Plotly figure.

    Args:
        fig: A Plotly Figure object.

    Returns:
        The same Figure with updated layout.
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#CBD5E1", "family": "system-ui, -apple-system, sans-serif"},
        title={"font": {"color": "white", "size": 16}, "x": 0, "xanchor": "left"},
        xaxis={
            "gridcolor": "#334155",
            "zerolinecolor": "#334155",
            "tickfont": {"color": "#CBD5E1"},
            "title": {"font": {"color": "#CBD5E1"}},
        },
        yaxis={
            "gridcolor": "#334155",
            "zerolinecolor": "#334155",
            "tickfont": {"color": "#CBD5E1"},
            "title": {"font": {"color": "#CBD5E1"}},
        },
        legend={"font": {"color": "#CBD5E1"}, "bgcolor": "rgba(0,0,0,0)"},
        coloraxis={"colorbar": {"tickfont": {"color": "#CBD5E1"}}},
        hoverlabel={
            "bgcolor": "#1E293B",
            "font": {"color": "white"},
            "bordercolor": "#334155",
        },
        margin={"t": 40, "b": 40, "l": 40, "r": 20},
    )
    return fig


# ============================================================
# API Client Helpers
# ============================================================


def api_get(endpoint: str) -> Optional[Any]:
    """
    Make a GET request to the FastAPI backend.

    Args:
        endpoint: API path (e.g. "/api/candidates").

    Returns:
        Parsed JSON response, or None if the request failed.
    """
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the server running?")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None


def api_post(endpoint: str, json_data: dict) -> Optional[Any]:
    """
    Make a POST request to the FastAPI backend.

    Args:
        endpoint: API path (e.g. "/api/recruit").
        json_data: Request body as a dictionary.

    Returns:
        Parsed JSON response, or None if the request failed.
    """
    try:
        resp = requests.post(
            f"{API_BASE_URL}{endpoint}", json=json_data, timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the server running?")
        return None
    except requests.exceptions.RequestException as e:
        detail = ""
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        st.error(f"API request failed: {detail}")
        return None


def api_post_file(endpoint: str, file_bytes: bytes, filename: str) -> Optional[Any]:
    """
    Upload a file to the FastAPI backend via multipart POST.

    Args:
        endpoint: API path (e.g. "/api/upload-resume").
        file_bytes: Raw file content.
        filename: Original filename for the upload.

    Returns:
        Parsed JSON response, or None if the request failed.
    """
    try:
        files = {"file": (filename, file_bytes)}
        resp = requests.post(
            f"{API_BASE_URL}{endpoint}", files=files, timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_BASE_URL}. Is the server running?")
        return None
    except requests.exceptions.RequestException as e:
        detail = ""
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        st.error(f"API request failed: {detail}")
        return None


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject the premium dark theme
inject_theme()

# ============================================================
# Session State Initialisation
# ============================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "recruit_results" not in st.session_state:
    st.session_state.recruit_results = None
if "interview_questions" not in st.session_state:
    st.session_state.interview_questions = {}
if "last_jd_text" not in st.session_state:
    st.session_state.last_jd_text = ""

# ============================================================
# Helper: Candidate Count
# ============================================================


def _fetch_candidate_count() -> int:
    """
    Fetch the total number of candidates in the database.

    Returns:
        Total candidate count, or 0 if the request fails.
    """
    result = api_get("/api/candidates")
    if result and "candidates" in result:
        return len(result["candidates"])
    return 0


# ============================================================
# Sidebar
# ============================================================

health = api_get("/api/health")

with st.sidebar:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem;">'
        f'<span style="font-size:1.8rem;line-height:1;">🔄</span>'
        f'<div><h2 style="margin:0;font-size:1.4rem !important;">{APP_NAME}</h2>'
        f'<p style="margin:0;font-size:0.75rem;color:#64748B;">AI Recruitment Platform</p></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<hr style="margin:0.75rem 0;" />',
        unsafe_allow_html=True,
    )

    # Connection status
    if health:
        st.markdown(
            f'<p style="margin:0 0 0.25rem 0;font-size:0.85rem;">'
            f'{status_indicator(True)}<span style="color:#22C55E;">Connected</span></p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="margin:0;font-size:0.75rem;color:#64748B;">'
            f'{health.get("app", APP_NAME)} v{health.get("version", "1.0")}</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<p style="margin:0;font-size:0.85rem;">'
            f'{status_indicator(False)}<span style="color:#EF4444;">Disconnected</span></p>',
            unsafe_allow_html=True,
        )

    # Quick stats
    candidate_count = _fetch_candidate_count()
    st.markdown(
        '<hr style="margin:0.75rem 0;" />'
        '<p style="font-size:0.75rem;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.06em;color:#64748B;margin:0 0 0.5rem 0;">Database</p>',
        unsafe_allow_html=True,
    )
    stats_md = (
        f'<div style="display:flex;flex-direction:column;gap:0.35rem;">'
        f'<div style="display:flex;justify-content:space-between;">'
        f'<span style="color:#CBD5E1;font-size:0.85rem;">Candidates</span>'
        f'<span style="color:white;font-weight:600;">{candidate_count}</span></div>'
    )
    if health:
        stats_md += (
            f'<div style="display:flex;justify-content:space-between;">'
            f'<span style="color:#CBD5E1;font-size:0.85rem;">Status</span>'
            f'<span style="color:#22C55E;font-size:0.85rem;">Operational</span></div>'
        )
    stats_md += "</div>"
    st.markdown(stats_md, unsafe_allow_html=True)

    st.markdown(
        '<hr style="margin:0.75rem 0;" />'
        f'<p style="font-size:0.7rem;color:#475569;text-align:center;margin-top:1rem;">'
        f'Powered by Multi-Agent AI</p>',
        unsafe_allow_html=True,
    )

# ============================================================
# Tab 1: Find Candidates
# ============================================================


def render_find_candidates_tab() -> None:
    """
    Render the Find Candidates tab.

    Provides:
        - Large text area for job description
        - "Find Best Candidates" button with progress indicator
        - Ranked results with stats, chart, export, and candidate cards
    """
    col_heading, col_count = st.columns([3, 1])
    with col_heading:
        st.markdown(
            '<h1 style="margin-bottom:0.25rem;">Find Candidates</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#64748B;margin-top:0;">'
            "Paste a job description to match candidates using AI-powered analysis.</p>",
            unsafe_allow_html=True,
        )
    with col_count:
        st.markdown(
            f'<div style="background:#1E293B;border:1px solid #334155;border-radius:10px;'
            f'padding:1rem;text-align:center;">'
            f'<p style="font-size:0.7rem;color:#64748B;text-transform:uppercase;'
            f'letter-spacing:0.05em;margin:0;">Database</p>'
            f'<p style="font-size:1.8rem;font-weight:700;color:white;margin:0.25rem 0 0 0;">'
            f'{_fetch_candidate_count()}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Job description input
    jd_text = st.text_area(
        "Job Description",
        height=180,
        placeholder="Paste the full job description here, including required skills, experience, and responsibilities...",
        help="Enter the full job description including required skills, experience, and responsibilities.",
    )

    # Controls row
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        top_k = st.number_input(
            "Top K candidates",
            min_value=1,
            max_value=50,
            value=10,
            help="Number of top candidates to return.",
        )
    with col2:
        st.markdown(
            '<p style="margin-bottom:0.25rem;font-size:0.85rem;color:#CBD5E1;'
            'font-weight:500;">&nbsp;</p>',
            unsafe_allow_html=True,
        )
        run_clicked = st.button(
            "Find Best Candidates",
            type="primary",
            use_container_width=True,
            disabled=not jd_text.strip(),
        )
    with col3:
        pass

    if run_clicked and jd_text.strip():
        progress_placeholder = st.container()
        with progress_placeholder:
            progress_bar = st.progress(0, text="Initialising pipeline...")

            progress_bar.progress(10, text="Analysing job description...")
            progress_bar.progress(30, text="Searching for matching candidates...")
            progress_bar.progress(50, text="Scoring candidates...")
            progress_bar.progress(70, text="Analysing skill gaps...")
            progress_bar.progress(90, text="Building ranked shortlist...")

            result = api_post("/api/recruit", {
                "job_description": jd_text,
                "top_k": top_k,
            })

            progress_bar.progress(100, text="Done!")
            progress_bar.empty()

        if result and result.get("success"):
            st.session_state.recruit_results = result
            st.session_state.last_jd_text = jd_text
            st.balloons()
        elif result and not result.get("success"):
            st.error("Pipeline did not complete successfully. Check server logs.")

    # Display results from current or previous run
    if st.session_state.recruit_results:
        _display_recruit_results(st.session_state.recruit_results)


def _display_recruit_results(result: Dict[str, Any]) -> None:
    """
    Display the recruitment pipeline results.

    Shows a stats row, a score comparison chart, an export button,
    and premium candidate cards.

    Args:
        result: The response from POST /api/recruit.
    """
    shortlist = result.get("shortlist", [])
    jd_analysis = result.get("jd_analysis", {})
    processing_time = result.get("processing_time_ms", 0)

    if not shortlist:
        st.warning("No matching candidates found.")
        return

    candidate_count = _fetch_candidate_count()
    top_score = shortlist[0]["final_score"]

    # ── Divider ──
    st.markdown(
        '<hr style="margin:1.5rem 0;" />',
        unsafe_allow_html=True,
    )

    # ── Stats row ──
    st.markdown(
        '<h2 style="margin-bottom:1rem;">Results Overview</h2>',
        unsafe_allow_html=True,
    )
    stats_cols = st.columns(4)
    stats_cols[0].metric("Candidates Found", len(shortlist))
    stats_cols[1].metric("Database Size", candidate_count)
    stats_cols[2].metric("Top Score", f"{top_score:.1f}/100")
    stats_cols[3].metric("Processing Time", f"{processing_time:.0f} ms")

    # ── Score chart ──
    _display_score_chart(shortlist)

    # ── Export button ──
    _display_export_button(shortlist)

    # ── Ranked candidate cards ──
    st.markdown(
        '<h2 style="margin-top:1.5rem;margin-bottom:1rem;">Ranked Candidates</h2>',
        unsafe_allow_html=True,
    )
    for entry in shortlist:
        is_top = entry["rank"] == 1
        rank_label = f"#{entry['rank']}"
        score_str = f"{entry['final_score']:.1f}/100"

        # Fetch candidate name if available
        cid = entry["candidate_id"]
        detail = api_get(f"/api/candidates/{cid}")
        c_name = f"Candidate #{cid}"
        c_exp = ""
        c_loc = ""
        c_skills_raw = ""
        if detail and detail.get("candidate"):
            c = detail["candidate"]
            c_name = c.get("name", c_name)
            c_exp = c.get("experience_years", "")
            c_loc = c.get("location", "")

        # Format the expander label
        label_parts = [f"#{entry['rank']} — {c_name}"]
        if c_exp:
            label_parts.append(f"{c_exp} yrs")
        if c_loc:
            label_parts.append(c_loc)
        label_parts.append(f"Score: {entry['final_score']:.1f}")
        label = " | ".join(label_parts)

        with st.expander(label, expanded=is_top):
            if is_top:
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">'
                    '<span style="background:rgba(59,130,246,0.15);color:#3B82F6;'
                    'border:1px solid rgba(59,130,246,0.3);border-radius:6px;'
                    'padding:2px 10px;font-size:0.75rem;font-weight:600;'
                    'text-transform:uppercase;letter-spacing:0.04em;">Top Match</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # Score breakdown
            score_cols = st.columns(5)
            score_cols[0].metric("Final Score", f"{entry['final_score']:.1f}")
            score_cols[1].metric("Semantic", f"{entry['semantic_score']:.1f}")
            score_cols[2].metric("Skill", f"{entry['skill_score']:.1f}")
            score_cols[3].metric("Signal", f"{entry['signal_score']:.1f}")
            score_cols[4].metric("Recency", f"{entry.get('recency_score', 0):.1f}")

            # Score progress bar
            bar_color = "#3B82F6"
            if entry["final_score"] >= 80:
                bar_color = "#22C55E"
            elif entry["final_score"] >= 60:
                bar_color = "#F59E0B"
            st.markdown(
                score_progress_bar(
                    entry["final_score"], 100, bar_color, "Overall Match"
                ),
                unsafe_allow_html=True,
            )

            # Explanation
            st.markdown(
                f'<div style="background:rgba(59,130,246,0.05);border:1px solid #334155;'
                f'border-radius:8px;padding:0.75rem 1rem;margin:0.75rem 0;">'
                f'<p style="color:#CBD5E1;margin:0;font-size:0.9rem;">'
                f'<strong style="color:white;">Explanation:</strong> '
                f'{entry.get("explanation", "N/A")}</p></div>',
                unsafe_allow_html=True,
            )

            # Skill gap badges
            skill_gap = entry.get("skill_gap", {})
            matched = skill_gap.get("matched", [])
            missing = skill_gap.get("missing", [])
            bonus = skill_gap.get("bonus", [])

            if matched or missing or bonus:
                st.markdown(
                    '<p style="font-weight:600;color:white;margin-bottom:0.5rem;">'
                    'Skill Gap Analysis</p>',
                    unsafe_allow_html=True,
                )

                # Skills as badges in a card
                skill_html = ""
                if matched:
                    skill_html += f'<p style="margin:0 0 0.25rem 0;font-size:0.8rem;color:#22C55E;font-weight:500;">Matched</p><div style="margin-bottom:0.5rem;">'
                    for s in matched:
                        skill_html += skill_badge(s, "matched")
                    skill_html += "</div>"
                if missing:
                    skill_html += f'<p style="margin:0 0 0.25rem 0;font-size:0.8rem;color:#F59E0B;font-weight:500;">Missing</p><div style="margin-bottom:0.5rem;">'
                    for s in missing:
                        skill_html += skill_badge(s, "missing")
                    skill_html += "</div>"
                if bonus:
                    skill_html += f'<p style="margin:0 0 0.25rem 0;font-size:0.8rem;color:#3B82F6;font-weight:500;">Bonus</p><div>'
                    for s in bonus:
                        skill_html += skill_badge(s, "bonus")
                    skill_html += "</div>"
                st.markdown(skill_html, unsafe_allow_html=True)

            # Action buttons
            st.markdown(
                '<hr style="margin:1rem 0;" />',
                unsafe_allow_html=True,
            )
            action_cols = st.columns(2)
            with action_cols[0]:
                iq_key = f"iq_{cid}_{entry['rank']}"
                if st.button("Generate Interview Questions", key=iq_key):
                    with st.spinner("Generating personalized interview questions..."):
                        candidate_detail = api_get(f"/api/candidates/{cid}")
                        if candidate_detail and candidate_detail.get("candidate"):
                            c = candidate_detail["candidate"]
                            payload = {
                                "candidate_id": cid,
                                "candidate_name": c.get("name", ""),
                                "candidate_skills": c.get("skills", ""),
                                "candidate_experience_years": c.get("experience_years", 0),
                                "candidate_previous_roles": c.get("previous_roles"),
                                "candidate_education": c.get("education"),
                                "job_description": st.session_state.last_jd_text,
                                "skill_gap_matched": skill_gap.get("matched", []),
                                "skill_gap_missing": skill_gap.get("missing", []),
                                "skill_gap_bonus": skill_gap.get("bonus", []),
                                "explanation": entry.get("explanation", ""),
                            }
                            questions_result = api_post("/api/interview-questions", payload)
                            if questions_result and "questions" in questions_result:
                                st.session_state.interview_questions[cid] = questions_result["questions"]
                            else:
                                st.error("Failed to generate interview questions. Check server logs.")
                        else:
                            st.error(f"Could not fetch details for candidate #{cid}.")

            with action_cols[1]:
                st.button(
                    "Submit Feedback",
                    disabled=True,
                    key=f"fb_{cid}_{entry['rank']}",
                    help=(
                        "Feedback requires the shortlist ID from the backend. "
                        "This feature will be enabled in a future update."
                    ),
                )

            # Display generated interview questions
            if cid in st.session_state.interview_questions:
                questions = st.session_state.interview_questions[cid]
                st.markdown(
                    '<hr style="margin:1rem 0;" />',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<h3 style="margin-bottom:0.75rem;">Interview Questions</h3>',
                    unsafe_allow_html=True,
                )
                for i, q in enumerate(questions, 1):
                    q_type = ["technical", "behavioral", "experience"][i % 3]
                    st.markdown(
                        question_card(q, q_type=q_type, index=i),
                        unsafe_allow_html=True,
                    )


def _display_score_chart(shortlist: List[Dict[str, Any]]) -> None:
    """
    Show a bar chart comparing final scores across ranked candidates.

    Args:
        shortlist: Ranked candidate entries from the API response.
    """
    chart_data = pd.DataFrame([
        {
            "Rank": e["rank"],
            "Candidate": f"#{e['candidate_id']}",
            "Final Score": e["final_score"],
        }
        for e in shortlist
    ])

    fig = px.bar(
        chart_data,
        x="Candidate",
        y="Final Score",
        title="Top Candidate Scores",
        color="Final Score",
        color_continuous_scale="Blues",
        text_auto=".1f",
    )
    fig = apply_dark_theme(fig)
    fig.update_traces(
        textfont={"color": "white", "size": 11},
        marker_line={"width": 0},
        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>",
    )
    fig.update_layout(showlegend=False, xaxis={"categoryorder": "array", "categoryarray": chart_data["Candidate"].tolist()})
    st.plotly_chart(fig, use_container_width=True)


def _display_export_button(shortlist: List[Dict[str, Any]]) -> None:
    """
    Provide a CSV download button for the shortlist data.

    Args:
        shortlist: Ranked candidate entries from the API response.
    """
    df_export = pd.DataFrame([
        {
            "Rank": e["rank"],
            "Candidate ID": e["candidate_id"],
            "Final Score": f"{e['final_score']:.1f}",
            "Semantic Score": f"{e['semantic_score']:.1f}",
            "Skill Score": f"{e['skill_score']:.1f}",
            "Signal Score": f"{e['signal_score']:.1f}",
            "Explanation": e.get("explanation", ""),
        }
        for e in shortlist
    ])

    csv_buffer = io.StringIO()
    df_export.to_csv(csv_buffer, index=False)

    st.download_button(
        "Export to CSV",
        data=csv_buffer.getvalue(),
        file_name="recruitx_shortlist.csv",
        mime="text/csv",
    )


# ============================================================
# Tab 2: Chat with RecruitX
# ============================================================


def render_chat_tab() -> None:
    """
    Render the Chat with RecruitX tab.

    Provides a ChatGPT-style chat interface for natural language queries.
    """
    st.markdown(
        '<h1 style="margin-bottom:0.25rem;">Chat with RecruitX</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#64748B;margin-top:0;">'
        "Ask natural language questions about your candidates and recruitment pipeline.</p>",
        unsafe_allow_html=True,
    )

    # Chat history container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            avatar = "👤" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Chat input
    prompt = st.chat_input(
        "Ask about candidates, search for skills, or get recruitment insights..."
    )
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                result = api_post("/api/chat", {
                    "message": prompt,
                    "session_id": st.session_state.session_id,
                })
            if result:
                response_text = result.get("response", "No response.")
            else:
                response_text = "Sorry, I could not process your request. Please try again."
            st.markdown(response_text)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": response_text}
        )

    # Clear chat button
    if st.session_state.chat_history:
        st.markdown(
            '<hr style="margin:1rem 0;" />',
            unsafe_allow_html=True,
        )
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()


# ============================================================
# Tab 3: Candidate Database
# ============================================================


def render_candidate_db_tab() -> None:
    """
    Render the Candidate Database tab with three sub-tabs:
        - Browse Candidates (search, filter, view, delete)
        - Add Candidate (manual form)
        - Upload Resume (file upload with AI parsing)
    """
    st.markdown(
        '<h1 style="margin-bottom:0.25rem;">Candidate Database</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#64748B;margin-top:0;">'
        "Browse, add, and manage your candidate pool.</p>",
        unsafe_allow_html=True,
    )

    tab_browse, tab_add, tab_upload = st.tabs(
        ["Browse Candidates", "Add Candidate", "Upload Resume"]
    )

    with tab_browse:
        _render_browse_candidates()

    with tab_add:
        _render_add_candidate()

    with tab_upload:
        _render_upload_resume()


def _render_browse_candidates() -> None:
    """
    Display all candidates in a searchable, filterable table with detail view.
    """
    result = api_get("/api/candidates")
    if not result:
        return

    candidates = result.get("candidates", [])
    if not candidates:
        st.info("No candidates found. Add candidates or upload resumes.")
        return

    df = pd.DataFrame(candidates)

    # Search bar
    search = st.text_input(
        "Search candidates",
        placeholder="Search by name, skill, or location...",
    )
    if search:
        mask = df.apply(
            lambda row: search.lower()
            in str(row.get("name", "")).lower()
            or search.lower() in str(row.get("skills", "")).lower()
            or search.lower() in str(row.get("location", "")).lower(),
            axis=1,
        )
        filtered_df = df[mask]
        st.markdown(
            f'<p style="font-size:0.8rem;color:#64748B;margin:0 0 0.5rem 0;">'
            f'Showing {len(filtered_df)} of {len(candidates)} candidates</p>',
            unsafe_allow_html=True,
        )
    else:
        filtered_df = df

    # Data table
    st.dataframe(
        filtered_df[
            [
                "id",
                "name",
                "email",
                "skills",
                "experience_years",
                "location",
                "profile_completeness",
                "last_active_days",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": "ID",
            "name": "Name",
            "email": "Email",
            "skills": "Skills",
            "experience_years": st.column_config.NumberColumn("Experience (yrs)"),
            "location": "Location",
            "profile_completeness": st.column_config.ProgressColumn(
                "Profile Completeness", format="%d", min_value=0, max_value=100
            ),
            "last_active_days": "Last Active (days ago)",
        },
    )

    # Candidate detail + delete
    if candidates:
        _render_candidate_detail(candidates)


def _render_candidate_detail(candidates: List[Dict[str, Any]]) -> None:
    """
    Show a dropdown to select and view a single candidate's full profile.

    Args:
        candidates: Full list of candidates from the API.
    """
    st.markdown(
        '<h3 style="margin-top:1.5rem;">Candidate Details</h3>',
        unsafe_allow_html=True,
    )

    selected_id = st.selectbox(
        "Select candidate:",
        [c["id"] for c in candidates],
        format_func=lambda x: f"Candidate #{x}",
        label_visibility="collapsed",
    )
    if not selected_id:
        return

    detail = api_get(f"/api/candidates/{selected_id}")
    if not detail or not detail.get("candidate"):
        return

    c = detail["candidate"]

    # Render detail in a card
    st.markdown(
        f'<div style="background:#1E293B;border:1px solid #334155;border-radius:12px;'
        f'padding:1.5rem;margin-top:0.5rem;">'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {c.get('name', 'N/A')}")
        st.markdown(f"**Email:** {c.get('email', 'N/A')}")
        st.markdown(f"**Phone:** {c.get('phone', 'N/A')}")
        st.markdown(f"**Location:** {c.get('location', 'N/A')}")
        st.markdown(f"**Education:** {c.get('education', 'N/A')}")
    with col2:
        st.markdown(f"**Experience:** {c.get('experience_years', 0)} years")
        st.markdown(f"**Skills:** {c.get('skills', 'N/A')}")
        st.markdown(f"**Previous Roles:** {c.get('previous_roles', 'N/A')}")
        st.markdown(f"**Profile Completeness:** {c.get('profile_completeness', 0)}%")
        st.markdown(f"**Last Active:** {c.get('last_active_days', 'N/A')} days ago")

    st.markdown(
        '<hr style="margin:1rem 0;" />',
        unsafe_allow_html=True,
    )

    if st.button("Delete Candidate", key=f"del_{selected_id}"):
        del_resp = requests.delete(
            f"{API_BASE_URL}/api/candidates/{selected_id}", timeout=10
        )
        if del_resp.ok:
            st.success(f"Candidate #{selected_id} deleted.")
            st.rerun()
        else:
            st.error("Failed to delete candidate.")


def _render_add_candidate() -> None:
    """
    Show a form to manually add a new candidate.
    Submits to POST /api/candidates.
    """
    st.markdown(
        '<p style="margin-bottom:1rem;color:#64748B;">'
        "Fill in the candidate details below. Fields marked with * are required.</p>",
        unsafe_allow_html=True,
    )

    with st.form("add_candidate_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", placeholder="Rahul Sharma")
            email = st.text_input("Email *", placeholder="rahul@example.com")
            phone = st.text_input("Phone", placeholder="9876543210")
            location = st.text_input("Location", placeholder="Bangalore")
        with col2:
            skills = st.text_input("Skills *", placeholder="Python, Machine Learning, SQL")
            experience = st.number_input(
                "Experience (years)", min_value=0.0, max_value=50.0, step=0.5
            )
            education = st.text_input("Education", placeholder="B.Tech Computer Science")
            previous_roles = st.text_input(
                "Previous Roles", placeholder="Data Analyst at TCS; Backend Dev at Infosys"
            )

        col_slider1, col_slider2 = st.columns(2)
        with col_slider1:
            profile_completeness = st.slider("Profile Completeness", 0, 100, 70)
        with col_slider2:
            last_active_days = st.number_input("Last Active (days ago)", min_value=0, value=30)

        submitted = st.form_submit_button(
            "Add Candidate", type="primary", use_container_width=True
        )

    if submitted:
        if not name or not email or not skills:
            st.error("Name, email, and skills are required.")
            return

        payload = {
            "name": name,
            "email": email,
            "skills": skills,
            "experience_years": experience,
            "phone": phone or None,
            "location": location or None,
            "education": education or None,
            "previous_roles": previous_roles or None,
            "profile_completeness": profile_completeness,
            "last_active_days": last_active_days,
        }

        result = api_post("/api/candidates", payload)
        if result:
            st.success(result.get("message", "Candidate created successfully!"))
            st.balloons()


def _render_upload_resume() -> None:
    """
    Show a file uploader for resumes with AI parsing.

    Uploaded resume is automatically parsed by the AI Resume Parser:
    extracts text, detects duplicates via MD5 hash, parses with LLM into
    a structured candidate profile, saves to database, and adds to FAISS index.
    """
    st.markdown(
        '<div style="text-align:center;margin-bottom:1rem;">'
        '<span style="font-size:2.5rem;">📄</span>'
        '<h3 style="margin:0.5rem 0 0.25rem;">Upload Resume</h3>'
        '<p style="color:#64748B;max-width:500px;margin:0 auto;">'
        "Upload a PDF or DOCX resume. The AI parser will extract text, "
        "detect duplicates, and create a structured candidate profile.</p></div>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=["pdf", "docx"],
        help="Max file size: 10 MB. Supported formats: PDF, DOCX",
    )

    if uploaded_file is not None:
        file_size = uploaded_file.size
        file_name = uploaded_file.name

        st.markdown(
            f'<div style="background:rgba(59,130,246,0.05);border:1px solid #334155;'
            f'border-radius:8px;padding:0.75rem 1rem;margin:0.5rem 0;'
            f'display:flex;align-items:center;gap:0.75rem;">'
            f'<span style="font-size:1.2rem;">📎</span>'
            f'<div style="flex:1;"><p style="margin:0;font-weight:500;color:white;">{file_name}</p>'
            f'<p style="margin:0;font-size:0.8rem;color:#64748B;">'
            f'{file_size / 1024:.1f} KB</p></div></div>',
            unsafe_allow_html=True,
        )

        if file_size > 10 * 1024 * 1024:
            st.error("File size exceeds the 10 MB limit.")
            return

        progress_bar = st.progress(0, text="Ready to upload...")

        if st.button("Upload and Parse Resume", type="primary", use_container_width=True):
            progress_bar.progress(20, text="Uploading file...")
            progress_bar.progress(40, text="Extracting text...")
            progress_bar.progress(60, text="Parsing with AI...")
            progress_bar.progress(80, text="Saving candidate profile...")

            result = api_post_file(
                "/api/upload-resume",
                uploaded_file.getvalue(),
                uploaded_file.name,
            )

            if result:
                progress_bar.progress(100, text="Complete!")
                candidate = result.get("candidate")
                is_new = result.get("is_new", True)

                if is_new:
                    st.success(result.get("message", "Resume parsed successfully!"))
                else:
                    st.info(result.get("message", "Duplicate resume detected."))

                if candidate:
                    st.markdown(
                        f'<div style="background:#1E293B;border:1px solid #334155;'
                        f'border-radius:10px;padding:1rem;margin-top:0.5rem;">'
                        f'<h4 style="margin:0 0 0.75rem 0;">Parsed Candidate</h4>'
                        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">',
                        unsafe_allow_html=True,
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Name:** {candidate.get('name', 'N/A')}")
                        st.markdown(f"**Email:** {candidate.get('email', 'N/A')}")
                        st.markdown(f"**Phone:** {candidate.get('phone', 'N/A')}")
                        st.markdown(f"**Location:** {candidate.get('location', 'N/A')}")
                        st.markdown(f"**Education:** {candidate.get('education', 'N/A')}")
                    with col2:
                        st.markdown(f"**Skills:** {candidate.get('skills', 'N/A')}")
                        st.markdown(f"**Experience:** {candidate.get('experience_years', 0)} years")
                        st.markdown(f"**Previous Roles:** {candidate.get('previous_roles', 'N/A')}")
                        st.markdown(f"**Profile Completeness:** {candidate.get('profile_completeness', 0)}%")
                        st.markdown(f"**Candidate ID:** {candidate.get('id', 'N/A')}")
                    st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                progress_bar.progress(0, text="Upload failed")
                st.error("Resume upload failed. Please try again.")


# ============================================================
# Tab 4: Analytics
# ============================================================


def render_analytics_tab() -> None:
    """
    Render the Analytics tab with charts based on candidate data.

    Charts:
        - Profile completeness distribution (histogram)
        - Top 15 skills (horizontal bar chart)
        - Experience distribution (box plot)
        - Experience vs completeness (scatter plot)
        - Candidates by location (pie chart)
        - Activity recency (bar chart by last active bucket)
    """
    st.markdown(
        '<h1 style="margin-bottom:0.25rem;">Analytics</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#64748B;margin-top:0;">'
        "Visual insights into your candidate database and recruitment pipeline.</p>",
        unsafe_allow_html=True,
    )

    result = api_get("/api/candidates")
    if not result:
        return

    candidates = result.get("candidates", [])
    if not candidates:
        st.info("No candidate data available for analytics.")
        return

    df = pd.DataFrame(candidates)

    # 1. Score distribution — profile completeness histogram
    st.markdown(
        '<h2 style="margin-top:1rem;">Profile Completeness Distribution</h2>',
        unsafe_allow_html=True,
    )
    fig1 = px.histogram(
        df,
        x="profile_completeness",
        nbins=10,
        title="Profile Completeness Distribution",
        labels={"profile_completeness": "Completeness (%)"},
        color_discrete_sequence=["#3B82F6"],
    )
    fig1 = apply_dark_theme(fig1)
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Top skills in demand
    st.markdown(
        '<h2 style="margin-top:2rem;">Top Skills in Demand</h2>',
        unsafe_allow_html=True,
    )
    all_skills: List[str] = []
    for c in candidates:
        skills_str = c.get("skills", "")
        if skills_str:
            all_skills.extend([s.strip() for s in skills_str.split(",") if s.strip()])

    if all_skills:
        skill_counts = (
            pd.Series(all_skills).value_counts().head(15).reset_index()
        )
        skill_counts.columns = ["Skill", "Count"]
        fig2 = px.bar(
            skill_counts,
            x="Count",
            y="Skill",
            orientation="h",
            title="Top 15 Skills Across All Candidates",
            color="Count",
            color_continuous_scale="Blues",
        )
        fig2 = apply_dark_theme(fig2)
        fig2.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No skills data available.")

    # 3. Experience distribution
    st.markdown(
        '<h2 style="margin-top:2rem;">Experience Distribution</h2>',
        unsafe_allow_html=True,
    )
    fig3 = px.box(
        df,
        y="experience_years",
        title="Years of Experience Distribution",
        labels={"experience_years": "Experience (years)"},
        color_discrete_sequence=["#3B82F6"],
    )
    fig3 = apply_dark_theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)

    # 4. Experience vs profile completeness
    st.markdown(
        '<h2 style="margin-top:2rem;">Experience vs Profile Completeness</h2>',
        unsafe_allow_html=True,
    )
    fig4 = px.scatter(
        df,
        x="experience_years",
        y="profile_completeness",
        hover_data=["name", "location"],
        title="Experience vs Profile Completeness",
        labels={
            "experience_years": "Experience (years)",
            "profile_completeness": "Profile Completeness (%)",
        },
        color="last_active_days",
        color_continuous_scale="Blues",
    )
    fig4 = apply_dark_theme(fig4)
    st.plotly_chart(fig4, use_container_width=True)

    # 5. Candidates by location
    st.markdown(
        '<h2 style="margin-top:2rem;">Candidates by Location</h2>',
        unsafe_allow_html=True,
    )
    location_counts = df["location"].value_counts().reset_index()
    location_counts.columns = ["Location", "Count"]
    fig5 = px.pie(
        location_counts,
        names="Location",
        values="Count",
        title="Candidates by Location",
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig5 = apply_dark_theme(fig5)
    fig5.update_traces(
        textfont={"color": "white"},
        hovertemplate="<b>%{label}</b><br>%{value} candidates (%{percent})<extra></extra>",
    )
    st.plotly_chart(fig5, use_container_width=True)

    # 6. Activity — last active day buckets
    st.markdown(
        '<h2 style="margin-top:2rem;">Candidate Activity</h2>',
        unsafe_allow_html=True,
    )
    _display_activity_chart(df)


def _display_activity_chart(df: pd.DataFrame) -> None:
    """
    Show a bar chart grouping candidates by how recently they were active.

    Args:
        df: DataFrame with a "last_active_days" column.
    """
    bins = [0, 7, 30, 90, 180, 365, 1000]
    labels = ["<1 week", "1-4 weeks", "1-3 months", "3-6 months", "6-12 months", ">1 year"]
    df["activity_bin"] = pd.cut(df["last_active_days"], bins=bins, labels=labels)
    activity_counts = df["activity_bin"].value_counts().reindex(labels).reset_index()
    activity_counts.columns = ["Activity", "Count"]
    activity_counts["Count"] = activity_counts["Count"].fillna(0).astype(int)

    fig6 = px.bar(
        activity_counts,
        x="Activity",
        y="Count",
        title="Candidates by Last Activity",
        color="Count",
        color_continuous_scale="Blues",
    )
    fig6 = apply_dark_theme(fig6)
    fig6.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": labels},
        showlegend=False,
    )
    st.plotly_chart(fig6, use_container_width=True)


# ============================================================
# Main App — Tab Navigation
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Search Candidates",
        "Chat with RecruitX",
        "Candidate Database",
        "Analytics",
    ]
)

with tab1:
    render_find_candidates_tab()

with tab2:
    render_chat_tab()

with tab3:
    render_candidate_db_tab()

with tab4:
    render_analytics_tab()
