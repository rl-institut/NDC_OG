import numpy as np
import pandas as pd
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input, State
import dash_daq as daq
from data_preparation import (
    ELECTRIFICATION_OPTIONS,
    ELECTRIFICATION_DICT,
    SCENARIOS_DICT,
    SE4ALL_SHIFT_SENARIO,
    PROG_SENARIO,
    POP_GET,
    HH_CAP,
    MENTI_DRIVES
)


def callback_generator(app, input_name, df_name):
    """Generate a callback for input components."""

    @app.callback(
        Output('%s-input' % input_name, 'value'),
        [
            Input('scenario-input', 'value'),
            Input('country-input', 'value'),
        ],
        [State('data-store', 'data')]
    )
    def update_drive_input(scenario, country_sel, cur_data):

        answer = 0
        country_iso = country_sel
        # in case of country_iso is a list of one element
        if np.shape(country_iso) and len(country_iso) == 1:
            country_iso = country_iso[0]

        # extract the data from the selected scenario if a country was selected
        if country_iso is not None:
            if scenario == SE4ALL_SHIFT_SENARIO:
                df = pd.read_json(cur_data[scenario]).set_index('country_iso')
                answer = df.loc[country_iso, '%s' % df_name]
        return answer

    update_drive_input.__name__ = 'update_%s_input' % input_name

    return update_drive_input


def country_div(df=None):
    """Fill and return a specific country exogenous results and information.

    :param df: a single line of the dataframe corresponding to the results of a country
    :return: the content of the country-div
    """

    # variables used in the div
    pop_2017 = 0
    country_pop_res = []
    country_cap_res = []

    if df is not None:
        df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0)
        pop_2017 = df.pop_2017
        country_pop_res = np.squeeze(df[POP_GET].values)
        country_cap_res = np.squeeze(df[HH_CAP].values) * 1e-6

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
    """Return controls for choice of scenario and electrification options."""

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


def controls_div(scenario):
    """Return controls for scenario dependent variables."""

    view_on_se4all = 'none'
    view_on_prog = 'none'
    view_on_both = 'none'
    if scenario == SE4ALL_SHIFT_SENARIO:
        view_on_se4all = 'flex'
    if scenario == PROG_SENARIO:
        view_on_prog = 'flex'
    if scenario in (SE4ALL_SHIFT_SENARIO, PROG_SENARIO):
        view_on_both = 'flex'

    divs = [
        html.Div(
            id='rise-shs-div',
            className='app__input__slider',
            style={'display': view_on_se4all},
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
            style={'display': view_on_se4all},
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
            style={'display': view_on_se4all},
            children=[
                         html.Div(
                             id='framework-label',
                             className='app__input__label',
                             children='Framework'
                         )
                     ] + [
                         dcc.Input(
                             id='mentis-%s-input' % input_name.replace('_', '-'),
                             className='app__input__num',
                             value=0,
                             type='number',
                             min=0,
                             max=1,
                             step=0.5
                         )
                         for input_name in MENTI_DRIVES
                     ]
        ),
        html.Div(
            id='tier-div',
            className='app__input',
            style={'display': view_on_both},
            children=[
                html.Div(
                    id='tier-label',
                    className='app__input__label',
                    children='TIER'
                ),
                dcc.Input(
                    id='tier-input',
                    value=2,
                    type='number',
                    min=1,
                    max=5,
                    step=1
                ),
            ]
        ),
        html.Div(
            id='invest-div',
            className='app__input',
            style={'display': view_on_both},
            children=[
                html.Div(
                    id='invest-label',
                    className='app__input__label',
                    children='Invest'
                ),
                dcc.Input(
                    id='invest-input',
                    type='number',
                ),
                html.Div(
                    id='invest-unit',
                    className='app__input__label',
                    children='USD/kW'
                ),
            ]
        ),
    ]
    return divs


def general_info_div():
    """Return text displayed for the user."""
    return dcc.Markdown('''Description of app and project here''')
