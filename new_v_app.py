import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static, st_folium
from geopy.geocoders import Nominatim
import io

# Streamlit app title
st.title("🚢 Vessel Movement Tracker")

# Upload CSV file
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # Load CSV into DataFrame
    df = pd.read_csv(uploaded_file)

    # Ensure required columns exist
    required_cols = {"MMSI", "Latitude", "Longitude", "Timestamp"}
    if not required_cols.issubset(df.columns):
        st.error(f"CSV file must contain these columns: {required_cols}")
    else:
        # Convert timestamp to readable format
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit='s')

        # Get unique MMSI numbers for selection
        unique_mmsi = df["MMSI"].unique()
        selected_mmsi = st.selectbox("Select MMSI Number", unique_mmsi)

        # Filter data for the selected MMSI
        vessel_data = df[df["MMSI"] == selected_mmsi].sort_values(by="Timestamp")

        if not vessel_data.empty:
            # Extract coordinates for plotting
            locations = list(zip(vessel_data["Latitude"], vessel_data["Longitude"]))
            start_point = locations[0]
            end_point = locations[-1]

            # Display data fields for selected MMSI
            st.subheader(f"📊 Data for MMSI: {selected_mmsi}")
            st.write(vessel_data)

            # Create map centered at the midpoint between the start and end points
            mid_point = [(start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2]
            m = folium.Map(location=mid_point, zoom_start=6)

            # Dictionary to store popups for each marker
            marker_popups = {}

            # Add markers for all positions with popups
            for i, row in vessel_data.iterrows():
                popup_text = (
                    f"📍 Position Info:<br>"
                    f"<b>MMSI:</b> {row['MMSI']}<br>"
                    f"<b>Latitude:</b> {row['Latitude']}<br>"
                    f"<b>Longitude:</b> {row['Longitude']}<br>"
                    f"<b>Timestamp:</b> {row['Timestamp']}"
                )

                marker = folium.Marker(
                    location=[row["Latitude"], row["Longitude"]],
                    popup=popup_text,
                    icon=folium.Icon(color="blue", icon="info-sign")
                )
                marker.add_to(m)

                # Store marker information
                marker_popups[(row["Latitude"], row["Longitude"])] = row.to_dict()

            # Add markers for start and end points with popups
            start_popup_text = (
                f"📍 Start Position:<br>"
                f"<b>MMSI:</b> {selected_mmsi}<br>"
                f"<b>Latitude:</b> {start_point[0]}<br>"
                f"<b>Longitude:</b> {start_point[1]}<br>"
                f"<b>Timestamp:</b> {vessel_data.iloc[0]['Timestamp']}"
            )
            folium.Marker(start_point, popup=start_popup_text, icon=folium.Icon(color="green")).add_to(m)

            end_popup_text = (
                f"📍 End Position:<br>"
                f"<b>MMSI:</b> {selected_mmsi}<br>"
                f"<b>Latitude:</b> {end_point[0]}<br>"
                f"<b>Longitude:</b> {end_point[1]}<br>"
                f"<b>Timestamp:</b> {vessel_data.iloc[-1]['Timestamp']}"
            )
            folium.Marker(end_point, popup=end_popup_text, icon=folium.Icon(color="red")).add_to(m)

            # Add polyline for movement path
            folium.PolyLine(locations, color="blue", weight=2.5, opacity=1).add_to(m)

            # Display the map in Streamlit with updated width and height
            map_data = st_folium(m, width=900, height=600)

            # Timestamp selection for fetching region info
            timestamp_options = vessel_data["Timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S').unique()
            selected_timestamp = st.selectbox("Select Timestamp", timestamp_options)

            # Button to fetch region info based on timestamp
            if st.button("Get Region Info"):
                # Find the corresponding row based on timestamp
                selected_row = vessel_data[vessel_data["Timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S') == selected_timestamp].iloc[0]
                lat = selected_row["Latitude"]
                lon = selected_row["Longitude"]

                # Use geopy to get the region name
                geolocator = Nominatim(user_agent="region_finder")
                location = geolocator.reverse((lat, lon), language='en', timeout=10)

                if location:
                    region_name = location.raw.get('address', {}).get('country', 'Region not found')
                    st.write(f"🌍 Region for Coordinates (Lat: {lat}, Lon: {lon}) at {selected_timestamp}: {region_name}")
                else:
                    st.write("Region not found for the given coordinates.")

            # Add the download button for the selected MMSI data
            @st.cache_data
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')

            csv = convert_df(vessel_data)

            st.download_button(
                label="Download Data for Selected MMSI",
                data=csv,
                file_name=f"vessel_data_mmsi_{selected_mmsi}.csv",
                mime="text/csv"
            )

        else:
            st.error(f"No data available for MMSI {selected_mmsi}")
