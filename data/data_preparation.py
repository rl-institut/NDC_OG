import logging
import numpy as np
import pandas as pd
import dash_html_components as html

RAW_DATA_LABELS = [
    'region',
    'pop_grid_share',
    'hh_yearly_electricity_consumption',
    'rise_shs',
    'country_iso',
    'country',
    'ease_doing_business_index',
    'pop_2017',
    'pop_shs_share',
    'rise_mg',
    'weak_grid_index',
    'dark_rate',
    'pop_mg_share',
    'gdp_per_capita',
    'hh_mg_share',
    'electrification_rate',
    'mobile_money_2014',
    'hh_av_size',
    'hh_grid_share',
    'corruption_index',
    'pop_2030',
    'rise_grid',
    'mobile_money_2017'
]

EXOGENOUS_RESULTS_LABELS = [
    'pop_newly_electrified_2030',
    'hh_grid_tier_peak_demand',
    'pop_rel_growth',
    'hh_mg_tier_peak_demand',
    'shs_unit_av_capacity',
    'cap_sn2_grid_tier_up',
    'pop_electrified_2017',
    'pop_dark_2017',
    'cap_sn2_shs_tier_up',
    'hh_mg_tier_yearly_electricity_consumption',
    'hh_grid_tier_yearly_electricity_consumption',
    'cap_sn2_mg_tier_up'
]

GRID = 'grid'
MG = 'mg'
SHS = 'shs'
NO_ACCESS = 'No Electricity'
ELECTRIFICATION_OPTIONS = [GRID, MG, SHS]
BAU_SCENARIO = 'bau'
SE4ALL_SCENARIO = 'se4all'
SE4ALL_FLEX_SCENARIO = 'se4all_shift'
PROG_SCENARIO = 'prog'
SCENARIOS = [BAU_SCENARIO, SE4ALL_SCENARIO, PROG_SCENARIO]

# Names for display
SCENARIOS_DICT = {
    BAU_SCENARIO: 'BaU',
    SE4ALL_SCENARIO: 'SE4All',
    PROG_SCENARIO: 'prOG',
}
SCENARIOS_DESCRIPTIONS = {
    BAU_SCENARIO:
        [html.H4('What it shows:'), '''The Business-as-Usual (BaU) scenario quantifies the number of new technology-specific electrifications (Grid Extension, Mini-Grids or Solar-Home Systems) until 2030 by projecting current business-as-usual growth rates into the future.''',
         html.H4('How it is obtained:'),  '''Regional projections of electrification rates and technologies are mapped to the country-level and modelled until 2030. The BaU scenario is based on the "New Policies" Scenario of the ''', html.A(children="international Energy Agency’s World Energy Outlook 2018", href='https://www.iea.org/weo2018/scenarios/'), '''. '''],
    SE4ALL_SCENARIO:
        [html.H4('What it shows:'), '''The Sustainable-Energy-For-All (SE4ALL) scenario estimates the number of new technology-specific electrifications (Grid Extension, Mini-Grids or Solar-Home Systems) necessary to achieve the universal access goal until 2030. These estimations account for expected population growth rates and current infrastructure and current regulatory frameworks.''',
         html.H4('How it is obtained:'),  '''Existing datasets providing night lights, population densities and transmission grids are combined to estimate the number of people lacking access to electricity. Appropriate electrification options are determined based on the remoteness and density of neglected populations. In this way, the model estimates the share of people that remain to be electrified by either Grid Extension, Mini-Grid deployment or Solar-Home-System adoption until 2030.''',
         html.P('''The GIS based estimates are further refined by accounting for (the lack of) favourable technology-specific frameworks through the integration of ''', html.A(children="ESMAP’s RISE Indicators", href='https://rise.esmap.org/'), ''' into the model’s calculations. ''')],
    PROG_SCENARIO:
        [html.H4('What it shows:'), '''The Progressive-Off-Grid (prOG) scenario estimates the number of new technology-specific electrifications (Grid Extension, Mini-Grids or Solar-Home Systems) necessary to achieve the universal access goal until 2030. These estimations account for expected population growth rates and current infrastructure and progressive regulatory frameworks.''',
         html.H4('How it is obtained:'),  '''Existing datasets providing night lights, population densities and transmission grids are combined to estimate the number of people lacking access to electricity. Appropriate electrification options are determined based on the remoteness and density of neglected populations. For the 2030 horizon, in this way the model estimates the share of neglected people that remain to be electrified by either Grid Extension, Mini-Grid deployment or Solar-Home System adoption.''',
         html.P('''In the prOG scenario, the GIS based estimates are modified to showcase the impact of fully favourable off-grid (Mini-Grid and Solar Home Systems) frameworks through the integration of maximized ''', html.A(children="ESMAP’s RISE Indicators", href='https://rise.esmap.org/'), ''' into the model’s calculations. ''')]
}

ELECTRIFICATION_DICT = {
    GRID: 'Grid',
    MG: 'Mini Grid',
    SHS: 'Solar Home System',
    NO_ACCESS: NO_ACCESS
}

ELECTRIFICATION_DESCRIPTIONS = {
    GRID: 'Grid: Electrification is achieved by extension of the existing electricity \
grid network',
    MG: 'Mini Grid: Electrification is achieved via a set of electricity generators and possibly \
energy storage systems interconnected to a distribution network that supplies electricity \
to a localized group of customers',
    SHS: 'Solar Home System: Electrification is achieved for a single household via solar panels.'
}

# column names of the exogenous results
ENDO_POP_GET = ['endo_pop_get_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS]
POP_GET = ['pop_get_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS]
HH_GET = ['hh_get_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS]
HH_CAP = ['hh_%s_capacity' % opt for opt in ELECTRIFICATION_OPTIONS]
HH_SCN2 = ['hh_cap_scn2_%s_capacity' % opt for opt in ELECTRIFICATION_OPTIONS]
INVEST = ['%s_investment_cost' % opt for opt in ELECTRIFICATION_OPTIONS]
INVEST_CAP = ['tier_capped_%s_investment_cost' % opt for opt in ELECTRIFICATION_OPTIONS]
GHG = ['ghg_%s_cumul' % opt for opt in ELECTRIFICATION_OPTIONS] + ['ghg_no_access_cumul']
GHG_ER = ['ghg_%s_ER_cumul' % opt for opt in ELECTRIFICATION_OPTIONS] \
         + ['ghg_no_access_ER_cumul']
GHG_CAP = ['tier_capped_ghg_%s_cumul' % opt for opt in ELECTRIFICATION_OPTIONS] \
          + ['tier_capped_ghg_no_access_cumul']
GHG_CAP_ER = ['tier_capped_ghg_%s_ER_cumul' % opt for opt in ELECTRIFICATION_OPTIONS] \
             + ['tier_capped_ghg_no_access_ER_cumul']
GHG_ALL = GHG + GHG_ER + GHG_CAP + GHG_CAP_ER \
          + ['ghg_tot_cumul', 'tier_capped_ghg_tot_cumul'] \
          + ['ghg_tot_ER_cumul', 'tier_capped_ghg_tot_ER_cumul'] \
          + ['ghg_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS] \
          + ['tier_capped_ghg_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS]
EXO_RESULTS = POP_GET + HH_GET + HH_CAP + HH_SCN2 + INVEST + INVEST_CAP + GHG_ALL

# source http://www.worldbank.org/content/dam/Worldbank/Topics/Energy%20and%20Extract/
# Beyond_Connections_Energy_Access_Redefined_Exec_ESMAP_2015.pdf
MIN_TIER_LEVEL = 3
MIN_RATED_CAPACITY = {1: 3, 2: 50, 3: 200, 4: 800, 5: 2000}  # index is TIER level [W]
MIN_ANNUAL_CONSUMPTION = {1: 4.5, 2: 73, 3: 365, 4: 1250, 5: 3000}  # index is TIER level [kWh/a]
RATIO_CAP_CONSUMPTION = {}

# Investment cost, source :
GRID_INV_COST_HH = 2500

# Investment Cost Source: Arranz and Worldbank,
# BENCHMARKING STUDY OF SOLAR PV MINIGRIDS INVESTMENT COSTS, 2017 (Jabref)
# unit is USD per household
MEDIAN_INVESTMENT_COST = {1: 742, 2: 1273, 3: 2516, 4: 5277, 5: 5492}

RISE_INDICES = ['rise_%s' % opt for opt in ELECTRIFICATION_OPTIONS]

RISE_SUB_INDICATORS = pd.read_csv('data/RISE_indicators.csv').set_index('indicator')

RISE_SUB_INDICATOR_STRUCTURE = {}
for opt in ELECTRIFICATION_OPTIONS:
    RISE_SUB_INDICATOR_STRUCTURE[opt] = []
    sub_groups = RISE_SUB_INDICATORS.loc['rise_{}'.format(opt)].sub_indicator_group.unique()
    for j, sub_group in enumerate(sub_groups):
        sub_group_df = RISE_SUB_INDICATORS.loc['rise_{}'.format(opt)]
        sub_group_df = sub_group_df.loc[sub_group_df.sub_indicator_group == sub_group]
        RISE_SUB_INDICATOR_STRUCTURE[opt].append(len(sub_group_df.index))

POP_RES = 'pop'
INVEST_RES = 'invest'
GHG_RES = 'ghg'
GHG_ER_RES = 'ghg-er'


def prepare_results_tables(df, sce=BAU_SCENARIO, result_category=POP_RES, ghg_er=False):

    answer = np.array([0, 0, 0, 0])

    if result_category == POP_RES:
        pop = np.squeeze(df[POP_GET].values * 1e-6)
        # compute the percentage of population with electricity access
        df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0)
        # gather the values of the results to display in the table
        pop_res = np.squeeze(df[POP_GET].values * 100)

        hh_res = np.squeeze(df[HH_GET].values * 1e-6)

        if sce == BAU_SCENARIO:
            total_share = pop_res.sum()
            total_pop = df.pop_newly_electrified_2030
            pop_no_elec = total_pop * 1e-6 - pop.sum()
            pop_res_no_elec = 100 - total_share
            pop = np.append(pop, pop_no_elec)
            pop_res = np.append(pop_res, pop_res_no_elec)
            hh_av_size = np.round(pop[0]/hh_res[0], 2)
            hh_res = np.append(hh_res, pop_no_elec / hh_av_size)
        else:
            pop = np.append(pop, 0)
            pop_res = np.append(pop_res, 0)
            hh_res = np.append(hh_res, 0)
        answer = np.vstack([pop_res, pop, hh_res])
    elif result_category == INVEST_RES:

        # cap_res = np.append(np.squeeze(df[HH_CAP].values * 1e-3).round(0), np.nan)
        # cap2_res = np.append(np.squeeze(df[HH_SCN2].values * 1e-3).round(0), np.nan)
        invest_res = np.append(np.squeeze(df[INVEST].values * 1e-9).round(3), np.nan)
        invest2_res = np.append(np.squeeze(df[INVEST_CAP].values * 1e-9).round(3), np.nan)
        answer = np.vstack([invest_res, invest2_res])

    elif result_category in [GHG_RES, GHG_ER_RES]:
        ghg_res = np.squeeze(df[GHG].values * 1e-6).round(3)
        ghg2_res = np.squeeze(df[GHG_CAP].values * 1e-6).round(3)
        if ghg_er:
            ghg_er_res = np.squeeze(df[GHG_ER].values * 1e-6).round(3)
            ghg2_er_res = np.squeeze(df[GHG_CAP_ER].values * 1e-6).round(3)
            answer = np.vstack([ghg_res, ghg_er_res, ghg2_res, ghg2_er_res])
        else:
            answer = np.vstack([ghg_res, ghg2_res])

    return answer


def compute_rise_shifts(rise, pop_get, opt, flag=''):

    df = pd.DataFrame(
        data=[rise, pop_get, [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
        columns=ELECTRIFICATION_OPTIONS)

    n = ELECTRIFICATION_OPTIONS.index(df.iloc[0].idxmin())
    R_n = df.iloc[0].min()

    m = ELECTRIFICATION_OPTIONS.index(df.iloc[0].idxmax())
    R_m = df.iloc[0].max()

    p = list(set(range(3)) - set([m, n]))[0]
    R_p = df.iloc[0, p]

    # calulate n_i
    df.iloc[2] = df.iloc[1] / df.iloc[1].sum()

    Delta_n = (R_m - R_n) / 100

    df.iloc[4, n] = - df.iloc[1, n] * Delta_n

    norm = 0
    for j in [m, p]:
        delta_jn = (df.iloc[0, j] - df.iloc[0, n])
        norm = norm + delta_jn
        df.iloc[4, j] = np.abs(df.iloc[4, n]) * delta_jn

    df.iloc[4, [m, p]] = df.iloc[4, [m, p]] / norm

    # --------------------------------------------------------

    DeltaN_pm = df.iloc[1, p] * (R_m - R_p) / 100

    df.iloc[4, p] = df.iloc[4, p] - DeltaN_pm
    df.iloc[4, m] = df.iloc[4, m] + DeltaN_pm

    df.iloc[7] = df.iloc[4] + df.iloc[1]

    if df.iloc[4].sum() > 1e-6:
        logging.error(
            'Error ({}): the sum of the shifts ({}) is not equal to zero!'.format(
                flag,
                df.iloc[4].sum(),
            )
        )

    df['sum'] = df.sum(axis=1)

    df['labels'] = ['R_i', 'N_i', 'n_i', '', 'Delta N_i', 'Delta N_i / N_i',
                    '', 'Delta N_i + N_i']

    return df.iloc[4, ELECTRIFICATION_OPTIONS.index(opt)]


def _slope_capacity_vs_yearly_consumption(tier_level):
    """Linearize the relation between min rated capacity and min annual consumption

    y = m*x +h, the function returns m for the interval corresponding
    to [tier_level, tier_level +1]
    :param tier_level: either 3 or 4 (there are only 3 tier levels considered in this study)
    :return: the slope of the linear relation
    """
    if tier_level not in [1, 2, 3, 4]:
        raise ValueError
    m = (MIN_RATED_CAPACITY[tier_level + 1] - MIN_RATED_CAPACITY[tier_level]) \
        / (MIN_ANNUAL_CONSUMPTION[tier_level + 1] - MIN_ANNUAL_CONSUMPTION[tier_level])
    return m


def _linear_investment_cost():
    """Linearize the relation between averaged min rated capacity and median investment cost

    y = m*x +h, the function returns m for the interval corresponding
    to [tier_level=3, tier_level=4]
    :return: m and h of the linear relation
    """
    cost_tier = {}
    for tier_level in [3, 4]:
        mean_capacity = (MIN_RATED_CAPACITY[tier_level + 1] + MIN_RATED_CAPACITY[tier_level]) / 2.
        # mean cost for a given tier level in USD / kW
        cost_tier[tier_level] = 1000 * MEDIAN_INVESTMENT_COST[tier_level] / mean_capacity

    m = 1000 * (cost_tier[4] - cost_tier[3]) / (MIN_RATED_CAPACITY[4] - MIN_RATED_CAPACITY[3])
    h = cost_tier[3] - m * (MIN_RATED_CAPACITY[3] / 1000)
    return m, h


for tier_lvl in [1, 2, 3, 4]:
    RATIO_CAP_CONSUMPTION[tier_lvl] = _slope_capacity_vs_yearly_consumption(tier_lvl)
RATIO_CAP_CONSUMPTION[5] = RATIO_CAP_CONSUMPTION[4]


def _find_tier_level(yearly_consumption, min_tier_level):
    """Find the lower bound of the TIER level based on the electrical yearly consumption

    Compare the yearly electricity consumption between the minimal yearly consumptions
    for tier levels (3, 4) and (4, 5) and assigns a tier level of 3 and 4, respectively.

    If the yearly_consumption is lower that the minimum consumption for min_tier_level
    then min_tier_level is returned nevertheless.

    :param yearly_consumption: yearly electricity consumption per household
    :param min_tier_level: minimum TIER level
    :return: maximum between the actual TIER level and the min_tier_level
    """
    answer = min_tier_level
    for tier_level in [1, 2, 3, 4]:
        if MIN_ANNUAL_CONSUMPTION[tier_level] \
                <= yearly_consumption \
                < MIN_ANNUAL_CONSUMPTION[tier_level + 1]:
            answer = tier_level
    if yearly_consumption >= MIN_ANNUAL_CONSUMPTION[5]:
        answer = 5
    return np.max([answer, min_tier_level])


def get_peak_capacity_from_yearly_consumption(yearly_consumption, min_tier_level):
    """Use linear interpolation of the minimum values of capacity and consumption.

    :param yearly_consumption: yearly consumption per household in kWh/year
    :return: peak capacity in kW
    :param min_tier_level: minimum TIER level
    """
    # Find the lower tier level bound
    tier_level = _find_tier_level(yearly_consumption, min_tier_level)
    # Renaming the variables to explicitly show the formula used
    x = yearly_consumption
    m = RATIO_CAP_CONSUMPTION[tier_level]
    x_i = MIN_ANNUAL_CONSUMPTION[tier_level]
    y_i = MIN_RATED_CAPACITY[tier_level]
    return (m * (x - x_i) + y_i) * 1e-3


def map_tier_yearly_consumption(
        yearly_consumption,
        electrification_option_share,
        min_tier_level
):
    """Assign yearly consumption adjusted for tier level."""
    if yearly_consumption < MIN_ANNUAL_CONSUMPTION[min_tier_level] / electrification_option_share:
        answer = MIN_ANNUAL_CONSUMPTION[min_tier_level]
    else:
        answer = yearly_consumption * electrification_option_share
    return answer


def map_capped_tier_yearly_consumption(
        yearly_consumption,
        min_tier_level,
):
    tier_level = _find_tier_level(yearly_consumption, min_tier_level)
    """Assign yearly consumption from the upper tier level bound."""
    if yearly_consumption >= MIN_ANNUAL_CONSUMPTION[tier_level]:
        if tier_level == 5:
            tier_level = 4
        answer = MIN_ANNUAL_CONSUMPTION[tier_level + 1]
    else:
        answer = MIN_ANNUAL_CONSUMPTION[tier_level]
    return answer


def prepare_shs_power_and_sales_volumes():
    shs_sales_volumes = pd.read_csv('data/shs_sales_volumes.csv', comment='#')
    # compute the average of the product categories 5 to 7
    shs_sales_volumes['tot_5-7'] = shs_sales_volumes[['5', '6', '7']].sum(axis=1)

    shs_power_categories = pd.read_csv('data/shs_power_per_product_categories.csv', comment='#')

    # compute the average power for each category
    shs_power_categories['power_av'] = shs_power_categories[
        ['power_low', 'power_high']].mean(axis=1)

    # select only the average power for the product categories 5 to 7
    cat_power_av_5_7 = shs_power_categories['power_av'].loc[
        shs_power_categories.category >= 5].values
    # compute the average power per region (multiply the number units sold per product
    # categories by the average power of the respective category)
    power_av_5_7 = shs_sales_volumes[['5', '6', '7']].values * cat_power_av_5_7
    # compute the average unit power per region (divide the sum over the
    # categories by the total unit sold)

    # avoid the zero for the division
    shs_sales_volumes.loc[shs_sales_volumes['tot_5-7'] == 0, 'tot_5-7'] = 1
    shs_sales_volumes['weighted_tot_5-7 [W]'] = \
        power_av_5_7.sum(axis=1) \
        / shs_sales_volumes['tot_5-7'].values

    return shs_power_categories.set_index('category'), shs_sales_volumes.set_index('region')


def prepare_shs_investment_cost():
    """Compute the average cost of shs in EUR per kW."""
    shs_costs = pd.read_csv('data/shs_power_investment_cost.csv', comment='#')
    shs_costs['cost_per_kW'] = 1000 * shs_costs.investment / shs_costs.power
    # take the mean value of the mean cost per kW for each category
    return np.mean([shs_costs[shs_costs.category == idx].cost_per_kW.mean() for idx in [5, 6, 7]])


SHS_POWER_CATEGORIES, SHS_SALES_VOLUMES = prepare_shs_power_and_sales_volumes()
SHS_AVERAGE_INVESTMENT_COST = prepare_shs_investment_cost()


def extract_bau_data(fname='data/bau.csv'):
    bau_data = pd.read_csv(fname, comment='#')
    return bau_data.set_index('region')


BAU_DATA = extract_bau_data()


def shs_av_power(power_cat, shs_power_categories=None):
    if shs_power_categories is None:
        shs_power_categories = SHS_POWER_CATEGORIES
    return shs_power_categories.loc[power_cat, 'power_av']


def prepare_endogenous_variables(
        input_df,
        min_tier_level,
        shs_sales_volumes=None,
        # min_tier_level=MIN_TIER_LEVEL
):

    if shs_sales_volumes is None:
        shs_sales_volumes = SHS_SALES_VOLUMES
    df = input_df.copy()

    # compute the TIER level of the countries base on their electricity consumption
    df['lower_tier_level'] = np.vectorize(_find_tier_level)(
        df.hh_yearly_electricity_consumption,
        min_tier_level
    )

    # compute the grid and mg yearly consumption adjusted for tier level
    for opt in [GRID, MG]:
        df['hh_%s_tier_yearly_electricity_consumption' % opt] = \
            np.vectorize(map_tier_yearly_consumption)(
                df.hh_yearly_electricity_consumption,
                df['hh_%s_share' % opt],
                min_tier_level
            )

    df['shs_unit_av_capacity'] = df.region.map(
        lambda region: shs_sales_volumes.loc[region]['weighted_tot_5-7 [W]']
    )

    opt = GRID
    for tier_level in [5, 4]:
        df.loc[
            df.hh_yearly_electricity_consumption <= MIN_ANNUAL_CONSUMPTION[tier_level],
            'cap_sn2_%s_tier_up' % opt] = MIN_RATED_CAPACITY[tier_level] / 1000

    opt = MG
    df['cap_sn2_%s_tier_up' % opt] = df.cap_sn2_grid_tier_up * df.hh_mg_share

    opt = SHS
    df['cap_sn2_%s_tier_up' % opt] = df.shs_unit_av_capacity.map(
        lambda shs_cap: shs_av_power(6) if shs_cap <= shs_av_power(5) else shs_av_power(7)
    )

    # peak demand computed row-wise and depending on the minimum tier level
    for opt in [GRID, MG]:
        df['hh_%s_tier_peak_demand' % opt] = \
            np.vectorize(get_peak_capacity_from_yearly_consumption)(
                df['hh_%s_tier_yearly_electricity_consumption' % opt],
                min_tier_level
            )

    df['pop_rel_growth'] = df.pop_2030 / df.pop_2017
    df['pop_dark_2017'] = df.pop_2017 * df.dark_rate
    df['pop_newly_electrified_2030'] = df.pop_rel_growth * df.pop_dark_2017
    df['pop_electrified_2017'] = df.electrification_rate * df.pop_2017

    return df


def prepare_bau_data(input_df, bau_data=None):

    if bau_data is None:
        bau_data = BAU_DATA
    df = input_df.copy()

    df['iea_regional_electricity_coverage'] = df['region'].map(
        lambda region: bau_data.loc[region]['iea_regional_electricity_coverage'])
    df.loc[df.country_iso == 'IND', 'iea_regional_electricity_coverage'] = 1
    df.loc[df.country_iso == 'IDN', 'iea_regional_electricity_coverage'] = 1
    df.loc[df.country_iso == 'YEM', 'iea_regional_electricity_coverage'] = 0.95

    df['bau_pop_newly_electrified'] = \
        df.iea_regional_electricity_coverage \
        * df.pop_newly_electrified_2030

    for opt in ELECTRIFICATION_OPTIONS:
        # assign the regional electricity share for each options
        df['bau_pop_%s_share' % opt] = df['region'].map(
            lambda region: bau_data.loc[region]['%s_share' % opt])

    return df


def prepare_se4all_data(
        input_df,
):
    # for se4all+SHIFT

    df = input_df.copy()

    for opt in ELECTRIFICATION_OPTIONS:
        df['endo_pop_get_%s_2030' % opt] = df['pop_%s_share' % opt] * df.pop_newly_electrified_2030

    shift_rise_df = []

    for idx, row in df.iterrows():
        shift_rise = []
        for opt in ELECTRIFICATION_OPTIONS:
            shift_rise.append(
                compute_rise_shifts(
                    row[RISE_INDICES].values,
                    row[ENDO_POP_GET].values,
                    opt,
                    row['country_iso'],
                )
            )
        shift_rise_df.append(shift_rise)
    shift_rise_df = np.vstack(shift_rise_df)

    for i, opt in enumerate(ELECTRIFICATION_OPTIONS):
        df['shift_rise_%s' % opt] = shift_rise_df[:, i]

    return df


def prepare_prog_data(input_df):
    # for prOG

    df = input_df.copy()

    df.rise_mg = 100
    df.rise_shs = 100

    for opt in ELECTRIFICATION_OPTIONS:
        df['endo_pop_get_%s_2030' % opt] = df['pop_%s_share' % opt] * df.pop_newly_electrified_2030

    weighted_norm = df.loc[:, RISE_INDICES].sum(axis=1)

    non_zero_indices = df.loc[:, RISE_INDICES].sum(axis=1) != 0

    for col in ['shift_grid_share', 'shift_grid_to_mg_share', 'shift_grid_to_shs_share']:
        # if the sum of the RISE indices and shift MENTI is 0 the corresponding rows in
        # the given columns are set to 0
        df.loc[df.loc[:, RISE_INDICES].sum(axis=1) == 0, col] = 0

    # share of population which will be on the grid in the se4all+SHIFT scenario
    df.loc[non_zero_indices, 'shift_grid_share'] = df.rise_grid / weighted_norm

    # share of population which will have changed from grid to mg in the se4all+SHIFT scenario
    df.loc[non_zero_indices, 'shift_grid_to_mg_share'] = df.rise_mg / weighted_norm

    # share of population which will have changed from grid to shs in the se4all+SHIFT scenario
    df.loc[non_zero_indices, 'shift_grid_to_shs_share'] = df.rise_shs / weighted_norm

    # Shared with se4all

    # if the predicted mg share is larger than the predicted grid share, the number of people
    # predited to use mg in the se4all+SHIFT scenario is returned
    # otherwise it is set to 0
    df.loc[df.shift_grid_to_mg_share >= df.shift_grid_share, 'shift_pop_grid_to_mg'] = \
        df.shift_grid_to_mg_share * df.endo_pop_get_grid_2030
    df.loc[df.shift_grid_to_mg_share < df.shift_grid_share, 'shift_pop_grid_to_mg'] = 0

    # if the predicted shs share is larger than the predicted grid share, the number of people
    # predited to use shs in the se4all+SHIFT scenario is returned
    # otherwise it is set to 0
    df.loc[df.shift_grid_to_shs_share >= df.shift_grid_share, 'shift_pop_grid_to_shs'] = \
        df.shift_grid_to_shs_share * df.endo_pop_get_grid_2030
    df.loc[df.shift_grid_to_shs_share < df.shift_grid_share, 'shift_pop_grid_to_shs'] = 0

    return df


def prepare_scenario_data(
        df,
        scenario,
        min_tier_level,
        prepare_endogenous=False,
):
    """Prepare the data prior to compute the exogenous results for a given scenario.
    :param df: (pandas.DataFrame) a dataframe for which the 'prepare_endogenous_variables' has
    been already applied (if prepare_endogenous is not True)
    :param scenario: (str) name of the scenario
    :param min_tier_level: (int) minimum TIER level
    :param prepare_endogenous: (bool)
    :return: a copy of the dataframe with the scenario specific data
    """
    if prepare_endogenous:
        df = prepare_endogenous_variables(input_df=df, min_tier_level=min_tier_level)

    if scenario == BAU_SCENARIO:
        df = prepare_bau_data(input_df=df)
    elif SE4ALL_SCENARIO in scenario:
        df = prepare_se4all_data(input_df=df)
    elif scenario == PROG_SCENARIO:
        df = prepare_prog_data(input_df=df)
    return df


def _compute_ghg_emissions(df, min_tier_level, bau_df=None):
    """Compute green house gases emissions in `extract_results_scenario."""
    # source : ???
    df['hh_no_access_consumption'] = 55
    # source : ???
    df['grid_emission_factor'] = df.emission_factor / 1000
    df['mg_emission_factor'] = 0.2
    df['shs_emission_factor'] = 0
    df['no_access_emission_factor'] = 6.8

    df['pop_no_access_2030'] = df.pop_newly_electrified_2030 - df[
        ['pop_get_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS]].sum(axis=1)
    # negative values are replaced by zero
    df.loc[df.pop_no_access_2030 < 0, 'pop_no_access_2030'] = 0

    df['ghg_grid_2030'] = \
        (df.pop_get_grid_2030 / df.hh_av_size) \
        * df.hh_grid_tier_yearly_electricity_consumption \
        * (df.grid_emission_factor / 1000)
    # integral is the surface of a triangle
    df['ghg_grid_cumul'] = 0.5 * df.ghg_grid_2030 * (2030 - 2017)

    df['ghg_mg_2030'] = \
        (df.pop_get_mg_2030 / df.hh_av_size) \
        * df.hh_mg_tier_yearly_electricity_consumption \
        * (df.mg_emission_factor / 1000)
    # integral is the surface of a triangle
    df['ghg_mg_cumul'] = 0.5 * df.ghg_mg_2030 * (2030 - 2017)

    df['ghg_shs_2030'] = df.pop_get_shs_2030 * df.shs_emission_factor
    # integral is the surface of a triangle
    df['ghg_shs_cumul'] = 0.5 * df.ghg_shs_2030 * (2030 - 2017)

    df['ghg_no_access_2017'] = \
        (df.dark_rate * df.pop_2017 / df.hh_av_size) \
        * df.hh_no_access_consumption \
        * (df.no_access_emission_factor / 1000)

    df['ghg_no_access_2030'] = \
        (df.pop_no_access_2030 / df.hh_av_size) \
        * df.hh_no_access_consumption \
        * (df.no_access_emission_factor / 1000)

    df['ghg_tot_2030'] = \
        df.ghg_grid_2030 \
        + df.ghg_mg_2030 \
        + df.ghg_shs_2030 \
        + df.ghg_no_access_2030

    df['ghg_tot_ER_cumul'] = 0
    df['ghg_grid_ER_cumul'] = 0
    df['ghg_mg_ER_cumul'] = 0
    df['ghg_shs_ER_cumul'] = 0
    df['ghg_no_access_ER_cumul'] = 0
    if bau_df is not None:
        df['ghg_ER_2030'] = bau_df.ghg_tot_2030 - df.ghg_tot_2030

        # integral is the surface of a triangle as everyone has access
        # to electricity by 2030 in these scenarios
        df['ghg_no_access_cumul'] = 0.5 * df.ghg_no_access_2017 * (2030 - 2017)
    else:
        # integral is the sum of the surfaces of a triangle and a square
        df['ghg_no_access_cumul'] = (
                                            df.ghg_no_access_2030
                                            + (df.ghg_no_access_2017 - df.ghg_no_access_2030) / 2
                                    ) * (2030 - 2017)

    df['ghg_tot_cumul'] = \
        df.ghg_grid_cumul \
        + df.ghg_mg_cumul \
        + df.ghg_shs_cumul \
        + df.ghg_no_access_cumul

    if bau_df is not None:
        df.ghg_tot_ER_cumul = bau_df.ghg_tot_cumul - df.ghg_tot_cumul
        df.ghg_grid_ER_cumul = bau_df.ghg_grid_cumul - df.ghg_grid_cumul
        df.ghg_mg_ER_cumul = bau_df.ghg_mg_cumul - df.ghg_mg_cumul
        df.ghg_shs_ER_cumul = bau_df.ghg_shs_cumul - df.ghg_shs_cumul
        df.ghg_no_access_ER_cumul = bau_df.ghg_no_access_cumul - df.ghg_no_access_cumul

    # consider the upper tier level minimal consumption value instead of the actual value
    df['hh_grid_tier_cap_yearly_electricity_consumption'] = \
        np.vectorize(map_capped_tier_yearly_consumption)(
            df.hh_grid_tier_yearly_electricity_consumption,
            min_tier_level=min_tier_level,
        )

    df['hh_mg_tier_cap_yearly_electricity_consumption'] = \
        df.hh_grid_tier_cap_yearly_electricity_consumption * 0.8

    df['tier_capped_ghg_grid_2030'] = \
        (df.pop_get_grid_2030 / df.hh_av_size) \
        * df.hh_grid_tier_cap_yearly_electricity_consumption \
        * (df.grid_emission_factor / 1000)
    # integral is the surface of a triangle
    df['tier_capped_ghg_grid_cumul'] = 0.5 * df.tier_capped_ghg_grid_2030 * (2030 - 2017)

    df['tier_capped_ghg_mg_2030'] = \
        (df.pop_get_mg_2030 / df.hh_av_size) \
        * df.hh_mg_tier_cap_yearly_electricity_consumption \
        * (df.mg_emission_factor / 1000)
    # integral is the surface of a triangle
    df['tier_capped_ghg_mg_cumul'] = 0.5 * df.tier_capped_ghg_mg_2030 * (2030 - 2017)

    df['tier_capped_ghg_shs_2030'] = df.ghg_shs_2030
    # integral is the surface of a triangle
    df['tier_capped_ghg_shs_cumul'] = 0.5 * df.tier_capped_ghg_shs_2030 * (2030 - 2017)

    df['tier_capped_ghg_no_access_2030'] = df.ghg_no_access_2030

    df['tier_capped_ghg_tot_2030'] = \
        df.tier_capped_ghg_grid_2030 \
        + df.tier_capped_ghg_mg_2030 \
        + df.tier_capped_ghg_no_access_2030

    df['tier_capped_ghg_tot_ER_cumul'] = 0
    df['tier_capped_ghg_grid_ER_cumul'] = 0
    df['tier_capped_ghg_mg_ER_cumul'] = 0
    df['tier_capped_ghg_shs_ER_cumul'] = 0
    df['tier_capped_ghg_no_access_ER_cumul'] = 0
    if bau_df is not None:
        df['tier_capped_ghg_ER_2030'] = \
            bau_df.tier_capped_ghg_tot_2030 \
            - df.tier_capped_ghg_tot_2030

        # integral is the surface of a triangle as everyone has access
        # to electricity by 2030 in these scenarios
        df['tier_capped_ghg_no_access_cumul'] = 0.5 * df.ghg_no_access_2017 * (2030 - 2017)
    else:
        # integral is the sum of the surfaces of a triangle and a square
        df['tier_capped_ghg_no_access_cumul'] = (
            df.ghg_no_access_2030
            + (df.ghg_no_access_2017 - df.ghg_no_access_2030) / 2
        ) * (2030 - 2017)

    df['tier_capped_ghg_tot_cumul'] = \
        df.tier_capped_ghg_grid_cumul \
        + df.tier_capped_ghg_mg_cumul \
        + df.tier_capped_ghg_shs_cumul \
        + df.tier_capped_ghg_no_access_cumul

    if bau_df is not None:
        df.tier_capped_ghg_tot_ER_cumul = \
            bau_df.tier_capped_ghg_tot_cumul \
            - df.tier_capped_ghg_tot_cumul
        df.tier_capped_ghg_grid_ER_cumul = \
            bau_df.tier_capped_ghg_grid_cumul - df.tier_capped_ghg_grid_cumul
        df.tier_capped_ghg_mg_ER_cumul = \
            bau_df.tier_capped_ghg_mg_cumul - df.tier_capped_ghg_mg_cumul
        df.tier_capped_ghg_shs_ER_cumul = \
            bau_df.tier_capped_ghg_shs_cumul - df.tier_capped_ghg_shs_cumul
        df.tier_capped_ghg_no_access_ER_cumul = \
            bau_df.tier_capped_ghg_no_access_cumul - df.tier_capped_ghg_no_access_cumul


def _compute_investment_cost(df):
    """Compute investment costs in USD in `extract_results_scenario."""
    m, h = _linear_investment_cost()
    df['grid_investment_cost'] = GRID_INV_COST_HH * df.pop_get_grid_2030.div(df.hh_av_size)
    df['mg_investment_cost_per_kW'] = df.hh_mg_tier_peak_demand * m + h
    df['mg_investment_cost'] = df.mg_investment_cost_per_kW * df.hh_mg_capacity
    df['shs_investment_cost'] = df.hh_shs_capacity * SHS_AVERAGE_INVESTMENT_COST
    df['tier_capped_grid_investment_cost'] = df.grid_investment_cost
    df['tier_capped_mg_investment_cost'] = \
        df.mg_investment_cost_per_kW * df.hh_cap_scn2_mg_capacity
    df['tier_capped_shs_investment_cost'] = \
        df.hh_cap_scn2_shs_capacity * SHS_AVERAGE_INVESTMENT_COST


def extract_results_scenario(
        input_df,
        scenario,
        min_tier_level,
        regions=None,
        bau_data=None,

):
    df = input_df.copy()

    if scenario == BAU_SCENARIO:
        if regions is None:
            regions = ['SSA', 'DA', 'LA']
        if bau_data is None:
            bau_data = BAU_DATA
        for opt in ELECTRIFICATION_OPTIONS:
            # not valid for other scenario than bau at the moment
            # create a columns with regional electrification option shares
            df['temp_%s' % opt] = df['region'].replace(regions, bau_data.loc[regions][
                '%s_share' % opt].to_list())

            # predicted number of people getting access to electricity (regional detail level)
            df['pop_get_%s_2030' % opt] = df.bau_pop_newly_electrified * df['temp_%s' % opt]
    elif scenario == PROG_SCENARIO:
        # SUMME(AA4:AB4) --> df.loc[:,['shift_pop_grid_to_mg' 'shift_pop_grid_to_shs']].sum(axis=1)
        # grid =D4-SUMME(AA4:AB4)
        opt = 'grid'
        # predicted number of people getting access to electricity (regional detail level)
        cumul_mg_shs = df.loc[:, ['shift_pop_grid_to_mg', 'shift_pop_grid_to_shs']].sum(axis=1)
        df['pop_get_%s_2030' % opt] = df['endo_pop_get_%s_2030' % opt] - cumul_mg_shs

        # mg =E5+AA5
        opt = 'mg'
        # predicted number of people getting access to electricity (regional detail level)
        df['pop_get_%s_2030' % opt] = \
            df['endo_pop_get_%s_2030' % opt] \
            + df['shift_pop_grid_to_%s' % opt]

        # shs =F6+AB6
        opt = 'shs'
        # predicted number of people getting access to electricity (regional detail level)
        df['pop_get_%s_2030' % opt] = \
            df['endo_pop_get_%s_2030' % opt] \
            + df['shift_pop_grid_to_%s' % opt]

    elif scenario == SE4ALL_SCENARIO:

        for opt in ELECTRIFICATION_OPTIONS:
            df['pop_get_%s_2030' % opt] = \
                df['endo_pop_get_%s_2030' % opt] + df['shift_rise_%s' % opt]
    else:
        raise ValueError

    for opt in ELECTRIFICATION_OPTIONS:
        # predicted number of household getting access to electricity (regional detail level)
        df['hh_get_%s_2030' % opt] = df['pop_get_%s_2030' % opt] / df.hh_av_size
        # predicted power (in kW) that the access to electricity will represent
        # (regional detail level)
        # the analysis is based on the peak demand for the grid and mg senarii, and the average
        # power of solar panel for shs scenario
        if opt in (GRID, MG):
            df['hh_%s_capacity' % opt] = df['hh_get_%s_2030' % opt] * df[
                'hh_%s_tier_peak_demand' % opt]
            df['hh_cap_scn2_%s_capacity' % opt] = df['hh_get_%s_2030' % opt] * df[
                'cap_sn2_%s_tier_up' % opt]
        else:
            df['hh_%s_capacity' % opt] = df['hh_get_%s_2030' % opt] * df[
                'shs_unit_av_capacity'] / 1000
            df['hh_cap_scn2_%s_capacity' % opt] = df['hh_get_%s_2030' % opt] * df[
                'cap_sn2_%s_tier_up' % opt] / 1000

    if scenario == BAU_SCENARIO:
        _compute_ghg_emissions(df, min_tier_level)
        df.to_csv('data/bau_results.csv')
    else:
        bau_data = pd.read_csv('data/bau_results.csv')
        _compute_ghg_emissions(df, min_tier_level, bau_df=bau_data)

    _compute_investment_cost(df)

    return df


def compute_ndc_results_from_raw_data(scenario, min_tier_level, fname='data/raw_data.csv'):
    """Compute the exogenous results from the raw data for a given scenario
    :param scenario: (str) name of the scenario
    :param min_tier_level: (int) minimum TIER level
    :param fname: (str) path to the raw data csv file
    :return:
    """
    # Load data from csv
    df = pd.read_csv(fname, float_precision='high')
    # Compute endogenous results for the given scenario
    df = prepare_scenario_data(df, scenario, min_tier_level, prepare_endogenous=True)
    # Compute the exogenous results
    return extract_results_scenario(df, scenario, min_tier_level)
