import numpy as np
import dash_html_components as html
import dash_core_components as dcc
import dash_daq as daq
from data_preparation import (
    ELECTRIFICATION_OPTIONS,
    ELECTRIFICATION_DICT,
    SCENARIOS_DICT,
    POP_GET,
    HH_CAP
)


def country_div(df=None, country_iso=None):
    """Fill and return a specific country exogenous results and information."""

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


def scenario_div(init_scenario, init_elec_opt):
    """"""

    divs = [
        html.Div(
            id='scenario-label',
            className='app__input__label',
            children='Scenario'
        ),
        dcc.Dropdown(
            id='scenario-input',
            className='app__input__dropdown',
            options=[
                {'label': v, 'value': k}
                for k, v in SCENARIOS_DICT.items()
            ],
            value=init_scenario,
        ),
        html.Div(
            id='elec-label',
            className='app__input__label',
            children='Electrification option'
        ),
        dcc.Dropdown(
            id='electrification-input',
            className='app__input__dropdown',
            options=[
                {'label': v, 'value': k}
                for k, v in ELECTRIFICATION_DICT.items()
            ],
            value=init_elec_opt,
        ),
    ]
    return divs


def controls_div(piechart):
    """"""
    divs = [
        html.Div(
            id='rise-shs-div',
            className='app__input__slider',
            children=[
                html.Div(
                    id='rise-shs-label',
                    className='app__input__label',
                    children='RISE-SHS'
                ),
                daq.Slider(
                    id='rise-shs-input',
                    min=0,
                    max=100,
                    value=14,
                    handleLabel={
                        "showCurrentValue": True, "label": "VALUE"},
                    step=1,
                ),
            ]
        ),
        html.Div(
            id='rise-mg-div',
            className='app__input__slider',
            children=[
                html.Div(
                    id='rise-label',
                    className='app__input__label',
                    children='RISE-MG'
                ),
                daq.Slider(
                    id='rise-mg-input',
                    min=0,
                    max=100,
                    value=67,
                    handleLabel={
                        "showCurrentValue": True, "label": "VALUE"},
                    step=1,
                ),
            ]
        ),
        html.Div(
            id='framework-div',
            className='app__input__slider',
            children=[
                html.Div(
                    id='framework-label',
                    className='app__input__label',
                    children='Framework'
                ),
                daq.Slider(
                    id='framework-input',
                    min=0,
                    max=10,
                    value=4,
                    handleLabel={
                        "showCurrentValue": True, "label": "VALUE"},
                    step=1,
                ),
            ]
        ),
        html.Div(
            id='tier-div',
            className='app__input',
            children=[
                html.Div(
                    id='tier-label',
                    className='app__input__label',
                    children='TIER'
                ),
                daq.NumericInput(
                    id='tier-input',
                    value=2
                ),
            ]
        ),
        html.Div(
            id='invest-div',
            className='app__input',
            children=[
                html.Div(
                    id='invest-label',
                    className='app__input__label',
                    children='Invest'
                ),
                daq.NumericInput(
                    id='invest-input',
                    label='USD/kW',
                    labelPosition='right'
                ),
            ]
        ),
        html.Div(
            id='piechart-div',
            className='app__piechart',
            children=dcc.Graph(
                id='piechart',
                figure=piechart,
                style={
                    'height': '55vh',
                }
            ),
        )
    ]
    return divs


def general_info_div():
    """"""
    return dcc.Markdown('''Description of app and project here''')
