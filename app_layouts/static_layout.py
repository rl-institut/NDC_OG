import base64
import os
import numpy as np
import pandas as pd
import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from app_main import app, APP_BG_COLOR

from data.data_preparation import (
    MIN_TIER_LEVEL,
    SCENARIOS,
    BAU_SCENARIO,
    SCENARIOS_DESCRIPTIONS,
    WHAT_CAN_YOU_DO_DESCRIPTIONS,
    SCENARIOS_DICT,
    SCENARIOS_NAMES,
    ELECTRIFICATION_OPTIONS,
    ELECTRIFICATION_DICT,
    NO_ACCESS,
    POP_GET,
    EXO_RESULTS,
    POP_RES,
    INVEST_RES,
    GHG_RES,
    GHG_ER_RES,
    compute_ndc_results_from_raw_data,
    prepare_results_tables,
)

from .app_components import (
    results_div,
    map_div,
    round_digits,
    format_percent,
    TABLES_LABEL_STYLING,
    BARPLOT_ELECTRIFICATION_COLORS,
    RES_AGGREGATE,
    RES_COMPARE,
    RES_COUNTRY,
    TABLE_ROWS,
    TABLE_COLUMNS_ID,
    COMPARE_COLUMNS_ID,
    TABLE_COLUMNS_LABEL,
    BARPLOT_YAXIS_OPT,
    BARPLOT_INVEST_YLABEL,
    BARPLOT_GHG_YLABEL,
    MAP_DIV_STYLE,
    WORLD_ID,
    REGIONS_GPD,
    REGIONS_NDC,
    MAP_REGIONS,
)

URL_PATHNAME = 'static'


def extract_centroids(reg):
    """Load the longitude and latitude of countries per region."""
    if not isinstance(reg, list):
        reg = [reg]
    centroids = pd.read_csv('data/centroid.csv')
    return centroids.loc[centroids.region.isin(reg)].copy()


VIEW_GENERAL = 'general'
VIEW_COUNTRY = 'specific'
VIEW_AGGREGATE = 'aggregate'
VIEW_COMPARE = 'compare'

LOCAL_SCENARIO_DATA = {
    sce: compute_ndc_results_from_raw_data(sce, MIN_TIER_LEVEL) for sce in SCENARIOS
}

CENTROIDS_DATA = {reg: extract_centroids(REGIONS_NDC[reg]).to_json() for reg in REGIONS_NDC}

# list all region and countries to compare with a single country
COMPARE_OPTIONS = []
for _, r in LOCAL_SCENARIO_DATA[BAU_SCENARIO].sort_values('country').iterrows():
    COMPARE_OPTIONS.append({'label': r['country'], 'value': r['country_iso']})
COMPARE_OPTIONS = [{'label': v, 'value': k} for k, v in REGIONS_GPD.items()] + COMPARE_OPTIONS

COUNTRIES_ISO = extract_centroids(REGIONS_NDC[WORLD_ID]).country_iso.tolist()
COMPARE_ISO = COUNTRIES_ISO + list(REGIONS_NDC.keys())

# colors for hightlight of comparison
COLOR_BETTER = '#218380'
COLOR_WORSE = '#8F2D56'


def country_hover_text(input_df):
    """Format the text displayed by the hover."""
    df = input_df.copy()
    # share of the population with electricity in 2030 (per electrification option)
    df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0)

    return df.country + '<br>' \
           + '2030 Predictions <br>' \
           + '  Population: ' + df.pop_2030.div(1e6).map('{:.1f} MIO'.format) + '<br>' \
           + '  Grid share: ' + df.pop_get_grid_2030.map('{:.1%}'.format) + '<br>' \
           + '  MG: ' + df.pop_get_mg_2030.map('{:.1%}'.format) + '<br>' \
           + '  SHS: ' + df.pop_get_shs_2030.map('{:.1%}'.format) + '<br>'


# # Initial input data for the map
map_data = [
    go.Choropleth(
        colorscale=[[0, '#a5dbc2'], [1, '#a5dbc2']],
        autocolorscale=False,
        showscale=False,
        locationmode='ISO-3',
        hoverinfo='text',
        marker=go.choropleth.Marker(
            line=go.choropleth.marker.Line(
                color='rgb(255,255,255)',
                width=1.5
            )
        ),

    )
]

map_options = dict(
    paper_bgcolor=APP_BG_COLOR,
    #autosize=False,
    height=500,
    margin=dict(
        l=10,
        r=10,
        b=2,
        t=2
    ),
    legend=dict(orientation='h', xanchor='center', x=0.5)
)

MAP_LAYOUTS = {
    'asia': go.Layout(
        geo=go.layout.Geo(
            bgcolor=APP_BG_COLOR,
            scope='asia',
            showlakes=True,
            showcountries=True,
            lakecolor='rgb(255, 255, 255)',
            projection=dict(type='equirectangular'),
            lonaxis=dict(range=[40, 150]),
            lataxis=dict(range=[-15, 70]),
            framewidth=0,
        ),
        **map_options
    ),
    'africa': go.Layout(
        geo=go.layout.Geo(
            bgcolor=APP_BG_COLOR,
            scope='africa',
            showlakes=True,
            showcountries=True,
            lakecolor='rgb(255, 255, 255)',
            projection=dict(type='equirectangular'),
        ),
        **map_options
    ),
    'southamerica': go.Layout(
        geo=go.layout.Geo(
            bgcolor=APP_BG_COLOR,
            scope='world',
            showlakes=True,
            showcountries=True,
            lakecolor='rgb(255, 255, 255)',
            projection=dict(type='equirectangular'),
            lonaxis=dict(range=[-95, -30.0]),
            lataxis=dict(range=[-60, 30]),
            framewidth=0,
        ),
        **map_options
    )
}


def layout(country_iso=None, sce=None, compare_iso=None):
    if sce is None or sce not in SCENARIOS:
        sce = BAU_SCENARIO
    if country_iso not in COUNTRIES_ISO:
        country_iso = None
    if compare_iso not in COMPARE_ISO:
        compare_iso = None
    return html.Div(
        id='main-div',
        children=[
            dcc.Store(
                id='static-url-store',
                storage_type='session',
                data=dict(
                    country_iso=country_iso,
                    sce=sce,
                    compare_iso=compare_iso
                )
            ),
            dcc.Store(
                id='data-store',
                storage_type='session',
                data=CENTROIDS_DATA.copy()
            ),
            dcc.Store(
                id='view-store',
                storage_type='session',
                data={'app_view': VIEW_GENERAL}
            ),
            html.Div(
                id='main-content',
                className='grid-x',
                children=[
                    html.Div(
                        id='main-head-div',
                        className='cell',
                        children=html.Div(
                            id='main-head-content',
                            className='grid-x',
                            children=[
                                html.Div(
                                    id='left-header-div',
                                    className='cell medium-6',
                                    children=[

                                        html.Div(
                                            id='general-info-div',
                                            className='scenario__info',
                                            children=''
                                        ),
                                    ]
                                ),
                                html.Div(
                                    id='right-header-div',
                                    className='cell medium-6',
                                    children=[
                                        html.Div(
                                            id='scenario-input-div',
                                            className='grid-x input-div',
                                            children=[
                                                html.Div(
                                                    id='scenario-label',
                                                    className='cell medium-3',
                                                    children='Explore a scenario:'
                                                ),
                                                html.Div(
                                                    id='scenario-input-wrapper',
                                                    className='cell medium-9',
                                                    children=dcc.Dropdown(
                                                        id='scenario-input',
                                                        options=[
                                                            {
                                                                'label': '{} ({})'.format(
                                                                    SCENARIOS_NAMES[k],
                                                                    SCENARIOS_DICT[k]
                                                                ),
                                                                'value': k
                                                            }
                                                            for k in SCENARIOS
                                                        ],
                                                        value=sce,
                                                    )
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            id='region-input-div',
                                            className='grid-x input-div',
                                            children=[
                                                html.Div(
                                                    id='region-label',
                                                    className='cell medium-3',
                                                    children='Region:'
                                                ),
                                                html.Div(
                                                    id='region-input-wrapper',
                                                    className='cell medium-9',
                                                    title='region selection description',
                                                    children=dcc.Dropdown(
                                                        id='region-input',
                                                        options=[
                                                            {'label': v, 'value': k}
                                                            for k, v in REGIONS_GPD.items()
                                                        ],
                                                        value=WORLD_ID
                                                    )
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            id='country-input-div',
                                            title='country selection description',
                                            className='grid-x input-div',
                                            children=[
                                                html.Div(
                                                    id='country-label',
                                                    className='cell medium-3',
                                                    children='Country:'
                                                ),
                                                html.Div(
                                                    id='country-input-wrapper',
                                                    className='cell medium-9',
                                                    children=dcc.Dropdown(
                                                        id='country-input',
                                                        options=[],
                                                        value=country_iso,
                                                        multi=False
                                                    )
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            id='compare-input-div',
                                            className='grid-x input-div',
                                            style={'visibility': 'hidden'},
                                            children=[
                                                html.Div(
                                                    id='country-comp-label',
                                                    className='cell medium-3',
                                                    children='Compare with:'
                                                ),
                                                html.Div(
                                                    id='compare-input-wrapper',
                                                    className='cell medium-9',
                                                    children=dcc.Dropdown(
                                                        id='compare-input',
                                                        options=COMPARE_OPTIONS,
                                                        value=compare_iso,
                                                        multi=False
                                                    )
                                                ),

                                            ],

                                        ),
                                        html.Div(
                                            id='specific-info-div',
                                            className='instructions',
                                            children=''
                                        ),
                                    ]
                                ),

                            ]
                        ),
                    ),
                    html.Div(
                        id='maps-div',
                        className='grid-x grid-margin-x align-center',
                        children=[
                            map_div(region, MAP_LAYOUTS[region], map_data)
                            for region in MAP_REGIONS
                        ]
                    ),
                    html.Div(
                        id='main-results-div',
                        children=html.Div(
                            id='main-results-contents',
                            className='grid-x align-center',
                            children=[

                                         html.Div(
                                             id='results-info-div',
                                             className='cell medium-10 large-8 country_info_style',
                                             children=''
                                         ),
                                     ] + [
                                         results_div(res_type, res_category)
                                         for res_category in [POP_RES, INVEST_RES, GHG_RES]
                                         for res_type in [RES_COUNTRY, RES_AGGREGATE, RES_COMPARE]
                                     ]
                        ),
                    ),
                ]
            ),
        ]
    )

# Barplot and results callbacks for single country


def country_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format('country', result_category)

    result_cat = result_category

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('country-input', 'value'),
            Input('{}-barplot-yaxis-input'.format(id_name), 'value')
        ],
        [
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def update_barplot(country_sel, y_sel, fig):

        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        country_iso = country_sel
        if country_iso is not None:
            x_vals = [SCENARIOS_DICT[sce] for sce in SCENARIOS]
            y_vals = []
            for sce_id, sce in enumerate(SCENARIOS):

                df = LOCAL_SCENARIO_DATA[sce]
                # narrow to the country's results
                df = df.loc[df.country_iso == country_iso]
                # extract the results formatted with good units
                results_data = prepare_results_tables(df, sce, result_category)
                # select the row corresponding to the barplot y axis choice
                y_vals.append(results_data[idx_y])

            y_vals = np.vstack(y_vals)

            for j, opt in enumerate(BARPLOT_YAXIS_OPT[result_cat]):
                fig['data'][j].update({'x': x_vals})
                fig['data'][j].update({'y': y_vals[:, j]})

            if result_cat == INVEST_RES:
                yaxis_label = BARPLOT_INVEST_YLABEL
            elif result_cat == GHG_RES:
                yaxis_label = BARPLOT_GHG_YLABEL
            else:
                yaxis_label = y_sel

            fig['layout'].update(
                {
                    'yaxis': go.layout.YAxis(
                        title=go.layout.yaxis.Title(
                            text=yaxis_label,
                        )
                    )
                }
            )

        return fig

    update_barplot.__name__ = 'update_%s_barplot' % id_name

    return update_barplot


def country_table_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(RES_COUNTRY, result_category)

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'data'),
        [
            Input('country-input', 'value'),
            Input('scenario-input', 'value'),
        ]
    )
    def update_table(
            country_iso,
            scenario,
    ):
        """Display information and study's results for a country."""

        result_cat = result_category

        answer_table = []
        if country_iso is not None:
            if scenario in SCENARIOS:

                df = LOCAL_SCENARIO_DATA[scenario]
                df = df.loc[df.country_iso == country_iso]

                ghg_er = False
                if result_cat == GHG_RES and scenario != BAU_SCENARIO:
                    ghg_er = True
                    result_cat = GHG_ER_RES

                results_data = prepare_results_tables(df, scenario, result_cat, ghg_er)

                total = np.nansum(results_data, axis=1)
                # prepare a DataFrame
                results_data = pd.DataFrame(
                    data=results_data,
                    columns=ELECTRIFICATION_OPTIONS + [NO_ACCESS]
                )
                # sums of the rows
                results_data['total'] = pd.Series(total)

                # Format the digits
                if result_cat == POP_RES:
                    results_data.iloc[1:, 0:] = results_data.iloc[1:, 0:].applymap(
                        round_digits
                    )
                    results_data.iloc[0, 0:] = results_data.iloc[0, 0:].map(
                        format_percent
                    )
                else:
                    results_data = results_data.applymap(round_digits)
                # label of the table rows
                table_rows = TABLE_ROWS[result_cat]
                results_data['labels'] = pd.Series(table_rows)

                answer_table = results_data[TABLE_COLUMNS_ID[result_cat]].to_dict('records')
        return answer_table

    update_table.__name__ = 'update_%s_table' % id_name
    return update_table


# Barplot and results callbacks for region


def aggregate_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(RES_AGGREGATE, result_category)

    result_cat = result_category

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('region-input', 'value'),
            Input('{}-barplot-yaxis-input'.format(id_name), 'value')
        ],
        [
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def update_barplot(region_id, y_sel, fig):

        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        if region_id is not None:
            x_vals = [SCENARIOS_DICT[sce] for sce in SCENARIOS]
            y_vals = []
            for sce_id, sce in enumerate(SCENARIOS):
                df = LOCAL_SCENARIO_DATA[sce]

                if region_id != WORLD_ID:
                    # narrow to the region if the scope is not on the whole world
                    df = df.loc[df.region == REGIONS_NDC[region_id]]

                # aggregate the results
                df = df[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

                # compute the percentage of population with electricity access
                results_data = prepare_results_tables(df, sce, result_category)

                y_vals.append(results_data[idx_y])

            y_vals = np.vstack(y_vals)

            for j, opt in enumerate(BARPLOT_YAXIS_OPT[result_cat]):
                fig['data'][j].update({'x': x_vals})
                fig['data'][j].update({'y': y_vals[:, j]})

            if result_cat == INVEST_RES:
                yaxis_label = BARPLOT_INVEST_YLABEL
            elif result_cat == GHG_RES:
                yaxis_label = BARPLOT_GHG_YLABEL
            else:
                yaxis_label = y_sel

            fig['layout'].update(
                {
                    'yaxis': go.layout.YAxis(
                        title=go.layout.yaxis.Title(
                            text=yaxis_label,
                        )
                    )
                }
            )

        return fig

    update_barplot.__name__ = 'update_%s_barplot' % id_name
    return update_barplot


def aggregate_table_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(RES_AGGREGATE, result_category)

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'data'),
        [
            Input('region-input', 'value'),
            Input('scenario-input', 'value'),
        ],
    )
    def update_table(
            region_id,
            scenario,
    ):
        """Display information and study's results for a country."""

        result_cat = result_category

        answer_table = []
        if region_id is not None:
            if scenario in SCENARIOS:

                df = LOCAL_SCENARIO_DATA[scenario]
                if region_id != WORLD_ID:
                    # narrow to the region if the scope is not on the whole world
                    df = df.loc[df.region == REGIONS_NDC[region_id]]
                # aggregate the results
                df = df[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

                ghg_er = False
                if result_cat == GHG_RES and scenario != BAU_SCENARIO:
                    ghg_er = True
                    result_cat = GHG_ER_RES

                results_data = prepare_results_tables(df, scenario, result_cat, ghg_er)

                total = np.nansum(results_data, axis=1)
                # prepare a DataFrame
                results_data = pd.DataFrame(
                    data=results_data,
                    columns=ELECTRIFICATION_OPTIONS + [NO_ACCESS]
                )
                # sums of the rows
                results_data['total'] = pd.Series(total)

                # Format the digits
                if result_cat == POP_RES:
                    results_data.iloc[1:, 0:] = results_data.iloc[1:, 0:].applymap(
                        round_digits
                    )
                    results_data.iloc[0, 0:] = results_data.iloc[0, 0:].map(
                        format_percent
                    )
                else:
                    results_data = results_data.applymap(round_digits)
                # label of the table rows
                table_rows = TABLE_ROWS[result_cat]
                results_data['labels'] = pd.Series(table_rows)

                answer_table = results_data[TABLE_COLUMNS_ID[result_cat]].to_dict('records')
        return answer_table

    update_table.__name__ = 'update_%s_table' % id_name
    return update_table


def country_aggregate_title_callback(app_handle, result_type, result_category):

    id_name = '{}-{}'.format(result_type, result_category)

    if result_type == RES_COUNTRY:
        inputs = [Input('country-input', 'value')]
    elif result_type == RES_AGGREGATE:
        inputs = [Input('region-input', 'value')]

    inputs.append(Input('scenario-input', 'value'))

    if result_category == POP_RES:
        description = 'Electrification Mix'
    elif result_category == INVEST_RES:
        description = 'Initial Investments Needed (in billion USD)'
    else:
        description = 'Cumulated GHG Emissions (2017-2030) (in million tons CO2)'

    @app_handle.callback(
        Output('{}-results-title'.format(id_name), 'children'),
        inputs,
    )
    def update_title(input_trigger, scenario):

        answer = 'Results'
        if scenario in SCENARIOS and input_trigger is not None:
            if result_type == RES_COUNTRY:
                df = LOCAL_SCENARIO_DATA[scenario]
                answer = '{}: '.format(df.loc[df.country_iso == input_trigger].country.values[0])
            elif result_type == RES_AGGREGATE:
                answer = '{}: Aggregated '.format(
                    REGIONS_GPD[input_trigger]
                )
        return '{}{}'.format(answer, description)

    update_title.__name__ = 'update_%s_title' % id_name
    return update_title


# Barplot and results callbacks for comparison between region and country


def compare_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(RES_COMPARE, result_category)

    result_cat = result_category

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('country-input', 'value'),
            Input('compare-input', 'value'),
            Input('scenario-input', 'value'),
            Input('{}-barplot-yaxis-input'.format(id_name), 'value')
        ],
        [
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def update_barplot(country_sel, comp_sel, scenario, y_sel, fig):
        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        if country_sel is not None and comp_sel is not None:
            comp_name = comp_sel
            df = LOCAL_SCENARIO_DATA[scenario]
            df_comp = df.copy()
            df_ref = df.loc[df.country_iso == country_sel]
            if comp_sel in REGIONS_NDC:
                # compare the reference country to a region
                if comp_sel != WORLD_ID:
                    df_comp = df_comp.loc[df_comp.region == REGIONS_NDC[comp_sel]]
                df_comp = df_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)
                comp_name = REGIONS_GPD[comp_sel]
                comp_iso = comp_name
            else:
                # compare the reference country to a country
                df_comp = df_comp.loc[df_comp.country_iso == comp_sel]
                comp_name = df_comp.country.values[0]
                comp_iso = df_comp.country_iso.values[0]

            ref_results_data = prepare_results_tables(df_ref, scenario, result_category)
            comp_results_data = prepare_results_tables(df_comp, scenario, result_category)

            x = [opt.upper() for opt in ELECTRIFICATION_OPTIONS] + [NO_ACCESS]
            y_ref = ref_results_data[idx_y]
            y_comp = comp_results_data[idx_y]

            country_txt = [country_sel for i in range(4)]

            comp_txt = [comp_iso for i in range(4)]

            if result_cat == INVEST_RES:
                x = x[:-1]
                y_ref = y_ref[:-1]
                y_comp = y_comp[:-1]
                country_txt = country_txt[:-1]
                comp_txt = comp_txt[:-1]

            fs = 15

            fig.update(
                {
                    'data': [
                        go.Bar(
                            x=x,
                            y=y_ref,
                            text=country_txt,
                            insidetextfont={'size': fs, 'color': 'white'},
                            textposition='auto',
                            marker=dict(
                                color=list(BARPLOT_ELECTRIFICATION_COLORS.values())
                            ),
                            hoverinfo='y+text'
                        ),
                        go.Bar(
                            x=x,
                            y=y_comp,
                            text=comp_txt,
                            insidetextfont={'size': fs, 'color': 'white'},
                            textposition='auto',
                            marker=dict(
                                color=['#a062d0', '#9ac1e5', '#f3a672', '#cccccc']
                            ),
                            hoverinfo='y+text'
                        ),
                    ],
                }
            )

            if result_cat == INVEST_RES:
                yaxis_label = BARPLOT_INVEST_YLABEL
            elif result_cat == GHG_RES:
                yaxis_label = BARPLOT_GHG_YLABEL
            else:
                yaxis_label = y_sel

            fig['layout'].update(
                {
                    'yaxis': go.layout.YAxis(
                        title=go.layout.yaxis.Title(
                            text=yaxis_label,
                        )
                    )
                }
            )

        return fig

    update_barplot.__name__ = 'update_%s_barplot' % id_name
    return update_barplot


def compare_table_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'data'),
        [
            Input('country-input', 'value'),
            Input('compare-input', 'value'),
            Input('scenario-input', 'value'),
        ],
    )
    def update_table(country_iso, comp_sel, scenario):
        """Display information and study's results comparison between countries."""
        answer_table = []

        result_cat = result_category

        # extract the data from the selected scenario if a country was selected
        if country_iso is not None and comp_sel is not None:
            if scenario in SCENARIOS:
                df = LOCAL_SCENARIO_DATA[scenario]
                df_comp = df.copy()
                df = df.loc[df.country_iso == country_iso]
                if comp_sel in REGIONS_NDC:
                    # compare the reference country to a region
                    if comp_sel != WORLD_ID:
                        df_comp = df_comp.loc[df_comp.region == REGIONS_NDC[comp_sel]]
                    df_comp = df_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)
                else:
                    # compare the reference country to a country
                    df_comp = df_comp.loc[df_comp.country_iso == comp_sel]

                ghg_er = False
                if result_cat == GHG_RES and scenario != BAU_SCENARIO:
                    ghg_er = True
                    result_cat = GHG_ER_RES

                results_data = prepare_results_tables(df, scenario, result_cat, ghg_er)
                comp_results_data = prepare_results_tables(df_comp, scenario, result_cat, ghg_er)

                total = np.nansum(results_data, axis=1)
                comp_total = np.nansum(comp_results_data, axis=1)

                results_data = np.hstack([results_data, comp_results_data])

                comp_ids = ['comp_{}'.format(c) for c in ELECTRIFICATION_OPTIONS] \
                           + ['comp_No Electricity']
                # prepare a DataFrame
                results_data = pd.DataFrame(
                    data=results_data,
                    columns=ELECTRIFICATION_OPTIONS + [NO_ACCESS] + comp_ids
                )
                # sums of the rows
                results_data['total'] = pd.Series(total)
                results_data['comp_total'] = pd.Series(comp_total)
                # Format the digits
                if result_cat == POP_RES:
                    results_data.iloc[1:, 0:] = results_data.iloc[1:, 0:].applymap(
                        round_digits
                    )
                    results_data.iloc[0, 0:] = results_data.iloc[0, 0:].map(
                        format_percent
                    )
                else:
                    results_data = results_data.applymap(round_digits)
                # label of the table rows
                table_rows = TABLE_ROWS[result_cat]
                results_data['labels'] = pd.Series(table_rows)

                answer_table = results_data[COMPARE_COLUMNS_ID].to_dict('records')
        return answer_table

    update_table.__name__ = 'update_%s_table' % id_name
    return update_table


def compare_title_callback(app_handle, result_category):

    id_name = '{}-{}'.format(RES_COMPARE, result_category)

    if result_category == POP_RES:
        description = 'Electrification Mix {}'
    elif result_category == INVEST_RES:
        description = 'Initial Investments needed {} (in billion USD)'
    else:
        description = 'Cumulated GHG Emissions (2017-2030) {} (in million tons CO2)'

    @app_handle.callback(
        Output('{}-results-title'.format(id_name), 'children'),
        [
            Input('country-input', 'value'),
            Input('compare-input', 'value'),
            Input('scenario-input', 'value')
        ],
    )
    def update_title(country_iso, comp_sel, scenario):

        answer = 'Results'
        if scenario in SCENARIOS and country_iso is not None and comp_sel is not None:
            df = LOCAL_SCENARIO_DATA[scenario]
            if comp_sel in REGIONS_NDC:
                comp_name = REGIONS_GPD[comp_sel]
            else:
                comp_name = df.loc[df.country_iso == comp_sel].country.values[0]
                comp_iso = df.loc[df.country_iso == comp_sel].country_iso.values[0]
                comp_name = '{} ({})'.format(comp_name, comp_iso)

            country_name = df.loc[df.country_iso == country_iso].country.values[0]

            answer = 'Comparison of {}'.format(
                description.format(
                    'between {} ({}) and {}'.format(
                        country_name,
                        country_iso,
                        comp_name,
                    )
                )
            )
        return answer

    update_title.__name__ = 'update_%s_title' % id_name
    return update_title


def table_title_callback(app_handle, result_type, result_category):

    id_name = '{}-{}'.format(result_type, result_category)

    if result_type == RES_COUNTRY:
        inputs = [Input('country-input', 'value')]
    elif result_type == RES_AGGREGATE:
        inputs = [Input('region-input', 'value')]
    elif result_type == RES_COMPARE:
        inputs = [Input('compare-input', 'value')]

    inputs.append(Input('scenario-input', 'value'))

    @app_handle.callback(
        Output('{}-results-table-title'.format(id_name), 'children'),
        inputs,
    )
    def update_title(input_trigger, scenario):

        answer = 'Detailed results'
        if scenario in SCENARIOS and input_trigger is not None:
            answer = 'Detailed Results for {} ({}) Scenario'.format(
                SCENARIOS_NAMES[scenario],
                SCENARIOS_DICT[scenario]
            )
        if result_category == INVEST_RES:
            answer = answer + ' (in billion USD)'
        elif result_category == GHG_RES:
            answer = answer + ' (in million tons CO2)'

        return answer

    update_title.__name__ = 'update_%s_title' % id_name
    return update_title


def compare_table_columns_title_callback(app_handle, result_category):

    id_name = '{}-{}'.format(RES_COMPARE, result_category)

    result_cat = result_category

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'columns'),
        [
            Input('country-input', 'value'),
            Input('compare-input', 'value'),
        ]
    )
    def update_table_columns_title(country_sel, comp_sel):

        columns_ids = []
        if country_sel is not None and comp_sel is not None:
            for col in TABLE_COLUMNS_ID[result_cat]:
                if col != 'labels':
                    columns_ids.append(
                        {'name': [TABLE_COLUMNS_LABEL[col], country_sel], 'id': col}
                    )
                    columns_ids.append(
                        {'name': [TABLE_COLUMNS_LABEL[col], comp_sel], 'id': 'comp_{}'.format(col)}
                    )
                else:
                    columns_ids.append({'name': TABLE_COLUMNS_LABEL[col], 'id': col})
        return columns_ids

    update_table_columns_title.__name__ = 'update_%s_table_columns_title' % id_name
    return update_table_columns_title


# def compare_table_styling_callback(app_handle, result_category):
#
#     id_name = '{}-{}'.format(RES_COMPARE, result_category)
#
#     result_cat = result_category
#
#     @app_handle.callback(
#         Output('{}-results-table'.format(id_name), 'style_data_conditional'),
#         [Input('{}-results-table'.format(id_name), 'data')],
#         [
#             State('{}-results-table'.format(id_name), 'style_data_conditional'),
#             State('compare-input', 'value'),
#             State('country-input', 'value'),
#             State('scenario-input', 'value')
#         ]
#     )
#     def update_table_styling(cur_data, cur_style, comp_sel, country_iso, scenario):
#
#         if comp_sel is not None and country_iso is not None:
#             data = pd.DataFrame.from_dict(cur_data)
#
#             col_ref = TABLE_COLUMNS_ID[result_cat][1:]
#             col_comp = ['comp_{}'.format(col) for col in TABLE_COLUMNS_ID[result_cat][1:]]
#             data = data[col_ref + col_comp].applymap(
#                 lambda x: 0 if x == '' else float(x.replace(',', '').replace('%', '')))
#             ref = data[col_ref]
#             comp = data[col_comp]
#
#             compare_results_styling = []
#             for j, col in enumerate(col_ref):
#                 for i in range(len(ref.index)):
#                     apply_condition = True
#                     if ref.iloc[i, j] > comp.iloc[i, j]:
#                         color = COLOR_BETTER
#                         font = 'bold'
#                         if result_category == GHG_RES:
#                             if scenario == BAU_SCENARIO or np.mod(i, 2) == 0:
#                                 color = COLOR_WORSE
#                                 font = 'normal'
#                     elif ref.iloc[i, j] < comp.iloc[i, j]:
#                         color = COLOR_WORSE
#                         font = 'normal'
#                         if result_category == GHG_RES:
#                             if scenario == BAU_SCENARIO or np.mod(i, 2) == 0:
#                                 color = COLOR_BETTER
#                                 font = 'bold'
#                     else:
#                         apply_condition = False
#
#                     if apply_condition:
#                         compare_results_styling.append(
#                             {
#                                 "if": {"column_id": col, "row_index": i},
#                                 'color': color,
#                                 'fontWeight': font
#                             }
#                         )
#                     cur_style = TABLES_LABEL_STYLING + compare_results_styling
#         return cur_style
#
#     update_table_styling.__name__ = 'update_%s_table_styling' % id_name
#     return update_table_styling


def ghg_dropdown_options_callback(app_handle, result_type):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(result_type, GHG_RES)

    @app_handle.callback(
        Output('{}-barplot-yaxis-input'.format(id_name), 'options'),
        [Input('scenario-input', 'value')]
    )
    def update_barplot(scenario):
        answer = []
        if scenario in SCENARIOS:
            table_rows = TABLE_ROWS[GHG_RES]
            answer = [{'label': r, 'value': r} for r in table_rows]
        return answer

    update_barplot.__name__ = 'update_%s_dropdown' % id_name
    return update_barplot


def toggle_results_div_callback(app_handle, result_type, result_category):

    id_name = '{}-{}'.format(result_type, result_category)

    @app_handle.callback(
        Output('{}-div'.format(id_name), 'style'),
        [Input('view-store', 'data')],
        [State('{}-div'.format(id_name), 'style')]
    )
    def toggle_results_div_display(cur_view, cur_style):
        """Change the display of results-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if result_type == RES_COUNTRY:
            if cur_view['app_view'] == VIEW_COUNTRY:
                cur_style = {}
            elif cur_view['app_view'] in [VIEW_GENERAL,VIEW_AGGREGATE, VIEW_COMPARE]:
                cur_style.update({'display': 'none'})
        elif result_type == RES_AGGREGATE:
            if cur_view['app_view'] == VIEW_AGGREGATE:
                cur_style = {}
            elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
                cur_style.update({'display': 'none'})
        elif result_type == RES_COMPARE:
            if cur_view['app_view'] == VIEW_COMPARE:
                cur_style = {}
            elif cur_view['app_view'] in [VIEW_GENERAL, VIEW_COUNTRY, VIEW_AGGREGATE]:
                cur_style.update({'display': 'none'})

        return cur_style

    toggle_results_div_display.__name__ = 'toggle_%s_display' % id_name
    return toggle_results_div_display


def update_maps_callback(app_handle, region):

    @app_handle.callback(
        Output('{}-map'.format(region), 'figure'),
        [
            Input('scenario-input', 'value'),
        ],
        [
            State('{}-map'.format(region), 'figure'),
            State('data-store', 'data')
        ]
    )
    def update_map(scenario, fig, cur_data):
        """Plot color map of the percentage of people with a given electrification option."""
        region_id = MAP_REGIONS[region]

        # load the data of the scenario
        df = LOCAL_SCENARIO_DATA[scenario]

        centroid = pd.read_json(cur_data[region_id])

        # narrow to the region if the scope is not on the whole world
        df = df.loc[df.region == REGIONS_NDC[region_id]]

        if region_id == 'SA':
            region_name = REGIONS_GPD[WORLD_ID]
        elif region_id == 'AS':
            region_name = REGIONS_GPD[region_id]
        elif region_id == 'AF':
            region_name = REGIONS_GPD[region_id]
        else:
            region_name = REGIONS_GPD[region_id]

        fig['data'][0].update(
            {
                'locations': df['country_iso'],
                'z': np.ones(len(df.index)),
                'text': country_hover_text(df),
            }
        )

        points = []
        i = 0
        if scenario == BAU_SCENARIO:
            z = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0).round(3)
            z[NO_ACCESS] = 1 - z.sum(axis=1)
            options = ELECTRIFICATION_OPTIONS + [NO_ACCESS]

        else:
            z = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0).round(3)
            z[NO_ACCESS] = 0
            options = ELECTRIFICATION_OPTIONS
        n = 4
        colors = BARPLOT_ELECTRIFICATION_COLORS
        show_legend = True

        # Populate the map with bar plots mapped onto circles
        for idx, c in centroid.iterrows():
            for j, opt in enumerate(options):
                if j == n - 1 and z.iloc[i, j] == 0:
                    # Otherwise points with radius of 0 are displayed with non zero radius
                    pass
                else:
                    points.append(
                        go.Scattergeo(
                            lon=[c['Longitude']],
                            lat=[c['Latitude']],
                            hoverinfo='skip',
                            marker=go.scattergeo.Marker(
                                size=z.iloc[i, j:n].sum() * 25,
                                color=colors[opt],
                                line=go.scattergeo.marker.Line(width=0)
                            ),
                            showlegend=show_legend,
                            legendgroup='group{}'.format(j),
                            name=ELECTRIFICATION_DICT[opt],
                        )
                    )
            show_legend = False
            i = i + 1

        fig['data'][1:] = points

        return fig

    update_map.__name__ = 'update_%s_map' % region
    return update_map


def select_map_callback(app_handle, region):
    @app_handle.callback(
        Output('{}-map-div'.format(region), 'className'),
        [
            Input('{}-map-btn'.format(reg), 'n_clicks')
            for reg in MAP_REGIONS
        ],
        [State('{}-map-btn'.format(region), 'className')]
    )
    def select_map(*args):
        ctx = dash.callback_context
        answer = MAP_DIV_STYLE + 'select-map'
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            if region in prop_id:
                answer = MAP_DIV_STYLE + 'select-map-selected'
        return answer

    select_map.__name__ = 'select_%s_map' % region
    return select_map


def callbacks(app_handle):

    # build callbacks automatically for various categories
    for res_cat in [POP_RES, INVEST_RES, GHG_RES]:

        country_barplot_callback(app_handle, res_cat)
        country_table_callback(app_handle, res_cat)

        aggregate_barplot_callback(app_handle, res_cat)
        aggregate_table_callback(app_handle, res_cat)

        compare_barplot_callback(app_handle, res_cat)
        compare_table_callback(app_handle, res_cat)
        # compare_table_styling_callback(app_handle, res_cat)
        compare_table_columns_title_callback(app_handle, res_cat)

        for res_type in [RES_COUNTRY, RES_AGGREGATE]:
            country_aggregate_title_callback(app_handle, res_type, res_cat)
        compare_title_callback(app_handle, res_cat)

        for res_type in [RES_COUNTRY, RES_AGGREGATE, RES_COMPARE]:
            toggle_results_div_callback(app_handle, res_type, res_cat)
            table_title_callback(app_handle, res_type, res_cat)

    for res_type in [RES_COUNTRY, RES_AGGREGATE, RES_COMPARE]:
        ghg_dropdown_options_callback(app_handle, res_type)

    for region in MAP_REGIONS:
        update_maps_callback(app_handle, region)
        select_map_callback(app_handle, region)


    @app_handle.callback(
        Output('view-store', 'data'),
        [
            Input('scenario-input', 'value'),
            Input('region-input', 'value'),
            Input('country-input', 'value'),
            Input('compare-input', 'value')
        ],
        [State('view-store', 'data')]
    )
    def update_view(scenario, region_id, country_sel, comp_sel, cur_view):
        """Toggle between the different views of the app.

        There are currently two views:
        - VIEW_GENERAL : information panel on the left and map of the world with countries of the
        study highlighted on the right panel. The user can hover over the countries and a piechart
        will update on the right panel. The only controls available in this view are the scenario
        and electrification option dropdowns.
        - VIEW_COUNTRY : controls to change the value of the model parameters (model dependent) on
        the left panel and results details as well as country-specific information
        on the right panel.

        The app start in the VIEW_GENERAL. The VIEW_COUNTRY can be accessed by cliking on a
        specific country or selecting it with the country dropdown,

        The controls_display is set to 'flex' only for the se4all+shift scenario and is set to
        'none' for the other scenarios (these scenarios do not have variables).
        """
        ctx = dash.callback_context
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            # trigger comes from clicking on a country
            if 'country-input' in prop_id:
                if country_sel:
                    if comp_sel:
                        cur_view.update({'app_view': VIEW_COMPARE})
                    else:
                        cur_view.update({'app_view': VIEW_COUNTRY})
                else:
                    if region_id is None:
                        cur_view.update({'app_view': VIEW_GENERAL})
                    else:
                        cur_view.update({'app_view': VIEW_AGGREGATE})

            # trigger comes from selecting a region
            elif 'region-input' in prop_id:
                if region_id is None:
                    cur_view.update({'app_view': VIEW_GENERAL})
                else:
                    cur_view.update({'app_view': VIEW_AGGREGATE})

            # trigger comes from selection a comparison region/country
            elif 'compare-input' in prop_id:
                if comp_sel:
                    cur_view.update({'app_view': VIEW_COMPARE})
                else:
                    if country_sel:
                        cur_view.update({'app_view': VIEW_COUNTRY})
                    else:
                        if region_id is None:
                            cur_view.update({'app_view': VIEW_GENERAL})
                        else:
                            cur_view.update({'app_view': VIEW_AGGREGATE})
        return cur_view

    @app_handle.callback(
        Output('specific-info-div', 'style'),
        [Input('view-store', 'data')],
        [State('specific-info-div', 'style')]
    )
    def toggle_specific_info_display(cur_view, cur_style):
        """Change the display information between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'block'}

        if cur_view['app_view'] in [VIEW_GENERAL, VIEW_AGGREGATE]:
            cur_style = {}
        elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('maps-div', 'style'),
        [Input('view-store', 'data')],
        [State('maps-div', 'style')]
    )
    def toggle_map_div_display(cur_view, cur_style):
        """Change the display of map between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'block'}

        if cur_view['app_view'] in [VIEW_GENERAL, VIEW_AGGREGATE]:
            cur_style = {}
        elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('right-map-div', 'style'),
        [Input('view-store', 'data')],
        [State('right-map-div', 'style')]
    )
    def toggle_map_div_display(cur_view, cur_style):
        """Change the display of map between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'block'}

        if cur_view['app_view'] in [VIEW_GENERAL, VIEW_AGGREGATE]:
            cur_style = {}
        elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('results-info-div', 'style'),
        [Input('view-store', 'data')],
        [State('results-info-div', 'style')]
    )
    def toggle_results_info_div_display(cur_view, cur_style):
        """Change the display of results-info-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if cur_view['app_view'] == VIEW_COUNTRY:
            cur_style = {}
        elif cur_view['app_view'] in [VIEW_GENERAL, VIEW_AGGREGATE, VIEW_COMPARE]:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('compare-input-div', 'style'),
        [
            Input('view-store', 'data'),
        ],
        [State('compare-input-div', 'style')]
    )
    def toggle_compare_input_div_display(cur_view, cur_style):
        """Change the display of compare-input-div between the app's views."""
        if cur_style is None:
            cur_style = {'visibility': 'hidden'}

        if cur_view['app_view'] in [VIEW_GENERAL, VIEW_AGGREGATE]:
            cur_style.update({'visibility': 'hidden'})
        elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
            cur_style.update({'visibility': 'visible'})
        return cur_style

    @app_handle.callback(
        Output('region-input', 'value'),
        [
            Input('{}-map-btn'.format(region), 'n_clicks')
            for region in MAP_REGIONS
        ],
        [State('region-input', 'value')]
    )
    def update_selected_region(*args):

        region_id = WORLD_ID
        ctx = dash.callback_context
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            region = prop_id.split('-')[0]
            region_id = MAP_REGIONS[region]

        return region_id

    @app_handle.callback(
        Output('country-input', 'value'),
        [
            Input('data-store', 'data'),
            Input('region-input', 'value'),
        ],
        [State('country-input', 'value')]
    )
    def update_selected_country_on_map(cur_data, region_id,  cur_val):

        # return None if the trigger is the region-input
        country_iso = None
        ctx = dash.callback_context
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            if 'data-store' in prop_id:
                country_iso = cur_data.get('selected_country')
                if country_iso is None:
                    country_iso = cur_val
        return country_iso

    @app_handle.callback(
        Output('results-info-div', 'children'),
        [
            Input('scenario-input', 'value'),
            Input('country-input', 'value')
        ],
    )
    def update_results_info_div(scenario, country_iso):

        divs = []
        if scenario in SCENARIOS and country_iso is not None:
            df = LOCAL_SCENARIO_DATA[scenario]
            df = df.loc[df.country_iso == country_iso]
            pop_2017 = np.round(df.pop_2017.values[0] * 1e-6, 2)
            pop_2017_coarse = np.round(df.pop_2017.values[0] * 1e-6, 0)
            pop_2030_coarse = np.round(df.pop_2030.values[0] * 1e-6, 0)
            pop_newly_electrified_2030 = np.round(df.pop_newly_electrified_2030.values[0] * 1e-6, 0)
            electrification_rate = np.round(df.electrification_rate.values[0] * 100, 0)
            name = df.country.values[0]
            image_filename = 'icons/{}.png'.format(country_iso)
            encoded_image = base64.b64encode(open(image_filename, 'rb').read())

            country_desc = """{} Its current population is approximately {:d} million people and for 
2030 it is expected to grow to {:d} million people. We estimated a current 
electrification rate of {:d} % which leads to almost {:d} million people to be newly 
electrified from 2017 until 2030.""".format(
                df.description.values[0],
                int(pop_2017_coarse),
                int(pop_2030_coarse),
                int(electrification_rate),
                int(pop_newly_electrified_2030)
            )

            divs = [
                html.Div(
                    id='results-info-header-div',
                    className='grid-x',
                    children=[
                        html.Img(
                            src='data:image/png;base64,{}'.format(encoded_image.decode()),
                            className='country__info__flag cell medium-4',
                        ),
                        html.H1(
                            className='cell medium-8 align__center',
                            children=name
                        ),
                    ],
                ),
                html.Div(
                    className='country__info__desc',
                    children=country_desc
                ),

                html.Table(
                    [
                        html.Tr(
                            id='country-key-indicators',
                            children=[
                                html.Td('Population (2017)'),
                                html.Td('Electrification rate (2017)'),
                                html.Td('GDP (2017)'),
                                html.Td('Capital'),
                                html.Td('Currency'),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td('{} million people'.format(pop_2017)),
                                html.Td(
                                    '{}'.format(
                                        format_percent(df.electrification_rate.values[0] * 100)
                                    )
                                ),
                                html.Td('{:.2f} Billion USD'.format(df.gdp.values[0])),
                                html.Td(df.capital.values[0]),
                                html.Td(df.currency.values[0]),
                            ]
                        )
                    ]
                ),
            ]

        return divs

    @app_handle.callback(
        Output('aggregate-info-div', 'children'),
        [
            Input('scenario-input', 'value'),
            Input('region-input', 'value')
        ],
    )
    def update_aggregate_info_div(scenario, region_id):

        pop_2017 = ''
        if scenario in SCENARIOS and region_id is not None:
            df = LOCAL_SCENARIO_DATA[scenario]
            pop_2017 = df.pop_2017.sum(axis=0)

        return html.Div('Population (2017) : {}'.format(pop_2017))

    @app_handle.callback(
        Output('country-input', 'options'),
        [Input('region-input', 'value')],
        [
            State('scenario-input', 'value'),

        ]
    )
    def update_country_selection_options(region_id, scenario):
        """List the countries in a given region in alphabetical order."""
        countries_in_region = []
        if scenario is not None:
            # load the data of the scenario
            df = LOCAL_SCENARIO_DATA[scenario]

            if region_id is None:
                region_id = WORLD_ID

            if region_id != WORLD_ID:
                # narrow to the region if the scope is not on the whole world
                df = df.loc[df.region == REGIONS_NDC[region_id]]

            # sort alphabetically by country
            df = df.sort_values('country')
            for idx, row in df.iterrows():
                countries_in_region.append({'label': row['country'], 'value': row['country_iso']})

        return countries_in_region

    @app_handle.callback(
        Output('data-store', 'data'),
        [Input('{}-map'.format(region), 'clickData') for region in MAP_REGIONS]+
        [Input('static-url-store', 'data')],
        [State('data-store', 'data')]
    )
    def update_data_store(*args):
        cur_data = args[-1]
        url_data = args[-2]
        if 'country_iso' in url_data:
            cur_data.update({'selected_country': url_data['country_iso']})
        for clicked_data in args[:-3]:
            if clicked_data is not None:
                country_iso = clicked_data['points'][0]['location']
                cur_data.update({'selected_country': country_iso})
        return cur_data

    @app_handle.callback(
        Output('general-info-div', 'children'),
        [Input('scenario-input', 'value')]
    )
    def update_scenario_description(scenario):
        return SCENARIOS_DESCRIPTIONS[scenario]

    @app_handle.callback(
        Output('specific-info-div', 'children'),
        [Input('scenario-input', 'value')]
    )
    def update_scenario_specific_description(scenario):
        return WHAT_CAN_YOU_DO_DESCRIPTIONS[scenario]


if __name__ == '__main__':
    app.run_server(debug=True)
