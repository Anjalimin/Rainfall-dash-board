import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st
import tempfile
import os

# Load IMD Rainfall Data
@st.cache_data
def load_rainfall_data(uploaded_file):
    data = xr.open_dataset(uploaded_file)
    return data

# Load Geospatial Data for India (states boundaries)
@st.cache_data
def load_geospatial_data(shapefile_files):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded shapefile components into a temporary directory
        for uploaded_file in shapefile_files:
            with open(os.path.join(tmpdir, uploaded_file.name), 'wb') as f:
                f.write(uploaded_file.read())
        
        # Check for the .shp file and ensure all required files are present
        shapefile_names = [f.name for f in shapefile_files]
        required_extensions = [".shp", ".shx", ".dbf"]
        missing_files = [ext for ext in required_extensions if not any(file.endswith(ext) for file in shapefile_names)]

        if missing_files:
            raise ValueError(f"Missing shapefile components: {', '.join(missing_files)}")
        
        shapefile_path = None
        for file in shapefile_files:
            if file.name.endswith(".shp"):
                shapefile_path = file.name
                break
        
        if not shapefile_path:
            raise ValueError("No .shp file found among the uploaded shapefile components.")
        
        # Read the shapefile using GeoPandas
        india_shapefile = gpd.read_file(os.path.join(tmpdir, shapefile_path))

        # Set the correct CRS if needed
        if india_shapefile.crs is None:
            india_shapefile = india_shapefile.set_crs("EPSG:4326")
        india_shapefile = india_shapefile.to_crs("EPSG:4326")

        return india_shapefile

# Process Rainfall Data (both cumulative and average calculations)
def process_data(data, start_date, end_date, calc_type):
    if 'TIME' not in data.coords:
        raise ValueError("'TIME' coordinate not found. Please check the dataset format.")

    data = data.sel(time=slice(start_date, end_date))

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
    india.plot(ax=ax, edgecolor='black', facecolor='none')
    RAINFALL.plot(ax=ax, cmap='Blues', vmin=vmin, vmax=vmax, cbar_kwargs={'label': 'Rainfall (mm)'})
    plt.title('Rainfall Visualization', fontsize=16)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    return fig

# Streamlit App
def main():
    st.title("IMD Rainfall Data Visualization")

    # Sidebar options
    st.sidebar.header("Upload Data and Configure Options")
    uploaded_nc_file = st.sidebar.file_uploader("Upload Rainfall NetCDF File", type=["nc"])
    shapefile_files = st.sidebar.file_uploader(
        "Upload Shapefile (Upload all related files: .shp, .shx, .dbf, etc.)", type=["shp", "shx", "dbf", "prj"], accept_multiple_files=True
    )

    start_date = st.sidebar.date_input("Start Date", value=pd.Timestamp("2023-06-01"))
    end_date = st.sidebar.date_input("End Date", value=pd.Timestamp("2023-09-30"))
    calc_type = st.sidebar.selectbox("Select Calculation", ['Cumulative', 'Average'])
    vmin = st.sidebar.number_input("Min Value for Color Scale", value=0)
    vmax = st.sidebar.number_input("Max Value for Color Scale", value=1200)

    if uploaded_nc_file and shapefile_files:
        try:
            data = load_rainfall_data(uploaded_nc_file)
            india = load_geospatial_data(shapefile_files)

            rainfall_result = process_data(data, start_date, end_date, calc_type)
            fig = plot_rainfall_on_map(rainfall_result, india, vmin, vmax)
            st.pyplot(fig)

            st.sidebar.download_button(
                label="Download Processed Data",
                data=rainfall_result.to_dataframe().to_csv(),
                file_name="processed_rainfall_data.csv"
            )
        except ValueError as e:
            st.error(f"An error occurred: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.info("Please upload both the NetCDF file and shapefile components to proceed.")

if __name__ == "__main__":
    main()
