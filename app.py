import streamlit as st
import requests
from datetime import datetime, timedelta
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
        return "🟢 Excellent 5G"
    elif score >= 70:
        return "🟡 Good 5G"
    elif score >= 55:
        return "🟠 Moderate 5G"
    else:
        return "🔴 Weak / No 5G"


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


st.set_page_config(page_title="Indian Railway Tracker", page_icon="🚂", layout="wide")

st.markdown("""
    <h1 style='text-align:center; color:#1A56DB;'>🚂 Indian Railway Live Train Tracker</h1>
    <p style='text-align:center; color:#555; font-size:18px;'>
    Real-time Status &nbsp;•&nbsp; Delay Prediction &nbsp;•&nbsp; ETA &nbsp;•&nbsp; 5G Coverage
    </p>
    <hr>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    train_number = st.text_input("🚆 Train Number", value="", placeholder="e.g. 12051")
with col2:
    selected_date = st.date_input("📅 Select Date", value=datetime.today())
    date = selected_date.strftime('%Y%m%d')
    display_date = selected_date.strftime('%d/%m/%Y')
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    search = st.button("🔍 Track Train", type="primary", use_container_width=True)

st.markdown(f"""
    <p style='text-align:right; color:#888; font-size:13px; margin-top:-10px;'>
    📅 Today: <b>{datetime.today().strftime('%d/%m/%Y')}</b>
    </p>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

if search:
    if not train_number:
        st.warning("⚠️ Please enter a Train Number first!")
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
            st.error("No data found. Please check train number and date.")
            st.stop()

        st.markdown(f"""
            <div style='background:#EEF3FB; padding:20px; border-radius:12px; margin-bottom:20px;'>
                <h2 style='color:#1A56DB; margin:0;'>🚆 {train_name}</h2>
                <p style='color:#555; margin:5px 0 0 0;'>
                Train No: <b>{train_number}</b> &nbsp;|&nbsp;
                Date: <b>{display_date}</b>
                </p>
            </div>
        """, unsafe_allow_html=True)

        if terminated:
            st.success("🏁 Train has reached its final destination!")
        elif current_stn_code:
            st.info(f"📍 Currently near: **{current_stn_code}**")

        delays = []
        last_known = None
        next_station = None
        first_station = stations_raw[0] if stations_raw else None
        last_station = stations_raw[-1] if stations_raw else None

        for s in stations_raw:
            actual = s.get('actual_arrival_time', '--')
            scheduled = s.get('arrivalTime', '--')
            delay = calculate_delay(scheduled, actual)
            if delay is not None:
                delays.append(delay)
                last_known = s
            elif next_station is None and last_known is not None:
                next_station = s

        avg_delay = round(sum(delays) / len(delays)) if delays else 0

        # Calculate total journey time
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

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🚉 Total Stations", len(stations_raw))
        m2.metric("⏱️ Avg Delay", f"{avg_delay} min")
        m3.metric("🕐 Total Journey", total_journey)
        if last_known:
            m4.metric("📍 Last Reported", last_known.get('stationName', '--'))
        if next_station:
            m5.metric("⏩ Next Station", next_station.get('stationName', '--'))

        st.markdown("<br>", unsafe_allow_html=True)

        # Journey summary
        if first_station and last_station:
            dep_time = first_station.get('departureTime', '--')
            arr_time = last_station.get('arrivalTime', '--')
            origin = first_station.get('stationName', '--')
            destination = last_station.get('stationName', '--')

            st.markdown("### 🗺️ Journey Summary")
            j1, j2, j3, j4 = st.columns(4)
            j1.metric("🟢 Origin", origin)
            j2.metric("🔴 Destination", destination)
            j3.metric("🕐 Departure", dep_time)
            j4.metric("🕐 Expected Arrival", arr_time)

        st.markdown("<br>", unsafe_allow_html=True)

        if next_station and not terminated:
            stn_name = next_station.get('stationName', '--')
            stn_code = next_station.get('stationCode', next_station.get('stationcode', ''))
            scheduled_arr = next_station.get('arrivalTime', '--')
            signal = get_5g_signal(stn_code)

            st.markdown("### ⏱️ Next Station Details")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🚉 Station", stn_name)
            c2.metric("📅 Scheduled Arrival", scheduled_arr)
            if avg_delay > 0:
                c3.metric("⚠️ Expected Delay", f"~{avg_delay} min late")
            else:
                c3.metric("✅ Status", "On Time")
            c4.metric("📶 5G Signal", signal)

        st.markdown("### 📋 Station-wise Status")

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
                "Distance (km)": s.get('distance', '--'),
                "5G Coverage": get_5g_signal(stn_code)
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=400)

        st.markdown("""
            <p style='text-align:center; color:#aaa; font-size:13px; margin-top:20px;'>
            Data from Indian Railways via RapidAPI &nbsp;|&nbsp; 5G coverage is indicative
            </p>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error("Something went wrong. Please try again.")
        st.json(data)
