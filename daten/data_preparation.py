ELECTRIFICATION_OPTIONS = ['grid', 'mg', 'shs']
SENARII = ['bau', 'se4all', 'prog']

MIN_TIER_LEVEL = 3
MIN_RATED_CAPACITY = {3: 200, 4: 800, 5: 2000}  # index is TIER level [W]
MIN_ANNUAL_CONSUMPTION = {3: 365, 4: 1250, 5: 3000}  # index is TIER level [kWh/a]


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
