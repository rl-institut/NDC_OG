import numpy as np
import pandas as pd
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input, State
import dash_daq as daq
import dash_table
import plotly.graph_objs as go
from data_preparation import (
    ELECTRIFICATION_OPTIONS,
    ELECTRIFICATION_DICT,
    BAU_SCENARIO,
    SCENARIOS_DICT,
    SE4ALL_FLEX_SCENARIO,
    POP_GET,
    HH_GET,
    HH_CAP,
    HH_SCN2,
    INVEST,
    INVEST_CAP,
    GHG,
    GHG_CAP,
    EXO_RESULTS,
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


def results_div(df=None, df_comp=None, aggregate=False):
    """Fill and return a specific country exogenous results and information.

    :param df: a single line of the dataframe corresponding to the results of a country
    :param df_comp: a single line of the dataframe corresponding to the BaU results of a country
    :param aggregate: (bool) determine whether the results should be summed country wise
    :return: the content of the country-div
    """

    # variables used in the div
    pop_2017 = 0
    country = ''

    basic_results_data = []
    ghg_results_data = []
    basic_columns = []
    ghg_columns = []

    # labels of the table columns
    labels_dict = ELECTRIFICATION_DICT.copy()
    # a column for the row labels
    labels_dict['labels'] = ''
    # a column for comparison of greenhouse gases emission
    labels_dict['comp'] = 'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO])

    # label of the table rows
    basic_rows = [
        '% population newly electrified in 2030',
        '# household newly electrified in 2030',
        'MW household capacity',
        'MW household capacity (TIER capped)',
        'Total investment (case 1) EUR',
        'Total investment (case 2) EUR',
    ]

    if df_comp is None:
        ghg_rows = [
            'GHG (case 1)',
            'GHG (case 2)',
            # 'GHG CUMUL'
        ]
    else:
        ghg_rows = [
            'GHG (case 1)',
            'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
            'GHG (case 2)',
            'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
        ]

    if df is not None:

        df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0).round(3)

        if aggregate is True:
            pop_2017 = df.pop_2017.sum(axis=0)
            country = 'selected region'
            df = df[EXO_RESULTS].sum(axis=0)
            if df_comp is not None:
                df_comp = df_comp[EXO_RESULTS].sum(axis=0)
        else:
            pop_2017 = df.pop_2017
            country = df.country.values[0]

        pop_res = np.squeeze(df[POP_GET].values) * 100
        hh_res = np.squeeze(df[HH_GET].values) * 100
        cap_res = np.squeeze(df[HH_CAP].values) * 1e-3
        cap2_res = np.squeeze(df[HH_SCN2].values) * 1e-3
        invest_res = np.squeeze(df[INVEST].values)
        invest_res = np.append(np.NaN, invest_res)
        invest2_res = np.squeeze(df[INVEST_CAP].values)
        invest2_res = np.append(np.NaN, invest2_res)
        ghg_res = np.squeeze(df[GHG].values)
        ghg2_res = np.squeeze(df[GHG_CAP].values)

        basic_results_data = np.vstack(
            [pop_res, hh_res, cap_res, cap2_res, invest_res, invest2_res]
        )

        basic_results_data = pd.DataFrame(data=basic_results_data, columns=ELECTRIFICATION_OPTIONS)
        basic_results_data['labels'] = pd.Series(basic_rows)
        basic_columns = ['labels'] + ELECTRIFICATION_OPTIONS
        basic_results_data = basic_results_data[basic_columns].to_dict('records')

        if df_comp is not None:
            ghg_comp_res = ghg_res - np.squeeze(df_comp[GHG].values)
            ghg2_comp_res = ghg2_res - np.squeeze(df_comp[GHG_CAP].values)
            ghg_results_data = np.vstack([ghg_res, ghg_comp_res, ghg2_res, ghg2_comp_res])
        else:
            ghg_results_data = np.vstack([ghg_res, ghg2_res])

        ghg_results_data = pd.DataFrame(data=ghg_results_data, columns=ELECTRIFICATION_OPTIONS)
        ghg_results_data['labels'] = pd.Series(ghg_rows)
        ghg_columns = ['labels'] + ELECTRIFICATION_OPTIONS
        ghg_results_data = ghg_results_data[ghg_columns].to_dict('records')

    if aggregate is True:
        id_name = 'aggregate'
    else:
        id_name = 'country'

    # tables containing the results
    results_divs = [
        html.Div(
            id='{}-basic-results-div'.format(id_name),
            className='{}__results__basic'.format(id_name),
            children=[
                html.H4('Results for {}'.format(country)),
                dash_table.DataTable(
                    id='{}-basic-results-table'.format(id_name),
                    columns=[
                        {'name': labels_dict[col], 'id': col} for col in basic_columns
                    ],
                    data=basic_results_data
                )
            ]
        ),
        html.Div(
            id='{}-ghg-results-div'.format(id_name),
            className='{}__results'.format(id_name),
            children=[
                html.H4('Greenhouse Gases emissions'),
                dash_table.DataTable(
                    id='{}-ghg-results-table'.format(id_name),
                    columns=[
                        {'name': labels_dict[col], 'id': col}
                        for col in ghg_columns
                    ],
                    data=ghg_results_data
                )
            ]
        ),
    ]
    if aggregate is False:
        # add a barplot below the tables with the results
        barplot = html.Div(
            id='barplot-div',
            className='app__{}__barplot'.format(id_name),
            title='Description',
            children=dcc.Graph(
                id='barplot',
                figure=go.Figure(data=[go.Bar(x=ELECTRIFICATION_OPTIONS, y=[20, 14, 23])]),
                style={'height': '200px'}
            ),
        )

        results_divs = results_divs + [barplot]

    divs = [
        html.Div(
            id='{}-info-div'.format(id_name),
            className='{}__info'.format(id_name),
            children='Population (2017) %i' % pop_2017
        ),
        html.Div(
            id='{}-results-div'.format(id_name),
            className='{}__results'.format(id_name),
            children=results_divs
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
        html.Div(
            id='aggregate-input-div',
            title='Tick this box to enable the aggregation of the results',
            children=dcc.Checklist(
                id='aggregate-input',
                className='app__input__checklist',
                options=[
                    {'label': 'Aggregate results', 'value': 'aggregate'}
                ],
                values=[],
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
