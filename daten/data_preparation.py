import numpy as np
import pandas as pd


GRID = 'grid'
MG = 'mg'
SHS = 'shs'

ELECTRIFICATION_OPTIONS = [GRID, MG, SHS]
BAU_SENARIO = 'bau'
SE4ALL_SHIFT_SENARIO = 'se4all_shift'
PROG_SENARIO = 'prog'
SENARII = [BAU_SENARIO, SE4ALL_SHIFT_SENARIO, PROG_SENARIO]

MIN_TIER_LEVEL = 3
MIN_RATED_CAPACITY = {3: 200, 4: 800, 5: 2000}  # index is TIER level [W]
MIN_ANNUAL_CONSUMPTION = {3: 365, 4: 1250, 5: 3000}  # index is TIER level [kWh/a]
RATIO_CAP_CONSUMPTION = {}

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

WEIGHT_GRID = 0.8  # $RT_shift_factors.$O$2
WEIGHT = 0.2  # $RT_shift_factors.$P$2
RISE_INDICES = ['rise_%s' % opt for opt in ELECTRIFICATION_OPTIONS]
SHIFT_MENTI = ['shift_menti_mg', 'shift_menti_shs']


def _slope_capacity_vs_yearly_consumption(tier_level):
    """Linearize the relation between min rated capacity and min annual consumption

    y = m*x +h, the function returns m for the interval corresponding
    to [tier_level, tier_level +1]
    :param tier_level: either 3 or 4 (there are only 3 tier levels considered in this study)
    :return: the slope of the linear relation
    """
    if tier_level not in [3, 4]:
        raise ValueError
    m = (MIN_RATED_CAPACITY[tier_level + 1] - MIN_RATED_CAPACITY[tier_level]) \
        / (MIN_ANNUAL_CONSUMPTION[tier_level + 1] - MIN_ANNUAL_CONSUMPTION[tier_level])
    return m


for tier_lvl in [3, 4]:
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
    """Use linear interpolation of the minimum values of capacity and consumption

    :param yearly_consumption: yearly consuption per household in kWh/year
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
    """Assign an index value to differentiate gdp per capita"""
    answer = 1
    if gdp_per_capita < 1500:
        answer = 0.5
    if gdp_per_capita < 700:
        answer = 0
    return answer


def map_mobile_money_class(mobile_money):
    """Assign an index value to differentiate mobile_money"""
    answer = 1
    if mobile_money <= 0.21:
        answer = 0.5
    if mobile_money <= 0.12:
        answer = 0
    return answer


def map_ease_doing_business_class(business_ease):
    """Assign an index value to differentiate ease of doing business"""
    answer = 1
    if business_ease <= 164:
        answer = 0.5
    if business_ease <= 131:
        answer = 0
    return answer


def map_corruption_class(corruption_idx):
    """Assign an index value to differentiate corruption"""
    answer = 1
    if corruption_idx <= 33:
        answer = 0.5
    if corruption_idx <= 26:
        answer = 0
    return answer


def map_weak_grid_class(weak_grid_idx):
    """Assign an index value to differentiate weak grid"""
    answer = 1
    if weak_grid_idx <= 4.5:
        answer = 0.5
    if weak_grid_idx <= 9:
        answer = 0
    return answer


def map_tier_yearly_consumption(
        yearly_consumption,
        electrification_option_share,
        tier_level=MIN_TIER_LEVEL
):
    """Assign yearly consumption adjusted for tier level"""
    if yearly_consumption < MIN_ANNUAL_CONSUMPTION[tier_level]:
        answer = MIN_ANNUAL_CONSUMPTION[tier_level] * electrification_option_share
    else:
        answer = yearly_consumption * electrification_option_share
    return answer


def prepare_shs_power_and_sales_volumes():
    shs_sales_volumes = pd.read_csv('daten/shs_sales_volumes.csv', comment='#')
    # compute the average of the product categories 5 to 7
    shs_sales_volumes['tot_5-7'] = shs_sales_volumes[['5', '6', '7']].sum(axis=1)

    shs_power_categories = pd.read_csv('daten/shs_power_per_product_categories.csv', comment='#')

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


SHS_POWER_CATEGORIES, SHS_SALES_VOLUMES = prepare_shs_power_and_sales_volumes()


def extract_bau_data(fname='daten/bau.csv'):
    bau_data = pd.read_csv(fname, comment='#')
    return bau_data.set_index('region')


BAU_DATA = extract_bau_data()


def shs_av_power(power_cat, shs_power_categories=None):
    if shs_power_categories is None:
        shs_power_categories = SHS_POWER_CATEGORIES
    return shs_power_categories.loc[power_cat, 'power_av']


def prepare_endogenous_variables(input_df, shs_sales_volumes=None):

    if shs_sales_volumes is None:
        shs_sales_volumes = SHS_SALES_VOLUMES
    df = input_df.copy()

    # compute the grid and mg yearly consumption adjusted for tier level
    for opt in [GRID, MG]:
        df['hh_%s_tier_yearly_electricity_consumption' % opt] = \
            np.vectorize(map_tier_yearly_consumption)(
                df.hh_yearly_electricity_consumption,
                df['hh_%s_share' % opt]
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

