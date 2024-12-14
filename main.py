import pandas as pd
import xarray as xr
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import streamlit as st


# Load IMD Rainfall Data
@st.cache_data
def load_rainfall_data(file_path):
    # Assuming the data is in NetCDF format
    data = xr.open_dataset(file_path)
    return data


file_path = "C:/Users/user/PycharmProjects/Rainfall/RF25_ind2023_rfp25.nc"
data = load_rainfall_data(file_path)


# Process Rainfall Data
def process_data(data, start_date, end_date):
    # Print data coordinates to check for correct dimension names
    print("Data Coordinates:", data.coords)

    # Check if 'time' is present, if not, print all available coordinates
    if 'time' not in data.coords:
        print(f"Available coordinates: {data.coords}")
        # You may need to adjust the 'time' dimension name based on what is printed here.
        # For example, if the coordinate is 'TIME', change 'time' to 'TIME'.
        raise ValueError("'time' coordinate not found. Check available coordinates.")

    # Ensure that start_date and end_date are in correct format
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Select time range, handle the case where the time dimension is not 'time'
    data = data.sel(time=slice(start_date, end_date))  # Adjust 'time' if necessary, e.g., 'TIME'

    # Calculate cumulative rainfall
    rainfall_cumulative = data['rainfall'].sum(dim='time')
    return rainfall_cumulative


# Load Geospatial Data for India
@st.cache_data
def load_geospatial_data():
    # Load India shapefile
    india_shapefile = gpd.read_file("C:/Users/user/PycharmProjects/Rainfall/India_Country_Boundary.shx")
    india = india_shapefile[india_shapefile['geometry'] == 'India']
    return india


# Plot Data on Map
def plot_rainfall_on_map(rainfall, india, vmin, vmax):
    fig, ax = plt.subplots(figsize=(10, 10))
    india.plot(ax=ax, edgecolor='black', facecolor='none')  # Plot India boundaries
    rainfall.plot(ax=ax, cmap='Blues', vmin=vmin, vmax=vmax, cbar_kwargs={'label': 'Rainfall (mm)'})
    plt.title('Cumulative Rainfall Visualization', fontsize=16)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    return fig


# Streamlit App
def main():
    st.title("IMD Rainfall Data Visualization")

    # Sidebar options
    st.sidebar.header("Select Period and Calculation Type")
    start_date = st.sidebar.date_input("Start Date", value=pd.Timestamp("2023-06-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.Timestamp("2023-09-30"))
    calc_type = st.sidebar.selectbox("Select Calculation", ['Cumulative'])
    vmin = st.sidebar.number_input("Min Value for Color Scale", value=0)
    vmax = st.sidebar.number_input("Max Value for Color Scale", value=1200)

    # Load data
    data = load_rainfall_data('C:/Users/user/PycharmProjects/Rainfall/RF25_ind2023_rfp25.nc')
    india = load_geospatial_data()

    # Process data
    try:
        rainfall_cumulative = process_data(data, start_date, end_date)
    except ValueError as e:
        st.error(str(e))
        return

    # Plot and visualize data
    fig = plot_rainfall_on_map(rainfall_cumulative, india, vmin, vmax)
    st.pyplot(fig)

    # Add download option
    st.sidebar.markdown("### Download Data")
    st.sidebar.download_button(label="Download Processed Data",
                               data=rainfall_cumulative.to_dataframe().to_csv(),
                               file_name="processed_rainfall_data.csv")


if __name__ == "__main__":
    main()
