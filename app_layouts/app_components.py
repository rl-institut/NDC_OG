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
    SCENARIOS,
    SCENARIOS_DICT,
    BAU_SCENARIO,
    ELECTRIFICATION_OPTIONS,
    ELECTRIFICATION_DICT,
    GRID,
    MG,
    SHS,
    NO_ACCESS,
    POP_RES,
    INVEST_RES,
    GHG_RES,
    GHG_ER_RES,
)

RES_COUNTRY = 'country'
RES_AGGREGATE = 'aggregate'
RES_COMPARE = 'compare'



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
    'Lower TIER cost',
    'Higher TIER cost',
]

GHG_ROWS = [
    'Lower TIER',
    'Higher TIER',
]
GHG_ER_ROWS = [
    'Lower TIER',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
    'Higher TIER',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
]

TABLE_ROWS = {
    POP_RES: POP_ROWS,
    INVEST_RES: INVEST_ROWS,
    GHG_RES: GHG_ROWS,
    GHG_ER_RES: GHG_ER_ROWS,
}

TABLE_ROWS_TOOLTIPS = {
    'People share': 'Percentage of people getting electricity access by 2030',
    'People (Mio)': 'Number of people getting electricity access by 2030',
    'HH (Mio)': 'Number of households getting electricity access by 2030',
    'HH demand (MW)': 'Expected household electricity demand by 2030, in MW',
    'HH demand (TIER + 1) (MW)':
        'Expected household electricity demand by 2030 for one TIER level up, in MW',
    'Lower TIER cost':
        'Needed initial investments to supply expected demand by 2030, in million USD',
    'Higher TIER cost':
        'Needed initial investments to supply expected demand by 2030 for one TIER level up, '
        'in million USD',
    'Lower TIER': '1',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]): '2',
    'Higher TIER': '3',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]): '4',
}
# labels of the columns of the result tables
TABLE_COLUMNS_LABEL = ELECTRIFICATION_DICT.copy()
TABLE_COLUMNS_LABEL['labels'] = ''
TABLE_COLUMNS_LABEL[NO_ACCESS] = NO_ACCESS
TABLE_COLUMNS_LABEL['total'] = 'Total'
TABLE_COLUMNS_ID = ['labels'] + ELECTRIFICATION_OPTIONS + [NO_ACCESS] + ['total']
COMPARE_COLUMNS_ID = ['labels']
for opt in ELECTRIFICATION_OPTIONS + [NO_ACCESS] + ['total']:
    COMPARE_COLUMNS_ID.append(opt)
    COMPARE_COLUMNS_ID.append('comp_{}'.format(opt))


BARPLOT_ELECTRIFICATION_COLORS = {
    GRID: '#7030a0',
    MG: '#5b9bd5',
    SHS: '#ed7d31',
    NO_ACCESS: '#a6a6a6'
}

BARPLOT_YAXIS_OPT = ELECTRIFICATION_OPTIONS.copy() + [NO_ACCESS]


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

    barplot_mode = 'stack'
    if result_type == RES_COMPARE:
        barplot_mode = 'group'

    x_vals = [SCENARIOS_DICT[sce] for sce in SCENARIOS]
    fs = 15

    # add a barplot above the tables with the results
    barplot = dcc.Graph(
        id='{}-barplot'.format(id_name),
        className='cell',
        figure=go.Figure(
            data=[
                go.Bar(
                    x=x_vals,
                    y=[0, 0, 0],
                    name=y_opt,
                    text=y_opt,
                    insidetextfont={'size': fs},
                    textposition='auto',
                    marker=dict(
                        color=BARPLOT_ELECTRIFICATION_COLORS[y_opt],
                    ),
                    hoverinfo='y+text'
                )
                for y_opt in BARPLOT_YAXIS_OPT
            ],
            layout=go.Layout(
                title='',
                barmode=barplot_mode,
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
                    hoverformat='.2f'
                )
            )
        ),
        config={
            'displayModeBar': True,
        }
    )

    columns_ids = []
    table_rows = TABLE_ROWS[result_category]

    if result_type in [RES_COUNTRY, RES_AGGREGATE]:
        duplicate_headers = False
        columns_ids = [{'name': TABLE_COLUMNS_LABEL[col], 'id': col} for col in TABLE_COLUMNS_ID]

    elif result_type == RES_COMPARE:
        duplicate_headers = True
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

    results_div_content = [
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
            css='cell',
            columns=columns_ids,
            style_data_conditional=TABLES_LABEL_STYLING,
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

            },
            merge_duplicate_headers=duplicate_headers
        ),
    ]

    return html.Div(
        className='cell',
        children=html.Div(
            className='grid-y',
            children=results_div_content
        )
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
        )
    ]

    return divs
