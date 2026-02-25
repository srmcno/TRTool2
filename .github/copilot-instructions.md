# Copilot Instructions for TRTool2

## Project Overview
This is the **CNO Tribal Reclamation Tool** — a Streamlit web application built for the Choctaw Nation of Oklahoma (CNO), Division of Legal & Compliance. It displays an interactive map of environmental, land-trust, and reclamation data layers relevant to tribal land recovery efforts.

## Tech Stack
- **Language**: Python 3
- **Framework**: [Streamlit](https://streamlit.io/) for the web UI
- **Mapping**: [Folium](https://python-visualization.github.io/folium/) + [streamlit-folium](https://folium.streamlit.app/) for interactive maps
- **Geospatial**: [GeoPandas](https://geopandas.org/) and [Shapely](https://shapely.readthedocs.io/) for spatial data processing
- **Data Sources**: Live ArcGIS REST API endpoints (BIA, USFS, USACE, DEQ, EPA, Census TIGER)

## Project Structure
- `app.py` — Single-file Streamlit application (all UI, data fetching, and mapping logic)
- `requirements.txt` — Python dependencies

## How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Brand & Style Guidelines
- **Primary color**: `#421400` (dark brown) — used for headings and CNO boundary
- **Accent color**: `#00853E` (green) — used for subheadings and USFS layer
- **Font**: Trebuchet MS
- Keep UI consistent with the `BRAND_COLORS` dictionary defined in `app.py`
- Use `st.markdown` with `unsafe_allow_html=True` only when applying brand styles

## Coding Conventions
- Use `@st.cache_data` on all data-fetching functions to avoid redundant API calls
- Keep spatial operations in GeoPandas; avoid raw geometry manipulation where possible
- Wrap all external API calls in `try/except` blocks and return `None` on failure
- Use `gpd.sjoin` with `predicate="intersects"` for clipping layers to the CNO boundary
- Layer toggles are controlled via Folium's `LayerControl`; all layers default to `show=False` except the base map

## Data Layer Naming Conventions
Use the keys in `gis_data` consistently:
- `cno` — CNO Reservation Boundary (Census TIGER)
- `bia` — BIA Trust Land
- `usfs` — USFS Ouachita National Forest
- `usace` — USACE Reservoirs
- `wmas` — Oklahoma State Wildlife Management Areas
- `nwrs` — Federal National Wildlife Refuges
- `deq_bf` — DEQ Brownfields
- `deq_sf` — DEQ Superfund/NPL Sites
- `deq_vcp` — DEQ Voluntary Cleanup Program
- `epa` — EPA Cleanups in My Community (CIMC)

## Testing
There is no automated test suite. To validate changes, run the app locally with `streamlit run app.py` and confirm the map renders all layers correctly.
