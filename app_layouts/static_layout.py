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
    BARPLOT_YAXIS_OPT
)

URL_PATHNAME = 'static'


def extract_centroids(reg):
    """Load the longitude and latitude of countries per region."""
    if not isinstance(reg, list):
        reg = [reg]
    centroids = pd.read_csv('data/centroid.csv')
    return centroids.loc[centroids.region.isin(reg)].copy()


WORLD_ID = 'WD'
REGIONS_GPD = dict(WD='World', SA='South America', AF='Africa', AS='Asia')

REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')

VIEW_GENERAL = 'general'
VIEW_COUNTRY = 'specific'
VIEW_AGGREGATE = 'aggregate'
VIEW_COMPARE = 'compare'

# A dict with the data for each scenario in json format
SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce, MIN_TIER_LEVEL).to_json() for sce in SCENARIOS
}
SCENARIOS_DATA.update(
    {reg: extract_centroids(REGIONS_NDC[reg]).to_json() for reg in REGIONS_NDC}
)


# list all region and countries to sompare with a single country
COMPARE_OPTIONS = []
for _, r in pd.read_json(SCENARIOS_DATA[BAU_SCENARIO]).sort_values('country').iterrows():
    COMPARE_OPTIONS.append({'label': r['country'], 'value': r['country_iso']})
COMPARE_OPTIONS = [{'label': v, 'value': k} for k, v in REGIONS_GPD.items()] + COMPARE_OPTIONS

# colors for hightlight of comparison
COLOR_BETTER = '#218380'
COLOR_WORSE = '#8F2D56'


def country_hover_text(input_df):
    """Format the text displayed by the hover."""
    df = input_df.copy()
    # share of the population with electricity in 2030 (per electrification option)
    df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0)

    return df.country + '<br>' \
           + '2017 <br>' \
           + '  Pop : ' + df.pop_2017.div(1e6).map('{:.1f} MIO'.format) + '<br>' \
           + '  Household electric consumption: ' + '<br>' \
           + '  ' + df.hh_yearly_electricity_consumption.map('{:.1f} kWh/year'.format) + '<br>' \
           + '  Grid share: ' + df.pop_grid_share.map('{:.1%}'.format) + '<br>' \
           + '  MG: ' + df.pop_mg_share.map('{:.1%}'.format) + '<br>' \
           + '  SHS: ' + df.pop_shs_share.map('{:.1%}'.format) + '<br>' \
           + '2030 <br>' \
           + '  Est Pop (2030): ' + df.pop_2030.div(1e6).map('{:.1f} MIO'.format) + '<br>' \
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

layout = go.Layout(
    # plot_bgcolor='red',
    paper_bgcolor=APP_BG_COLOR,
    #autosize=True,
    height=500,
    margin=dict(
        l=2,
        r=2,
        b=2,
        t=2
    ),
    legend=dict(orientation='h', xanchor='center', x=0.5),
    geo=go.layout.Geo(
        bgcolor=APP_BG_COLOR,
        scope='world',
        showlakes=True,
        showcountries=True,
        lakecolor='rgb(255, 255, 255)',
        projection=dict(type='orthographic'),
    ),
    # south america
    geo2=go.layout.Geo(
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
    # asia
    geo3=go.layout.Geo(
        bgcolor=APP_BG_COLOR,
        scope='world',
        showlakes=True,
        showcountries=True,
        lakecolor='rgb(255, 255, 255)',
        projection=dict(type='equirectangular'),
        lonaxis=dict(range=[25, -170]),
        lataxis=dict(range=[-15, 90]),
        framewidth=0,
    )
)

fig_map = go.Figure(data=map_data, layout=layout)


layout = html.Div(
    id='main-div',
    children=[
        dcc.Store(
            id='data-store',
            storage_type='session',
            data=SCENARIOS_DATA.copy()
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
                        id='meain-head-content',
                        className='grid-x grid-padding-x',
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
                                        id='scenario-div',
                                        className='grid-x',
                                        children=[
                                            html.Div(
                                                id='scenario-label',
                                                className='cell medium-3',
                                                children='Explore a scenario:'
                                            ),
                                            html.Div(
                                                id='scenario-input-div',
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
                                                    value=BAU_SCENARIO,
                                                )
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        id='region-input-div',
                                        className='grid-x',
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
                                        className='grid-x',
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
                                                    value=None,
                                                    multi=False
                                                )
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id='compare-input-div',
                                        className='grid-x',
                                        style={'display': 'none'},
                                        children=[
                                            html.Div(
                                                id='country-comp-label',
                                                className='cell medium-4',
                                                children='Compare with:'
                                            ),
                                            html.Div(
                                                id='compare-input-wrapper',
                                                className='cell medium-8',
                                                children=dcc.Dropdown(
                                                    id='compare-input',
                                                    options=COMPARE_OPTIONS,
                                                    value=None,
                                                    multi=False
                                                )
                                            ),

                                        ],

                                    ),
                                ]
                            ),
                            html.Div(
                                id='left-map-div',
                                className='cell medium-6',
                                children=dcc.Graph(
                                    id='map',
                                    figure=fig_map,
                                )
                            ),
                            html.Div(
                                id='right-map-div',
                                className='cell medium-6',
                                children=[
                                    html.P(
                                        'Hover over the map to view country specific information.'
                                    ),
                                    html.P(
                                        'For more information, click on the country or select it '
                                        'in the menu above.'
                                    ),
                                    html.P(
                                        'To view the results aggregated over a region, please '
                                        'select a region in the menu above'
                                    )
                                ]
                            ),
                        ]
                    ),
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


def country_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format('country', result_category)

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('country-input', 'value'),
            Input('{}-barplot-yaxis-input'.format(id_name), 'value')
        ],
        [
            State('data-store', 'data'),
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def update_barplot(country_sel, y_sel, cur_data, fig):

        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        country_iso = country_sel
        if country_iso is not None:
            x_vals = [SCENARIOS_DICT[sce] for sce in SCENARIOS]
            y_vals = []
            for sce_id, sce in enumerate(SCENARIOS):

                df = pd.read_json(cur_data[sce])
                # narrow to the country's results
                df = df.loc[df.country_iso == country_iso]
                # extract the results formatted with good units
                results_data = prepare_results_tables(df, sce, result_category)
                # select the row corresponding to the barplot y axis choice
                y_vals.append(results_data[idx_y])

            y_vals = np.vstack(y_vals)

            for j, opt in enumerate(BARPLOT_YAXIS_OPT):
                fig['data'][j].update({'x': x_vals})
                fig['data'][j].update({'y': y_vals[:, j]})

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
        ],
        [State('data-store', 'data')]
    )
    def update_table(
            country_iso,
            scenario,
            cur_data,
    ):
        """Display information and study's results for a country."""

        result_cat = result_category

        answer_table = []
        if country_iso is not None:
            if scenario in SCENARIOS:

                df = pd.read_json(cur_data[scenario])
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


def aggregate_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(RES_AGGREGATE, result_category)

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('region-input', 'value'),
            Input('{}-barplot-yaxis-input'.format(id_name), 'value')
        ],
        [
            State('data-store', 'data'),
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def update_barplot(region_id, y_sel, cur_data, fig):

        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        if region_id is not None:
            x_vals = [SCENARIOS_DICT[sce] for sce in SCENARIOS]
            y_vals = []
            for sce_id, sce in enumerate(SCENARIOS):
                df = pd.read_json(cur_data[sce])

                if region_id != WORLD_ID:
                    # narrow to the region if the scope is not on the whole world
                    df = df.loc[df.region == REGIONS_NDC[region_id]]

                # aggregate the results
                df = df[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

                # compute the percentage of population with electricity access
                results_data = prepare_results_tables(df, sce, result_category)

                y_vals.append(results_data[idx_y])

            y_vals = np.vstack(y_vals)

            for j, opt in enumerate(BARPLOT_YAXIS_OPT):
                fig['data'][j].update({'x': x_vals})
                fig['data'][j].update({'y': y_vals[:, j]})
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
        [State('data-store', 'data')]
    )
    def update_table(
            region_id,
            scenario,
            cur_data,
    ):
        """Display information and study's results for a country."""

        result_cat = result_category

        answer_table = []
        if region_id is not None:
            if scenario in SCENARIOS:

                df = pd.read_json(cur_data[scenario])
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


def compare_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = '{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('country-input', 'value'),
            Input('compare-input', 'value'),
            Input('scenario-input', 'value'),
            Input('{}-barplot-yaxis-input'.format(id_name), 'value')
        ],
        [
            State('data-store', 'data'),
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def update_barplot(country_sel, comp_sel, scenario, y_sel, cur_data, fig):
        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        if country_sel is not None and comp_sel is not None:
            comp_name = comp_sel
            df = pd.read_json(cur_data[scenario])
            df_comp = df.copy()
            df_ref = df.loc[df.country_iso == country_sel]
            if comp_sel in REGIONS_NDC:
                # compare the reference country to a region
                if comp_sel != WORLD_ID:
                    df_comp = df_comp.loc[df_comp.region == REGIONS_NDC[comp_sel]]
                df_comp = df_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)
                comp_name = REGIONS_GPD[comp_sel]
            else:
                # compare the reference country to a country
                df_comp = df_comp.loc[df_comp.country_iso == comp_sel]
                comp_name = df_comp.country.values[0]

            ref_results_data = prepare_results_tables(df_ref, scenario, result_category)
            comp_results_data = prepare_results_tables(df_comp, scenario, result_category)

            x = [opt.upper() for opt in ELECTRIFICATION_OPTIONS] + [NO_ACCESS]
            y_ref = ref_results_data[idx_y]
            y_comp = comp_results_data[idx_y]

            fs = 12

            fig.update(
                {'data': [
                    go.Bar(
                        x=x,
                        y=y_ref,
                        text=[country_sel for i in range(4)],
                        name=df_ref.country.values[0],
                        insidetextfont={'size': fs},
                        textposition='auto',
                        marker=dict(
                            color=list(BARPLOT_ELECTRIFICATION_COLORS.values())
                        ),
                        hoverinfo='y+text'
                    ),
                    go.Bar(
                        x=x,
                        y=y_comp,
                        text=[comp_name for i in range(4)],
                        name=comp_name,
                        insidetextfont={'size': fs},
                        textposition='auto',
                        marker=dict(
                            color=['#a062d0', '#9ac1e5', '#f3a672', '#cccccc']
                        ),
                        hoverinfo='y+text'
                    ),
                ]
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
        [State('data-store', 'data')]
    )
    def update_table(country_iso, comp_sel, scenario, cur_data):
        """Display information and study's results comparison between countries."""
        answer_table = []

        result_cat = result_category

        # extract the data from the selected scenario if a country was selected
        if country_iso is not None and comp_sel is not None:
            if scenario in SCENARIOS:
                df = pd.read_json(cur_data[scenario])
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


def compare_table_styling_callback(app_handle, result_category):

    id_name = '{}-{}'.format(RES_COMPARE, result_category)

    result_cat = result_category

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'style_data_conditional'),
        [Input('{}-results-table'.format(id_name), 'data')],
        [
            State('{}-results-table'.format(id_name), 'style_data_conditional'),
            State('compare-input', 'value'),
            State('country-input', 'value'),
            State('scenario-input', 'value')
        ]
    )
    def update_table_styling(cur_data, cur_style, comp_sel, country_iso, scenario):

        if comp_sel is not None and country_iso is not None:
            data = pd.DataFrame.from_dict(cur_data)

            col_ref = TABLE_COLUMNS_ID[result_cat][1:]
            col_comp = ['comp_{}'.format(col) for col in TABLE_COLUMNS_ID[result_cat][1:]]
            data = data[col_ref + col_comp].applymap(
                lambda x: 0 if x == '' else float(x.replace(',', '').replace('%', '')))
            ref = data[col_ref]
            comp = data[col_comp]

            compare_results_styling = []
            for j, col in enumerate(col_ref):
                for i in range(len(ref.index)):
                    apply_condition = True
                    if ref.iloc[i, j] > comp.iloc[i, j]:
                        color = COLOR_BETTER
                        font = 'bold'
                        if result_category == GHG_RES:
                            if scenario == BAU_SCENARIO or np.mod(i, 2) == 0:
                                color = COLOR_WORSE
                                font = 'normal'
                    elif ref.iloc[i, j] < comp.iloc[i, j]:
                        color = COLOR_WORSE
                        font = 'normal'
                        if result_category == GHG_RES:
                            if scenario == BAU_SCENARIO or np.mod(i, 2) == 0:
                                color = COLOR_BETTER
                                font = 'bold'
                    else:
                        apply_condition = False

                    if apply_condition:
                        compare_results_styling.append(
                            {
                                "if": {"column_id": col, "row_index": i},
                                'color': color,
                                'fontWeight': font
                            }
                        )
                    cur_style = TABLES_LABEL_STYLING + compare_results_styling
        return cur_style

    update_table_styling.__name__ = 'update_%s_table_styling' % id_name
    return update_table_styling


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
        [State('data-store', 'data')]
    )
    def update_title(input_trigger, scenario, cur_data):

        answer = 'Results'
        if scenario in SCENARIOS and input_trigger is not None:
            if result_type == RES_COUNTRY:
                df = pd.read_json(cur_data[scenario])
                answer = '{}: '.format(df.loc[df.country_iso == input_trigger].country.values[0])
            elif result_type == RES_AGGREGATE:
                answer = '{}: Aggregated '.format(
                    REGIONS_GPD[input_trigger]
                )
        return '{}{}'.format(answer, description)

    update_title.__name__ = 'update_%s_title' % id_name
    return update_title


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
        [State('data-store', 'data')]
    )
    def update_title(country_iso, comp_sel, scenario, cur_data):

        answer = 'Results'
        if scenario in SCENARIOS and country_iso is not None and comp_sel is not None:
            df = pd.read_json(cur_data[scenario])
            if comp_sel in REGIONS_NDC:
                comp_name = REGIONS_GPD[comp_sel]
            else:
                comp_name = df.loc[df.country_iso == comp_sel].country.values[0]
            answer = 'Comparison of {}'.format(
                description.format(
                    'between {} and {}'.format(
                        df.loc[df.country_iso == country_iso].country.values[0],
                        comp_name
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

        answer='Detailed results'
        if scenario in SCENARIOS and input_trigger is not None:
            answer = 'Detailed Results for {} ({}) Scenario'.format(
                SCENARIOS_NAMES[scenario],
                SCENARIOS_DICT[scenario]
            )

        return answer

    update_title.__name__ = 'update_%s_title' % id_name
    return update_title


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
                cur_style.update({'display': 'block'})
            elif cur_view['app_view'] in [VIEW_GENERAL,VIEW_AGGREGATE, VIEW_COMPARE]:
                cur_style.update({'display': 'none'})
        elif result_type == RES_AGGREGATE:
            if cur_view['app_view'] == VIEW_AGGREGATE:
                cur_style.update({'display': 'block'})
            elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
                cur_style.update({'display': 'none'})
        elif result_type == RES_COMPARE:
            if cur_view['app_view'] == VIEW_COMPARE:
                cur_style.update({'display': 'block'})
            elif cur_view['app_view'] in [VIEW_GENERAL, VIEW_COUNTRY, VIEW_AGGREGATE]:
                cur_style.update({'display': 'none'})

        return cur_style

    toggle_results_div_display.__name__ = 'toggle_%s_display' % id_name
    return toggle_results_div_display


def callbacks(app_handle):

    # build callbacks automatically for various categories
    for res_cat in [POP_RES, INVEST_RES, GHG_RES]:

        country_barplot_callback(app_handle, res_cat)
        country_table_callback(app_handle, res_cat)

        aggregate_barplot_callback(app_handle, res_cat)
        aggregate_table_callback(app_handle, res_cat)

        compare_barplot_callback(app_handle, res_cat)
        compare_table_callback(app_handle, res_cat)
        compare_table_styling_callback(app_handle, res_cat)
        compare_table_columns_title_callback(app_handle, res_cat)

        for res_type in [RES_COUNTRY, RES_AGGREGATE]:
            country_aggregate_title_callback(app_handle, res_type, res_cat)
        compare_title_callback(app_handle, res_cat)

        for res_type in [RES_COUNTRY, RES_AGGREGATE, RES_COMPARE]:
            toggle_results_div_callback(app_handle, res_type, res_cat)
            table_title_callback(app_handle, res_type, res_cat)

    for res_type in [RES_COUNTRY, RES_AGGREGATE, RES_COMPARE]:
        ghg_dropdown_options_callback(app_handle, res_type)

    @app_handle.callback(
        Output('map', 'figure'),
        [
            Input('region-input', 'value'),
            Input('scenario-input', 'value'),
        ],
        [
            State('map', 'figure'),
            State('data-store', 'data')
        ]
    )
    def update_map(region_id, scenario, fig, cur_data):
        """Plot color map of the percentage of people with a given electrification option."""

        # load the data of the scenario
        df = pd.read_json(cur_data[scenario])

        if region_id is None:
            region_id = WORLD_ID

        centroid = pd.read_json(cur_data[region_id])

        if region_id != WORLD_ID:
            # narrow to the region if the scope is not on the whole world
            df = df.loc[df.region == REGIONS_NDC[region_id]]

        if region_id == 'SA':
            region_name = REGIONS_GPD[WORLD_ID]
            geo = 'geo2'
        elif region_id == 'AS':
            region_name = REGIONS_GPD[region_id]
            geo = 'geo3'
        else:
            region_name = REGIONS_GPD[region_id]
            geo = 'geo'

        fig['data'][0].update(
            {
                'locations': df['country_iso'],
                'z': np.ones(len(df.index)),
                'text': country_hover_text(df),
                'geo': geo,
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
                if j == n-1 and z.iloc[i, j] == 0:
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
                            geo=geo
                        )
                    )
            show_legend = False
            i = i + 1

        fig['data'][1:] = points

        fig['layout']['geo'].update({'scope': region_name.lower()})
        return fig

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
        Output('left-map-div', 'style'),
        [Input('view-store', 'data')],
        [State('left-map-div', 'style')]
    )
    def toggle_map_div_display(cur_view, cur_style):
        """Change the display of map between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'block'}

        if cur_view['app_view'] in [VIEW_GENERAL, VIEW_AGGREGATE]:
            cur_style.update({'display': 'block'})
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
            cur_style.update({'display': 'block'})
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
            cur_style.update({'display': 'block'})
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
            cur_style = {'display': 'none'}

        if cur_view['app_view'] in [VIEW_GENERAL, VIEW_AGGREGATE]:
            cur_style.update({'display': 'none'})
        elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
            cur_style.update({'display': 'block'})
        return cur_style

    @app_handle.callback(
        Output('country-input', 'value'),
        [
            Input('data-store', 'data'),
            Input('region-input', 'value'),
        ],
        [State('country-input', 'value')]
    )
    def update_selected_country_on_map(cur_data, region_id, cur_val):

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
        [State('data-store', 'data')]
    )
    def update_results_info_div(scenario, country_iso, cur_data):

        divs = []
        nigeria_desc = ''
        nigeria_info = []
        if scenario in SCENARIOS and country_iso is not None:
            df = pd.read_json(cur_data[scenario])
            df = df.loc[df.country_iso == country_iso]
            pop_2017 = np.round(df.pop_2017.values[0] * 1e-6, 2)
            name = df.country.values[0]
            image_filename = 'icons/{}.png'.format(country_iso)
            encoded_image = base64.b64encode(open(image_filename, 'rb').read())

            if country_iso == 'NGA':
                nigeria_desc = 'Nigeria is a lower-middle income country located in West-Africa. Its current population is approximately 190 million people and for 2030 it is expected to grow to 264 million people. We estimated a current electrification rate of  63 % which leads to almost 100 people to be newly electrified until 2030.'

                nigeria_info = [
                    html.P(
                        'Capital : Abuja'
                    ),
                    html.P(
                        'Currency : Naira'
                    )
                ]

            divs = [
                html.Div(
                    id='results-info-header-div',
                    className='grid-x',
                    children=[
                        html.Img(
                            src='data:image/png;base64,{}'.format(encoded_image.decode()),
                            className='country__info__flag cell medium-6',
                            style={'width': '30%'}
                        ),
                        html.H1(
                            className='cell medium-6',
                            children=name
                        ),
                    ],
                ),
                html.Table(
                    [
                        html.Tr(
                            [
                                html.Td('Population (2017)'),
                                html.Td('Electrification rate (2017)'),
                                html.Td('GDP (2017)'),
                                html.Td('Capital'),
                                html.Td('Currency'),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td('16.67'),
                                html.Td('0.45'),
                                html.Td('1'),
                                html.Td('-'),
                                html.Td('EUR'),
                            ]
                        )
                    ]
                ),
                html.Div(children=nigeria_desc),
                html.H4('Key indicators:'),
                html.P(
                    'Population (2017) : {} million people'.format(pop_2017)
                ),
                html.P(
                    'Electrification rate (2017) : {}'.format(
                        format_percent(df.electrification_rate.values[0] * 100)
                    )
                ),
                html.P(
                    'GDP (2017) : {} Billion USD'.format(df.gdp_per_capita.values[0])
                ),

            ]

        return divs + nigeria_info

    @app_handle.callback(
        Output('aggregate-info-div', 'children'),
        [
            Input('scenario-input', 'value'),
            Input('region-input', 'value')
        ],
        [State('data-store', 'data')]
    )
    def update_aggregate_info_div(scenario, region_id, cur_data):

        pop_2017 = ''
        if scenario in SCENARIOS and region_id is not None:
            df = pd.read_json(cur_data[scenario])
            pop_2017 = df.pop_2017.sum(axis=0)

        return html.Div('Population (2017) : {}'.format(pop_2017))

    @app_handle.callback(
        Output('country-input', 'options'),
        [Input('region-input', 'value')],
        [
            State('scenario-input', 'value'),
            State('data-store', 'data')
        ]
    )
    def update_country_selection_options(region_id, scenario, cur_data):
        """List the countries in a given region in alphabetical order."""
        countries_in_region = []
        if scenario is not None:
            # load the data of the scenario
            df = pd.read_json(cur_data[scenario])

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
        [Input('map', 'clickData')],
        [State('data-store', 'data')]
    )
    def update_data_store(clicked_data, cur_data):
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


if __name__ == '__main__':
    app.run_server(debug=True)
