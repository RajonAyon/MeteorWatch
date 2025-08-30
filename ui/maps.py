import folium
from streamlit_folium import st_folium
import streamlit as st

def make_map(click_location=None):
    m = folium.Map(location=[20, 0], zoom_start=2)

    # Add marker if location exists
    if click_location:
        lat, lon = click_location
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color="blue", icon="circle", prefix="fa")
        ).add_to(m)

    return m

def update_map_with_click(m, click_location):
    if click_location:
        lat, lon = click_location
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color="red", icon="star", prefix="fa")
        ).add_to(m)
    return m