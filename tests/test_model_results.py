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
    compute_ndc_results_from_raw_data
)

COMP_COLS = POP_GET + HH_GET + HH_CAP + HH_SCN2


SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce, MIN_TIER_LEVEL).to_json() for sce in SCENARIOS
}


def highlight_mismatch(col, df_diff,eps=0.001):
    return df_diff.loc[np.abs(df_diff[col]) > eps]


class TestModellass(unittest.TestCase):

    def test_bau_exo_results(self):
        bau_df = pd.read_json(SCENARIOS_DATA[BAU_SCENARIO]).set_index('country_iso').sort_index(
            ascending=True)
        xls_bau = pd.read_csv('data/xls_bau.csv', float_precision='high')

        df_diff = xls_bau[COMP_COLS] - bau_df[COMP_COLS]

        l = []
        for col in COMP_COLS:
            temp = highlight_mismatch(col, df_diff).index.to_list()
            if temp:
                print('problems with ', col, temp)
                print(len(temp))
            l = l + temp
        len(set(l))
        l = list(set(l))
        df_diff.loc[l]

        self.assertEqual(len(set(l)), 0)

    def test_uea_exo_results(self):
        se_df = pd.read_json(SCENARIOS_DATA[SE4ALL_SCENARIO]).set_index('country_iso').sort_index(
            ascending=True)
        xls_se = pd.read_csv('data/xls_se.csv', float_precision='high').set_index(
            'country_iso').sort_index(ascending=True)

        df_diff = xls_se[COMP_COLS] - se_df[COMP_COLS]

        l = []
        for col in COMP_COLS:
            temp = highlight_mismatch(col, df_diff).index.to_list()
            if temp:
                print('problems with ', col, temp)
                print(len(temp))
            l = l + temp
        len(set(l))
        l = list(set(l))
        df_diff.loc[l]

        self.assertEqual(len(set(l)), 0)

    def test_prog_exo_results(self):
        xls_prog = pd.read_csv('data/xls_prog.csv', float_precision='high')
        prog_df = pd.read_json(SCENARIOS_DATA[PROG_SCENARIO]).set_index(
            'country_iso').sort_index(ascending=True)

        COMP_COLS = POP_GET + HH_GET + HH_CAP + HH_SCN2

        df_diff = xls_prog[COMP_COLS] - prog_df[COMP_COLS]

        l = []
        for col in COMP_COLS:
            temp = highlight_mismatch(col, df_diff).index.to_list()
            if temp:
                print('problems with ', col, temp)
                print(len(temp))
            l = l + temp
        len(set(l))
        l = list(set(l))
        df_diff.loc[l]

        self.assertEqual(len(set(l)), 0)
