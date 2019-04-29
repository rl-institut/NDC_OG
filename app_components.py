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
    SE4ALL_FLEX_SCENARIO,
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
            if scenario == SE4ALL_FLEX_SCENARIO:
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
        df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0).round(3)
        pop_2017 = df.pop_2017
        country_pop_res = np.squeeze(df[POP_GET].values)
        country_cap_res = np.squeeze(df[HH_CAP].values) * 1e-3

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
                                html.P('{:.1f}'.format(res * 100)) for res in country_pop_res
                            ]
                        ),
                    ]
                ),
                html.Div(
                    id='country-cap-results-div',
                    className='country__results__cap',
                    children=[
                        html.H4('MW household capacity'),
                        html.Div(
                            className='country__results__cap__hdr',
                            children=[
                                html.P(str(opt)) for opt in ELECTRIFICATION_OPTIONS
                            ]
                        ),
                        html.Div(
                            className='country__results__cap__line',
                            children=[
                                html.P('{:.1f}'.format(res)) for res in country_cap_res
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
        html.Div(
            id='scenario-input-div',
            title='scenarios description',
            children=dcc.Dropdown(
                id='scenario-input',
                className='app__input__dropdown',
                options=[
                    {'label': v, 'value': k}
                    for k, v in SCENARIOS_DICT.items()
                ],
                value=init_scenario,
            )
        ),
        html.Div(
            id='elec-label',
            className='app__input__label',
            children='Electrification option'
        ),
        html.Div(
            id='electrification-input-div',
            title='electrification option description',
            children=dcc.Dropdown(
                id='electrification-input',
                className='app__input__dropdown',
                options=[
                    {'label': v, 'value': k}
                    for k, v in ELECTRIFICATION_DICT.items()
                ],
                value=init_elec_opt,
            )
        ),
    ]
    return divs


def controls_div():
    """Return controls for scenario dependent variables."""

    divs = [
        html.Div(
            id='rise-div',
            className='app__input',
            children=[
                html.Div(
                    id='rise-shs-div',
                    className='app__input__slider',
                    title='rise shs description',
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
                    title='rise mg description',
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
                )
            ]
        ),
        html.Div(
            id='mentis-weight-div',
            className='app__input',
            children=[
                html.Div(
                    id='mentis-weight-label',
                    className='app__input__label',
                    children='Mentis weight'
                ),
                html.Div(
                    id='mentis-weight-input-div',
                    title='mentis weight description',
                    children=dcc.Input(
                        id='mentis-weight-input',
                        className='app__input__mentis-weight',
                        value=0.2,
                        type='number',
                        min=0,
                        max=1,
                        step=0.01
                    )
                )
            ]
        ),
        html.Div(
            id='mentis-drives-div',
            className='app__input',
            children=[
                         html.Div(
                             id='mentis-label',
                             className='app__input__label',
                             children='Mentis drives'
                         )
                     ] + [
                         html.Div(
                             id='mentis-%s-input-div' % input_name.replace('_', '-'),
                             title='%s description' % input_name.replace('_', ' '),
                             children=[
                                 html.Div(
                                     id='mentis-%s-input_label' % input_name.replace('_', '-'),
                                     children=input_name.replace('_', ' ')
                                 ),
                                 dcc.Input(
                                     id='mentis-%s-input' % input_name.replace('_', '-'),
                                     className='app__input__mentis-drives',
                                     value=0,
                                     type='number',
                                     min=0,
                                     max=1,
                                     step=0.5
                                 ),
                             ]
                         )
                         for input_name in MENTI_DRIVES
                     ]
        ),
        html.Div(
            id='tier-div',
            className='app__input',
            children=[
                html.Div(
                    id='tier-label',
                    className='app__input__label',
                    children='Min TIER level'
                ),
                html.Div(
                    id='tier-input-div',
                    title='min tier level description',
                    children=dcc.Input(
                        id='tier-input',
                        className='app__input__tier',
                        value=2,
                        type='number',
                        min=1,
                        max=5,
                        step=1
                    )
                ),
            ]
        ),
        html.Div(
            id='invest-div',
            className='app__input',
            children=[
                html.Div(
                    id='invest-label',
                    className='app__input',
                    children='Invest'
                ),
                html.Div(
                    id='invest-input-div',
                    title='invest description',
                    children=dcc.Input(
                        id='invest-input',
                        className='app__input__invest',
                        type='number',
                    )
                ),
                html.Div(
                    id='invest-unit',
                    className='app__input__unit',
                    children='USD/kW'
                ),
            ]
        ),
    ]
    return divs


def general_info_div():
    """Return text displayed for the user."""
    return [
        html.P(
            'In the Study on Renewable Energy Off-Grid Components of NDCs and their Role for \
            Climate Change Mitigation financed by GIZ,  Reiner Lemoine Institute and the \
            greenwerk develop strategies for the use of renewable energy that can support \
            climate protection in developing countries.'
        ),
        html.P(
            'The study targets the inclusion of off-grid components \
           in the Nationally Determined Contributions (NDCs), in which the signatory states \
           to the Paris Climate Change Convention commit themselves to elaborate national \
           climate protection targets, should be achieved.'
        ),
        html.P(
            'In this visualization tool a quantification of four different new \
        electrification until 2030 scenarios are presented for 52 countries. These countries were \
        selected through the criteria of having > 1 million people without electricity \
        access in 2017.'
        )
    ]
