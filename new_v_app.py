import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Streamlit page config
st.set_page_config(layout="wide")

# App title
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
    # Load CSV into DataFrame
    df = pd.read_csv(uploaded_file)

    # Ensure required columns exist
    required_cols = {"MMSI", "Latitude", "Longitude", "Timestamp", "Navigation Status"}
    if not required_cols.issubset(df.columns):
        st.error(f"CSV must contain: {required_cols}")
    else:
        # Convert timestamp to readable format
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit='s')
        
        # Convert Navigation_Status to readable format
        df["Navigation Status"] = df["Navigation Status"].map(NAVIGATION_STATUS)

        # Get unique MMSI numbers
        unique_mmsi = df["MMSI"].unique()
        selected_mmsi = st.selectbox("🚢 Select MMSI Number", unique_mmsi)

        # Filter data for selected MMSI
        vessel_data = df[df["MMSI"] == selected_mmsi].sort_values(by="Timestamp")

        # Create buttons
        show_table = st.button("📋 Display Data Table")
        show_map = st.button("🗺️ Plot Ship Movements")

        # If "Display Data Table" is clicked, show table with increased width
        if show_table:
            st.subheader(f"📊 Data for MMSI: {selected_mmsi}")
            st.dataframe(vessel_data.style.set_properties(**{'white-space': 'nowrap'}), height=400, width=1500)

        # If "Plot Ship Movements" is clicked, show map
        if show_map:
            if not vessel_data.empty:
                # Extract coordinates for plotting
                locations = list(zip(vessel_data["Latitude"], vessel_data["Longitude"]))
                start_point = locations[0]
                end_point = locations[-1]

                # Create map centered at the start location
                m = folium.Map(location=start_point, zoom_start=7, control_scale=True, tiles="cartodb positron")

                # Marker Cluster for better visualization
                marker_cluster = MarkerCluster().add_to(m)

                # Dictionary to store popups for each marker
                marker_popups = {}

                # Add markers for all positions
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

                    # Store marker data
                    marker_popups[(row["Latitude"], row["Longitude"])] = row.to_dict()

                # Add markers for start and end points with labels
                folium.Marker(
                    start_point, popup="🟢 Start Position", icon=folium.Icon(color="green")
                ).add_to(m)

                folium.Marker(
                    end_point, popup="🔴 End Position", icon=folium.Icon(color="red")
                ).add_to(m)

                # Add polyline for movement path
                folium.PolyLine(locations, color="blue", weight=3, opacity=0.8).add_to(m)

                # Display map in Streamlit
                map_data = st_folium(m, width=1000, height=600)

                # If a marker is clicked, show corresponding data
                if map_data["last_clicked"]:
                    clicked_coords = tuple(map_data["last_clicked"].values())
                    if clicked_coords in marker_popups:
                        st.subheader("📌 Selected Position Data:")
                        st.write(pd.DataFrame([marker_popups[clicked_coords]]))
