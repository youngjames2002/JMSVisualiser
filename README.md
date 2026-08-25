# JMS Data Visualiser

An internal dashboard for the JMS Metaltec management team, providing visual insight into
capacity planning, workshop scheduling, order value and quality (NCR) data across the
Kilrea and Ballymena sites.

Built with Python, Streamlit, Pandas and Plotly. Data is pulled live from the
**Statii ERP API**, **SharePoint** (via Microsoft Graph), **Microsoft Planner** and a
**PostgreSQL** NCR database.

## Access

The dashboard is hosted at [jmsvisualiser.streamlit.app](https://jmsvisualiser.streamlit.app/)

Login is via Microsoft Entra ID (JMS work account) — the app uses Streamlit's native
OpenID Connect auth, so there is no separate app password. To request access, or a version
pre-loaded with demo data, email james@jmsmetaltec.com

## Pages

| Page | What it shows | Source |
|---|---|---|
| Flat Cutting | Weekly laser flat-cutting load vs capacity, KPIs, job table | Bundle staging sheet *or* Statii (toggle) |
| Tube Cutting | Weekly laser tube-cutting load vs capacity, KPIs, job table | Bundle staging sheet *or* Statii (toggle) |
| Folding | Brake press load split by site (Kilrea / Ballymena / both) | Bundle staging sheet *or* Statii (toggle) |
| Saw Schedule | Weekly saw load, late / this week / next week KPIs | SharePoint Teams tool |
| Machining Schedule | Load by operation (CNC milling, turning, csking/drilling, manual turning, after-weld), site filter | SharePoint Teams tool + Planner labels |
| Weld Schedule | Weld load by site, including outsourced work, vs per-site capacity | SharePoint Teams tool |
| Kilrea Paint Capacity | Paint value (£) per week or day vs capacity, next-available-week calculator | Statii |
| Galv Capacity | Galvanising value (£) by week | Statii |
| Ballymena Finishing Capacity | Wrightbus/Bamford finishing value by week + finish-type breakdown | Statii |
| Rubber Lining | Weekly rubber lining load vs capacity | SharePoint Teams tool |
| Total Order Value By Month | Expected vs actual delivered order value by month, and the difference | Statii |
| NCR Log | Non-conformance KPIs, breakdowns by customer/department, editable NCR table | PostgreSQL |

Common behaviour across the schedule pages:

- **Overdue roll-up** — jobs from past weeks are stacked as a hatched "overdue" segment on
  the current week's bar rather than being hidden.
- **Capacity lines** — MAX and 75% capacity lines, with bars recoloured amber/red as they
  cross those thresholds.
- **Editable capacities** — capacity values are `number_input`s on the page. Changes are
  written to `capacity_config.json` on SharePoint, so they persist across restarts and
  redeploys for all users.
- **Refresh Data** — clears the Streamlit data cache and re-pulls every source.
- **Completed-job filtering** — jobs marked complete in Statii are removed from the
  SharePoint-sourced schedules (`remove_completed_jobs_statii`).

## Project layout

```
login.py                  Entry point — Microsoft login, and require_auth() used by pages
pages/                    One file per dashboard page (Streamlit multipage app)
data.py                   All data access: Statii API, SharePoint/Graph, Planner, plus cleaning
metrics.py                Pure data shaping: KPI builders, chart data builders, table filters
ui_components.py          Streamlit/Plotly rendering: page_setup(), KPI cards, bar charts, tables
capacity_config.py        Capacity defaults, labels, and load/save to SharePoint
ncr_functions.py          Everything for the NCR Log page (PostgreSQL queries + rendering)
weld_site_overrides.json  Manual S.O. → site ("Kilrea"/"Ballymena"/"Outsourced") overrides for welding
stylesheet.css            Shared card/layout styles
assets/logo.jpg           Header logo
```

Every page starts with `page_setup("Page Title")`, which applies the auth check, page
config, CSS and header row.

### Site logic

Site is derived rather than stored, and differs per resource:

- **Weld / saw / rubber lining** — Bamford (Wrightbus) → Ballymena, everything else →
  Kilrea; jobs whose Customer P.O. mentions "Link Arms" are forced to Kilrea; individual
  sales orders can be overridden in `weld_site_overrides.json` (also used to flag
  outsourced welding).
- **Machining** — taken from the Microsoft Planner board labels (`category19` = Kilrea,
  `category23` = Ballymena), joined on S.O. No. + Operation. Unlabelled jobs show as
  "No Site Assigned".
- **Flat cutting** — REGIUS machine → Ballymena, otherwise Kilrea.

## Running locally

**Requirements:** Python 3.11 or later

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure credentials — create a `.streamlit/secrets.toml` file (fill in the blanks for
   your own tenant/app registration):
```toml
# Set to true to bypass Microsoft login when developing locally.
# Deployed secrets omit this, so auth always runs in production.
TEST_MODE = true

# Streamlit native OIDC login (used by st.login in login.py)
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = ""

[auth.microsoft]
client_id = ""
client_secret = ""
server_metadata_url = "https://login.microsoftonline.com/<TENANT_ID>/v2.0/.well-known/openid-configuration"

# App registration used for Graph (SharePoint files + Planner), client-credentials flow
[sharepoint]
CLIENT_ID = ""
TENANT_ID = ""
CLIENT_SECRET = ""
SHAREPOINT_SITE = "jmsengineering.sharepoint.com"

# Statii ERP REST API
[statii]
BASE_URL = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

# PostgreSQL database behind the NCR Log page
[NCRDB]
DATABASE_PUBLIC_URL = ""
```

3. Run the app:
```bash
python -m streamlit run login.py
```

## Screenshots
<img width="754" height="449" alt="image" src="https://github.com/user-attachments/assets/1870d058-3b2d-4233-af57-8ba8a56a2a2d" />
<img width="855" height="383" alt="image" src="https://github.com/user-attachments/assets/5c81a03c-4876-40dc-8b21-16662aeb833b" />
<img width="752" height="241" alt="image" src="https://github.com/user-attachments/assets/90cb5390-f536-4d1b-9807-e6c14d5a23f1" />

## Roadmap

- Integrate directly with the Statii ERP API to replace manual Excel exports
