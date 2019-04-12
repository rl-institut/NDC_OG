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
            + df.ease_doing_business_class * menti[opt]['high_ease_doing_business']\
            + df.corruption_class * menti[opt]['low_corruption']\
            + df.weak_grid_class * menti[opt]['high_grid_weakness']


def prepare_se4all_data(input_df, weight_grid=WEIGHT_GRID, weight=WEIGHT):
    # for se4all+SHIFT

    df = input_df.copy()
    prepare_se4all_shift_drives(df)
    apply_se4all_shift_drives(df)

    for opt in ELECTRIFICATION_OPTIONS:
        df['pop_get_%s_2030' % opt] = df['pop_%s_share' % opt] * df.pop_newly_electrified_2030

    # to normalize the senarii weigthed sum
    weighted_norm = \
        df.loc[:, RISE_INDICES].sum(axis=1) * weight_grid \
        + df.loc[:, SHIFT_MENTI].sum(axis=1) * weight

    non_zero_indices = df.loc[:, RISE_INDICES + SHIFT_MENTI].sum(axis=1) != 0

    for col in ['shift_grid_share', 'shift_grid_to_mg_share', 'shift_grid_to_shs_share']:
        # if the sum of the RISE indices and shift MENTI is 0 the corresponding rows
        # in the given columns are set to 0
        df.loc[df.loc[:, RISE_INDICES + SHIFT_MENTI].sum(axis=1) == 0, col] = 0

    # share of population which will be on the grid in the se4all+SHIFT senario
    df.loc[non_zero_indices, 'shift_grid_share'] = df.rise_grid * weight_grid / weighted_norm

    # share of population which will have changed from grid to mg in the se4all+SHIFT senario
    df.loc[non_zero_indices, 'shift_grid_to_mg_share'] = \
        (df.rise_mg * weight_grid + df.shift_menti_mg * weight) / weighted_norm

    # share of population which will have changed from grid to shs in the se4all+SHIFT senario
    df.loc[non_zero_indices, 'shift_grid_to_shs_share'] = \
        (df.rise_shs * weight_grid + df.shift_menti_shs * weight) / weighted_norm

    # SHARED WITH prOG
    # if the predicted mg share is larger than the predicted grid share, the number of people
    # predited to use mg in the se4all+SHIFT senario is returned, otherwise it is set to 0
    df.loc[df.shift_grid_to_mg_share >= df.shift_grid_share, 'shift_pop_grid_to_mg'] = \
        df.shift_grid_to_mg_share * df.pop_get_grid_2030
    df.loc[df.shift_grid_to_mg_share < df.shift_grid_share, 'shift_pop_grid_to_mg'] = 0

    # if the predicted shs share is larger than the predicted grid share, the number of people
    # predited to use shs in the se4all+SHIFT senario is returned, otherwise it is set to 0
    df.loc[df.shift_grid_to_shs_share >= df.shift_grid_share, 'shift_pop_grid_to_shs'] = \
        df.shift_grid_to_shs_share * df.pop_get_grid_2030
    df.loc[df.shift_grid_to_shs_share < df.shift_grid_share, 'shift_pop_grid_to_shs'] = 0

    return df


def prepare_prog_data(input_df):
    # for prOG

    df = input_df.copy()

    df.rise_mg = 100
    df.rise_shs = 100

    for opt in ELECTRIFICATION_OPTIONS:
        df['pop_get_%s_2030' % opt] = df['pop_%s_share' % opt] * df.pop_newly_electrified_2030

    weighted_norm = df.loc[:, RISE_INDICES].sum(axis=1)

    non_zero_indices = df.loc[:, RISE_INDICES].sum(axis=1) != 0

    for col in ['shift_grid_share', 'shift_grid_to_mg_share', 'shift_grid_to_shs_share']:
        # if the sum of the RISE indices and shift MENTI is 0 the corresponding rows in
        # the given columns are set to 0
        df.loc[df.loc[:, RISE_INDICES].sum(axis=1) == 0, col] = 0

    # share of population which will be on the grid in the se4all+SHIFT senario
    df.loc[non_zero_indices, 'shift_grid_share'] = df.rise_grid / weighted_norm

    # share of population which will have changed from grid to mg in the se4all+SHIFT senario
    df.loc[non_zero_indices, 'shift_grid_to_mg_share'] = df.rise_mg / weighted_norm

    # share of population which will have changed from grid to shs in the se4all+SHIFT senario
    df.loc[non_zero_indices, 'shift_grid_to_shs_share'] = df.rise_shs / weighted_norm

    # Shared with se4all

    # if the predicted mg share is larger than the predicted grid share, the number of people
    # predited to use mg in the se4all+SHIFT senario is returned
    # otherwise it is set to 0
    df.loc[df.shift_grid_to_mg_share >= df.shift_grid_share, 'shift_pop_grid_to_mg'] = \
        df.shift_grid_to_mg_share * df.pop_get_grid_2030
    df.loc[df.shift_grid_to_mg_share < df.shift_grid_share, 'shift_pop_grid_to_mg'] = 0

    # if the predicted shs share is larger than the predicted grid share, the number of people
    # predited to use shs in the se4all+SHIFT senario is returned
    # otherwise it is set to 0
    df.loc[df.shift_grid_to_shs_share >= df.shift_grid_share, 'shift_pop_grid_to_shs'] = \
        df.shift_grid_to_shs_share * df.pop_get_grid_2030
    df.loc[df.shift_grid_to_shs_share < df.shift_grid_share, 'shift_pop_grid_to_shs'] = 0

    return df


def extract_results_senario(input_df, senario, regions=None, bau_data=None):
    df = input_df.copy()

    if senario == BAU_SENARIO:
        if regions is None:
            regions = ['SSA', 'DA', 'LA']
        if bau_data is None:
            bau_data = BAU_DATA
        for opt in ELECTRIFICATION_OPTIONS:
            # not valid for other senario than bau at the moment
            # create a columns with regional electrification option shares
            df['temp_%s' % opt] = df['region'].replace(regions, bau_data.loc[regions][
                '%s_share' % opt].to_list())

            # predicted number of people getting access to electricity (regional detail level)
            df['pop_get_%s_2030' % opt] = df.bau_pop_newly_electrified * df['temp_%s' % opt]
    elif senario in [SE4ALL_SHIFT_SENARIO, PROG_SENARIO]:
        # SUMME(AA4:AB4) --> df.loc[:,['shift_pop_grid_to_mg' 'shift_pop_grid_to_shs']].sum(axis=1)
        # grid =D4-SUMME(AA4:AB4)
        opt = 'grid'
        # predicted number of people getting access to electricity (regional detail level)
        cumul_mg_shs = df.loc[:, ['shift_pop_grid_to_mg', 'shift_pop_grid_to_shs']].sum(axis=1)
        df['pop_get_%s_2030' % opt] = df['pop_get_%s_2030' % opt] - cumul_mg_shs

        # mg =E5+AA5
        opt = 'mg'
        # predicted number of people getting access to electricity (regional detail level)
        df['pop_get_%s_2030' % opt] = \
            df['pop_get_%s_2030' % opt] \
            + df['shift_pop_grid_to_%s' % opt]

        # shs =F6+AB6
        opt = 'shs'
        # predicted number of people getting access to electricity (regional detail level)
        df['pop_get_%s_2030' % opt] = \
            df['pop_get_%s_2030' % opt] \
            + df['shift_pop_grid_to_%s' % opt]
    else:
        raise ValueError

    for opt in ELECTRIFICATION_OPTIONS:
        # predicted number of household getting access to electricity (regional detail level)
        df['hh_get_%s_2030' % opt] = df['pop_get_%s_2030' % opt] / df.hh_av_size
        # predicted power (in kW) that the access to electricity will represent
        # (regional detail level)
        # the analysis is based on the peak demand for the grid and mg senarii, and the average
        # power of solar panel for shs senario
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

    return df
