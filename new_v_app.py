import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Streamlit UI
st.title("🚢 Vessel Movement Tracker")

# Upload CSV File
uploaded_file = st.file_uploader("Upload CSV file with vessel movement data", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Ensure required columns exist
    required_columns = {'MMSI', 'Latitude', 'Longitude', 'Timestamp'}
    if not required_columns.issubset(df.columns):
        st.error(f"CSV must contain columns: {required_columns}")
    else:
        # Convert Timestamp to datetime for readability
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])

        # Get unique MMSI numbers and ask user to select one
        mmsi_list = df['MMSI'].unique().tolist()
        selected_mmsi = st.selectbox("Select MMSI Number:", mmsi_list)

        # Filter data for selected vessel
        vessel_data = df[df['MMSI'] == selected_mmsi]

        if vessel_data.empty:
            st.warning("No data available for this MMSI.")
        else:
            # Create Folium map centered at first coordinate
            m = folium.Map(location=[vessel_data.iloc[0]['Latitude'], vessel_data.iloc[0]['Longitude']], zoom_start=10)

            # Add movement path
            coords = list(zip(vessel_data['Latitude'], vessel_data['Longitude']))
            folium.PolyLine(coords, color="blue", weight=2.5, opacity=1).add_to(m)

            # Add markers with timestamps
            for idx, row in vessel_data.iterrows():
                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=f"Time: {row['Timestamp']}",
                    icon=folium.Icon(color="red", icon="info-sign"),
                ).add_to(m)

            # Display the map in Streamlit
            st_folium(m, width=700, height=500)
