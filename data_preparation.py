import numpy as np
import pandas as pd

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
ELECTRIFICATION_OPTIONS = [GRID, MG, SHS]
BAU_SCENARIO = 'bau'
SE4ALL_SCENARIO = 'se4all'
SE4ALL_FLEX_SCENARIO = 'se4all_shift'
PROG_SCENARIO = 'prog'
SCENARIOS = [BAU_SCENARIO, SE4ALL_SCENARIO, SE4ALL_FLEX_SCENARIO, PROG_SCENARIO]

# Names for display
SCENARIOS_DICT = {
    BAU_SCENARIO: 'BaU',
    SE4ALL_SCENARIO: 'SE4All',
    SE4ALL_FLEX_SCENARIO: 'SE4All Flex',
    PROG_SCENARIO: 'prOG',
}
ELECTRIFICATION_DICT = {
    GRID: 'Grid',
    MG: 'Mini Grid',
    SHS: 'Solar Home System'
}


# column names of the exogenous results
POP_GET = ['pop_get_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS]
HH_GET = ['hh_get_%s_2030' % opt for opt in ELECTRIFICATION_OPTIONS]
HH_CAP = ['hh_%s_capacity' % opt for opt in ELECTRIFICATION_OPTIONS]
HH_SCN2 = ['hh_cap_scn2_%s_capacity' % opt for opt in ELECTRIFICATION_OPTIONS]
EXO_RESULTS = POP_GET + HH_GET + HH_CAP + HH_SCN2

# source http://www.worldbank.org/content/dam/Worldbank/Topics/Energy%20and%20Extract/
# Beyond_Connections_Energy_Access_Redefined_Exec_ESMAP_2015.pdf
MIN_TIER_LEVEL = 3
MIN_RATED_CAPACITY = {1: 3, 2: 50, 3: 200, 4: 800, 5: 2000}  # index is TIER level [W]
MIN_ANNUAL_CONSUMPTION = {1: 4.5, 2: 73, 3: 365, 4: 1250, 5: 3000}  # index is TIER level [kWh/a]
RATIO_CAP_CONSUMPTION = {}

# Investment Cost Source: Arranz and Worldbank,
# BENCHMARKING STUDY OF SOLAR PV MINIGRIDS INVESTMENT COSTS, 2017 (Jabref)
# unit is USD per household
MEDIAN_INVESTMENT_COST = {1: 742, 2: 1273, 3: 2516, 4: 5277, 5: 5492}

# Currency conversion
USD_TO_EUR = 0.87
FCFA_TO_EUR = 0.0015

# drives for the socio-economic model
MENTI = pd.DataFrame({MG: [3, 13. / 6, 19. / 6, 3.25, 11. / 3],
                      SHS: [23. / 12, 4.5, 37. / 12, 17. / 6, 41. / 12],
                      'labels': [
                          'high_gdp',
                          'high_mobile_money',
                          'high_ease_doing_business',
                          'low_corruption',
                          'high_grid_weakness'
                      ]
                      })
MENTI = MENTI.set_index('labels')

MENTI_DRIVES = ['gdp', 'mobile_money', 'ease_doing_business', 'corruption', 'weak_grid']

# $RT_shift_factors.$P$2
WEIGHT_MENTIS = 0.2
# -->WEIGHT_GRID = 0.8 ($RT_shift_factors.$O$2)  and  WEIGHT_GRID = 1 - WEIGHT_MENTIS
RISE_INDICES = ['rise_%s' % opt for opt in ELECTRIFICATION_OPTIONS]
SHIFT_MENTI = ['shift_menti_mg', 'shift_menti_shs']


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


def _find_tier_level(yearly_consumption):
    """Find the lower bound of the TIER level based on the electrical yearly consumption

    Compare the yearly electricity consumption between the minimal yearly consumptions
    for tier levels (3, 4) and (4, 5).

    ### APPROXIMATION ###

    If the yearly_consumption is lower that the minimum consumption for tier level 3
    then tier level 3 is returned nevertheless.

    :param yearly_consumption: yearly electricity consumption per household
    """
    answer = 3
    for tier_level in [3, 4]:
        if MIN_ANNUAL_CONSUMPTION[tier_level] \
                <= yearly_consumption \
                < MIN_ANNUAL_CONSUMPTION[tier_level + 1]:
            answer = tier_level
    return answer


def get_peak_capacity_from_yearly_consumption(yearly_consumption):
    """Use linear interpolation of the minimum values of capacity and consumption.

    :param yearly_consumption: yearly consumption per household in kWh/year
    :return: peak capacity in kW
    """
    # Find the lower tier level bound
    tier_level = _find_tier_level(yearly_consumption)
    # Renaming the variables to explicitly show the formula used
    x = yearly_consumption
    m = RATIO_CAP_CONSUMPTION[tier_level]
    x_i = MIN_ANNUAL_CONSUMPTION[tier_level]
    y_i = MIN_RATED_CAPACITY[tier_level]
    return (m * (x - x_i) + y_i) * 1e-3


def map_gdp_class(gdp_per_capita):
    """Assign an index value to differentiate gdp per capita."""
    answer = 1
    if gdp_per_capita < 1500:
        answer = 0.5
    if gdp_per_capita < 700:
        answer = 0
    return answer


def map_mobile_money_class(mobile_money):
    """Assign an index value to differentiate mobile_money."""
    answer = 1
    if mobile_money <= 0.21:
        answer = 0.5
    if mobile_money <= 0.12:
        answer = 0
    return answer


def map_ease_doing_business_class(business_ease):
    """Assign an index value to differentiate ease of doing business."""
    answer = 1
    if business_ease <= 164:
        answer = 0.5
    if business_ease < 131:
        answer = 0
    return answer


def map_corruption_class(corruption_idx):
    """Assign an index value to differentiate corruption."""
    answer = 1
    if corruption_idx <= 33:
        answer = 0.5
    if corruption_idx < 26:
        answer = 0
    return answer


def map_weak_grid_class(weak_grid_idx):
    """Assign an index value to differentiate weak grid."""
    answer = 1
    if weak_grid_idx <= 9:
        answer = 0.5
    if weak_grid_idx < 4.5:
        answer = 0
    return answer


def map_tier_yearly_consumption(
        yearly_consumption,
        electrification_option_share,
        tier_level=MIN_TIER_LEVEL
):
    """Assign yearly consumption adjusted for tier level."""
    if yearly_consumption < MIN_ANNUAL_CONSUMPTION[tier_level] / electrification_option_share:
        answer = MIN_ANNUAL_CONSUMPTION[tier_level]
    else:
        answer = yearly_consumption * electrification_option_share
    return answer


def map_capped_tier_yearly_consumption(
        yearly_consumption,
        tier_level=4
):
    """Assign yearly consumption from the upper tier level bound."""
    if yearly_consumption >= MIN_ANNUAL_CONSUMPTION[tier_level]:
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


def prepare_endogenous_variables(input_df, shs_sales_volumes=None, tier_level=MIN_TIER_LEVEL):

    if shs_sales_volumes is None:
        shs_sales_volumes = SHS_SALES_VOLUMES
    df = input_df.copy()

    # compute the grid and mg yearly consumption adjusted for tier level
    for opt in [GRID, MG]:
        df['hh_%s_tier_yearly_electricity_consumption' % opt] = \
            np.vectorize(map_tier_yearly_consumption)(
                df.hh_yearly_electricity_consumption,
                df['hh_%s_share' % opt],
                tier_level
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

    # peak demand
    for opt in [GRID, MG]:
        df['hh_%s_tier_peak_demand' % opt] = \
            df['hh_%s_tier_yearly_electricity_consumption' % opt].map(
                get_peak_capacity_from_yearly_consumption,
                na_action='ignore'
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


def prepare_se4all_shift_drives(df):
    # compute the shift drives
    df['weak_grid_class'] = df['weak_grid_index'].map(map_weak_grid_class, na_action='ignore')
    df['corruption_class'] = df['corruption_index'].map(map_corruption_class, na_action='ignore')
    df['ease_doing_business_class'] = df['ease_doing_business_index'].map(
        map_ease_doing_business_class, na_action='ignore')
    df['gdp_class'] = df['gdp_per_capita'].map(map_gdp_class, na_action='ignore')
    df['mobile_money'] = df['mobile_money_2017'].fillna(df['mobile_money_2014'])
    df['mobile_money_class'] = df['mobile_money'].map(
        map_mobile_money_class, na_action='ignore').fillna(0)


def apply_se4all_shift_drives(df, menti=None):
    if menti is None:
        menti = MENTI
    # apply the shift drives
    for opt in [MG, SHS]:
        df['shift_menti_%s' % opt] = \
            df.gdp_class * menti[opt]['high_gdp'] \
            + df.mobile_money_class * menti[opt]['high_mobile_money'] \
            + df.ease_doing_business_class * menti[opt]['high_ease_doing_business'] \
            + df.corruption_class * menti[opt]['low_corruption'] \
            + df.weak_grid_class * menti[opt]['high_grid_weakness']


def prepare_se4all_data(
        input_df,
        weight_mentis=WEIGHT_MENTIS,
        fixed_shift_drives=True
):
    # for se4all+SHIFT

    df = input_df.copy()

    weight_grid = 1 - weight_mentis

    if fixed_shift_drives:
        prepare_se4all_shift_drives(df)
    apply_se4all_shift_drives(df)

    for opt in ELECTRIFICATION_OPTIONS:
        df['endo_pop_get_%s_2030' % opt] = df['pop_%s_share' % opt] * df.pop_newly_electrified_2030

    # to normalize the senarii weigthed sum
    weighted_norm = \
        df.loc[:, RISE_INDICES].sum(axis=1) * weight_grid \
        + df.loc[:, SHIFT_MENTI].sum(axis=1) * weight_mentis

    non_zero_indices = df.loc[:, RISE_INDICES + SHIFT_MENTI].sum(axis=1) != 0

    for col in ['shift_grid_share', 'shift_grid_to_mg_share', 'shift_grid_to_shs_share']:
        # if the sum of the RISE indices and shift MENTI is 0 the corresponding rows
        # in the given columns are set to 0
        df.loc[df.loc[:, RISE_INDICES + SHIFT_MENTI].sum(axis=1) == 0, col] = 0

    # share of population which will be on the grid in the se4all+SHIFT scenario
    df.loc[non_zero_indices, 'shift_grid_share'] = df.rise_grid * weight_grid / weighted_norm

    # share of population which will have changed from grid to mg in the se4all+SHIFT scenario
    df.loc[non_zero_indices, 'shift_grid_to_mg_share'] = \
        (df.rise_mg * weight_grid + df.shift_menti_mg * weight_mentis) / weighted_norm

    # share of population which will have changed from grid to shs in the se4all+SHIFT scenario
    df.loc[non_zero_indices, 'shift_grid_to_shs_share'] = \
        (df.rise_shs * weight_grid + df.shift_menti_shs * weight_mentis) / weighted_norm

    # SHARED WITH prOG
    # if the predicted mg share is larger than the predicted grid share, the number of people
    # predicted to use mg in the se4all+SHIFT scenario is returned, otherwise it is set to 0
    df.loc[df.shift_grid_to_mg_share >= df.shift_grid_share, 'shift_pop_grid_to_mg'] = \
        df.shift_grid_to_mg_share * df.endo_pop_get_grid_2030
    df.loc[df.shift_grid_to_mg_share < df.shift_grid_share, 'shift_pop_grid_to_mg'] = 0

    # if the predicted shs share is larger than the predicted grid share, the number of people
    # predicted to use shs in the se4all+SHIFT scenario is returned, otherwise it is set to 0
    df.loc[df.shift_grid_to_shs_share >= df.shift_grid_share, 'shift_pop_grid_to_shs'] = \
        df.shift_grid_to_shs_share * df.endo_pop_get_grid_2030
    df.loc[df.shift_grid_to_shs_share < df.shift_grid_share, 'shift_pop_grid_to_shs'] = 0

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


def prepare_scenario_data(df, scenario, prepare_endogenous=False, tier_level=MIN_TIER_LEVEL):
    """Prepare the data prior to compute the exogenous results for a given scenario.
    :param df (pandas.DataFrame): a dataframe for which the 'prepare_endogenous_variables' has
    been already applied (if prepare_endogenous is not True)
    :param scenario (str): name of the scenario
    :param prepare_endogenous (bool):
    :return: a copy of the dataframe with the scenario specific data
    """
    if prepare_endogenous:
        df = prepare_endogenous_variables(input_df=df, tier_level=tier_level)

    if scenario == BAU_SCENARIO:
        df = prepare_bau_data(input_df=df)
    elif SE4ALL_SCENARIO in scenario:
        df = prepare_se4all_data(input_df=df)
    elif scenario == PROG_SCENARIO:
        df = prepare_prog_data(input_df=df)
    return df


def _compute_ghg_emissions(df):
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
        * df.hh_grid_tier_yearly_electricity_consumption\
        * (df.grid_emission_factor / 1000)

    df['ghg_mg_2030'] = \
        (df.pop_get_mg_2030 / df.hh_av_size) \
        * df.hh_mg_tier_yearly_electricity_consumption \
        * (df.mg_emission_factor / 1000)

    df['ghg_shs_2030'] = df.pop_get_shs_2030 * df.shs_emission_factor

    df['ghg_no_access_2030'] = \
        (df.pop_no_access_2030 / df.hh_av_size) \
        * df.hh_no_access_consumption \
        * (df.no_access_emission_factor / 1000)

    # consider the upper tier level minimal consumption value instead of the actual value
    df['hh_grid_tier_cap_yearly_electricity_consumption'] = \
        df.hh_grid_tier_yearly_electricity_consumption.map(map_capped_tier_yearly_consumption)

    df['hh_mg_tier_cap_yearly_electricity_consumption'] = \
        df.hh_grid_tier_cap_yearly_electricity_consumption * 0.8

    df['tier_capped_ghg_grid_2030'] = \
        (df.pop_get_grid_2030 / df.hh_av_size) \
        * df.hh_grid_tier_cap_yearly_electricity_consumption\
        * (df.grid_emission_factor / 1000)

    df['tier_capped_ghg_mg_2030'] = \
        (df.pop_get_mg_2030 / df.hh_av_size) \
        * df.hh_mg_tier_cap_yearly_electricity_consumption \
        * (df.mg_emission_factor / 1000)

    df['tier_capped_ghg_shs_2030'] = df.ghg_shs_2030

    df['tier_capped_ghg_no_access_2030'] = df.ghg_no_access_2030


def _compute_investment_cost(df):
    """Compute investment costs in EUR in `extract_results_scenario."""
    m, h = _linear_investment_cost()

    df['mg_investment_cost_per_kW'] = (df.hh_mg_tier_peak_demand * m + h) * USD_TO_EUR
    df['mg_investment_cost'] = df.mg_investment_cost_per_kW * df.hh_mg_capacity
    df['shs_investment_cost'] = df.hh_shs_capacity * SHS_AVERAGE_INVESTMENT_COST
    df['tier_capped_mg_investment_cost'] = \
        df.mg_investment_cost_per_kW * df.hh_cap_scn2_mg_capacity
    df['tier_capped_shs_investment_cost'] = \
        df.hh_cap_scn2_shs_capacity * SHS_AVERAGE_INVESTMENT_COST



def extract_results_scenario(input_df, scenario, regions=None, bau_data=None):
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
    elif scenario in [SE4ALL_SCENARIO, SE4ALL_FLEX_SCENARIO, PROG_SCENARIO]:
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

    _compute_ghg_emissions(df)
    _compute_investment_cost(df)

    return df


def compute_ndc_results_from_raw_data(scenario, fname='data/raw_data.csv'):
    """Compute the exogenous results from the raw data for a given scenario
    :param scenario (str): name of the scenario
    :param fname (str): path to the raw data csv file
    :return:
    """
    # Load data from csv
    df = pd.read_csv(fname, float_precision='high')
    # Compute endogenous results for the given scenario
    df = prepare_scenario_data(df, scenario, prepare_endogenous=True)
    # Compute the exogenous results
    return extract_results_scenario(df, scenario)
