# app.py — TR Land Tool
# Tribal Land Reclamation Officer Tool
# Valid Python — NO Jupyter magic commands

import streamlit as st
import pandas as pd
import json
import math
import io
import datetime
import traceback

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TR Land Tool 🌿",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Optional heavy imports — handled gracefully if not installed
# ---------------------------------------------------------------------------
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon, shape
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

# ---------------------------------------------------------------------------
# App version
# ---------------------------------------------------------------------------
APP_VERSION = "1.0.0"
LAST_UPDATED = "2025-02-25"

# ---------------------------------------------------------------------------
# Sample / demo data
# ---------------------------------------------------------------------------
SAMPLE_TRIBAL_BOUNDARY = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Sample Tribal Territory"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-101.5, 43.2], [-100.5, 43.2],
                    [-100.5, 43.8], [-101.5, 43.8],
                    [-101.5, 43.2],
                ]],
            },
        }
    ],
}

SAMPLE_PARCELS = [
    {"Parcel ID": "P-001", "Name": "Elm Creek Meadow",    "Acreage": 320.0,  "Owner of Record": "State of SD",        "Tribal Claim Status": "Reclaimed",   "Land Use": "Grazing",        "Priority Level": "High",   "Notes": "Transfer complete 2023"},
    {"Parcel ID": "P-002", "Name": "Badlands Flats",      "Acreage": 580.0,  "Owner of Record": "Private — J. Smith", "Tribal Claim Status": "Disputed",    "Land Use": "Uncultivated",   "Priority Level": "High",   "Notes": "Litigation pending"},
    {"Parcel ID": "P-003", "Name": "Cedar Ridge",         "Acreage": 210.5,  "Owner of Record": "BIA",                "Tribal Claim Status": "In Progress", "Land Use": "Timber",         "Priority Level": "Medium", "Notes": "Fee-to-trust application filed"},
    {"Parcel ID": "P-004", "Name": "River Bend South",    "Acreage": 145.0,  "Owner of Record": "Private — R. Jones", "Tribal Claim Status": "Unreturned",  "Land Use": "Agriculture",    "Priority Level": "Low",    "Notes": "Initial contact made"},
    {"Parcel ID": "P-005", "Name": "Eagle Rock Forest",   "Acreage": 790.0,  "Owner of Record": "USFS",               "Tribal Claim Status": "In Progress", "Land Use": "Conservation",   "Priority Level": "High",   "Notes": "Co-management negotiations"},
    {"Parcel ID": "P-006", "Name": "Sunrise Prairie",     "Acreage": 430.0,  "Owner of Record": "Private — T. Brown", "Tribal Claim Status": "Reclaimed",   "Land Use": "Grazing",        "Priority Level": "Medium", "Notes": "Allotment restored 2022"},
    {"Parcel ID": "P-007", "Name": "Medicine Creek Bend", "Acreage": 95.0,   "Owner of Record": "County",             "Tribal Claim Status": "Disputed",    "Land Use": "Riparian",       "Priority Level": "High",   "Notes": "Sacred water source"},
    {"Parcel ID": "P-008", "Name": "Buffalo Plateau",     "Acreage": 1250.0, "Owner of Record": "State of SD",        "Tribal Claim Status": "Unreturned",  "Land Use": "Rangeland",      "Priority Level": "Medium", "Notes": "Treaty land — 1868"},
]

SAMPLE_CULTURAL_SITES = [
    {"name": "Spirit Mound",       "lat": 43.40, "lon": -101.10, "type": "Sacred Site",    "notes": "Annual ceremony location"},
    {"name": "Old Village Site",   "lat": 43.55, "lon": -100.80, "type": "Archaeological", "notes": "Pre-1800s settlement"},
    {"name": "Healing Waters",     "lat": 43.30, "lon": -101.30, "type": "Sacred Site",    "notes": "Medicinal spring"},
    {"name": "Grandfather Stones", "lat": 43.65, "lon": -101.00, "type": "Ceremonial",     "notes": "Vision quest site"},
]

SAMPLE_FIELD_NOTES = [
    {"Timestamp": "2025-01-10 09:15", "Officer": "Mary Runs Fast",    "Parcel ID": "P-002", "Note": "Walked fence line — encroachment on east side confirmed.",            "Lat": 43.50, "Lon": -101.00, "Photos": 0},
    {"Timestamp": "2025-01-22 14:30", "Officer": "James Two Bears",   "Parcel ID": "P-005", "Note": "Met with USFS ranger re: co-management MOU draft.",                   "Lat": 43.62, "Lon": -100.75, "Photos": 2},
    {"Timestamp": "2025-02-05 11:00", "Officer": "Sarah Whitehorse",  "Parcel ID": "P-003", "Note": "BIA trust application package submitted — awaiting acknowledgment.",  "Lat": 43.45, "Lon": -101.20, "Photos": 1},
    {"Timestamp": "2025-02-14 16:45", "Officer": "Mary Runs Fast",    "Parcel ID": "P-007", "Note": "Water quality samples taken from Medicine Creek.",                    "Lat": 43.48, "Lon": -100.95, "Photos": 3},
    {"Timestamp": "2025-02-20 08:00", "Officer": "James Two Bears",   "Parcel ID": "P-001", "Note": "Fencing installation complete on reclaimed parcel.",                  "Lat": 43.35, "Lon": -101.40, "Photos": 2},
]

SAMPLE_DOCUMENTS = [
    {"Filename": "P002_Litigation_Brief.pdf",   "Parcel ID": "P-002", "Upload Date": "2025-01-15", "Type": "Legal",         "Notes": "Initial complaint filing"},
    {"Filename": "P003_BIA_Application.pdf",    "Parcel ID": "P-003", "Upload Date": "2025-01-30", "Type": "Application",   "Notes": "Fee-to-Trust packet"},
    {"Filename": "P005_USFS_MOU_Draft.docx",   "Parcel ID": "P-005", "Upload Date": "2025-02-07", "Type": "Agreement",     "Notes": "Draft co-management MOU"},
    {"Filename": "P007_WaterQuality_Lab.pdf",   "Parcel ID": "P-007", "Upload Date": "2025-02-21", "Type": "Environmental", "Notes": "Lab results Q1 2025"},
]

SAMPLE_PROGRESS = [
    {"Month": "Jan 2024", "Parcels Reclaimed": 3,  "Acreage Reclaimed": 850},
    {"Month": "Feb 2024", "Parcels Reclaimed": 3,  "Acreage Reclaimed": 850},
    {"Month": "Mar 2024", "Parcels Reclaimed": 4,  "Acreage Reclaimed": 1100},
    {"Month": "Apr 2024", "Parcels Reclaimed": 4,  "Acreage Reclaimed": 1100},
    {"Month": "May 2024", "Parcels Reclaimed": 5,  "Acreage Reclaimed": 1430},
    {"Month": "Jun 2024", "Parcels Reclaimed": 5,  "Acreage Reclaimed": 1430},
    {"Month": "Jul 2024", "Parcels Reclaimed": 6,  "Acreage Reclaimed": 1750},
    {"Month": "Aug 2024", "Parcels Reclaimed": 6,  "Acreage Reclaimed": 1750},
    {"Month": "Sep 2024", "Parcels Reclaimed": 7,  "Acreage Reclaimed": 2050},
    {"Month": "Oct 2024", "Parcels Reclaimed": 7,  "Acreage Reclaimed": 2050},
    {"Month": "Nov 2024", "Parcels Reclaimed": 8,  "Acreage Reclaimed": 2300},
    {"Month": "Dec 2024", "Parcels Reclaimed": 10, "Acreage Reclaimed": 2750},
]

GLOSSARY = {
    "Allotment": "A parcel of tribal land assigned to an individual tribal member under the Dawes Act (1887); many allotments were later lost due to sale or heirship fractionation.",
    "Fee-to-Trust": "The process by which the federal government acquires land in trust for a tribe, removing it from state/local jurisdiction and returning it to Indian Country status.",
    "Indian Country": "A legal term defined in 18 U.S.C. § 1151 encompassing all land within a reservation, dependent Indian communities, and individual Indian allotments.",
    "Treaty Land": "Lands explicitly reserved for tribal use under treaties between tribes and the U.S. government.",
    "Riparian Rights": "Rights relating to use of water bodies adjacent to or flowing through parcels of land.",
    "Co-Management": "Shared governance arrangement between a tribe and a federal/state agency over a natural resource area.",
    "MOU": "Memorandum of Understanding — a non-binding agreement outlining cooperative intentions between parties.",
    "BIA": "Bureau of Indian Affairs — federal agency within the Dept. of the Interior responsible for administering Indian law and policy.",
    "USFS": "United States Forest Service — manages national forests, some of which overlap with historic tribal territories.",
    "Fractionation": "The progressive division of allotted lands among heirs, creating extremely small undivided ownership interests.",
}

STATUS_COLORS = {
    "Reclaimed":   "#2E7D32",  # green
    "In Progress": "#F57F17",  # amber
    "Disputed":    "#C62828",  # red
    "Unreturned":  "#546E7A",  # blue-grey
}

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
def init_session_state():
    """Initialise all session state keys with default sample data."""
    if "parcels" not in st.session_state:
        st.session_state.parcels = pd.DataFrame(SAMPLE_PARCELS)
    if "field_notes" not in st.session_state:
        st.session_state.field_notes = pd.DataFrame(SAMPLE_FIELD_NOTES)
    if "documents" not in st.session_state:
        st.session_state.documents = pd.DataFrame(SAMPLE_DOCUMENTS)
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = [
            {"Timestamp": "2025-01-10 09:00", "Action": "App initialized",           "User": "System",          "Detail": "Session started"},
            {"Timestamp": "2025-01-10 09:02", "Action": "Parcel P-002 updated",      "User": "Mary Runs Fast",   "Detail": "Status changed to Disputed"},
            {"Timestamp": "2025-01-22 14:35", "Action": "Document uploaded",         "User": "James Two Bears",  "Detail": "P005_USFS_MOU_Draft.docx added"},
            {"Timestamp": "2025-02-05 11:05", "Action": "Parcel P-003 updated",      "User": "Sarah Whitehorse", "Detail": "BIA application number recorded"},
        ]
    if "map_layers" not in st.session_state:
        st.session_state.map_layers = {
            "tribal_boundary": True,
            "parcels": True,
            "cultural_sites": True,
            "historic_boundary": True,
        }

init_session_state()

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def add_audit_entry(action: str, user: str, detail: str):
    """Append an entry to the in-session audit log."""
    entry = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Action": action,
        "User": user,
        "Detail": detail,
    }
    st.session_state.audit_log.append(entry)


def haversine_miles(lat1, lon1, lat2, lon2):
    """Return great-circle distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.markdown("# 🌿 TR Land Tool")
st.sidebar.markdown(f"**v{APP_VERSION}**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    [
        "🗺️ Interactive Land Map",
        "📋 Parcel Registry",
        "🔍 Geospatial Analysis",
        "📁 Document Vault",
        "📊 Dashboard & Reporting",
        "📝 Field Notes & Audit Log",
        "ℹ️ Help & Resources",
    ],
)

# Layer toggles (shown for map page but kept persistent)
if page == "🗺️ Interactive Land Map":
    st.sidebar.markdown("### Map Layers")
    st.session_state.map_layers["tribal_boundary"] = st.sidebar.checkbox(
        "Tribal Boundary", value=st.session_state.map_layers["tribal_boundary"]
    )
    st.session_state.map_layers["parcels"] = st.sidebar.checkbox(
        "Land Parcels", value=st.session_state.map_layers["parcels"]
    )
    st.session_state.map_layers["cultural_sites"] = st.sidebar.checkbox(
        "Cultural / Sacred Sites", value=st.session_state.map_layers["cultural_sites"]
    )
    st.session_state.map_layers["historic_boundary"] = st.sidebar.checkbox(
        "Historic Boundary", value=st.session_state.map_layers["historic_boundary"]
    )
    map_tile = st.sidebar.selectbox(
        "Map Style",
        ["OpenStreetMap", "CartoDB Positron", "Esri WorldImagery", "Stamen Terrain"],
    )

st.sidebar.markdown("---")
st.sidebar.markdown("<small>Powered by SRMCNO</small>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Parcel lat/lon lookup (approximate centres for the sample data)
# ---------------------------------------------------------------------------
PARCEL_COORDS = {
    "P-001": (43.35, -101.40),
    "P-002": (43.50, -101.00),
    "P-003": (43.45, -101.20),
    "P-004": (43.38, -100.90),
    "P-005": (43.62, -100.75),
    "P-006": (43.55, -101.35),
    "P-007": (43.48, -100.95),
    "P-008": (43.70, -101.15),
}

# ===========================================================================
# PAGE 1 — Interactive Land Map
# ===========================================================================
if page == "🗺️ Interactive Land Map":
    st.title("🗺️ Interactive Land Map")
    st.markdown("Explore tribal land parcels, cultural sites, and boundaries.")

    if not FOLIUM_AVAILABLE:
        st.error("Folium / streamlit-folium not installed. Run: `pip install folium streamlit-folium`")
    else:
        try:
            # Tile URL mapping
            tile_map = {
                "OpenStreetMap":    ("OpenStreetMap", None),
                "CartoDB Positron": ("CartoDB positron", None),
                "Esri WorldImagery": (
                    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    "Esri WorldImagery &copy; Esri",
                ),
                "Stamen Terrain": (
                    "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
                    "Map tiles by Stamen Design, under CC BY 3.0.",
                ),
            }
            tile_url, tile_attr = tile_map[map_tile]

            if tile_attr:
                m = folium.Map(location=[43.5, -101.0], zoom_start=9, tiles=tile_url, attr=tile_attr)
            else:
                m = folium.Map(location=[43.5, -101.0], zoom_start=9, tiles=tile_url)

            # --- Tribal boundary layer ---
            if st.session_state.map_layers["tribal_boundary"]:
                folium.GeoJson(
                    SAMPLE_TRIBAL_BOUNDARY,
                    name="Tribal Boundary",
                    style_function=lambda _: {
                        "fillColor": "#2E7D32", "color": "#1B5E20",
                        "weight": 3, "fillOpacity": 0.15,
                    },
                    tooltip="Sample Tribal Territory",
                ).add_to(m)

            # --- Historic boundary (dashed, different colour) ---
            if st.session_state.map_layers["historic_boundary"]:
                historic = {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {"name": "Historic Treaty Boundary"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [-102.0, 43.0], [-100.0, 43.0],
                                [-100.0, 44.0], [-102.0, 44.0],
                                [-102.0, 43.0],
                            ]],
                        },
                    }],
                }
                folium.GeoJson(
                    historic,
                    name="Historic Boundary",
                    style_function=lambda _: {
                        "fillColor": "none", "color": "#8D6E63",
                        "weight": 2, "dashArray": "8 4", "fillOpacity": 0,
                    },
                    tooltip="Historic Treaty Boundary (1868)",
                ).add_to(m)

            # --- Parcel markers ---
            if st.session_state.map_layers["parcels"]:
                parcels_df = st.session_state.parcels
                for _, row in parcels_df.iterrows():
                    pid = row["Parcel ID"]
                    if pid in PARCEL_COORDS:
                        lat, lon = PARCEL_COORDS[pid]
                        status = row.get("Tribal Claim Status", "Unreturned")
                        color_hex = STATUS_COLORS.get(status, "#546E7A")
                        # Map hex to folium colour name (approximate)
                        folium_color = {
                            "#2E7D32": "green",
                            "#F57F17": "orange",
                            "#C62828": "red",
                            "#546E7A": "blue",
                        }.get(color_hex, "gray")
                        popup_html = (
                            f"<b>{row['Name']}</b><br>"
                            f"ID: {pid}<br>"
                            f"Acreage: {row['Acreage']:.1f} ac<br>"
                            f"Owner: {row['Owner of Record']}<br>"
                            f"Status: <span style='color:{color_hex}'>{status}</span><br>"
                            f"Land Use: {row['Land Use']}<br>"
                            f"Priority: {row['Priority Level']}<br>"
                            f"Notes: {row['Notes']}"
                        )
                        folium.Marker(
                            location=[lat, lon],
                            popup=folium.Popup(popup_html, max_width=280),
                            tooltip=f"{row['Name']} ({status})",
                            icon=folium.Icon(color=folium_color, icon="map-marker", prefix="fa"),
                        ).add_to(m)

            # --- Cultural / sacred sites ---
            if st.session_state.map_layers["cultural_sites"]:
                for site in SAMPLE_CULTURAL_SITES:
                    popup_html = (
                        f"<b>{site['name']}</b><br>"
                        f"Type: {site['type']}<br>"
                        f"Notes: {site['notes']}"
                    )
                    folium.Marker(
                        location=[site["lat"], site["lon"]],
                        popup=folium.Popup(popup_html, max_width=220),
                        tooltip=f"⭐ {site['name']}",
                        icon=folium.Icon(color="purple", icon="star", prefix="fa"),
                    ).add_to(m)

            folium.LayerControl().add_to(m)

            # Render map
            map_data = st_folium(m, width="100%", height=560)

            # Show click info
            if map_data and map_data.get("last_object_clicked"):
                clicked = map_data["last_object_clicked"]
                st.info(f"Clicked coordinates: {clicked}")

        except Exception:
            st.error("Error rendering map. Please check your dependencies.")
            st.code(traceback.format_exc())

    # Legend
    st.markdown("#### Parcel Status Legend")
    cols = st.columns(len(STATUS_COLORS))
    for col, (status, color) in zip(cols, STATUS_COLORS.items()):
        col.markdown(
            f"<span style='background:{color};color:#fff;padding:4px 10px;"
            f"border-radius:4px;font-size:0.85em'>{status}</span>",
            unsafe_allow_html=True,
        )

# ===========================================================================
# PAGE 2 — Parcel Registry
# ===========================================================================
elif page == "📋 Parcel Registry":
    st.title("📋 Parcel Registry")

    # --- Filters ---
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.multiselect(
            "Status", options=list(STATUS_COLORS.keys()), default=list(STATUS_COLORS.keys())
        )
    with col2:
        priority_opts = ["High", "Medium", "Low"]
        filter_priority = st.multiselect("Priority", options=priority_opts, default=priority_opts)
    with col3:
        filter_owner = st.text_input("Owner (partial match)", "")

    df = st.session_state.parcels.copy()
    df = df[df["Tribal Claim Status"].isin(filter_status)]
    df = df[df["Priority Level"].isin(filter_priority)]
    if filter_owner:
        df = df[df["Owner of Record"].str.contains(filter_owner, case=False, na=False)]

    st.markdown(f"**{len(df)} parcels shown**")

    # --- Editable table ---
    st.markdown("### Parcel Data (editable)")
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="parcel_editor",
    )
    if st.button("💾 Save changes"):
        # Merge edits back into session state
        st.session_state.parcels = edited_df.reset_index(drop=True)
        add_audit_entry("Parcel registry saved", "User", "Table edits committed")
        st.success("Changes saved to session.")

    # --- Add new parcel form ---
    st.markdown("### Add New Parcel")
    with st.expander("➕ Add parcel"):
        with st.form("add_parcel_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_pid   = c1.text_input("Parcel ID")
            new_name  = c2.text_input("Name")
            new_acr   = c1.number_input("Acreage", min_value=0.0, step=0.5)
            new_owner = c2.text_input("Owner of Record")
            new_stat  = c1.selectbox("Tribal Claim Status", list(STATUS_COLORS.keys()))
            new_use   = c2.text_input("Land Use")
            new_pri   = c1.selectbox("Priority Level", ["High", "Medium", "Low"])
            new_notes = st.text_area("Notes")
            submitted = st.form_submit_button("Add Parcel")
            if submitted:
                if not new_pid or not new_name:
                    st.error("Parcel ID and Name are required.")
                else:
                    new_row = {
                        "Parcel ID": new_pid, "Name": new_name, "Acreage": new_acr,
                        "Owner of Record": new_owner, "Tribal Claim Status": new_stat,
                        "Land Use": new_use, "Priority Level": new_pri, "Notes": new_notes,
                    }
                    st.session_state.parcels = pd.concat(
                        [st.session_state.parcels, pd.DataFrame([new_row])], ignore_index=True
                    )
                    add_audit_entry("Parcel added", "User", f"New parcel {new_pid} — {new_name}")
                    st.success(f"Parcel {new_pid} added.")

    # --- Download ---
    st.markdown("### Export / Import")
    csv_bytes = st.session_state.parcels.to_csv(index=False).encode()
    st.download_button("⬇️ Download parcels as CSV", csv_bytes, "parcels.csv", "text/csv")

    # --- CSV upload ---
    uploaded_csv = st.file_uploader("📤 Upload CSV to bulk-import parcels", type=["csv"])
    if uploaded_csv:
        try:
            imported = pd.read_csv(uploaded_csv)
            st.session_state.parcels = pd.concat(
                [st.session_state.parcels, imported], ignore_index=True
            ).drop_duplicates(subset=["Parcel ID"])
            add_audit_entry("Bulk import", "User", f"{len(imported)} rows imported from CSV")
            st.success(f"Imported {len(imported)} parcels (duplicates by Parcel ID removed).")
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")

# ===========================================================================
# PAGE 3 — Geospatial Analysis
# ===========================================================================
elif page == "🔍 Geospatial Analysis":
    st.title("🔍 Geospatial Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Buffer Analysis", "Overlap / Intersection", "Proximity Report", "Area Calculator"]
    )

    # --- Tab 1: Buffer Analysis ---
    with tab1:
        st.markdown("### Buffer Analysis")
        st.markdown("Select a parcel and generate a buffer around it to identify nearby features.")
        parcel_ids = st.session_state.parcels["Parcel ID"].tolist()
        sel_parcel = st.selectbox("Select Parcel", parcel_ids, key="buf_parcel")
        buf_radius = st.slider("Buffer radius (miles)", 1, 50, 5, key="buf_radius")

        if st.button("Generate Buffer", key="buf_btn"):
            if not FOLIUM_AVAILABLE:
                st.warning("Folium not available.")
            elif sel_parcel not in PARCEL_COORDS:
                st.warning("No coordinates on file for this parcel.")
            else:
                try:
                    lat, lon = PARCEL_COORDS[sel_parcel]
                    # Rough degree conversion (~1 deg lat ≈ 69 mi)
                    deg_radius = buf_radius / 69.0

                    bm = folium.Map(location=[lat, lon], zoom_start=10)
                    folium.Marker([lat, lon], tooltip=sel_parcel).add_to(bm)
                    folium.Circle(
                        location=[lat, lon],
                        radius=buf_radius * 1609.34,  # metres
                        color="#2E7D32", fill=True, fill_opacity=0.2,
                        tooltip=f"{buf_radius}-mile buffer",
                    ).add_to(bm)

                    # Which other parcels fall inside buffer?
                    inside = []
                    for pid, (plat, plon) in PARCEL_COORDS.items():
                        if pid == sel_parcel:
                            continue
                        d = haversine_miles(lat, lon, plat, plon)
                        if d <= buf_radius:
                            inside.append({"Parcel ID": pid, "Distance (mi)": round(d, 2)})
                            folium.Marker(
                                [plat, plon],
                                icon=folium.Icon(color="orange"),
                                tooltip=f"{pid} — {d:.1f} mi",
                            ).add_to(bm)

                    st_folium(bm, width="100%", height=420)

                    if inside:
                        st.markdown(f"**{len(inside)} parcel(s) within {buf_radius} miles:**")
                        st.dataframe(pd.DataFrame(inside), use_container_width=True)
                    else:
                        st.info("No other parcels within buffer radius.")
                except Exception:
                    st.error("Buffer rendering error.")
                    st.code(traceback.format_exc())

    # --- Tab 2: Overlap / Intersection ---
    with tab2:
        st.markdown("### Overlap / Intersection Check")
        st.markdown("Upload two GeoJSON layers to compute their intersection area.")
        col_a, col_b = st.columns(2)
        geojson_a = col_a.file_uploader("Layer A (GeoJSON)", type=["geojson", "json"], key="geo_a")
        geojson_b = col_b.file_uploader("Layer B (GeoJSON)", type=["geojson", "json"], key="geo_b")

        if st.button("Compute Intersection"):
            if not geojson_a or not geojson_b:
                st.warning("Please upload both layers.")
            elif not GEOPANDAS_AVAILABLE:
                st.warning("GeoPandas / Shapely not available.")
            else:
                try:
                    gdf_a = gpd.read_file(geojson_a)
                    gdf_b = gpd.read_file(geojson_b)
                    gdf_a = gdf_a.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3857")
                    gdf_b = gdf_b.set_crs("EPSG:4326", allow_override=True).to_crs("EPSG:3857")
                    intersection = gpd.overlay(gdf_a, gdf_b, how="intersection")
                    area_m2 = intersection.geometry.area.sum()
                    area_acres = area_m2 / 4046.86
                    area_sqkm  = area_m2 / 1_000_000
                    st.success(
                        f"Intersection area: **{area_acres:.2f} acres** ({area_sqkm:.4f} km²)"
                    )
                    st.dataframe(intersection.drop(columns="geometry").head(20))
                except Exception as e:
                    st.error(f"Intersection error: {e}")

    # --- Tab 3: Proximity Report ---
    with tab3:
        st.markdown("### Proximity Report")
        st.markdown("Enter a reference point and find all parcels within a given distance.")
        c1, c2, c3 = st.columns(3)
        ref_lat = c1.number_input("Reference Latitude",  value=43.5,    format="%.6f")
        ref_lon = c2.number_input("Reference Longitude", value=-101.0,  format="%.6f")
        prox_mi = c3.slider("Radius (miles)", 1, 100, 20)

        if st.button("Run Proximity Report"):
            results = []
            for pid, (plat, plon) in PARCEL_COORDS.items():
                d = haversine_miles(ref_lat, ref_lon, plat, plon)
                if d <= prox_mi:
                    parcel_row = st.session_state.parcels[
                        st.session_state.parcels["Parcel ID"] == pid
                    ]
                    name = parcel_row["Name"].values[0] if not parcel_row.empty else pid
                    status = parcel_row["Tribal Claim Status"].values[0] if not parcel_row.empty else "—"
                    results.append({
                        "Parcel ID": pid, "Name": name,
                        "Status": status, "Distance (mi)": round(d, 2),
                    })
            if results:
                results_df = pd.DataFrame(results).sort_values("Distance (mi)")
                st.markdown(f"**{len(results)} parcel(s) within {prox_mi} miles:**")
                st.dataframe(results_df, use_container_width=True)

                if FOLIUM_AVAILABLE:
                    try:
                        pm = folium.Map(location=[ref_lat, ref_lon], zoom_start=9)
                        folium.Marker(
                            [ref_lat, ref_lon],
                            icon=folium.Icon(color="red", icon="home", prefix="fa"),
                            tooltip="Reference Point",
                        ).add_to(pm)
                        folium.Circle(
                            [ref_lat, ref_lon], radius=prox_mi * 1609.34,
                            color="#2E7D32", fill=True, fill_opacity=0.1,
                        ).add_to(pm)
                        for r in results:
                            pid = r["Parcel ID"]
                            plat, plon = PARCEL_COORDS[pid]
                            folium.Marker(
                                [plat, plon], tooltip=f"{r['Name']} ({r['Distance (mi)']} mi)"
                            ).add_to(pm)
                        st_folium(pm, width="100%", height=400)
                    except Exception:
                        pass  # Map is optional here
            else:
                st.info("No parcels found within the specified radius.")

    # --- Tab 4: Area Calculator ---
    with tab4:
        st.markdown("### Area Calculator")
        st.markdown(
            "Upload a GeoJSON polygon (or paste JSON below) to compute its area."
        )
        area_file = st.file_uploader("Upload GeoJSON polygon", type=["geojson", "json"], key="area_file")
        area_json_text = st.text_area(
            "…or paste GeoJSON here",
            value=json.dumps(SAMPLE_TRIBAL_BOUNDARY, indent=2),
            height=200,
        )

        if st.button("Calculate Area"):
            source = None
            if area_file:
                try:
                    source = json.load(area_file)
                except Exception as e:
                    st.error(f"Could not parse file: {e}")
            elif area_json_text:
                try:
                    source = json.loads(area_json_text)
                except Exception as e:
                    st.error(f"Could not parse JSON: {e}")

            if source and GEOPANDAS_AVAILABLE:
                try:
                    gdf = gpd.GeoDataFrame.from_features(source["features"])
                    gdf = gdf.set_crs("EPSG:4326").to_crs("EPSG:3857")
                    area_m2   = gdf.geometry.area.sum()
                    area_acres = area_m2 / 4046.86
                    area_sqkm  = area_m2 / 1_000_000
                    st.success(
                        f"Total area: **{area_acres:,.2f} acres** | "
                        f"**{area_sqkm:.4f} km²** | "
                        f"**{area_m2:,.0f} m²**"
                    )
                    st.dataframe(
                        pd.DataFrame({
                            "Metric": ["Acres", "Square Kilometres", "Square Metres"],
                            "Value":  [f"{area_acres:,.2f}", f"{area_sqkm:.4f}", f"{area_m2:,.0f}"],
                        })
                    )
                except Exception as e:
                    st.error(f"Area calculation error: {e}")
            elif source and not GEOPANDAS_AVAILABLE:
                st.warning("GeoPandas not available — cannot compute area.")

# ===========================================================================
# PAGE 4 — Document Vault
# ===========================================================================
elif page == "📁 Document Vault":
    st.title("📁 Document Vault")
    st.markdown(
        "> **Note:** Documents are stored in session state for this demo. "
        "In production, replace with persistent storage (S3, Azure Blob, etc.)."
    )

    # --- Upload form ---
    st.markdown("### Upload Document")
    with st.form("doc_upload_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        doc_file   = st.file_uploader("Select file (PDF, DOCX, image)", type=["pdf","docx","doc","png","jpg","jpeg"])
        doc_parcel = c1.selectbox("Associate with Parcel", st.session_state.parcels["Parcel ID"].tolist())
        doc_type   = c2.selectbox("Document Type", ["Legal","Application","Agreement","Environmental","Survey","Other"])
        doc_notes  = st.text_input("Notes")
        doc_submit = st.form_submit_button("Upload")
        if doc_submit:
            if doc_file is None:
                st.error("Please select a file.")
            else:
                new_doc = {
                    "Filename":    doc_file.name,
                    "Parcel ID":   doc_parcel,
                    "Upload Date": datetime.date.today().isoformat(),
                    "Type":        doc_type,
                    "Notes":       doc_notes,
                    # In production: store bytes to S3 and save URL here
                    "_bytes":      doc_file.read(),
                }
                new_doc_display = {k: v for k, v in new_doc.items() if k != "_bytes"}
                st.session_state.documents = pd.concat(
                    [st.session_state.documents, pd.DataFrame([new_doc_display])],
                    ignore_index=True,
                )
                add_audit_entry("Document uploaded", "User", f"{doc_file.name} → {doc_parcel}")
                st.success(f"'{doc_file.name}' uploaded and associated with {doc_parcel}.")

    # --- Filter & display ---
    st.markdown("### Document Library")
    filter_parcel_doc = st.selectbox(
        "Filter by Parcel",
        ["All"] + st.session_state.parcels["Parcel ID"].tolist(),
        key="doc_filter",
    )
    docs_df = st.session_state.documents.copy()
    if filter_parcel_doc != "All":
        docs_df = docs_df[docs_df["Parcel ID"] == filter_parcel_doc]

    if docs_df.empty:
        st.info("No documents found.")
    else:
        st.dataframe(docs_df[["Filename","Parcel ID","Upload Date","Type","Notes"]], use_container_width=True)

    # Download all metadata as CSV
    csv_docs = st.session_state.documents[["Filename","Parcel ID","Upload Date","Type","Notes"]].to_csv(index=False).encode()
    st.download_button("⬇️ Download document metadata as CSV", csv_docs, "documents.csv", "text/csv")

# ===========================================================================
# PAGE 5 — Dashboard & Reporting
# ===========================================================================
elif page == "📊 Dashboard & Reporting":
    st.title("📊 Dashboard & Reporting")

    parcels = st.session_state.parcels

    # --- KPI cards ---
    total_parcels  = len(parcels)
    total_acreage  = parcels["Acreage"].sum()
    reclaimed_cnt  = len(parcels[parcels["Tribal Claim Status"] == "Reclaimed"])
    high_priority  = len(parcels[parcels["Priority Level"] == "High"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Parcels", total_parcels)
    k2.metric("Total Acreage", f"{total_acreage:,.1f} ac")
    k3.metric("Parcels Reclaimed", reclaimed_cnt)
    k4.metric("High Priority", high_priority)

    st.markdown("---")

    # --- Charts ---
    if PLOTLY_AVAILABLE:
        col_left, col_right = st.columns(2)

        # Pie: status breakdown
        status_counts = parcels["Tribal Claim Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(
            status_counts, names="Status", values="Count",
            title="Parcels by Status",
            color="Status",
            color_discrete_map=STATUS_COLORS,
        )
        col_left.plotly_chart(fig_pie, use_container_width=True)

        # Bar: priority breakdown
        priority_counts = parcels["Priority Level"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]
        fig_bar = px.bar(
            priority_counts, x="Priority", y="Count",
            title="Parcels by Priority",
            color="Priority",
            color_discrete_map={"High": "#C62828", "Medium": "#F57F17", "Low": "#2E7D32"},
        )
        col_right.plotly_chart(fig_bar, use_container_width=True)

        # Line: reclamation progress over time
        prog_df = pd.DataFrame(SAMPLE_PROGRESS)
        fig_line = px.line(
            prog_df, x="Month", y=["Parcels Reclaimed", "Acreage Reclaimed"],
            title="Reclamation Progress Over Time",
            markers=True,
        )
        fig_line.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Plotly not installed. Run `pip install plotly` for charts.")
        st.dataframe(parcels)

    # --- HTML Report export ---
    st.markdown("---")
    st.markdown("### Export Summary Report")
    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>TR Land Tool — Summary Report</title>
      <style>
        body {{ font-family: sans-serif; background: #F5F5DC; color: #1B1B1B; padding: 32px; }}
        h1 {{ color: #2E7D32; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
        th {{ background: #2E7D32; color: #fff; padding: 8px 12px; text-align: left; }}
        td {{ border: 1px solid #ccc; padding: 8px 12px; }}
        tr:nth-child(even) {{ background: #E8E0D0; }}
        .kpi {{ display: inline-block; background: #2E7D32; color: #fff; border-radius: 8px;
                padding: 12px 24px; margin: 8px; font-size: 1.1em; }}
      </style>
    </head>
    <body>
      <h1>🌿 TR Land Tool — Summary Report</h1>
      <p>Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")} &nbsp;|&nbsp; Version {APP_VERSION}</p>
      <div>
        <span class="kpi">Total Parcels: {total_parcels}</span>
        <span class="kpi">Total Acreage: {total_acreage:,.1f} ac</span>
        <span class="kpi">Reclaimed: {reclaimed_cnt}</span>
        <span class="kpi">High Priority: {high_priority}</span>
      </div>
      <h2>Parcel Registry</h2>
      {parcels.to_html(index=False)}
    </body>
    </html>
    """
    st.download_button(
        "⬇️ Download HTML Report",
        report_html.encode(),
        "tr_land_tool_report.html",
        "text/html",
    )
    with st.expander("Preview Report"):
        st.markdown(report_html, unsafe_allow_html=True)

# ===========================================================================
# PAGE 6 — Field Notes & Audit Log
# ===========================================================================
elif page == "📝 Field Notes & Audit Log":
    st.title("📝 Field Notes & Audit Log")

    tab_notes, tab_audit = st.tabs(["Field Notes", "Audit Trail"])

    with tab_notes:
        st.markdown("### Add Field Note")
        with st.form("field_note_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            fn_officer = c1.text_input("Officer Name")
            fn_parcel  = c2.selectbox("Parcel ID", st.session_state.parcels["Parcel ID"].tolist())
            fn_note    = st.text_area("Field Note")
            fn_lat     = c1.number_input("GPS Latitude",  value=43.5, format="%.6f")
            fn_lon     = c2.number_input("GPS Longitude", value=-101.0, format="%.6f")
            fn_photos  = st.file_uploader("Photos", accept_multiple_files=True, type=["jpg","jpeg","png"])
            fn_submit  = st.form_submit_button("Add Note")
            if fn_submit:
                if not fn_officer or not fn_note:
                    st.error("Officer name and note text are required.")
                else:
                    new_note = {
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Officer":   fn_officer,
                        "Parcel ID": fn_parcel,
                        "Note":      fn_note,
                        "Lat":       fn_lat,
                        "Lon":       fn_lon,
                        "Photos":    len(fn_photos) if fn_photos else 0,
                    }
                    st.session_state.field_notes = pd.concat(
                        [st.session_state.field_notes, pd.DataFrame([new_note])],
                        ignore_index=True,
                    )
                    add_audit_entry("Field note added", fn_officer, f"Parcel {fn_parcel}")
                    st.success("Field note recorded.")

        st.markdown("### Notes Log")
        notes_df = st.session_state.field_notes
        # Filters
        filt_officer = st.selectbox(
            "Filter by Officer", ["All"] + sorted(notes_df["Officer"].unique().tolist()), key="fn_off"
        )
        filt_parcel_fn = st.selectbox(
            "Filter by Parcel", ["All"] + sorted(notes_df["Parcel ID"].unique().tolist()), key="fn_pid"
        )
        disp = notes_df.copy()
        if filt_officer != "All":
            disp = disp[disp["Officer"] == filt_officer]
        if filt_parcel_fn != "All":
            disp = disp[disp["Parcel ID"] == filt_parcel_fn]

        st.dataframe(disp, use_container_width=True)

        csv_notes = notes_df.to_csv(index=False).encode()
        st.download_button("⬇️ Export notes as CSV", csv_notes, "field_notes.csv", "text/csv")

    with tab_audit:
        st.markdown("### Audit Trail (read-only)")
        st.markdown(
            "> All data changes recorded during this session are listed below. "
            "In production this would persist to a database."
        )
        audit_df = pd.DataFrame(st.session_state.audit_log)
        st.dataframe(audit_df, use_container_width=True)

# ===========================================================================
# PAGE 7 — Help & Resources
# ===========================================================================
elif page == "ℹ️ Help & Resources":
    st.title("ℹ️ Help & Resources")

    # External links
    st.markdown("### 🔗 Key Resources")
    st.markdown(
        """
        | Resource | Link |
        |---|---|
        | BIA Branch of Geospatial Support | [bia.gov](https://www.bia.gov/bia/ots/dris/bogs) |
        | EPA Tribal Boundaries Guidance | [epa.gov](https://www.epa.gov/geospatial/guidance-using-tribal-boundaries-areas-and-names-resources) |
        | Tribal Nations GeoHub | [tribal-nations-geoplatform.hub.arcgis.com](https://tribal-nations-geoplatform.hub.arcgis.com) |
        """
    )

    # Glossary
    st.markdown("### 📖 Glossary")
    for term, definition in GLOSSARY.items():
        with st.expander(term):
            st.markdown(definition)

    # Contact form
    st.markdown("### ✉️ Contact Form")
    with st.form("contact_form", clear_on_submit=True):
        contact_name    = st.text_input("Your Name")
        contact_email   = st.text_input("Your Email")
        contact_message = st.text_area("Message")
        contact_submit  = st.form_submit_button("Send")
        if contact_submit:
            if not contact_name or not contact_email or not contact_message:
                st.error("All fields are required.")
            else:
                st.success(
                    f"Thank you, {contact_name}! Your message has been received. "
                    "(In production this would be emailed or logged.)"
                )

    # App info
    st.markdown("---")
    st.markdown(
        f"**TR Land Tool** &nbsp;|&nbsp; Version `{APP_VERSION}` &nbsp;|&nbsp; "
        f"Last updated: `{LAST_UPDATED}` &nbsp;|&nbsp; Powered by SRMCNO",
        unsafe_allow_html=False,
    )
