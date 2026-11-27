"""
Airtel Telecom Analytics — Customer Service Dashboard
Domain D · Group 4
Entry-point: streamlit run dashboard/app.py
"""

import base64, gzip, json, pathlib, sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ──────────────────────────────────────────────────────────────
# 0.  Page config & styling (Red & White UI · Black Fonts)
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Airtel · Customer Service",
    page_icon="📞",
    layout="wide",
)

BG_PATH = pathlib.Path(__file__).resolve().parent / "airtel_bg.jpg"
bg_css = ""
if BG_PATH.exists():
    bg_b64 = base64.b64encode(BG_PATH.read_bytes()).decode()
    bg_css = (
        f'background-image: linear-gradient(135deg, rgba(232, 25, 44, 0.08) 0%, rgba(255, 255, 255, 0.06) 50%, rgba(232, 25, 44, 0.08) 100%), '
        f'url("data:image/jpeg;base64,{bg_b64}");'
        f"background-size: cover; background-position: center; background-attachment: fixed;"
    )

st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"]{{
        {bg_css}
        color: #111111 !important;
    }}
    [data-testid="stHeader"]{{background: transparent !important;}}
    .block-container{{padding-top:1rem;padding-bottom:0.5rem;}}
    h1, h2, h3, p, span, label, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"]{{
        color: #111111 !important;
    }}
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] p strong{{
        background: rgba(255, 255, 255, 0.90);
        padding: 4px 12px;
        border-radius: 6px;
        border-left: 3px solid #e8192c;
        display: inline-block;
    }}
    [data-testid="stMetric"]{{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.90) 0%, rgba(255, 240, 242, 0.86) 100%) !important;
        border: 1px solid rgba(232, 25, 44, 0.24);
        border-left: 4px solid #e8192c !important;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 3px 10px rgba(232, 25, 44, 0.10);
    }}
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *{{
        font-size: 0.82rem; color: #111111 !important;
    }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] *{{
        font-size: 1.4rem; color: #111111 !important; font-weight: 700;
    }}
    div[data-testid="stTabs"] [data-baseweb="tab-list"]{{
        gap: 12px;
        border-bottom: none !important;
    }}
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] [data-baseweb="tab-border"]{{
        display: none !important;
    }}
    div[data-testid="stTabs"] button{{
        font-size: 0.95rem;
        font-weight: 600;
        color: #111111 !important;
        background: linear-gradient(135deg, #ffffff 0%, #fff0f2 100%) !important;
        border: 1.5px solid #e8192c !important;
        border-radius: 10px !important;
        padding: 6px 24px !important;
        box-shadow: 0 2px 8px rgba(232, 25, 44, 0.10);
    }}
    div[data-testid="stTabs"] button[aria-selected="true"]{{
        background: linear-gradient(135deg, #ff2a3c 0%, #c81020 100%) !important;
        color: #111111 !important;
        border: 1.5px solid #c81020 !important;
        box-shadow: 0 4px 12px rgba(232, 25, 44, 0.28);
    }}
    [data-testid="stSidebar"]{{
        background-color: #ffffff !important;
        background-image:
            radial-gradient(circle at 100% 0%, rgba(232, 25, 44, 0.34) 0%, rgba(232, 25, 44, 0.12) 28%, transparent 55%),
            linear-gradient(180deg, rgba(255, 242, 244, 0.98) 0%, rgba(255, 255, 255, 0.97) 55%, rgba(255, 232, 236, 0.97) 100%) !important;
        border-right: 1px solid rgba(232, 25, 44, 0.22);
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarContent"]{{padding-top:1.2rem;}}
    div[data-baseweb="select"] > div{{
        background: linear-gradient(135deg, #ffffff 0%, #fff6f7 100%) !important;
        color: #111111 !important;
        border: 1px solid rgba(232, 25, 44, 0.35) !important;
        border-left: 4px solid #e8192c !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(232, 25, 44, 0.08);
    }}
    div[data-baseweb="select"] span, div[data-baseweb="select"] svg{{
        color: #111111 !important; fill: #111111 !important;
    }}
    [data-testid="stPlotlyChart"]{{
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(232, 25, 44, 0.16);
        box-shadow: 0 3px 12px rgba(232, 25, 44, 0.08);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _style_fig(fig: go.Figure) -> go.Figure:
    """Apply Red & White theme with crisp black fonts to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(255, 255, 255, 0.86)",
        plot_bgcolor="rgba(255, 255, 255, 0.86)",
        font=dict(color="#111111"),
        title_font=dict(color="#111111", size=14),
        xaxis=dict(color="#111111", tickfont=dict(color="#111111"), title_font=dict(color="#111111"), gridcolor="rgba(0,0,0,0.08)"),
        yaxis=dict(color="#111111", tickfont=dict(color="#111111"), title_font=dict(color="#111111"), gridcolor="rgba(0,0,0,0.08)"),
    )
    return fig

# ──────────────────────────────────────────────────────────────
# 1.  Database helper  q()
# ──────────────────────────────────────────────────────────────
DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw" / "airtel.db"
LITE_PATH = pathlib.Path(__file__).resolve().parent / "airtel_data.json.gz"


@st.cache_resource
def _cloud_conn() -> sqlite3.Connection:
    """Build an in-memory SQLite DB from airtel_data.json.gz when airtel.db is absent (e.g. Streamlit Cloud)."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    data = json.loads(gzip.decompress(LITE_PATH.read_bytes()).decode("utf-8"))
    conn.execute(
        "CREATE TABLE complaints (complaint_id INTEGER, customer_id INTEGER, "
        "complaint_date TEXT, category TEXT, channel TEXT, is_resolved INTEGER, resolution_days REAL)"
    )
    conn.executemany("INSERT INTO complaints VALUES (?,?,?,?,?,?,?)", data["complaints"])
    conn.execute(
        "CREATE TABLE customer_features (customer_id INTEGER, circle_name TEXT, region TEXT, "
        "age_band TEXT, connection_type TEXT, is_churned INTEGER, complaint_count INTEGER, unresolved_count INTEGER)"
    )
    conn.executemany("INSERT INTO customer_features VALUES (?,?,?,?,?,?,?,?)", data["customer_features"])
    conn.commit()
    return conn


def q(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run *sql* against the project SQLite database (or cloud fallback) and return a DataFrame."""
    if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        with sqlite3.connect(str(DB_PATH)) as conn:
            return pd.read_sql_query(sql, conn, params=params)
    return pd.read_sql_query(sql, _cloud_conn(), params=params)


# ──────────────────────────────────────────────────────────────
# 2.  Sidebar filters  — Connection type & Region
# ──────────────────────────────────────────────────────────────
st.sidebar.markdown("### Filters")

conn_types = ["All"] + q("SELECT DISTINCT connection_type FROM customer_features ORDER BY 1")["connection_type"].tolist()
sel_conn = st.sidebar.selectbox("Customer Type", conn_types, index=0)

regions = ["All"] + q("SELECT DISTINCT region FROM customer_features ORDER BY 1")["region"].tolist()
sel_region = st.sidebar.selectbox("Region", regions, index=0)


def _where(table_prefix: str = "", extra: str = "") -> str:
    """Build a WHERE clause fragment for the active filters."""
    clauses = []
    if sel_conn != "All":
        clauses.append(f"{table_prefix}connection_type = '{sel_conn}'")
    if sel_region != "All":
        clauses.append(f"{table_prefix}region = '{sel_region}'")
    if extra:
        clauses.append(extra)
    return ("WHERE " + " AND ".join(clauses)) if clauses else ("WHERE " + extra if extra else "")


def _where_cf(extra: str = "") -> str:
    """WHERE clause using customer_features columns (no prefix needed)."""
    return _where("", extra)


# ──────────────────────────────────────────────────────────────
# 3.  Title
# ──────────────────────────────────────────────────────────────
ICON_PATH = pathlib.Path(__file__).resolve().parent / "airtel_icon.png"
icon_html = ""
if ICON_PATH.exists():
    icon_b64 = base64.b64encode(ICON_PATH.read_bytes()).decode()
    icon_html = (
        f'<img src="data:image/png;base64,{icon_b64}" '
        f'style="height:54px;width:auto;display:block;" alt="Airtel">'
        f'<div style="width:1.5px;height:52px;background:rgba(17,17,17,0.35);margin:0 18px;"></div>'
    )

st.markdown(
    f"""
    <div style="background:linear-gradient(115deg,rgba(255,255,255,0.98) 0%,rgba(255,244,246,0.96) 65%,rgba(255,224,228,0.95) 100%);
                border:1px solid rgba(232,25,44,0.24);
                border-left:5px solid #e8192c;border-radius:10px;padding:14px 20px;
                box-shadow:0 4px 14px rgba(232,25,44,0.12);margin-bottom:10px;">
        <div style="display:flex;align-items:center;">
            {icon_html}
            <div>
                <div style="font-size:2.05rem;font-weight:800;line-height:1.15;color:#111111;letter-spacing:-0.02em;">
                    Airtel Telecom Analytics
                </div>
                <div style="font-size:1.0rem;font-weight:500;color:#444444;margin-top:2px;">
                    Domain D — Customer service
                </div>
            </div>
        </div>
        <div style="font-size:0.86rem;color:#333333;margin-top:8px;">
            This dashboard helps the Head of Customer Service prioritise service effort and understand ticket patterns and ticket-status relationships.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# 4.  Tabs
# ──────────────────────────────────────────────────────────────
tab_overview, tab_detail = st.tabs(["Overview", "Detail"])


# ══════════════════════════════════════════════════════════════
#       OVERVIEW TAB
# ══════════════════════════════════════════════════════════════
with tab_overview:

    # ── 4a. Three metric cards ────────────────────────────────
    c1, c2, c3 = st.columns(3)

    # Card 1 — Fixed total ticket count (ignores filters)
    total_tickets = q("SELECT COUNT(*) AS n FROM complaints")["n"].iloc[0]
    c1.metric("Total Tickets", f"{total_tickets:,}")

    # Card 2 — T7 chi-squared test result (fixed / validated)
    c2.metric("T7 χ² Test (Two-tailed · p < 0.001)", "χ² = 101.37")

    # Card 3 — Open-ticket count & share (responds to filters)
    df_open = q(
        f"""
        SELECT COUNT(*) AS open_n
        FROM complaints co
        JOIN customer_features cf ON co.customer_id = cf.customer_id
        {_where_cf("co.is_resolved = 0")}
        """
    )
    open_n = int(df_open["open_n"].iloc[0])

    df_denom = q(
        f"""
        SELECT COUNT(*) AS total_n
        FROM complaints co
        JOIN customer_features cf ON co.customer_id = cf.customer_id
        {_where_cf()}
        """
    )
    total_n = int(df_denom["total_n"].iloc[0])
    open_pct = round(open_n * 100 / total_n, 1) if total_n else 0

    c3.metric("Open Tickets", f"{open_n:,}  ({open_pct}%)")

    # ── 4b. Hero chart — Churn rate by complaint history (Lollipop) ──
    h_title_col, h_flt_col = st.columns([3.5, 1])
    age_bands = ["All Ages"] + q("SELECT DISTINCT age_band FROM customer_features ORDER BY 1")["age_band"].tolist()
    sel_age_hero = h_flt_col.selectbox("Age Band (Hero)", age_bands, key="flt_hero_age", label_visibility="collapsed")
    age_extra = f"age_band = '{sel_age_hero}'" if sel_age_hero != "All Ages" else ""

    df_churn_hist = q(
        f"""
        SELECT
            CASE
                WHEN complaint_count = 0 THEN 'No ticket'
                WHEN unresolved_count  = 0 THEN 'All closed'
                ELSE 'One+ open'
            END AS complaint_history,
            COUNT(*)            AS subscribers,
            SUM(is_churned)     AS churned,
            ROUND(SUM(is_churned)*100.0/COUNT(*),1) AS churn_rate
        FROM customer_features
        {_where_cf(age_extra)}
        GROUP BY 1
        """
    )
    order = ["No ticket", "All closed", "One+ open"]
    df_churn_hist["complaint_history"] = pd.Categorical(
        df_churn_hist["complaint_history"], categories=order, ordered=True
    )
    df_churn_hist = df_churn_hist.sort_values("complaint_history")

    overall_churn = q(
        f"SELECT ROUND(AVG(is_churned)*100,1) AS rate FROM customer_features {_where_cf(age_extra)}"
    )["rate"].iloc[0]

    colors_lolli = ["#6c757d", "#fa5252", "#e8192c"]
    fig_hero = go.Figure()
    for idx, row in enumerate(df_churn_hist.itertuples()):
        c = colors_lolli[idx % len(colors_lolli)]
        fig_hero.add_trace(
            go.Scatter(
                x=[row.complaint_history, row.complaint_history],
                y=[0, row.churn_rate],
                mode="lines",
                line=dict(color=c, width=4),
                showlegend=False,
                hoverinfo="skip",
            )
        )
    fig_hero.add_trace(
        go.Scatter(
            x=df_churn_hist["complaint_history"],
            y=df_churn_hist["churn_rate"],
            mode="markers+text",
            marker=dict(size=18, color=colors_lolli[: len(df_churn_hist)], line=dict(width=2, color="#ffffff")),
            text=[
                f"{r:.1f}% (n={s:,})"
                for r, s in zip(df_churn_hist["churn_rate"], df_churn_hist["subscribers"])
            ],
            textposition="top center",
            showlegend=False,
            hovertemplate="<b>%{x}</b><br>Churn Rate: %{y:.1f}%<extra></extra>",
        )
    )
    fig_hero.add_hline(
        y=overall_churn,
        line_dash="dash",
        line_color="#868e96",
        annotation_text=f"Overall churn {overall_churn:.1f}%",
        annotation_position="top left",
    )
    max_y = float(df_churn_hist["churn_rate"].max()) * 1.28 if len(df_churn_hist) else 35
    age_tag = f" · {sel_age_hero}" if sel_age_hero != "All Ages" else ""
    fig_hero.update_layout(
        title=f"Subscribers with open tickets churn more — is ticket status associated with leaving?{age_tag}",
        yaxis_title="Churn Rate (%)",
        xaxis_title="Complaint History Group",
        yaxis=dict(range=[0, max_y]),
        height=295,
        margin=dict(t=45, b=25),
        showlegend=False,
    )
    h_title_col.markdown("**Lollipop Chart — Churn by Complaint History**")
    st.plotly_chart(_style_fig(fig_hero), use_container_width=True, key="hero_overview")

    # ── 4c. Supporting charts (each with its own filter) ──────
    left, right = st.columns(2)

    with left:
        l_hdr, l_flt = st.columns([2, 1])
        months = ["All Months"] + q("SELECT DISTINCT substr(complaint_date,1,7) AS m FROM complaints ORDER BY 1")["m"].tolist()
        sel_month_hm = l_flt.selectbox("Month (Heatmap)", months, key="flt_hm_month", label_visibility="collapsed")
        hm_extra = f"substr(co.complaint_date,1,7) = '{sel_month_hm}'" if sel_month_hm != "All Months" else ""

        df_closure = q(
            f"""
            SELECT co.category,
                   co.channel,
                   COUNT(*)                           AS total,
                   SUM(co.is_resolved)                AS closed,
                   ROUND(SUM(co.is_resolved)*100.0/COUNT(*),1) AS closure_pct
            FROM complaints co
            JOIN customer_features cf ON co.customer_id = cf.customer_id
            {_where_cf(hm_extra)}
            GROUP BY co.category, co.channel
            ORDER BY co.category, co.channel
            """
        )
        piv_pct = df_closure.pivot(index="category", columns="channel", values="closure_pct")
        piv_cnt = df_closure.pivot(index="category", columns="channel", values="total")
        piv_cls = df_closure.pivot(index="category", columns="channel", values="closed")

        cell_text = [
            [
                f"{piv_pct.loc[cat, ch]:.1f}%<br>({int(piv_cls.loc[cat, ch]):,}/{int(piv_cnt.loc[cat, ch]):,})"
                if pd.notna(piv_pct.loc[cat, ch]) else ""
                for ch in piv_pct.columns
            ]
            for cat in piv_pct.index
        ]
        fig_closure = go.Figure(
            go.Heatmap(
                z=piv_pct.values,
                x=piv_pct.columns.tolist(),
                y=piv_pct.index.tolist(),
                text=cell_text,
                texttemplate="%{text}",
                textfont=dict(size=10),
                colorscale="Reds",
                colorbar=dict(title="Closure %", thickness=12, tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
                hovertemplate="<b>%{y} · %{x}</b><br>Closure Share: %{z:.1f}%<extra></extra>",
            )
        )
        m_tag = f" · {sel_month_hm}" if sel_month_hm != "All Months" else ""
        fig_closure.update_layout(
            title=f"Which categories & channels close the most tickets?{m_tag}",
            xaxis_title="Channel",
            yaxis_title="Complaint Category",
            height=275,
            margin=dict(t=40, b=25, l=120),
        )
        l_hdr.markdown("**Heatmap — Closure Share by Category & Channel**")
        st.plotly_chart(_style_fig(fig_closure), use_container_width=True, key="closure_overview")

    with right:
        r_hdr, r_flt = st.columns([2, 1])
        cats_all = ["All Categories"] + q("SELECT DISTINCT category FROM complaints ORDER BY 1")["category"].tolist()
        sel_cat_tm = r_flt.selectbox("Category (Treemap)", cats_all, key="flt_tm_cat", label_visibility="collapsed")
        tm_join_cond = f"AND co.category = '{sel_cat_tm}'" if sel_cat_tm != "All Categories" else ""

        df_rate = q(
            f"""
            SELECT cf.region,
                   cf.circle_name,
                   COUNT(DISTINCT cf.customer_id) AS subscribers,
                   COUNT(co.complaint_id)         AS tickets,
                   ROUND(COUNT(co.complaint_id)*100.0
                         /COUNT(DISTINCT cf.customer_id),1) AS rate_per_100
            FROM customer_features cf
            LEFT JOIN complaints co ON cf.customer_id = co.customer_id {tm_join_cond}
            {_where_cf()}
            GROUP BY cf.region, cf.circle_name
            HAVING tickets > 0
            ORDER BY rate_per_100 DESC
            """
        )
        fig_rate = px.treemap(
            df_rate,
            path=[px.Constant("All Circles"), "region", "circle_name"],
            values="tickets",
            color="rate_per_100",
            color_continuous_scale="Reds",
            custom_data=["rate_per_100", "subscribers"],
            height=275,
        )
        fig_rate.update_traces(
            texttemplate="<b>%{label}</b><br>%{customdata[0]:.1f}/100 subs<br>%{value:,} tkts",
            hovertemplate="<b>%{label}</b><br>Rate: %{customdata[0]:.1f} / 100 subs<br>Tickets: %{value:,}<br>Subscribers: %{customdata[1]:,}<extra></extra>",
        )
        c_tag = f" · {sel_cat_tm}" if sel_cat_tm != "All Categories" else ""
        fig_rate.update_layout(
            title=f"Ticket rate & volume by circle — where should capacity increase?{c_tag}",
            margin=dict(t=40, b=10, l=10, r=10),
            coloraxis_colorbar=dict(title="Tkts/100", thickness=12, tickfont=dict(color="#111111"), title_font=dict(color="#111111")),
        )
        r_hdr.markdown("**Treemap — Tickets per 100 Subscribers by Circle**")
        st.plotly_chart(_style_fig(fig_rate), use_container_width=True, key="rate_overview")


# ══════════════════════════════════════════════════════════════
#       DETAIL TAB
# ══════════════════════════════════════════════════════════════
with tab_detail:

    categories = q("SELECT DISTINCT category FROM complaints ORDER BY 1")["category"].tolist()

    # Selector in a narrow column alongside three cards
    sel_col, d1, d2, d3 = st.columns([1.2, 1, 1, 1])
    sel_cat = sel_col.selectbox("Complaint Category", categories, key="detail_cat")

    # ── Detail cards ──────────────────────────────────────────
    df_det = q(
        f"""
        SELECT COUNT(*)           AS total,
               SUM(co.is_resolved)  AS closed,
               SUM(CASE WHEN co.is_resolved=0 THEN 1 ELSE 0 END) AS open_n,
               ROUND(SUM(co.is_resolved)*100.0/COUNT(*),1)        AS closure_pct
        FROM complaints co
        JOIN customer_features cf ON co.customer_id = cf.customer_id
        {_where_cf(f"co.category = '{sel_cat}'")}
        """
    )
    det_total = int(df_det["total"].iloc[0])
    det_closed = int(df_det["closed"].iloc[0])
    det_open = int(df_det["open_n"].iloc[0])
    det_closure = float(df_det["closure_pct"].iloc[0])

    d1.metric(f"'{sel_cat}' Tickets", f"{det_total:,}")
    d1.caption("Filtered ticket count for selected category")
    d2.metric("Closed / Open", f"{det_closed:,} / {det_open:,}")
    d2.caption(f"Closure share: {det_closure}%  (closed ÷ total)")
    d3.metric("Closure Share", f"{det_closure}%")
    d3.caption(f"Denominator: {det_total:,} tickets in '{sel_cat}'")

    st.divider()

    # ── Detail hero: Monthly ticket trend (line chart) ────────
    dh_hdr, dh_flt = st.columns([3.5, 1])
    channels_all = ["All Channels"] + q("SELECT DISTINCT channel FROM complaints ORDER BY 1")["channel"].tolist()
    sel_ch_trend = dh_flt.selectbox("Channel (Trend)", channels_all, key="flt_det_ch_trend", label_visibility="collapsed")
    trend_extra = f"co.category = '{sel_cat}'" + (f" AND co.channel = '{sel_ch_trend}'" if sel_ch_trend != "All Channels" else "")

    df_trend = q(
        f"""
        SELECT strftime('%Y-%m', co.complaint_date) AS month,
               COUNT(*) AS tickets
        FROM complaints co
        JOIN customer_features cf ON co.customer_id = cf.customer_id
        {_where_cf(trend_extra)}
        GROUP BY 1
        ORDER BY 1
        """
    )
    fig_trend = go.Figure(
        go.Scatter(
            x=df_trend["month"],
            y=df_trend["tickets"],
            mode="lines+markers+text",
            text=df_trend["tickets"],
            textposition="top center",
            line=dict(color="#e8192c", width=2),
            marker=dict(size=6),
        )
    )
    ch_tag = f" · {sel_ch_trend}" if sel_ch_trend != "All Channels" else ""
    fig_trend.update_layout(
        title=f"When do '{sel_cat}' tickets peak? — Monthly trend{ch_tag}",
        xaxis_title="Month",
        yaxis_title="Ticket Count",
        height=255,
        margin=dict(t=40, b=25),
        showlegend=False,
    )
    dh_hdr.markdown(f"**Line Chart — Monthly Ticket Trend ({sel_cat})**")
    st.plotly_chart(_style_fig(fig_trend), use_container_width=True, key="trend_detail")

    # ── Detail supporting charts (each with its own filter) ──
    mid_d, right_d = st.columns(2)

    with mid_d:
        md_hdr, md_flt = st.columns([1.4, 1])
        sel_sub_stat = md_flt.selectbox(
            "Subscriber (Box)", ["All Subscribers", "Active", "Churned"], key="flt_det_sub", label_visibility="collapsed"
        )
        box_extra = f"co.category = '{sel_cat}' AND co.is_resolved = 1"
        if sel_sub_stat == "Active":
            box_extra += " AND cf.is_churned = 0"
        elif sel_sub_stat == "Churned":
            box_extra += " AND cf.is_churned = 1"

        df_res_days = q(
            f"""
            SELECT co.resolution_days
            FROM complaints co
            JOIN customer_features cf ON co.customer_id = cf.customer_id
            {_where_cf(box_extra)}
            """
        )
        fig_box = go.Figure(
            go.Box(
                y=df_res_days["resolution_days"],
                name=sel_cat,
                marker_color="#e8192c",
                boxmean=True,
            )
        )
        sub_tag = f" · {sel_sub_stat}" if sel_sub_stat != "All Subscribers" else ""
        fig_box.update_layout(
            title=f"Resolution-day spread{sub_tag}",
            yaxis_title="Resolution Days",
            height=255,
            margin=dict(t=40, b=25),
            showlegend=False,
        )
        md_hdr.markdown("**Box Plot — Resolution-Day Spread**")
        st.plotly_chart(_style_fig(fig_box), use_container_width=True, key="box_detail")

    with right_d:
        rd_hdr, rd_flt = st.columns([1.4, 1])
        sel_tkt_stat = rd_flt.selectbox(
            "Ticket Status (Funnel)", ["All Tickets", "Closed", "Open"], key="flt_det_tkt", label_visibility="collapsed"
        )
        fn_extra = f"co.category = '{sel_cat}'"
        if sel_tkt_stat == "Closed":
            fn_extra += " AND co.is_resolved = 1"
        elif sel_tkt_stat == "Open":
            fn_extra += " AND co.is_resolved = 0"

        df_channel = q(
            f"""
            SELECT co.channel,
                   COUNT(*) AS tickets,
                   SUM(co.is_resolved) AS closed,
                   ROUND(SUM(co.is_resolved)*100.0/COUNT(*),1) AS closure_pct
            FROM complaints co
            JOIN customer_features cf ON co.customer_id = cf.customer_id
            {_where_cf(fn_extra)}
            GROUP BY co.channel
            ORDER BY tickets DESC
            """
        )
        fig_funnel = go.Figure(
            go.Funnel(
                y=df_channel["channel"],
                x=df_channel["tickets"],
                text=[f"{t:,} tkts · {p}% closed" for t, p in zip(df_channel["tickets"], df_channel["closure_pct"])],
                marker_color=["#e8192c", "#fa5252", "#ff8787", "#ffc9c9"],
                textposition="inside",
            )
        )
        tkt_tag = f" · {sel_tkt_stat}" if sel_tkt_stat != "All Tickets" else ""
        fig_funnel.update_layout(
            title=f"'{sel_cat}' volume by channel{tkt_tag}",
            height=255,
            margin=dict(t=40, b=20),
            showlegend=False,
        )
        rd_hdr.markdown("**Funnel Chart — Volume by Channel**")
        st.plotly_chart(_style_fig(fig_funnel), use_container_width=True, key="funnel_detail")
