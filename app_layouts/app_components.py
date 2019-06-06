import numpy as np
import pandas as pd
import textwrap
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input, State
import dash_daq as daq
import dash_table
import plotly.graph_objs as go
from data.data_preparation import (
    ELECTRIFICATION_OPTIONS,
    BAU_SCENARIO,
    SE4ALL_SCENARIO,
    SCENARIOS_DICT,
    SE4ALL_FLEX_SCENARIO,
    PROG_SCENARIO,
    GRID,
    MG,
    SHS,
    BASIC_ROWS,
    BASIC_ROWS_FULL,
    LABEL_COLUMNS,
    BASIC_COLUMNS_ID,
    GHG_COLUMNS_ID,
)

TABLES_COLUMNS_WIDTH = [
    {'if': {'column_id': 'labels'},
     'width': '30%'},
    {'if': {'column_id': GRID},
     'width': '15%'},
    {'if': {'column_id': MG},
     'width': '15%'},
    {'if': {'column_id': SHS},
     'width': '15%'},
    {'if': {'column_id': 'total'},
     'width': '250px'},
]


def create_tooltip(cell):
    """Create tooltips for tables"""
    return textwrap.dedent(
        '''
        **{value}**.
        '''.format(value=cell)
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


def results_div(aggregate=False):
    """Fill and return a specific country exogenous results and information.

    :param aggregate: (bool) determine whether the results should be summed country wise
    :return: the content of the results-div
    """

    if aggregate is True:
        id_name = 'aggregate'

    else:
        id_name = 'country'

    x_vals = ELECTRIFICATION_OPTIONS.copy() + ['No electricity']
    fs = 12

    # add a barplot above the tables with the results
    barplot = html.Div(
        id='{}-barplot-div'.format(id_name),
        className='app__barplot',
        style={'width': '100%'},
        children=dcc.Graph(
            id='{}-barplot'.format(id_name),
            figure=go.Figure(
                data=[
                    go.Bar(
                        x=x_vals,
                        y=[0, 0, 0, 0],
                        text=[SCENARIOS_DICT[BAU_SCENARIO] for i in range(4)],
                        insidetextfont={'size': fs},
                        textposition='auto',
                        marker=dict(
                            color=['#0000ff', '#ffa500', '#008000', 'red']
                        ),
                        hoverinfo='y+text'
                    ),
                    go.Bar(
                        x=x_vals,
                        y=[0, 0, 0, 0],
                        text=[SCENARIOS_DICT[SE4ALL_SCENARIO] for i in range(4)],
                        insidetextfont={'size': fs},
                        textposition='auto',
                        marker=dict(
                            color=['#8080ff', '#ffd280', '#1aff1a', 'red']
                        ),
                        hoverinfo='y+text'
                    ),
                    go.Bar(
                        x=x_vals,
                        y=[0, 0, 0, 0],
                        text=[SCENARIOS_DICT[PROG_SCENARIO] for i in range(4)],
                        insidetextfont={'size': fs},
                        textposition='auto',
                        marker=dict(
                            color=['#ccccff', '#ffedcc', '#99ff99', 'red']
                        ),
                        hoverinfo='y+text'
                    )
                ],
                layout=go.Layout(
                    title='',
                    barmode='group',
                    paper_bgcolor='#EBF2FA',
                    plot_bgcolor='#EBF2FA',
                    showlegend=False,
                    height=400,
                    autosize=True,
                    margin=dict(
                        l=55,
                        r=0,
                        b=30,
                        t=30
                    ),
                    font=dict(size=20, family='Roboto'),
                    titlefont=dict(size=20),
                    yaxis=dict(
                        hoverformat='.1f'
                    )
                )
            ),
            config={
                'displayModeBar': True,
            }
        ),
    )

    # add tables with the results
    # align number on the right
    number_styling = [
        {
            'if': {
                'column_id': c,
                'filter': 'labels eq "{}"'.format(label)
            },
            'textAlign': 'right'
        }
        for c in ELECTRIFICATION_OPTIONS
        for label in BASIC_ROWS
    ]
    # align row labels on the left
    label_styling = [
        {
            'if': {'column_id': 'labels'},
            'textAlign': 'left'
        }
    ]

    # tables containing the results
    results_divs = [
        html.Div(
            id='{}-barplot-title'.format(id_name),
            children=[
                dcc.Dropdown(
                    id='{}-barplot-yaxis-input'.format(id_name),
                    options=[{'label': r, 'value': r} for r in BASIC_ROWS],
                    value=BASIC_ROWS[0],
                )
            ],
        ),
        barplot,
        html.Div(
            id='{}-basic-results-div'.format(id_name),
            className='{}__results__basic'.format(id_name),
            children=[
                html.H4(id='{}-basic-results-title'.format(id_name), children='Results'),
                dash_table.DataTable(
                    id='{}-basic-results-table'.format(id_name),
                    columns=[
                        {'name': LABEL_COLUMNS[col], 'id': col} for col in BASIC_COLUMNS_ID
                    ],
                    style_data_conditional=number_styling + label_styling,
                    style_cell_conditional=TABLES_COLUMNS_WIDTH,
                    style_header={'textAlign': 'center'},
                    style_cell={
                        'fontFamily': "Roboto"
                    },
                    tooltips={
                        'labels': [
                            {
                                'type': 'markdown',
                                'value': create_tooltip(BASIC_ROWS_FULL[lbl])
                            }
                            for lbl in BASIC_ROWS
                        ]

                    }
                )
            ]
        ),
        html.Div(
            id='{}-ghg-results-div'.format(id_name),
            className='{}__results'.format(id_name),
            children=[
                html.H4(
                    'Cumulated greenhouse Gases emissions '
                    'from 2017 until 2030 (in million tons CO2)'
                ),
                dash_table.DataTable(
                    id='{}-ghg-results-table'.format(id_name),
                    columns=[
                        {'name': LABEL_COLUMNS[col], 'id': col}
                        for col in GHG_COLUMNS_ID
                    ],
                    style_data_conditional=number_styling + label_styling,
                    style_cell_conditional=TABLES_COLUMNS_WIDTH,
                    style_header={'textAlign': 'center'},
                    style_cell={
                        'fontFamily': "Roboto"
                    },
                )
            ]
        ),
    ]

    divs = [
        html.Div(
            id='{}-results-div'.format(id_name),
            className='{}__results'.format(id_name),
            children=results_divs
        )
    ]

    return divs


def compare_div():
    """Fill and return a comparison to specific country exogenous results.

    :return: the content of the compare-div
    """

    id_name = 'compare'

    # add a barplot above the tables with the results
    barplot = html.Div(
        id='{}-barplot-div'.format(id_name),
        className='app__barplot',
        style={'width': '100%'},
        children=dcc.Graph(
            id='{}-barplot'.format(id_name),
            figure=go.Figure(
                data=[],
                layout=go.Layout(
                    title='',
                    barmode='group',
                    paper_bgcolor='#EBF2FA',
                    plot_bgcolor='#EBF2FA',
                    showlegend=False,
                    height=400,
                    autosize=True,
                    margin=dict(
                        l=55,
                        r=0,
                        b=30,
                        t=30
                    ),
                    font=dict(size=20, family='Roboto'),
                    titlefont=dict(size=20),
                    yaxis=dict(
                        hoverformat='.1f'
                    )
                )
            ),
            config={
                'displayModeBar': True,
            }
        ),
    )

    # add tables with the results
    # align number on the right
    number_styling = [
        {
            'if': {
                'column_id': c,
                'filter': 'labels eq "{}"'.format(label)
            },
            'textAlign': 'right'
        }
        for c in ELECTRIFICATION_OPTIONS
        for label in BASIC_ROWS
    ]
    # align row labels on the left
    label_styling = [
        {
            'if': {'column_id': 'labels'},
            'textAlign': 'left'
        }
    ]

    basic_columns_ids = []
    for col in BASIC_COLUMNS_ID:
        if col != 'labels':
            basic_columns_ids.append({'name': [LABEL_COLUMNS[col], 'value'], 'id': col})
            basic_columns_ids.append(
                {'name': [LABEL_COLUMNS[col], 'rel.'], 'id': 'comp_{}'.format(col)}
            )
        else:
            basic_columns_ids.append({'name': LABEL_COLUMNS[col], 'id': col})

    ghg_columns_ids = []
    for col in GHG_COLUMNS_ID:
        if col != 'labels':
            ghg_columns_ids.append({'name': [LABEL_COLUMNS[col], 'value'], 'id': col})
            ghg_columns_ids.append(
                {'name': [LABEL_COLUMNS[col], 'rel.'], 'id': 'comp_{}'.format(col)}
            )
        else:
            ghg_columns_ids.append({'name': LABEL_COLUMNS[col], 'id': col})

    compare_results_styling = [
        {"if": {"row_index": i},
            'backgroundColor': 'rgb(248, 248, 248)'}
        for i in [3, 4, 5, 6]
    ]

    # tables containing the results
    results_divs = [
        html.Div(
            id='{}-barplot-title'.format(id_name),
            children=[
                dcc.Dropdown(
                    id='{}-barplot-yaxis-input'.format(id_name),
                    options=[{'label': r, 'value': r} for r in BASIC_ROWS],
                    value=BASIC_ROWS[0],
                )
            ],
        ),
        barplot,
        html.Div(
            id='{}-basic-results-div'.format(id_name),
            className='{}__results__basic'.format(id_name),
            style={'width': '90%'},
            children=[
                html.H4(id='{}-basic-results-title'.format(id_name), children='Results'),
                dash_table.DataTable(
                    id='{}-basic-results-table'.format(id_name),
                    columns=basic_columns_ids,
                    style_data_conditional=number_styling + label_styling,
                    style_cell_conditional=TABLES_COLUMNS_WIDTH + compare_results_styling,
                    style_header={'textAlign': 'center'},
                    style_cell={
                        'fontFamily': "Roboto"
                    },
                    merge_duplicate_headers=True,
                    tooltips={
                        'labels': [
                            {
                                'type': 'markdown',
                                'value': create_tooltip(BASIC_ROWS_FULL[lbl])
                            }
                            for lbl in BASIC_ROWS
                        ]

                    }
                )
            ]
        ),
        html.Div(
            id='{}-ghg-results-div'.format(id_name),
            className='{}__results'.format(id_name),
            style={'width': '90%'},
            children=[
                html.H4(
                    'Cumulated greenhouse Gases emissions '
                    'from 2017 until 2030 (in million tons CO2)'
                ),
                dash_table.DataTable(
                    id='{}-ghg-results-table'.format(id_name),
                    columns=ghg_columns_ids,
                    style_data_conditional=number_styling + label_styling,
                    style_cell_conditional=TABLES_COLUMNS_WIDTH + compare_results_styling,
                    style_header={'textAlign': 'center'},
                    style_cell={
                        'fontFamily': "Roboto"
                    },
                    merge_duplicate_headers=True,
                )
            ]
        ),
    ]

    divs = [
        html.Div(
            id='{}-results-div'.format(id_name),
            className='{}__results'.format(id_name),
            children=results_divs
        )
    ]

    return divs


def scenario_div(init_scenario):
    """Return controls for choice of scenario and electrification options."""

    divs = [
        html.Div(
            id='scenario-label',
            className='app__input__label',
            children='Explore a scenario:'
        ),
        html.Div(
            id='scenario-input-div',
            children=dcc.RadioItems(
                id='scenario-input',
                className='app__input__radio',
                options=[
                    {'label': v, 'value': k}
                    for k, v in SCENARIOS_DICT.items()
                ],
                value=init_scenario,
            )
        )
    ]
    return divs


def impact_factors_div(opt, title=''):
    factors = []
    for input_name in IMPACT_FACTORS.index.to_list():
        factors.append(
            html.Div(
                id='impact-{}-{}-input-div'.format(opt, input_name.replace('_', '-')),
                title='{} description'.format(input_name.replace('_', ' ')),
                children=[
                    html.Div(
                        id='impact-{}-{}-input_label'.format(opt, input_name.replace('_', '-')),
                        children=input_name.replace('_', ' ')
                    ),
                    dcc.Input(
                        id='impact-{}-{}-input'.format(opt, input_name.replace('_', '-')),
                        className='app__input__impact',
                        value=np.round(IMPACT_FACTORS[opt][input_name], 3),
                        type='number',
                        min=0,
                        max=5,
                        step=0.001
                    ),
                ]
            )
        )

    return html.Div(
        id='impact-{}-drives-div'.format(opt),
        className='app__input',
        title=title,
        children=[
                     html.Div(
                         id='impact-{}-label'.format(opt),
                         className='app__input__label',
                         children='Impact factors ({})'.format(opt.upper())
                     )
                 ] + factors
    )


def controls_div():
    """Return controls for scenario dependent variables."""

    divs = [
        html.Div(
            id='tier-div',
            className='app__input',
            children=[
                html.Div(
                    id='min-tier-label',
                    className='app__input__label',
                    children='Min TIER level'
                ),
                html.Div(
                    id='min-tier-input-div',
                    className='app__input__input',
                    title='min tier level description',
                    children=dcc.Input(
                        id='min-tier-input',
                        className='app__input__tier',
                        value=3,
                        type='number',
                        min=1,
                        max=5,
                        step=1
                    )
                ),
                html.Div(
                    id='tier-label',
                    className='app__input__label',
                    children='Lower TIER level'
                ),
                html.Div(
                    id='tier-value-div',
                    title='tier level description',
                    children=html.Div(
                        id='tier-value',
                        className='app__display__tier',
                        children=''
                    )
                ),
            ]
        ),
        html.Div(
            id='rise-div',
            className='app__input',
            children=[
                html.Div(
                    id='rise-grid-div',
                    className='app__input__slider',
                    title='rise grid description',
                    children=[
                        html.Div(
                            id='rise-grid-label',
                            className='app__input__label',
                            children='RISE-GRID'
                        ),
                        daq.Slider(
                            id='rise-grid-input',
                            className='daq__slider',
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
                            className='daq__slider',
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
                            className='daq__slider',
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
            id='factor-div',
            className='app__input',
            children=[
                html.Div(
                    id='mentis-weight-div',
                    className='app__input',
                    children=[
                        html.Div(
                            id='mentis-weight-label',
                            className='app__input__label',
                            children='Weight RISE / influence factors'
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
                                     children='Influence factors'
                                 )
                             ] + [
                                 html.Div(
                                     id='mentis-%s-input-div' % input_name.replace('_', '-'),
                                     title='%s description' % input_name.replace('_', ' '),
                                     children=[
                                         html.Div(
                                             id='mentis-%s-input_label' %
                                                input_name.replace('_', '-'),
                                             children=input_name.replace('_', ' ')
                                         ),
                                         dcc.Input(
                                             id='mentis-%s-input' %
                                                input_name.replace('_', '-'),
                                             className='app__input__influence',
                                     # options=[
                                     #     {'label': l, 'value': v}
                                     #     for l, v in zip(['low', 'medium', 'high'], [0, 0.5, 1])
                                     # ],
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
                impact_factors_div('mg'),
                impact_factors_div('shs'),
            ]
        )
    ]
    return divs
