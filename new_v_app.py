import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static, st_folium

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv("ais_data.csv")  # Replace with your actual file
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")  # Convert Timestamp
    df = df.dropna(subset=["Timestamp", "Latitude", "Longitude"])  # Remove NaN values
    return df

df = load_data()

# App UI
st.title("🚢 Vessel Tracking App")

# Sidebar Filters
st.sidebar.header("Filter Options")

# Select MMSI
mmsi_list = df["MMSI"].unique()
mmsi_number = st.sidebar.selectbox("Select MMSI Number", mmsi_list)

# Filter by MMSI
vessel_data = df[df["MMSI"] == mmsi_number]

# Time Range Filter
if not vessel_data.empty:
    min_date = vessel_data["Timestamp"].min().date()
    max_date = vessel_data["Timestamp"].max().date()

    if min_date == max_date:  # Prevents RangeError
        st.sidebar.warning("Only one timestamp available, showing full data.")
        date_range = (min_date, max_date)
    else:
        date_range = st.sidebar.slider(
            "Select Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM-DD"
        )

    # Apply Date Filter
    vessel_data = vessel_data[
        (vessel_data["Timestamp"].dt.date >= date_range[0]) &
        (vessel_data["Timestamp"].dt.date <= date_range[1])
    ]

    # Display Filtered Data
    st.write(f"📊 Showing data for vessel: **{mmsi_number}**")
    st.dataframe(vessel_data)

    # Create Map
    if not vessel_data.empty:
        m = folium.Map(
            location=[vessel_data["Latitude"].mean(), vessel_data["Longitude"].mean()],
            zoom_start=8
        )

        # Polyline for movement path
        points = list(zip(vessel_data["Latitude"], vessel_data["Longitude"]))
        folium.PolyLine(points, color="red", weight=2.5, opacity=1).add_to(m)

        # Start & End markers
        folium.Marker(points[0], icon=folium.Icon(color="green"), popup="Start Point").add_to(m)
        folium.Marker(points[-1], icon=folium.Icon(color="blue"), popup="End Point").add_to(m)

        # Abnormal Detection (Speed > 20 knots or Sudden Course Change > 45°)
        vessel_data["Speed"] = vessel_data["Speed"].fillna(0)  # Handle NaN speed values
        vessel_data["Course_Change"] = vessel_data["Course"].diff().fillna(0).abs()

        for _, row in vessel_data.iterrows():
            abnormal = (row["Speed"] > 20) or (row["Course_Change"] > 45)
            color = "red" if abnormal else "gray"
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                popup=f"Time: {row['Timestamp']}<br>Speed: {row['Speed']} knots<br>Course: {row['Course']}°",
                tooltip="⚠ Abnormal" if abnormal else "🛳 Normal"
            ).add_to(m)

        # Show Map
        folium_static(m)
    else:
        st.warning("No data available for the selected time range.")

else:
    st.warning("No data found for the selected MMSI.")

# CSV Download
if not vessel_data.empty:
    csv = vessel_data.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Download Filtered Data", data=csv, file_name="filtered_ais_data.csv", mime="text/csv")
