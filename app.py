import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import database as db
import joblib

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Market Trend Analysis System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (dark premium theme) ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #0a0e1a; color: #e2e8f0; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1629 0%, #1a1f3a 100%);
    border-right: 1px solid #1e2d4a;
}
section[data-testid="stSidebar"] * { color: #c8d6e5 !important; }

.metric-card {
    background: linear-gradient(135deg, #1a2540 0%, #0f1629 100%);
    border: 1px solid #2a3a5c;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}
.metric-card:hover { transform: translateY(-3px); border-color: #00d4ff; }
.metric-value { font-size: 2rem; font-weight: 700; color: #00d4ff; }
.metric-label { font-size: 0.85rem; color: #94a3b8; margin-top: 4px; }

.page-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f1629 100%);
    border-left: 4px solid #00d4ff;
    border-radius: 0 12px 12px 0;
    padding: 16px 24px;
    margin-bottom: 24px;
}
.page-header h1 { font-size: 1.6rem; font-weight: 700; color: #fff; margin: 0; }
.page-header p  { font-size: 0.9rem; color: #94a3b8; margin: 4px 0 0 0; }

.job-card {
    background: linear-gradient(135deg, #1a2540 0%, #111827 100%);
    border: 1px solid #2a3a5c;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.job-card:hover { border-color: #7c3aed; }
.job-card h4 { color: #00d4ff; margin: 0 0 6px 0; font-size: 1rem; }
.job-card .meta { color: #94a3b8; font-size: 0.82rem; }
.job-card .score-bar { background:#1e2d4a; border-radius:6px; height:8px; margin-top:8px; }
.job-card .score-fill { background: linear-gradient(90deg,#7c3aed,#00d4ff); border-radius:6px; height:8px; }

.sidebar-brand {
    background: linear-gradient(135deg, #00d4ff22, #7c3aed22);
    border: 1px solid #00d4ff44;
    border-radius: 12px;
    padding: 14px 16px;
    text-align: center;
    margin-bottom: 20px;
}
.sidebar-brand h2 { font-size: 1rem; font-weight: 700; color: #00d4ff !important; margin: 0; }
.sidebar-brand p  { font-size: 0.7rem; color: #94a3b8 !important; margin: 4px 0 0 0; }

div[data-testid="stMetric"] label { color: #94a3b8 !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 1.8rem !important; }

/* Custom Sidebar Navigation Button Styles */
div[data-testid="stSidebar"] button {
    display: flex;
    justify-content: flex-start !important;
    align-items: center;
    border-radius: 10px !important;
    padding: 10px 16px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    transition: all 0.2s ease-in-out !important;
    margin-bottom: 6px !important;
    border: 1px solid transparent !important;
}

/* Inactive button tab style */
div[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #1e2d4a !important;
}
div[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: #1e2d4a !important;
    color: #00d4ff !important;
    border-color: #00d4ff55 !important;
    transform: translateX(4px);
}

/* Active button tab style */
div[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(90deg, #7c3aed 0%, #00d4ff 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px 0 rgba(0, 212, 255, 0.3) !important;
    border: none !important;
}
div[data-testid="stSidebar"] button[kind="primary"]:hover {
    transform: scale(1.02);
}

/* Style widget labels to be crisp white in dark theme */
label, 
div[data-testid="stWidgetLabel"] p, 
div[data-testid="stWidgetLabel"] label,
label[data-testid="stWidgetLabel"],
div[data-testid="stExpander"] p,
span[data-testid="stHeader"] {
    color: #ffffff !important;
}

/* Specific class overrides for streamlit selectbox, text input, slider and multi-select labels */
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextInput"] label {
    color: #ffffff !important;
}

.stDataFrame { background: #111827 !important; border-radius: 8px !important; }

/* Custom Insights Style */
.insight-box {
    background: linear-gradient(135deg, #111827 0%, #1e293b 100%);
    border: 1px solid #2a3a5c;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
}
.insight-box h3 { margin-top: 0; color: #00d4ff; font-size: 1.25rem; font-weight: 600; }
.insight-box ul { margin: 0; padding-left: 20px; color: #e2e8f0; line-height: 1.6; }
.insight-box li { margin-bottom: 8px; }
.insight-box li b { color: #00d4ff; }
</style>
""", unsafe_allow_html=True)

# ── Colour palette for charts ─────────────────────────────────────────────────
COLORS = ["#00d4ff","#7c3aed","#06b6d4","#8b5cf6","#0ea5e9","#6366f1","#22d3ee","#a78bfa"]
CHART_LAYOUT = dict(
    paper_bgcolor="#111827",
    plot_bgcolor="#111827",
    font=dict(family="Inter", color="#e2e8f0"),
    title_font=dict(size=16, color="#fff"),
    legend=dict(bgcolor="#1a2540", bordercolor="#2a3a5c"),
    margin=dict(l=40, r=20, t=50, b=40),
    coloraxis_colorbar=dict(tickfont=dict(color="#e2e8f0")),
    xaxis=dict(gridcolor="#1e2d4a", linecolor="#2a3a5c", tickfont=dict(color="#94a3b8")),
    yaxis=dict(gridcolor="#1e2d4a", linecolor="#2a3a5c", tickfont=dict(color="#94a3b8")),
)

def style_fig(fig, height=450):
    fig.update_layout(**CHART_LAYOUT, height=height)
    return fig

# ── Check for Database existence ──────────────────────────────────────────────
total_db_jobs = db.get_total_row_count()
if total_db_jobs == 0:
    st.error("⚠️ Database is empty or does not exist at `data/job_market.db`. Please run `python preprocess.py` first.")
    st.stop()

# ── Session State for Navigation & AI Recommendations ─────────────────────────
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "🏠 Dashboard"
if "rec_results" not in st.session_state:
    st.session_state["rec_results"] = None
if "rec_query_skills" not in st.session_state:
    st.session_state["rec_query_skills"] = []

# ── Sidebar Navigation & Global Filters ────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <h2>📊 Job Market</h2>
      <p>Trend Analysis System</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("<p style='font-size:0.75rem;color:#94a3b8;margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:1px;'>Navigation</p>", unsafe_allow_html=True)
    
    pages = [
        "🏠 Dashboard",
        "📈 Skill Trends",
        "🌍 Location Analysis",
        "🤖 Job Recommendation",
        "🔍 Job Search"
    ]
    
    for p in pages:
        is_active = st.session_state["active_page"] == p
        if st.button(
            p,
            key=f"nav_btn_{p}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state["active_page"] = p
            st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem;color:#94a3b8;margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:1px;'>Global Filters</p>", unsafe_allow_html=True)

    # Fetch unique categories dynamically from DB
    db_countries, db_types, db_levels = db.get_unique_filter_options()

    # 1. Country Filter
    selected_country = st.selectbox("Country", ["All"] + [c.title() for c in db_countries])
    
    # 2. City Filter (Dependent on Country selection)
    db_cities = db.get_cities_for_country(selected_country)
    selected_city = st.selectbox("City", ["All"] + [c.title() for c in db_cities])
    
    # 3. Job Type Filter
    selected_type = st.selectbox("Job Type", ["All"] + [t.title() for t in db_types])
    
    # 4. Job Level Filter
    selected_level = st.selectbox("Job Level", ["All"] + [l.title() for l in db_levels])
    
    # 5. Skill Keyword Filter
    skill_kw = st.text_input("Skill keyword", "")
    
    # 6. Job Title Keyword Filter
    title_kw = st.text_input("Job Title keyword", "")

    st.markdown("---")
    st.markdown(f"<span style='color:#94a3b8;font-size:0.78rem;'>📁 {total_db_jobs:,} jobs loaded in database</span>", unsafe_allow_html=True)

# Apply global filters dynamically
filters = {
    "country": selected_country,
    "city": selected_city,
    "job_type": selected_type,
    "job_level": selected_level,
    "skill_kw": skill_kw,
    "title_kw": title_kw
}

page = st.session_state["active_page"]

# ── Helper HTML Components ────────────────────────────────────────────────────
def header(title, subtitle=""):
    st.markdown(f"""
    <div class="page-header">
      <h1>{title}</h1>
      {'<p>'+subtitle+'</p>' if subtitle else ''}
    </div>""", unsafe_allow_html=True)

def kpi(col, label, value):
    col.markdown(f"""
    <div class="metric-card">
      <div class="metric-value">{value}</div>
      <div class="metric-label">{label}</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    header("🏠 Dashboard Overview", "Real-time snapshot of the job market landscape")

    kpis = db.get_kpis(filters)

    if kpis["total_jobs"] == 0:
        st.warning("⚠️ No data available matching the selected filters. Please adjust the sidebar filters.")
    else:
        # KPI Layout (5 Columns)
        c1, c2, c3, c4, c5 = st.columns(5)
        kpi(c1, "Total Jobs", f"{kpis['total_jobs']:,}")
        kpi(c2, "Total Companies", f"{kpis['total_companies']:,}")
        kpi(c3, "Total Locations", f"{kpis['total_locations']:,}")
        kpi(c4, "Unique Job Titles", f"{kpis['unique_titles']:,}")
        kpi(c5, "Total Unique Skills", f"{kpis['total_skills']:,}")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Insights Summary Section
        st.subheader("💡 Key Market Insights")
        insights = db.get_market_insights(filters)
        
        st.markdown(f"""
        <div class="insight-box">
            <ul>
                <li>🏆 <b>Most Demanded Job Title:</b> {insights['top_title']}</li>
                <li>🛠️ <b>Most Demanded Skill:</b> {insights['top_skill']}</li>
                <li>🌍 <b>Highest Job Demand Location:</b> {insights['top_location']}</li>
                <li>🕐 <b>Most Common Job Type:</b> {insights['top_type']}</li>
                <li>🎓 <b>Most Common Job Level:</b> {insights['top_level']}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # ── Job Posting Trend (Line / Area Chart) ────────────────────────────────
        st.subheader("📅 Job Posting Trend")
        c_a, c_b = st.columns([1, 4])
        with c_a:
            granularity = st.radio("Granularity", ["Daily","Monthly"], horizontal=True, key="dashboard_trend_gran")
        with c_b:
            st.markdown("")
        
        trend = db.get_job_posting_trend(filters, granularity)
        
        if not trend.empty:
            fig_trend = go.Figure(go.Scatter(
                x=trend["period"], y=trend["count"],
                mode="lines+markers",
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.08)",
                line=dict(color="#00d4ff", width=2),
                marker=dict(color="#00d4ff", size=5),
                hovertemplate="<b>%{x}</b><br>Jobs: %{y:,}<extra></extra>",
            ))
            style_fig(fig_trend, 380)
            fig_trend.update_layout(
                title=f"{granularity} Job Postings Volume over Time",
                xaxis=dict(title="Date / Period", tickangle=-45, gridcolor="#1e2d4a"),
                yaxis=dict(title="Number of Postings", gridcolor="#1e2d4a"),
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            st.markdown("<p style='font-size:0.78rem;color:#94a3b8;font-style:italic;margin-top:-10px;'>“The trend is based on available first_seen dates in the database.”</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No posting date information available to show trends.")

        # ── Row 1 Visualizations: Job Titles & Companies ──────────────────────────
        r1_l, r1_r = st.columns(2)
        with r1_l:
            st.subheader("🏆 Top 10 Job Titles")
            top_titles = db.get_top_job_titles(filters, 10)
            if not top_titles.empty:
                fig_titles = px.bar(
                    top_titles.sort_values("count"),
                    x="count", y="job_title", orientation="h",
                    color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                    labels={"count":"# Jobs","job_title":""},
                    title="Top Job Titles by Count"
                )
                fig_titles.update_traces(texttemplate="%{x:,}", textposition="outside")
                style_fig(fig_titles, 420)
                fig_titles.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_titles, use_container_width=True)
            else:
                st.info("No job titles available.")

        with r1_r:
            st.subheader("🏢 Top Hiring Companies")
            comp = db.get_top_hiring_companies(filters, 15)
            if not comp.empty:
                view_comp = st.radio("Display as:", ["Treemap", "Bar Chart"], horizontal=True, key="dashboard_comp_view")
                if view_comp == "Treemap":
                    fig_comp = px.treemap(
                        comp, path=["company"], values="count",
                        color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                        title="Treemap representation of Hiring Companies"
                    )
                    fig_comp.update_traces(textfont=dict(size=12, color="#fff"))
                else:
                    fig_comp = px.bar(
                        comp.sort_values("count"), x="count", y="company", orientation="h",
                        color="count", color_continuous_scale=["#1e3a5f","#7c3aed"],
                        labels={"count":"# Jobs","company":""},
                        title="Hiring Company Volumes"
                    )
                    fig_comp.update_traces(texttemplate="%{x:,}", textposition="outside")
                    fig_comp.update_layout(coloraxis_showscale=False)
                style_fig(fig_comp, 420)
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("No hiring company details available.")

        # ── Row 2 Visualizations: Job Type & Level ────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        r2_l, r2_r = st.columns(2)
        with r2_l:
            st.subheader("🍩 Job Type Distribution")
            jt = db.get_job_type_distribution(filters, 8)
            if not jt.empty:
                fig_type = go.Figure(go.Pie(
                    labels=jt["type"], values=jt["count"],
                    hole=0.55,
                    marker=dict(colors=COLORS, line=dict(color="#0a0e1a", width=2)),
                    hovertemplate="<b>%{label}</b><br>Jobs: %{value:,}<br>Percentage: %{percent}<extra></extra>"
                ))
                fig_type.update_traces(textfont_color="#fff")
                style_fig(fig_type, 400)
                fig_type.update_layout(title="Job Types Breakdown")
                st.plotly_chart(fig_type, use_container_width=True)
            else:
                st.info("No job type information available.")

        with r2_r:
            st.subheader("🎯 Job Level Distribution")
            jl = db.get_job_level_distribution(filters, 10)
            if not jl.empty:
                fig_level = px.bar(
                    jl, x="level", y="count",
                    color="count", color_continuous_scale=["#1e3a5f","#7c3aed"],
                    labels={"level":"","count":"# Jobs"},
                    title="Job Count by Experience Level"
                )
                fig_level.update_traces(texttemplate="%{y:,}", textposition="outside")
                style_fig(fig_level, 400)
                fig_level.update_layout(coloraxis_showscale=False, xaxis_tickangle=-15)
                st.plotly_chart(fig_level, use_container_width=True)
            else:
                st.info("No job level information available.")

        # ── Row 3 Visualizations: Role vs Type & Level vs Type ────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        r3_l, r3_r = st.columns(2)
        with r3_l:
            st.subheader("👔 Job Role vs Job Type")
            role_type_gp = db.get_role_vs_type(filters, 10)
            if not role_type_gp.empty:
                fig_role_type = px.bar(
                    role_type_gp, y="job_title", x="count", color="job_type",
                    orientation="h", barmode="stack",
                    color_discrete_sequence=COLORS,
                    labels={"job_title": "", "count": "# Jobs", "job_type": "Job Type"},
                    title="Employment Type breakdown for Top 10 Roles"
                )
                style_fig(fig_role_type, 420)
                st.plotly_chart(fig_role_type, use_container_width=True)
            else:
                st.info("No role vs type details available.")

        with r3_r:
            st.subheader("🎓 Job Level vs Job Type")
            level_type_gp = db.get_level_vs_type(filters)
            if not level_type_gp.empty:
                fig_level_type = px.bar(
                    level_type_gp, x="job_level", y="count", color="job_type",
                    barmode="group",
                    color_discrete_sequence=COLORS,
                    labels={"job_level": "", "count": "# Jobs", "job_type": "Job Type"},
                    title="Job level mapped against employment types"
                )
                style_fig(fig_level_type, 420)
                st.plotly_chart(fig_level_type, use_container_width=True)
            else:
                st.info("No level vs type details available.")

        # ── Row 4 Visualizations (Custom Additions) ──────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        r4_l, r4_r = st.columns(2)
        with r4_l:
            st.subheader("👔 Job Role vs Experience Level")
            role_level_gp = db.get_role_vs_level(filters, 10)
            if not role_level_gp.empty:
                fig_role_level = px.bar(
                    role_level_gp, y="job_title", x="count", color="job_level",
                    orientation="h", barmode="stack",
                    color_discrete_sequence=COLORS,
                    labels={"job_title": "", "count": "# Jobs", "job_level": "Experience Level"},
                    title="Experience levels required for Top 10 Roles (Custom Insight)"
                )
                style_fig(fig_role_level, 420)
                st.plotly_chart(fig_role_level, use_container_width=True)
            else:
                st.info("No role vs level details available.")

        with r4_r:
            st.subheader("📊 Distribution of Skills Count per Job")
            skills_count = db.get_skills_count_distribution(filters)
            if not skills_count.empty:
                fig_skills_dist = px.bar(
                    skills_count, x="skill_count", y="job_count",
                    color_discrete_sequence=[COLORS[0]],
                    labels={"skill_count": "Number of Skills Required", "job_count": "Job Listings"},
                    title="How many skills are typically required per Job Posting? (Custom Insight)"
                )
                style_fig(fig_skills_dist, 420)
                fig_skills_dist.update_layout(
                    xaxis_title="Number of Skills Required",
                    yaxis_title="Number of Job Postings",
                    showlegend=False
                )
                st.plotly_chart(fig_skills_dist, use_container_width=True)
            else:
                st.info("No skill count data available.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SKILL TRENDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Skill Trends":
    header("📈 Skill Trends", "Discover the most in-demand skills in today's job market")

    kpis = db.get_kpis(filters)

    if kpis["total_jobs"] == 0:
        st.warning("⚠️ No data available matching the selected filters. Please adjust the sidebar filters.")
    else:
        # Get top skills for active subset
        skills_df = db.get_top_skills_filtered(filters, 100)

        if skills_df.empty:
            st.error("No skill data available matching these filters.")
        else:
            st.subheader("Top 20 In-Demand Skills")
            top20 = skills_df.head(20).sort_values("count")
            fig_top_skills = px.bar(
                top20, x="count", y="skill_name", orientation="h",
                color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                labels={"count":"# Jobs","skill_name":""},
                title="Top 20 Skills required in filtered listings"
            )
            fig_top_skills.update_traces(texttemplate="%{x:,}", textposition="outside")
            style_fig(fig_top_skills, 500)
            fig_top_skills.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_top_skills, use_container_width=True)

            # Skill vs Job Role Heatmap
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🔥 Skill vs Job Role Heatmap")
            heatmap_df = db.get_skill_role_heatmap(filters)
            if heatmap_df is not None and not heatmap_df.empty:
                fig_heat = go.Figure(data=go.Heatmap(
                    z=heatmap_df.values,
                    x=heatmap_df.columns,
                    y=heatmap_df.index,
                    colorscale=[[0.0, "#0f1629"], [0.5, "#7c3aed"], [1.0, "#00d4ff"]],
                    hovertemplate="Role: %{y}<br>Skill: %{x}<br>Percentage of postings: %{z}%<extra></extra>"
                ))
                style_fig(fig_heat, 480)
                fig_heat.update_layout(
                    title="Skill Requirement Probability by Top Job Titles (%)",
                    xaxis=dict(title="Skills Required", tickangle=-45),
                    yaxis=dict(title="Job Title / Role"),
                )
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Insufficient data to build a Skill vs Job Role heatmap.")

            # Top Skills by Selected Job Role
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🎯 Top Skills by Selected Job Role")
            
            top_roles_df = db.get_top_job_titles(filters, 30)
            available_roles = top_roles_df["job_title"].tolist() if not top_roles_df.empty else []
            
            if available_roles:
                selected_role = st.selectbox("Select a Job Role / Title", options=[r.title() for r in available_roles])
                
                role_filters = filters.copy()
                role_filters["exact_title"] = selected_role.lower()
                role_skills = db.get_top_skills_filtered(role_filters, 10)
                
                if not role_skills.empty:
                    fig_role_skills = px.bar(
                        role_skills.sort_values("count"), x="count", y="skill_name", orientation="h",
                        color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                        labels={"count":"# Jobs","skill_name":""},
                        title=f"Top 10 skills required for {selected_role.title()}"
                    )
                    fig_role_skills.update_traces(texttemplate="%{x:,}", textposition="outside")
                    style_fig(fig_role_skills, 400)
                    fig_role_skills.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_role_skills, use_container_width=True)
                else:
                    st.info(f"No skill metrics available for the job role: '{selected_role}'")
            else:
                st.info("No job titles available to analyze.")

            # Search skills table
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📋 Search all skills in selection")
            search_sk = st.text_input("🔍 Search a skill name", "")
            filtered_sk_table = skills_df[skills_df["skill"].str.contains(search_sk.lower(), case=False, na=False)] if search_sk else skills_df
            
            st.dataframe(
                filtered_sk_table[["skill_name", "count"]].reset_index(drop=True),
                use_container_width=True,
                height=300,
                column_config={"skill_name": "Skill Name", "count": "Job Postings Count"}
            )

            # Download CSV
            csv_sk = filtered_sk_table[["skill", "count"]].to_csv(index=False).encode()
            st.download_button("⬇ Download Skills CSV", csv_sk, "skills.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LOCATION ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 Location Analysis":
    header("🌍 Location Analysis", "Geographic distribution of job opportunities")

    kpis = db.get_kpis(filters)

    if kpis["total_jobs"] == 0:
        st.warning("⚠️ No data available matching the selected filters. Please adjust the sidebar filters.")
    else:
        # World Choropleth Map
        st.subheader("🗺️ Country-wise Job Demand Map")
        country_df = db.get_location_demand_map(filters)
        
        if not country_df.empty:
            fig_map = px.choropleth(
                country_df, locations="country_name",
                locationmode="country names",
                color="count",
                color_continuous_scale=["#0f1629","#00d4ff"],
                labels={"count":"# Jobs", "country_name": "Country"},
                title="Global Job Postings volume by country"
            )
            style_fig(fig_map, 460)
            fig_map.update_geos(
                bgcolor="#0a0e1a",
                lakecolor="#0a0e1a",
                landcolor="#1a2540",
                showcoastlines=True, coastlinecolor="#2a3a5c",
                showframe=False,
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("No location coordinates data to build country map.")

        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)

        with col_l:
            st.subheader("🌐 Top Countries")
            cc = db.get_top_countries(filters, 15)
            if not cc.empty:
                fig_country = px.bar(
                    cc, x="country", y="count",
                    color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                    labels={"country":"","count":"# Jobs"},
                    title="Job Postings by Search Country"
                )
                fig_country.update_traces(texttemplate="%{y:,}", textposition="outside")
                style_fig(fig_country, 400)
                fig_country.update_layout(coloraxis_showscale=False, xaxis_tickangle=-30)
                st.plotly_chart(fig_country, use_container_width=True)
            else:
                st.info("No search country details available.")

        with col_r:
            st.subheader("🏙️ Top Cities by Job Demand")
            city_df = db.get_top_cities(filters, 15)
            if not city_df.empty:
                fig_city = px.bar(
                    city_df.sort_values("count"), x="count", y="city", orientation="h",
                    color="count", color_continuous_scale=["#1e3a5f","#7c3aed"],
                    labels={"city":"","count":"# Jobs"},
                    title="Top 15 Cities by demand volume"
                )
                fig_city.update_traces(texttemplate="%{x:,}", textposition="outside")
                style_fig(fig_city, 400)
                fig_city.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_city, use_container_width=True)
            else:
                st.info("No search city details available.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📍 Top Job Locations")
        loc_df = db.get_top_locations(filters, 25)
        if not loc_df.empty:
            fig_loc = px.bar(
                loc_df.sort_values("count"), x="count", y="location", orientation="h",
                color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                labels={"location":"","count":"# Jobs"},
                title="Top 25 Job Locations details"
            )
            fig_loc.update_traces(texttemplate="%{x:,}", textposition="outside")
            style_fig(fig_loc, 600)
            fig_loc.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_loc, use_container_width=True)
        else:
            st.info("No location details available.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: JOB RECOMMENDATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Job Recommendation":
    header("🤖 Job Recommendation", "Get AI-powered job matches based on your skills")

    # Determine known skills for multiselect (fetch top 100 skills from DB)
    known_skills_df = db.get_top_skills_filtered({}, 100)
    known = known_skills_df["skill"].tolist() if not known_skills_df.empty else ["python", "sql", "aws", "excel"]

    default_skills = [s for s in ["python", "sql", "aws", "excel"] if s in known]
    
    selected = st.multiselect("🎯 Select your skills", options=[s.title() for s in known], default=[s.title() for s in default_skills])
    extra    = st.text_input("➕ Add more skills manually (comma-separated)", "")
    n_recs   = st.slider("Number of recommendations to retrieve", 5, 100, 20)

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        get_recs = st.button("🚀 Recommend Jobs", type="primary", use_container_width=True)

    if get_recs:
        extra_list = [s.strip().lower() for s in extra.split(",") if s.strip()]
        user_skills = [s.lower() for s in selected] + extra_list
        if not user_skills:
            st.warning("Please select or enter at least one skill.")
        else:
            with st.spinner("Finding matches using SQL-Backed Skill Overlap Search..."):
                results = db.get_recommendations_sql(user_skills, limit=200)
                if results.empty:
                    st.session_state["rec_results"] = None
                    st.warning("⚠️ No job postings found matching any of the selected skills.")
                else:
                    results["match_score"] = results["match_score"].round(3)
                    # Store results in session state
                    st.session_state["rec_results"] = results
                    st.session_state["rec_query_skills"] = user_skills
                    st.success("Recommendations computed successfully!")

    # Check and render session state recommendations if available
    if st.session_state["rec_results"] is not None:
        st.markdown("---")
        st.subheader("🔍 Refine and Filter Matches")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            rec_loc_filter = st.text_input("📍 Filter recommendations by location (type to search)", "")
        with col_f2:
            levels_list = ["All"] + sorted([l.title() for l in st.session_state["rec_results"]["job_level"].dropna().unique().tolist() if l])
            rec_level_filter = st.selectbox("🎓 Filter recommendations by experience level", levels_list)

        # Apply filters on session state dataframe
        filtered_recs = st.session_state["rec_results"].copy()
        if rec_loc_filter:
            filtered_recs = filtered_recs[filtered_recs["job_location"].str.contains(rec_loc_filter.lower(), case=False, na=False)]
        if rec_level_filter != "All":
            filtered_recs = filtered_recs[filtered_recs["job_level"].str.lower() == rec_level_filter.lower()]

        display_recs = filtered_recs.head(n_recs)
        st.success(f"✅ Displaying **{len(display_recs)}** matching recommendations (from {len(filtered_recs)} total matches)")

        if display_recs.empty:
            st.info("No matching recommendations found for the selected location or level filters.")
        else:
            for _, row in display_recs.iterrows():
                score_pct = int(row["match_score"] * 100)
                job_link = row.get('job_link', '')
                link_html = f'<a href="{job_link}" target="_blank" style="text-decoration:none; color:#00d4ff; font-weight:600; font-size:0.82rem; margin-top:8px; display:inline-block;">🔗 View Job Posting &rarr;</a>' if job_link and str(job_link).startswith("http") else ''
                
                # Format skills: Highlight matching skills in bold cyan
                skills_list = [s.strip() for s in str(row.get('job_skills','')).split(",") if s.strip()]
                formatted_skills = []
                for s in skills_list:
                    if s.lower() in st.session_state["rec_query_skills"]:
                        formatted_skills.append(f"<b style='color:#00d4ff;'>{s.title()}</b>")
                    else:
                        formatted_skills.append(s.title())
                skills_str = ", ".join(formatted_skills)

                st.markdown(f"""
                <div class="job-card">
                  <h4>💼 {row.get('job_title','N/A').title()}</h4>
                  <div class="meta">
                    🏢 <b>{row.get('company','N/A').title()}</b> &nbsp;|&nbsp;
                    📍 {row.get('job_location','N/A').title()} &nbsp;|&nbsp;
                    🎓 {row.get('job_level','N/A').title()} &nbsp;|&nbsp;
                    🕐 {row.get('job_type','N/A').title()}
                  </div>
                  <div class="meta" style="margin-top:6px;">🛠️ Skills: {skills_str if skills_str else 'N/A'}</div>
                  {link_html}
                  <div style="margin-top:10px;font-size:0.8rem;color:#94a3b8;">Match Score: {score_pct}%</div>
                  <div class="score-bar">
                    <div class="score-fill" style="width:{score_pct}%;"></div>
                  </div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: JOB SEARCH
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Job Search":
    header("🔍 Job Search", "Find jobs by title, location, skill, type, and level")

    # Local Filters Expander, pre-populated with global sidebar inputs
    with st.expander("🎛️ Filter Results", expanded=True):
        f1, f2 = st.columns(2)
        title_q    = f1.text_input("Job Title Keyword", value=title_kw, key="search_page_title")
        location_q = f2.text_input("Location Keyword (City / Country)", value=selected_city if selected_city != "All" else "", key="search_page_loc")

        f3, f4, f5 = st.columns(3)
        skill_q    = f3.text_input("Skill keyword", value=skill_kw, key="search_page_skill")
        
        # Pull options dynamically from DB for drop-downs
        levels = ["All"] + [l.title() for l in db_levels]
        types = ["All"] + [t.title() for t in db_types]
        
        # Pre-select matching values from global filters
        def_level_idx = levels.index(selected_level) if selected_level in levels else 0
        def_type_idx = types.index(selected_type) if selected_type in types else 0
        
        level_sel  = f4.selectbox("Job Level", levels, index=def_level_idx, key="search_page_level")
        type_sel   = f5.selectbox("Job Type",  types, index=def_type_idx, key="search_page_type")

    # Apply search filters to the database query
    search_filters = {
        "title_kw": title_q,
        "location_kw": location_q,
        "skill_kw": skill_q,
        "job_level": level_sel,
        "job_type": type_sel
    }

    # Fetch matching counts and statistics
    search_kpis = db.get_kpis(search_filters)
    total = search_kpis["total_jobs"]

    # Search Results KPIs
    s1, s2, s3 = st.columns(3)
    kpi(s1, "Matching Jobs Found", f"{total:,}")
    kpi(s2, "Companies", f"{search_kpis['total_companies']:,}")
    kpi(s3, "Locations", f"{search_kpis['total_locations']:,}")
    st.markdown("<br>", unsafe_allow_html=True)

    if total > 0:
        # Load actual search results from DB (limit to 200 for fast page render)
        search_results = db.search_jobs(search_filters, limit=200)

        # Format dataframe fields for visualization
        disp_df = search_results.copy()
        for col in ["job_title", "company", "job_location", "job_type", "job_level"]:
            if col in disp_df.columns:
                disp_df[col] = disp_df[col].astype(str).str.title()

        st.subheader(f"📋 Search Results (showing top 200 of {total:,})")
        st.dataframe(
            disp_df,
            use_container_width=True,
            height=400,
            column_config={
                "job_link": st.column_config.LinkColumn("Job Link", display_text="Open Link 🔗"),
                "job_title": "Job Title",
                "company": "Company",
                "job_location": "Location",
                "job_type": "Job Type",
                "job_level": "Job Level",
                "job_skills": "Skills"
            }
        )

        # CSV Download Button (loads top 1000 from database)
        csv_results = db.search_jobs(search_filters, limit=1000)
        csv_out = csv_results.to_csv(index=False).encode()
        st.download_button("⬇ Download Top 1000 Search Results CSV", csv_out, "job_search_results.csv", "text/csv")

        # Summary charts for search results
        st.markdown("---")
        st.subheader("📊 Search Results Insights")

        r1, r2 = st.columns(2)
        with r1:
            top_c = db.get_top_hiring_companies(search_filters, 10)
            if not top_c.empty:
                fc = px.bar(
                    top_c.sort_values("count"), x="count", y="company", orientation="h",
                    color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                    labels={"company":"","count":"# Jobs"},
                    title="Top Hiring Companies in Results"
                )
                style_fig(fc, 350)
                fc.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fc, use_container_width=True)
            else:
                st.info("No company analytics available for these search results.")
            
        with r2:
            top_l = db.get_top_locations(search_filters, 10)
            if not top_l.empty:
                fl = px.bar(
                    top_l.sort_values("count"), x="count", y="location", orientation="h",
                    color="count", color_continuous_scale=["#1e3a5f","#7c3aed"],
                    labels={"location":"","count":"# Jobs"},
                    title="Top Job Locations in Results"
                )
                style_fig(fl, 350)
                fl.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fl, use_container_width=True)
            else:
                st.info("No location analytics available for these search results.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🛠️ Top Skills in Search Results")
        results_skills = db.get_top_skills_filtered(search_filters, 15)
        if not results_skills.empty:
            fs = px.bar(
                results_skills.sort_values("count"), x="count", y="skill_name", orientation="h",
                color="count", color_continuous_scale=["#1e3a5f","#00d4ff"],
                labels={"skill_name":"","count":"# Jobs"},
                title="Top 15 Skills Required in filtered search results"
            )
            style_fig(fs, 400)
            fs.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fs, use_container_width=True)
        else:
            st.info("No skill counts available for the search results.")
    else:
        st.info("No job listings match your current filters. Try loosening your keywords or drop-down selects.")