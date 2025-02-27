from streamlit_extras.colored_header import colored_header
import pandas as pd
import matplotlib.pyplot as plt
import folium
import lca_algebraic as agb
from streamlit_folium import *
import streamlit as st
from lib.utils import get_pv_prod_data, get_city_coordinates, init_once, display_params, compute_lca, \
    compute_intermediate, get_tooltip_html, get_js_code, get_css_code
from lib.settings import *

def show():
    global y_elec_consumption_from_PV_Wh, y_not_claimed_elec, total_elec_consumed_by_electro_Wh
    st.set_page_config(layout="wide")

    init_once()

    st.markdown("# HySPI Calculator")
    st.markdown("#### Hydrogen production via electrolysis")
    st.markdown("###### Functional unit: 1kg of Hydrogen")  # verify the option to switch fu
    st.markdown("###### Method: EF v3.0 no LT")

    colored_header(
        label="Foreground",
        description="Parameters extracted directly from your production plant",
        color_name="blue-70",
    )

    p, input_decision = display_params()

    ir = compute_intermediate(p)

    # Add JavaScript and CSS to the page
    st.markdown(get_js_code(), unsafe_allow_html=True)
    st.markdown(get_css_code(), unsafe_allow_html=True)

    # Get tooltip HTML
    tooltip_html1, tooltip_html2 = get_tooltip_html()

    # Display tooltips
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f'{tooltip_html1}', unsafe_allow_html=True)
        st.markdown(f'{tooltip_html2}', unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div style="padding: 5px; margin: 10px; border: 1px solid #cccccc; border-radius: 5px;"><b>Hydrogen production:</b> {ir.H2_year / 1000:.2f} t/year</div>',
            unsafe_allow_html=True)


    geodata = None  # Initialize data with a default value

    if p.renewable_coupling == "Yes":
        colored_header(
            label="Photovoltaic system",
            description="Select the location and PV capacity",
            color_name="blue-70",
        )

        st.session_state.setdefault("last_clicked", "")
        st.session_state.setdefault("latlon", "")
        st.session_state.setdefault("city_name", "")


        # Initialize OpenCage geocoder with your API key

        st.write("#### Enter a location or select one on the map")
        with st.container():
            col1, col2, col3= st.columns([1, 1, 1])


            with col1:
                city_name = st.text_input("Enter city name:", placeholder="Fos-sur-Mer")
                st.write("or")
                latlon = st.text_input("Enter latitude and longitude :",placeholder="e.g.: 43.4380, 4.9455", type="default")
                if latlon:
                    city_lat, city_lon = map(float, latlon.split(','))

            # Create a Folium map
            m = folium.Map(location=[46.903354, 2.088334], zoom_start=5)
            m.add_child(folium.LatLngPopup())

            if city_name:  # Check if city name is entered
                geodata = get_city_coordinates(city_name)
                if geodata:
                    folium.Marker(location=geodata).add_to(m)
                    #m.location=geodata in case we want to use for the rest of europe

            if latlon:  # Check if latitude and longitude are entered
                geodata = (city_lat, city_lon)
                folium.Marker(location=geodata).add_to(m)
                m.fit_bounds([geodata])

            with col2:
                # When the user interacts with the map
                map_data = st_folium(
                    m,
                    width = 270,
                    height=290,
                    key="folium_map"
                )

                if map_data.get("last_clicked"):
                    # Round the latitude and longitude to 4 decimal places
                    lat = round(map_data["last_clicked"]["lat"], 4)
                    lng = round(map_data["last_clicked"]["lng"], 4)

                    # Get the position using the rounded values
                    geodata = (lat, lng)

                    # Add the marker to the map
                    folium.Marker(location=geodata).add_to(m)

            col1.write("")
            col1.markdown(f'<div style="padding: 5px; margin: 10px; border: 1px solid #cccccc; border-radius: 5px;"><b>Location selected:</b> {geodata}</div>', unsafe_allow_html=True)

            col3.write("")
            pv_logo = "pv logo.png"
            col3.image(pv_logo, caption='', width= 200)
            col3.markdown("Solar radiation data was extracted from the PVGIS webapp. It consists of one value for every hour over a one year period. For more information consult:")
            col3.markdown("[PVGIS documentation](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/getting-started-pvgis/pvgis-user-manual_en)")

        col1, col2, col3 = st.columns([1, 1, 1])
        pv_cap_MW = col1.number_input("PV system capacity (MW):", value=5.0 * p.electro_capacity_MW,
                                      min_value=0.1,
                                      max_value=1_000_000.0, step=0.1)
        battery_coupling = col2.selectbox("Battery coupled?", ["Yes", "No"], index=0)
        if geodata is not None:
            pv_cap_kW=pv_cap_MW*1_000 #website requires pv capacity to be in kWp
            df = get_pv_prod_data(geodata[0], geodata[1], pv_cap_kW)


            # Sum of all elec_Wh figures
            hours_year = 365 * 24
            total_elec_consumed_by_electro_Wh = ir.electro_capacity_W * p.cf * hours_year  # here we add the capacity factor because this is related to electrolyzer's consumption, this assumes that the maintenance will be done when pv is not producing electricity
            y_elec_production_from_PV_Wh = df['elec_Wh'].sum() #total electricity produced by the PV system during that one-year period
            capped_values = df['elec_Wh'].clip(upper=ir.electro_capacity_W) #all values under electro_capacity_Wh
            max_direct_pv_consumption_by_electro = capped_values.sum() #consumption of electricity from PV due to direct connection, it doesn't include any electricity due to allocation
            if total_elec_consumed_by_electro_Wh > max_direct_pv_consumption_by_electro:
                h_grid = total_elec_consumed_by_electro_Wh - max_direct_pv_consumption_by_electro #in the hourly allocation rule no PV credit exists
                h_not_claimed_elec = y_elec_production_from_PV_Wh - max_direct_pv_consumption_by_electro  # h_credit, the hourly allocation system doesnt allow any allocation to "seen" due to the hourly resolution od the PV data
            else:
                st.warning("Under this configuration, no grid electricity is required.")
                return

            # yearly cap begins here:
            if y_elec_production_from_PV_Wh >= total_elec_consumed_by_electro_Wh:
                y_elec_consumption_from_PV_Wh = total_elec_consumed_by_electro_Wh #the electrolyzer will never consume more electricity than what its capacity allows, even if the PV is oversized
                y_not_claimed_elec = y_elec_production_from_PV_Wh - total_elec_consumed_by_electro_Wh #in this case there will be surplus electricity that can be sold in the market, or stored, or wasted
            elif y_elec_production_from_PV_Wh < total_elec_consumed_by_electro_Wh:
                y_elec_consumption_from_PV_Wh = y_elec_production_from_PV_Wh #in case the PV system is undersized every electricity produced will be consumed under this allocation rule
                y_not_claimed_elec = 0 #no electricity to sell, or store, actually, electricity from the grid will be needed to fulfill capacity

            y_credit = y_elec_consumption_from_PV_Wh - max_direct_pv_consumption_by_electro  #this is the share of electricity from the PV, that was sent to the grid, but consumed later as it was claimed as PV sourced under the annual allocation rule
            y_grid = total_elec_consumed_by_electro_Wh - (y_credit + max_direct_pv_consumption_by_electro) #in case the electricity produced during the year by the PV system is not enough, grid electricity will be used

            # monthly cap begins here:
            # Extract month and year part and create a new column YearMonth
            df['YearMonth'] = df['DateTime'].dt.to_period('M')

            # Group by the month and sum the 'elec_Wh' values
            monthly_sums = df.groupby('YearMonth')['elec_Wh'].sum().reset_index()

            # Calculate the monthly maximum values based on the number of days in each month
            monthly_sums['days_in_month'] = monthly_sums['YearMonth'].dt.days_in_month
            monthly_sums['max_value'] = monthly_sums['days_in_month'] * 24 * ir.electro_capacity_W

            # Cap the monthly sums
            monthly_sums['Total_elec_Wh_month_capped'] = monthly_sums['elec_Wh'].clip(upper=monthly_sums['max_value']) #max electricity consumed from PV for each month

            m_elec_consumption_from_PV_Wh = monthly_sums['Total_elec_Wh_month_capped'].sum()  #* p.cf #total electricity that can be claimed from PV
            m_elec_consumption_from_PV_Wh = min (total_elec_consumed_by_electro_Wh, m_elec_consumption_from_PV_Wh)
            m_not_claimed_elec = y_elec_production_from_PV_Wh - m_elec_consumption_from_PV_Wh
            m_credit = m_elec_consumption_from_PV_Wh - max_direct_pv_consumption_by_electro #this is the share of electricity from the PV, that was sent to the grid, but consumed later as it was claimed as PV sourced under the monthly allocation rule
            m_grid = total_elec_consumed_by_electro_Wh - m_elec_consumption_from_PV_Wh

            # daily cap begins here:
            # Extract date part and create a new column
            df['Date'] = df['DateTime'].dt.date

            # Group by the date and sum the 'elec_Wh' values
            daily_sums = df.groupby('Date')['elec_Wh'].sum().reset_index()

            # Rename columns for clarity
            daily_sums.columns = ['Date', 'Total_elec_Wh_day']

            # Daily cap
            max_value = 24 * ir.electro_capacity_W

            # Preserve the original column
            original_values = daily_sums['Total_elec_Wh_day']

            # Clip the column and replace it
            daily_sums['Total_elec_Wh_day'] = original_values.clip(upper=max_value)

            d_elec_consumption_from_PV_Wh = daily_sums['Total_elec_Wh_day'].sum()
            d_elec_consumption_from_PV_Wh = min(total_elec_consumed_by_electro_Wh, d_elec_consumption_from_PV_Wh )

            d_not_claimed_elec = y_elec_production_from_PV_Wh - d_elec_consumption_from_PV_Wh
            d_credit = d_elec_consumption_from_PV_Wh - max_direct_pv_consumption_by_electro  # this is the share of electricity from the PV, that was sent to the grid, but consumed later as it was claimed as PV sourced under the monthly allocation rule
            d_grid = total_elec_consumed_by_electro_Wh - d_elec_consumption_from_PV_Wh

            if battery_coupling == "No":
                gifb_path = 'H2b.gif'
                col3.image(gifb_path, use_container_width=True)
                st.markdown("---")


            # Initialize battery state variables
            stored_in_battery_Wh = 0
            total_elec_sent_to_battery_Wh = 0
            elec_from_battery_to_electro_Wh = 0
            elec_from_PV_to_battery_Wh = 0

            if battery_coupling == "Yes":
                gif_path = 'H2.gif'
                col3.image(gif_path, use_container_width=True)
                st.markdown("---")

                # Battery system
                eff_charge = 0.867 #square root of 75%
                eff_discharge = 0.867
                battery_power_capacity_MW = col1.number_input("Battery power capacity (MW):", value=5.0, min_value=0.0,
                                                              step=1.0)
                battery_power_capacity_W = battery_power_capacity_MW * 1_000_000  # Convert to watts

                col1.number_input(
                    "Round-trip efficiency:", value= 0.75, disabled=True
                )

                # Define storage capacity in Wh (20 MWh)
                # Compute storage capacity as 6 times power capacity
                battery_storage_capacity_MWh = battery_power_capacity_MW * 6
                battery_storage_capacity_Wh = battery_storage_capacity_MWh * 1_000_000  # Convert to watt-hours

                # Compute storage capacity as 6 times power capacity
                battery_storage_capacity_MWh = battery_power_capacity_MW * 6

                # Display storage capacity as a non-editable field with better styling
                col2.text_input(
                    "Battery storage capacity (MWh):", value=f"{battery_storage_capacity_MWh:.2f}", disabled=True
                )

                # Process each row to manage battery charging/discharging
                for index, row in df.iterrows():
                    date = row['Date']
                    surplus_Wh = row['elec_Wh'] - ir.electro_capacity_W
                    if surplus_Wh > 0:
                        # Charge the battery with surplus electricity
                        available_in_battery_Wh = battery_storage_capacity_Wh - stored_in_battery_Wh
                        available_to_charge_Wh = min(surplus_Wh, battery_power_capacity_W, available_in_battery_Wh) #battery_power_capacity_W * 1h
                        charged_to_battery = available_to_charge_Wh * eff_charge
                        stored_in_battery_Wh += charged_to_battery
                        total_elec_sent_to_battery_Wh += charged_to_battery
                        elec_from_PV_to_battery_Wh += available_to_charge_Wh
                    else:
                        # Discharge the battery if there is no PV production
                        required_from_battery_Wh = min(-surplus_Wh, battery_power_capacity_W, stored_in_battery_Wh)
                        discharged_from_battery = required_from_battery_Wh * eff_discharge
                        stored_in_battery_Wh -= required_from_battery_Wh
                        elec_from_battery_to_electro_Wh += discharged_from_battery

                # Calculate efficiency losses
                efficiency_losses_Wh = elec_from_PV_to_battery_Wh - elec_from_battery_to_electro_Wh

            # Define constants for colors
            COLOR_PV = '#FFD700'
            COLOR_GRID = '#7E868E'
            COLOR_BATTERY = 'red'
            COLOR_NON_CLAIMED = '#ff8000'

            # Prepare data for plotting
            data = {
                'Category': ['Year', 'Month', 'Day', 'Hour'],
                'Grid': [(y_grid) / 1_000_000, (m_grid) / 1_000_000, (d_grid) / 1_000_000,
                         (h_grid - elec_from_battery_to_electro_Wh) / 1_000_000],
                'PV Credit': [y_credit / 1_000_000, m_credit / 1_000_000, d_credit / 1_000_000, 0],
                # No PV credit for hourly
                'PV non claimed': [y_not_claimed_elec / 1_000_000, m_not_claimed_elec / 1_000_000,
                                   d_not_claimed_elec / 1_000_000, (h_not_claimed_elec- elec_from_battery_to_electro_Wh) / 1_000_000],
                'PV Actual': [max_direct_pv_consumption_by_electro / 1_000_000] * 4,
                'PV due to battery storage': [0, 0, 0,
                                              elec_from_battery_to_electro_Wh / 1_000_000 if battery_coupling == "Yes" else 0]
            }

            df = pd.DataFrame(data)

            # Plot the data
            fig, ax = plt.subplots(figsize=(5, 3))
            bar_width = 0.35

            # Plot bars
            bar1 = ax.bar(df['Category'], df['PV Actual'], bar_width, label='PV', color=COLOR_PV)
            bar2 = ax.bar(df['Category'], df['PV Credit'], bar_width, bottom=df['PV Actual'], label='PV Credit',
                          color=COLOR_PV, edgecolor=COLOR_GRID, hatch='///')
            if battery_coupling == "Yes":
                bar3 = ax.bar(df['Category'], df['PV due to battery storage'], bar_width,
                              bottom=df['PV Actual'] + df['PV Credit'], label='Battery',
                              color=COLOR_BATTERY)
            bar4 = ax.bar(df['Category'], df['Grid'], bar_width, bottom=df['PV Actual'] + df['PV Credit']+ df['PV due to battery storage'], label='Grid',
                          color=COLOR_GRID)
            bar5 = ax.bar(df['Category'], df['PV non claimed'], bar_width,
                          bottom=df['PV Actual'] + df['PV Credit'] + df['Grid'] + df['PV due to battery storage'],
                          label='Non-claimed', color=COLOR_NON_CLAIMED)

            # Add labels and title
            ax.set_xlabel('Category', fontsize=10)
            ax.set_ylabel('Electricity (MWh)', fontsize=10)
            ax.set_title('Grid, PV, and PV Credit Percentages', fontsize=12)
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

            # Add total consumption line
            total_consumption = total_elec_consumed_by_electro_Wh / 1_000_000
            ax.axhline(y=total_consumption, color='blue', linestyle='--',
                       label=f'Total Consumption = {total_consumption:.2f} MWh')

            # Adjust layout
            plt.tight_layout()
            fig.subplots_adjust(right=0.8)

            # Display in Streamlit
            col4, col_a = st.columns([3, 4])
            col_a.pyplot(fig)

            col4.write("##### Credit assignment:")
            col4.write("")
            col4.write("")
            col4.write("")
            col4.write("")
            col4.write("")

            with col4.container(border=True):
                allocation = st.radio(
                    "Temporal correlation cap:",
                    ["Year", "Month", "Day", "Hour"],
                    index=1,
                    horizontal=True
                )

            expander = st.expander("Electricity information:")
            with expander:
                # Global electricity information table
                e_data = {
                    "Global electricity information": [
                        "Electrolyzer's total consumption",
                        "PV production",
                        "Electrolyzer's direct consumption from PV",
                        "Electricity supplied by the battery (from PV)"
                    ],
                    "Value (MWh)": [
                        f"{total_elec_consumed_by_electro_Wh / 1_000_000:.2f}",
                        f"{y_elec_production_from_PV_Wh / 1_000_000:.2f}",
                        f"{max_direct_pv_consumption_by_electro / 1_000_000:.2f}",
                        f"{elec_from_battery_to_electro_Wh / 1_000_000:.2f}"
                    ]
                }
                df = pd.DataFrame(e_data)
                st.table(df)

                # Hourly allocation electricity data table
                data_allocation = {
                    "Electricity information due to allocation ": [
                        "Total PV credit consumed",
                        "PV production non-claimed",
                    ],
                    "Hourly": [
                        "Hidden in data",
                        f"{h_not_claimed_elec / 1_000_000:.2f}",
                    ],
                    "Daily": [
                        f"{d_credit / 1_000_000:.2f}",
                        f"{d_not_claimed_elec / 1_000_000:.2f}",
                    ],
                    "Monthly": [
                        f"{m_credit / 1_000_000:.2f}",
                        f"{m_not_claimed_elec / 1_000_000:.2f}",
                    ],
                    "Annualy": [
                        f"{y_credit / 1_000_000:.2f}",
                        f"{y_not_claimed_elec / 1_000_000:.2f}",
                    ]
                }
                df_allocation = pd.DataFrame(data_allocation)
                st.table(df_allocation)

            data_grid_year = y_grid/ total_elec_consumed_by_electro_Wh
            data_pv_year = 1-data_grid_year
            data_grid_month = m_grid / total_elec_consumed_by_electro_Wh
            data_pv_month = 1 - data_grid_month
            data_grid_day = d_grid / total_elec_consumed_by_electro_Wh
            data_pv_day = 1 - data_grid_day
            if battery_coupling == "Yes":
                data_grid_hour = (h_grid - elec_from_battery_to_electro_Wh) / total_elec_consumed_by_electro_Wh
                data_pv_hour = 1 - data_grid_hour
            else:
                data_grid_hour = h_grid / total_elec_consumed_by_electro_Wh
                data_pv_hour = 1 - data_grid_hour

            if allocation == "Year":
                data_grid = data_grid_year
                data_pv = data_pv_year
            if allocation == "Month":
                data_grid = data_grid_month
                data_pv = data_pv_month
            if allocation == "Day":
                data_grid = data_grid_day
                data_pv = data_pv_day
            if allocation == "Hour":
                data_grid = data_grid_hour
                data_pv = data_pv_hour


    #Indication for background before the data
    colored_header(
        label="Background",
        description="Electricity scenarios 2050",
        color_name="blue-70",
    )


    col4, col5, col6, col7 = st.columns([1, 1, 1, 1])

    demand_scenario = col4.radio("**Demand Scenarios**", options=["Reference", "Sobriety", "Reindustrialization"],
                                 key="demand_scenario")
    production_scenario = col5.radio("**Production Scenarios**", options=["M0", "M1", "M23", "N1", "N2", "N03"],
                                     key="production_scenario", horizontal=True)
    imports_market_group = col6.radio("**Imports market group**", options=["Western European Union (WEU)", "Neighbouring"],
                                      key="imports_market_group")
    iam_applied = col7.radio("**IAM applied**", options=["TIAM-UCL SSP2-RCP45", "TIAM-UCL SSP2-Base", "Image SSP2-Base", "None"], key="iam_applied")

    if demand_scenario == "Reference":
        if production_scenario == "M0":
            if imports_market_group == "Western European Union (WEU)":
                if iam_applied == "Image SSP2-Base":
                    p.grid_market = "EIBM0"
                    p.PV_database = "PV_IB"
                elif iam_applied == "TIAM-UCL SSP2-Base":
                    p.grid_market = "ETBM0"
                    p.PV_database = "PV_TB"
                elif iam_applied == "TIAM-UCL SSP2-RCP45":
                    p.grid_market = "ET45M0"
                    p.PV_database = "PV_T45"
                elif iam_applied == "None":
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")
            else:
                if iam_applied == "None":
                    p.grid_market = "ENIMO"
                    p.PV_database = "PV_NI"
                else:
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")

        if production_scenario == "M1":
            if imports_market_group == "Western European Union (WEU)":
                if iam_applied == "Image SSP2-Base":
                    p.grid_market = "EIBM1"
                    p.PV_database = "PV_IB"
                elif iam_applied == "TIAM-UCL SSP2-Base":
                    p.grid_market = "ETBM1"
                    p.PV_database = "PV_TB"
                elif iam_applied == "TIAM-UCL SSP2-RCP45":
                    p.grid_market = "ET45M1"
                    p.PV_database = "PV_T45"
                elif iam_applied == "None":
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")
            else:
                if iam_applied == "None":
                    p.grid_market = "ENIM1"
                    p.PV_database = "PV_NI"
                else:
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")

        if production_scenario == "M23":
            if imports_market_group == "Western European Union (WEU)":
                if iam_applied == "Image SSP2-Base":
                    p.grid_market = "EIBM23"
                    p.PV_database = "PV_IB"
                elif iam_applied == "TIAM-UCL SSP2-Base":
                    p.grid_market = "ETBM23"
                    p.PV_database = "PV_TB"
                elif iam_applied == "TIAM-UCL SSP2-RCP45":
                    p.grid_market = "ET45M23"
                    p.PV_database = "PV_T45"
                elif iam_applied == "None":
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")
            else:
                if iam_applied == "None":
                    p.grid_market = "ENIM23"
                    p.PV_database = "PV_NI"
                else:
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")

        if production_scenario == "N1":
            if imports_market_group == "Western European Union (WEU)":
                if iam_applied == "Image SSP2-Base":
                    p.grid_market = "EIBN1"
                    p.PV_database = "PV_IB"
                elif iam_applied == "TIAM-UCL SSP2-Base":
                    p.grid_market = "ETBN1"
                    p.PV_database = "PV_TB"
                elif iam_applied == "TIAM-UCL SSP2-RCP45":
                    p.grid_market = "ET45N1"
                    p.PV_database = "PV_T45"
                elif iam_applied == "None":
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")
            else:
                if iam_applied == "None":
                    p.grid_market = "ENIN1"
                    p.PV_database = "PV_NI"
                else:
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")

        if production_scenario == "N2":
            if imports_market_group == "Western European Union (WEU)":
                if iam_applied == "Image SSP2-Base":
                    p.grid_market = "EIBN2"
                    p.PV_database = "PV_IB"
                elif iam_applied == "TIAM-UCL SSP2-Base":
                    p.grid_market = "ETBN2"
                    p.PV_database = "PV_TB"
                elif iam_applied == "TIAM-UCL SSP2-RCP45":
                    p.grid_market = "ET45N2"
                    p.PV_database = "PV_T45"
                elif iam_applied == "None":
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")
            else:
                if iam_applied == "None":
                    p.grid_market = "ENIN2"
                    p.PV_database = "PV_NI"
                else:
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")

        if production_scenario == "N03":
            if imports_market_group == "Western European Union (WEU)":
                if iam_applied == "Image SSP2-Base":
                    p.grid_market = "EIBN03"
                    p.PV_database = "PV_IB"
                elif iam_applied == "TIAM-UCL SSP2-Base":
                    p.grid_market = "ETBN03"
                    p.PV_database = "PV_TB"
                elif iam_applied == "TIAM-UCL SSP2-RCP45":
                    p.grid_market = "ET45N03"
                    p.PV_database = "PV_T45"
                elif iam_applied == "None":
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")
            else:
                if iam_applied == "None":
                    p.grid_market = "ENIN03"
                    p.PV_database = "PV_NI"
                else:
                    p.grid_market = None
                    st.write("Demand modelling in progress, not currently available")
    else:
        p.grid_market = None
        st.write("Demand modelling in progress, not currently available")

    if p.grid_market is None:
        st.write("Select a valid option")
    else:
        if geodata is not None and st.button("Compute result"):
            pass

        elif geodata is None and st.button("Compute result"):
            data_pv=0
            data_grid=1


        else:
            st.stop()

        #Results indication before code
        colored_header(
            label="LCA Results",
            description="",
            color_name="yellow-80",
        )

        lca_result, system = compute_lca(p, ir, data_grid, data_pv)

        # Check if 'stored_results' and 'results_summary' exist in session state, if not, initialize them
        if 'stored_results' not in st.session_state:
            st.session_state.stored_results = pd.DataFrame()

        if 'results_summary' not in st.session_state:
            st.session_state.results_summary = []

        # Append the new results to the stored results
        st.session_state.stored_results = pd.concat([st.session_state.stored_results, lca_result], axis=0)

        # Track the user selections for this result
        result_summary = {
            "Result ID": f"Result {st.session_state.counter}",
            "Electrolyzer stack": p.stack_type,
            "Electrolyzer capacity (MW)": p.electro_capacity_MW,
            "Stack lifetime (h)": p.stack_LT,
            "Balance of Plant lifetime (years)": p.BoP_LT_y,
            "Capacity factor (0 to 1)": p.cf,
            "Photovoltaic coupled?": p.renewable_coupling,
            "Storage": p.storage_choice,
            "Transport method": p.transp,
            "Demand Scenario": demand_scenario,
            "Production Scenario": production_scenario,
            "Imports Market Group": imports_market_group,
            "IAM Applied": iam_applied
        }
        if input_decision == "Efficiency":
            result_summary["Stack efficiency (0 to 1):"] = p.eff
        else:
            result_summary["Electricity (kWh/kg)"] = p.electricity
        if p.renewable_coupling == "Yes":
            result_summary["PV system capacity (MW)"] = pv_cap_MW
            result_summary["Battery coupled?"] = battery_coupling
            result_summary["Allocation"]= allocation
            if battery_coupling == "Yes":
                result_summary["Battery power capacity (MW)"] = battery_power_capacity_MW
                result_summary["Battery storage capacity (MWh)"] = battery_storage_capacity_MWh
                result_summary["Charging efficiency"] = eff_charge
                result_summary["Discharging efficiency"] = eff_discharge

        # Append the summary of this result
        st.session_state.results_summary.append(result_summary)

        # Update result name order
        st.session_state.counter += 1

        # Transpose the stored results for display
        transposed_table = st.session_state.stored_results.transpose()

        # Display the transposed DataFrame
        st.table(transposed_table)

        # Initialize summary_text as an empty string
        summary_text = ""

        # Loop through all result summaries and build the summary_text
        for summary in st.session_state.results_summary:
            result_line = (
                f"**{summary['Result ID']}**: "
                f"Demand Scenario: {summary['Demand Scenario']}, "
                f"Production Scenario: {summary['Production Scenario']}, "
                f"Imports Market Group: {summary['Imports Market Group']}, "
                f"IAM Applied: {summary['IAM Applied']}, "
                f"Photovoltaic coupled?: {summary['Photovoltaic coupled?']}, "
                f"Storage: {summary['Storage']}, "
                f"Transport method: {summary['Transport method']}, "
                f"Electrolyzer stack: {summary['Electrolyzer stack']}, "
                f"Electrolyzer capacity: {summary['Electrolyzer capacity (MW)']} MW, "
                f"Stack lifetime: {summary['Stack lifetime (h)']} h, "
                f"Balance of Plant lifetime: {summary['Balance of Plant lifetime (years)']} years, "
                f"Capacity factor: {summary['Capacity factor (0 to 1)']}"
            )

            # Add efficiency or electricity consumption based on input decision
            if "Stack efficiency (0 to 1):" in summary:
                result_line += f", Stack efficiency: {summary['Stack efficiency (0 to 1):']}"
            elif "Electricity (kWh/kg)" in summary:
                result_line += f", Electricity consumption: {summary['Electricity (kWh/kg)']} kWh/kg"

            # Add PV system details if applicable
            if summary.get("PV system capacity (MW)"):
                result_line += f", PV system capacity: {summary['PV system capacity (MW)']} MW"
                # Add battery details if applicable
                if summary.get("Battery coupled?") == "Yes":
                    result_line += (
                        f", Allocation: {summary['Allocation']},"
                        f" Battery power capacity: {summary.get('Battery power capacity (MW)', 'N/A')} MW"
                        f", Battery storage capacity: {summary.get('Battery storage capacity (MWh)', 'N/A')} MWh"
                        f", Charging efficiency: {summary.get('Charging efficiency', 'N/A')}"
                        f", Discharging efficiency: {summary.get('Discharging efficiency', 'N/A')}"
                    )

            # Append each result line to summary_text
            summary_text += result_line + "  \n"

        # After the loop, display the accumulated summary
        expander = st.expander("Summary of Results")
        with expander:
            st.markdown(summary_text)

        expander = st.expander("Hydrogen and electricity information")
        with expander:
            with st.container():
                paragraph = (
                    f"The estimated electricity consumption throughout the plant's lifetime is {ir.Ec_GWh:.2f} GWh.\n\n"
                    f"The total hydrogen production throughout the plant's lifetime is projected to be {ir.H2p_ton:.2f} tons.\n\n"
                    f"The hydrogen production rate is approximately {ir.H2_per_hour:.2f} kg per hour.\n\n"
                    f"Approximately {ir.E1:.2f} kWh of electricity is required to produce 1 kg of hydrogen.\n\n"
                )

            # Display the combined paragraph
            st.info(paragraph)


        st.markdown("---")

if __name__ == "__main__":
    show()
