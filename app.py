import os
import io
import time
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CycloMart Influencer Dashboard", layout="wide")

# --------- Helpers
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

def try_load_default(name):
    path = f"/content/{name}.csv"
    if os.path.exists(path):
        return load_csv(path)
    return None

def kpi_card(label, value, help_text=None, fmt="{:,.0f}"):
    with st.container(border=True):
        st.caption(label)
        if isinstance(value, (int, float, np.integer, np.floating)):
            st.markdown(f"### {fmt.format(value)}")
        else:
            st.markdown(f"### {value}")
        if help_text:
            st.caption(help_text)

# --------- Sidebar: Data & Filters
st.sidebar.header("Data")
st.sidebar.write("Load CSVs (or leave blank to use defaults if saved by the notebook).")

u_master = st.sidebar.file_uploader("master_df.csv", type=["csv"])
u_platform = st.sidebar.file_uploader("platform_performance.csv", type=["csv"])
u_persona = st.sidebar.file_uploader("persona_performance.csv", type=["csv"])
u_tracking = st.sidebar.file_uploader("tracking_df.csv", type=["csv"])

# Load priority: uploaded → default path → error
if u_master is not None:
    master_df = pd.read_csv(u_master)
else:
    df_ = try_load_default("master_df")
    if df_ is None:
        st.stop()
    master_df = df_

if u_platform is not None:
    platform_performance = pd.read_csv(u_platform)
else:
    platform_performance = try_load_default("platform_performance")

if u_persona is not None:
    persona_performance = pd.read_csv(u_persona)
else:
    persona_performance = try_load_default("persona_performance")

if u_tracking is not None:
    tracking_df = pd.read_csv(u_tracking)
else:
    tracking_df = try_load_default("tracking_df")

# Ensure expected cols exist (soft checks)
needed_master = {"influencer_id","name","platform","category","follower_count","roas","total_revenue",
                 "total_payout","total_orders","total_reach","total_likes","total_comments",
                 "engagement_rate","conversion_rate","efficiency_score","performance_category",
                 "follower_tier","persona_combination"}
missing = [c for c in needed_master if c not in master_df.columns]
if missing:
    st.warning(f"master_df is missing columns: {missing}. Some charts may not render.")

# Filters
st.sidebar.header("Filters")
brands = master_df["brand"].dropna().unique().tolist() if "brand" in master_df.columns else []
products = master_df["product"].dropna().unique().tolist() if "product" in master_df.columns else []
platforms = master_df["platform"].dropna().unique().tolist()
categories = master_df["category"].dropna().unique().tolist()
tiers = master_df["follower_tier"].dropna().unique().tolist() if "follower_tier" in master_df.columns else []
perf_cats = master_df["performance_category"].dropna().unique().tolist() if "performance_category" in master_df.columns else []

f_brand = st.sidebar.multiselect("Brand", options=brands, default=brands if brands else [])
f_product = st.sidebar.multiselect("Product", options=products, default=products if products else [])
f_platform = st.sidebar.multiselect("Platform", options=platforms, default=platforms)
f_category = st.sidebar.multiselect("Category", options=categories, default=categories)
f_tier = st.sidebar.multiselect("Influencer Tier", options=tiers, default=tiers if tiers else [])
f_perf = st.sidebar.multiselect("Performance Category", options=perf_cats, default=perf_cats if perf_cats else [])

# Date filter (based on first/last_post_date if present)
date_min = pd.to_datetime(master_df.get("first_post_date")).min() if "first_post_date" in master_df.columns else None
date_max = pd.to_datetime(master_df.get("last_post_date")).max() if "last_post_date" in master_df.columns else None
if date_min is not None and pd.notna(date_min) and date_max is not None and pd.notna(date_max):
    dr = st.sidebar.date_input("Date Range (by post window)", value=(date_min.date(), date_max.date()))
    if isinstance(dr, tuple) and len(dr) == 2:
        d_start, d_end = pd.to_datetime(dr[0]), pd.to_datetime(dr[1])
    else:
        d_start, d_end = date_min, date_max
else:
    d_start = d_end = None

# Apply filters
df = master_df.copy()
if f_brand and "brand" in df.columns:
    df = df[df["brand"].isin(f_brand)]
if f_product and "product" in df.columns:
    df = df[df["product"].isin(f_product)]
if f_platform:
    df = df[df["platform"].isin(f_platform)]
if f_category:
    df = df[df["category"].isin(f_category)]
if f_tier:
    df = df[df["follower_tier"].isin(f_tier)]
if f_perf:
    df = df[df["performance_category"].isin(f_perf)]
if d_start is not None and d_end is not None and "first_post_date" in df.columns and "last_post_date" in df.columns:
    df["first_post_date"] = pd.to_datetime(df["first_post_date"], errors="coerce")
    df["last_post_date"] = pd.to_datetime(df["last_post_date"], errors="coerce")
    df = df[(df["last_post_date"] >= d_start) & (df["first_post_date"] <= d_end)]

# ---------------- Row 1: Executive Summary (4 KPI cards)
st.markdown("## Executive Summary")
k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Total Revenue", df["total_revenue"].sum(), fmt="₹{:,.0f}")
with k2:
    total_payout = df["total_payout"].sum()
    overall_roas = (df["total_revenue"].sum() / total_payout) if total_payout > 0 else 0
    kpi_card("Overall ROAS", overall_roas, fmt="{:,.2f}x")
with k3:
    if tracking_df is not None and "campaign" in tracking_df.columns:
        active_campaigns = tracking_df["campaign"].nunique()
    else:
        active_campaigns = int(df.get("campaigns_count", pd.Series([0])).sum())
    kpi_card("Active Campaigns", active_campaigns)
with k4:
    kpi_card("Total Influencers", df["influencer_id"].nunique())

st.divider()

# ---------------- Row 2: Influencer-Level (Leaderboard + Scatter)
st.markdown("## Influencer Performance")

c1, c2 = st.columns([2, 1], gap="large")

with c1:
    st.subheader("Leaderboard")
    cols = [c for c in ["name","platform","category","roas","total_revenue","engagement_rate","total_payout","total_orders"] if c in df.columns]
    table_df = df[cols].copy().sort_values("roas", ascending=False).reset_index(drop=True)
    st.dataframe(table_df, use_container_width=True, height=420)

with c2:
    st.subheader("ROAS vs Engagement")
    if {"engagement_rate","roas"}.issubset(df.columns):
        scatter_df = df.dropna(subset=["engagement_rate","roas"]).copy()
        scatter_df["bubble_size"] = np.clip(scatter_df.get("total_revenue", 0), 1, None)
        color_col = "performance_category" if "performance_category" in scatter_df.columns else "platform"
        fig = px.scatter(
            scatter_df, x="engagement_rate", y="roas",
            size="bubble_size", color=color_col,
            hover_data=["name","platform","total_revenue"],
            size_max=40, title=None
        )
        fig.update_layout(margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need columns: engagement_rate, roas.")

st.divider()

# ---------------- Row 3: Platform & Persona (side-by-side)
st.markdown("## Platform & Persona Insights")
p1, p2 = st.columns(2, gap="large")

with p1:
    st.subheader("Platform Performance")
    # Bars: ROAS by platform
    if "platform" in df.columns and {"total_revenue","total_payout"}.issubset(df.columns):
        plat = df.groupby("platform", as_index=False).agg(
            total_revenue=("total_revenue","sum"),
            total_payout=("total_payout","sum"),
            total_orders=("total_orders","sum"),
            total_reach=("total_reach","sum"),
            influencer_count=("name","count")
        )
        plat["platform_roas"] = np.where(plat["total_payout"]>0, plat["total_revenue"]/plat["total_payout"], 0)
        plat["revenue_share"] = np.where(plat["total_revenue"].sum()>0, plat["total_revenue"]/plat["total_revenue"].sum()*100, 0)

        fig1 = px.bar(plat.sort_values("platform_roas", ascending=False),
                      x="platform", y="platform_roas", text="platform_roas")
        fig1.update_traces(texttemplate="%{text:.2f}x", textposition="outside", cliponaxis=False)
        fig1.update_layout(yaxis_title="ROAS", xaxis_title="", margin=dict(l=10,r=10,t=10,b=10), height=320)
        st.plotly_chart(fig1, use_container_width=True)

        # Donut: revenue share
        fig2 = px.pie(plat, values="total_revenue", names="platform", hole=0.5)
        fig2.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=320)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Need platform, total_revenue, total_payout in master_df.")

with p2:
    st.subheader("Persona Insights")
    if "persona_combination" in df.columns and "roas" in df.columns:
        persona_mean = df.groupby("persona_combination", as_index=False).agg(
            avg_roas=("roas","mean"),
            efficiency_score=("efficiency_score","mean"),
            revenue=("total_revenue","sum"),
            influencer_count=("name","count")
        )
        persona_mean = persona_mean.sort_values("avg_roas", ascending=False)

        # Heatmap-like bar for Avg ROAS by persona
        fig3 = px.bar(persona_mean, x="persona_combination", y="avg_roas", hover_data=["efficiency_score","revenue","influencer_count"])
        fig3.update_layout(xaxis_title="", yaxis_title="Avg ROAS", xaxis_tickangle=45, margin=dict(l=10,r=10,t=10,b=10), height=320)
        st.plotly_chart(fig3, use_container_width=True)

        # Supporting table
        show_cols = ["persona_combination","avg_roas","efficiency_score","revenue","influencer_count"]
        st.dataframe(persona_mean[show_cols], use_container_width=True, height=260)
    else:
        st.info("Need persona_combination and roas in master_df.")

st.divider()

# ---------------- Row 4: Category Insights (3 columns L→R)
st.markdown("## Category Insights")
cL, cC, cR = st.columns(3, gap="large")

with cL:
    st.subheader("Avg ROAS by Category")
    if {"category","roas"}.issubset(df.columns):
        cat = df.groupby("category", as_index=False).agg(avg_roas=("roas","mean"))
        fig = px.bar(cat.sort_values("avg_roas", ascending=True), x="avg_roas", y="category", orientation="h", text="avg_roas")
        fig.update_traces(texttemplate="%{text:.2f}x")
        fig.update_layout(xaxis_title="Avg ROAS", yaxis_title="", margin=dict(l=10,r=10,t=10,b=10), height=360)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need category and roas.")

with cC:
    st.subheader("Engagement Rate by Category")
    if {"category","engagement_rate"}.issubset(df.columns):
        cat_e = df.groupby("category", as_index=False).agg(avg_eng=("engagement_rate","mean"))
        fig = px.bar(cat_e.sort_values("avg_eng", ascending=False), x="category", y="avg_eng", text="avg_eng")
        fig.update_traces(texttemplate="%{text:.2f}%")
        fig.update_layout(xaxis_title="", yaxis_title="Engagement Rate (%)", margin=dict(l=10,r=10,t=10,b=10), height=360)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need category and engagement_rate.")

with cR:
    st.subheader("Category Summary")
    have_cols = [c for c in ["category","total_revenue","roas","engagement_rate","name"] if c in df.columns]
    if set(["category"]).issubset(have_cols):
        cat_tbl = df.groupby("category", as_index=False).agg(
            revenue=("total_revenue","sum") if "total_revenue" in df.columns else ("category","count"),
            avg_roas=("roas","mean") if "roas" in df.columns else ("category","count"),
            avg_eng=("engagement_rate","mean") if "engagement_rate" in df.columns else ("category","count"),
            influencer_count=("name","count") if "name" in df.columns else ("category","count")
        )
        st.dataframe(cat_tbl.sort_values("avg_roas", ascending=False), use_container_width=True, height=360)
    else:
        st.info("Need category plus revenue/roas/engagement_rate.")

st.divider()

# ---------------- Row 5: Investment Recommendations (3 columns L→R)
st.markdown("## Investment Recommendations")

def build_actions(src):
    if src.empty:
        return pd.DataFrame(columns=["name","roas","total_payout","total_revenue","platform"])
    q30 = src["total_payout"].quantile(0.30)
    q70 = src["total_payout"].quantile(0.70)
    invest_more = src[(src["roas"] >= 3.5) & (src["total_payout"] <= q30)].nlargest(5, "roas")[["name","roas","total_payout","total_revenue","platform"]]
    optimize = src[(src["roas"] < 2.0) & (src["total_payout"] >= q70)].nsmallest(5, "roas")[["name","roas","total_payout","total_revenue","platform"]]
    monitor = src[(src["roas"] >= 2.0) & (src["roas"] < 3.5)].copy()
    if not monitor.empty:
        monitor = monitor.sample(min(5, len(monitor)))[["name","roas","total_payout","total_revenue","platform"]]
    else:
        monitor = monitor.reindex(columns=["name","roas","total_payout","total_revenue","platform"])
    return invest_more, optimize, monitor

i_df, o_df, m_df = build_actions(df if not df.empty else master_df)

a, b, c = st.columns(3, gap="large")
with a:
    st.subheader("Invest More")
    st.dataframe(i_df, use_container_width=True, height=260)
with b:
    st.subheader("Optimize")
    st.dataframe(o_df, use_container_width=True, height=260)
with c:
    st.subheader("Monitor")
    st.dataframe(m_df, use_container_width=True, height=260)

st.divider()

# ---------------- Optional Exports
st.markdown("### Export")
colx, coly, colz = st.columns(3)
with colx:
    if st.button("Export filtered master_df CSV"):
        df.to_csv("filtered_master_df.csv", index=False)
        st.success("Saved filtered_master_df.csv")

with coly:
    # Rebuild platform metrics on filtered df for export
    if {"platform","total_revenue","total_payout"}.issubset(df.columns):
        plat = df.groupby("platform", as_index=False).agg(
            total_revenue=("total_revenue","sum"),
            total_payout=("total_payout","sum"),
            total_orders=("total_orders","sum"),
            total_reach=("total_reach","sum"),
            influencer_count=("name","count")
        )
        plat["platform_roas"] = np.where(plat["total_payout"]>0, plat["total_revenue"]/plat["total_payout"], 0)
        plat["revenue_share"] = np.where(plat["total_revenue"].sum()>0, plat["total_revenue"]/plat["total_revenue"].sum()*100, 0)
        if st.button("Export platform_performance CSV"):
            plat.to_csv("platform_performance_filtered.csv", index=False)
            st.success("Saved platform_performance_filtered.csv")
with colz:
    # Rebuild persona metrics on filtered df for export
    if {"persona_combination","roas"}.issubset(df.columns):
        persona_mean = df.groupby("persona_combination", as_index=False).agg(
            avg_roas=("roas","mean"),
            efficiency_score=("efficiency_score","mean"),
            revenue=("total_revenue","sum"),
            influencer_count=("name","count")
        )
        if st.button("Export persona_performance CSV"):
            persona_mean.to_csv("persona_performance_filtered.csv", index=False)
            st.success("Saved persona_performance_filtered.csv")

st.caption("Tip: For permanent sharing, push this app to a GitHub repo and deploy on Streamlit Community Cloud.")
