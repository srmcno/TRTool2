%%writefile app.py
import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import requests
import warnings
import math
from shapely.geometry import Point

warnings.filterwarnings('ignore')

# BRAND ALIGNMENT & PAGE CONFIG
st.set_page_config(page_title="CNO Tribal Reclamation Tool", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        html, body, [class*="css"] { font-family: 'Trebuchet MS', sans-serif !important; }
        h1, h2, h3, .brand-primary { color: #421400 !important; font-weight: bold !important; }
        h4, h5, h6, .brand-accent { color: #00853E !important; font-weight: 300 !important; }
        [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 4px solid #421400; }
        .stSpinner > div > div { color: #00853E !important; }
    </style>
""", unsafe_allow_html=True)

BRAND_COLORS = {
    "CNO_BOUNDARY": "#421400", "BIA_TRUST": "#C9A904", "USFS_FOREST": "#00853E",
    "USACE_RESERVOIR": "#009ADA", "STATE_WMA": "#4A9E6B", "FED_NWR": "#5BB5E0",
    "BROWNFIELD_OUTLINE": "#C9A904", "BROWNFIELD_FILL": "#421400", "SUPERFUND": "#EF373E",
    "VCP": "#421400", "EPA_CIMC": "#87674F"
}

@st.cache_data(show_spinner=False)
def arcgis_query(url, where="1=1", out_fields="*", max_page=1000, out_sr=4326, geojson=True):
    all_feats = []
    offset = 0
    fmt = "geojson" if geojson else "json"
    while True:
        params = {"where": where, "outFields": out_fields, "outSR": out_sr, "f": fmt, "resultOffset": offset, "resultRecordCount": max_page, "returnGeometry": "true"}
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200: break
            data = r.json()
            feats = data.get("features", [])
            if not feats: break
            all_feats.extend(feats)
            if len(feats) < max_page: break
            offset += len(feats)
        except: break
    if not all_feats: return None
    if geojson: return gpd.GeoDataFrame.from_features({"type": "FeatureCollection", "features": all_feats}, crs="EPSG:4326")
    return all_feats

@st.cache_data(show_spinner=False)
def arcgis_points(url, where="1=1", out_fields="*", max_page=1000, lat_field="LAT", lon_field="LONG"):
    params = {"where": where, "outFields": out_fields, "outSR": 4326, "f": "json", "resultRecordCount": max_page, "returnGeometry": "true"}
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
            if lat and lon:
                attrs["geometry"] = Point(float(lon), float(lat))
                rows.append(attrs)
        if not rows: return None
        return gpd.GeoDataFrame(rows, crs="EPSG:4326")
    except: return None

@st.cache_data(show_spinner=False)
def load_all_data():
    data = {}
    data['cno'] = arcgis_query("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/AIANNHA/MapServer/7/query", where="BASENAME = 'Choctaw'")
    data['bia'] = arcgis_query("https://biamaps.geoplatform.gov/server/rest/services/DivLTR/BIA_AIAN_National_LAR/MapServer/0/query", where="LARNAME LIKE '%Choctaw%'")
    data['usfs'] = arcgis_query("https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_ForestSystemBoundaries_01/MapServer/0/query", where="FORESTNAME LIKE '%Ouachita%'")
    data['usace'] = arcgis_query("https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/USACE_Reservoirs/FeatureServer/0/query", where="DIST_SYM = 'SWT'")
    data['wmas'] = arcgis_query("https://services6.arcgis.com/RBtoEUQ2lmN0K3GY/arcgis/rest/services/OklahomaRecreationalAreas/FeatureServer/0/query")
    data['nwrs'] = arcgis_query("https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0/query", where="FWSREGION = '2'")
    data['deq_bf'] = arcgis_points("https://gis.deq.ok.gov/server/rest/services/LandWeb/MapServer/2/query", lat_field="LAT", lon_field="LONG")
    data['deq_sf'] = arcgis_points("https://gis.deq.ok.gov/server/rest/services/LandWeb/MapServer/1/query", lat_field="LATDD3", lon_field="LONDD3")
    data['deq_vcp'] = arcgis_points("https://gis.deq.ok.gov/server/rest/services/LandWeb/MapServer/0/query", lat_field="Lat", lon_field="Long")
    data['epa'] = arcgis_query("https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/Cleanups_in_my_Community_Sites/FeatureServer/0/query", where="STATE_CODE = 'OK'")
    
    cno_bounds = data['cno']
    def clip(gdf):
        if gdf is None or cno_bounds is None: return gdf
        try: return gpd.sjoin(gdf.to_crs("EPSG:4326"), cno_bounds[["geometry"]].to_crs("EPSG:4326"), predicate="intersects").drop(columns=["index_right"], errors="ignore")
        except: return gdf

    data['wmas'] = clip(data['wmas'])
    data['nwrs'] = clip(data['nwrs'])
    data['usace'] = clip(data['usace'])
    data['deq_bf'] = clip(data['deq_bf'])
    data['deq_sf'] = clip(data['deq_sf'])
    data['deq_vcp'] = clip(data['deq_vcp'])
    data['epa'] = clip(data['epa'])
    return data

st.markdown("<h1 class='brand-primary'>Tribal Reclamation & Land Intelligence Tool</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='brand-accent'>Choctaw Nation of Oklahoma | Division of Legal & Compliance</h3>", unsafe_allow_html=True)

with st.spinner("Fetching live environmental and parcel data..."):
    gis_data = load_all_data()

def add_point_markers(gdf, name_field, layer_name, fill_color, border_color, m):
    if gdf is None or len(gdf) == 0: return
    group = MarkerCluster(name=layer_name, show=False) 
    for _, row in gdf.iterrows():
        if row.geometry is None or math.isnan(row.geometry.y): continue
        name = row.get(name_field, "Unknown Site")
        popup_html = f"<div style='font-family:Trebuchet MS;'><b style='color:#421400;'>{name}</b><br></div>"
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x], radius=7, color=border_color, weight=2, fill=True, fillColor=fill_color, fillOpacity=0.9, popup=folium.Popup(popup_html, max_width=300), tooltip=str(name)
        ).add_to(group)
    group.add_to(m)

m = folium.Map(location=[34.55, -95.4], zoom_start=8, tiles="CartoDB positron")

if gis_data['cno'] is not None: folium.GeoJson(gis_data['cno'], name="CNO Reservation Boundary", style_function=lambda x: {"fillColor": "none", "color": BRAND_COLORS["CNO_BOUNDARY"], "weight": 3, "dashArray": "6 6"}).add_to(m)
if gis_data['bia'] is not None: folium.GeoJson(gis_data['bia'], name="BIA Trust Land", style_function=lambda x: {"fillColor": BRAND_COLORS["BIA_TRUST"], "color": BRAND_COLORS["BIA_TRUST"], "weight": 1, "fillOpacity": 0.6}).add_to(m)
if gis_data['usfs'] is not None: folium.GeoJson(gis_data['usfs'], name="USFS Ouachita NF", style_function=lambda x: {"fillColor": BRAND_COLORS["USFS_FOREST"], "color": BRAND_COLORS["USFS_FOREST"], "weight": 1, "fillOpacity": 0.4}).add_to(m)
if gis_data['usace'] is not None: folium.GeoJson(gis_data['usace'], name="USACE Reservoirs", style_function=lambda x: {"fillColor": BRAND_COLORS["USACE_RESERVOIR"], "color": BRAND_COLORS["USACE_RESERVOIR"], "weight": 1, "fillOpacity": 0.5}).add_to(m)
if gis_data['wmas'] is not None: folium.GeoJson(gis_data['wmas'], name="State WMAs", style_function=lambda x: {"fillColor": BRAND_COLORS["STATE_WMA"], "color": BRAND_COLORS["STATE_WMA"], "weight": 1, "fillOpacity": 0.5}).add_to(m)
if gis_data['nwrs'] is not None: folium.GeoJson(gis_data['nwrs'], name="Federal NWRs", style_function=lambda x: {"fillColor": BRAND_COLORS["FED_NWR"], "color": BRAND_COLORS["FED_NWR"], "weight": 1, "fillOpacity": 0.5}).add_to(m)

add_point_markers(gis_data['deq_bf'], "PROJECT_NA", "DEQ Brownfields", BRAND_COLORS["BROWNFIELD_FILL"], BRAND_COLORS["BROWNFIELD_OUTLINE"], m)
add_point_markers(gis_data['deq_sf'], "NPL_SITE", "DEQ Superfund/NPL", BRAND_COLORS["SUPERFUND"], "#FFFFFF", m)
add_point_markers(gis_data['deq_vcp'], "Facility_N", "DEQ Voluntary Cleanup", BRAND_COLORS["VCP"], "#FFFFFF", m)
add_point_markers(gis_data['epa'], "PRIMARY_NAME", "EPA CIMC Sites", BRAND_COLORS["EPA_CIMC"], "#FFFFFF", m)

folium.LayerControl(collapsed=False).add_to(m)

col1, col2 = st.columns([3, 1])
with col1:
    st_folium(m, width="100%", height=700, returned_objects=[])

with col2:
    st.markdown("<h3 class='brand-primary'>Map Legend</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-family:'Trebuchet MS'; font-size: 14px;">
        <span style="color:{BRAND_COLORS['CNO_BOUNDARY']}; font-weight:bold;">&#9644;&#9644;</span> CNO Boundary<br>
        <span style="background:{BRAND_COLORS['BIA_TRUST']}; padding:2px 10px;">&nbsp;</span> BIA Trust Land<br>
        <span style="background:{BRAND_COLORS['USFS_FOREST']}; padding:2px 10px;">&nbsp;</span> Ouachita NF<br>
        <span style="background:{BRAND_COLORS['USACE_RESERVOIR']}; padding:2px 10px;">&nbsp;</span> USACE Reservoirs<br>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2 class='brand-primary'>Reclamation Workflow</h2>", unsafe_allow_html=True)
    st.markdown("1. Identify target parcels\n2. Phase I ESA\n3. BIA application\n4. Title search\n5. BIA Notice of Decision\n6. Land placed in trust")
