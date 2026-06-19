import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure root folder is in path to import hotel_analytics_engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from hotel_analytics_engine import process_bookings, load_rooms, run_engine

# Page setup
st.set_page_config(
    page_title="Hotel Analytics Engine Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Font style overriding */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Dashboard main title */
    .dashboard-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* KPI Card layout */
    .kpi-card {
        padding: 18px;
        border-radius: 12px;
        background-color: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.12);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.01);
        transition: all 0.2s ease-in-out;
        margin-bottom: 12px;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
        border-color: rgba(128, 128, 128, 0.2);
    }
    
    .kpi-title {
        font-size: 0.8rem;
        color: #7c7c7c;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.75px;
        margin-bottom: 6px;
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: inherit;
        margin: 2px 0px;
    }
    
    .kpi-delta {
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 4px;
    }
    
    .kpi-icon {
        font-size: 1.4rem;
        float: right;
        margin-top: -4px;
    }

    /* KPI color borders */
    .kpi-bookings { border-left: 5px solid #3b82f6; }
    .kpi-revenue { border-left: 5px solid #10b981; }
    .kpi-occupancy { border-left: 5px solid #8b5cf6; }
    .kpi-cancelled { border-left: 5px solid #ef4444; }
    .kpi-active { border-left: 5px solid #06b6d4; }
    .kpi-risk { border-left: 5px solid #f97316; }

    /* Section Subheadings */
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        margin-top: 0.5rem;
        margin-bottom: 1.0rem;
        border-bottom: 2px solid rgba(128, 128, 128, 0.1);
        padding-bottom: 5px;
        color: #2b4c7e;
    }
    
    /* Search box highlight */
    .search-box-text {
        font-weight: bold;
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)


# Load data and cache it
@st.cache_data(ttl=600)
def get_cached_data():
    rooms_path = "hotel_rooms.csv"
    bookings_path = "hotel_bookings.csv"
    
    # Run processing engine
    booking_results, occupancy_rows, cancellation_analysis = process_bookings(rooms_path, bookings_path)
    rooms = load_rooms(rooms_path)
    
    # Process rooms into DataFrame
    rooms_records = []
    for r_id, r in rooms.items():
        rooms_records.append({
            "room_id": r.room_id,
            "room_type": r.room_type,
            "price_per_night": r.price_per_night,
            "room_status": r.room_status
        })
    df_rooms = pd.DataFrame(rooms_records)
    
    # Process booking results into DataFrame
    bookings_records = []
    for r in booking_results:
        bookings_records.append({
            "booking_id": r.booking_id,
            "room_id": r.room_id,
            "guest_id": r.guest_id,
            "checkin_date": r.checkin_date,
            "nights": r.nights,
            "booking_status": r.booking_status,
            "revenue": r.revenue,
            "error_message": r.error_message
        })
    df_bookings = pd.DataFrame(bookings_records)
    
    # Merge for complete information (contains room type, room status, price_per_night)
    # Perform left join to retain invalid room bookings
    df_bookings = df_bookings.merge(df_rooms, on="room_id", how="left")
    # Clean up empty values in merged room columns for invalid rooms
    df_bookings["room_type"] = df_bookings["room_type"].fillna("Invalid/Unknown")
    df_bookings["price_per_night"] = df_bookings["price_per_night"].fillna(0.0)
    df_bookings["room_status"] = df_bookings["room_status"].fillna("UNKNOWN")
    
    return df_bookings, df_rooms, cancellation_analysis

# Helper to clear cache (Manual Refresh)
def force_refresh_data():
    st.cache_data.clear()

# Load Data
df_bookings, df_rooms, raw_cancellation_analysis = get_cached_data()

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("<h2 style='margin-top:0px;'>🏨 Hotel Analytics</h2>", unsafe_allow_html=True)

# Navigation Menu
st.sidebar.markdown("### Navigation")
nav_options = {
    "Executive Overview (KPIs)": "📊",
    "Revenue Performance": "💸",
    "Room Occupancy Analytics": "🛌",
    "Booking Volume & Status": "📈",
    "Cancellation Risk Profiles": "⚠️",
    "Data Quality & Validation": "🔍"
}
selected_page = st.sidebar.radio(
    "Select Section",
    options=list(nav_options.keys()),
    format_func=lambda x: f"{nav_options[x]} {x}",
    label_visibility="collapsed"
)

# Auto Refresh Setting
auto_refresh = st.sidebar.toggle("Auto Refresh Data", value=False, help="Automatically reload browser view every 30s")
refresh_interval = 30
if auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="{refresh_interval}">', unsafe_allow_html=True)

# Search Box
st.sidebar.markdown("### 🔍 Global Search")
search_query = st.sidebar.text_input("Search Booking ID or Room ID", value="", placeholder="e.g. BK001, RM005").strip()

# Date range extraction
# Filter out invalid dates to find date boundary
df_valid_dates = df_bookings[(df_bookings["booking_status"] != "REJECTED") & (df_bookings["checkin_date"] != "invalid_date")].copy()
df_valid_dates["checkin_date"] = pd.to_datetime(df_valid_dates["checkin_date"])
min_date_val = df_valid_dates["checkin_date"].min()
max_date_val = df_valid_dates["checkin_date"].max()

st.sidebar.markdown("### 🛠️ Filters")

# Date range filter
selected_dates = st.sidebar.date_input(
    "Check-in Date Range",
    value=(min_date_val.date(), max_date_val.date()),
    min_value=min_date_val.date(),
    max_value=max_date_val.date()
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates[0]
    end_date = selected_dates[0]

# Room type filter
room_types = sorted(list(df_rooms["room_type"].unique()))
selected_room_types = st.sidebar.multiselect(
    "Room Type",
    options=room_types,
    default=room_types
)

# Booking status filter
booking_statuses = ["CONFIRMED", "CANCELLED", "REJECTED"]
selected_statuses = st.sidebar.multiselect(
    "Booking Status",
    options=booking_statuses,
    default=booking_statuses
)

# Revenue range filter
confirmed_revs = df_bookings[df_bookings["booking_status"] == "CONFIRMED"]["revenue"]
min_rev = float(confirmed_revs.min()) if not confirmed_revs.empty else 0.0
max_rev = float(confirmed_revs.max()) if not confirmed_revs.empty else 10000.0

selected_revenue = st.sidebar.slider(
    "Booking Revenue Range ($)",
    min_value=0.0,
    max_value=max_rev,
    value=(0.0, max_rev),
    step=100.0
)

# Clear/Reset filters button
if st.sidebar.button("Reset All Filters", use_container_width=True):
    st.rerun()

# ----------------- DRILL DOWN -----------------
# Drill down room type selection
drill_down_selection = st.sidebar.selectbox(
    "🎯 Drill-Down Room Type Focus",
    options=["No Drill-Down"] + room_types,
    index=0,
    help="Select a single room type to focus all visual analytics specifically on it."
)

# Apply filters
df_filtered = df_bookings.copy()

# Apply Search
if search_query:
    df_filtered = df_filtered[
        df_filtered["booking_id"].str.contains(search_query, case=False, na=False) |
        df_filtered["room_id"].str.contains(search_query, case=False, na=False)
    ]

# Apply Date Range (Only check for valid dates first, but keep invalid ones in backup for data quality view)
df_filtered_with_dates = df_filtered[df_filtered["checkin_date"] != "invalid_date"].copy()
df_filtered_with_dates["checkin_datetime"] = pd.to_datetime(df_filtered_with_dates["checkin_date"])
df_filtered_with_dates = df_filtered_with_dates[
    (df_filtered_with_dates["checkin_datetime"].dt.date >= start_date) &
    (df_filtered_with_dates["checkin_datetime"].dt.date <= end_date)
]

# Keep rejected dates from filtering if we filter by status and they don't have date,
# but for metric cards we strictly use date filters.
# To be robust:
df_filtered = df_filtered_with_dates.drop(columns=["checkin_datetime"])

# Apply Room Type Filter
df_filtered = df_filtered[df_filtered["room_type"].isin(selected_room_types)]

# Apply Drill Down Focus (overrides selection)
if drill_down_selection != "No Drill-Down":
    df_filtered = df_filtered[df_filtered["room_type"] == drill_down_selection]

# Apply Booking Status Filter
df_filtered = df_filtered[df_filtered["booking_status"].isin(selected_statuses)]

# Apply Revenue Filter (only affects confirmed bookings or all bookings within budget)
# If bookings are CANCELLED or REJECTED they have 0 revenue, so they fit in range if min_revenue is 0.
df_filtered = df_filtered[
    (df_filtered["revenue"] >= selected_revenue[0]) &
    (df_filtered["revenue"] <= selected_revenue[1])
]

# ----------------- MAIN PANEL HEADER -----------------
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<div class="dashboard-title">Hotel Booking Revenue & Occupancy Analytics</div>', unsafe_allow_html=True)
    st.markdown(f"**Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} | **Room Focus:** {drill_down_selection if drill_down_selection != 'No Drill-Down' else 'All'}")
with col_status:
    # Refresh button
    if st.button("🔄 Force Data Refresh", use_container_width=True):
        force_refresh_data()
        st.toast("Data Refreshed from Source CSV Files!")
        st.rerun()

# Drill down indicator
if drill_down_selection != "No Drill-Down":
    st.info(f"🎯 **Drill-down active**: Displaying data exclusively for **{drill_down_selection}** rooms.")

if search_query:
    st.warning(f"🔍 **Search Query Active**: Filtering records matching '**{search_query}**'")

# ----------------- COMMON CALCULATIONS (needed across sections) -----------------
# Trend calculations for delta values (Comparing Second Half of selected period with First Half)
period_days = (end_date - start_date).days + 1
mid_point = start_date + pd.Timedelta(days=period_days // 2)

df_h1 = df_bookings[(df_bookings["booking_status"] != "REJECTED") & (df_bookings["checkin_date"] != "invalid_date")].copy()
df_h1["checkin_dt"] = pd.to_datetime(df_h1["checkin_date"]).dt.date
df_h2 = df_h1.copy()

# Filter by selected rooms
df_h1 = df_h1[df_h1["room_type"].isin(selected_room_types)]
df_h2 = df_h2[df_h2["room_type"].isin(selected_room_types)]
if drill_down_selection != "No Drill-Down":
    df_h1 = df_h1[df_h1["room_type"] == drill_down_selection]
    df_h2 = df_h2[df_h2["room_type"] == drill_down_selection]

df_h1 = df_h1[(df_h1["checkin_dt"] >= start_date) & (df_h1["checkin_dt"] < mid_point)]
df_h2 = df_h2[(df_h2["checkin_dt"] >= mid_point) & (df_h2["checkin_dt"] <= end_date)]

# Calculate metric values for filtered set
total_bookings = len(df_filtered)
total_revenue = df_filtered[df_filtered["booking_status"] == "CONFIRMED"]["revenue"].sum()
total_cancelled = len(df_filtered[df_filtered["booking_status"] == "CANCELLED"])

# Occupancy calculation:
# For the selected filtered dates, sum of occupied nights of confirmed bookings / total room nights
active_rooms_subset = df_rooms[df_rooms["room_status"] != "MAINTENANCE"]
if drill_down_selection != "No Drill-Down":
    rooms_for_occ = active_rooms_subset[active_rooms_subset["room_type"] == drill_down_selection]
else:
    rooms_for_occ = active_rooms_subset[active_rooms_subset["room_type"].isin(selected_room_types)]
    
total_active_rooms_count = len(rooms_for_occ)
available_room_nights = total_active_rooms_count * period_days

occupied_nights_filtered = df_filtered[df_filtered["booking_status"] == "CONFIRMED"]["nights"].sum()
overall_occupancy_rate = (occupied_nights_filtered / available_room_nights * 100) if available_room_nights > 0 else 0.0
overall_occupancy_rate = min(overall_occupancy_rate, 100.0) # Clip to 100% max

# Risk rooms calculations
# Flag rooms with cancellations > 3 in the filtered bookings
cancellations_by_room_filtered = df_filtered[df_filtered["booking_status"] == "CANCELLED"].groupby("room_id").size()
high_risk_rooms_count = sum(cancellations_by_room_filtered > 3)

# Deltas
bookings_h1 = len(df_h1)
bookings_h2 = len(df_h2)
bookings_change = ((bookings_h2 - bookings_h1) / bookings_h1 * 100) if bookings_h1 > 0 else 0.0

rev_h1 = df_h1[df_h1["booking_status"] == "CONFIRMED"]["revenue"].sum()
rev_h2 = df_h2[df_h2["booking_status"] == "CONFIRMED"]["revenue"].sum()
rev_change = ((rev_h2 - rev_h1) / rev_h1 * 100) if rev_h1 > 0 else 0.0

cancellations_h1 = len(df_h1[df_h1["booking_status"] == "CANCELLED"])
cancellations_h2 = len(df_h2[df_h2["booking_status"] == "CANCELLED"])
cancellations_change = ((cancellations_h2 - cancellations_h1) / cancellations_h1 * 100) if cancellations_h1 > 0 else 0.0

occ_h1_nights = df_h1[df_h1["booking_status"] == "CONFIRMED"]["nights"].sum()
occ_h2_nights = df_h2[df_h2["booking_status"] == "CONFIRMED"]["nights"].sum()
days_h1 = (mid_point - start_date).days
days_h2 = (end_date - mid_point).days + 1
occ_h1 = (occ_h1_nights / (total_active_rooms_count * days_h1) * 100) if (total_active_rooms_count * days_h1) > 0 else 0.0
occ_h2 = (occ_h2_nights / (total_active_rooms_count * days_h2) * 100) if (total_active_rooms_count * days_h2) > 0 else 0.0
occ_change = occ_h2 - occ_h1 # Direct rate point difference

def render_kpi_card(title, value, icon, delta_val, border_class, prefix="", suffix="", is_delta_percentage=True):
    delta_str = ""
    delta_color = "gray"
    if delta_val is not None:
        sign = "+" if delta_val > 0 else ""
        symbol = "%" if is_delta_percentage else " pts"
        delta_str = f"{sign}{delta_val:.1f}{symbol} vs H1"
        delta_color = "green" if delta_val >= 0 else "red"
        # Cancellations going up is bad (red)
        if "Cancelled" in title and delta_val > 0:
            delta_color = "red"
        elif "Cancelled" in title and delta_val < 0:
            delta_color = "green"
            
    delta_style = f"color: {'#10b981' if delta_color == 'green' else '#ef4444'};"
    
    st.markdown(f"""
    <div class="kpi-card {border_class}">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{prefix}{value}{suffix}</div>
        <div class="kpi-delta" style="{delta_style}">{delta_str}</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- SECTION PAGES RENDERING -----------------

if selected_page == "Executive Overview (KPIs)":
    st.markdown('<div class="section-header">📊 Executive Overview & KPIs</div>', unsafe_allow_html=True)
    
    # Render KPI Columns
    cols = st.columns(6)
    with cols[0]:
        render_kpi_card("Total Bookings", f"{total_bookings}", "📅", bookings_change, "kpi-bookings")
    with cols[1]:
        render_kpi_card("Total Revenue", f"{total_revenue:,.0f}", "💰", rev_change, "kpi-revenue", prefix="$")
    with cols[2]:
        render_kpi_card("Occupancy Rate", f"{overall_occupancy_rate:.1f}", "📈", occ_change, "kpi-occupancy", suffix="%", is_delta_percentage=False)
    with cols[3]:
        render_kpi_card("Total Cancelled", f"{total_cancelled}", "❌", cancellations_change, "kpi-cancelled")
    with cols[4]:
        render_kpi_card("Active Rooms", f"{total_active_rooms_count}", "🔑", None, "kpi-active")
    with cols[5]:
        render_kpi_card("Risk Rooms (>3 Cancels)", f"{high_risk_rooms_count}", "⚠️", None, "kpi-risk")
        
    st.markdown("### Quick Insights")
    st.info("""
    - Change global filters like check-in dates, room types, status and revenue range to see KPIs update instantly.
    - Check the **Data Quality & Validation** page for issues flagged by the analytical engine (e.g. invalid dates, negative night values).
    """)

elif selected_page == "Revenue Performance":
    st.markdown('<div class="section-header">💸 Revenue Performance Analytics</div>', unsafe_allow_html=True)
    col_rev1, col_rev2, col_rev3 = st.columns([2, 1.2, 1.2])
    
    # Prepare Daily Revenue data
    df_confirmed_only = df_filtered[df_filtered["booking_status"] == "CONFIRMED"].copy()
    if not df_confirmed_only.empty:
        df_confirmed_only["checkin_date"] = pd.to_datetime(df_confirmed_only["checkin_date"])
        
        # Fill in complete dates in range
        all_dates = pd.date_range(start_date, end_date)
        df_daily_rev = df_confirmed_only.groupby("checkin_date")["revenue"].sum().reset_index()
        df_daily_rev = pd.DataFrame({"checkin_date": all_dates}).merge(df_daily_rev, on="checkin_date", how="left").fillna(0.0)
        
        df_daily_rev["Cumulative Revenue"] = df_daily_rev["revenue"].cumsum()
        df_daily_rev = df_daily_rev.rename(columns={"revenue": "Daily Revenue", "checkin_date": "Date"})
    else:
        df_daily_rev = pd.DataFrame(columns=["Date", "Daily Revenue", "Cumulative Revenue"])

    with col_rev1:
        st.markdown("##### Revenue Trend Over Time")
        trend_type = st.radio("Aggregation Level", options=["Daily", "Cumulative"], horizontal=True, key="rev_trend_select")
        
        if not df_daily_rev.empty:
            fig_rev_trend = px.line(
                df_daily_rev,
                x="Date",
                y=f"{trend_type} Revenue",
                template="plotly_white",
                color_discrete_sequence=["#10b981"]
            )
            # Beautify chart
            fig_rev_trend.update_traces(mode='lines+markers', line=dict(width=3, shape='spline'))
            fig_rev_trend.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=10, b=10),
                hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickprefix="$"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_rev_trend, use_container_width=True)
        else:
            st.info("No confirmed bookings found for the selected filters.")

    with col_rev2:
        st.markdown("##### Revenue by Room Type")
        if not df_confirmed_only.empty:
            df_rev_by_type = df_confirmed_only.groupby("room_type")["revenue"].sum().reset_index()
            fig_rev_bar = px.bar(
                df_rev_by_type,
                x="room_type",
                y="revenue",
                color="room_type",
                color_discrete_map={"DELUXE": "#3b82f6", "SUITE": "#8b5cf6", "STANDARD": "#06b6d4"},
                labels={"room_type": "Room Type", "revenue": "Revenue ($)"},
                template="plotly_white"
            )
            fig_rev_bar.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", tickprefix="$"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_rev_bar, use_container_width=True)
        else:
            st.info("No confirmed bookings.")

    with col_rev3:
        st.markdown("##### Revenue Contribution")
        if not df_confirmed_only.empty:
            df_rev_pie = df_confirmed_only.groupby("room_type")["revenue"].sum().reset_index()
            fig_rev_pie = px.pie(
                df_rev_pie,
                values="revenue",
                names="room_type",
                hole=0.5,
                color="room_type",
                color_discrete_map={"DELUXE": "#3b82f6", "SUITE": "#8b5cf6", "STANDARD": "#06b6d4"},
                template="plotly_white"
            )
            fig_rev_pie.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_rev_pie, use_container_width=True)
        else:
            st.info("No confirmed bookings.")

elif selected_page == "Room Occupancy Analytics":
    st.markdown('<div class="section-header">🛌 Room Occupancy Analytics</div>', unsafe_allow_html=True)
    col_occ1, col_occ2, col_occ3 = st.columns([1.2, 1, 1.8])
    
    # Calculate occupancy rate calculations per room type
    occ_summary = []
    for rt in selected_room_types:
        df_rt = df_filtered[df_filtered["room_type"] == rt]
        occupied_nights_rt = df_rt[df_rt["booking_status"] == "CONFIRMED"]["nights"].sum()
        total_rooms_rt = df_rooms[(df_rooms["room_type"] == rt) & (df_rooms["room_status"] == "AVAILABLE")].shape[0]
        avail_nights_rt = total_rooms_rt * period_days
        rate = (occupied_nights_rt / avail_nights_rt * 100) if avail_nights_rt > 0 else 0.0
        occ_summary.append({"Room Type": rt, "Occupancy Rate (%)": min(rate, 100.0)})
        
    df_occ_summary = pd.DataFrame(occ_summary)

    with col_occ1:
        st.markdown("##### Occupancy by Room Type")
        if not df_occ_summary.empty:
            fig_occ_bar = px.bar(
                df_occ_summary,
                y="Room Type",
                x="Occupancy Rate (%)",
                orientation="h",
                color="Room Type",
                color_discrete_map={"DELUXE": "#3b82f6", "SUITE": "#8b5cf6", "STANDARD": "#06b6d4"},
                text_auto=".1f",
                template="plotly_white"
            )
            fig_occ_bar.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", range=[0, 100]),
                yaxis=dict(showgrid=False),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_occ_bar, use_container_width=True)
        else:
            st.info("No occupancy data.")

    with col_occ2:
        st.markdown("##### Utilization Gauge")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_occupancy_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#7c7c7c"},
                'bar': {'color': "#8b5cf6"},
                'bgcolor': "rgba(0,0,0,0.02)",
                'borderwidth': 1,
                'bordercolor': "rgba(128,128,128,0.2)",
                'steps': [
                    {'range': [0, 30], 'color': 'rgba(239, 68, 68, 0.15)'},     # Red
                    {'range': [30, 70], 'color': 'rgba(245, 158, 11, 0.15)'},   # Yellow
                    {'range': [70, 100], 'color': 'rgba(16, 185, 129, 0.15)'}   # Green
                ],
                'threshold': {
                    'line': {'color': "#b91c1c", 'width': 3},
                    'thickness': 0.75,
                    'value': 90.0
                }
            }
        ))
        fig_gauge.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="gray")
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_occ3:
        st.markdown("##### Occupancy Pattern Heatmap")
        
        # Calculate daily occupied nights in range
        daily_occ_records = []
        df_confirmed_only = df_filtered[df_filtered["booking_status"] == "CONFIRMED"].copy()
        for _, row in df_confirmed_only.iterrows():
            try:
                ch_date = pd.to_datetime(row["checkin_date"])
                nights_count = int(row["nights"])
                for offset in range(nights_count):
                    daily_occ_records.append({"date": ch_date + pd.Timedelta(days=offset)})
            except Exception:
                pass
                
        df_daily_occ = pd.DataFrame(daily_occ_records)
        
        if not df_daily_occ.empty:
            df_daily_grouped = df_daily_occ.groupby("date").size().reset_index(name="occupied_rooms")
            all_dates = pd.date_range(start_date, end_date)
            df_heatmap_data = pd.DataFrame({"date": all_dates}).merge(df_daily_grouped, on="date", how="left").fillna(0.0)
            
            # Calculate rates
            df_heatmap_data["Occupancy %"] = (df_heatmap_data["occupied_rooms"] / total_active_rooms_count * 100) if total_active_rooms_count > 0 else 0.0
            df_heatmap_data["Occupancy %"] = df_heatmap_data["Occupancy %"].clip(upper=100.0)
            
            # Date parts for pivot
            df_heatmap_data["Day of Week"] = df_heatmap_data["date"].dt.day_name()
            day_order_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            df_heatmap_data["Day of Week"] = pd.Categorical(df_heatmap_data["Day of Week"], categories=day_order_list, ordered=True)
            
            # Format week starts
            df_heatmap_data["Week Start"] = df_heatmap_data["date"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")
            
            df_pivot = df_heatmap_data.pivot(index="Day of Week", columns="Week Start", values="Occupancy %").fillna(0.0)
            df_pivot = df_pivot.reindex(day_order_list)
            
            fig_heat = px.imshow(
                df_pivot,
                labels=dict(x="Week Commencing", y="Day of Week", color="Occupancy %"),
                x=df_pivot.columns,
                y=df_pivot.index,
                color_continuous_scale="Purples",
                text_auto=".0f",
                template="plotly_white"
            )
            fig_heat.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("No confirmed bookings to generate a heatmap.")

elif selected_page == "Booking Volume & Status":
    st.markdown('<div class="section-header">📊 Booking Volume & Dynamics</div>', unsafe_allow_html=True)
    col_bk1, col_bk2, col_bk3 = st.columns([1, 1.8, 1.8])

    with col_bk1:
        st.markdown("##### Booking Status Distribution")
        status_counts = df_filtered["booking_status"].value_counts().reset_index()
        
        if not status_counts.empty:
            fig_status = px.pie(
                status_counts,
                values="count",
                names="booking_status",
                color="booking_status",
                color_discrete_map={"CONFIRMED": "#10b981", "CANCELLED": "#ef4444", "REJECTED": "#6b7280"},
                template="plotly_white",
                hole=0.4
            )
            fig_status.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No bookings match filters.")

    with col_bk2:
        st.markdown("##### Cumulative Booking Volume")
        df_vol = df_filtered[df_filtered["booking_status"] != "REJECTED"].copy()
        
        if not df_vol.empty:
            df_vol["checkin_date"] = pd.to_datetime(df_vol["checkin_date"])
            all_dates = pd.date_range(start_date, end_date)
            
            df_daily_vol = df_vol.groupby("checkin_date").size().reset_index(name="bookings")
            df_daily_vol = pd.DataFrame({"checkin_date": all_dates}).merge(df_daily_vol, on="checkin_date", how="left").fillna(0)
            df_daily_vol["Cumulative Bookings"] = df_daily_vol["bookings"].cumsum()
            
            fig_vol = px.area(
                df_daily_vol,
                x="checkin_date",
                y="Cumulative Bookings",
                template="plotly_white",
                color_discrete_sequence=["rgba(59, 130, 246, 0.4)"]
            )
            fig_vol.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.info("No valid bookings in selected range.")

    with col_bk3:
        st.markdown("##### Daily Check-in Trend")
        df_vol = df_filtered[df_filtered["booking_status"] != "REJECTED"].copy()
        if not df_vol.empty:
            df_trends = df_vol.groupby(["checkin_date", "booking_status"]).size().reset_index(name="bookings_count")
            df_trends["checkin_date"] = pd.to_datetime(df_trends["checkin_date"])
            
            # Build master dataframe containing all dates
            all_dates = pd.date_range(start_date, end_date)
            template_records = []
            for d in all_dates:
                for s in ["CONFIRMED", "CANCELLED"]:
                    template_records.append({"checkin_date": d, "booking_status": s})
            df_template = pd.DataFrame(template_records)
            df_trends_filled = df_template.merge(df_trends, on=["checkin_date", "booking_status"], how="left").fillna(0)
            
            fig_trends = px.line(
                df_trends_filled,
                x="checkin_date",
                y="bookings_count",
                color="booking_status",
                color_discrete_map={"CONFIRMED": "#10b981", "CANCELLED": "#ef4444"},
                template="plotly_white"
            )
            fig_trends.update_traces(line=dict(width=2, shape='spline'))
            fig_trends.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_trends, use_container_width=True)
        else:
            st.info("No valid bookings in selected range.")

elif selected_page == "Cancellation Risk Profiles":
    st.markdown('<div class="section-header">⚠️ Cancellation & Risk Analytics</div>', unsafe_allow_html=True)
    col_can1, col_can2, col_can3 = st.columns([1.5, 1.5, 2])

    with col_can1:
        st.markdown("##### Cancellation Rate by Room Type")
        df_c_valid = df_filtered[df_filtered["booking_status"].isin(["CONFIRMED", "CANCELLED"])]
        if not df_c_valid.empty:
            c_rates = []
            for rt in selected_room_types:
                df_rt = df_c_valid[df_c_valid["room_type"] == rt]
                total = len(df_rt)
                cancels = len(df_rt[df_rt["booking_status"] == "CANCELLED"])
                rate = (cancels / total * 100) if total > 0 else 0.0
                c_rates.append({"Room Type": rt, "Cancellation Rate (%)": rate})
            df_c_rates = pd.DataFrame(c_rates)
            
            fig_crate = px.bar(
                df_c_rates,
                x="Room Type",
                y="Cancellation Rate (%)",
                color="Room Type",
                color_discrete_map={"DELUXE": "#3b82f6", "SUITE": "#8b5cf6", "STANDARD": "#06b6d4"},
                text_auto=".1f",
                template="plotly_white"
            )
            fig_crate.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", range=[0, 100]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_crate, use_container_width=True)
        else:
            st.info("No bookings records found to calculate rates.")

    with col_can2:
        st.markdown("##### Cancellation Volume Trend")
        df_cancels_only = df_filtered[df_filtered["booking_status"] == "CANCELLED"].copy()
        if not df_cancels_only.empty:
            df_cancels_only["checkin_date"] = pd.to_datetime(df_cancels_only["checkin_date"])
            all_dates = pd.date_range(start_date, end_date)
            
            df_daily_cancels = df_cancels_only.groupby("checkin_date").size().reset_index(name="cancellations")
            df_daily_cancels = pd.DataFrame({"checkin_date": all_dates}).merge(df_daily_cancels, on="checkin_date", how="left").fillna(0)
            
            fig_ctrend = px.line(
                df_daily_cancels,
                x="checkin_date",
                y="cancellations",
                template="plotly_white",
                color_discrete_sequence=["#ef4444"]
            )
            fig_ctrend.update_traces(mode='lines+markers', line=dict(width=2, shape='spline'))
            fig_ctrend.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_ctrend, use_container_width=True)
        else:
            st.info("No cancellations recorded in this range.")

    with col_can3:
        st.markdown("##### Room Cancellation Risk Table")
        df_cancels_all = df_bookings[df_bookings["booking_status"] == "CANCELLED"].groupby("room_id").size().reset_index(name="cancellations")
        df_risk = df_rooms[["room_id", "room_type"]].merge(df_cancels_all, on="room_id", how="left").fillna(0)
        df_risk["cancellations"] = df_risk["cancellations"].astype(int)
        
        def get_risk_cat(c):
            if c > 3:
                return "High Risk"
            elif c >= 1:
                return "Moderate Risk"
            return "Safe"
            
        df_risk["Risk Level"] = df_risk["cancellations"].apply(get_risk_cat)
        df_risk = df_risk.rename(columns={
            "room_id": "Room ID",
            "room_type": "Room Type",
            "cancellations": "Cancellation Count"
        })
        
        df_risk_filtered = df_risk[df_risk["Room Type"].isin(selected_room_types)]
        if drill_down_selection != "No Drill-Down":
            df_risk_filtered = df_risk_filtered[df_risk_filtered["Room Type"] == drill_down_selection]
            
        df_risk_filtered = df_risk_filtered.sort_values(by="Cancellation Count", ascending=False).reset_index(drop=True)
        
        def style_risk_cells(val):
            if val == "High Risk":
                return "background-color: rgba(239, 68, 68, 0.15); color: #b91c1c; font-weight: 600;"
            elif val == "Moderate Risk":
                return "background-color: rgba(245, 158, 11, 0.15); color: #b45309; font-weight: 500;"
            elif val == "Safe":
                return "background-color: rgba(16, 185, 129, 0.15); color: #047857;"
            return ""
            
        styled_risk_df = df_risk_filtered.style.map(style_risk_cells, subset=["Risk Level"])
        st.dataframe(styled_risk_df, use_container_width=True, height=230)
        
        # Export options
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        with col_exp1:
            st.download_button(
                "Export Table as CSV",
                data=df_risk_filtered.to_csv(index=False),
                file_name="cancellation_risk_table.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp2:
            st.download_button(
                "Export Table as JSON",
                data=df_risk_filtered.to_json(orient="records", indent=2),
                file_name="cancellation_risk_table.json",
                mime="application/json",
                use_container_width=True
            )
        with col_exp3:
            try:
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_risk_filtered.to_excel(writer, index=False, sheet_name='Risk Table')
                st.download_button(
                    "Export Table as Excel",
                    data=buffer.getvalue(),
                    file_name="cancellation_risk_table.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception:
                st.write("Excel export unavailable")

elif selected_page == "Data Quality & Validation":
    st.markdown('<div class="section-header">🔍 Data Quality & Engine Validation Summary</div>', unsafe_allow_html=True)
    col_val1, col_val2 = st.columns([1.5, 2.5])

    df_all_bookings = df_bookings.copy()
    df_rejected = df_all_bookings[df_all_bookings["booking_status"] == "REJECTED"].copy()

    # Counts
    invalid_room_ids_count = df_rejected[df_rejected["error_message"].str.contains("Room does not exist", na=False)].shape[0]
    maintenance_conflict_count = df_rejected[df_rejected["error_message"].str.contains("Room is under maintenance", na=False)].shape[0]
    invalid_dates_count = df_rejected[df_rejected["error_message"].str.contains("Invalid checkin_date", na=False)].shape[0]
    negative_nights_count = df_rejected[df_rejected["error_message"].str.contains("nights must be greater than 0", na=False)].shape[0]

    with col_val1:
        st.markdown("##### Validation Metrics")
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div style="padding: 12px; background: rgba(239, 68, 68, 0.08); border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.2); text-align: center;">
                <div style="font-size: 0.8rem; color: #b91c1c; font-weight: 600; text-transform: uppercase;">Invalid Room IDs</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #b91c1c; margin-top: 4px;">{invalid_room_ids_count}</div>
            </div>
            <div style="padding: 12px; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border: 1px solid rgba(245, 158, 11, 0.2); text-align: center;">
                <div style="font-size: 0.8rem; color: #b45309; font-weight: 600; text-transform: uppercase;">Maintenance Blocks</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #b45309; margin-top: 4px;">{maintenance_conflict_count}</div>
            </div>
            <div style="padding: 12px; background: rgba(59, 130, 246, 0.08); border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2); text-align: center;">
                <div style="font-size: 0.8rem; color: #1d4ed8; font-weight: 600; text-transform: uppercase;">Invalid Dates</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #1d4ed8; margin-top: 4px;">{invalid_dates_count}</div>
            </div>
            <div style="padding: 12px; background: rgba(107, 114, 128, 0.08); border-radius: 8px; border: 1px solid rgba(107, 114, 128, 0.2); text-align: center;">
                <div style="font-size: 0.8rem; color: #374151; font-weight: 600; text-transform: uppercase;">Negative Nights</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #374151; margin-top: 4px;">{negative_nights_count}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.info("💡 **Engine Rules Alert**: Confirmed and Cancelled bookings must pass all validation checks. Rejected bookings are automatically given zero revenue and logged.")

    with col_val2:
        st.markdown("##### Validation Error Table")
        def map_validation_error_type(msg):
            if "Room does not exist" in msg:
                return "Missing Room ID"
            elif "Room is under maintenance" in msg:
                return "Room Under Maintenance"
            elif "Invalid checkin_date" in msg:
                return "Invalid Ingest Date"
            elif "nights must be greater than 0" in msg:
                return "Negative/Zero Nights"
            return "Unknown Validation Failure"
            
        df_rejected["Error Type"] = df_rejected["error_message"].apply(map_validation_error_type)
        
        df_rejected_table = df_rejected[["booking_id", "room_id", "guest_id", "Error Type", "error_message"]].rename(columns={
            "booking_id": "Booking ID",
            "room_id": "Room ID",
            "guest_id": "Guest ID",
            "error_message": "Validation Details"
        }).reset_index(drop=True)
        
        st.dataframe(df_rejected_table, use_container_width=True, height=180)

# ----------------- REPORTS DOWNLOADING (GLOBAL SIDEBAR BUTTONS) -----------------
st.sidebar.markdown("### 📥 Download Reports")

# Precalculate default occupancy list for room summary report download
occ_summary_download = []
for rt in room_types:
    df_rt = df_filtered[df_filtered["room_type"] == rt]
    total = len(df_rt)
    occupied_nights_rt = df_rt[df_rt["booking_status"] == "CONFIRMED"]["nights"].sum()
    total_rooms_rt = df_rooms[(df_rooms["room_type"] == rt) & (df_rooms["room_status"] == "AVAILABLE")].shape[0]
    avail_nights_rt = total_rooms_rt * period_days
    rate = (occupied_nights_rt / avail_nights_rt * 100) if avail_nights_rt > 0 else 0.0
    occ_summary_download.append({
        "Room Type": rt,
        "Occupancy Rate (%)": round(min(rate, 100.0), 2),
        "Total Bookings": total
    })
df_occ_summary_dl = pd.DataFrame(occ_summary_download)

# Report 1: booking_revenue_report.csv
df_rep_rev = df_filtered[["booking_id", "room_id", "revenue", "booking_status"]].rename(columns={
    "booking_id": "Booking ID",
    "room_id": "Room ID",
    "revenue": "Revenue",
    "booking_status": "Status"
})

st.sidebar.download_button(
    "booking_revenue_report.csv",
    data=df_rep_rev.to_csv(index=False),
    file_name="booking_revenue_report.csv",
    mime="text/csv",
    use_container_width=True,
    help="Download report containing Booking ID, Room ID, Revenue, and Status."
)

# Report 2: room_occupancy_summary.csv
df_rep_occ = df_occ_summary_dl.rename(columns={
    "Room Type": "Room Type",
    "Occupancy Rate (%)": "Occupancy %",
    "Total Bookings": "Total Bookings"
})

st.sidebar.download_button(
    "room_occupancy_summary.csv",
    data=df_rep_occ.to_csv(index=False),
    file_name="room_occupancy_summary.csv",
    mime="text/csv",
    use_container_width=True,
    help="Download report containing Room Type, Occupancy %, and Total Bookings."
)

# Report 3: cancellation_analysis.json
# Compute risk analysis values for report download
df_cancels_dl = df_bookings[df_bookings["booking_status"] == "CANCELLED"].groupby("room_id").size().reset_index(name="cancellations")
df_risk_dl = df_rooms[["room_id", "room_type"]].merge(df_cancels_dl, on="room_id", how="left").fillna(0)
df_risk_dl["cancellations"] = df_risk_dl["cancellations"].astype(int)

def get_risk_cat_dl(c):
    if c > 3:
        return "High Risk"
    elif c >= 1:
        return "Moderate Risk"
    return "Safe"
df_risk_dl["Risk Category"] = df_risk_dl["cancellations"].apply(get_risk_cat_dl)
df_rep_cancel = df_risk_dl[["room_id", "cancellations", "Risk Category"]].rename(columns={
    "room_id": "Room ID",
    "cancellations": "Cancellation Count",
    "Risk Category": "Risk Category"
})

st.sidebar.download_button(
    "cancellation_analysis.json",
    data=df_rep_cancel.to_json(orient="records", indent=2),
    file_name="cancellation_analysis.json",
    mime="application/json",
    use_container_width=True,
    help="Download report containing Room ID, Cancellation Count, and Risk Category."
)

st.sidebar.markdown("---")
st.sidebar.caption("Hotel Analytics Dashboard v1.1.0 | Design: Premium Enterprise Style")
