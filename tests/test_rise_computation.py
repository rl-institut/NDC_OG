import unittest

# run these tests with `python -m unittest tests/_test_calc_unittest.py`
# to run these tests with pytest, simply remove the '_' at the beginning of the filename

import numpy as np
import pandas as pd
from data.data_preparation import (
    SCENARIOS,
    MIN_TIER_LEVEL,
    SE4ALL_SCENARIO,
    BAU_SCENARIO,
    PROG_SCENARIO,
    ELECTRIFICATION_OPTIONS,
    GRID,
    MG,
    SHS,
    POP_GET,
    HH_GET,
    HH_CAP,
    HH_SCN2,
    INVEST,
    INVEST_CAP,
    GHG_ALL,
    ENDO_POP_GET,
    RISE_INDICES,
    compute_ndc_results_from_raw_data,
    compute_rise_shifts,
    prepare_scenario_data,
    extract_results_scenario
)

COMP_EXO = POP_GET + HH_GET + HH_CAP + HH_SCN2
COMP_INVEST = INVEST + INVEST_CAP
COMP_GHG = GHG_ALL

WORLD_ID = 'WD'
REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')


SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce, MIN_TIER_LEVEL).to_json() for sce in SCENARIOS
}


class TestRise(unittest.TestCase):

    def test_same_rise_dont_create_shift(self):
        pop_get = [1e+7, 2e+6, 6e+6]
        for r in range(101):
            rise = [r, r, r]
            for opt in ELECTRIFICATION_OPTIONS:
                pop_shift = compute_rise_shifts(rise, pop_get, opt)
                self.assertEqual(pop_shift, 0.0)

    def test_grid_compute_rise_recreates_uea(self):
        df = pd.read_json(SCENARIOS_DATA[SE4ALL_SCENARIO]).set_index('country_iso')
        for iso in df.index:
            print(iso)
            endo_pop_get = df.loc[iso, ENDO_POP_GET].values
            uea_pop_get = df.loc[iso, POP_GET].values
            rise = df.loc[iso, RISE_INDICES].values
            for i, opt in enumerate(ELECTRIFICATION_OPTIONS):
                pop_shift = compute_rise_shifts(rise, endo_pop_get, opt)
                self.assertAlmostEqual(endo_pop_get[i] + pop_shift, uea_pop_get[i])
