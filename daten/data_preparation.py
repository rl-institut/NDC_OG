import numpy as np

ELECTRIFICATION_OPTIONS = ['grid', 'mg', 'shs']
SENARII = ['bau', 'se4all', 'prog']

MIN_TIER_LEVEL = 3
MIN_RATED_CAPACITY = {3: 200, 4: 800, 5: 2000}  # index is TIER level [W]
MIN_ANNUAL_CONSUMPTION = {3: 365, 4: 1250, 5: 3000}  # index is TIER level [kWh/a]
RATIO_CAP_CONSUMPTION = {}


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
    for tier levels (3, 4) and (4, 5)
    :param yearly_consumption: yearly electricity consumption per household
    """
    answer = np.nan
    for tier_level in [3, 4]:
        if MIN_ANNUAL_CONSUMPTION[tier_level] \
                <= yearly_consumption \
                < MIN_ANNUAL_CONSUMPTION[tier_level + 1]:
            answer = tier_level
    return answer


def get_rated_capacity_from_yearly_consumption(yearly_consumption):
    """Use linear interpolation of the minimum values of capacity and consumption"""
    # Find the lower tier level bound
    tier_level = _find_tier_level(yearly_consumption)
    # Renaming the variables to explicitly show the formula used
    x = yearly_consumption
    m = RATIO_CAP_CONSUMPTION[tier_level]
    x_i = MIN_ANNUAL_CONSUMPTION[tier_level]
    y_i = MIN_RATED_CAPACITY[tier_level]
    return m * (x - x_i) + y_i


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
