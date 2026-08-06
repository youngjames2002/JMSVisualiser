# JMS Data Visualiser

An internal dashboard for the JMS Metaltec management team, providing visual insights 
into capacity planning, order processing, and other key operational metrics.

Built with Python, Streamlit, Pandas, Plotly Express, and openpyxl.

## Access

The dashboard is hosted at [jmsvisualiser.streamlit.app](https://jmsvisualiser.streamlit.app/)

It is password protected. To request access, or a version pre-loaded with demo data, 
email james@jmsmetaltec.com

## Running Locally

**Requirements:** Python 3.9 or later

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure credentials — create a `.streamlit/secrets.toml` file (replace blank values with appropriate ones for your use):
```toml
[sharepoint]
CLIENT_ID = ""
TENANT_ID = ""
CLIENT_SECRET = ""
SHAREPOINT_SITE = "jmsengineering.sharepoint.com"

[credentials.usernames.jms]
password = ""
roles = ["default"]

[cookie]
name = "jms_data_visualiser"
key = ""
expiry_days = 5

```

3. Run the app:
```bash
python -m streamlit run login.py
```
