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
    ELECTRIFICATION_DICT,
    BAU_SCENARIO,
    SE4ALL_SCENARIO,
    SCENARIOS_DICT,
    SCENARIOS,
    SE4ALL_FLEX_SCENARIO,
    PROG_SCENARIO,
    GRID,
    MG,
    SHS,
    NO_ACCESS,
    # BASIC_ROWS,
    # BASIC_ROWS_FULL,
    # LABEL_COLUMNS,
    # BASIC_COLUMNS_ID,
    # GHG_COLUMNS_ID,
)

RES_COUNTRY = 'country'
RES_AGGREGATE = 'aggregate'
RES_COMPARE = 'compare'

POP_RES = 'pop'
INVEST_RES = 'invest'
GHG_BAU_RES = 'ghg-bau'
GHG_OTHER_RES = 'ghg'

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

TABLES_LABEL_STYLING = [
    {
        'if': {'column_id': 'labels'},
        'textAlign': 'left'
    }
]

TABLES_HEADER_STYLING = {
    'textAlign': 'center',
    'backgroundColor': '#e6e6e6',
    'fontWeight': 'bold'
}

POP_ROWS = [
    'People share',
    'People (Mio)',
    'HH (Mio)',
]

INVEST_ROWS = [
    'Investment BUSD',
    'Investment (TIER + 1) BUSD',
]

GHG_ROWS_BAU = [
    'GHG',
    'GHG (TIER + 1)',
]
GHG_ROWS_OTHER = [
    'GHG',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
    'GHG (TIER +1)',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
]

TABLE_ROWS = {
    POP_RES: POP_ROWS,
    INVEST_RES: INVEST_ROWS,
    GHG_BAU_RES: GHG_ROWS_BAU,
    GHG_OTHER_RES: GHG_ROWS_OTHER,
}

TABLE_ROWS_TOOLTIPS = {
    'People share': 'Percentage of people getting electricity access by 2030',
    'People (Mio)': 'Number of people getting electricity access by 2030',
    'HH (Mio)': 'Number of households getting electricity access by 2030',
    'HH demand (MW)': 'Expected household electricity demand by 2030, in MW',
    'HH demand (TIER + 1) (MW)':
        'Expected household electricity demand by 2030 for one TIER level up, in MW',
    'Investment BUSD':
        'Needed initial investments to supply expected demand by 2030, in million USD',
    'Investment (TIER + 1) BUSD':
        'Needed initial investments to supply expected demand by 2030 for one TIER level up, '
        'in million USD',
    'GHG': '',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]): '',
    'GHG (TIER +1)': '',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]): '',
}
# labels of the columns of the result tables
TABLE_COLUMNS_LABEL = ELECTRIFICATION_DICT.copy()
TABLE_COLUMNS_LABEL['labels'] = ''
TABLE_COLUMNS_LABEL['No Electricity'] = 'No Electricity'
TABLE_COLUMNS_LABEL['total'] = 'Total'
TABLE_COLUMNS_ID = ['labels'] + ELECTRIFICATION_OPTIONS + ['No Electricity'] + ['total']
COMPARE_COLUMNS_ID = ['labels']
for opt in ELECTRIFICATION_OPTIONS + ['No Electricity'] + ['total']:
    COMPARE_COLUMNS_ID.append(opt)
    COMPARE_COLUMNS_ID.append('comp_{}'.format(opt))


BARPLOT_ELECTRIFICATION_COLORS = {
    GRID: '#7030a0',
    MG: '#5b9bd5',
    SHS: '#ed7d31',
    NO_ACCESS: '#a6a6a6'
}

BARPLOT_YAXIS_OPT = ELECTRIFICATION_OPTIONS.copy() + ['No Electricity']


def create_tooltip(cell):
    """Create tooltips for tables"""
    return textwrap.dedent(
        '''
        **{value}**.
        '''.format(value=cell)
    )


def results_div(result_type, result_category):
    """

    :param result_type: one of country, aggregate, or compare
    :param result_category: one of pop, invest or ghg
    :return: a div with a title, a graph and a table
    """

    id_name = '{}-{}'.format(result_type, result_category)

    x_vals = ELECTRIFICATION_OPTIONS.copy() + ['No electricity']
    fs = 12

    # add a barplot above the tables with the results
    barplot = dcc.Graph(
        id='{}-barplot'.format(id_name),
        className='cell',
        figure=go.Figure(
            data=[
                go.Bar(
                    x=x_vals,
                    y=[0, 0, 0, 0],
                    text=[SCENARIOS_DICT[BAU_SCENARIO] for i in range(4)],
                    insidetextfont={'size': fs},
                    textposition='auto',
                    marker=dict(
                        color=BARPLOT_ELECTRIFICATION_COLORS,
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
                        color=BARPLOT_ELECTRIFICATION_COLORS,
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
                        color=BARPLOT_ELECTRIFICATION_COLORS,
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
    )

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

    columns_labels = TABLE_COLUMNS_LABEL
    columns_ids = []
    table_rows = TABLE_ROWS[]
    if result_type in [RES_COUNTRY, RES_AGGREGATE]:

        columns_ids = [{'name': TABLE_COLUMNS_LABEL[col], 'id': col} for col in TABLE_COLUMNS_ID]

    elif result_type == RES_COMPARE:
        for col in TABLE_COLUMNS_ID:
            if col != 'labels':
                columns_ids.append({'name': [TABLE_COLUMNS_LABEL[col], 'value'], 'id': col})
                columns_ids.append(
                    {'name': [TABLE_COLUMNS_LABEL[col], 'rel.'], 'id': 'comp_{}'.format(col)}
                )
            else:
                columns_ids.append({'name': TABLE_COLUMNS_LABEL[col], 'id': col})

    else:
        print('error in the result type in results_div()')

    # tables containing the results
    results_divs = [
        html.H4(
            id='{}-results-title'.format(id_name),
            className='cell',
            children='Results'
        ),
        dcc.Dropdown(
            id='{}-barplot-yaxis-input'.format(id_name),
            className='cell',
            options=[{'label': r, 'value': r} for r in table_rows],
            value=table_rows[0],
        ),
        barplot,
        dash_table.DataTable(
            id='{}-results-table'.format(id_name),
            columns=columns_ids,
            style_data_conditional=number_styling + TABLES_LABEL_STYLING,
            style_cell_conditional=TABLES_COLUMNS_WIDTH,
            style_header=TABLES_HEADER_STYLING,
            style_cell={
                'fontFamily': "Roboto"
            },
            tooltips={
                'labels': [
                    {
                        'type': 'markdown',
                        'value': create_tooltip(TABLE_ROWS_TOOLTIPS[lbl])
                    }
                    for lbl in table_rows
                ]

            }
        ),
    ]

        )
    )


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
