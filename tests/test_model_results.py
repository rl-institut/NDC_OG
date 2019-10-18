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
    POP_GET,
    HH_GET,
    HH_CAP,
    HH_SCN2,
    INVEST,
    INVEST_CAP,
    GHG_ALL,
    compute_ndc_results_from_raw_data
)

COMP_EXO = POP_GET + HH_GET + HH_CAP + HH_SCN2
COMP_INVEST = INVEST + INVEST_CAP
COMP_GHG = GHG_ALL

WORLD_ID = 'WD'
REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')


SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce, MIN_TIER_LEVEL).to_json() for sce in SCENARIOS
}


def highlight_mismatch(col=None, df_diff=None, eps=0.001):
    """Filter lines of a Dataframe column which are larger than threshold"""
    return df_diff.loc[np.abs(df_diff[col]) > eps]


def highlight_mismatch_region(col=None, df_diff=None, eps=0.001):
    """Filter lines of a Dataframe column which are larger than threshold"""
    return np.abs(df_diff[col]) > eps


class TestModellass(unittest.TestCase):

    def compare_results_countries(self, sce, fname, comp, eps=0.001):
        df = pd.read_json(SCENARIOS_DATA[sce]).set_index('country_iso')
        df = df.sort_index(ascending=True)
        xls = pd.read_csv(
            'tests/data/{}'.format(fname),
            float_precision='high',
            encoding='latin'
        ).set_index('country_iso')
        xls = xls.sort_index(ascending=True)

        df_diff = xls[comp] - df[comp]
        print(df_diff)
        l = []
        for col in comp:
            temp = highlight_mismatch(col, df_diff, eps).index.to_list()
            if temp:
                print('problems with ', col, temp)
                print(len(temp))
            l = l + temp
        l = list(set(l))

        self.assertEqual(len(set(l)), 0)

    def compare_results_region(self, sce, region_id, fname, comp, eps=0.001):
        df = pd.read_json(SCENARIOS_DATA[sce]).set_index('country_iso')
        df = df.sort_index(ascending=True)
        xls = pd.read_csv(
            'tests/data/{}'.format(fname),
            float_precision='high',
            encoding='latin'
        ).set_index('country_iso')
        xls = xls.sort_index(ascending=True)

        if region_id != WORLD_ID:
            df = df.loc[df.region == REGIONS_NDC[region_id]]
            xls = xls.loc[df.region == REGIONS_NDC[region_id]]

        df_diff = xls[comp].sum(axis=0) - df[comp].sum(axis=0)

        l = []
        for col in comp:
            temp = highlight_mismatch_region(col, df_diff, eps)
            if temp:
                print('problems with ', col, temp)
                print(len(temp))
            l = l + temp
        l = list(set(l))

        self.assertEqual(len(l), 0)

    def test_bau_exo_results_countries(self):
        self.compare_results_countries(
            BAU_SCENARIO,
            'results_test_comparison_{}.csv'.format(BAU_SCENARIO),
            COMP_EXO,
            0.2
        )

    def test_bau_exo_results_region(self):
        self.compare_results_region(
            BAU_SCENARIO,
            WORLD_ID,
            'results_test_comparison_{}.csv'.format(BAU_SCENARIO),
            COMP_EXO,
            0.2
        )

    def test_bau_invest_results_countries(self):
        self.compare_results_countries(
            BAU_SCENARIO,
            'results_test_comparison_{}.csv'.format(BAU_SCENARIO),
            COMP_INVEST,
            0.2
        )

    def test_bau_invest_results_region(self):
        self.compare_results_region(
            BAU_SCENARIO,
            WORLD_ID,
            'results_test_comparison_{}.csv'.format(BAU_SCENARIO),
            COMP_INVEST,
            0.2
        )

    def test_prog_exo_results(self):
        self.compare_results_countries(
            PROG_SCENARIO,
            'results_test_comparison_{}.csv'.format(PROG_SCENARIO),
            COMP_EXO,
            0.2
        )

    def test_prog_exo_results_region(self):
        self.compare_results_region(
            PROG_SCENARIO,
            WORLD_ID,
            'results_test_comparison_{}.csv'.format(PROG_SCENARIO),
            COMP_EXO,
            0.2
        )

    def test_prog_invest_results(self):
        self.compare_results_countries(
            PROG_SCENARIO,
            'results_test_comparison_{}.csv'.format(PROG_SCENARIO),
            COMP_INVEST,
            0.2
        )

    def test_prog_invest_results_region(self):
        self.compare_results_region(
            PROG_SCENARIO,
            WORLD_ID,
            'results_test_comparison_{}.csv'.format(PROG_SCENARIO),
            COMP_INVEST,
            0.2
        )

    def test_uea_exo_results(self):
        self.compare_results_countries(
            SE4ALL_SCENARIO,
            'results_test_comparison_{}.csv'.format(SE4ALL_SCENARIO),
            COMP_EXO,
            0.2
        )

    def test_uea_exo_results_region(self):
        self.compare_results_region(
            SE4ALL_SCENARIO,
            WORLD_ID,
            'results_test_comparison_{}.csv'.format(SE4ALL_SCENARIO),
            COMP_EXO,
            0.2
        )

    def test_uea_invest_results(self):
        self.compare_results_countries(
            SE4ALL_SCENARIO,
            'results_test_comparison_{}.csv'.format(SE4ALL_SCENARIO),
            COMP_INVEST,
            0.2
        )

    def test_uea_invest_results_region(self):
        self.compare_results_region(
            SE4ALL_SCENARIO,
            WORLD_ID,
            'results_test_comparison_{}.csv'.format(SE4ALL_SCENARIO),
            COMP_INVEST,
            0.2
        )
