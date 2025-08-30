import streamlit as st
from ui.sidebar import get_inputs
from ui.maps import make_map
from calculation import effective_ke
from ui.visualization import *
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🌍 Asteroid Impact Simulator")

# -----------------------------
# Sidebar Inputs
# -----------------------------
params = get_inputs()  # returns dict with radius, velocity, density, angle
calculate_clicked = st.sidebar.button("Calculate Impact")

# -----------------------------
# Initialize session state
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "input"  # "input" or "result"
if "click_location" not in st.session_state:
    st.session_state.click_location = None
if "params" not in st.session_state:
    st.session_state.params = None

# -----------------------------
# Input Page
# -----------------------------
if st.session_state.mode == "input":
    st.markdown("Set asteroid parameters in the sidebar and click **Calculate Impact**.")

    # Wait for the user to click "Calculate Impact"
    if calculate_clicked:
        st.session_state.params = params
        st.session_state.mode = "result"
        st.rerun()

# -----------------------------
# Result Page
# -----------------------------
elif st.session_state.mode == "result":
    # If user has not set impact location yet, show base map to click
    if st.session_state.click_location is None:
        map_obj = make_map()
        st.markdown("Click on the map to select the impact location.")
        map_data = st_folium(map_obj, width=700, height=500, returned_objects=["last_clicked"])

        if map_data and map_data.get("last_clicked"):
            lat = map_data["last_clicked"]["lat"]
            lon = map_data["last_clicked"]["lng"]
            st.session_state.click_location = (lat, lon)
            st.rerun()  # rerun to show result map
    else:
        lat, lon = st.session_state.click_location

        if st.session_state.params is not None:


            # --------------------------
            # Tabs for results
            # --------------------------
            tab1, tab2,tab3= st.tabs(["Crater & Ejecta","Thermal & Seismic","Human Impact"])

            if "active_tab" not in st.session_state:
                st.session_state.active_tab = "tab1"

            with tab1:
                st.subheader("Crater & Ejecta")

                # type hint ensures editor knows crater is a CraterAndEjecta
                crater: CraterAndEjecta = CraterAndEjecta(**st.session_state.params)

                # this method exists and will be suggested in VS Code
                deck = crater.show_on_map_pydeck(lat, lon)

                # show pydeck map in Streamlit
                st.pydeck_chart(deck)

                # show your extra visualization (altair, matplotlib, etc.)
                crater.visualize()

            with tab2:
                st.subheader("Thermal & Seismic Effects")

                thermal = ThermalAndSeismic(**st.session_state.params)
                deck = thermal.show_on_map_pydeck(lat, lon)
                st.pydeck_chart(deck)

                # Keep your Altair charts and summary
                thermal.visualize()

            with tab3:
                st.subheader("🧑‍🤝‍🧑 Human Impact Simulation")

                # Compute thermal burn data
                humanimpact = HumanImpact(**st.session_state.params, lat=lat, lon=lon)
                df = humanimpact.compute_zones()
                thermal = df[df["Zone"] == "Thermal Zone"].iloc[0]

                thermal_data = {
                    "minor": thermal["Minor Injuries"],
                    "moderate": thermal["Moderate Injuries"],
                    "severe": thermal["Severe Injuries"]
                }

                # Show GPU-accelerated thermal burn map
                humanimpact.show_human_impact_pydeck(lat, lon, humanimpact.thermal_radius_km, thermal_data)

                # Show tables & charts
                humanimpact.visualize()







        else:
            st.error("Asteroid parameters are not set. Go back and click 'Calculate Impact' in the sidebar.")



        # Try Again button
        if st.button("Try Again"):
            st.session_state.click_location = None
            st.session_state.params = None
            st.session_state.mode = "input"
            st.rerun()
