"""
frontend/dashboard.py — RecruitX Streamlit Dashboard

This is the main recruiter interface for RecruitX. It provides four tabs:
    1. Find Candidates — Run the recruitment pipeline
    2. Chat with RecruitX — Natural language queries (placeholder until Phase 14)
    3. Candidate Database — Browse, add, and upload candidates
    4. Analytics — Visualize recruitment data

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
import requests
import streamlit as st

# ============================================================
# Configuration
# ============================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "RecruitX")

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

st.title(f"🔄 {APP_NAME}")
st.caption("Autonomous Multi-Agent AI Recruitment System")

# Sidebar — API health check
health = api_get("/api/health")
if health:
    st.sidebar.success(
        f"API Connected — {health.get('app', 'RecruitX')} v{health.get('version', '?')}"
    )
else:
    st.sidebar.error("API Not Connected")

# ============================================================
# Session State Initialisation
# ============================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "recruit_results" not in st.session_state:
    st.session_state.recruit_results = None

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
    st.header("🔍 Find Candidates")
    st.markdown(
        "Paste a job description below to find the best matching candidates "
        "from the database."
    )

    jd_text = st.text_area(
        "Job Description",
        height=200,
        placeholder="Paste the job description here...",
        help="Enter the full job description including required skills, experience, and responsibilities.",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        top_k = st.number_input(
            "Top K candidates",
            min_value=1,
            max_value=50,
            value=10,
            help="Number of top candidates to return.",
        )
    with col2:
        st.write("")
        st.write("")
        run_clicked = st.button(
            "🚀 Find Best Candidates",
            type="primary",
            use_container_width=True,
            disabled=not jd_text.strip(),
        )

    if run_clicked and jd_text.strip():
        with st.spinner("🤖 AI agents are processing your request..."):
            # Progress bar with stage labels to show pipeline progress
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
    and one expandable card per candidate.

    Args:
        result: The response from POST /api/recruit.
    """
    shortlist = result.get("shortlist", [])
    jd_analysis = result.get("jd_analysis", {})
    processing_time = result.get("processing_time_ms", 0)

    if not shortlist:
        st.warning("No matching candidates found.")
        return

    # Fetch database size from the backend for the stats row
    candidate_count = _fetch_candidate_count()

    # Stats row
    top_score = shortlist[0]["final_score"]
    stats_cols = st.columns(4)
    stats_cols[0].metric("Candidates Found", len(shortlist))
    stats_cols[1].metric("Database Size", candidate_count)
    stats_cols[2].metric("Top Score", f"{top_score:.1f}/100")
    stats_cols[3].metric("Processing Time", f"{processing_time:.0f} ms")

    # Bar chart — top candidate scores
    _display_score_chart(shortlist)

    # Export to CSV button
    _display_export_button(shortlist)

    # Ranked candidate cards
    st.subheader("Ranked Candidates")
    for entry in shortlist:
        with st.expander(
            f"#{entry['rank']} — Candidate #{entry['candidate_id']} "
            f"(Score: {entry['final_score']:.1f}/100)"
        ):
            _display_candidate_card(entry)


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
        color_continuous_scale="Viridis",
        text_auto=".1f",
    )
    fig.update_layout(showlegend=False)
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
        "📥 Export to CSV",
        data=csv_buffer.getvalue(),
        file_name="recruitx_shortlist.csv",
        mime="text/csv",
    )


def _display_candidate_card(entry: Dict[str, Any]) -> None:
    """
    Render a single expandable candidate card with scores, explanation,
    skill gap tags, and action buttons.

    Args:
        entry: A single candidate entry from the shortlist.
    """
    # Score breakdown row
    score_cols = st.columns(5)
    score_cols[0].metric("Final Score", f"{entry['final_score']:.1f}")
    score_cols[1].metric("Semantic", f"{entry['semantic_score']:.1f}")
    score_cols[2].metric("Skill", f"{entry['skill_score']:.1f}")
    score_cols[3].metric("Signal", f"{entry['signal_score']:.1f}")
    score_cols[4].metric("Recency", f"{entry.get('recency_score', 0):.1f}")

    # Explanation text
    st.markdown(f"**Explanation:** {entry.get('explanation', 'N/A')}")

    # Skill gap tags — uses ✅/❌/⭐ emojis as specified in Feature 3
    skill_gap = entry.get("skill_gap", {})
    matched = skill_gap.get("matched", [])
    missing = skill_gap.get("missing", [])
    bonus = skill_gap.get("bonus", [])

    if matched or missing or bonus:
        st.markdown("**Skill Gap Analysis:**")
        tag_cols = st.columns(3)
        with tag_cols[0]:
            st.markdown("**✅ Matched**")
            for skill in matched:
                st.markdown(f"- {skill}")
        with tag_cols[1]:
            st.markdown("**❌ Missing**")
            for skill in missing:
                st.markdown(f"- {skill}")
        with tag_cols[2]:
            st.markdown("**⭐ Bonus**")
            for skill in bonus:
                st.markdown(f"- {skill}")

    # Action buttons row
    action_cols = st.columns(2)
    with action_cols[0]:
        # Interview questions — stub until Phase 15
        if st.button(
            "🎯 Generate Interview Questions",
            key=f"iq_{entry['candidate_id']}_{entry['rank']}",
        ):
            st.info(
                "Interview question generation will be available in Phase 15. "
                "It will generate tailored technical and behavioural questions "
                "based on the candidate's skill gaps and the job requirements."
            )

    with action_cols[1]:
        # Recruiter feedback — disabled until the backend provides shortlist_id
        st.button(
            "👍 / 👎 Submit Feedback",
            disabled=True,
            key=f"fb_{entry['candidate_id']}_{entry['rank']}",
            help=(
                "Feedback requires the shortlist ID from the backend. "
                "This feature will be enabled in a future update."
            ),
        )


# ============================================================
# Tab 2: Chat with RecruitX
# ============================================================


def render_chat_tab() -> None:
    """
    Render the Chat with RecruitX tab.

    Provides a chat interface for natural language queries.
    The backend returns placeholder responses until Phase 14.
    """
    st.header("💬 Chat with RecruitX")
    st.markdown(
        "Ask natural language questions about your candidates. "
        "Full conversational AI will be available in Phase 14."
    )

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    prompt = st.chat_input("Ask about candidates...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
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
        if st.button("🗑️ Clear Chat"):
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
        - Upload Resume (file upload, parsing in Phase 13)
    """
    st.header("👥 Candidate Database")

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
    st.subheader("All Candidates")

    result = api_get("/api/candidates")
    if not result:
        return

    candidates = result.get("candidates", [])
    if not candidates:
        st.info("No candidates found. Add candidates or upload resumes.")
        return

    df = pd.DataFrame(candidates)

    # Search/filter across name, skills, and location
    search = st.text_input("🔍 Search by name, skill, or location", "")
    if search:
        mask = df.apply(
            lambda row: search.lower()
            in str(row.get("name", "")).lower()
            or search.lower() in str(row.get("skills", "")).lower()
            or search.lower() in str(row.get("location", "")).lower(),
            axis=1,
        )
        df = df[mask]
        st.caption(f"Showing {len(df)} of {len(candidates)} candidates")

    # Data table
    st.dataframe(
        df[
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
    selected_id = st.selectbox(
        "View candidate details:",
        [c["id"] for c in candidates],
        format_func=lambda x: f"Candidate #{x}",
    )
    if not selected_id:
        return

    detail = api_get(f"/api/candidates/{selected_id}")
    if not detail or not detail.get("candidate"):
        return

    c = detail["candidate"]
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

        if st.button("🗑️ Delete Candidate", key=f"del_{selected_id}"):
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
    st.subheader("Add New Candidate")

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

        profile_completeness = st.slider("Profile Completeness", 0, 100, 70)
        last_active_days = st.number_input("Last Active (days ago)", min_value=0, value=30)

        submitted = st.form_submit_button(
            "💾 Add Candidate", type="primary", use_container_width=True
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

    Uploaded resume is automatically parsed by the AI Resume Parser (Phase 13):
    extracts text, detects duplicates via MD5 hash, parses with LLM into
    a structured candidate profile, saves to database, and adds to FAISS index.
    """
    st.subheader("Upload Resume")
    st.markdown(
        "Upload a PDF or DOCX resume file. The AI Resume Parser will "
        "automatically extract text, detect duplicates, and create a "
        "structured candidate profile in the database."
    )

    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=["pdf", "docx"],
        help="Max file size: 10 MB",
    )

    if uploaded_file is not None:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File size exceeds the 10 MB limit.")
            return

        if st.button("📤 Upload and Parse Resume", type="primary"):
            with st.spinner("🤖 AI is parsing the resume..."):
                result = api_post_file(
                    "/api/upload-resume",
                    uploaded_file.getvalue(),
                    uploaded_file.name,
                )
            if result:
                candidate = result.get("candidate")
                is_new = result.get("is_new", True)

                if is_new:
                    st.success(result.get("message", "Resume parsed successfully!"))
                else:
                    st.info(result.get("message", "Duplicate resume detected."))

                if candidate:
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
    st.header("📊 Analytics")

    result = api_get("/api/candidates")
    if not result:
        return

    candidates = result.get("candidates", [])
    if not candidates:
        st.info("No candidate data available for analytics.")
        return

    df = pd.DataFrame(candidates)

    # 1. Score distribution — profile completeness histogram
    st.subheader("Candidate Profile Completeness Distribution")
    fig1 = px.histogram(
        df,
        x="profile_completeness",
        nbins=10,
        title="Profile Completeness Distribution",
        labels={"profile_completeness": "Completeness (%)"},
        color_discrete_sequence=["#4C78A8"],
    )
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Top skills in demand
    st.subheader("Top Skills in Demand")
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
        fig2.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No skills data available.")

    # 3. Experience distribution
    st.subheader("Experience Distribution")
    fig3 = px.box(
        df,
        y="experience_years",
        title="Years of Experience Distribution",
        labels={"experience_years": "Experience (years)"},
        color_discrete_sequence=["#4C78A8"],
    )
    st.plotly_chart(fig3, use_container_width=True)

    # 4. Experience vs profile completeness
    st.subheader("Experience vs Profile Completeness")
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
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig4, use_container_width=True)

    # 5. Candidates by location
    st.subheader("Candidates by Location")
    location_counts = df["location"].value_counts().reset_index()
    location_counts.columns = ["Location", "Count"]
    fig5 = px.pie(
        location_counts,
        names="Location",
        values="Count",
        title="Candidates by Location",
    )
    st.plotly_chart(fig5, use_container_width=True)

    # 6. Activity heatmap — last active day buckets
    st.subheader("Candidate Activity")
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

    fig6 = px.bar(
        activity_counts,
        x="Activity",
        y="Count",
        title="Candidates by Last Activity",
        color="Count",
        color_continuous_scale="RdYlGn_r",
    )
    st.plotly_chart(fig6, use_container_width=True)


# ============================================================
# Main App — Tab Navigation
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🔍 Find Candidates",
        "💬 Chat with RecruitX",
        "👥 Candidate Database",
        "📊 Analytics",
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
