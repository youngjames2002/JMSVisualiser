import json
import streamlit as st
from data import download_excel_from_sharepoint, upload_file_to_sharepoint

SITE_NAME = "JMSEngineeringTeam"
CONFIG_FILE_PATH = "JMS Engineering Team SharePoint/JMS Master Schedule/visualiserConfig/capacity_config.json"

# Fallback values, used until a site edits and persists its own value,
# or if the SharePoint file can't be reached
DEFAULT_CAPACITIES = {
    "weld_ballymena": 256,
    "weld_kilrea": 288,
    "flat_cutting": 148,
    "tube_cutting": 28,
    "folding": 80,
    "machining": 114,
    "rubber_lining": 60,
    "paint_capacity": 35000,
}

LABELS = {
    "weld_ballymena": "Weld Capacity - Ballymena (hours/week)",
    "weld_kilrea": "Weld Capacity - Kilrea (hours/week)",
    "flat_cutting": "Flat Cutting Capacity (hours/week)",
    "tube_cutting": "Tube Cutting Capacity (hours/week)",
    "folding": "Folding Capacity (hours/week)",
    "machining": "Machining Capacity (hours/week)",
    "rubber_lining": "Rubber Lining Capacity (hours/week)",
    "paint_capacity": "Paint MAX Capacity (£/week)",
}


def load_capacities():
    try:
        bytes_io = download_excel_from_sharepoint(SITE_NAME, CONFIG_FILE_PATH)
        saved = json.loads(bytes_io.read())
    except Exception:
        saved = {}
    return {**DEFAULT_CAPACITIES, **saved}


def save_capacities(capacities):
    try:
        upload_file_to_sharepoint(
            SITE_NAME, CONFIG_FILE_PATH,
            json.dumps(capacities, indent=2).encode("utf-8"),
            content_type="application/json",
        )
        download_excel_from_sharepoint.clear(SITE_NAME, CONFIG_FILE_PATH)
    except Exception:
        st.warning("Could not save capacity change to SharePoint - it won't persist.")


def get_capacity(key):
    return load_capacities().get(key, DEFAULT_CAPACITIES.get(key, 0))


def capacity_input(key, col=None, step=1, min_value=0, width=110):
    """Inline, editable capacity value. Renders a small number_input pre-filled
    with the current value and persists any change to capacity_config.json on SharePoint."""
    target = col if col is not None else st
    capacities = load_capacities()
    current_value = int(capacities.get(key, DEFAULT_CAPACITIES.get(key, 0)))

    new_value = target.number_input(
        LABELS.get(key, key),
        min_value=min_value,
        step=step,
        value=current_value,
        key=f"capacity_input_{key}",
        width=width,
    )

    if new_value != current_value:
        capacities[key] = new_value
        save_capacities(capacities)

    return new_value
