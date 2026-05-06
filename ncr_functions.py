import streamlit as st
import psycopg2
import pandas as pd
import ast
import re
import datetime
import base64
from data import load_so_statii

DISPLAY_COLS = {
    "id":                              "ID",
    "name":                            "Reported By",
    "customer":                        "Customer",
    "customer_ncr_no":                 "Customer NCR No",
    "original_sales_order":            "Original Sales Order",
    "customer_po":                     "Customer PO",
    "description":                     "Description",
    "department":                      "Department",
    "suggested_corrective_action":     "Suggested Corrective Action",
    "corrective_action_delegated_to":  "Delegated To",
    "returned_to_customer":            "Returned to Customer?",
    "corrective_action_completed":     "Corrective Action Completed?",
}


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


def load_ncr_data(conn):
    df = pd.read_sql_query("SELECT * FROM ncr_log ORDER BY id DESC", conn)
    df["department"] = df["department"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.strip() else []
    )
    df["corrective_action_delegated_to"] = df["corrective_action_delegated_to"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.strip() else []
    )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
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
        for sublist in df["corrective_action_delegated_to"]
        for p in sublist
        if p and str(p).strip()
    })
    return names, customers, departments, delegated


def render_date_filter():
    col1, _ = st.columns([1, 4])
    with col1:
        date_filter = st.date_input("Show data from:", value=datetime.datetime(2025, 1, 1))
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
        st.markdown(f'<div class="stat-result"><span>{count} NCRs</span> — {round(count / num_ncrs * 100, 1)}% of total</div>', unsafe_allow_html=True)

    with c2:
        dept_sel = st.selectbox("By Department", options=departments, key="sel_dept")
        count = len(df[df["department"].apply(lambda x: dept_sel in x)])
        st.markdown(f'<div class="stat-result"><span>{count} NCRs</span> — {round(count / num_ncrs * 100, 1)}% of total</div>', unsafe_allow_html=True)

    with c3:
        cause_sel = st.selectbox("By Root Cause", options=df["root_cause"].dropna().unique(), key="sel_cause")
        count = len(df[df["root_cause"] == cause_sel])
        st.markdown(f'<div class="stat-result"><span>{count} NCRs</span> — {round(count / num_ncrs * 100, 1)}% of total</div>', unsafe_allow_html=True)


def render_so_and_weekly(df, date_filter):
    num_ncrs = len(df[df["customer_ncr_no"] != "Internal"])
    if num_ncrs == 0:
        return

    all_so = load_so_statii()
    all_so = all_so.rename(columns={"date_required": "Date Required"})
    all_so["Date Required"] = pd.to_datetime(all_so["Date Required"], format="mixed")

    today          = pd.Timestamp.today().normalize()
    month_ago      = today - pd.Timedelta(days=30)
    six_months_ago = today - pd.Timedelta(days=182)

    so_since  = all_so[all_so["Date Required"] >= date_filter]
    so_pct    = round(num_ncrs / len(so_since) * 100, 1) if len(so_since) else 0

    so_1m     = all_so[all_so["Date Required"] >= month_ago]
    ncr_1m    = df[df["date"] >= month_ago]
    so_pct_1m = round(len(ncr_1m) / len(so_1m) * 100, 1) if len(so_1m) else 0

    show_6m = date_filter <= six_months_ago
    if show_6m:
        so_6m        = all_so[all_so["Date Required"] >= six_months_ago]
        ncr_6m       = df[df["date"] >= six_months_ago]
        so_pct_6m    = round(len(ncr_6m) / len(so_6m) * 100, 1) if len(so_6m) else 0
        ncr_6m_count = int(len(ncr_6m))
        six_month_so_html = f"""
            <div class="info-sub-item">
                <span class="info-sub-label">Last 6 months</span>
                <span class="info-sub-val">{so_pct_6m}%</span>
            </div>"""
        six_month_ncr_html = f"""
            <div class="info-sub-item">
                <span class="info-sub-label">Last 6 months</span>
                <span class="info-sub-val">{ncr_6m_count}</span>
            </div>"""
    else:
        six_month_so_html = six_month_ncr_html = ""

    this_week_start = (today - pd.Timedelta(days=today.weekday())).normalize()
    last_week_start = this_week_start - pd.Timedelta(weeks=1)
    week_df         = df.copy()
    week_df["Week"] = week_df["date"].dt.to_period("W").dt.start_time
    this_week       = int(len(week_df[week_df["Week"] == this_week_start]))
    last_week       = int(len(week_df[week_df["Week"] == last_week_start]))
    delta           = this_week - last_week
    arrow           = "▲" if delta > 0 else "▼" if delta < 0 else "─"
    delta_label     = f"{arrow} {abs(delta)} vs last week ({last_week})"
    ncr_30d         = int(len(df[df["date"] >= month_ago]))

    st.markdown('<div class="section-heading">Activity</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(f"""
    <div class="info-card">
        Sales orders affected
        <span class="info-value">{so_pct}%</span>
        <span class="info-delta">since {date_filter.strftime("%d %b %Y")}</span>
        <div class="info-sub-stats">
            <div class="info-sub-item">
                <span class="info-sub-label">Last 30 days</span>
                <span class="info-sub-val">{so_pct_1m}%</span>
            </div>{six_month_so_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    c2.markdown(f"""
    <div class="info-card">
        NCRs logged this week
        <span class="info-value">{this_week}</span>
        <span class="info-delta">{delta_label}</span>
        <div class="info-sub-stats">
            <div class="info-sub-item">
                <span class="info-sub-label">Last 30 days</span>
                <span class="info-sub-val">{ncr_30d}</span>
            </div>{six_month_ncr_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


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
    if any(len(s) == 0 for s in df["corrective_action_delegated_to"]):
        delegated = ["Unassigned"] + delegated

    fc1, fc2, fc3, fc4 = st.columns(4)
    selected_names       = fc1.multiselect("Reported By",  options=names,        default=names)
    selected_departments = fc2.multiselect("Department",   options=departments,  default=departments)
    selected_delegated   = fc3.multiselect("Delegated To", options=delegated,    default=delegated)
    selected_customers   = fc4.multiselect("Customer",     options=customers,    default=customers)

    mask = (
        (df["name"].isin(selected_names) if selected_names else True)
        & (df["customer"].isin(selected_customers) if selected_customers else True)
        & df["corrective_action_delegated_to"].apply(
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

    display_df = filtered_df[list(DISPLAY_COLS.keys())].rename(columns=DISPLAY_COLS)
    st.caption(f"{len(display_df)} records shown")
    edited_display = st.data_editor(display_df, use_container_width=True, hide_index=True)

    col1, col2, _ = st.columns([1, 1, 5])
    with col1:
        if st.button("💾 Save Changes"):
            reverse_map = {v: k for k, v in DISPLAY_COLS.items()}
            edited_orig = edited_display.rename(columns=reverse_map).set_index("id")
            cur = conn.cursor()
            editable_cols = [c for c in edited_orig.columns if c != "id"]
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
