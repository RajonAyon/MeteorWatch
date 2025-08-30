import streamlit as st

def get_inputs():
    # Meteor radius (m)
    radius = st.sidebar.slider(
        "Meteor radius (m)",
        min_value=50,
        max_value=1200,  # reasonable upper limit
        value=50,
        step=50
    )

    # Meteor density (kg/m³)
    density = st.sidebar.slider(
        "Meteor density (kg/m³)",
        min_value=2000,
        max_value=10000,
        value=2000,
        step=100
    )

    # Meteor velocity (km/s) — now integer
    velocity = st.sidebar.slider(
        "Meteor velocity (km/s)",
        min_value=12,
        max_value=100,  # extreme upper limit
        value=12,
        step=1
    )

    # Impact angle (°)
    angle = st.sidebar.slider(
        "Impact angle (°)",
        min_value=30,
        max_value=90,
        value=90,
        step=1
    )

    return {"density": density, "radius": radius, "velocity": velocity, "angle": angle}
