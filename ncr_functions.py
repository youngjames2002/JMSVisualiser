import streamlit as st
import psycopg2
import pandas as pd
import re
import datetime
import base64
import json
import plotly.graph_objects as go
from data import load_so_statii

DISPLAY_COLS = {
    "id":                          "ID",
    "name":                        "Reported By",
    "customer":                    "Customer",
    "customer_ncr_no":             "Customer NCR No",
    "original_sales_order":        "Original Sales Order",
    "customer_po":                 "Customer PO",
    "date":                        "Date Recorded",
    "description":                 "Description",
    "department":                  "Department",
    "root_cause":                  "Root Cause(s)",
    "corrective_action":           "Corrective Action(s)",
    "delegated_to":                "Delegated To",
    "returned_to_customer":        "Returned to Customer?",
    "corrective_action_completed": "Corrective Action Completed?",
}

# Columns sourced from causal_factors — read-only in the inline editor
CF_DISPLAY_COLS = {"department", "root_cause", "corrective_action", "delegated_to"}


def _format_so(val):
    if pd.isna(val) or not str(val).strip():
        return val
    digits = re.sub(r"[^0-9]", "", str(val))
    return f"SO-{digits.zfill(6)}" if digits else val


def kpi_card(label, value, sub=None, accent=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi-card {accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
    </div>
    """


def get_connection():
    return psycopg2.connect(st.secrets["NCRDB"]["DATABASE_PUBLIC_URL"])




def _split_csv(val):
    if isinstance(val, list):
        return val
    if not isinstance(val, str) or not val.strip():
        return []
    stripped = val.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except (json.JSONDecodeError, ValueError):
            pass
    return [v.strip() for v in stripped.split(",") if v.strip()]


def load_ncr_data(conn):
    df = pd.read_sql_query("SELECT * FROM ncr_log ORDER BY id DESC", conn)

    df = df.drop(columns=[
        "department", "root_cause", "suggested_corrective_action",
        "corrective_action_delegated_to", "corrective_action_due_date",
    ], errors="ignore")

    cf = pd.read_sql_query("SELECT * FROM causal_factors", conn)

    if cf.empty:
        df["department"]        = [[] for _ in range(len(df))]
        df["delegated_to"]      = [[] for _ in range(len(df))]
        df["root_cause_list"]   = [[] for _ in range(len(df))]
        df["root_cause"]        = ""
        df["corrective_action"] = ""
    else:
        cf["department"]   = cf["department"].apply(_split_csv)
        cf["delegated_to"] = cf["delegated_to"].apply(_split_csv)

        def agg(group):
            all_dept = list(dict.fromkeys(d for depts in group["department"] for d in depts))
            all_del  = list(dict.fromkeys(p for ppl   in group["delegated_to"] for p in ppl))
            rc_list  = [r for r in group["root_cause"].dropna() if str(r).strip()]
            ca_list  = [c for c in group["corrective_action"].dropna() if str(c).strip()]
            return pd.Series({
                "_dept":    all_dept,
                "_del":     all_del,
                "_rc_list": rc_list,
                "_rc_str":  ", ".join(rc_list),
                "_ca_str":  " | ".join(ca_list),
            })

        grouped = cf.groupby("ncr_id").apply(agg).reset_index()
        df = df.merge(grouped, left_on="id", right_on="ncr_id", how="left")

        df["department"]        = df["_dept"].apply(lambda x: x if isinstance(x, list) else [])
        df["delegated_to"]      = df["_del"].apply( lambda x: x if isinstance(x, list) else [])
        df["root_cause_list"]   = df["_rc_list"].apply(lambda x: x if isinstance(x, list) else [])
        df["root_cause"]        = df["_rc_str"].fillna("")
        df["corrective_action"] = df["_ca_str"].fillna("")

        df = df.drop(columns=["ncr_id", "_dept", "_del", "_rc_list", "_rc_str", "_ca_str"], errors="ignore")

    df['date'] = pd.to_datetime(df['date'].astype(str), errors='coerce', format='mixed')
    return df


def get_filter_options(df):
    names = sorted([n for n in df["name"].dropna().unique() if str(n).strip()])
    customers = sorted([c for c in df["customer"].dropna().unique() if str(c).strip()])
    departments = sorted({
        d.strip()
        for sublist in df["department"]
        for d in sublist
        if d and str(d).strip()
    })
    delegated = sorted({
        p.strip()
        for sublist in df["delegated_to"]
        for p in sublist
        if p and str(p).strip()
    })
    return names, customers, departments, delegated


def render_date_filter():
    col1, _ = st.columns([1, 4])
    with col1:
        date_filter = st.date_input("Show data from:", value=datetime.datetime(2026, 1, 1))
    return pd.to_datetime(date_filter)


def render_page_header(date_filter):
    logo_b64 = base64.b64encode(open("assets/logo.jpg", "rb").read()).decode()
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex;align-items:center;gap:1rem;">
            <div style="background:#fff;border-radius:8px;padding:6px 10px;display:flex;align-items:center;">
                <img src="data:image/jpeg;base64,{logo_b64}" style="height:48px;object-fit:contain;" />
            </div>
            <div>
                <h1 style="margin:0;">NCR Log Dashboard</h1>
                <p style="margin:0;">Non-Conformance Report tracking — data from {date_filter.strftime("%d %B %Y")} onwards</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_section(df):
    num_ncrs = len(df)
    if num_ncrs == 0:
        st.warning("No NCRs found for the selected date range.")
        return

    counts   = df["customer_ncr_no"].value_counts()
    internal = int(counts.get("Internal", 0))
    external = num_ncrs - internal

    st.markdown('<div class="section-heading">Overview</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_card("Total NCRs Logged", num_ncrs), unsafe_allow_html=True)
    c2.markdown(kpi_card(
        "Internal NCRs", internal,
        sub=f"{round(internal / num_ncrs * 100, 1)}% of total",
        accent="accent-orange"
    ), unsafe_allow_html=True)
    c3.markdown(kpi_card(
        "External NCRs", external,
        sub=f"{round(external / num_ncrs * 100, 1)}% of total",
        accent="accent-green"
    ), unsafe_allow_html=True)


def render_breakdown_section(df, customers, departments):
    num_ncrs = len(df)
    if num_ncrs == 0:
        return

    st.markdown('<div class="section-heading">Breakdown</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        customer_sel = st.selectbox("By Customer", options=customers, key="sel_customer")
        count = len(df[df["customer"] == customer_sel])
        st.markdown(f'<div class="stat-result"><span>{count} NCRs</span> — {round(count / num_ncrs * 100, 1)}% of Total NCRS Logged</div>', unsafe_allow_html=True)

    with c2:
        dept_sel = st.selectbox("By Department", options=departments, key="sel_dept")
        count = len(df[df["department"].apply(lambda x: dept_sel in x)])
        st.markdown(f'<div class="stat-result"><span>{count} NCRs</span> — {round(count / num_ncrs * 100, 1)}% of Total NCRS Logged</div>', unsafe_allow_html=True)

    with c3:
        cause_options = sorted({rc for rcs in df["root_cause_list"] for rc in rcs if rc and str(rc).strip()})
        cause_sel = st.selectbox("By Root Cause", options=cause_options or ["—"], key="sel_cause")
        count = len(df[df["root_cause_list"].apply(lambda x: cause_sel in x)])
        st.markdown(f'<div class="stat-result"><span>{count} NCRs</span> — {round(count / num_ncrs * 100, 1)}% of Total NCRS Logged</div>', unsafe_allow_html=True)


def render_so_and_weekly(df, date_filter):
    external = df[df["customer_ncr_no"] != "Internal"].copy()
    if len(external) == 0:
        return

    all_so = load_so_statii()
    all_so = all_so.rename(columns={"date_required": "Date Required"})
    all_so["Date Required"] = pd.to_datetime(all_so["Date Required"], format="mixed")

    today          = pd.Timestamp.today().normalize()
    month_ago      = today - pd.Timedelta(days=30)
    six_months_ago = today - pd.Timedelta(days=182)

    st.markdown('<div class="section-heading">Activity</div>', unsafe_allow_html=True)

    # Customer filter for the SO% calculation
    ncr_customers = sorted([c for c in external["customer"].dropna().unique() if str(c).strip()])
    filter_col, _ = st.columns([1, 3])
    with filter_col:
        selected_customer = st.selectbox(
            "Filter % SOs affected by customer:",
            options=["All customers"] + ncr_customers,
            key="activity_customer_filter",
        )

    # Identify the customer column in SO data (Statii returns lowercase column names)
    so_customer_col = next((c for c in all_so.columns if c.lower() == "customer"), None)

    is_filtered = selected_customer != "All customers"

    if is_filtered:
        ncr_subset = external[external["customer"] == selected_customer]
        if so_customer_col:
            sel_lower = selected_customer.strip().lower()
            so_names  = all_so[so_customer_col].astype(str).str.strip().str.lower()
            # Bidirectional contains: handles "Bamford Bus" ↔ "Bamford Bus & Coach Ltd"
            so_subset = all_so[so_names.apply(lambda x: sel_lower in x or x in sel_lower)]
        else:
            so_subset = all_so  # fallback: SO data has no customer column
    else:
        ncr_subset = external
        so_subset  = all_so

    # Always compute all-customer totals so filtered view can show comparison
    total_so_since  = all_so[all_so["Date Required"] >= date_filter]
    total_so_pct    = round(len(external) / len(total_so_since) * 100, 1) if len(total_so_since) else 0
    total_so_1m_df  = all_so[all_so["Date Required"] >= month_ago]
    total_ncr_1m    = external[external["date"] >= month_ago]
    total_so_pct_1m = round(len(total_ncr_1m) / len(total_so_1m_df) * 100, 1) if len(total_so_1m_df) else 0

    so_since  = so_subset[so_subset["Date Required"] >= date_filter]
    so_pct    = round(len(ncr_subset) / len(so_since) * 100, 1) if len(so_since) else 0

    so_1m     = so_subset[so_subset["Date Required"] >= month_ago]
    ncr_1m    = ncr_subset[ncr_subset["date"] >= month_ago]
    so_pct_1m = round(len(ncr_1m) / len(so_1m) * 100, 1) if len(so_1m) else 0

    def _pct_color(val, total):
        if val > total:
            return "#d63e2f"
        if val < total:
            return "#2a9e5f"
        return "#112444"

    raw_note      = f'<span style="font-size:12px;color:#7a8baa;margin-left:8px;">({len(ncr_subset)}&thinsp;/&thinsp;{len(so_since)} SOs)</span>'
    raw_note_1m   = f'<span style="font-size:10px;color:#7a8baa;margin-left:4px;">({len(ncr_1m)}&thinsp;/&thinsp;{len(so_1m)})</span>'

    if is_filtered:
        main_color    = _pct_color(so_pct, total_so_pct)
        main_val_html = (
            f'<span class="info-value" style="color:{main_color};">{so_pct}%</span>'
            f'{raw_note}'
            f'<span style="font-size:13px;color:#7a8baa;margin-left:10px;">vs {total_so_pct}% overall</span>'
        )
        sub_color_1m = _pct_color(so_pct_1m, total_so_pct_1m)
        sub_30d_html = (
            f'<span class="info-sub-val" style="color:{sub_color_1m};">{so_pct_1m}%</span>'
            f'{raw_note_1m}'
            f'<span style="font-size:10px;color:#7a8baa;"> / {total_so_pct_1m}% all</span>'
        )
    else:
        main_val_html = f'<span class="info-value">{so_pct}%</span>{raw_note}'
        sub_30d_html  = f'<span class="info-sub-val">{so_pct_1m}%</span>{raw_note_1m}'

    show_6m = date_filter <= six_months_ago
    if show_6m:
        so_6m        = so_subset[so_subset["Date Required"] >= six_months_ago]
        ncr_6m       = ncr_subset[ncr_subset["date"] >= six_months_ago]
        so_pct_6m    = round(len(ncr_6m) / len(so_6m) * 100, 1) if len(so_6m) else 0
        ncr_6m_count = int(len(ncr_6m))

        raw_note_6m = f'<span style="font-size:10px;color:#7a8baa;margin-left:4px;">({len(ncr_6m)}&thinsp;/&thinsp;{len(so_6m)})</span>'

        if is_filtered:
            total_so_6m     = all_so[all_so["Date Required"] >= six_months_ago]
            total_ncr_6m    = external[external["date"] >= six_months_ago]
            total_so_pct_6m = round(len(total_ncr_6m) / len(total_so_6m) * 100, 1) if len(total_so_6m) else 0
            sub_color_6m    = _pct_color(so_pct_6m, total_so_pct_6m)
            six_month_so_val = (
                f'<span class="info-sub-val" style="color:{sub_color_6m};">{so_pct_6m}%</span>'
                f'{raw_note_6m}'
                f'<span style="font-size:10px;color:#7a8baa;"> / {total_so_pct_6m}% all</span>'
            )
        else:
            six_month_so_val = f'<span class="info-sub-val">{so_pct_6m}%</span>{raw_note_6m}'

        six_month_so_html = f"""
            <div class="info-sub-item">
                <span class="info-sub-label">Last 6 months</span>
                {six_month_so_val}
            </div>"""
        six_month_ncr_html = f"""
            <div class="info-sub-item">
                <span class="info-sub-label">Last 6 months</span>
                <span class="info-sub-val">{ncr_6m_count}</span>
            </div>"""
    else:
        six_month_so_html = six_month_ncr_html = ""

    week_source     = df[df["customer"] == selected_customer] if is_filtered else df
    this_week_start = (today - pd.Timedelta(days=today.weekday())).normalize()
    last_week_start = this_week_start - pd.Timedelta(weeks=1)
    week_df         = week_source.copy()
    week_df["Week"] = week_df["date"].dt.to_period("W").dt.start_time
    this_week_df    = week_df[week_df["Week"] == this_week_start]
    last_week_df    = week_df[week_df["Week"] == last_week_start]
    this_week       = int(len(this_week_df))
    this_week_int   = int((this_week_df["customer_ncr_no"] == "Internal").sum())
    this_week_ext   = this_week - this_week_int
    last_week       = int(len(last_week_df))
    last_week_int   = int((last_week_df["customer_ncr_no"] == "Internal").sum())
    last_week_ext   = last_week - last_week_int
    df_30d          = week_source[week_source["date"] >= month_ago]
    ncr_30d         = int(len(df_30d))
    ncr_30d_int     = int((df_30d["customer_ncr_no"] == "Internal").sum())
    ncr_30d_ext     = ncr_30d - ncr_30d_int

    def _delta_label(curr, prev):
        d = curr - prev
        arrow = "▲" if d > 0 else "▼" if d < 0 else "─"
        return f"{arrow} {abs(d)} vs {prev} last wk"

    card_label = f"Sales orders affected ({selected_customer})" if is_filtered else "Sales orders affected"

    c1, c2 = st.columns(2)
    c1.markdown(f"""
    <div class="info-card">
        {card_label}
        {main_val_html}
        <span class="info-delta">since {date_filter.strftime("%d %b %Y")}</span>
        <div class="info-sub-stats">
            <div class="info-sub-item">
                <span class="info-sub-label">Last 30 days</span>
                {sub_30d_html}
            </div>{six_month_so_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    week_card_label = f"NCRs logged this week ({selected_customer})" if is_filtered else "NCRs logged this week"
    c2.markdown(f"""
    <div class="info-card">
        {week_card_label}
        <div style="display:flex;gap:20px;margin-top:4px;">
            <div style="flex:1;">
                <span style="font-size:11px;font-weight:700;color:#7a8baa;text-transform:uppercase;letter-spacing:0.5px;">Total</span>
                <span class="info-value">{this_week}</span>
                <span class="info-delta">{_delta_label(this_week, last_week)}</span>
            </div>
            <div style="flex:1;">
                <span style="font-size:11px;font-weight:700;color:#7a8baa;text-transform:uppercase;letter-spacing:0.5px;">Internal</span>
                <span class="info-value">{this_week_int}</span>
                <span class="info-delta">{_delta_label(this_week_int, last_week_int)}</span>
            </div>
            <div style="flex:1;">
                <span style="font-size:11px;font-weight:700;color:#7a8baa;text-transform:uppercase;letter-spacing:0.5px;">External</span>
                <span class="info-value">{this_week_ext}</span>
                <span class="info-delta">{_delta_label(this_week_ext, last_week_ext)}</span>
            </div>
        </div>
        <div class="info-sub-stats">
            <div class="info-sub-item">
                <span class="info-sub-label">Last 30 days (total)</span>
                <span class="info-sub-val">{ncr_30d}</span>
            </div>
            <div class="info-sub-item">
                <span class="info-sub-label">Internal</span>
                <span class="info-sub-val">{ncr_30d_int}</span>
            </div>
            <div class="info-sub-item">
                <span class="info-sub-label">External</span>
                <span class="info-sub-val">{ncr_30d_ext}</span>
            </div>{six_month_ncr_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    ncr_graph(df, all_so)

def ncr_graph(df, all_so=None):
    st.markdown('<div class="section-heading">Trends</div>', unsafe_allow_html=True)
    dated = df.dropna(subset=["date"]).copy()
    dated["week"] = dated["date"].dt.to_period("W").dt.start_time
    dated["type"] = dated["customer_ncr_no"].apply(lambda x: "Internal" if x == "Internal" else "External")

    weekly_split = dated.groupby(["week", "type"]).size().unstack(fill_value=0).reset_index()
    for col in ("Internal", "External"):
        if col not in weekly_split.columns:
            weekly_split[col] = 0
    weekly_split = weekly_split.sort_values("week").reset_index(drop=True)
    weekly_split["total"] = weekly_split["Internal"] + weekly_split["External"]
    weekly_split["rolling"] = weekly_split["total"].rolling(4, min_periods=1).mean().round(1)

    fig_weekly = go.Figure()
    fig_weekly.add_trace(go.Bar(
        x=weekly_split["week"], y=weekly_split["External"],
        name="External", marker_color="rgba(224,92,42,0.5)",
        hovertemplate="%{x|%d %b %Y} — External: %{y}<extra></extra>",
    ))
    fig_weekly.add_trace(go.Bar(
        x=weekly_split["week"], y=weekly_split["Internal"],
        name="Internal",
        marker=dict(
            color="rgba(224,92,42,0.25)",
            pattern=dict(shape="/", fgcolor="rgba(224,92,42,0.8)", size=6),
        ),
        hovertemplate="%{x|%d %b %Y} — Internal: %{y}<extra></extra>",
    ))
    fig_weekly.add_trace(go.Scatter(
        x=weekly_split["week"], y=weekly_split["rolling"],
        name="4-wk avg (total)", mode="lines+markers",
        line=dict(color="#e05c2a", width=2),
        hovertemplate="%{x|%d %b %Y}: %{y}<extra></extra>",
    ))
    fig_weekly.update_layout(
        title="NCRs Recorded (4-week rolling avg)",
        xaxis_title="Week", yaxis_title="NCRs Recorded",
        barmode="stack",
        margin=dict(t=40, b=20, l=20, r=20),
        legend=dict(orientation="h", y=-0.2),
        bargap=0.2,
    )

    if all_so is not None:
        external = dated[dated["customer_ncr_no"] != "Internal"].copy()
        external["week"] = external["date"].dt.to_period("W").dt.start_time
        ncr_weekly = external.groupby("week").size().reset_index(name="ncr_count")

        so = all_so.copy()
        so["week"] = so["Date Required"].dt.to_period("W").dt.start_time
        so_weekly = so.groupby("week").size().reset_index(name="so_count")

        merged = pd.merge(ncr_weekly, so_weekly, on="week", how="right")
        merged["ncr_count"] = merged["ncr_count"].fillna(0)
        merged = merged.sort_values("week").reset_index(drop=True)

        this_week_start = (pd.Timestamp.today().normalize() - pd.Timedelta(days=pd.Timestamp.today().weekday()))
        merged = merged[merged["week"] <= this_week_start].reset_index(drop=True)

        nonzero = merged.index[merged["ncr_count"] > 0]
        if len(nonzero):
            merged = merged.iloc[nonzero[0]:].reset_index(drop=True)

        merged["pct"] = (merged["ncr_count"] / merged["so_count"] * 100).round(1)
        merged["pct_rolling"] = merged["pct"].rolling(4, min_periods=1).mean().round(1)

        fig_pct = go.Figure()
        fig_pct.add_trace(go.Bar(
            x=merged["week"], y=merged["pct"],
            name="% (weekly)", marker_color="rgba(42,122,224,0.25)",
            hovertemplate="%{x|%d %b %Y}: %{y}%<extra></extra>",
        ))
        fig_pct.add_trace(go.Scatter(
            x=merged["week"], y=merged["pct_rolling"],
            name="4-wk avg", mode="lines+markers",
            line=dict(color="#2a7ae0", width=2),
            hovertemplate="%{x|%d %b %Y}: %{y}%<extra></extra>",
        ))
        fig_pct.add_hline(y=2, line=dict(color="red", width=2, dash="dash"), annotation_text="2% target", annotation_position="top right")
        fig_pct.update_layout(
            title="% Sales Orders Affected (4-week rolling avg)",
            xaxis_title="Week", yaxis_title="% SOs Affected",
            margin=dict(t=40, b=20, l=20, r=20),
            legend=dict(orientation="h", y=-0.2),
            bargap=0.2,
        )

        c1, c2 = st.columns(2)
        c2.plotly_chart(fig_weekly, use_container_width=True)
        c1.plotly_chart(fig_pct, use_container_width=True)

        # with st.expander("Debug: % SOs affected — raw data per week", expanded=False):
        #     st.markdown("**Weekly summary** (ncr_count, so_count, raw %, rolling avg)")
        #     st.dataframe(
        #         merged[["week", "ncr_count", "so_count", "pct", "pct_rolling"]].rename(columns={
        #             "week": "Week", "ncr_count": "NCRs", "so_count": "SOs",
        #             "pct": "% (raw)", "pct_rolling": "% (4wk avg)",
        #         }),
        #         use_container_width=True,
        #     )
        #     ncr_detail_cols = [c for c in ["id", "date", "week", "customer", "original_sales_order", "description"] if c in external.columns]
        #     st.markdown("**NCRs per week** (external only)")
        #     st.dataframe(external[ncr_detail_cols].sort_values("week").reset_index(drop=True), use_container_width=True)
        #     st.markdown("**SOs per week** (Date Required, trimmed to same range)")
        #     so_trimmed = so[(so["week"] >= merged["week"].min()) & (so["week"] <= merged["week"].max())]
        #     st.dataframe(so_trimmed.sort_values("week").reset_index(drop=True), use_container_width=True)
    else:
        st.plotly_chart(fig_weekly, use_container_width=True)



def render_completion_stats(df):
    total = len(df)
    if total == 0:
        return

    st.markdown('<div class="section-heading">Completion Status</div>', unsafe_allow_html=True)

    sca_done = int((df["corrective_action_completed"] == "Yes").sum())
    sca_pct  = round(sca_done / total, 2)
    st.progress(sca_pct, f"Corrective action completed: {sca_done} of {total} ({int(sca_pct * 100)}%)")

    rtc_done = int((df["returned_to_customer"] == "Yes").sum())
    rtc_pct  = round(rtc_done / total, 2)
    st.progress(rtc_pct, f"Returned to customer: {rtc_done} of {total} ({int(rtc_pct * 100)}%)")


def render_ncr_table(df, conn, names, customers, departments, delegated):
    st.markdown('<div class="section-heading">Full NCR Log</div>', unsafe_allow_html=True)
    st.caption("Click any cell to edit inline, then press Save Changes to write to the database.")

    if any(len(s) == 0 for s in df["department"]):
        departments = ["Unassigned"] + departments
    if any(len(s) == 0 for s in df["delegated_to"]):
        delegated = ["Unassigned"] + delegated

    fc1, fc2, fc3, fc4 = st.columns(4)
    selected_names       = fc1.multiselect("Reported By",  options=names,       default=names)
    selected_departments = fc2.multiselect("Department",   options=departments, default=departments)
    selected_delegated   = fc3.multiselect("Delegated To", options=delegated,   default=delegated)
    selected_customers   = fc4.multiselect("Customer",     options=customers,   default=customers)

    mask = (
        (df["name"].isin(selected_names) if selected_names else True)
        & (df["customer"].isin(selected_customers) if selected_customers else True)
        & df["delegated_to"].apply(
            lambda people: (
                not selected_delegated
                or ("Unassigned" in selected_delegated and not people)
                or any(p in selected_delegated for p in people)
            )
        )
        & df["department"].apply(
            lambda depts: (
                not selected_departments
                or ("Unassigned" in selected_departments and not depts)
                or any(d in selected_departments for d in depts)
            )
        )
    )

    filtered_df = df[mask].copy()
    filtered_df["original_sales_order"] = filtered_df["original_sales_order"].apply(_format_so)

    # Flatten list columns to comma-joined strings for display
    for col in ("department", "delegated_to"):
        filtered_df[col] = filtered_df[col].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else (x or "")
        )

    display_cols_present = [c for c in DISPLAY_COLS if c in filtered_df.columns]
    display_df = filtered_df[display_cols_present].rename(columns=DISPLAY_COLS)
    st.caption(f"{len(display_df)} records shown")

    cf_display_renamed = {DISPLAY_COLS[c] for c in CF_DISPLAY_COLS if c in DISPLAY_COLS}
    column_config = {col: st.column_config.TextColumn(disabled=True) for col in cf_display_renamed}
    edited_display = st.data_editor(display_df, use_container_width=True, hide_index=True, column_config=column_config)

    col1, col2, _ = st.columns([1, 1, 5])
    with col1:
        if st.button("💾 Save Changes"):
            reverse_map = {v: k for k, v in DISPLAY_COLS.items()}
            edited_orig = edited_display.rename(columns=reverse_map).set_index("id")
            cur = conn.cursor()
            editable_cols = [c for c in edited_orig.columns if c != "id" and c not in CF_DISPLAY_COLS]
            for row_id, row in edited_orig.iterrows():
                for col in editable_cols:
                    val = row[col]
                    if isinstance(val, list):
                        val = str(val)
                    cur.execute(
                        f'UPDATE ncr_log SET "{col}" = %s WHERE id = %s',
                        (val, row_id),
                    )
            conn.commit()
            st.success("Database updated successfully.")
    with col2:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()
