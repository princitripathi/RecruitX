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
    """Inject custom CSS for a premium SaaS dark theme matching Linear/Notion/Vercel quality."""
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

    :root {
        --bg-primary: #0B1120;
        --bg-secondary: #080E18;
        --bg-card: #111827;
        --bg-card-hover: #1A2332;
        --bg-card-elevated: #1E293B;
        --border: #1E293B;
        --border-light: rgba(30,41,59,0.6);
        --border-subtle: rgba(30,41,59,0.3);
        --accent: #3B82F6;
        --accent-hover: #60A5FA;
        --accent-soft: rgba(59,130,246,0.08);
        --accent-glow: rgba(59,130,246,0.2);
        --accent-glow-strong: rgba(59,130,246,0.35);
        --accent-secondary: #7C3AED;
        --accent-secondary-soft: rgba(124,58,237,0.1);
        --success: #22C55E;
        --success-bg: rgba(34,197,94,0.1);
        --success-border: rgba(34,197,94,0.25);
        --warning: #F59E0B;
        --warning-bg: rgba(245,158,11,0.1);
        --warning-border: rgba(245,158,11,0.25);
        --danger: #EF4444;
        --danger-bg: rgba(239,68,68,0.1);
        --danger-border: rgba(239,68,68,0.25);
        --text-primary: #F1F5F9;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --text-bright: #FFFFFF;
        --radius-xs: 6px;
        --radius-sm: 8px;
        --radius: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --radius-full: 9999px;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.15);
        --shadow: 0 1px 3px rgba(0,0,0,0.15);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.2);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.25);
        --shadow-glow: 0 0 12px rgba(59,130,246,0.1);
        --shadow-glow-strong: 0 0 20px rgba(59,130,246,0.15);
        --transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-slow: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        --space-1: 0.25rem;
        --space-2: 0.5rem;
        --space-3: 0.75rem;
        --space-4: 1rem;
        --space-5: 1.25rem;
        --space-6: 1.5rem;
        --space-8: 2rem;
        --space-10: 2.5rem;
        --space-12: 3rem;
    }

    .stApp, .main > div {
        background: var(--bg-primary) !important;
        font-family: var(--font-family) !important;
    }
    * { font-family: var(--font-family) !important; }
    .material-symbols-outlined,
    [data-testid="collapsedControl"] * {
        font-family: 'Material Symbols Outlined', sans-serif !important;
    }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    [data-testid="stHeader"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    .stApp { background: var(--bg-primary) !important; }
    .block-container {
        padding: var(--space-8) var(--space-10) !important;
        max-width: 1320px !important;
    }

    /* ── Typography ── */
    h1 {
        color: var(--text-bright) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.04em !important;
        margin-bottom: var(--space-2) !important;
        line-height: 1.15 !important;
    }
    h2 {
        color: var(--text-primary) !important;
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.3 !important;
        margin-bottom: var(--space-4) !important;
    }
    h3 {
        color: var(--text-primary) !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        line-height: 1.4 !important;
    }
    h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    p, li, .stMarkdown {
        color: var(--text-secondary) !important;
        line-height: 1.65 !important;
        font-size: 0.875rem !important;
    }
    .stCaption {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        line-height: 1.5 !important;
    }
    a {
        color: var(--accent) !important;
        text-decoration: none !important;
        transition: var(--transition) !important;
    }
    a:hover { color: var(--accent-hover) !important; }
    strong, b {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #080E18 0%, #0B1120 60%, #111827 100%) !important;
        border-right: 1px solid rgba(30,41,59,0.4) !important;
        padding: var(--space-6) var(--space-4) !important;
        width: 270px !important;
    }
    section[data-testid="stSidebar"] > div { padding: 0 !important; }
    section[data-testid="stSidebar"] .stMarkdown { color: var(--text-secondary) !important; }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary) !important;
    }
    section[data-testid="stSidebar"] hr {
        border: none !important;
        border-top: 1px solid rgba(30,41,59,0.3) !important;
        margin: var(--space-3) 0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button { width: 100%; }
    section[data-testid="stSidebar"] .stButton > button:hover {
        transform: none;
    }
    section[data-testid="stSidebar"] .sidebar-stat {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 0.25rem 0 !important;
    }
    section[data-testid="stSidebar"] .sidebar-stat-label {
        color: #64748B !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] .sidebar-stat-value {
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .sidebar-logo-glow {
        box-shadow: 0 0 20px rgba(59,130,246,0.2) !important;
        border-radius: 12px !important;
    }

    /* ── Cards ── */
    div[data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        margin-bottom: var(--space-5) !important;
        overflow: hidden;
        transition: var(--transition) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
    }
    div[data-testid="stExpander"]:hover {
        border-color: rgba(59,130,246,0.2) !important;
    }
    div[data-testid="stExpander"] > details > summary {
        padding: var(--space-5) var(--space-6) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.01em !important;
    }
    div[data-testid="stExpander"] > details > div {
        padding: 0 var(--space-6) var(--space-6) !important;
    }
    .top-match div[data-testid="stExpander"] {
        border-color: rgba(59,130,246,0.3) !important;
        background: linear-gradient(135deg, rgba(59,130,246,0.02) 0%, var(--bg-card) 100%) !important;
    }

    .candidate-card {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: var(--space-6) !important;
        margin-bottom: var(--space-5) !important;
        transition: var(--transition) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
    }
    .candidate-card:hover {
        border-color: rgba(59,130,246,0.2) !important;
        transform: translateY(-2px);
    }
    .candidate-card.top-match {
        border-color: rgba(59,130,246,0.3) !important;
        background: linear-gradient(135deg, rgba(59,130,246,0.02) 0%, var(--bg-card) 100%) !important;
    }

    .compact-card {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 0.85rem !important;
        transition: var(--transition) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
        height: 100%;
    }
    .compact-card:hover {
        border-color: rgba(59,130,246,0.2) !important;
    }
    .compact-card.top-match {
        border-color: rgba(59,130,246,0.3) !important;
        background: linear-gradient(135deg, rgba(59,130,246,0.02) 0%, var(--bg-card) 100%) !important;
    }
    .expanded-details {
        margin-top: 0.5rem;
        animation: fadeIn 0.2s ease;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-radius: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
        border: none !important;
        border-bottom: 1px solid var(--border) !important;
        margin-bottom: var(--space-8) !important;
        box-shadow: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0 !important;
        padding: 0.75rem 1.25rem !important;
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: var(--transition) !important;
        border: none !important;
        background: transparent !important;
        letter-spacing: -0.01em !important;
        margin-bottom: -1px !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        border-bottom: 2px solid var(--accent) !important;
        border-radius: 0 !important;
    }
    .stTabs .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid var(--border) !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin-bottom: var(--space-6) !important;
        box-shadow: none !important;
    }
    .stTabs .stTabs [data-baseweb="tab"] {
        padding: var(--space-3) var(--space-4) !important;
        border-radius: 0 !important;
    }
    .stTabs .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent) !important;
        box-shadow: none !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        padding: 0.55rem 1.35rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: var(--transition) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        letter-spacing: -0.01em !important;
        cursor: pointer !important;
        line-height: 1.5 !important;
        min-height: 40px !important;
    }
    .stButton > button:hover {
        color: var(--text-primary) !important;
        border-color: var(--accent) !important;
        background: var(--accent-soft) !important;
        filter: brightness(1.1);
    }
    .stButton > button:active {
        filter: brightness(0.95) !important;
    }
    .stButton > button:focus-visible {
        outline: 2px solid var(--accent) !important;
        outline-offset: 2px !important;
    }
    .stButton > button:disabled {
        opacity: 0.4 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="primary"],
    .stButton > button[kind="primaryFormSubmit"],
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15) !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[kind="primaryFormSubmit"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, var(--accent-hover) 0%, #1D4ED8 100%) !important;
        border: none !important;
        filter: brightness(1.05);
    }
    .stButton > button[kind="primary"]:active,
    .stButton > button[kind="primaryFormSubmit"]:active,
    div[data-testid="stFormSubmitButton"] > button:active {
        filter: brightness(0.95) !important;
    }
    .stButton > button[kind="primary"]:disabled,
    .stButton > button[kind="primaryFormSubmit"]:disabled,
    div[data-testid="stFormSubmitButton"] > button:disabled {
        background: linear-gradient(135deg, #334155 0%, #475569 100%) !important;
        color: var(--text-muted) !important;
        box-shadow: none !important;
        opacity: 0.6 !important;
    }

    /* ── Add Candidate button (purple/indigo accent) ── */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
        filter: brightness(1) !important;
        transform: translateY(-1px);
    }

    .stDownloadButton > button {
        border-radius: var(--radius-sm) !important;
        padding: 0.55rem 1.35rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: var(--transition) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        min-height: 40px !important;
    }
    .stDownloadButton > button:hover {
        color: var(--text-primary) !important;
        border-color: var(--accent) !important;
        background: var(--accent-soft) !important;
        filter: brightness(1.1);
    }
    div.row-widget.stButton { margin-bottom: 0 !important; }

    /* button loading spinner */
    @keyframes btn-spin {
        to { transform: rotate(360deg); }
    }
    .stButton > button[kind="primary"] .btn-loading::after {
        content: '';
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: btn-spin 0.6s linear infinite;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* ── Inputs ── */
    .stTextInput, .stTextArea, .stSelectbox, .stNumberInput {
        margin-bottom: var(--space-4) !important;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.875rem !important;
        transition: var(--transition) !important;
        line-height: 1.5 !important;
        min-height: 44px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px var(--accent-glow) !important;
        background: var(--bg-card) !important;
    }
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.775rem !important;
        letter-spacing: 0.01em !important;
        margin-bottom: var(--space-2) !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
        font-weight: 400 !important;
        font-size: 0.85rem !important;
    }

    /* ── Number Input ── */
    .stNumberInput input {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
    }
    .stNumberInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    .stNumberInput button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        transition: var(--transition) !important;
    }
    .stNumberInput button:hover {
        background: var(--accent-soft) !important;
        border-color: var(--accent) !important;
        color: var(--text-primary) !important;
    }

    /* ── Slider ── */
    .stSlider div[data-baseweb="slider"] { background: transparent !important; }
    .stSlider div[role="slider"] {
        background: var(--accent) !important;
        border: 2px solid white !important;
        box-shadow: 0 2px 6px rgba(59,130,246,0.3) !important;
    }
    .stSlider .stMarkdown { color: var(--text-secondary) !important; }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        color: var(--text-bright) !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        letter-spacing: -0.03em !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    [data-testid="stMetricDelta"] { font-size: 0.8rem !important; font-weight: 500 !important; }
    div[data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: var(--space-5) var(--space-6) !important;
        transition: var(--transition) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
    }
    div[data-testid="metric-container"]:hover {
        border-color: rgba(59,130,246,0.2) !important;
    }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] {
        background: var(--bg-card) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
        overflow: hidden !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
    }
    [data-testid="stDataFrame"] table { font-size: 0.85rem !important; }
    [data-testid="stDataFrame"] thead tr th {
        background: var(--bg-secondary) !important;
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        padding: var(--space-3) var(--space-5) !important;
        border-bottom: 1px solid var(--border) !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
    }
    [data-testid="stDataFrame"] tbody tr td {
        padding: 0.75rem var(--space-5) !important;
        border-bottom: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(even) td {
        background: rgba(11,17,32,0.3) !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover td {
        background: var(--accent-soft) !important;
    }

    /* ── File Uploader ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 1.5px dashed rgba(59,130,246,0.25) !important;
        border-radius: 16px !important;
        padding: var(--space-12) var(--space-8) !important;
        text-align: center !important;
        transition: var(--transition) !important;
        cursor: pointer !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent) !important;
        background: rgba(59,130,246,0.04) !important;
    }
    [data-testid="stFileUploader"] section {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: var(--space-3) !important;
    }
    [data-testid="stFileUploader"] [data-testid="stMarkdown"] {
        color: var(--text-muted) !important;
        font-size: 0.875rem !important;
    }
    [data-testid="stFileUploader"] button {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--space-2) var(--space-6) !important;
        font-weight: 500 !important;
        transition: var(--transition) !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background: var(--accent-hover) !important;
        box-shadow: 0 4px 12px rgba(59,130,246,0.3) !important;
    }

    /* ── Progress Bars ── */
    .stProgress > div {
        background: var(--border) !important;
        border-radius: var(--radius-full) !important;
        height: 6px !important;
        overflow: hidden !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent), #60A5FA) !important;
        border-radius: var(--radius-full) !important;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* ── Custom Alerts (replace Streamlit defaults) ── */
    div[data-testid="stAlert"] {
        border-radius: var(--radius-sm) !important;
        border: none !important;
        padding: var(--space-3) var(--space-4) !important;
        font-size: 0.875rem !important;
    }
    .stAlert-success {
        background: var(--success-bg) !important;
        border-left: 3px solid var(--success) !important;
        color: var(--success) !important;
    }
    .stAlert-error {
        background: var(--danger-bg) !important;
        border-left: 3px solid var(--danger) !important;
        color: var(--danger) !important;
    }
    .stAlert-warning {
        background: var(--warning-bg) !important;
        border-left: 3px solid var(--warning) !important;
        color: var(--warning) !important;
    }
    .stAlert-info {
        background: var(--accent-soft) !important;
        border-left: 3px solid var(--accent) !important;
        color: var(--accent) !important;
    }

    /* ── Chat ── */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        border-radius: var(--radius) !important;
        padding: 0 !important;
        margin-bottom: var(--space-3) !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        color: var(--text-secondary) !important;
        line-height: 1.7 !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] code {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-xs) !important;
        padding: 2px 6px !important;
        font-size: 0.825rem !important;
        color: #A78BFA !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] pre {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--space-4) !important;
    }
    [data-testid="stFileUploader"] button span {
        display: none !important;
    }
    [data-testid="stFileUploader"] button::after {
        content: "Browse Files" !important;
        display: block !important;
    }

    /* ── Info / Warning / Error bare elements ── */
    .stInfo {
        background: var(--accent-soft) !important;
        border: 1px solid rgba(59,130,246,0.2) !important;
        border-left: 3px solid var(--accent) !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--space-3) var(--space-4) !important;
        color: var(--accent) !important;
    }
    .stWarning {
        background: var(--warning-bg) !important;
        border: 1px solid var(--warning-border) !important;
        border-left: 3px solid var(--warning) !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--space-3) var(--space-4) !important;
        color: var(--warning) !important;
    }
    .stError {
        background: var(--danger-bg) !important;
        border: 1px solid var(--danger-border) !important;
        border-left: 3px solid var(--danger) !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--space-3) var(--space-4) !important;
        color: var(--danger) !important;
    }
    .stSuccess {
        background: var(--success-bg) !important;
        border: 1px solid var(--success-border) !important;
        border-left: 3px solid var(--success) !important;
        border-radius: var(--radius-sm) !important;
        padding: var(--space-3) var(--space-4) !important;
        color: var(--success) !important;
    }

    /* ── Dividers ── */
    hr {
        border: none !important;
        border-top: 1px solid var(--border-light) !important;
        margin: var(--space-6) 0 !important;
    }

    /* ── Form ── */
    [data-testid="stForm"] {
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: var(--space-6) !important;
        background: var(--bg-card) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="InputInstructions"] { display: none !important; }

    /* ── Spinner ── */
    .stSpinner { color: var(--accent) !important; }

    /* ── Checkbox / Radio ── */
    .stCheckbox label, .stRadio label { color: var(--text-secondary) !important; }
    .stCheckbox input:checked ~ div { background: var(--accent) !important; }

    /* ── Selectbox dropdown ── */
    div[data-baseweb="select"] [data-baseweb="popover"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-lg) !important;
    }
    div[data-baseweb="select"] [data-baseweb="popover"] li {
        color: var(--text-secondary) !important;
        transition: var(--transition) !important;
    }
    div[data-baseweb="select"] [data-baseweb="popover"] li:hover {
        background: var(--accent-soft) !important;
        color: var(--text-primary) !important;
    }

    /* ── Plotly Chart containers ── */
    .stPlotlyChart {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: var(--space-5) !important;
        margin-bottom: var(--space-6) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
        transition: var(--transition) !important;
    }
    .stPlotlyChart:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important; }

    /* ── Balloons override ── */
    .balloon { opacity: 0.7 !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: var(--radius-full);
        transition: background 0.2s ease;
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ── Animations (minimal) ── */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes logoEntrance {
        0% { opacity: 0; transform: translateY(-8px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes skeleton-loading {
        0% { background-position: -200px 0; }
        100% { background-position: calc(200px + 100%) 0; }
    }
    .stApp > div {
        animation: fadeIn 0.2s ease;
    }
    .sidebar-logo-anim {
        animation: logoEntrance 0.4s ease-out forwards;
    }
    .sidebar-title-anim {
        animation: logoEntrance 0.4s ease-out forwards;
        animation-delay: 0.1s;
        opacity: 0;
    }

    /* ── Typing indicator for chat ── */
    .typing-dots span {
        display: inline-block;
        animation: typingDot 1.4s infinite both;
        font-size: 1.3rem;
        line-height: 1;
        color: #94A3B8;
    }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typingDot {
        0% { opacity: 0.2; }
        20% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    /* Chat input styling — match JD textarea blue accent */
    [data-testid="stChatInput"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px var(--accent-glow) !important;
    }

    /* ── Skeleton loading ── */
    .skeleton {
        background: linear-gradient(90deg, var(--bg-card) 25%, var(--bg-card-hover) 50%, var(--bg-card) 75%);
        background-size: 200px 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
        border-radius: var(--radius-sm);
    }
    .skeleton-line {
        height: 12px;
        margin-bottom: 8px;
        width: 100%;
    }
    .skeleton-line:last-child { width: 60%; }
    .skeleton-card {
        height: 180px;
        border-radius: var(--radius-lg);
        margin-bottom: var(--space-4);
    }

    /* ── Focus visible for accessibility ── */
    *:focus-visible {
        outline: 2px solid var(--accent) !important;
        outline-offset: 2px !important;
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .block-container {
            padding: var(--space-4) var(--space-3) !important;
        }
        h1 { font-size: 1.5rem !important; }
    }
    </style>""", unsafe_allow_html=True)


# ============================================================
# HTML Utility Components
# ============================================================


def skill_badge(skill: str, badge_type: str = "matched") -> str:
    colors = {
        "matched": {
            "bg": "rgba(34,197,94,0.12)",
            "text": "#4ADE80",
            "border": "rgba(34,197,94,0.3)",
            "icon": "✓",
        },
        "missing": {
            "bg": "rgba(245,158,11,0.12)",
            "text": "#F59E0B",
            "border": "rgba(245,158,11,0.3)",
            "icon": "✕",
        },
        "bonus": {
            "bg": "rgba(59,130,246,0.12)",
            "text": "#60A5FA",
            "border": "rgba(59,130,246,0.3)",
            "icon": "+",
        },
    }
    c = colors.get(badge_type, colors["matched"])
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{c["bg"]};'
        f'color:{c["text"]};border:1px solid {c["border"]};'
        f'border-radius:9999px;padding:3px 12px;font-size:0.78rem;'
        f'font-weight:500;margin:2px 4px 2px 0;'
        f'white-space:nowrap;line-height:1.4;'
        f'transition:all 0.15s ease;cursor:default;"'
        f'onmouseover="this.style.filter=\'brightness(1.15)\'"'
        f'onmouseout="this.style.filter=\'brightness(1)\'"'
        f'>'
        f'<span style="font-size:0.55rem;font-weight:700;opacity:0.8;">{c["icon"]}</span>'
        f'{skill}</span>'
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
        f'<div style="background:rgba(30,41,59,0.5);border-radius:9999px;height:5px;'
        f'overflow:hidden;margin:3px 0;">'
        f'<div style="width:{pct:.0f}%;background:linear-gradient(90deg, {color}, {color}cc);'
        f'height:100%;border-radius:9999px;'
        f'transition:width 0.4s ease;"></div></div>'
    )
    if label:
        header = (
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;font-size:0.78rem;color:#94A3B8;margin-bottom:2px;">'
            f'<span style="font-weight:500;">{label}</span>'
            f'<span style="font-weight:600;color:#F1F5F9;font-size:0.85rem;">{value:.1f}</span></div>'
        )
        return header + bar
    return bar


def question_card(question: str, q_type: str = "technical", index: int = 1, difficulty: str = "medium") -> str:
    type_config = {
        "technical": {"icon": "💻", "color": "#3B82F6", "bg": "rgba(59,130,246,0.08)", "label": "Technical"},
        "behavioral": {"icon": "🧠", "color": "#8B5CF6", "bg": "rgba(139,92,246,0.08)", "label": "Behavioral"},
        "experience": {"icon": "🔍", "color": "#F59E0B", "bg": "rgba(245,158,11,0.08)", "label": "Experience"},
        "leadership": {"icon": "👥", "color": "#22C55E", "bg": "rgba(34,197,94,0.08)", "label": "Leadership"},
        "system_design": {"icon": "🏗️", "color": "#06B6D4", "bg": "rgba(6,182,212,0.08)", "label": "System Design"},
        "communication": {"icon": "💬", "color": "#3B82F6", "bg": "rgba(59,130,246,0.08)", "label": "Communication"},
        "machine_learning": {"icon": "🤖", "color": "#A855F7", "bg": "rgba(168,85,247,0.08)", "label": "Machine Learning"},
    }
    difficulty_config = {
        "easy": {"color": "#22C55E", "bg": "rgba(34,197,94,0.1)", "label": "Easy"},
        "medium": {"color": "#F59E0B", "bg": "rgba(245,158,11,0.1)", "label": "Medium"},
        "hard": {"color": "#7C3AED", "bg": "rgba(124,58,237,0.1)", "label": "Hard"},
    }
    cfg = type_config.get(q_type, type_config["technical"])
    diff = difficulty_config.get(difficulty, difficulty_config["medium"])

    qid = f"q_{index}_{hash(question) % 10000}"

    return f"""
    <div style="background:#111827;border:1px solid #1E293B;border-radius:12px;
                padding:1rem 1.25rem;margin-bottom:0.75rem;
                border-left:4px solid {cfg['color']};
                transition:all 0.15s ease;
                cursor:default;box-shadow:0 1px 3px rgba(0,0,0,0.1);"
         onmouseover="this.style.borderColor='{cfg['color']}'"
         onmouseout="this.style.borderColor='#1E293B';this.style.borderLeftColor='{cfg['color']}'">
        <div style="display:flex;align-items:flex-start;gap:0.75rem;">
            <div style="background:{cfg['bg']};border-radius:10px;width:36px;height:36px;
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;
                        font-size:1rem;">
                {cfg['icon']}
            </div>
            <div style="flex:1;min-width:0;">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.35rem;flex-wrap:wrap;">
                    <span style="background:{cfg['bg']};color:{cfg['color']};
                                font-size:0.65rem;font-weight:600;
                                text-transform:uppercase;letter-spacing:0.06em;
                                padding:2px 8px;border-radius:4px;">
                        {cfg['label']}
                    </span>
                    <span style="background:{diff['bg']};color:{diff['color']};
                                font-size:0.65rem;font-weight:600;
                                padding:2px 8px;border-radius:4px;">
                        {diff['label']}
                    </span>
                    <span style="color:#64748B;font-size:0.72rem;font-weight:500;">
                        Q{index}
                    </span>
                    <button onclick="navigator.clipboard.writeText(document.getElementById('{qid}').innerText)"
                            style="margin-left:auto;background:transparent;border:1px solid #1E293B;
                                   border-radius:6px;padding:2px 8px;cursor:pointer;color:#64748B;
                                   font-size:0.7rem;transition:all 0.15s ease;"
                            onmouseover="this.style.borderColor='#3B82F6';this.style.color='#3B82F6'"
                            onmouseout="this.style.borderColor='#1E293B';this.style.color='#64748B'"
                            title="Copy question">📋 Copy</button>
                </div>
                <p id="{qid}" style="color:#CBD5E1;margin:0;line-height:1.65;font-size:0.9rem;">
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
            '<span style="display:inline-block;width:6px;height:6px;'
            'background:#22C55E;border-radius:50%;margin-right:8px;'
            'box-shadow:0 0 6px rgba(34,197,94,0.3);"></span>'
        )
    return (
        '<span style="display:inline-block;width:6px;height:6px;'
        'background:#EF4444;border-radius:50%;margin-right:8px;"></span>'
    )


def kpi_card(icon: str, value: str, label: str, color: str = "#3B82F6", trend: str = "") -> str:
    trend_html = ""
    if trend:
        trend_color = "#22C55E" if trend.startswith("+") else "#F59E0B" if trend.startswith("-") else "#94A3B8"
        trend_html = (
            f'<span style="font-size:0.7rem;font-weight:600;color:{trend_color};'
            f'margin-left:6px;padding:1px 6px;border-radius:4px;'
            f'background:{trend_color}15;">{trend}</span>'
        )

    return (
        f'<div style="background:#111827;border:1px solid #1E293B;border-radius:12px;'
        f'padding:1.15rem 1.25rem;transition:all 0.15s ease;'
        f'cursor:default;position:relative;overflow:hidden;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.15);"'
        f'onmouseover="this.style.borderColor=\'{color}30\';'
        f'this.style.boxShadow=\'0 4px 16px rgba(0,0,0,0.2)\';'
        f'this.style.transform=\'translateY(-1px)\'"'
        f'onmouseout="this.style.borderColor=\'#1E293B\';'
        f'this.style.boxShadow=\'0 1px 3px rgba(0,0,0,0.15)\';'
        f'this.style.transform=\'translateY(0)\'">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">'
        f'<div style="width:36px;height:36px;border-radius:10px;'
        f'background:{color}12;display:flex;align-items:center;justify-content:center;'
        f'font-size:1rem;">{icon}</div>'
        f'<span style="font-size:0.65rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.06em;color:#64748B;">{label}</span>'
        f'</div>'
        f'<div style="display:flex;align-items:baseline;gap:6px;">'
        f'<span style="font-size:1.75rem;font-weight:700;color:#F1F5F9;'
        f'letter-spacing:-0.03em;line-height:1.2;">{value}</span>'
        f'{trend_html}'
        f'</div></div>'
    )


def empty_state(icon: str, title: str, description: str, action_text: str = "") -> str:
    action_html = ""
    if action_text:
        action_html = (
            f'<p style="margin:1rem 0 0;font-size:0.85rem;color:#3B82F6;'
            f'font-weight:500;cursor:default;">{action_text} →</p>'
        )
    return (
        f'<div style="text-align:center;padding:3rem 2rem;max-width:420px;'
        f'margin:2rem auto;background:rgba(30,41,59,0.2);border:1px solid rgba(51,65,85,0.2);'
        f'border-radius:12px;">'
        f'<div style="font-size:3.5rem;margin-bottom:1rem;opacity:0.6;'
        f'line-height:1;">{icon}</div>'
        f'<h3 style="color:#F1F5F9;margin:0 0 0.5rem;font-size:1.15rem;font-weight:600;">{title}</h3>'
        f'<p style="color:#64748B;margin:0;font-size:0.9rem;line-height:1.6;">{description}</p>'
        f'{action_html}</div>'
    )


def section_header(title: str, subtitle: str = "") -> str:
    subtitle_html = ""
    if subtitle:
        subtitle_html = (
            f'<p style="color:#64748B;margin:0.2rem 0 0;font-size:0.85rem;'
            f'line-height:1.5;font-weight:400;max-width:600px;">{subtitle}</p>'
        )
    return (
        f'<div style="margin-bottom:var(--space-6);">'
        f'<h1 style="margin:0;font-size:1.75rem;font-weight:700;'
        f'letter-spacing:-0.03em;color:#FFFFFF;">{title}</h1>'
        f'{subtitle_html}</div>'
    )


def candidate_avatar(name: str, rank: int = 0, size: int = 44) -> str:
    """
    Render a candidate avatar placeholder with initials.

    Args:
        name: Candidate full name.
        rank: Candidate rank (0 for no rank).
        size: Avatar size in pixels.

    Returns:
        HTML string.
    """
    initials = "".join([w[0].upper() for w in name.split()[:2]]) if name and name.strip() else "?"
    colors = ["#3B82F6", "#8B5CF6", "#A855F7", "#22C55E", "#F59E0B", "#06B6D4", "#60A5FA"]
    color = colors[hash(name) % len(colors)] if name else "#3B82F6"
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:12px;'
        f'background:linear-gradient(135deg, {color}, {color}cc);'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:{size//3}px;font-weight:700;color:white;'
        f'flex-shrink:0;letter-spacing:0.02em;'
        f'box-shadow:0 2px 8px {color}30;">{initials}</div>'
    )


def loading_skeleton(lines: int = 3, card: bool = False) -> str:
    if card:
        return '<div class="skeleton skeleton-card"></div>'
    skeleton_lines = ""
    for _ in range(lines):
        skeleton_lines += '<div class="skeleton skeleton-line"></div>'
    return f'<div style="padding:1rem 0;">{skeleton_lines}</div>'


def alert_card(message: str, alert_type: str = "info") -> str:
    """
    Render a custom alert card with icon.

    Args:
        message: Alert message text.
        alert_type: One of "success", "warning", "error", "info".

    Returns:
        HTML string.
    """
    config = {
        "success": {"icon": "✓", "color": "#22C55E", "bg": "rgba(34,197,94,0.08)", "border": "rgba(34,197,94,0.2)"},
        "warning": {"icon": "⚠", "color": "#F59E0B", "bg": "rgba(245,158,11,0.08)", "border": "rgba(245,158,11,0.2)"},
        "error": {"icon": "✕", "color": "#EF4444", "bg": "rgba(239,68,68,0.08)", "border": "rgba(239,68,68,0.2)"},
        "info": {"icon": "ℹ", "color": "#3B82F6", "bg": "rgba(59,130,246,0.08)", "border": "rgba(59,130,246,0.2)"},
    }
    c = config.get(alert_type, config["info"])
    return (
        f'<div style="background:{c["bg"]};border:1px solid {c["border"]};'
        f'border-left:3px solid {c["color"]};border-radius:8px;'
        f'padding:0.75rem 1rem;display:flex;align-items:center;gap:0.75rem;'
        f'margin:0.5rem 0;">'
        f'<span style="color:{c["color"]};font-size:1rem;font-weight:700;'
        f'flex-shrink:0;">{c["icon"]}</span>'
        f'<span style="color:{c["color"]};font-size:0.875rem;font-weight:500;">'
        f'{message}</span></div>'
    )


# ============================================================
# Plotly Theme Helper
# ============================================================


def apply_dark_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94A3B8", "family": "Inter, system-ui, -apple-system, sans-serif", "size": 11},
        title={"font": {"color": "#F1F5F9", "size": 14, "family": "Inter, sans-serif"}, "x": 0, "xanchor": "left"},
        xaxis={
            "gridcolor": "rgba(30,41,59,0.4)",
            "gridwidth": 1,
            "zerolinecolor": "rgba(30,41,59,0.4)",
            "zerolinewidth": 1,
            "tickfont": {"color": "#64748B", "size": 11},
            "title": {"font": {"color": "#94A3B8", "size": 11}},
        },
        yaxis={
            "gridcolor": "rgba(30,41,59,0.4)",
            "gridwidth": 1,
            "zerolinecolor": "rgba(30,41,59,0.4)",
            "zerolinewidth": 1,
            "tickfont": {"color": "#64748B", "size": 11},
            "title": {"font": {"color": "#94A3B8", "size": 11}},
        },
        legend={"font": {"color": "#94A3B8", "size": 11}, "bgcolor": "rgba(0,0,0,0)"},
        coloraxis={"colorbar": {"tickfont": {"color": "#64748B", "size": 10}}},
        hoverlabel={
            "bgcolor": "#111827",
            "font": {"color": "#F1F5F9", "size": 12, "family": "Inter, sans-serif"},
            "bordercolor": "#1E293B",
        },
        margin={"t": 20, "b": 40, "l": 40, "r": 16},
        dragmode=False,
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
        resp = requests.get(f"{API_BASE_URL}{endpoint}", timeout=120)
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
            f"{API_BASE_URL}{endpoint}", files=files, timeout=12000
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
        f'<div style="display:flex;align-items:flex-start;gap:1rem;margin-bottom:0.25rem;">'
        f'<div class="sidebar-logo-anim" style="width:48px;height:48px;border-radius:12px;'
        f'background:linear-gradient(135deg, #3B82F6, #2563EB);'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:1.5rem;box-shadow:0 0 20px rgba(59,130,246,0.2);">🔄</div>'
        f'<div class="sidebar-title-anim">'
        f'<h2 style="margin:0;font-size:1.5rem !important;letter-spacing:-0.03em;'
        f'color:#F1F5F9 !important;">{APP_NAME}</h2>'
        f'<p style="margin:0;font-size:0.65rem;color:#64748B;font-weight:500;'
        f'letter-spacing:0.02em;">AI Recruitment Platform</p>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr style="margin:0.5rem 0;" />', unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:0.6rem;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.08em;color:#475569;margin:0 0 0.5rem 0;">System</p>',
        unsafe_allow_html=True,
    )

    if health:
        st.markdown(
            f'<div style="display:flex;flex-direction:column;gap:0.15rem;">'
            f'<div class="sidebar-stat">'
            f'<span class="sidebar-stat-label">🔌 API</span>'
            f'<span style="display:flex;align-items:center;gap:4px;">'
            f'{status_indicator(True)}'
            f'<span style="color:#22C55E;font-size:0.7rem;font-weight:500;">Online</span></span></div>'
            f'<div class="sidebar-stat">'
            f'<span class="sidebar-stat-label">🗄️ Database</span>'
            f'<span style="display:flex;align-items:center;gap:4px;">'
            f'{status_indicator(True)}'
            f'<span style="color:#22C55E;font-size:0.7rem;font-weight:500;">Connected</span></span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="sidebar-stat">'
            f'<span class="sidebar-stat-label">🔌 API</span>'
            f'<span style="display:flex;align-items:center;gap:4px;">'
            f'{status_indicator(False)}'
            f'<span style="color:#EF4444;font-size:0.7rem;font-weight:500;">Offline</span></span></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="margin:0.5rem 0;" />', unsafe_allow_html=True)

    candidate_count = _fetch_candidate_count()
    st.markdown(
        '<p style="font-size:0.6rem;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.08em;color:#475569;margin:0 0 0.5rem 0;">Overview</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="sidebar-stat">'
        f'<span class="sidebar-stat-label">👥 Candidates</span>'
        f'<span style="color:#F1F5F9;font-weight:700;font-size:0.9rem;">{candidate_count}</span></div>',
        unsafe_allow_html=True,
    )

    if health:
        version_str = health.get("version", "1.0")
        st.markdown(
            f'<div class="sidebar-stat" style="margin-top:0.25rem;">'
            f'<span class="sidebar-stat-label">📦 Version</span>'
            f'<span style="color:#94A3B8;font-size:0.7rem;font-weight:500;">v{version_str}</span></div>'
            f'<div class="sidebar-stat">'
            f'<span class="sidebar-stat-label">⚡ Status</span>'
            f'<span style="color:#22C55E;font-size:0.7rem;font-weight:500;">Operational</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<hr style="margin:0.5rem 0;" />'
        '<div style="text-align:center;padding:0.25rem 0;">'
        '<p style="font-size:0.62rem;color:#475569;margin:0;">Powered by</p>'
        '<p style="font-size:0.65rem;color:#64748B;font-weight:500;margin:0.1rem 0 0;">'
        'Multi-Agent AI System</p></div>',
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
    # ── Header Row ──
    col_heading, col_count = st.columns([3, 1])
    with col_heading:
        st.markdown(
            section_header(
                "Find Candidates",
                "Paste a job description to match candidates using AI-powered analysis."
            ),
            unsafe_allow_html=True,
        )
    with col_count:
        st.markdown(
            kpi_card("👥", str(_fetch_candidate_count()), "In Database", "#3B82F6"),
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

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
            '<p style="margin-bottom:0.25rem;font-size:0.85rem;color:#94A3B8;'
            'font-weight:500;">&nbsp;</p>',
            unsafe_allow_html=True,
        )
        run_clicked = st.button(
            "🔍  Find Best Candidates",
            key="find_candidates",
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

            progress_bar.progress(10, text="🔍 Analysing job description...")
            progress_bar.progress(30, text="🔎 Searching for matching candidates...")
            progress_bar.progress(50, text="📊 Scoring candidates...")
            progress_bar.progress(70, text="🧩 Analysing skill gaps...")
            progress_bar.progress(90, text="📋 Building ranked shortlist...")

            result = api_post("/api/recruit", {
                "job_description": jd_text,
                "top_k": top_k,
            })

            progress_bar.progress(100, text="✅ Done!")
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
    else:
        st.markdown(
            empty_state(
                "🔍",
                "No Results Yet",
                "Paste a job description above and click 'Find Best Candidates' to get AI-powered candidate matching.",
                "Your ranked candidates will appear here."
            ),
            unsafe_allow_html=True,
        )


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
        st.markdown(
            empty_state(
                "📭",
                "No Matching Candidates",
                "No candidates matched the job description. Try broadening the requirements or adding more candidates to the database.",
                "Upload resumes or add candidates manually."
            ),
            unsafe_allow_html=True,
        )
        return

    candidate_count = _fetch_candidate_count()
    top_score = shortlist[0]["final_score"]
    avg_score = sum(e["final_score"] for e in shortlist) / len(shortlist)

    # ── Divider ──
    st.markdown('<hr style="margin:1.5rem 0;" />', unsafe_allow_html=True)

    # ── Results Overview ──
    st.markdown(
        '<h2 style="margin-bottom:1.25rem;">Results Overview</h2>',
        unsafe_allow_html=True,
    )

    # ── KPI Cards ──
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(
            kpi_card("🎯", str(len(shortlist)), "Candidates Found", "#3B82F6"),
            unsafe_allow_html=True,
        )
    with kpi_cols[1]:
        st.markdown(
            kpi_card("🗄️", str(candidate_count), "Database Size", "#8B5CF6"),
            unsafe_allow_html=True,
        )
    with kpi_cols[2]:
        st.markdown(
            kpi_card("🏆", f"{top_score:.1f}", "Top Score", "#22C55E"),
            unsafe_allow_html=True,
        )
    with kpi_cols[3]:
        st.markdown(
            kpi_card("⚡", f"{processing_time:.0f}ms", "Processing Time", "#F59E0B"),
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    # ── Score chart ──
    _display_score_chart(shortlist)

    # ── Export button ──
    _display_export_button(shortlist)

    # ── Ranked candidate cards ──
    st.markdown(
        '<div style="margin-top:1.5rem;">'
        '<h2 style="margin-bottom:0.5rem;">Ranked Candidates</h2>'
        '<p style="color:#64748B;font-size:0.85rem;margin:0 0 1.25rem;">AI-ranked by overall match score</p></div>',
        unsafe_allow_html=True,
    )

    # Pre-fetch all candidate details once to avoid N+1 API calls
    candidate_details = {}
    for entry in shortlist:
        cid = entry["candidate_id"]
        detail = api_get(f"/api/candidates/{cid}")
        candidate_details[cid] = detail

    if "expanded_cards" not in st.session_state:
        st.session_state.expanded_cards = set()

    # Render candidates in a 2-column grid
    num_candidates = len(shortlist)
    for i in range(0, num_candidates, 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx >= num_candidates:
                break
            entry = shortlist[idx]
            is_top = entry["rank"] == 1
            cid = entry["candidate_id"]
            detail = candidate_details.get(cid)

            c_name = f"Candidate #{cid}"
            c_exp = ""
            c_loc = ""
            if detail and detail.get("candidate"):
                c = detail["candidate"]
                c_name = c.get("name", c_name)
                c_exp = c.get("experience_years", "")
                c_loc = c.get("location", "")

            skill_gap = entry.get("skill_gap", {})
            matched = skill_gap.get("matched", [])
            missing = skill_gap.get("missing", [])
            bonus = skill_gap.get("bonus", [])

            final_score = entry['final_score']
            bar_color = "#22C55E" if final_score >= 80 else "#F59E0B" if final_score >= 60 else "#3B82F6"

            explanation = entry.get("explanation", "")
            explanation_short = explanation
            if len(explanation) > 120:
                explanation_short = explanation[:117] + "..."

            with cols[j]:
                card_class = "compact-card" + (" top-match" if is_top else "")

                top_badge = ""
                if is_top:
                    top_badge = (
                        '<div style="margin-bottom:0.5rem;">'
                        '<span style="background:rgba(59,130,246,0.08);'
                        'color:#60A5FA;border:1px solid rgba(59,130,246,0.2);border-radius:6px;'
                        'padding:2px 8px;font-size:0.62rem;font-weight:600;'
                        'text-transform:uppercase;letter-spacing:0.05em;'
                        'display:inline-flex;align-items:center;gap:4px;">'
                         '<span style="font-size:0.65rem;">🏆</span> Top Match</span></div>'
                    )

                card_html = f'<div class="{card_class}">'
                card_html += top_badge
                card_html += (
                    f'<div style="display:flex;align-items:center;gap:0.75rem;">'
                    f'{candidate_avatar(c_name, entry["rank"], size=36)}'
                    f'<div style="flex:1;min-width:0;">'
                    f'<h4 style="margin:0;font-size:0.9rem;color:#F1F5F9;font-weight:600;">{c_name}</h4>'
                    f'<div style="display:flex;gap:0.5rem;margin-top:0.1rem;flex-wrap:wrap;">'
                    + (f'<span style="color:#64748B;font-size:0.7rem;display:flex;align-items:center;gap:3px;">📌 {c_loc}</span>' if c_loc else '')
                    + (f'<span style="color:#64748B;font-size:0.7rem;display:flex;align-items:center;gap:3px;">💼 {c_exp}y exp</span>' if c_exp else '')
                    + f'</div></div>'
                    f'<div style="text-align:right;flex-shrink:0;">'
                    f'<span style="font-size:1.35rem;font-weight:700;'
                    f'color:{bar_color};'
                    f'letter-spacing:-0.03em;">{final_score:.1f}</span>'
                    f'<p style="margin:0;font-size:0.55rem;color:#64748B;font-weight:600;'
                    f'text-transform:uppercase;letter-spacing:0.04em;">Score</p>'
                    f'</div></div>'
                )
                card_html += '<div style="margin:0.5rem 0;">'
                card_html += score_progress_bar(final_score, 100, bar_color, "Overall")
                card_html += score_progress_bar(entry["semantic_score"], 100, "#3B82F6", "Semantic")
                card_html += score_progress_bar(entry["skill_score"], 100, "#7C3AED", "Skill")
                card_html += score_progress_bar(entry["signal_score"], 100, "#06B6D4", "Signal")
                card_html += '</div>'

                card_html += '<div style="margin:0.35rem 0;">'
                if matched:
                    shown = matched[:3]
                    remaining = len(matched) - 3
                    for s in shown:
                        card_html += skill_badge(s, "matched")
                    if remaining > 0:
                        card_html += (
                            f'<span style="display:inline-flex;align-items:center;gap:5px;'
                            f'background:rgba(30,41,59,0.5);color:#94A3B8;'
                            f'border:1px solid rgba(30,41,59,0.5);border-radius:9999px;'
                            f'padding:3px 10px;font-size:0.72rem;font-weight:500;'
                            f'margin:2px 4px 2px 0;">+{remaining} more</span>'
                        )
                card_html += '</div>'

                if explanation:
                    card_html += (
                        f'<div style="background:rgba(59,130,246,0.03);border:1px solid rgba(30,41,59,0.4);'
                        f'border-radius:8px;padding:0.5rem 0.65rem;margin:0.4rem 0;">'
                        f'<p style="color:#94A3B8;margin:0;font-size:0.72rem;line-height:1.4;'
                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                        f'💡 {explanation_short}</p></div>'
                    )

                card_html += '</div>'

                st.markdown(card_html, unsafe_allow_html=True)

                is_expanded = cid in st.session_state.expanded_cards
                btn_label = "▲  View Details" if is_expanded else "▼  View Details"
                if st.button(btn_label, key=f"vd_{cid}_{entry['rank']}", use_container_width=True):
                    if cid in st.session_state.expanded_cards:
                        st.session_state.expanded_cards.discard(cid)
                    else:
                        st.session_state.expanded_cards.add(cid)
                    st.rerun()

                if is_expanded:
                    details_html = '<div class="expanded-details">'
                    all_skills_html = ""
                    if matched or missing or bonus:
                        all_skills_html = (
                            '<div style="background:rgba(11,17,32,0.3);border:1px solid rgba(30,41,59,0.3);'
                            'border-radius:10px;padding:0.65rem 0.85rem;margin-top:0.5rem;">'
                        )
                        if matched:
                            all_skills_html += (
                                '<div style="margin-bottom:0.25rem;">'
                                '<p style="margin:0 0 0.2rem;font-size:0.6rem;color:#4ADE80;font-weight:600;'
                                'text-transform:uppercase;letter-spacing:0.05em;display:flex;align-items:center;gap:4px;">'
                                '<span>✓</span> Matched</p>'
                                '<div style="display:flex;flex-wrap:wrap;gap:2px;">'
                            )
                            for s in matched:
                                all_skills_html += skill_badge(s, "matched")
                            all_skills_html += '</div></div>'
                        if missing:
                            all_skills_html += (
                                '<div style="margin-bottom:0.25rem;">'
                                '<p style="margin:0 0 0.2rem;font-size:0.6rem;color:#F59E0B;font-weight:600;'
                                'text-transform:uppercase;letter-spacing:0.05em;display:flex;align-items:center;gap:4px;">'
                                '<span>✕</span> Missing</p>'
                                '<div style="display:flex;flex-wrap:wrap;gap:2px;">'
                            )
                            for s in missing:
                                all_skills_html += skill_badge(s, "missing")
                            all_skills_html += '</div></div>'
                        if bonus:
                            all_skills_html += (
                                '<div>'
                                '<p style="margin:0 0 0.2rem;font-size:0.6rem;color:#60A5FA;font-weight:600;'
                                'text-transform:uppercase;letter-spacing:0.05em;display:flex;align-items:center;gap:4px;">'
                                '<span>+</span> Bonus</p>'
                                '<div style="display:flex;flex-wrap:wrap;gap:2px;">'
                            )
                            for s in bonus:
                                all_skills_html += skill_badge(s, "bonus")
                            all_skills_html += '</div></div>'
                        all_skills_html += '</div>'
                    details_html += all_skills_html

                    if explanation and len(explanation) > 120:
                        details_html += (
                            f'<div style="background:rgba(59,130,246,0.03);border:1px solid rgba(30,41,59,0.5);'
                            f'border-radius:10px;padding:0.75rem 0.85rem;margin:0.5rem 0;">'
                            f'<div style="display:flex;align-items:flex-start;gap:0.6rem;">'
                            f'<span style="font-size:0.8rem;flex-shrink:0;margin-top:1px;">💡</span>'
                            f'<div>'
                            f'<p style="color:#64748B;margin:0 0 0.15rem;font-size:0.62rem;font-weight:600;'
                            f'text-transform:uppercase;letter-spacing:0.05em;">AI Analysis</p>'
                            f'<p style="color:#CBD5E1;margin:0;font-size:0.8rem;line-height:1.6;">'
                            f'{explanation}</p></div></div></div>'
                        )

                    details_html += '</div>'
                    st.markdown(details_html, unsafe_allow_html=True)

                act_cols = st.columns([1, 1])
                with act_cols[0]:
                    iq_key = f"iq_{cid}_{entry['rank']}"
                    if st.button("🎤  Interview Qs", key=iq_key, use_container_width=True):
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
                                    st.error("Failed to generate interview questions.")
                            else:
                                st.error(f"Could not fetch details for candidate #{cid}.")

                with act_cols[1]:
                    st.button(
                        "📝  Feedback",
                        disabled=True,
                        key=f"fb_{cid}_{entry['rank']}",
                        use_container_width=True,
                        help="Feedback will be enabled in a future update.",
                    )

                if cid in st.session_state.interview_questions:
                    questions = st.session_state.interview_questions[cid]
                    st.markdown(
                        '<div style="margin-top:0.75rem;padding:0.65rem;background:rgba(11,17,32,0.3);'
                        'border:1px solid rgba(30,41,59,0.3);border-radius:10px;">'
                        '<div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.65rem;">'
                        '<span style="font-size:0.9rem;">🎤</span>'
                        '<h4 style="margin:0;font-size:0.8rem;">Interview Questions</h4>'
                        '<span style="background:rgba(59,130,246,0.1);color:#60A5FA;'
                        'border-radius:9999px;padding:1px 8px;font-size:0.65rem;'
                        f'font-weight:600;">{len(questions)}</span></div>',
                        unsafe_allow_html=True,
                    )
                    for qi, q in enumerate(questions, 1):
                        q_type = ["technical", "behavioral", "experience"][qi % 3]
                        st.markdown(
                            question_card(q, q_type=q_type, index=qi),
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
        title="",
        color="Final Score",
        color_continuous_scale=["#1E293B", "#3B82F6", "#7C3AED"],
        text_auto=".1f",
    )
    fig = apply_dark_theme(fig)
    fig.update_traces(
        textfont={"color": "white", "size": 11, "family": "Inter, sans-serif"},
        marker_line={"width": 0},
        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>",
    )
    fig.update_layout(
        showlegend=False,
        margin={"t": 12, "b": 40, "l": 40, "r": 16},
        xaxis={"categoryorder": "array", "categoryarray": chart_data["Candidate"].tolist()},
    )
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

    col_exp1, col_exp2, col_exp3 = st.columns([2, 2, 2])
    with col_exp2:
        st.download_button(
            "📥  Export to CSV",
            data=csv_buffer.getvalue(),
            file_name="recruitx_shortlist.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ============================================================
# Tab 2: Chat with RecruitX
# ============================================================


def render_chat_tab() -> None:
    from datetime import datetime

    st.markdown(
        section_header(
            "Chat with RecruitX",
            "Ask natural language questions about your candidates and recruitment pipeline."
        ),
        unsafe_allow_html=True,
    )

    chat_loading = st.session_state.get("chat_loading", False)

    # ── Chat history container ──
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            is_user = msg["role"] == "user"
            avatar_icon = "👤" if is_user else "🤖"
            avatar_label = "You" if is_user else "RecruitX"
            ts = msg.get("timestamp", "")
            ts_html = f'<span style="font-size:0.65rem;color:#475569;margin-top:4px;">{ts}</span>' if ts else ""

            bubble_bg = "linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.04) 100%)" if is_user else "var(--bg-card)"
            bubble_border = "1px solid rgba(59,130,246,0.2)" if is_user else "1px solid var(--border-light)"

            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:1rem;'
                f'flex-direction:{"row-reverse" if is_user else "row"};">'
                f'<div style="width:34px;height:34px;border-radius:10px;flex-shrink:0;'
                f'background:{"linear-gradient(135deg, #3B82F6, #2563EB)" if is_user else "linear-gradient(135deg, #22C55E, #16A34A)"};'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:0.85rem;box-shadow:0 2px 6px {("rgba(59,130,246,0.3)" if is_user else "rgba(34,197,94,0.3)")};">'
                f'{avatar_icon}</div>'
                f'<div style="max-width:75%;">'
                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:4px;'
                f'justify-content:{"flex-end" if is_user else "flex-start"};">'
                f'<span style="font-size:0.72rem;font-weight:600;color:#64748B;">{avatar_label}</span>'
                f'{ts_html}</div>'
                f'<div style="background:{bubble_bg};border:{bubble_border};'
                f'border-radius:{"16px 16px 4px 16px" if is_user else "16px 16px 16px 4px"};'
                f'padding:0.85rem 1.1rem;">'
                f'<div style="color:#CBD5E1;font-size:0.875rem;line-height:1.65;">{msg["content"]}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )

    # Inline typing indicator shown during API call
    if chat_loading:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">'
            f'<div style="width:34px;height:34px;border-radius:10px;flex-shrink:0;'
            f'background:linear-gradient(135deg, #22C55E, #16A34A);'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.85rem;box-shadow:0 2px 6px rgba(34,197,94,0.3);">🤖</div>'
            f'<div style="color:#94A3B8;font-size:0.875rem;">RecruitX is thinking'
            f'<span class="typing-dots" style="display:inline-flex;gap:2px;margin-left:2px;">'
            f'<span>.</span><span>.</span><span>.</span></span></div></div>',
            unsafe_allow_html=True,
        )

    # Chat input (disabled while loading — prevents dim overlay)
    prompt = st.chat_input(
        "Ask about candidates, search for skills, or get recruitment insights...",
        disabled=chat_loading,
    )

    if prompt:
        st.session_state.chat_loading = True
        now = datetime.now().strftime("%I:%M %p")

        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": now,
        })

        # Show user message inline (history loop already passed)
        st.markdown(
            f'<div style="display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:1rem;'
            f'flex-direction:row-reverse;">'
            f'<div style="width:34px;height:34px;border-radius:10px;flex-shrink:0;'
            f'background:linear-gradient(135deg, #3B82F6, #2563EB);'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.85rem;box-shadow:0 2px 6px rgba(59,130,246,0.3);">👤</div>'
            f'<div style="max-width:75%;">'
            f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:4px;justify-content:flex-end;">'
            f'<span style="font-size:0.72rem;font-weight:600;color:#64748B;">You</span>'
            f'<span style="font-size:0.65rem;color:#475569;">{now}</span></div>'
            f'<div style="background:linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(59,130,246,0.04) 100%);'
            f'border:1px solid rgba(59,130,246,0.2);'
            f'border-radius:16px 16px 4px 16px;padding:0.85rem 1.1rem;">'
            f'<div style="color:#CBD5E1;font-size:0.875rem;line-height:1.65;">{prompt}</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

        # Inline typing indicator (no dim overlay, no spinner, no full-page loading)
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">'
            f'<div style="width:34px;height:34px;border-radius:10px;flex-shrink:0;'
            f'background:linear-gradient(135deg, #22C55E, #16A34A);'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.85rem;box-shadow:0 2px 6px rgba(34,197,94,0.3);">🤖</div>'
            f'<div style="color:#94A3B8;font-size:0.875rem;">RecruitX is thinking'
            f'<span class="typing-dots" style="display:inline-flex;gap:2px;margin-left:2px;">'
            f'<span>.</span><span>.</span><span>.</span></span></div></div>',
            unsafe_allow_html=True,
        )

        result = api_post("/api/chat", {
            "message": prompt,
            "session_id": st.session_state.session_id,
        })
        if result:
            response_text = result.get("response", "No response.")
        else:
            response_text = "Sorry, I could not process your request. Please try again."

        now = datetime.now().strftime("%I:%M %p")

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": now,
        })
        st.session_state.chat_loading = False
        st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        st.markdown('<hr style="margin:1rem 0;" />', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 2, 3])
        with c2:
            if st.button("🗑️  Clear Chat", key="clear_chat", use_container_width=True):
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
        section_header(
            "Candidate Database",
            "Browse, add, and manage your candidate pool."
        ),
        unsafe_allow_html=True,
    )

    tab_browse, tab_add, tab_upload = st.tabs(
        ["📋  Browse Candidates", "➕  Add Candidate", "📄  Upload Resume"]
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
        st.markdown(
            empty_state(
                "📭",
                "No Candidates Yet",
                "Your candidate database is empty. Add candidates manually or upload resumes to get started.",
                "Use the 'Add Candidate' or 'Upload Resume' tab to begin."
            ),
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(candidates)

    # ── Search bar ──
    search = st.text_input(
        "🔍  Search candidates",
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
            f'<p style="font-size:0.78rem;color:#64748B;margin:0.25rem 0 0.75rem 0;'
            f'display:flex;align-items:center;gap:4px;">'
            f'<span style="color:#94A3B8;font-weight:600;">{len(filtered_df)}</span>'
            f'of {len(candidates)} candidates match your search</p>',
            unsafe_allow_html=True,
        )
    else:
        filtered_df = df

    # ── Data table ──
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
        '<div style="margin-top:1.5rem;">'
        '<h3 style="margin:0 0 0.75rem;display:flex;align-items:center;gap:0.5rem;">'
        '<span style="font-size:1rem;">👤</span> Candidate Details</h3></div>',
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

    c_name = c.get('name', 'N/A')
    st.markdown(
        f'<div style="background:#111827;border:1px solid #1E293B;border-radius:12px;'
        f'padding:1.25rem;margin-top:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
        f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem;">'
        f'{candidate_avatar(c_name, size=52)}'
        f'<div>'
        f'<h3 style="margin:0;font-size:1.1rem;color:#F1F5F9;">{c_name}</h3>'
        f'<p style="margin:0.15rem 0 0;font-size:0.82rem;color:#64748B;">'
        f'{c.get("email", "N/A")}  ·  {c.get("location", "N/A")}</p>'
        f'</div></div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Name</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("name", "N/A")}</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Email</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("email", "N/A")}</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Phone</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("phone", "N/A")}</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Location</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("location", "N/A")}</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Education</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("education", "N/A")}</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Experience</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("experience_years", 0)} years</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Skills</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("skills", "N/A")}</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Previous Roles</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("previous_roles", "N/A")}</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Profile Completeness</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("profile_completeness", 0)}%</span></div>'
        f'<div><span style="color:#64748B;font-size:0.78rem;">Last Active</span><br>'
        f'<span style="color:#F1F5F9;font-size:0.9rem;font-weight:500;">{c.get("last_active_days", "N/A")} days ago</span></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr style="margin:1rem 0;" />', unsafe_allow_html=True)

    col_del1, col_del2, col_del3 = st.columns([2, 1, 2])
    with col_del2:
        if st.button("🗑️  Delete Candidate", key=f"del_{selected_id}", use_container_width=True):
            del_resp = requests.delete(
                f"{API_BASE_URL}/api/candidates/{selected_id}", timeout=120
            )
            if del_resp.ok:
                st.success(f"Candidate #{selected_id} deleted.")
                st.rerun()
            else:
                st.error("Failed to delete candidate.")


def _render_add_candidate() -> None:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1.25rem;'
        'padding:0.75rem 1rem;background:rgba(59,130,246,0.04);border:1px solid rgba(59,130,246,0.1);'
        'border-radius:10px;">'
        '<span style="font-size:1.1rem;">✍️</span>'
        '<p style="margin:0;color:#94A3B8;font-size:0.85rem;">'
        'Fill in the candidate details below. Fields marked with <span style="color:#F59E0B;">*</span> are required.</p></div>',
        unsafe_allow_html=True,
    )

    with st.form("add_candidate_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", placeholder="e.g. Rahul Sharma")
            email = st.text_input("Email *", placeholder="e.g. rahul@example.com")
            phone = st.text_input("Phone", placeholder="e.g. 9876543210")
            location = st.text_input("Location", placeholder="e.g. Bangalore, India")
        with col2:
            skills = st.text_input("Skills *", placeholder="e.g. Python, Machine Learning, SQL")
            experience = st.number_input(
                "Experience (years)", min_value=0.0, max_value=50.0, step=0.5, value=0.0
            )
            education = st.text_input("Education", placeholder="e.g. B.Tech Computer Science")
            previous_roles = st.text_input(
                "Previous Roles", placeholder="e.g. Data Analyst at TCS; Backend Dev at Infosys"
            )

        col_slider1, col_slider2 = st.columns(2)
        with col_slider1:
            profile_completeness = st.slider("Profile Completeness", 0, 100, 70)
        with col_slider2:
            last_active_days = st.number_input("Last Active (days ago)", min_value=0, value=30)

        submitted = st.form_submit_button(
            "➕  Add Candidate", type="primary", use_container_width=True
        )

    if submitted:
        errors = []
        if not name: errors.append("Name")
        if not email: errors.append("Email")
        if not skills: errors.append("Skills")

        if errors:
            st.markdown(
                alert_card(f"Required fields missing: {', '.join(errors)}.", "error"),
                unsafe_allow_html=True,
            )
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
            st.markdown(
                alert_card(result.get("message", "Candidate created successfully!"), "success"),
                unsafe_allow_html=True,
            )
            st.balloons()


def _render_upload_resume() -> None:
    st.markdown(
        '<div style="text-align:center;margin-bottom:2rem;">'
        '<div style="width:64px;height:64px;border-radius:16px;'
        'background:linear-gradient(135deg, rgba(59,130,246,0.1), rgba(59,130,246,0.03));'
        'display:flex;align-items:center;justify-content:center;'
        'margin:0 auto 0.75rem;border:1px solid rgba(59,130,246,0.1);">'
        '<span style="font-size:1.75rem;">📄</span></div>'
        '<p style="color:#64748B;max-width:440px;margin:0 auto;font-size:0.875rem;line-height:1.6;">'
        'PDF or DOCX supported. AI parses text, detects duplicates, and creates a structured profile.</p></div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Select a resume file",
        type=["pdf", "docx"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        file_size = uploaded_file.size
        file_name = uploaded_file.name
        file_ext = file_name.rsplit(".", 1)[-1].upper() if "." in file_name else "FILE"

        if file_size > 10 * 1024 * 1024:
            st.markdown(alert_card("File size exceeds the 10 MB limit.", "error"), unsafe_allow_html=True)
            return

        st.markdown(
            f'<div style="background:rgba(59,130,246,0.04);border:1px solid rgba(30,41,59,0.5);'
            f'border-radius:10px;padding:0.75rem 1rem;margin:0.75rem 0;'
            f'display:flex;align-items:center;gap:0.75rem;">'
            f'<div style="width:36px;height:36px;border-radius:8px;'
            f'background:rgba(59,130,246,0.1);display:flex;align-items:center;'
            f'justify-content:center;flex-shrink:0;">'
            f'<span style="font-size:0.65rem;font-weight:700;color:#60A5FA;">{file_ext}</span></div>'
            f'<div style="flex:1;min-width:0;">'
            f'<p style="margin:0;font-weight:500;color:#F1F5F9;font-size:0.85rem;'
            f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{file_name}</p>'
            f'<p style="margin:0;font-size:0.75rem;color:#64748B;">{file_size / 1024:.1f} KB</p></div>'
            f'<span style="color:#22C55E;font-size:0.75rem;font-weight:500;padding:3px 10px;'
            f'background:rgba(34,197,94,0.1);border-radius:6px;">✓ Ready</span></div>',
            unsafe_allow_html=True,
        )

        progress_bar = st.progress(0, text="")

        upload_clicked = st.button(
            "Upload Resume",
            key="upload_resume",
            type="primary",
            use_container_width=True,
        )

        if upload_clicked:
            progress_bar.progress(20, text="📤 Uploading file...")
            progress_bar.progress(40, text="📝 Extracting text...")
            progress_bar.progress(60, text="🤖 Parsing with AI...")
            progress_bar.progress(80, text="💾 Saving candidate profile...")

            result = api_post_file(
                "/api/upload-resume",
                uploaded_file.getvalue(),
                uploaded_file.name,
            )

            if result:
                progress_bar.progress(100, text="✅ Complete!")
                candidate = result.get("candidate")
                is_new = result.get("is_new", True)

                if is_new:
                    st.markdown(
                        '<div>'
                        + alert_card(result.get("message", "Resume parsed successfully!"), "success")
                        + '</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div>'
                        + alert_card(result.get("message", "Duplicate resume detected."), "warning")
                        + '</div>',
                        unsafe_allow_html=True,
                    )

                if candidate:
                    c_name = candidate.get('name', 'N/A')
                    st.markdown(
                        f'<div style="background:#1E293B;border:1px solid #334155;'
                        f'border-radius:12px;padding:1.25rem 1.5rem;margin-top:0.75rem;'
                        f'box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
                        f'<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">'
                        f'{candidate_avatar(c_name)}'
                        f'<div>'
                        f'<h4 style="margin:0;font-size:0.95rem;color:#F1F5F9;">Parsed Candidate</h4>'
                        f'<p style="margin:0;font-size:0.78rem;color:#64748B;">'
                        f'Extracted from {file_name}</p></div></div>'
                        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">'
                        f'<div><span style="color:#64748B;font-size:0.78rem;">Name</span><br>'
                        f'<span style="color:#F1F5F9;font-size:0.875rem;font-weight:500;">{candidate.get("name", "N/A")}</span></div>'
                        f'<div><span style="color:#64748B;font-size:0.78rem;">Email</span><br>'
                        f'<span style="color:#F1F5F9;font-size:0.875rem;font-weight:500;">{candidate.get("email", "N/A")}</span></div>'
                        f'<div><span style="color:#64748B;font-size:0.78rem;">Phone</span><br>'
                        f'<span style="color:#F1F5F9;font-size:0.875rem;font-weight:500;">{candidate.get("phone", "N/A")}</span></div>'
                        f'<div><span style="color:#64748B;font-size:0.78rem;">Location</span><br>'
                        f'<span style="color:#F1F5F9;font-size:0.875rem;font-weight:500;">{candidate.get("location", "N/A")}</span></div>'
                        f'<div><span style="color:#64748B;font-size:0.78rem;">Skills</span><br>'
                        f'<span style="color:#F1F5F9;font-size:0.875rem;font-weight:500;">{candidate.get("skills", "N/A")}</span></div>'
                        f'<div><span style="color:#64748B;font-size:0.78rem;">Experience</span><br>'
                        f'<span style="color:#F1F5F9;font-size:0.875rem;font-weight:500;">{candidate.get("experience_years", 0)} years</span></div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                progress_bar.progress(0, text="Upload failed")
                st.markdown(
                    alert_card("Resume upload failed. Please try again.", "error"),
                    unsafe_allow_html=True,
                )


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
        section_header(
            "Analytics",
            "Visual insights into your candidate database and recruitment pipeline."
        ),
        unsafe_allow_html=True,
    )

    result = api_get("/api/candidates")
    if not result:
        return

    candidates = result.get("candidates", [])
    if not candidates:
        st.markdown(
            empty_state(
                "📊",
                "No Analytics Data",
                "Add candidates to your database to see analytics and insights about your talent pipeline.",
                "Upload resumes or add candidates to get started."
            ),
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(candidates)

    # ── KPI Summary Row ──
    kpi_cols = st.columns(4)
    avg_completeness = df["profile_completeness"].mean() if "profile_completeness" in df else 0
    avg_experience = df["experience_years"].mean() if "experience_years" in df else 0
    total_candidates = len(candidates)
    active_recent = len(df[df["last_active_days"] <= 30]) if "last_active_days" in df else 0

    with kpi_cols[0]:
        st.markdown(
            kpi_card("👥", str(total_candidates), "Total Candidates", "#3B82F6"),
            unsafe_allow_html=True,
        )
    with kpi_cols[1]:
        st.markdown(
            kpi_card("📊", f"{avg_completeness:.0f}%", "Avg Completeness", "#8B5CF6"),
            unsafe_allow_html=True,
        )
    with kpi_cols[2]:
        st.markdown(
            kpi_card("💼", f"{avg_experience:.1f}", "Avg Experience (yrs)", "#22C55E"),
            unsafe_allow_html=True,
        )
    with kpi_cols[3]:
        st.markdown(
            kpi_card("🟢", str(active_recent), "Active (30d)", "#F59E0B"),
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

    # 1. Score distribution — profile completeness histogram
    st.markdown(
        '<h2 style="margin-top:0.5rem;margin-bottom:0.75rem;">Profile Completeness Distribution</h2>',
        unsafe_allow_html=True,
    )
    fig1 = px.histogram(
        df,
        x="profile_completeness",
        nbins=10,
        title="",
        labels={"profile_completeness": "Completeness (%)"},
        color_discrete_sequence=["#3B82F6"],
    )
    fig1 = apply_dark_theme(fig1)
    fig1.update_layout(showlegend=False, margin={"t": 16, "b": 48, "l": 48, "r": 24})
    fig1.update_traces(
        marker_line={"width": 0},
        hovertemplate="<b>%{x}%</b><br>Count: %{y}<extra></extra>",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Top skills in demand
    st.markdown(
        '<h2 style="margin-top:1.5rem;margin-bottom:0.75rem;">Top Skills in Demand</h2>',
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
            title="",
            color="Count",
            color_continuous_scale=["#1E293B", "#3B82F6", "#7C3AED"],
        )
        fig2 = apply_dark_theme(fig2)
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, margin={"t": 12, "b": 40, "l": 40, "r": 16})
        fig2.update_traces(
            marker_line={"width": 0},
            hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown(
            empty_state("🏷️", "No Skills Data", "Skills data will appear here once candidates are added."),
            unsafe_allow_html=True,
        )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(
            '<h2 style="margin-top:1.5rem;margin-bottom:0.75rem;">Experience Distribution</h2>',
            unsafe_allow_html=True,
        )
        fig3 = px.box(
            df,
            y="experience_years",
            title="",
            labels={"experience_years": "Experience (years)"},
            color_discrete_sequence=["#3B82F6"],
        )
        fig3 = apply_dark_theme(fig3)
        fig3.update_layout(margin={"t": 16, "b": 48, "l": 48, "r": 24})
        st.plotly_chart(fig3, use_container_width=True)

    with chart_col2:
        st.markdown(
            '<h2 style="margin-top:1.5rem;margin-bottom:0.75rem;">Experience vs Completeness</h2>',
            unsafe_allow_html=True,
        )
        fig4 = px.scatter(
            df,
            x="experience_years",
            y="profile_completeness",
            hover_data=["name", "location"],
            title="",
            labels={
                "experience_years": "Experience (years)",
                "profile_completeness": "Completeness (%)",
            },
            color="last_active_days",
            color_continuous_scale=["#7C3AED", "#3B82F6", "#1E293B"],
        )
        fig4 = apply_dark_theme(fig4)
        fig4.update_layout(margin={"t": 16, "b": 48, "l": 48, "r": 24})
        fig4.update_traces(
            marker={"size": 10, "line": {"width": 1, "color": "rgba(255,255,255,0.15)"}},
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown(
        '<h2 style="margin-top:1.5rem;margin-bottom:0.75rem;">Candidates by Location</h2>',
        unsafe_allow_html=True,
    )
    location_counts = df["location"].value_counts().reset_index()
    location_counts.columns = ["Location", "Count"]
    fig5 = px.pie(
        location_counts,
        names="Location",
        values="Count",
        title="",
        color_discrete_sequence=["#3B82F6", "#60A5FA", "#7C3AED", "#A78BFA",
                                  "#93C5FD", "#8B5CF6", "#C4B5FD",
                                  "#6366F1", "#818CF8", "#A5B4FC"],
    )
    fig5 = apply_dark_theme(fig5)
    fig5.update_layout(margin={"t": 16, "b": 48, "l": 48, "r": 24})
    fig5.update_traces(
        textfont={"color": "white", "size": 12},
        hovertemplate="<b>%{label}</b><br>%{value} candidates (%{percent})<extra></extra>",
        marker={"line": {"width": 2, "color": "#1E293B"}},
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown(
        '<h2 style="margin-top:1.5rem;margin-bottom:0.75rem;">Candidate Activity</h2>',
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
        title="",
        color="Count",
        color_continuous_scale=["#1E293B", "#3B82F6", "#7C3AED"],
    )
    fig6 = apply_dark_theme(fig6)
    fig6.update_layout(
        xaxis={"categoryorder": "array", "categoryarray": labels},
        showlegend=False,
        margin={"t": 12, "b": 40, "l": 40, "r": 16},
    )
    fig6.update_traces(
        marker_line={"width": 0},
        hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
    )
    st.plotly_chart(fig6, use_container_width=True)


# ============================================================
# Main App — Tab Navigation
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🔍  Search Candidates",
        "💬  Chat with RecruitX",
        "🗄️  Candidate Database",
        "📊  Analytics",
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
