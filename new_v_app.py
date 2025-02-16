import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Streamlit page config
st.set_page_config(layout="wide")

st.title("🚢 Vessel Movement Tracker")

# Upload CSV file
uploaded_file = st.file_uploader("📂 Upload CSV file", type=["csv"])

# Define navigation status codes
NAVIGATION_STATUS = {
    0: "Under way using engine",
    1: "At anchor",
    2: "Not under command",
    3: "Restricted maneuverability",
    4: "Constrained by her draft",
    5: "Moored",
    6: "Aground",
    7: "Engaged in fishing",
    8: "Under way sailing",
    9: "Reserved for future use",
    10: "Reserved for future use",
    11: "Power-driven vessel towing astern",
    12: "Power-driven vessel pushing ahead",
    13: "Reserved for future use",
    14: "AIS-SART (Search and Rescue)",
    15: "Undefined"
}

# Sidebar for Navigation Status Codes
with st.sidebar:
    st.subheader("📜 Navigation Status Codes")
    for code, meaning in NAVIGATION_STATUS.items():
        st.write(f"**{code}:** {meaning}")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Ensure required columns exist
    required_cols = {"MMSI", "Latitude", "Longitude", "Timestamp", "Navigation Status"}
    if not required_cols.issubset(df.columns):
        st.error(f"CSV must contain: {required_cols}")
    else:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit='s')
        df["Navigation Status"] = df["Navigation Status"].map(NAVIGATION_STATUS)

        unique_mmsi = df["MMSI"].unique()
        selected_mmsi = st.selectbox("🚢 Select MMSI Number", unique_mmsi)

        # Buttons for actions
        if "show_table" not in st.session_state:
            st.session_state.show_table = False
        if "show_map" not in st.session_state:
            st.session_state.show_map = False

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("📋 Display Data Table"):
                st.session_state.show_table = True

        with col2:
            if st.button("🗺️ Plot Ship Movements"):
                st.session_state.show_map = True

        vessel_data = df[df["MMSI"] == selected_mmsi].sort_values(by="Timestamp")

        if st.session_state.show_table:
            st.subheader(f"📊 Data for MMSI: {selected_mmsi}")
            st.dataframe(vessel_data, height=400, width=1500)

        if st.session_state.show_map and not vessel_data.empty:
            locations = list(zip(vessel_data["Latitude"], vessel_data["Longitude"]))
            start_point = locations[0]
            end_point = locations[-1]

            # Store the map in session state to prevent it from disappearing
            if "map" not in st.session_state:
                st.session_state.map = folium.Map(location=start_point, zoom_start=7, control_scale=True, tiles="cartodb positron")
                marker_cluster = MarkerCluster().add_to(st.session_state.map)

                for i, row in vessel_data.iterrows():
                    popup_text = (
                        f"📍 **Position Info:**<br>"
                        f"**MMSI:** {row['MMSI']}<br>"
                        f"**Latitude:** {row['Latitude']}<br>"
                        f"**Longitude:** {row['Longitude']}<br>"
                        f"**Timestamp:** {row['Timestamp']}<br>"
                        f"**Navigation Status:** {row['Navigation Status']}"
                    )

                    marker = folium.Marker(
                        location=[row["Latitude"], row["Longitude"]],
                        popup=popup_text,
                        icon=folium.Icon(color="blue", icon="info-sign")
                    )
                    marker.add_to(marker_cluster)

                folium.Marker(
                    start_point, popup="🟢 Start Position", icon=folium.Icon(color="green")
                ).add_to(st.session_state.map)

                folium.Marker(
                    end_point, popup="🔴 End Position", icon=folium.Icon(color="red")
                ).add_to(st.session_state.map)

                folium.PolyLine(locations, color="blue", weight=3, opacity=0.8).add_to(st.session_state.map)

            # Display the stored map
            st_folium(st.session_state.map, width=1000, height=600)
