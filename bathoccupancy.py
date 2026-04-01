import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(
    page_title="Bath Car Parks",
    page_icon="🅿️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .block-container { padding: 2rem 2rem 1rem; }
    .header { margin-bottom: 1.5rem; }
    .header h1 { font-size: 2rem; font-weight: 600; margin: 0; }
    .header p { font-size: 0.85rem; color: #888; margin: 4px 0 0; font-family: 'DM Mono', monospace; }
    .metric-row { display: flex; gap: 12px; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .metric-card { background: rgba(255,255,255,0.08); border-radius: 12px; padding: 1rem 1.25rem; flex: 1; min-width: 140px; border: 1px solid rgba(255,255,255,0.15); }
    .metric-label { font-size: 11px; color: #aaa; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
    .metric-value { font-size: 1.75rem; font-weight: 600; }
    .metric-value.green { color: #2ecc71; }
    .metric-value.red { color: #e74c3c; }
    .park-card { background: rgba(255,255,255,0.06); border-radius: 16px; padding: 0.75rem 1rem 1rem; border: 1px solid rgba(255,255,255,0.12); margin-bottom: 4px; }
    .park-name { font-size: 0.9rem; font-weight: 600; text-align: center; margin-top: 4px; padding: 0 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .park-sub { font-size: 0.75rem; color: #aaa; text-align: center; margin-top: 6px; padding-bottom: 4px; }
    .status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.03em; }
    .status-filling { background: #fff3e0; color: #e65100; }
    .status-emptying { background: #e8f5e9; color: #2e7d32; }
    .status-static { background: #f3f3f3; color: #555; }
    .footer { font-size: 0.75rem; color: #666; text-align: center; margin-top: 1.5rem; font-family: 'DM Mono', monospace; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def fetch_data():
    try:
        url = "https://data.bathhacked.org/api/datasets/8/rows?page=1&per_page=15"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        raw = r.json()
        rows = raw["data"]
        parks = []
        for i, row in enumerate(rows):
            cap = int(row.get("capacity") or 0)
            occ = int(row.get("occupancy") or 0)
            avail = max(0, cap - occ)
            pct_avail = (avail / cap * 100) if cap > 0 else 0
            parks.append({
                "index": i,
                "name": row.get("name", f"Car Park {i+1}"),
                "capacity": cap,
                "occupancy": occ,
                "available": avail,
                "pct_available": pct_avail,
                "status": row.get("status", ""),
                "lastupdate": row.get("lastupdate", ""),
            })
        parks.sort(key=lambda x: x["available"], reverse=True)
        return parks, None
    except Exception as e:
        return None, str(e)


def get_colour(pct):
    if pct >= 50:
        return "#2ecc71", "#27ae60"
    elif pct >= 25:
        return "#f39c12", "#e67e22"
    else:
        return "#e74c3c", "#c0392b"


def make_gauge(park):
    pct = park["pct_available"]
    fill, dark = get_colour(pct)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=park["available"],
        number={"font": {"size": 32, "color": dark, "family": "DM Sans"}},
        gauge={
            "axis": {
                "range": [0, max(park["capacity"], 1)],
                "showticklabels": False,
                "tickwidth": 0
            },
            "bar": {"color": fill, "thickness": 0.7},
            "bgcolor": "rgba(200,200,200,0.15)",
            "borderwidth": 0,
        }
    ))
    fig.update_layout(
        height=180,
        margin=dict(t=20, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "DM Sans"},
    )
    return fig


def status_badge(status):
    s = (status or "").lower()
    if "fill" in s:
        return '<span class="status-badge status-filling">&#8593; Getting busier</span>'
    elif "empty" in s:
        return '<span class="status-badge status-emptying">&#8595; Clearing out</span>'
    else:
        return '<span class="status-badge status-static">&#8594; Steady</span>'


# --- Main App ---
now = datetime.now().strftime("%d %b %Y · %H:%M")
parks, error = fetch_data()

st.markdown(f"""
<div class="header">
    <h1>🅿️ Bath Car Parks</h1>
    <p>Available spaces · {now}</p>
</div>
""", unsafe_allow_html=True)

if error or not parks:
    st.error(f"Could not load data: {error}")
else:
    total_cap = sum(p["capacity"] for p in parks)
    total_avail = sum(p["available"] for p in parks)
    busy = sum(1 for p in parks if p["pct_available"] < 25)
    best = parks[0]["name"]
    busy_class = "red" if busy > 0 else "green"

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-label">Total spaces</div>
            <div class="metric-value">{total_cap:,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Available now</div>
            <div class="metric-value green">{total_avail:,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Nearly full</div>
            <div class="metric-value {busy_class}">{busy} of {len(parks)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Best option</div>
            <div class="metric-value" style="font-size:1.1rem; padding-top:6px;">{best}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for idx, park in enumerate(parks):
        with cols[idx % 3]:
            st.markdown('<div class="park-card">', unsafe_allow_html=True)
            st.plotly_chart(
                make_gauge(park),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"gauge_{idx}"
            )
            st.markdown(f"""
                <div class="park-name">{park['name']}</div>
                <div class="park-sub">
                    {park['available']} of {park['capacity']} free
                    &nbsp;·&nbsp;
                    {status_badge(park['status'])}
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="footer">Data: Bath Hacked · Refreshes every 5 min · {now}</div>',
        unsafe_allow_html=True
    )

    time.sleep(300)
    st.rerun()