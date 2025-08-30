
import rasterio
import rasterio.mask
from shapely.geometry import Point, mapping
import pyproj
from shapely.ops import transform
import math
import numpy as np
import os
import requests


raster_path = "data/ppp_2020_1km_Aggregated.tif"

# Dropbox link (replace with your actual file link ending with ?dl=1)
dropbox_url = "https://www.dropbox.com/scl/fi/zkesvwoui2z1xsqe33yc5/ppp_2020_1km_Aggregated.tif?dl=1"

# Download dataset if not exists
if not os.path.exists(raster_path):
    os.makedirs("data", exist_ok=True)
    r = requests.get(dropbox_url)
    with open(raster_path, "wb") as f:
        f.write(r.content)
    print("Dataset downloaded from Dropbox.")


def get_population_in_radius(lat, lon, radius_km):
    # Load raster
    with rasterio.open(raster_path) as src:
        point = Point(lon, lat)

        # Project to meters for accurate buffer
        project = pyproj.Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True).transform
        point_m = transform(project, point)
        buffer_m = point_m.buffer(radius_km * 1000)  # radius in meters

        # Transform back to lat/lon
        buffer = transform(pyproj.Transformer.from_crs("epsg:3857", "epsg:4326", always_xy=True).transform, buffer_m)

        # Mask raster
        out_image, out_transform = rasterio.mask.mask(src, [mapping(buffer)], crop=True)
        out_image = out_image[0]

        # Sum population ignoring nodata
        nodata = src.nodata
        mask = (out_image != nodata) & (out_image > 0)
        pop_sum = out_image[mask].sum()

    return int(pop_sum)


def mass_from_density_radius(density, radius):
    volume = (4/3) * math.pi * radius**3
    return density * volume

def effective_ke(density, radius, velocity, angle):
    mass = mass_from_density_radius(density, radius)
    KE_total = 0.5 * mass * (velocity*1000)**2
    angle_rad = math.radians(angle)
    return KE_total * math.sin(angle_rad)

def format_large_number(num):
    if num >= 1_00_00_00_000:
        return f"{num/1_00_00_00_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)


