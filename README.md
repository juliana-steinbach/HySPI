# HySPI Web App

HySPI is a web-based tool that allows users to obtain **Life Cycle Assessment (LCA) results** for **hydrogen production via electrolysis**, providing **tailored data** specific to their projects.

Users can configure their system by selecting options from **foreground data**, **background data**, and **renewable energy integration**.

## System Configuration Options

### Foreground Data (User-Specified Parameters)
Users can define key technical parameters for their electrolyzer system, including:

- **Stack efficiency** / **Electricity consumption per kg of hydrogen**
- **Electrolyzer stack type**: **PEM** / **AEC**
- **Electrolyzer capacity** (MW)
- **Stack lifetime** (h)
- **Balance of Plant (BoP) lifetime** (years)
- **Capacity factor**
- **Photovoltaic (PV) coupled system** (optional)
- **Storage options**
- **Transport methods**

### Background Data (Scenario Selection)

The grid electricity activity is associated with a background scenario extracted from RTE_scenarios repository developed by O.I.E. Mines Paristech. This repo focuses on modeling RTE scenarios based on the Futurs Énergétiques 2050 report and can be extracted as an external scenario using Premise.

For more details on the grid modeling methodology refer to: https://github.com/oie-mines-paristech/RTE_scenarios

Users can select different **energy demand and production scenarios** to model their system within various grid contexts:

- **RTE Demand Scenarios**: **Reference**, **Sobriety**, **Reindustrialization**
- **RTE Production Scenarios**: **M1**, **M2**, **M23**, **N1**, **N2**, **N03**
- **Imports Modeling**: **Western Europe market group** / **Neighboring market group**
- **Integrated Assessment Model (IAM) Applied**:
  - **TIAM-UCL SSP2-RCP45**
  - **TIAM-UCL SSP2-Base** 
  - **IMAGE SSP2-Base**  
  - **No IAM applied**
 
The selection made at this point links the ‘market for electricity, low voltage’ activity, located in France, to a different database depending on the user's choice. The market represents an yearly avarage grid data normalized into a 1kWh activity. This is the methodology applied to hydrogen production for industrial use, where continuous operation is often required as shown in Figure 1.

<p align="center">
  <img src="https://github.com/user-attachments/assets/ab5a91b4-a244-4edd-afd2-8da682a22b37" alt="image" width="50%">
</p>

<p align="center"><em>Fig. 1 Continuous operation mode with electricity provided by the grid</em></p>


When renewables are integrated into the system, the use of yearly avaraged grid data serves as a proxy for the lack of dynamic data related to prospective grid electricity activities. A more refined method to model electricity consumption by the electrolyzer from the grid would involve understanding which specific technologies are supplying electricity to the grid at the time of consumption. A dynamic, prospective electricity mix model would provide a more accurate representation and is expected to be developed in the future.

<p align="center">
  <img src="https://github.com/user-attachments/assets/2aa2762b-815a-4a4b-b849-dccedda06455" alt="image" width="50%">
</p>

<p align="center"><em>Fig. 3 Continuous operation mode with electricity provided by the grid and PV system</em></p>

### Renewable Energy Integration (PV Coupling)
For projects integrating renewable energy, users can define **PV system characteristics**:

- **Geographical location**
- **PV system capacity**: (MW)
- **Battery coupled**: Yes / No
- **Battery power capacity** (MW)
- **Battery storage capacity** (MWh)
- **Charging efficiency**
- **Discharging efficiency**
- **Credit allocation methods**: **Yearly**, **Monthly**, **Daily**, **Hourly**

### PVGIS Integration
When selecting a **PV-coupled system**, the HySPI calculator retrieves solar data from **PVGIS** (Photovoltaic Geographical Information System) to provide accurate location-based solar potential estimates:

- **Solar radiation database**: **PVGIS-SARAH2**
- **Available years**: **2018**, **2019**, **2020** (avareged data 2018-2020)
- **Mounting type**: **Fixed**
- **Slope & Azimuth**: **Optimized**
- **PV Technology**: **Crystalline silicon**
- **Installed peak PV power**: **Matches user-defined PV system capacity (MW)**
- **System loss factor**: **14%**

PVGIS generates average hourly power outputs from the PV system in kWp. This data enables the calculation of how much electricity can be directly consumed by the electrolyzer from the PV system, based on the electrolyzer’s maximum capacity and operational capacity factor. Any remaining electricity required to power the electrolyzer is drawn from the grid. This approach reflects an almost instantaneous consumption of electricity from both the PV system and the grid, providing a real-time view of the electrical flow.

<p align="center">
  <img src="https://github.com/user-attachments/assets/c4be4d57-5c35-4871-b671-da70d251fcf6" alt="image" width="50%">
</p>

<p align="center"><em>Fig. 1 Example of the allocation criteria options provided by the webapp</em></p>

Additionally, a yearly allocation system alternative is used to allocate the total electricity produced by the PV system over the course of a year to the electricity consumed by the electrolyzer within that same year. This method simplifies the calculation by assuming that the PV system can supply electricity to the electrolyzer regardless of when the electricity is produced. In this system, the PV capacity is linked to the electrolyzer's capacity on an annual basis for both production and consumption. This approach is suitable for systems where surplus electricity produced during the summer months, when sunlight and irradiance are more abundant, can be "banked" and used during the winter months, when daylight hours are shorter. 

If constraints are applied to the data, it is possible to calculate the share of electricity drawn from the grid versus the PV system based on credit allocations constrained by monthly or daily time correlations.

The monthly allocation criteria assumes that surplus electricity produced on sunny days can offset the consumption on cloudy days, as long as the total surplus over the month is consumed within the same month. Under this configuration, the summer months, with longer days and more sunlight, will contribute more electricity from the PV system, while the winter months will require greater reliance on grid electricity.

The daily allocation criteria models a system where electricity produced on a given day is allocated to that same day. This method limits the PV credits to sunny days, leaving cloudy days to rely almost entirely on grid electricity.

Once an allocation criteria is selected in the web app, the resulting share of grid and PV electricity consumption is calculated and linked to PV and grid activities. The default PV activity used is based on a 570 kWp open ground multi-Si photovoltaic installation located in France. 

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/b18a7a77-7887-4b03-af33-8749793f9af2" alt="image" width="50%">
</p>

<p align="center"><em>Fig. 4 Implementation of a battery to the PV/Hydrogen system</em></p>

---






