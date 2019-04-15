import numpy as np
import dash_html_components as html
from data_preparation import (
    ELECTRIFICATION_OPTIONS,
    POP_GET,
    HH_CAP,
)


def country_div(df=None, country_iso=None):
    """Fill and return a specific country exogenous results and information"""

    # variables used in the div
    pop_2017 = 0
    country_pop_res = []
    country_cap_res = []

    if df is not None:
        df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0)
        # narrow the selection for the country specific information
        dfc = df.loc[country_iso]
        pop_2017 = dfc.pop_2017
        country_pop_res = np.squeeze(dfc[POP_GET].values)
        country_cap_res = np.squeeze(dfc[HH_CAP].values) * 1e-6

    divs = [
        html.Div(
            id='country-info-div',
            className='country__info',
            children='Population (2017) %i' % pop_2017
        ),
        html.Div(
            id='country-results-div',
            className='country__results',
            children=[
                html.Div(
                    id='country-pop-results-div',
                    className='country__results__pop',
                    children=[
                        html.H4('% POPULATION NEWLY ELECTRIFIED in 2030'),
                        html.Div(
                            className='country__results__pop__hdr',
                            children=[
                                html.P(str(opt)) for opt in ELECTRIFICATION_OPTIONS
                            ]
                        ),
                        html.Div(
                            className='country__results__pop__line',
                            children=[
                                html.P('%.2f' % res) for res in country_pop_res
                            ]
                        ),
                    ]
                ),
                html.Div(
                    id='country-cap-results-div',
                    className='country__results__cap',
                    children=[
                        html.H4('GW household capacity'),
                        html.Div(
                            className='country__results__cap__hdr',
                            children=[
                                html.P(str(opt)) for opt in ELECTRIFICATION_OPTIONS
                            ]
                        ),
                        html.Div(
                            className='country__results__cap__line',
                            children=[
                                html.P('%.2f' % res) for res in country_cap_res
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ]
    return divs
