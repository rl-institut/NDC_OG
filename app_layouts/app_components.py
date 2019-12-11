import numpy as np
import pandas as pd
import textwrap
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input, State
import dash_daq as daq
import dash_table
import plotly.graph_objs as go
from app_main import APP_BG_COLOR, INFO_ICON
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
    RISE_SUB_INDICATORS,
    RESULTS_TITLE_HELP,
)

WORLD_ID = 'WD'
# Region names in nice format
REGIONS_GPD = dict(WD='World', SA='Central & South America', AF='Africa', AS='Asia')

# code in the raw data columns
REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')

# Region names for div dynamic creation
MAP_REGIONS = {'africa': 'AF', 'asia': 'AS', 'southamerica': 'SA'}

RES_COUNTRY = 'country'
RES_AGGREGATE = 'aggregate'
RES_COMPARE = 'compare'


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
    'Share of People',
    'People (Mio)',
    'Household (Mio)',
]

INVEST_ROWS = [
    'Lower TIER case',
    'Higher TIER case',
]

GHG_ROWS = [
    'Lower TIER case',
    'Higher TIER case',
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
    'Share of People': 'Percentage of people getting electricity access by 2030',
    'People (Mio)': 'Number of people getting electricity access by 2030',
    'Household (Mio)': 'Number of households getting electricity access by 2030',
    'HH demand (MW)': 'Expected household electricity demand by 2030, in MW',
    'HH demand (TIER + 1) (MW)':
        'Expected household electricity demand by 2030 for one TIER level up, in MW',
    'Lower TIER case':
        'Needed initial investments to supply expected demand by 2030, in million USD',
    'Higher TIER case':
        'Needed initial investments to supply expected demand by 2030 for one TIER level up, '
        'in million USD',
    'Lower TIER': 'Green-House-Gas emissions by 2030, in million ton CO2',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]): 'Difference of Green-House-Gas emissions '
        'with Business-as-Usual scenario emissions, in million tons CO2',
    'Higher TIER': 'Green-House-Gas emissions by 2030 for one TIER level up, in million ton CO2',
    'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]): 'Difference of Green-House-Gas emissions '
        'with Business-as-Usual scenario emissions for one TIER level up, in million tons CO2',
}
# labels of the columns of the result tables
TABLE_COLUMNS_LABEL = ELECTRIFICATION_DICT.copy()
TABLE_COLUMNS_LABEL['labels'] = ''
TABLE_COLUMNS_LABEL[NO_ACCESS] = NO_ACCESS
TABLE_COLUMNS_LABEL['total'] = 'Total'
TABLE_COLUMNS_ID = ['labels'] + ELECTRIFICATION_OPTIONS + [NO_ACCESS] + ['total']

TABLE_COLUMNS_ID = {
    POP_RES: ['labels'] + ELECTRIFICATION_OPTIONS + [NO_ACCESS] + ['total'],
    INVEST_RES: ['labels'] + ELECTRIFICATION_OPTIONS + ['total'],
    GHG_RES: ['labels'] + ELECTRIFICATION_OPTIONS + [NO_ACCESS] + ['total'],
    GHG_ER_RES: ['labels'] + ELECTRIFICATION_OPTIONS + [NO_ACCESS] + ['total']
}


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

BARPLOT_YAXIS_OPT = {
    POP_RES: ELECTRIFICATION_OPTIONS.copy() + [NO_ACCESS],
    INVEST_RES: ELECTRIFICATION_OPTIONS.copy(),
    GHG_RES: ELECTRIFICATION_OPTIONS.copy() + [NO_ACCESS],
    GHG_ER_RES: ELECTRIFICATION_OPTIONS.copy() + [NO_ACCESS],
}

BARPLOT_INVEST_YLABEL = 'Initial Investments (in billion USD)'
BARPLOT_GHG_YLABEL = 'GHG Emissions (in million tons CO2)'

MAP_DIV_STYLE = 'cell small-10 medium-4 '


def round_digits(val):
    """Formats number by rounding to 2 digits and add commas for thousands"""
    if np.isnan(val):
        answer = ''
    else:
        if len('{:d}'.format(int(val))) > 3:
            # add commas and no dot if in the thousands range
            answer = '{:,}'.format(val)
            answer = answer.split('.')[0]
        else:
            # add dot if not in the thousands range
            answer = '{:.2f}'.format(val)

        if np.round(val, 2) == 0:
            # always round the zero
            answer = '0'
    return answer


def format_percent(val):
    """Format number for percents."""
    if isinstance(val, str):
        answer = val
    else:
        if np.isnan(val):
            answer = ''
        else:
            if np.round(val, 2) == 0:
                answer = '0%'
            elif val >= 100:
                answer = '100%'
            else:
                answer = '{:.2f}%'.format(val)
    return answer


def create_tooltip(cell):
    """Create tooltips for tables"""
    return textwrap.dedent(
        '''
        **{value}**.
        '''.format(value=cell)
    )


def map_div(region, layout, map_data):
    return html.Div(
        id='{}-map-div'.format(region),
        className=MAP_DIV_STYLE + 'select-map',
        children=html.Div(
            className='grid-x',
            children=[
                html.H4(
                    children=REGIONS_GPD[MAP_REGIONS[region]],
                    className='cell align__center',
                ),
                html.Button(
                    id='{}-map-btn'.format(region),
                    children='Select Region',
                    className='btn btn--hollow cell medium-offset-4 medium-4'
                ),
                dcc.Graph(
                    id='{}-map'.format(region),
                    className='cell align__center',
                    figure=go.Figure(
                        data=map_data,
                        layout=layout),
                )
            ]
        )
    )


def results_div(result_type, result_category, flex_case=''):
    """
    :param result_type: one of country, aggregate, or compare
    :param result_category: one of pop, invest or ghg
    :param flex_case: string to distinguish the components' ids
    :return: a div with a title, a graph and a table
    """

    id_name = '{}{}-{}'.format(flex_case, result_type, result_category)

    if flex_case == 'flex-':
        class_name = 'cell small-12 medium-11 large-9 results_style'
    else:
        class_name = 'cell small-11 medium-10 large-8 results_style'

    barplot_mode = 'stack'
    if result_type == RES_COMPARE:
        barplot_mode = 'group'
        show_legends = False
    else:
        show_legends = True

    x_vals = [SCENARIOS_DICT[sce] for sce in SCENARIOS]
    fs = 15

    barplot_yaxis_opt = BARPLOT_YAXIS_OPT[result_category]

    # add a barplot above the tables with the results
    barplot = dcc.Graph(
        id='{}-barplot'.format(id_name),
        figure=go.Figure(
            data=[
                go.Bar(
                    x=x_vals,
                    y=[0, 0, 0],
                    name=y_opt.upper(),
                    text=y_opt.upper(),
                    insidetextfont={'size': fs, 'color': 'white'},
                    textposition='inside',
                    marker=dict(
                        color=BARPLOT_ELECTRIFICATION_COLORS[y_opt],
                    ),
                    hoverinfo='y+text'
                )
                for y_opt in barplot_yaxis_opt
            ],
            layout=go.Layout(
                title='',
                barmode=barplot_mode,
                paper_bgcolor=APP_BG_COLOR,
                plot_bgcolor=APP_BG_COLOR,
                showlegend=show_legends,
                autosize=True,
                margin=dict(
                    l=80,
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
    table_columns = TABLE_COLUMNS_ID[result_category]

    if result_type in [RES_COUNTRY, RES_AGGREGATE]:
        duplicate_headers = False
        columns_ids = [{'name': TABLE_COLUMNS_LABEL[col], 'id': col} for col in table_columns]

    elif result_type == RES_COMPARE:
        duplicate_headers = True
        for col in table_columns:
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
        html.Div(
            className='grid-x',
            children=[
                html.H3(
                    id='{}-results-title'.format(id_name),
                    children='Results',
                    className='cell medium-10 medium-offset-1'
                ),
                html.Div(
                    className='cell medium-1 align__right',
                    children=html.Img(
                        id='{}-results-title-help'.format(id_name),
                        src='data:image/png;base64,{}'.format(INFO_ICON.decode()),
                        title=RESULTS_TITLE_HELP[result_category],
                        className='info__icon'
                    )
                ),
            ]
        ),
        dcc.Dropdown(
            id='{}-barplot-yaxis-input'.format(id_name),
            options=[{'label': r, 'value': r} for r in table_rows],
            value=table_rows[0],
        ),
        barplot,
        html.Div(
            className='grid-x',
            children=[
                html.H3(
                    id='{}-results-table-title'.format(id_name),
                    children='Detailed results for scenario',
                    className='cell medium-10 medium-offset-1'

                ),
                html.Div(
                    className='cell medium-1 align__right display__none',
                    children=html.Img(
                        id='{}-results-table-title-help'.format(id_name),
                        src='data:image/png;base64,{}'.format(INFO_ICON.decode()),
                        title='Hover text',
                        className='info__icon'
                    )
                ),
            ]
        ),
        dash_table.DataTable(
            id='{}-results-table'.format(id_name),
            columns=columns_ids,
            style_data_conditional=TABLES_LABEL_STYLING,
            style_header=TABLES_HEADER_STYLING,
            css=[
                {
                    'selector': '.dash-cell div.dash-cell-value',
                    'rule': 'display: inline; white-space: inherit; '
                            'overflow: inherit; text-overflow: inherit;'
                },
                {
                    'selector': '.column-0',
                    'rule': 'text-decoration: underline; text-decoration-style: dotted;'
                },
            ],
            style_table={
                'marginTop': '10px'
            },
            style_cell={
                'fontFamily': 'roboto',
                'whiteSpace': 'no-wrap',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0,
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
        id='{}-div'.format(id_name),
        className=class_name,
        style={'display': 'none'},
        children=results_div_content
    )


def rise_slider(id_name, display_name):

    return html.Div(
        id='flex-rise-{}-div'.format(id_name),
        className='cell medium-4 grid-x grid-margin-x',
        title='rise mg description',
        children=[
            html.Div(
                id='flex-rise-{}-label'.format(id_name),
                className='cell medium-4 medium-offset-3 daq__slider__label',
                children="RISE Score for \n {}".format(ELECTRIFICATION_DICT[id_name])
            ),
            html.Div(
                id='flex-rise-{}-value'.format(id_name),
                className='cell medium-3 daq__slider__value',
                children=''
            ),
            html.Button(
                id='flex-rise-{}-btn'.format(id_name),
                className='cell medium-7 medium-offset-3 daq__slider__btn',
                children=display_name
            ),
            dcc.Slider(
                id='flex-rise-{}-input'.format(id_name),
                className='cell medium-10 medium-offset-1 daq__slider',
                min=0,
                max=100,
                value=67,
                step=1,
                updatemode='drag'
            ),

        ]
    )


def sub_indicator_line(id_name, text, score, sub_group_idx, sub_idx):

    return html.Div(
        className='cell grid-x',
        children=[
            html.P(
                className='cell medium-10',
                children=text,
            ),
            html.Div(
                className='cell medium-2 rise_sub__dropdown',
                children=dcc.Dropdown(
                    id='flex-rise-{}-sub-group{}-{}-toggle'.format(id_name, sub_group_idx, sub_idx),

                    options=[{'label': 'Yes', 'value': 1./score}, {'label': 'No', 'value': 0}],
                    value=0,
                    clearable=False
                )
            )
        ]
    )


def sub_indicator_table(id_name, sub_df=RISE_SUB_INDICATORS):
    """Fills the RISE sub indicators table."""
    sub_groups = sub_df.loc['rise_{}'.format(id_name)].sub_indicator_group.unique()
    divs = [
        html.H3(className='cell', children='RISE {} sub-indicators'.format(id_name)),
        html.Div(
            className='cell grid-x',
            children=[
                html.P(
                    className='cell medium-10',
                    children='''The Rise Subindicators set the framework for the development of a chosen indicator (Grid, MG, SHS). By answereing the questions by selecting yes or no from the drop down buttom you can experiment with different framework scenarios.''',
                ),
                html.Div(
                    className='cell medium-2 rise_sub__dropdown',
                    children=dcc.Dropdown(
                        id='flex-rise-{}-general-toggle'.format(id_name),
                        options=[
                            {'label': 'Yes to all', 'value': 1},
                            {'label': 'No to all', 'value': 0},
                            {'label': 'Default', 'value': -1},
                        ],
                        value=0,
                        clearable=False
                    )
                )
            ]
        )
    ]
    for j, sub_group in enumerate(sub_groups):
        divs.append(
            html.H4(className='cell', children=sub_group)
        )
        sub_group_df = RISE_SUB_INDICATORS.loc['rise_{}'.format(id_name)]
        sub_group_df = sub_group_df.loc[sub_group_df.sub_indicator_group == sub_group]
        texts = sub_group_df.sub_indicator_text.values
        values = sub_group_df.score_count_yes.values
        for i in range(len(sub_group_df.index)):
            divs.append(sub_indicator_line(id_name, texts[i], values[i], j, i))

    return divs


def controls_div():
    """Return controls for scenario dependent variables."""

    divs = [
        html.Div(
            id='flex-tier-div',
            className='cell',
            children=html.Div(
                id='flex-tier-mg-content',
                className='grid-x',
                children=[
                    html.Div(
                        id='flex-min-tier-mg-label',
                        className='cell medium-2',
                        children='Min MG TIER level'
                    ),
                    html.Div(
                        id='flex-min-tier-mg-input-div',
                        className='cell medium-2',
                        title='min tier level description',
                        children=dcc.Input(
                            id='flex-min-tier-mg-input',
                            value=3,
                            type='number',
                            min=3,
                            max=4,
                            step=1
                        )
                    ),
                    html.Div(
                        id='flex-tier-mg-value-div',
                        className='cell medium-3',
                        title='tier level description',
                        children=html.Div(
                            id='flex-tier-mg-value',
                            children=''
                        )
                    ),
                    html.Div(
                        id='flex-min-tier-shs-label',
                        className='cell medium-2',
                        children='Min SHS TIER level'
                    ),
                    html.Div(
                        id='flex-min-tier-shs-input-div',
                        className='cell medium-2',
                        title='min tier level description',
                        children=dcc.Input(
                            id='flex-min-tier-shs-input',
                            value=3,
                            type='number',
                            min=2,
                            max=5,
                            step=1
                        )
                    ),
                    html.Div(
                        id='flex-tier-shs-value-div',
                        className='cell medium-3',
                        title='tier level description',
                        children=html.Div(
                            id='flex-tier-shs-value',
                            children=''
                        )
                    ),
                ]
            )
        ),
        html.Div(
            id='flex-rise-div',
            className='cell',
            children=html.Div(
                className='grid-x align-center',
                children=[
                    rise_slider('grid', 'Show RISE Sub-Indicators'),
                    rise_slider('mg', 'Show RISE Sub-Indicators'),
                    rise_slider('shs', 'Show RISE Sub-Indicators'),
                    html.Div(
                        id='flex-rise-sub-indicators-div',
                        className='cell medium-9',
                        style={'display': 'none'},
                        children=[
                            html.Div(
                                id='flex-rise-sub-grid-div',
                                className='cell medium-8 grid-x align-center',
                                title='Click on the name left to the slider to display '
                                      'the sub-indicators',
                                children=sub_indicator_table('grid')
                            ),
                            html.Div(
                                id='flex-rise-sub-mg-div',
                                className='cell medium-4 grid-x align-center',
                                title='Click on the name left to the slider to display '
                                      'the sub-indicators',
                                children=sub_indicator_table('mg')
                            ),
                            html.Div(
                                id='flex-rise-sub-shs-div',
                                className='cell medium-8 grid-x align-center',
                                title='Click on the name left to the slider to display '
                                      'the sub-indicators',
                                children=sub_indicator_table('shs')
                            ),
                        ]
                    )
                ]
            )
        ),
    ]

    return divs
