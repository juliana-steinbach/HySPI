from dataclasses import dataclass
from io import StringIO
from urllib.request import urlopen
import streamlit
from opencage.geocoder import OpenCageGeocode
from streamlit import cache_data
import streamlit as st
import pandas as pd
import lca_algebraic as agb
from lca_algebraic import *
from lib.settings import *

@dataclass
class UserInput :

    stack_type : str = None
    electro_capacity_MW : float = 0

    stack_LT : float = 0
    BoP_LT_y : float = 0
    eff : float = 0
    cf : float = 0
    transp : str = 0
    renewable_coupling : bool = 0
    storage : str = None
    grid_market : str = None
    n_tanks : int = 0
    electricity : float = 0


@dataclass
class IntermediateResult :

    electro_capacity_kW : float = None
    electro_capacity_W: float = 0
    BoP_LT_h : float = None
    Electricity_consumed_kWh : float = None
    Ec_kWh : float = None
    Ec_MWh : float = None
    Ec_GWh : float = None
    # Higher heating value
    HHV_kWhkg : float = None

    H2_year : float = None

    H2_produced : float = None
    H2p : float = None
    H2p_ton : float = None
    H2_per_hour : float = None
    Electricity_1kg : float = None
    E1 : float = None
    n_stacks : float = None

# Higher heating value: From water to vapor
HHV_kWhkg = 39.4  # kWh/kg

def display_params() -> tuple[UserInput, str]:

    col1, col2, col3 = st.columns([1, 1, 1])

    res = UserInput()

    input_decision = st.radio("Select input method:", ("Efficiency", "Electricity"))

    # Create column layout
    col1, col2, col3 = st.columns([1, 1, 1])

    # Toggle between efficiency or electricity inputs
    if input_decision == "Efficiency":
        res.eff = col1.number_input("Stack efficiency (0 to 1):", value=0.72, min_value=0.0, max_value=1.0, step=0.01)
    else:
        res.electricity = col1.number_input("Electricity (kWh/kg):", value=HHV_kWhkg / 0.72, min_value=0.0, step=0.01)

    # Common input fields
    res.stack_type = col2.selectbox("Electrolyzer stack:", ["PEM", "AEC"])
    res.electro_capacity_MW = col3.number_input("Electrolyzer capacity (MW):", value=20, min_value=1, step=1)
    res.stack_LT = col1.number_input("Stack lifetime (h):", value=120000, min_value=1, step=100)
    res.BoP_LT_y = col2.number_input("Balance of Plant lifetime (years):", value=20, min_value=1, step=1)
    res.cf = col3.number_input("Capacity factor (0 to 1):", value=0.9, min_value=0.01, max_value=1.00, step=0.05)
    res.renewable_coupling = col1.selectbox("Photovoltaic coupled?", ["Yes", "No"], index=1)
    res.storage_choice = col2.selectbox("Storage", ["Tank", "No storage"], index=1)
    res.transp = col3.selectbox("Transport method", ["Pipeline", "Truck"], index=0)

    return res, input_decision


@streamlit.cache_data
def init_once() :
    """Ensure to run this only once"""
    bw.projects.set_current('name_your_project')



def compute_intermediate(p:UserInput) :

    res = IntermediateResult()

    # Forefront questions
    res.electro_capacity_W = p.electro_capacity_MW * 1000000
    res.electro_capacity_kW = p.electro_capacity_MW * 1_000
    res.BoP_LT_h = p.BoP_LT_y * 365 * 24
    res.Electricity_consumed_kWh = res.BoP_LT_h * p.cf * res.electro_capacity_kW
    res.Ec_kWh = int(res.Electricity_consumed_kWh)
    res.Ec_MWh = res.Ec_kWh / 1_000  # Convert kWh to MWh
    res.Ec_GWh = res.Ec_kWh / 1_000_000  # Convert kWh to GWh

    # Check if electricity input is selected
    if p.eff > 0:
        # Hydrogen production using efficiency
        res.H2_year = 365 * 24 * p.cf * res.electro_capacity_kW * p.eff / HHV_kWhkg  # 24h
    else:
        # Hydrogen production using electricity consumption per kg
        res.H2_year = 365 * 24 * p.cf * res.electro_capacity_kW / p.electricity

    # Check if electricity input is selected
    if p.eff > 0:
        # Hydrogen production using efficiency
        res.H2_produced = res.BoP_LT_h * p.cf * res.electro_capacity_kW * p.eff / HHV_kWhkg
    else:
        # Hydrogen production using electricity consumption per kg
        res.H2_produced = res.Electricity_consumed_kWh / p.electricity

    res.H2p = int(res.H2_produced)
    res.H2p_ton = (res.H2p / 1000)  # Convert kg to tons
    res.H2_per_hour = res.H2p / (res.BoP_LT_h * p.cf)
    res.Electricity_1kg = (res.Electricity_consumed_kWh / res.H2_produced)  # = HHV/eff

    res.E1 = round(res.Electricity_consumed_kWh / res.H2_produced, 2)

    res.n_stacks = (res.BoP_LT_h / p.stack_LT) #*res.electro_capacity_MW

    return res

def compute_lca(p:UserInput, ir:IntermediateResult, data_grid, data_pv) :

    agb.resetDb(USER_DB)
    agb.resetParams()

    def negAct(act):
        """Correct the sign of some activities that are accounted as negative in brightway. """
        return agb.newActivity(USER_DB, act["name"] + "_neg", act["unit"], {
            act: -1,
        })

    Elec_TI_45_RM0 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='TI_SSP2_RCP45_Ref_M0')
    Elec_TI_45_RM1 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='TI_SSP2_RCP45_Ref_M1')
    Elec_TI_45_RM23 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                       db_name='TI_SSP2_RCP45_Ref_M23')
    Elec_TI_45_RN1 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='TI_SSP2_RCP45_Ref_N1')
    Elec_TI_45_RN2 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='TI_SSP2_RCP45_Ref_N2')
    Elec_TI_45_RN03 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                       db_name='TI_SSP2_RCP45_Ref_N03')

    Elec_TI_B_RM0 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='TI_SSP2_Base_Ref_M0')
    Elec_TI_B_RM1 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='TI_SSP2_Base_Ref_M1')
    Elec_TI_B_RM23 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='TI_SSP2_Base_Ref_M23')
    Elec_TI_B_RN1 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='TI_SSP2_Base_Ref_N1')
    Elec_TI_B_RN2 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='TI_SSP2_Base_Ref_N2')
    Elec_TI_B_RN03 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='TI_SSP2_Base_Ref_N03')

    Elec_IM_B_RM0 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='IM_SSP2_Base_Ref_M0')
    Elec_IM_B_RM1 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='IM_SSP2_Base_Ref_M1')
    Elec_IM_B_RM23 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='IM_SSP2_Base_Ref_M23')
    Elec_IM_B_RN1 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='IM_SSP2_Base_Ref_N1')
    Elec_IM_B_RN2 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                     db_name='IM_SSP2_Base_Ref_N2')
    Elec_IM_B_RN03 = agb.findActivity("market for electricity, low voltage, FE2050", loc="FR", single=False,
                                      db_name='IM_SSP2_Base_Ref_N03')

    Elec_RM0 = agb.findActivity(name="market for electricity, low voltage M0",
                                db_name='RTE scenarios neighbouring imports', loc="FR")
    Elec_RM1 = agb.findActivity(name="market for electricity, low voltage M1",
                                db_name='RTE scenarios neighbouring imports', loc="FR")
    Elec_RM23 = agb.findActivity(name="market for electricity, low voltage M23",
                                 db_name='RTE scenarios neighbouring imports', loc="FR")
    Elec_RN1 = agb.findActivity(name="market for electricity, low voltage N1",
                                db_name='RTE scenarios neighbouring imports', loc="FR")
    Elec_RN2 = agb.findActivity(name="market for electricity, low voltage N2",
                                db_name='RTE scenarios neighbouring imports', loc="FR")
    Elec_RN03 = agb.findActivity(name="market for electricity, low voltage N03",
                                 db_name='RTE scenarios neighbouring imports', loc="FR")


    # PV activity: This is the PV activity used for the foreground system when H2 is powered by PV
    PV_TB = agb.findActivity("electricity production, photovoltaic, 570kWp open ground installation, multi-Si",
                             loc="FR", db_name="TI_SSP2_Base_Ref_N1")
    PV_T45 = agb.findActivity("electricity production, photovoltaic, 570kWp open ground installation, multi-Si",
                              loc="FR", db_name="TI_SSP2_RCP45_Ref_N1")
    PV_IB = agb.findActivity("electricity production, photovoltaic, 570kWp open ground installation, multi-Si",
                             loc="FR", db_name="IM_SSP2_Base_Ref_N1")
    PV_NI = agb.findActivity("electricity production, photovoltaic, 570kWp open ground installation, multi-Si updated",
                             db_name='RTE scenarios neighbouring imports')  # updated activity

    # Biosphere:
    water_H2 = agb.findBioAct("Water, unspecified natural origin", categories=('natural resource', 'in ground'))
    Oxygen = agb.findBioAct("Oxygen", categories=('air',))
    Occupation_ind = agb.findBioAct("Occupation, industrial area", categories=('natural resource', 'land'))
    Transformation_from_ind = agb.findBioAct("Transformation, from industrial area",
                                             categories=('natural resource', 'land'))
    Transformation_to_ind = agb.findBioAct("Transformation, to industrial area",
                                           categories=('natural resource', 'land'))

    # Lorry_E6 = agb.findActivity("market for transport, freight, lorry >32 metric ton, EURO6", single=False, db_name=EI)

    tank = agb.findActivity(
        "high pressure storage tank production and maintenance, per 10kgH2 at 500bar, from grid electricity",
        single=False, db_name='AEC/PEM')

    # No activity is used for the case where no storage is used
    null_activity = newActivity(USER_DB,  # We define foreground activities in our own DB
                                "no activity, or zero impact activity",  # Name of the activity
                                "unit",  # Unit
                                exchanges={})

    def negAct(act):
        """Correct the sign of some activities that are accounted as negative in brightway. """
        return agb.newActivity(USER_DB, act["name"] + "_neg", act["unit"], {
            act: -1,
        })

    # Electrolyzer selection:
    activity_names = {
        'PEM': {
            'Stack': 'electrolyzer production, 1MWe, PEM, Stack',
            'BoP': 'electrolyzer production, 1MWe, PEM, Balance of Plant',
            'Treatment_Stack': 'treatment of fuel cell stack, 1MWe, PEM',
            'Treatment_BoP': 'treatment of fuel cell balance of plant, 1MWe, PEM'
        },
        'AEC': {
            'Stack': 'electrolyzer production, 1MWe, AEC, Stack',
            'BoP': 'electrolyzer production, 1MWe, AEC, Balance of Plant',
            'Treatment_Stack': 'treatment of fuel cell stack, 1MWe, AEC',
            'Treatment_BoP': 'treatment of fuel cell balance of plant, 1MWe, AEC'
        }
    }

    # activities from AEC/PEM database
    stack_activity = agb.findActivity(name=activity_names[p.stack_type]['Stack'], db_name='AEC/PEM')
    bop_activity = agb.findActivity(name=activity_names[p.stack_type]['BoP'], db_name='AEC/PEM')
    t_Stack_activity = negAct(agb.findActivity(name=activity_names[p.stack_type]['Treatment_Stack'], db_name='AEC/PEM'))
    t_BoP_activity = negAct(agb.findActivity(name=activity_names[p.stack_type]['Treatment_BoP'], db_name='AEC/PEM'))

    T45 = ['ET45M0', 'ET45M1', 'ET45M23', 'ET45N1', 'ET45N2', 'ET45N03']
    TB = ['ETBM0', 'ETBM1', 'ETBM23', 'ETBN1', 'ETBN2', 'ETBN03']
    IB = ['EIBM0', 'EIBM1', 'EIBM3', 'EIBN1', 'EIBN2', 'EIBN03']
    NI = ['ENIM0', 'ENIM1', 'ENIM23', 'ENIN1', 'ENIN2', 'ENIN03', ]

    param_g = agb.newEnumParam(
        "param_g",  # Short name
        label="electricity g",
        description="low voltage electricity from the grid in France",  # Long description
        values=T45 + TB + IB + NI,
        default="ET45N1")

    electricity_g = newSwitchAct(USER_DB, "electricity_g", param_g, {
        'ET45M0': Elec_TI_45_RM0,
        'ET45M1': Elec_TI_45_RM1,
        'ET45M23': Elec_TI_45_RM23,
        'ET45N1': Elec_TI_45_RN1,
        'ET45N2': Elec_TI_45_RN2,
        'ET45N03': Elec_TI_45_RN03,

        'ETBM0': Elec_TI_B_RM0,
        'ETBM1': Elec_TI_B_RM1,
        'ETBM23': Elec_TI_B_RM23,
        'ETBN1': Elec_TI_B_RN1,
        'ETBN2': Elec_TI_B_RN2,
        'ETBN03': Elec_TI_B_RN03,

        'EIBM0': Elec_IM_B_RM0,
        'EIBM1': Elec_IM_B_RM1,
        'EIBM3': Elec_IM_B_RM23,
        'EIBN1': Elec_IM_B_RN1,
        'EIBN2': Elec_IM_B_RN2,
        'EIBN03': Elec_IM_B_RN03,

        'ENIM0': Elec_RM0,
        'ENIM1': Elec_RM1,
        'ENIM23': Elec_RM23,
        'ENIN1': Elec_RN1,
        'ENIN2': Elec_RN2,
        'ENIN03': Elec_RN03
    })

    param_pv = agb.newEnumParam(
        "param_pv",  # Short name
        label="electricity PV",  # English label
        description="pv",  # Long description
        values=["PV_IB", "PV_TB", "PV_T45", "PV_NI"],
        default="PV_T45")

    electricity_pv = newSwitchAct(USER_DB, "electricity_pv", param_pv, {
        "PV_IB": PV_IB,
        "PV_TB": PV_TB,
        "PV_T45": PV_T45,
        "PV_NI": PV_NI
    })


    def define_production():
        return agb.newActivity(USER_DB, "H2 production phase",
                               unit="unit",
                               exchanges={
                                   electricity_g: ir.Electricity_1kg * data_grid,
                                   electricity_pv: ir.Electricity_1kg * data_pv,
                                   water_H2: 0.0014,
                                   Oxygen: -8
                               })


    production = define_production()

    # land factors retrieved from Romain's LCI: no information was given regarding the references for these figures: *ask him!
    land_factor = 0.09 if p.stack_type == 'PEM' else 0.12


    # Infrastructure eol
    def define_eol():
        return agb.newActivity(USER_DB, "infrastructure end of life for H2 production",
                               unit="unit",
                               exchanges={
                                   t_Stack_activity: 1 / ir.H2_produced,
                                   t_BoP_activity: 1 / ir.H2_produced
                               })


    eol = define_eol()


    # Infrastructure
    def define_infrastructure():
        return agb.newActivity(USER_DB, "infrastructure for H2 production",
                               unit="unit",
                               exchanges={
                                   stack_activity: ir.n_stacks / ir.H2_produced,
                                   bop_activity: 1 / ir.H2_produced,
                                   Occupation_ind: land_factor / ir.electro_capacity_kW / ir.H2_produced / p.BoP_LT_y,
                                   Transformation_from_ind: land_factor / ir.H2_produced,
                                   Transformation_to_ind: land_factor / ir.H2_produced,
                                   eol: 1,
                               })


    infra = define_infrastructure()

    if p.storage == "Tank" :
        storage_act = tank
        dx = 1
    else:
        dx = float(p.n_tanks / ir.H2_produced)
        storage_act = null_activity


    storage =  agb.newActivity(USER_DB, "H2 storage",
                       unit="unit",
                       exchanges={
                           storage_act: dx
                       })

    if 'counter' not in st.session_state:
        st.session_state.counter = 1

    order = f"result {st.session_state.counter}"
    system = agb.newActivity(USER_DB, name=order,
                           unit="kg",
                           exchanges={
                               production: 1,
                               infra: 1,
                               storage: 1
                           })

    result_table_H2 = agb.compute_impacts(
        system,
        IMPACTS,
        param_g = p.grid_market,
        param_pv = p.PV_database,
    )


    # Set pandas to display in scientific notation globally
    pd.options.display.float_format = '{:.2e}'.format

    # Or apply formatting specifically to result_table_H2
    result_table_H2 = result_table_H2.applymap(lambda x: '{:.2e}'.format(x) if isinstance(x, (int, float)) else x)

    header_mapping = {
        'climate change no LT - global warming potential (GWP100) no LT[kg CO2-Eq]': 'climate change [kg CO2-Eq]',
        'material resources: metals/minerals no LT - abiotic depletion potential (ADP): elements (ultimate reserves) no LT[kg Sb-Eq]': 'material resources [kg Sb-Eq]',
        'land use no LT - soil quality index no LT[dimensionless]': 'land use [dimensionless]',
        'water use no LT - user deprivation potential (deprivation-weighted water consumption) no LT[m3 world eq. deprived]': 'water use [m3 world eq. deprived]',
        'acidification no LT - accumulated exceedance (AE) no LT[mol H+-Eq]': 'acidification [mol H+-Eq]',
        'eutrophication: marine no LT - fraction of nutrients reaching marine end compartment (N) no LT[kg N-Eq]': 'eutrophication: marine [kg N-Eq]',
        'eutrophication: freshwater no LT - fraction of nutrients reaching freshwater end compartment (P) no LT[kg P-Eq]': 'eutrophication: freshwater [kg P-Eq]',
        'eutrophication: terrestrial no LT - accumulated exceedance (AE) no LT[mol N-Eq]': 'eutrophication: terrestrial [mol N-Eq]',
        'ionising radiation: human health no LT - human exposure efficiency relative to u235 no LT[kBq U235-Eq]': 'ionising radiation [kBq U235-Eq]',
        'energy resources: non-renewable no LT - abiotic depletion potential (ADP): fossil fuels no LT[MJ, net calorific value]': 'energy resources: non-renewable [MJ, net calorific value]'
    }

    # Rename the columns in the result table using the mapping
    result_table_H2.rename(columns=header_mapping, inplace=True)


    lca_result = result_table_H2.iloc[:, :]

    return lca_result, system,



def get_city_coordinates(city_name):
    geocoder = OpenCageGeocode(API_KEY)
    query = f'{city_name}, France'
    results = geocoder.geocode(query)
    if results and len(results):
        # Get the latitude and longitude values
        lat = results[0]['geometry']['lat']
        lng = results[0]['geometry']['lng']

        # Round the latitude and longitude to 4 decimal places
        rounded_lat = round(lat, 4)
        rounded_lng = round(lng, 4)

        return rounded_lat, rounded_lng
    else:
        return None

@cache_data
def get_pv_prod_data(lat, lon, pv_cap_kW):
    years = [2018, 2019, 2020]
    data_frames = []

    for year in years:
        URL = f"https://re.jrc.ec.europa.eu/api/v5_2/seriescalc?lat={lat:.3f}&lon={lon:.3f}&raddatabase=PVGIS-SARAH2&browser=1&outputformat=csv&userhorizon=&usehorizon=1&angle=&aspect=&startyear={year}&endyear={year}&mountingplace=free&optimalinclination=0&optimalangles=1&js=1&select_database_hourly=PVGIS-SARAH2&hstartyear={year}&hendyear={year}&trackingtype=0&hourlyoptimalangles=1&pvcalculation=1&pvtechchoice=crystSi&peakpower={pv_cap_kW}&loss=14&components=1"

        r = urlopen(URL)
        o = StringIO(r.read().decode())

        data2 = []
        start_line = 12
        header = ["DateTime", "elec_W"]

        o.seek(0)
        for i, line in enumerate(o):
            if i >= start_line:
                if line.strip() == "":
                    break
                columns = line.strip().split(',')
                if len(columns) >= 2:
                    data2.append([columns[0], columns[1]])

        df = pd.DataFrame(data2, columns=header)
        df['elec_W'] = pd.to_numeric(df['elec_W'], errors='coerce')
        df['elec_Wh'] = df['elec_W']
        df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y%m%d:%H%M')

        if year == 2020:
            df = df[~((df['DateTime'].dt.month == 2) & (df['DateTime'].dt.day == 29))]

        data_frames.append(df)

    avg_df = data_frames[0].copy()
    avg_df['elec_W'] = sum(df['elec_W'] for df in data_frames) / len(years)
    avg_df['elec_Wh'] = avg_df['elec_W']
    df['elec_W']= avg_df['elec_W']
    return df


def get_tooltip_html():
    tooltip_html1 = """
    <div class="tooltip">
        <span class="tooltiptext">
            <table>
                <thead>
                    <tr>
                        <th></th>
                        <th colspan='2'>AEC</th>
                        <th colspan='2'>PEM</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td></td><td>Current,&nbsp;2019</td><td>Future,&nbsp;2050</td><td>Current,&nbsp;2019</td><td>Future,&nbsp;2050</td></tr>
                    <tr><td>Stack lifetime (operating hours)</td><td>60000-90000</td><td>100000-150000</td><td>30000-90000</td><td>100000-150000</td></tr>
                </tbody>
            </table>
            <p>source: IEA, The Future of Hydrogen - Seizing today’s opportunities, International Energy Agency, 2019.</p>
        </span>
        <span id="tooltip_trigger1">Need help with prospective Stack lifetime data? Check this info  <i class="fas fa-lightbulb"></i></span>
    </div>
    """

    tooltip_html2 = """
    <div class="tooltip">
        <span class="tooltiptext">
            <table>
                <thead>
                    <tr>
                        <th></th>
                        <th colspan='2'>AEC</th>
                        <th colspan='2'>PEM</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td></td><td>Current,&nbsp;2019</td><td>Future,&nbsp;2050</td><td>Current,&nbsp;2019</td><td>Future,&nbsp;2050</td></tr>
                    <tr><td>Electrical efficiency (%LHV)</td><td>63-70</td><td>70-80</td><td>56-60</td><td>67-74</td></tr>
                </tbody>
            </table>
            <p>source: IEA, The Future of Hydrogen - Seizing today’s opportunities, International Energy Agency, 2019.</p>
        </span>
        <span id="tooltip_trigger2">Need help with prospective Stack efficiency data? Check this info  <i class="fas fa-lightbulb"></i></span>
    </div>
    """
    return tooltip_html1, tooltip_html2


def get_js_code():
    js_code = """
    <script>
        // Add event listener to show tooltip on mouseover
        document.getElementById("tooltip_trigger1").addEventListener("mouseover", function() {
            var tooltipText = document.querySelector(".tooltiptext");
            tooltipText.style.visibility = "visible";
        });

        // Add event listener to hide tooltip on mouseout
        document.getElementById("tooltip_trigger1").addEventListener("mouseout", function() {
            var tooltipText = document.querySelector(".tooltiptext");
            tooltipText.style.visibility = "hidden";
        });

        // Add event listener to show tooltip on mouseover
        document.getElementById("tooltip_trigger2").addEventListener("mouseover", function() {
            var tooltipText = document.querySelector(".tooltiptext");
            tooltipText.style.visibility = "visible";
        });

        // Add event listener to hide tooltip on mouseout
        document.getElementById("tooltip_trigger2").addEventListener("mouseout", function() {
            var tooltipText = document.querySelector(".tooltiptext");
            tooltipText.style.visibility = "hidden";
        });
    </script>
    """
    return js_code


def get_css_code():
    css_code = """
    <style>
        .tooltip {
            position: relative;
            display: inline-block;
            cursor: help;
        }

        .tooltiptext {
            visibility: hidden;
            width: 700px;
            background-color: white;
            color: black;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            top: 125%;
            left: 0;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
            opacity: 1; /* Make the tooltip non-transparent */
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
        }
    </style>
    """
    return css_code