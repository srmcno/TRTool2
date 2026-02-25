import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster, MeasureControl, Fullscreen, LocateControl
from streamlit_folium import st_folium
import requests
import warnings
import math
import json
import io
from datetime import datetime
from shapely.geometry import Point

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# PAGE CONFIG & BRAND SYSTEM
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CNO Tribal Reclamation Tool",
    page_icon="\U0001F3DB",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CNO brand palette
BRAND = {
    "maroon": "#421400",
    "gold": "#C9A904",
    "green": "#00853E",
    "blue": "#009ADA",
    "sage": "#4A9E6B",
    "sky": "#5BB5E0",
    "red": "#EF373E",
    "brown": "#87674F",
    "light_bg": "#F8F9FA",
    "white": "#FFFFFF",
}

LAYER_META = {
    "cno":     {"label": "CNO Reservation Boundary", "color": BRAND["maroon"],  "type": "line"},
    "bia":     {"label": "BIA Trust Land",           "color": BRAND["gold"],    "type": "poly"},
    "usfs":    {"label": "USFS Ouachita NF",         "color": BRAND["green"],   "type": "poly"},
    "usace":   {"label": "USACE Reservoirs",         "color": BRAND["blue"],    "type": "poly"},
    "wmas":    {"label": "State WMAs",               "color": BRAND["sage"],    "type": "poly"},
    "nwrs":    {"label": "Federal NWRs",             "color": BRAND["sky"],     "type": "poly"},
    "deq_bf":  {"label": "DEQ Brownfields",          "color": BRAND["maroon"],  "type": "point"},
    "deq_sf":  {"label": "DEQ Superfund / NPL",      "color": BRAND["red"],     "type": "point"},
    "deq_vcp": {"label": "DEQ Voluntary Cleanup",    "color": BRAND["maroon"],  "type": "point"},
    "epa":     {"label": "EPA CIMC Sites",           "color": BRAND["brown"],   "type": "point"},
}

POINT_NAME_FIELDS = {
    "deq_bf": "PROJECT_NA",
    "deq_sf": "NPL_SITE",
    "deq_vcp": "Facility_N",
    "epa": "PRIMARY_NAME",
}

BASEMAPS = {
    "Light (CartoDB Positron)": "CartoDB positron",
    "Dark (CartoDB Dark Matter)": "CartoDB dark_matter",
    "Satellite (Esri WorldImagery)": "Esri.WorldImagery",
    "Terrain (OpenTopoMap)": "OpenTopoMap",
    "Street (OpenStreetMap)": "OpenStreetMap",
}

# ---------------------------------------------------------------------------
# GLOBAL CSS  --  CNO Legal & Compliance brand standards
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Inter', 'Trebuchet MS', sans-serif !important;
        }}
        /* Header area */
        .cno-header {{
            background: linear-gradient(135deg, {BRAND["maroon"]} 0%, #5a1e00 100%);
            padding: 1.5rem 2rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .cno-header h1 {{
            color: {BRAND["white"]} !important;
            font-size: 1.65rem !important;
            margin: 0 !important;
            font-weight: 700 !important;
            letter-spacing: 0.3px;
        }}
        .cno-header .subtitle {{
            color: {BRAND["gold"]};
            font-size: 0.95rem;
            font-weight: 300;
            margin-top: 4px;
        }}
        .cno-header .seal {{
            font-size: 2.5rem;
            margin-right: 1rem;
        }}
        /* Headings */
        h1, h2, h3 {{ color: {BRAND["maroon"]} !important; font-weight: 700 !important; }}
        h4, h5, h6 {{ color: {BRAND["green"]} !important; font-weight: 600 !important; }}
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {BRAND["light_bg"]};
            border-right: 4px solid {BRAND["maroon"]};
        }}
        [data-testid="stSidebar"] h2 {{
            border-bottom: 2px solid {BRAND["gold"]};
            padding-bottom: 0.4rem;
        }}
        /* Metrics */
        [data-testid="stMetric"] {{
            background: {BRAND["white"]};
            border: 1px solid #e0e0e0;
            border-left: 4px solid {BRAND["green"]};
            border-radius: 6px;
            padding: 12px 16px;
        }}
        [data-testid="stMetricValue"] {{
            color: {BRAND["maroon"]} !important;
            font-weight: 700 !important;
        }}
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 6px 6px 0 0;
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {BRAND["maroon"]} !important;
            color: {BRAND["white"]} !important;
        }}
        /* Legend items */
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 0;
            font-size: 0.85rem;
        }}
        .legend-swatch {{
            width: 18px;
            height: 14px;
            border-radius: 3px;
            display: inline-block;
            flex-shrink: 0;
        }}
        .legend-line {{
            width: 18px;
            height: 0;
            border-top: 3px dashed;
            display: inline-block;
            flex-shrink: 0;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }}
        /* Footer */
        .cno-footer {{
            text-align: center;
            font-size: 0.75rem;
            color: #888;
            margin-top: 2rem;
            padding: 1rem 0 0.5rem;
            border-top: 1px solid #ddd;
        }}
        /* Spinner */
        .stSpinner > div > div {{ color: {BRAND["green"]} !important; }}
        /* Workflow steps */
        .wf-step {{
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 6px;
            font-size: 0.85rem;
        }}
        .wf-done {{
            background: #e6f4ea;
            border-left: 4px solid {BRAND["green"]};
        }}
        .wf-active {{
            background: #fff8e1;
            border-left: 4px solid {BRAND["gold"]};
            font-weight: 600;
        }}
        .wf-pending {{
            background: #f5f5f5;
            border-left: 4px solid #ccc;
            color: #999;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# BRANDED HEADER
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="cno-header">
        <div style="display:flex; align-items:center;">
            <span class="seal">\U0001F3DB</span>
            <div>
                <h1>Tribal Reclamation &amp; Land Intelligence Tool</h1>
                <div class="subtitle">Choctaw Nation of Oklahoma &nbsp;|&nbsp; Division of Legal &amp; Compliance</div>
            </div>
        </div>
        <div style="color:#C9A904; font-size:0.8rem; text-align:right;">
            Live GIS Data<br>
            <span style="font-size:0.7rem; color:#ddd;">Session: {date}</span>
        </div>
    </div>
    """.format(date=datetime.now().strftime("%B %d, %Y")),
    unsafe_allow_html=True,
)


# ===================================================================
# DATA FETCHING
# ===================================================================
@st.cache_data(show_spinner=False)
def arcgis_query(url, where="1=1", out_fields="*", max_page=1000, out_sr=4326, geojson=True):
    """Paginated ArcGIS REST query returning a GeoDataFrame or None."""
    all_feats = []
    offset = 0
    fmt = "geojson" if geojson else "json"
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "outSR": out_sr,
            "f": fmt,
            "resultOffset": offset,
            "resultRecordCount": max_page,
            "returnGeometry": "true",
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                break
            data = r.json()
            feats = data.get("features", [])
            if not feats:
                break
            all_feats.extend(feats)
            if len(feats) < max_page:
                break
            offset += len(feats)
        except Exception:
            break
    if not all_feats:
        return None
    if geojson:
        return gpd.GeoDataFrame.from_features(
            {"type": "FeatureCollection", "features": all_feats}, crs="EPSG:4326"
        )
    return all_feats


@st.cache_data(show_spinner=False)
def arcgis_points(url, where="1=1", out_fields="*", max_page=1000, lat_field="LAT", lon_field="LONG"):
    """ArcGIS point query returning a GeoDataFrame from attribute lat/lon."""
    params = {
        "where": where,
        "outFields": out_fields,
        "outSR": 4326,
        "f": "json",
        "resultRecordCount": max_page,
        "returnGeometry": "true",
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        feats = data.get("features", [])
        rows = []
        for f in feats:
            attrs = f.get("attributes", {})
            geom = f.get("geometry", {})
            lat = geom.get("y") or attrs.get(lat_field) or attrs.get("Lat") or attrs.get("LATDD3")
            lon = geom.get("x") or attrs.get(lon_field) or attrs.get("Long") or attrs.get("LONDD3")
            if lat is not None and lon is not None:
                try:
                    attrs["geometry"] = Point(float(lon), float(lat))
                    rows.append(attrs)
                except (ValueError, TypeError):
                    continue
        if not rows:
            return None
        return gpd.GeoDataFrame(rows, crs="EPSG:4326")
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def load_all_data():
    """Fetch every data layer, clip to CNO boundary, return dict."""
    data = {}
    load_status = {}

    sources = {
        "cno": lambda: arcgis_query(
            "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/AIANNHA/MapServer/7/query",
            where="BASENAME = 'Choctaw'",
        ),
        "bia": lambda: arcgis_query(
            "https://biamaps.geoplatform.gov/server/rest/services/DivLTR/BIA_AIAN_National_LAR/MapServer/0/query",
            where="LARNAME LIKE '%Choctaw%'",
        ),
        "usfs": lambda: arcgis_query(
            "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForestSystemBoundaries_01/MapServer/0/query",
            where="FORESTNAME LIKE '%Ouachita%'",
        ),
        "usace": lambda: arcgis_query(
            "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/USACE_Reservoirs/FeatureServer/0/query",
            where="DIST_SYM = 'SWT'",
        ),
        "wmas": lambda: arcgis_query(
            "https://services6.arcgis.com/RBtoEUQ2lmN0K3GY/arcgis/rest/services/OklahomaRecreationalAreas/FeatureServer/0/query",
        ),
        "nwrs": lambda: arcgis_query(
            "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query",
            where="FWSREGION = '2'",
        ),
        "deq_bf": lambda: arcgis_points(
            "https://gis.deq.ok.gov/server/rest/services/LandWeb/MapServer/2/query",
            lat_field="LAT", lon_field="LONG",
        ),
        "deq_sf": lambda: arcgis_points(
            "https://gis.deq.ok.gov/server/rest/services/LandWeb/MapServer/1/query",
            lat_field="LATDD3", lon_field="LONDD3",
        ),
        "deq_vcp": lambda: arcgis_points(
            "https://gis.deq.ok.gov/server/rest/services/LandWeb/MapServer/0/query",
            lat_field="Lat", lon_field="Long",
        ),
        "epa": lambda: arcgis_query(
            "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/Cleanups_in_my_Community_Sites/FeatureServer/0/query",
            where="STATE_CODE = 'OK'",
        ),
    }

    for key, loader in sources.items():
        try:
            data[key] = loader()
            load_status[key] = data[key] is not None
        except Exception:
            data[key] = None
            load_status[key] = False

    # Spatial clip to CNO boundary
    cno_bounds = data.get("cno")

    def clip(gdf):
        if gdf is None or cno_bounds is None:
            return gdf
        try:
            return (
                gpd.sjoin(
                    gdf.to_crs("EPSG:4326"),
                    cno_bounds[["geometry"]].to_crs("EPSG:4326"),
                    predicate="intersects",
                )
                .drop(columns=["index_right"], errors="ignore")
            )
        except Exception:
            return gdf

    for key in ["wmas", "nwrs", "usace", "deq_bf", "deq_sf", "deq_vcp", "epa"]:
        data[key] = clip(data[key])

    return data, load_status


# ===================================================================
# LOAD DATA
# ===================================================================
with st.spinner("Fetching live GIS data from federal & state sources..."):
    gis_data, load_status = load_all_data()


# ===================================================================
# HELPER: safe record count
# ===================================================================
def _count(gdf):
    if gdf is None:
        return 0
    try:
        return len(gdf)
    except Exception:
        return 0


# ===================================================================
# SIDEBAR
# ===================================================================
with st.sidebar:
    st.markdown(f"<h2 style='color:{BRAND['maroon']}'>Map Controls</h2>", unsafe_allow_html=True)

    # Basemap selector
    basemap_label = st.selectbox("Basemap", list(BASEMAPS.keys()), index=0)
    basemap_tiles = BASEMAPS[basemap_label]

    # Layer visibility toggles
    st.markdown(f"<h4 style='color:{BRAND['green']}'>Layer Visibility</h4>", unsafe_allow_html=True)
    visible_layers = {}
    for key, meta in LAYER_META.items():
        default_on = key in ("cno", "bia", "deq_bf", "deq_sf", "epa")
        visible_layers[key] = st.checkbox(meta["label"], value=default_on, key=f"layer_{key}")

    st.markdown("---")

    # Data load status
    st.markdown(f"<h2 style='color:{BRAND['maroon']}'>Data Status</h2>", unsafe_allow_html=True)
    for key, meta in LAYER_META.items():
        status_icon = "\u2705" if load_status.get(key) else "\u274C"
        count = _count(gis_data.get(key))
        st.markdown(f"{status_icon} **{meta['label']}** — {count} features")

    st.markdown("---")

    # Reclamation Workflow tracker
    st.markdown(f"<h2 style='color:{BRAND['maroon']}'>Reclamation Workflow</h2>", unsafe_allow_html=True)
    workflow_steps = [
        "Identify target parcels via GIS analysis",
        "Phase I Environmental Site Assessment (ESA)",
        "Submit BIA fee-to-trust application (25 CFR 151)",
        "Complete title search & legal review",
        "BIA Notice of Decision issued",
        "Land placed into federal trust status",
    ]
    if "wf_progress" not in st.session_state:
        st.session_state.wf_progress = 0

    for i, step in enumerate(workflow_steps):
        if i < st.session_state.wf_progress:
            css = "wf-done"
            icon = "\u2705"
        elif i == st.session_state.wf_progress:
            css = "wf-active"
            icon = "\u25B6\uFE0F"
        else:
            css = "wf-pending"
            icon = "\u2B1C"
        st.markdown(
            f"<div class='wf-step {css}'>{icon} <strong>Step {i+1}:</strong> {step}</div>",
            unsafe_allow_html=True,
        )

    wf_cols = st.columns(2)
    with wf_cols[0]:
        if st.button("Prev Step", use_container_width=True, disabled=st.session_state.wf_progress <= 0):
            st.session_state.wf_progress -= 1
            st.rerun()
    with wf_cols[1]:
        if st.button("Next Step", use_container_width=True, disabled=st.session_state.wf_progress >= len(workflow_steps) - 1):
            st.session_state.wf_progress += 1
            st.rerun()

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:0.75rem; color:#999;'>"
        f"Data sourced from US Census TIGERweb, BIA, USDA Forest Service, "
        f"USACE, USFWS, Oklahoma DEQ, and EPA.<br>"
        f"Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>",
        unsafe_allow_html=True,
    )


# ===================================================================
# MAIN CONTENT — TABS
# ===================================================================
tab_map, tab_data, tab_search, tab_export = st.tabs(
    ["Interactive Map", "Data Explorer", "Site Search", "Export & Reports"]
)

# ===================================================================
# TAB 1 — INTERACTIVE MAP
# ===================================================================
with tab_map:
    # Metrics row
    m_cols = st.columns(5)
    m_cols[0].metric("Boundary", "1" if gis_data.get("cno") is not None else "0")
    m_cols[1].metric("Trust Parcels", _count(gis_data.get("bia")))
    m_cols[2].metric("Brownfields", _count(gis_data.get("deq_bf")))
    m_cols[3].metric("Superfund", _count(gis_data.get("deq_sf")))
    m_cols[4].metric("EPA CIMC", _count(gis_data.get("epa")))

    # Build Folium map
    fmap = folium.Map(location=[34.55, -95.4], zoom_start=8, tiles=basemap_tiles)

    # Plugins
    Fullscreen(position="topleft").add_to(fmap)
    MeasureControl(position="bottomleft", primary_length_unit="miles", primary_area_unit="acres").add_to(fmap)
    LocateControl(strings={"title": "My location"}).add_to(fmap)

    # --- Polygon / line layers ---
    def _add_polygon(key, gdf, name, style_fn):
        if gdf is not None and visible_layers.get(key):
            folium.GeoJson(gdf, name=name, style_function=style_fn).add_to(fmap)

    _add_polygon("cno", gis_data.get("cno"), "CNO Reservation Boundary",
                 lambda x: {"fillColor": "none", "color": BRAND["maroon"], "weight": 3, "dashArray": "6 6"})
    _add_polygon("bia", gis_data.get("bia"), "BIA Trust Land",
                 lambda x: {"fillColor": BRAND["gold"], "color": BRAND["gold"], "weight": 1, "fillOpacity": 0.55})
    _add_polygon("usfs", gis_data.get("usfs"), "USFS Ouachita NF",
                 lambda x: {"fillColor": BRAND["green"], "color": BRAND["green"], "weight": 1, "fillOpacity": 0.35})
    _add_polygon("usace", gis_data.get("usace"), "USACE Reservoirs",
                 lambda x: {"fillColor": BRAND["blue"], "color": BRAND["blue"], "weight": 1, "fillOpacity": 0.45})
    _add_polygon("wmas", gis_data.get("wmas"), "State WMAs",
                 lambda x: {"fillColor": BRAND["sage"], "color": BRAND["sage"], "weight": 1, "fillOpacity": 0.45})
    _add_polygon("nwrs", gis_data.get("nwrs"), "Federal NWRs",
                 lambda x: {"fillColor": BRAND["sky"], "color": BRAND["sky"], "weight": 1, "fillOpacity": 0.45})

    # --- Point layers ---
    def add_point_markers(gdf, name_field, layer_name, fill_color, border_color, target_map):
        if gdf is None or len(gdf) == 0:
            return
        cluster = MarkerCluster(name=layer_name)
        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None:
                continue
            try:
                lat, lon = geom.y, geom.x
                if math.isnan(lat) or math.isnan(lon):
                    continue
            except Exception:
                continue
            name_val = str(row.get(name_field, "Unknown Site"))
            # Build rich popup
            popup_parts = [
                f"<div style='font-family:Inter,Trebuchet MS,sans-serif;min-width:200px;'>",
                f"<b style='color:{BRAND['maroon']};font-size:1rem;'>{name_val}</b><hr style='margin:4px 0;border-color:{BRAND['gold']}'>",
            ]
            for col in gdf.columns:
                if col in ("geometry", name_field):
                    continue
                val = row.get(col)
                if val is not None and str(val).strip() and str(val) != "None":
                    popup_parts.append(f"<b>{col}:</b> {val}<br>")
            popup_parts.append(
                f"<div style='margin-top:6px;font-size:0.7rem;color:#999;'>Lat {lat:.5f}, Lon {lon:.5f}</div></div>"
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                color=border_color,
                weight=2,
                fill=True,
                fillColor=fill_color,
                fillOpacity=0.9,
                popup=folium.Popup("".join(popup_parts), max_width=350),
                tooltip=name_val,
            ).add_to(cluster)
        cluster.add_to(target_map)

    if visible_layers.get("deq_bf"):
        add_point_markers(gis_data.get("deq_bf"), "PROJECT_NA", "DEQ Brownfields", BRAND["maroon"], BRAND["gold"], fmap)
    if visible_layers.get("deq_sf"):
        add_point_markers(gis_data.get("deq_sf"), "NPL_SITE", "DEQ Superfund/NPL", BRAND["red"], BRAND["white"], fmap)
    if visible_layers.get("deq_vcp"):
        add_point_markers(gis_data.get("deq_vcp"), "Facility_N", "DEQ Voluntary Cleanup", BRAND["maroon"], BRAND["white"], fmap)
    if visible_layers.get("epa"):
        add_point_markers(gis_data.get("epa"), "PRIMARY_NAME", "EPA CIMC Sites", BRAND["brown"], BRAND["white"], fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)

    # Render map + legend side-by-side
    map_col, legend_col = st.columns([4, 1])
    with map_col:
        st_folium(fmap, width="100%", height=680, returned_objects=[])

    with legend_col:
        st.markdown(f"### Map Legend")
        for key, meta in LAYER_META.items():
            if meta["type"] == "line":
                swatch = f"<span class='legend-line' style='border-color:{meta['color']};'></span>"
            elif meta["type"] == "point":
                swatch = f"<span class='legend-dot' style='background:{meta['color']};'></span>"
            else:
                swatch = f"<span class='legend-swatch' style='background:{meta['color']};opacity:0.7;'></span>"
            active = "\u2705" if visible_layers.get(key) else "\u2B1C"
            st.markdown(
                f"<div class='legend-item'>{swatch} {active} {meta['label']}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            f"<div style='font-size:0.75rem; color:#666;'>"
            f"<b>Map Tools:</b><br>"
            f"\u2022 Use the ruler (bottom-left) to measure distances & areas<br>"
            f"\u2022 Click fullscreen (top-left) for expanded view<br>"
            f"\u2022 Click locate to center on your position<br>"
            f"\u2022 Toggle layers in the sidebar</div>",
            unsafe_allow_html=True,
        )


# ===================================================================
# TAB 2 — DATA EXPLORER
# ===================================================================
with tab_data:
    st.markdown(f"### Data Explorer")
    st.markdown("Browse attribute data for every loaded layer. Select a dataset below.")

    explorer_options = {
        meta["label"]: key for key, meta in LAYER_META.items() if gis_data.get(key) is not None
    }
    if not explorer_options:
        st.warning("No datasets were loaded. Check network connectivity and try refreshing.")
    else:
        selected_label = st.selectbox("Select dataset", list(explorer_options.keys()))
        selected_key = explorer_options[selected_label]
        gdf = gis_data[selected_key]

        # Drop geometry for display
        display_df = gdf.drop(columns=["geometry"], errors="ignore")

        st.markdown(f"**{selected_label}** -- {len(display_df)} records")

        # Column filter
        all_cols = list(display_df.columns)
        shown_cols = st.multiselect("Columns to display", all_cols, default=all_cols[:10])
        if shown_cols:
            st.dataframe(display_df[shown_cols], use_container_width=True, height=420)
        else:
            st.dataframe(display_df, use_container_width=True, height=420)

        # Summary stats for numeric columns
        numeric_df = display_df.select_dtypes(include=["number"])
        if not numeric_df.empty:
            with st.expander("Summary Statistics"):
                st.dataframe(numeric_df.describe().T, use_container_width=True)


# ===================================================================
# TAB 3 — SITE SEARCH
# ===================================================================
with tab_search:
    st.markdown(f"### Site Search")
    st.markdown("Search across all environmental site layers by name or keyword.")

    search_query = st.text_input("Enter site name or keyword", placeholder="e.g., Creek, Mine, Lumber...")

    if search_query:
        search_results = []
        for key, name_field in POINT_NAME_FIELDS.items():
            gdf = gis_data.get(key)
            if gdf is None:
                continue
            if name_field not in gdf.columns:
                continue
            mask = gdf[name_field].astype(str).str.contains(search_query, case=False, na=False)
            matched = gdf[mask].copy()
            if len(matched) > 0:
                matched["_source_layer"] = LAYER_META[key]["label"]
                matched["_name"] = matched[name_field].astype(str)
                matched["_lat"] = matched.geometry.y
                matched["_lon"] = matched.geometry.x
                search_results.append(matched[["_source_layer", "_name", "_lat", "_lon"]])

        if search_results:
            results_df = gpd.pd.concat(search_results, ignore_index=True)
            st.success(f"Found {len(results_df)} matching site(s).")
            st.dataframe(
                results_df.rename(columns={"_source_layer": "Layer", "_name": "Site Name", "_lat": "Latitude", "_lon": "Longitude"}),
                use_container_width=True,
                height=350,
            )

            # Mini map of results
            if len(results_df) > 0:
                with st.expander("Show results on map", expanded=True):
                    res_map = folium.Map(location=[34.55, -95.4], zoom_start=8, tiles="CartoDB positron")
                    for _, r in results_df.iterrows():
                        folium.Marker(
                            location=[r["_lat"], r["_lon"]],
                            popup=f"{r['_name']} ({r['_source_layer']})",
                            tooltip=r["_name"],
                            icon=folium.Icon(color="red", icon="info-sign"),
                        ).add_to(res_map)
                    st_folium(res_map, width="100%", height=400, returned_objects=[])
        else:
            st.info("No sites matched your search. Try a different keyword.")
    else:
        st.info("Enter a keyword above to search across DEQ Brownfields, Superfund, Voluntary Cleanup, and EPA CIMC datasets.")


# ===================================================================
# TAB 4 — EXPORT & REPORTS
# ===================================================================
with tab_export:
    st.markdown(f"### Export & Reports")
    st.markdown("Download layer data as CSV or GeoJSON for offline analysis and reporting.")

    export_options = {
        meta["label"]: key for key, meta in LAYER_META.items() if gis_data.get(key) is not None
    }
    if not export_options:
        st.warning("No datasets available to export.")
    else:
        export_label = st.selectbox("Select layer to export", list(export_options.keys()), key="export_sel")
        export_key = export_options[export_label]
        export_gdf = gis_data[export_key]

        exp_col1, exp_col2 = st.columns(2)

        # CSV export
        with exp_col1:
            st.markdown(f"#### CSV Download")
            csv_df = export_gdf.drop(columns=["geometry"], errors="ignore")
            csv_buf = io.StringIO()
            csv_df.to_csv(csv_buf, index=False)
            st.download_button(
                label=f"Download {export_label} (.csv)",
                data=csv_buf.getvalue(),
                file_name=f"cno_{export_key}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.caption(f"{len(csv_df)} rows, {len(csv_df.columns)} columns")

        # GeoJSON export
        with exp_col2:
            st.markdown(f"#### GeoJSON Download")
            try:
                geojson_str = export_gdf.to_json()
                st.download_button(
                    label=f"Download {export_label} (.geojson)",
                    data=geojson_str,
                    file_name=f"cno_{export_key}_{datetime.now().strftime('%Y%m%d')}.geojson",
                    mime="application/geo+json",
                    use_container_width=True,
                )
                feat_count = len(json.loads(geojson_str).get("features", []))
                st.caption(f"{feat_count} features with geometry")
            except Exception as e:
                st.error(f"GeoJSON export unavailable for this layer: {e}")

        # Quick report
        st.markdown("---")
        st.markdown(f"#### Quick Layer Summary")
        summary_cols = st.columns(3)
        summary_cols[0].metric("Records", len(export_gdf))
        summary_cols[1].metric("Columns", len(export_gdf.columns))
        geom_types = set()
        for g in export_gdf.geometry:
            if g is not None:
                geom_types.add(g.geom_type)
        summary_cols[2].metric("Geometry Types", ", ".join(geom_types) if geom_types else "N/A")


# ===================================================================
# FOOTER
# ===================================================================
st.markdown(
    f"""
    <div class="cno-footer">
        <strong>Choctaw Nation of Oklahoma</strong> &mdash; Division of Legal &amp; Compliance<br>
        This tool is for internal governmental use only. Data sourced from federal and state GIS services.<br>
        All analyses should be verified by qualified personnel before any legal or regulatory action.<br>
        &copy; {datetime.now().year} Choctaw Nation of Oklahoma. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True,
)
