import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

# Load IMD Rainfall Data
@st.cache_data
def load_rainfall_data(file_path):
    # Assuming the data is in NetCDF format
    data = xr.open_dataset(file_path)
    return data


# Load Geospatial Data for India (states boundaries)
@st.cache_data
def load_geospatial_data():
    # Load India shapefile for state boundaries
    india_shapefile = gpd.read_file("C:/Users/user/PycharmProjects/Rainfall/india_st.shx")

    # Check if the CRS is already set; if not, define it
    if india_shapefile.crs is None:
        # Assuming the shapefile's CRS is EPSG:4326 (replace with the correct CRS if known)
        india_shapefile = india_shapefile.set_crs("EPSG:4326")

    # Reproject to WGS84 if the current CRS is not EPSG:4326
    india_shapefile = india_shapefile.to_crs("EPSG:4326")

    return india_shapefile


# Process Rainfall Data (both cumulative and average calculations)
def process_data(data, start_date, end_date, calc_type):
    # Print data coordinates to check for correct dimension names
    print("Data Coordinates:", data.coords)

    # Check if 'time' is present, if not, adjust to the correct coordinate name
    if 'time' not in data.coords:
        print(f"Available coordinates: {data.coords}")
        if 'TIME' in data.coords:
            data = data.sel(TIME=slice(start_date, end_date))
        elif 'timestamp' in data.coords:
            data = data.sel(timestamp=slice(start_date, end_date))
        elif 'date' in data.coords:
            data = data.sel(date=slice(start_date, end_date))
        else:
            raise ValueError("'TIME' or any related coordinate not found. Please check dataset.")
    else:
        data = data.sel(time=slice(start_date, end_date))

    # Calculate cumulative or average rainfall based on selected calculation type
    if calc_type == 'Cumulative':
        rainfall_result = data['RAINFALL'].sum(dim='TIME')
    elif calc_type == 'Average':
        rainfall_result = data['RAINFALL'].mean(dim='TIME')
    else:
        raise ValueError("Unsupported calculation type. Please choose 'Cumulative' or 'Average'.")

    return rainfall_result


# Plot Data on Map
def plot_rainfall_on_map(RAINFALL, india, vmin, vmax):
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot state boundaries from the shapefile
    india.plot(ax=ax, edgecolor='black', facecolor='none')

    # Plot rainfall data (assuming RAINFALL is an xarray DataArray)
    RAINFALL.plot(ax=ax, cmap='Blues', vmin=vmin, vmax=vmax, cbar_kwargs={'label': 'RAINFALL (mm)'})

    plt.title('Rainfall Visualization', fontsize=16)
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
    calc_type = st.sidebar.selectbox("Select Calculation", ['Cumulative', 'Average'])
    vmin = st.sidebar.number_input("Min Value for Color Scale", value=0)
    vmax = st.sidebar.number_input("Max Value for Color Scale", value=1200)

    # Load data
    data = load_rainfall_data('C:/Users/user/PycharmProjects/Rainfall/RF25_ind2023_rfp25.nc')
    india = load_geospatial_data()

    # Process data based on the selected calculation type
    try:
        rainfall_result = process_data(data, start_date, end_date, calc_type)
    except ValueError as e:
        st.error(str(e))
        return

    # Plot and visualize data
    fig = plot_rainfall_on_map(rainfall_result, india, vmin, vmax)
    st.pyplot(fig)

    # Add download option for the full processed data
    st.sidebar.markdown("### Download Data")
    st.sidebar.download_button(
        label="Download Processed Data",
        data=rainfall_result.to_dataframe().to_csv(),
        file_name="processed_rainfall_data.csv"
    )


if __name__ == "__main__":
    main()
