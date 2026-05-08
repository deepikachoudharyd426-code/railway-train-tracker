import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

API_KEY = st.secrets["API_KEY"]
API_HOST = "indian-railway-irctc.p.rapidapi.com"

CITY_5G = {
    'NDLS': 95, 'DR': 90, 'TNA': 88, 'PNVL': 82, 'CHI': 78,
    'RN': 72, 'KUDL': 60, 'SWV': 58, 'MAO': 75, 'KKW': 55,
    'THVM': 65, 'MAS': 88, 'SBC': 87, 'HWH': 85, 'PUNE': 83,
    'ADI': 80, 'LKO': 75, 'CNB': 70, 'BPL': 65, 'ST': 78,
}

def get_5g_signal(code):
    score = CITY_5G.get(code, 50)
    if score >= 85:
        return "🟢 Excellent"
    elif score >= 70:
        return "🟡 Good"
    elif score >= 55:
        return "🟠 Moderate"
    else:
        return "🔴 Weak"

def get_train_status(train_number, date):
    url = "https://indian-railway-irctc.p.rapidapi.com/api/trains/v1/train/status"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }
    params = {
        "departure_date": date,
        "isH5": "true",
        "client": "web",
        "train_number": train_number
    }
    response = requests.get(url, headers=headers, params=params, verify=False)
    return response.json()

def calculate_delay(scheduled, actual):
    if not scheduled or not actual or scheduled == "--" or actual == "--":
        return None
    fmt = "%H:%M"
    try:
        s = datetime.strptime(scheduled, fmt)
        a = datetime.strptime(actual, fmt)
        diff = int((a - s).seconds / 60)
        if diff > 720:
            diff = diff - 1440
        return diff
    except Exception:
        return None

def time_to_minutes(t):
    if not t or t == "--":
        return None
    try:
        h, m = map(int, t.split(":"))
        return h * 60 + m
    except Exception:
        return None

def minutes_to_hhmm(mins):
    if mins is None:
        return "--"
    hrs = int(mins) // 60
    mn = int(mins) % 60
    return f"{hrs}h {mn}m"

st.set_page_config(page_title="GoRail", page_icon="🚂", layout="wide")

st.markdown("""
<style>
    /* Global */
    .stApp {
        background-color: #F8FAFF;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Hide streamlit defaults */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header */
    .gorail-header {
        background: linear-gradient(135deg, #1A56DB 0%, #0E3B8F 100%);
        padding: 40px 50px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(26, 86, 219, 0.2);
    }
    
    .gorail-title {
        font-size: 48px;
        font-weight: 800;
        color: white;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .gorail-subtitle {
        font-size: 16px;
        color: rgba(255,255,255,0.8);
        margin: 8px 0 0 0;
        letter-spacing: 1px;
    }
    
    /* Search box */
    .search-container {
        background: white;
        padding: 30px 35px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        margin-bottom: 25px;
        border: 1px solid #E8EEFF;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        border: 1px solid #E8EEFF;
        text-align: center;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1A56DB;
        margin: 0;
    }
    
    .metric-label {
        font-size: 13px;
        color: #6B7280;
        margin: 4px 0 0 0;
        font-weight: 500;
    }
    
    /* Train info banner */
    .train-banner {
        background: white;
        padding: 24px 30px;
        border-radius: 14px;
        border-left: 5px solid #1A56DB;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        margin-bottom: 20px;
    }
    
    .train-name {
        font-size: 24px;
        font-weight: 700;
        color: #1A56DB;
        margin: 0;
    }
    
    .train-meta {
        font-size: 14px;
        color: #6B7280;
        margin: 6px 0 0 0;
    }
    
    /* Section headers */
    .section-header {
        font-size: 18px;
        font-weight: 700;
        color: #1E1E1E;
        margin: 25px 0 15px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #E8EEFF;
    }
    
    /* Journey card */
    .journey-card {
        background: linear-gradient(135deg, #EEF3FB 0%, #E8EEFF 100%);
        padding: 24px;
        border-radius: 14px;
        border: 1px solid #D0DEFF;
        margin-bottom: 20px;
    }
    
    /* Status badges */
    .badge-ontime {
        background: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }
    
    .badge-late {
        background: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }
    
    /* Input styling */
    .stTextInput input {
        border-radius: 10px !important;
        border: 2px solid #E8EEFF !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        background: #FAFBFF !important;
    }
    
    .stTextInput input:focus {
        border-color: #1A56DB !important;
        box-shadow: 0 0 0 3px rgba(26,86,219,0.1) !important;
    }
    
    /* Button */
    .stButton button {
        background: linear-gradient(135deg, #1A56DB, #0E3B8F) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 12px 30px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(26,86,219,0.3) !important;
        transition: all 0.2s !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(26,86,219,0.4) !important;
    }
    
    /* Dataframe */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #E8EEFF !important;
    }
    
    /* Divider */
    hr {
        border: none !important;
        border-top: 2px solid #E8EEFF !important;
        margin: 20px 0 !important;
    }
    
    /* Alert boxes */
    .stSuccess {
        border-radius: 10px !important;
    }
    
    .stInfo {
        border-radius: 10px !important;
    }
    
    .stWarning {
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown(f"""
<div class="gorail-header">
    <p class="gorail-title">🚂 GoRail</p>
    <p class="gorail-subtitle">REAL-TIME STATUS &nbsp;•&nbsp; DELAY PREDICTION &nbsp;•&nbsp; ETA &nbsp;•&nbsp; 5G COVERAGE</p>
</div>
""", unsafe_allow_html=True)

# ── SEARCH BOX ──
st.markdown('<div class="search-container">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    train_number = st.text_input("🚆 Train Number", value="", placeholder="Enter train number e.g. 12051")
with col2:
    selected_date = st.date_input("📅 Journey Date", value=datetime.today(), format="DD/MM/YYYY")
    date = selected_date.strftime('%Y%m%d')
    display_date = selected_date.strftime('%d/%m/%Y')
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    search = st.button("🔍 Track Train", type="primary", use_container_width=True)

st.markdown(f"""
    <p style='text-align:right; color:#9CA3AF; font-size:13px; margin-top:5px;'>
    Today: <b>{datetime.today().strftime('%d/%m/%Y')}</b>
    </p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if search:
    if not train_number:
        st.warning("⚠️ Please enter a Train Number to continue.")
        st.stop()

    with st.spinner("Fetching live train data..."):
        data = get_train_status(train_number, date)

    try:
        body = data.get('body', data.get('data', {}))
        stations_raw = body.get('data', body.get('stations', []))
        train_name = body.get('train_name', body.get('trainName', f'Train {train_number}'))
        current_stn_code = body.get('current_station', '')
        terminated = body.get('terminated', False)

        if not stations_raw:
            st.error("❌ No data found. Please verify train number and date.")
            st.stop()

        # ── TRAIN BANNER ──
        st.markdown(f"""
        <div class="train-banner">
            <p class="train-name">🚆 {train_name}</p>
            <p class="train-meta">Train No: <b>{train_number}</b> &nbsp;|&nbsp; Date: <b>{display_date}</b></p>
        </div>
        """, unsafe_allow_html=True)

        if terminated:
            st.success("🏁 Train has reached its final destination!")
        elif current_stn_code:
            st.info(f"📍 Currently near station: **{current_stn_code}**")

        # ── CALCULATE STATS ──
        delays = []
        last_known = None
        next_station = None
        first_station = stations_raw[0] if stations_raw else None
        last_station = stations_raw[-1] if stations_raw else None

        for s in stations_raw:
            delay = calculate_delay(s.get('arrivalTime', '--'), s.get('actual_arrival_time', '--'))
            if delay is not None:
                delays.append(delay)
                last_known = s
            elif next_station is None and last_known is not None:
                next_station = s

        avg_delay = round(sum(delays) / len(delays)) if delays else 0

        first_dep = first_station.get('departureTime', '--') if first_station else '--'
        last_arr = last_station.get('arrivalTime', '--') if last_station else '--'
        first_min = time_to_minutes(first_dep)
        last_min = time_to_minutes(last_arr)
        if first_min is not None and last_min is not None:
            total_mins = last_min - first_min
            if total_mins < 0:
                total_mins += 1440
            total_journey = minutes_to_hhmm(total_mins)
        else:
            total_journey = "--"

        # ── METRIC CARDS ──
        st.markdown('<p class="section-header">📊 Live Statistics</p>', unsafe_allow_html=True)
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f'<div class="metric-card"><p class="metric-value">{len(stations_raw)}</p><p class="metric-label">Total Stations</p></div>', unsafe_allow_html=True)
        with m2:
            color = "#DC2626" if avg_delay > 15 else "#D97706" if avg_delay > 0 else "#16A34A"
            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color:{color}">{avg_delay} min</p><p class="metric-label">Avg Delay</p></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><p class="metric-value">{total_journey}</p><p class="metric-label">Total Journey</p></div>', unsafe_allow_html=True)
        with m4:
            last_name = last_known.get('stationName', '--') if last_known else '--'
            st.markdown(f'<div class="metric-card"><p class="metric-value" style="font-size:16px">{last_name}</p><p class="metric-label">Last Reported</p></div>', unsafe_allow_html=True)
        with m5:
            next_name = next_station.get('stationName', '--') if next_station else 'Destination'
            st.markdown(f'<div class="metric-card"><p class="metric-value" style="font-size:16px">{next_name}</p><p class="metric-label">Next Station</p></div>', unsafe_allow_html=True)

        # ── JOURNEY SUMMARY ──
        if first_station and last_station:
            st.markdown('<p class="section-header">🗺️ Journey Summary</p>', unsafe_allow_html=True)
            origin = first_station.get('stationName', '--')
            destination = last_station.get('stationName', '--')
            dep_time = first_station.get('departureTime', '--')
            arr_time = last_station.get('arrivalTime', '--')

            st.markdown(f"""
            <div class="journey-card">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:20px;">
                    <div style="text-align:center;">
                        <p style="font-size:13px; color:#6B7280; margin:0;">ORIGIN</p>
                        <p style="font-size:20px; font-weight:700; color:#1A56DB; margin:4px 0;">🟢 {origin}</p>
                        <p style="font-size:15px; color:#374151; margin:0;">Dep: <b>{dep_time}</b></p>
                    </div>
                    <div style="text-align:center; flex:1;">
                        <p style="font-size:13px; color:#9CA3AF; letter-spacing:2px;">━━━━━ 🚂 ━━━━━</p>
                        <p style="font-size:13px; color:#6B7280;">{total_journey}</p>
                    </div>
                    <div style="text-align:center;">
                        <p style="font-size:13px; color:#6B7280; margin:0;">DESTINATION</p>
                        <p style="font-size:20px; font-weight:700; color:#DC2626; margin:4px 0;">🔴 {destination}</p>
                        <p style="font-size:15px; color:#374151; margin:0;">Arr: <b>{arr_time}</b></p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── NEXT STATION ──
        if next_station and not terminated:
            stn_name = next_station.get('stationName', '--')
            stn_code = next_station.get('stationCode', next_station.get('stationcode', ''))
            scheduled_arr = next_station.get('arrivalTime', '--')
            signal = get_5g_signal(stn_code)

            st.markdown('<p class="section-header">⏱️ Next Station Details</p>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="metric-card"><p class="metric-value" style="font-size:18px">{stn_name}</p><p class="metric-label">Next Station</p></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><p class="metric-value">{scheduled_arr}</p><p class="metric-label">Scheduled Arrival</p></div>', unsafe_allow_html=True)
            with c3:
                delay_text = f"~{avg_delay} min late" if avg_delay > 0 else "On Time ✅"
                delay_color = "#DC2626" if avg_delay > 0 else "#16A34A"
                st.markdown(f'<div class="metric-card"><p class="metric-value" style="color:{delay_color}; font-size:18px">{delay_text}</p><p class="metric-label">Expected Status</p></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="metric-card"><p class="metric-value" style="font-size:18px">{signal}</p><p class="metric-label">5G Coverage</p></div>', unsafe_allow_html=True)

        # ── STATION TABLE ──
        st.markdown('<p class="section-header">📋 Station-wise Status</p>', unsafe_allow_html=True)

        table_data = []
        for s in stations_raw:
            scheduled = s.get('arrivalTime', '--')
            actual = s.get('actual_arrival_time', '--')
            stn_code = s.get('stationCode', s.get('stationcode', ''))
            delay = calculate_delay(scheduled, actual)

            if delay is None:
                status = "⏳ Upcoming"
                delay_str = "--"
            elif delay > 15:
                status = "🔴 Late"
                delay_str = f"+{delay} min"
            elif delay > 0:
                status = "🟡 Slight Delay"
                delay_str = f"+{delay} min"
            elif delay < 0:
                status = "🟢 Early"
                delay_str = f"{delay} min"
            else:
                status = "🟢 On Time"
                delay_str = "On Time"

            table_data.append({
                "Station": s.get('stationName', '--'),
                "Arr. Scheduled": scheduled,
                "Arr. Actual": actual,
                "Dep. Scheduled": s.get('departureTime', '--'),
                "Dep. Actual": s.get('actual_departure_time', '--'),
                "Delay": delay_str,
                "Status": status,
                "Dist. (km)": s.get('distance', '--'),
                "5G": get_5g_signal(stn_code)
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=420)

        st.markdown("""
            <p style='text-align:center; color:#9CA3AF; font-size:12px; margin-top:20px;'>
            © GoRail &nbsp;|&nbsp; Data from Indian Railways via RapidAPI &nbsp;|&nbsp; 5G coverage is indicative
            </p>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error("Something went wrong. Please try again.")
        st.json(data)
