import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import st_folium
from calculation import *
import branca.colormap as cm
import pydeck as pdk

class CraterAndEjecta:
    def __init__(self, density, radius, velocity, angle):
        self.radius = radius
        self.density = density
        self.velocity = velocity
        self.angle = angle

    def crater_inf(self, target_density=2500, gravity=9.81, k=1):
        d_i = self.radius * 2  # asteroid diameter in meters
        D_transient = k * ((self.density / target_density) ** (1 / 3)) * (d_i ** 0.78) * ((self.velocity*1000) ** 0.44) * (gravity ** -0.22)
        D_final = 1.3 * D_transient
        Depth = 0.2 * D_final
        return Depth, D_final

    def ejecta_radius(self, target_density=2500, gravity=9.81, k=1):
        _, D = self.crater_inf(target_density, gravity, k)
        heavy = 1.5 * D
        light = 3 * D
        return heavy, light

    def show_on_map_pydeck(self, lat, lon, target_density=2500, gravity=9.81, k=1):
        _, D_final = self.crater_inf(target_density, gravity, k)
        heavy_ejecta, light_ejecta = self.ejecta_radius(target_density, gravity, k)

        min_radius = 50
        crater_radius = max(D_final / 2, min_radius)
        heavy_radius = max(heavy_ejecta, min_radius)
        light_radius = max(light_ejecta, min_radius)

        # --- Data for each circle ---
        layers = []

        # Light ejecta (yellow)
        light_df = pd.DataFrame([{
            "lat": lat,
            "lon": lon,
            "radius_m": light_radius,
            "tooltip": f"🌕 Light Ejecta Radius: {int(light_radius/1000)} km"
        }])
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                light_df,
                get_position='[lon, lat]',
                get_radius="radius_m",
                get_fill_color='[255, 255, 0, 60]',
                pickable=True
            )
        )

        # Heavy ejecta (orange)
        heavy_df = pd.DataFrame([{
            "lat": lat,
            "lon": lon,
            "radius_m": heavy_radius,
            "tooltip": f"🟠 Heavy Ejecta Radius: {int(heavy_radius/1000)} km"
        }])
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                heavy_df,
                get_position='[lon, lat]',
                get_radius="radius_m",
                get_fill_color='[255, 140, 0, 80]',
                pickable=True
            )
        )

        # Crater (red)
        crater_df = pd.DataFrame([{
            "lat": lat,
            "lon": lon,
            "radius_m": crater_radius,
            "tooltip": f"🔴 Crater Diameter: {int(D_final/1000)} km"
        }])
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                crater_df,
                get_position='[lon, lat]',
                get_radius="radius_m",
                get_fill_color='[255, 0, 0, 120]',
                pickable=True
            )
        )

        # Impact point (black dot)
        impact_df = pd.DataFrame([{
            "lat": lat,
            "lon": lon,
            "radius_m": 100,
            "tooltip": "💥 Impact Point"
        }])
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                impact_df,
                get_position='[lon, lat]',
                get_radius="radius_m",
                get_fill_color='[0, 0, 0, 255]',
                pickable=True
            )
        )

        # --- View state (auto zoom to fit ejecta) ---
        max_radius = max(crater_radius, heavy_radius, light_radius)
        zoom = max(2, 12 - (max_radius / 50000))  # crude zoom scaling

        view_state = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            pitch=0
        )

        deck = pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=layers,
            tooltip={"text": "{tooltip}"}
        )

        return deck


    def visualize(self):
        depth, diameter = self.crater_inf()
        heavy, light = self.ejecta_radius()

        # Convert to km
        depth_km = int(depth / 1000)
        diameter_km = int(diameter / 1000)
        heavy_km = int(heavy / 1000)
        light_km = int(light / 1000)

        # -------------------------
        # Crater Table
        # -------------------------
        data = {
            "Feature": ["Crater Depth", "Crater Diameter", "Heavy Ejecta Radius", "Light Ejecta Radius"],
            "Value (km)": [depth_km, diameter_km, heavy_km, light_km]
        }
        df = pd.DataFrame(data)
        st.subheader("Crater & Ejecta Table")
        st.table(df)

        # -------------------------
        # Crater Bar Chart
        # -------------------------
        chart = alt.Chart(df).mark_bar().encode(
            x='Feature',
            y='Value (km)',
            color='Feature'
        ).properties(width=500, height=300)
        st.altair_chart(chart)

        # -------------------------
        # Comparison with Top 10 Craters
        # -------------------------
        st.subheader("Comparison with Top 10 Largest Craters")

        # Load CSV (assume you saved it previously)
        df_craters = pd.read_csv("data/top_10_craters.csv")

        # Add user's crater
        user_row = pd.DataFrame([{
            "Name": "Your Crater",
            "Diameter_km": diameter_km,
            "Location": "User Input",
            "Age_MYA": 0,
            "Notes": "Calculated impact"
        }])
        df_plot = pd.concat([df_craters, user_row], ignore_index=True)

        df_plot = df_plot.rename(columns={"Name": "Feature", "Diameter_km": "Value (km)"})

        comp_chart = alt.Chart(df_plot).mark_bar().encode(
            x=alt.X('Feature', sort=alt.SortField('Value (km)', order='descending')),
            y='Value (km)',
            color=alt.condition(
                alt.datum.Feature == "Your Crater",
                alt.value('red'),
                'Feature'
            )
        ).properties(width=800, height=400)

        st.altair_chart(comp_chart)
class ThermalAndSeismic:
    def __init__(self, density, radius, velocity, angle):
        self.radius = radius
        self.density = density
        self.velocity = velocity
        self.angle = angle
        self.energy_Mt = effective_ke(density, radius, velocity, angle) / 4.184e15  # J → Mt TNT

    def compute_effects(self):
        """
        Estimate thermal and seismic effects based on simple scaling.
        Returns DataFrame for table and distance vs pressure for line chart.
        """
        # Thermal radiation radius (fires/burns) in km
        thermal_radius_km = 5 * (self.energy_Mt ** (1/3))

        # Seismic effect (Richter equivalent) - rough estimate
        seismic_magnitude = 2 + np.log10(self.energy_Mt)

        # Table for display
        table_df = pd.DataFrame({
            "Effect": ["Thermal Radiation Radius", "Seismic Magnitude"],
            "Value": [int(thermal_radius_km), round(seismic_magnitude, 2)],
            "Unit": ["km", ""]
        })


        # Distance vs pressure decay
        distances_km = np.linspace(0, thermal_radius_km * 2, 100)
        pressures_Pa = 101325 * np.exp(-distances_km / thermal_radius_km)  # decay with distance

        line_df = pd.DataFrame({
            "Distance_km": distances_km,
            "Pressure_Pa": pressures_Pa
        })

        return thermal_radius_km, seismic_magnitude, table_df, line_df

    def show_on_map_pydeck(self, lat, lon):
        thermal_radius_km, seismic_magnitude,table_df,line_df = self.compute_effects()

        # --- Thermal zone (red circle) ---
        thermal_df = pd.DataFrame([{
            "lat": lat,
            "lon": lon,
            "radius_m": thermal_radius_km * 1000,
            "tooltip": f"🔥 Thermal Radius: ~{thermal_radius_km:.1f} km"
        }])

        thermal_layer = pdk.Layer(
            "ScatterplotLayer",
            thermal_df,
            get_position='[lon, lat]',
            get_radius="radius_m",
            get_fill_color='[255, 0, 0, 40]',  # semi-transparent red
            pickable=True
        )

        # --- Seismic zones ---
        k = 1.2
        seismic_layers = []
        for delta_m in range(1, 4):
            target_mag = seismic_magnitude - delta_m
            if target_mag < 4:
                continue
            distance_km = 10 ** ((seismic_magnitude - target_mag) / k)

            if target_mag >= 9:
                desc = "Violent"
            elif target_mag >= 8:
                desc = "Severe"
            elif target_mag >= 7:
                desc = "Strong"
            elif target_mag >= 6:
                desc = "Moderate"
            elif target_mag >= 5:
                desc = "Light"
            else:
                desc = "Minor"

            seismic_df = pd.DataFrame([{
                "lat": lat,
                "lon": lon,
                "radius_m": distance_km * 1000,
                "tooltip": f"🌍 Seismic Zone: {target_mag:.1f} Richter ({desc})"
            }])

            layer = pdk.Layer(
                "ScatterplotLayer",
                seismic_df,
                get_position='[lon, lat]',
                get_radius="radius_m",
                get_fill_color='[0, 0, 255, 40]',  # semi-transparent blue
                pickable=True
            )
            seismic_layers.append(layer)

        # --- View state ---
        view_state = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=6,
            pitch=0
        )

        # --- Deck.gl map ---
        deck = pdk.Deck(
            map_style=None,  # No basemap, just your layers
            initial_view_state=view_state,
            layers=[thermal_layer] + seismic_layers,
            tooltip={"text": "{tooltip}"}
        )

        return deck

    def visualize(self):
        # --- Compute effects ---
        thermal_radius_km, seismic_magnitude, table_df, df = self.compute_effects()

        # --- Load crater CSV safely ---
        df_craters = pd.read_csv(
            "data/top_10_craters.csv",
            quotechar='"'
        )
        df_craters["Thermal_Radius_km"] = df_craters["Thermal_Radius_km"].replace('~', '', regex=True).astype(float)
        df_craters["Seismic_Magnitude"] = df_craters["Seismic_Magnitude"].astype(float)

        # --- Add your asteroid ---
        your_asteroid_df = pd.DataFrame([{
            "Name": "Your Asteroid",
            "Diameter_km": int(self.radius * 2),
            "Thermal_Radius_km": int(thermal_radius_km),
            "Seismic_Magnitude": int(seismic_magnitude)
        }])
        df_craters = pd.concat([df_craters, your_asteroid_df], ignore_index=True)

        # --- Thermal comparison ---
        thermal_chart = (
            alt.Chart(df_craters)
            .mark_bar()
            .encode(
                x=alt.X("Name", sort="-y", title="Impact Crater"),
                y=alt.Y("Thermal_Radius_km", title="Thermal Radiation Radius (km)"),
                color=alt.condition(
                    alt.datum.Name == "Your Asteroid", alt.value("red"), alt.value("steelblue")
                ),
                tooltip=["Name", "Thermal_Radius_km"]
            )
            .properties(width=750, height=400, title="🔥 Thermal Radiation Radius Comparison")
        )
        st.altair_chart(thermal_chart)

        # --- Seismic comparison ---
        seismic_chart = (
            alt.Chart(df_craters)
            .mark_bar()
            .encode(
                x=alt.X("Name", sort="-y", title="Impact Crater"),
                y=alt.Y("Seismic_Magnitude", title="Seismic Magnitude (Richter)"),
                color=alt.condition(
                    alt.datum.Name == "Your Asteroid", alt.value("red"), alt.value("orange")
                ),
                tooltip=["Name", "Seismic_Magnitude"]
            )
            .properties(width=750, height=400, title="🌍 Seismic Magnitude Comparison")
        )
        st.altair_chart(seismic_chart)

        # --- Pressure vs Distance chart ---
        df.rename(columns={"Distance_km": "Distance (km)", "Pressure_Pa": "Pressure (Pa)"}, inplace=True)
        chart = (
            alt.Chart(df)
            .mark_line(color="red")
            .encode(
                x=alt.X("Distance (km)", title="Distance from Impact (km)"),
                y=alt.Y("Pressure (Pa)", title="Shockwave Pressure (Pa)", scale=alt.Scale(type="log")),
                tooltip=["Distance (km)", "Pressure (Pa)"]
            )
            .properties(width=700, height=400, title="💨 Shockwave Intensity of Your Asteroid")
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)

        # --- Summary ---
        st.markdown(
            f"⚠️ **Your asteroid impact** would create a **thermal radius of ~{thermal_radius_km:.1f} km** "
            f"and a **seismic magnitude of ~{seismic_magnitude:.2f} Richter**.\n\n"
            "**Inside the thermal radius:**\n\n"
            "🔥 Fires would erupt across the area.\n"
            "💥 Severe burns would affect living beings.\n"
            "🌳 Vegetation and flammable structures could ignite instantly.\n"
            "🏚️ Buildings and infrastructure may be severely damaged.\n\n"
            "This impact would rank among the most catastrophic events in Earth's history."
        )
class HumanImpact:
    def __init__(self, density, radius, velocity, angle, lat, lon):
        self.density = density
        self.radius = radius
        self.velocity = velocity
        self.angle = angle
        self.lat = lat
        self.lon = lon
        self.energy_Mt = effective_ke(density, radius, velocity, angle) / 4.184e15

        # Zones
        self.thermal_radius_km = 5 * (self.energy_Mt ** (1/3))
        self.seismic_radius_km = self.thermal_radius_km * 2  # for reporting only

    def estimate_casualties(self, population):
        """Estimate fatalities and injuries by severity"""
        fatalities = int(population * 0.05)
        severe = int(population * 0.1)      # 3rd degree burns
        moderate = int(population * 0.15)   # 2nd degree burns
        minor = int(population * 0.2)       # 1st degree burns
        survivors = population - (fatalities + severe + moderate + minor)
        return fatalities, severe, moderate, minor, survivors

    def compute_zones(self):
        """Compute populations and casualties for thermal and seismic zones"""
        pop_thermal = get_population_in_radius(self.lat, self.lon, self.thermal_radius_km)
        pop_seismic = get_population_in_radius(self.lat, self.lon, self.seismic_radius_km) - pop_thermal

        thermal_data = self.estimate_casualties(pop_thermal)
        seismic_data = self.estimate_casualties(pop_seismic)

        # Return both zones for reporting
        df = pd.DataFrame([
            {"Zone": "Thermal Zone", "Population": pop_thermal,
             "Fatalities": thermal_data[0], "Severe Injuries": thermal_data[1],
             "Moderate Injuries": thermal_data[2], "Minor Injuries": thermal_data[3],
             "Survivors": thermal_data[4]},
            {"Zone": "Seismic Zone", "Population": pop_seismic,
             "Fatalities": seismic_data[0], "Severe Injuries": seismic_data[1],
             "Moderate Injuries": seismic_data[2], "Minor Injuries": seismic_data[3],
             "Survivors": seismic_data[4]}
        ])
        return df

    def show_human_impact_pydeck(self, lat, lon, thermal_radius_km, thermal_data):
        zones = [
            {"radius": thermal_radius_km * 1000, "color": [255, 255, 0],
             "tooltip": f"1st° Burns: {thermal_data['minor']}"},
            {"radius": thermal_radius_km * 0.6 * 1000, "color": [255, 165, 0],
             "tooltip": f"2nd° Burns: {thermal_data['moderate']}"},
            {"radius": thermal_radius_km * 0.3 * 1000, "color": [139, 0, 0],
             "tooltip": f"3rd° Burns: {thermal_data['severe']}"},
            {"radius": self.seismic_radius_km * 1000, "color": [0, 0, 255],
             "tooltip": f"Seismic Zone (~{int(self.seismic_radius_km)} km radius)"}
        ]

        layers = []
        for z in sorted(zones, key=lambda x: x['radius'], reverse=True):  # largest first
            angles = np.linspace(0, 2 * np.pi, 64)
            lon_circle = lon + (z["radius"] / 111320) * np.cos(angles)
            lat_circle = lat + (z["radius"] / 110540) * np.sin(angles)
            poly = pd.DataFrame([{
                "polygon": list(zip(lon_circle, lat_circle)),
                "color": z["color"],
                "tooltip": z["tooltip"]
            }])
            layers.append(
                pdk.Layer(
                    "PolygonLayer",
                    poly,
                    get_polygon="polygon",
                    get_fill_color="color",
                    pickable=True,
                    auto_highlight=True,
                    extruded=False,
                    opacity=0.01
                )
            )

        view_state = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=6,
            pitch=0
        )

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={"html": "{tooltip}", "style": {"color": "white"}}
        )

        st.pydeck_chart(deck)

    def visualize(self):
        """Show human impact tables and charts in Streamlit"""
        df = self.compute_zones()

        # Format numbers
        df_display = df.copy()
        for col in ["Population","Fatalities","Severe Injuries","Moderate Injuries","Minor Injuries","Survivors"]:
            df_display[col] = df_display[col].apply(lambda x: format_large_number(int(x)))

        st.subheader("🌍 Human Impact Summary")
        st.table(df_display)

        # Stacked bar chart
        stacked = alt.Chart(df).mark_bar().encode(
            x="Zone",
            y=alt.Y("Fatalities", stack="zero", title="Population"),
            color=alt.value("black"),
            tooltip=["Zone", alt.Tooltip("Fatalities", format=",")]
        ) + alt.Chart(df).mark_bar().encode(
            x="Zone",
            y="Severe Injuries", color=alt.value("red"), tooltip=["Zone", alt.Tooltip("Severe Injuries", format=",")]
        ) + alt.Chart(df).mark_bar().encode(
            x="Zone",
            y="Moderate Injuries", color=alt.value("orange"), tooltip=["Zone", alt.Tooltip("Moderate Injuries", format=",")]
        ) + alt.Chart(df).mark_bar().encode(
            x="Zone",
            y="Minor Injuries", color=alt.value("yellow"), tooltip=["Zone", alt.Tooltip("Minor Injuries", format=",")]
        )
        st.altair_chart(stacked.properties(width=700, height=400, title="Human Impact by Severity"))

        # Pie chart
        total = df.sum()
        pie_data = pd.DataFrame({
            "Category": ["Fatalities","Severe","Moderate","Minor","Survivors"],
            "Count": [total["Fatalities"], total["Severe Injuries"], total["Moderate Injuries"], total["Minor Injuries"], total["Survivors"]]
        })
        pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Category", type="nominal"),
            tooltip=["Category","Count"]
        ).properties(width=400, height=400, title="Overall Human Impact Distribution")
        st.altair_chart(pie_chart)


