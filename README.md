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

Once an allocation criteria is selected in the web app, the resulting share of grid and PV electricity consumption is calculated and linked to PV and grid activities. The default PV activity used is based on a 570 kWp open ground multi-Si photovoltaic installation located in France. In the future, the web app will provide a range of PV activity options to better match the proposed system. The grid electricity activity is associated with a background scenario as described later in this README.

## Allocation Equations

This section describes the allocation rules for electricity consumption and distribution, considering hourly, yearly, monthly, and daily caps.

---

### 1. Hourly Allocation  
The **hourly allocation** determines how much electricity is taken from the **grid** and how much is unclaimed from PV generation at an hourly level.

$$ H_{\text{grid}} = \max\left( 0, E_{\text{elec, total}} - E_{\text{elec, direct PV}} \right) $$  
$$ H_{\text{not claimed}} = E_{\text{PV, total}} - E_{\text{elec, direct PV}} $$  

where:  

- E_elec, total = electrolyzer capacity × capacity factor × 8760 (total yearly electricity required by the electrolyzer)  
- E_elec, direct PV = electricity directly consumed by the electrolyzer from PV (instantaneous consumption)  
- E_PV, total = total yearly PV electricity production
- H_grid is the electricity **taken from the grid** under an hourly time allocation
- H_not claimed is the **surplus PV electricity** not used by the electrolyzer (can be stored or sold). 

If the electrolyzer needs more electricity than what PV directly provides, the grid supplies the difference. Any excess PV electricity that is not used directly is **not claimed**.

---

### 2. Yearly Allocation  
The **yearly allocation** considers how much electricity can be claimed as PV-sourced over an entire year.

$$ Y_{\text{elec from PV}} = \min(E_{\text{elec, total}}, E_{\text{PV, total}}) $$  
$$ Y_{\text{not claimed}} = \max(0, E_{\text{PV, total}} - E_{\text{elec, total}}) $$  
$$ Y_{\text{credit}} = Y_{\text{elec from PV}} - E_{\text{elec, direct PV}} $$  
$$ Y_{\text{grid}} = E_{\text{elec, total}} - Y_{\text{elec from PV}} $$  

where: 
- Y_elec from PV is the **total electricity** that can be claimed as PV-sourced.  
- Y_not claimed is the **surplus PV electricity** not used by the electrolyzer (can be stored or sold).  
- Y_credit is the electricity that was **sent to the grid but later reclaimed** as PV electricity.  
- Y_grid is the electricity **taken from the grid** if PV electricity is insufficient.  

If the PV system produces **more** than what the electrolyzer consumes, the excess is **not claimed**. If PV produces **less**, the grid supplies the difference.

---

### 3. Monthly Allocation  
The **monthly allocation** applies a cap on how much PV electricity can be claimed each month, ensuring that grid and PV allocations align with monthly energy availability.

$$ M_{\text{elec from PV}} = \sum_{m=1}^{12} \min\left(E_{\text{PV, month}}[m], \text{monthly cap} \right) $$  
$$ M_{\text{not claimed}} = E_{\text{PV, total}} - M_{\text{elec from PV}} $$  
$$ M_{\text{credit}} = M_{\text{elec from PV}} - E_{\text{elec, direct PV}} $$  
$$ M_{\text{grid}} = E_{\text{elec, total}} - M_{\text{elec from PV}} $$  

where:  
- E_PV, month [m] = electricity produced by PV during month **m**.  
- **monthly cap** = number of days in the month × 24 × electrolyzer capacity.
- M_elec from PV is the PV electricity that the electrolyzer consumes daily.  
- M_not claimed is the **excess PV electricity** not consumed.  
- M_credit represents electricity that was sent to the grid but later claimed as PV-sourced.  
- M_grid is the electricity taken from the grid if PV is insufficient.  

This allocation ensures that monthly PV electricity consumption does not exceed the electrolyzer's capacity.

---

### 4. Daily Allocation  
The **daily allocation** applies a cap at the **daily level** to determine how much PV electricity can be claimed as used.

$$ D_{\text{elec from PV}} = \sum_{d=1}^{365} \min\left(E_{\text{PV, day}}[d], \text{daily cap} \right) $$  
$$ D_{\text{not claimed}} = E_{\text{PV, total}} - D_{\text{elec from PV}} $$  
$$ D_{\text{credit}} = D_{\text{elec from PV}} - E_{\text{elec, direct PV}} $$  
$$ D_{\text{grid}} = E_{\text{elec, total}} - D_{\text{elec from PV}} $$  

where: 
- E_PV, day [d] = electricity produced by PV during day **d**. 
- **daily cap** = 24 x electrolyzer capacity
- D_elec from PV is the PV electricity that the electrolyzer consumes daily.
- D_not claimed is the **excess PV electricity** not consumed.  
- D_credit represents electricity that was sent to the grid but later claimed as PV-sourced.  
- D_grid is the electricity taken from the grid if PV is insufficient.  

This allocation ensures that the electrolyzer does not **over-claim** PV electricity beyond what is feasible on a **daily basis**.

---

## Summary
The allocation methods define how much electricity is sourced from **PV** and how much comes from the **grid**, depending on the **time resolution**:
- **Hourly:** Direct PV consumption and grid use in real-time.
- **Yearly:** Total PV electricity that can be claimed over a year.
- **Monthly:** Ensures PV electricity claims do not exceed monthly production.
- **Daily:** Caps electricity consumption to daily PV availability.

---

### Background Data (Scenario Selection)
Users can select different **energy demand and production scenarios** to model their system within various grid contexts:

- **RTE Demand Scenarios**: **Reference**, **Sobriety**, **Reindustrialization**
- **RTE Production Scenarios**: **M1**, **M2**, **M23**, **N1**, **N2**, **N03**
- **Imports Modeling**: **Western Europe market group** / **Neighboring market group**
- **Integrated Assessment Model (IAM) Applied**:  
  - **IMAGE SSP2-Base**  
  - **TIAM-UCL SSP2-RCP45**  
  - **No IAM applied**
 
The selection made at this point links the ‘market for electricity, low voltage’ activity, located in France, to a different database depending on the user's choice. The market represents an yearly avarage grid data normalized into a 1kWh activity.

It is important to note that applying this activity to the background is a widely accepted methodology for calculating the electricity consumed by the electrolyzer when the grid is the sole electricity source, especially in systems with high capacity factors as shown in Figure 2. This is the prevalent methodology applied to hydrogen production for industrial use, where continuous operation is often required.

<p align="center">
  <img src="https://github.com/user-attachments/assets/ab5a91b4-a244-4edd-afd2-8da682a22b37" alt="image" width="80%">
</p>

<p align="center"><em>Fig. 2 Continuous operation mode with electricity provided by the grid</em></p>


When renewables are integrated into the system, the use of yearly avaraged grid data serves as a proxy for the lack of dynamic data related to prospective grid electricity activities. A more refined method to model electricity consumption by the electrolyzer from the grid would involve understanding which specific technologies are supplying electricity to the grid at the time of consumption. A dynamic, prospective electricity mix model would provide a more accurate representation and is expected to be developed in the future.

<p align="center">
  <img src="https://github.com/user-attachments/assets/2aa2762b-815a-4a4b-b849-dccedda06455" alt="image" width="80%">
</p>

<p align="center"><em>Fig. 3 Continuous operation mode with electricity provided by the grid and PV system</em></p>


This repository provides comprehensive instructions for setting up the required environments to host the necessary libraries for each stage of web app development. It includes:

- The code used to extract databases from Premise;
- Inventories for Hydrogen systems using PEM and AEC technologies;
- Inventory data for the French electricity modeling using a market from neighboring countries;
- The integration code linking the computational LCA (Life Cycle Assessment) model with the Streamlit-based web interface to enhance usability.

Additionally, a simplified version of the web app is available as Jupyter Notebooks, offering an alternative approach to generating results using parameterized values instead of user selections.



