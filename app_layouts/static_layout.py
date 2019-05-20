import base64
import os
import numpy as np
import pandas as pd
import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from app_main import app

from data.data_preparation import (
    MIN_TIER_LEVEL,
    SCENARIOS,
    BAU_SCENARIO,
    SE4ALL_SCENARIO,
    SE4ALL_FLEX_SCENARIO,
    PROG_SCENARIO,
    SCENARIOS_DICT,
    SCENARIOS_DESCRIPTIONS,
    ELECTRIFICATION_OPTIONS,
    POP_GET,
    HH_GET,
    HH_CAP,
    HH_SCN2,
    INVEST,
    INVEST_CAP,
    GHG,
    GHG_CAP,
    EXO_RESULTS,
    BASIC_ROWS,
    BASIC_COLUMNS_ID,
    GHG_COLUMNS_ID,
    compute_ndc_results_from_raw_data,
)

from .app_components import (
    results_div,
    scenario_div,
    general_info_div,
)

URL_PATHNAME = 'static'


def extract_centroids(reg):
    """Load the longitude and latitude of countries per region."""
    if not isinstance(reg, list):
        reg = [reg]
    centroids = pd.read_csv('data/centroid.csv')
    return centroids.loc[centroids.region.isin(reg)].copy()


def add_comma(val):
    if np.isnan(val):
        answer = ''
    else:
        answer = "{:,}".format(np.round(val, 0))
        answer = answer.split('.')[0]
    return answer


WORLD_ID = 'WD'
REGIONS_GPD = dict(WD='World', SA='South America', AF='Africa', AS='Asia')

REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')

VIEW_GENERAL = 'general'
VIEW_COUNTRY = 'specific'

# A dict with the data for each scenario in json format
SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce, MIN_TIER_LEVEL).to_json() for sce in SCENARIOS
}
SCENARIOS_DATA.update(
    {reg: extract_centroids(REGIONS_NDC[reg]).to_json() for reg in REGIONS_NDC}
)


logos = [
    base64.b64encode(open('logos/{}'.format(fn), 'rb').read())
    for fn in os.listdir('logos') if fn.endswith('.png')
]


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
data = [
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
    paper_bgcolor='#EBF2FA',
    geo=go.layout.Geo(
        scope='world',
        showlakes=True,
        showcountries=True,
        lakecolor='rgb(255, 255, 255)',
        projection=dict(type='equirectangular'),
    ),
    geo2=go.layout.Geo(
        scope='world',
        showlakes=True,
        showcountries=True,
        lakecolor='rgb(255, 255, 255)',
        projection=dict(type='equirectangular'),
        lonaxis=dict(range=[-95, -30.0]),
        lataxis=dict(range=[-60, 30]),
        framewidth=0,
    )
)

fig_map = go.Figure(data=data, layout=layout)


layout = html.Div(
    id='main-div',
    children=[
        html.Div(
            id='app-title',
            className='title',
            children='Visualization of New Electrification Scenarios by 2030 and the'
                     ' Relevance of Off-Grid Components in the NDCs'
        ),
        html.Div(
            id='app-div',
            className='app',
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
                    id='left-panel-div',
                    className='app__container',
                    children=[
                        html.Div(
                            id='scenario-div',
                            className='app__options',
                            children=scenario_div(BAU_SCENARIO)
                        ),
                        html.Div(
                            id='general-info-div',
                            className='app__info',
                            children=general_info_div()
                        ),
                        html.Div(
                            id='aggregate-div',
                            className='app__aggregate',
                            children=results_div(aggregate=True),
                            style={'display': 'none'}
                        ),
                        html.Div(
                            id='results-div',
                            className='app__results',
                            children=results_div(),
                            style={'display': 'none'}
                        ),
                    ]
                ),
                html.Div(
                    id='right-panel-div',
                    className='app__container',
                    children=[
                        html.Div(
                            id='header-div',
                            className='app__header',
                            children=[
                                html.Div(
                                    id='region-label',
                                    className='app__input__label',
                                    children='Region:'
                                ),
                                html.Div(
                                    id='region-input-div',
                                    className='app__dropdown',
                                    title='region selection description',
                                    children=dcc.Dropdown(
                                        id='region-input',
                                        className='app__input__dropdown__map',
                                        options=[
                                            {'label': v, 'value': k}
                                            for k, v in REGIONS_GPD.items()
                                        ],
                                        value=WORLD_ID
                                    )
                                ),
                                html.Div(
                                    id='logo-div',
                                    children=[
                                        html.Img(
                                            src='data:image/png;base64,{}'.format(logo.decode()),
                                            className='app__logo',
                                            # style={'height': '5vh', 'padding': '10px'}
                                        )
                                        for logo in logos
                                    ]
                                ),
                            ]
                        ),
                        html.Div(
                            id='country-input-div',
                            className='app__dropdown',
                            title='country selection description',
                            children=dcc.Dropdown(
                                id='country-input',
                                className='app__input__dropdown__country',
                                options=[],
                                value=None,
                                multi=False
                            )
                        ),
                        html.Div(
                            id='results-info-div',
                            className='results__info',
                            children=''
                        ),
                        html.Div(
                            id='map-div',
                            className='app__map',
                            title='Hover over a country to display information.\n'
                                  + 'Click on it to access detailed report.',
                            children=dcc.Graph(
                                id='map',
                                figure=fig_map,
                                style={'width': '100vh', 'height': '100vh'},
                                config={
                                    'displayModeBar': False,
                                    'autosizable': True,
                                }
                            ),
                        ),
                    ]

                )
            ],
        )
    ]
)


def callbacks(app_handle):
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

        centroid = pd.read_json(cur_data[region_id])

        if region_id != WORLD_ID:
            # narrow to the region if the scope is not on the whole world
            df = df.loc[df.region == REGIONS_NDC[region_id]]

        if region_id == 'SA':
            region_name = REGIONS_GPD[WORLD_ID]
            geo = 'geo2'
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
            z['no_ec'] = 1 - z.sum(axis=1)
            n = 4
            labels = ELECTRIFICATION_OPTIONS.copy() + ['No electricity']
        else:
            z = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0).round(3)
            n = 3
            labels = ELECTRIFICATION_OPTIONS.copy()
        colors = ['blue', 'orange', 'green', 'red']
        for idx, c in centroid.iterrows():
            for j in range(n):
                points.append(
                    go.Scattergeo(
                        lon=[c['Longitude']],
                        lat=[c['Latitude']],
                        hoverinfo='skip',
                        marker=go.scattergeo.Marker(
                            size=z.iloc[i, j:n].sum() * 25,
                            color=colors[j],
                            line=go.scattergeo.marker.Line(width=0)
                        ),
                        showlegend=False,
                        geo=geo
                    )
                )
            i = i + 1

        fig['data'][1:] = points

        fig['layout']['geo'].update({'scope': region_name.lower()})
        return fig

    @app_handle.callback(
        Output('country-barplot', 'figure'),
        [Input('country-input', 'value')],
        [
            State('data-store', 'data'),
            State('country-barplot', 'figure')
        ]
    )
    def update_country_barplot(country_sel, cur_data, fig):
        """update the barplot for every scenario"""

        country_iso = country_sel
        if country_iso is not None:
            for sce_id, sce in enumerate(SCENARIOS):
                df = pd.read_json(cur_data[sce])
                # narrow to the country's results
                df = df.loc[df.country_iso == country_iso]
                # compute the percentage of population with electricity access
                y = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0) * 100

                y = np.append(y, 0)
                if sce == BAU_SCENARIO:
                    y[3] = 100 - y.sum()

                fig['data'][sce_id].update({'y': y})
        return fig

    @app_handle.callback(
        Output('aggregate-barplot', 'figure'),
        [Input('region-input', 'value')],
        [
            State('data-store', 'data'),
            State('aggregate-barplot', 'figure')
        ]
    )
    def update_aggregate_barplot(region_id, cur_data, fig):
        """update the barplot for every scenario"""
        if region_id is not None:
            for sce_id, sce in enumerate(SCENARIOS):
                df = pd.read_json(cur_data[sce])

                if region_id != WORLD_ID:
                    # narrow to the region if the scope is not on the whole world
                    df = df.loc[df.region == REGIONS_NDC[region_id]]

                # aggregate the results
                df = df[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

                # compute the percentage of population with electricity access
                y = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0) * 100

                y = np.append(y, 0)
                if sce == BAU_SCENARIO:
                    y[3] = 100 - y.sum()

                fig['data'][sce_id].update({'y': y})
        return fig

    @app_handle.callback(
        Output('view-store', 'data'),
        [
            Input('scenario-input', 'value'),
            Input('region-input', 'value'),
            Input('country-input', 'value')
        ],
        [State('view-store', 'data')]
    )
    def update_view(scenario, region_id, country_sel, cur_view):
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
                    cur_view.update({'app_view': VIEW_COUNTRY})
                else:
                    cur_view.update({'app_view': VIEW_GENERAL})

            # trigger comes from selecting a region
            elif 'region-input' in prop_id:
                cur_view.update({'app_view': VIEW_GENERAL})

        if scenario == SE4ALL_FLEX_SCENARIO:
            cur_view.update({'controls_display': 'flex'})
        else:
            cur_view.update({'controls_display': 'none'})
        return cur_view

    @app_handle.callback(
        Output('map-div', 'style'),
        [Input('view-store', 'data')],
        [State('map-div', 'style')]
    )
    def toggle_map_div_display(cur_view, cur_style):
        """Change the display of map-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'flex'}

        if cur_view['app_view'] == VIEW_GENERAL:
            cur_style.update({'display': 'flex'})
        elif cur_view['app_view'] == VIEW_COUNTRY:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('results-div', 'style'),
        [Input('view-store', 'data')],
        [State('results-div', 'style')]
    )
    def toggle_results_div_display(cur_view, cur_style):
        """Change the display of results-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if cur_view['app_view'] == VIEW_GENERAL:
            cur_style.update({'display': 'none'})
        elif cur_view['app_view'] == VIEW_COUNTRY:
            cur_style.update({'display': 'flex'})
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

        if cur_view['app_view'] == VIEW_GENERAL:
            cur_style.update({'display': 'none'})
        elif cur_view['app_view'] == VIEW_COUNTRY:
            cur_style.update({'display': 'flex'})
        return cur_style

    @app_handle.callback(
        Output('general-info-div', 'style'),
        [
            Input('view-store', 'data'),
            Input('aggregate-input', 'values'),
        ],
        [State('general-info-div', 'style')]
    )
    def toggle_general_info_div_display(cur_view, aggregate, cur_style):
        """Change the display of general-info-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if cur_view['app_view'] == VIEW_GENERAL:
            if aggregate:
                cur_style.update({'display': 'none'})
            else:
                cur_style.update({'display': 'flex'})
        elif cur_view['app_view'] == VIEW_COUNTRY:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('aggregate-div', 'style'),
        [
            Input('view-store', 'data'),
            Input('aggregate-input', 'values'),
        ],
        [State('aggregate-div', 'style')]
    )
    def toggle_aggregate_div_display(cur_view, aggregate, cur_style):
        """Change the display of aggregate-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if cur_view['app_view'] == VIEW_GENERAL:
            if aggregate:
                cur_style.update({'display': 'flex'})
            else:
                cur_style.update({'display': 'none'})
        elif cur_view['app_view'] == VIEW_COUNTRY:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('country-basic-results-table', 'data'),
        [
            Input('country-input', 'value'),
            Input('scenario-input', 'value'),
        ],
        [State('data-store', 'data')]
    )
    def update_country_basic_results_table(
            country_sel,
            scenario,
            cur_data,
    ):
        """Display information and study's results for a country."""
        answer_table = []
        country_iso = country_sel
        # in case of country_iso is a list of one element
        if np.shape(country_iso) and len(country_iso) == 1:
            country_iso = country_iso[0]

        # extract the data from the selected scenario if a country was selected
        if country_iso is not None:
            if scenario in SCENARIOS:

                df = pd.read_json(cur_data[scenario])
                df = df.loc[df.country_iso == country_iso]

                # compute the percentage of population with electricity access
                df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0).round(3)
                # gather the values of the results to display in the table
                pop_res = np.squeeze(df[POP_GET].values * 100).round(1)
                hh_res = np.squeeze(df[HH_GET].values).round(0)
                cap_res = np.squeeze(df[HH_CAP].values * 1e-3).round(0)
                cap2_res = np.squeeze(df[HH_SCN2].values * 1e-3).round(0)
                invest_res = np.squeeze(df[INVEST].values).round(0)
                invest_res = np.append(np.NaN, invest_res)
                invest2_res = np.squeeze(df[INVEST_CAP].values).round(0)
                invest2_res = np.append(np.NaN, invest2_res)
                basic_results_data = np.vstack(
                    [pop_res, hh_res, cap_res, cap2_res, invest_res, invest2_res]
                )

                total = np.nansum(basic_results_data, axis=1)

                # prepare a DataFrame
                basic_results_data = pd.DataFrame(
                    data=basic_results_data,
                    columns=ELECTRIFICATION_OPTIONS
                )
                # sums of the rows
                basic_results_data['total'] = pd.Series(total)
                # label of the table rows
                basic_results_data['labels'] = pd.Series(BASIC_ROWS)
                basic_results_data.iloc[1:, 0:4] = basic_results_data.iloc[1:, 0:4].applymap(
                    add_comma
                )
                answer_table = basic_results_data[BASIC_COLUMNS_ID].to_dict('records')

        return answer_table

    @app_handle.callback(
        Output('country-ghg-results-table', 'data'),
        [
            Input('country-input', 'value'),
            Input('scenario-input', 'value'),
        ],
        [State('data-store', 'data')]
    )
    def update_country_ghg_results_table(
            country_sel,
            scenario,
            cur_data,
    ):
        """Display information and study's results for a country."""
        answer_table = []
        df_bau = None
        country_iso = country_sel
        # in case of country_iso is a list of one element
        if np.shape(country_iso) and len(country_iso) == 1:
            country_iso = country_iso[0]

        # extract the data from the selected scenario if a country was selected
        if country_iso is not None:
            if scenario in SCENARIOS:

                df = pd.read_json(cur_data[scenario])
                df = df.loc[df.country_iso == country_iso]

                if scenario in [SE4ALL_FLEX_SCENARIO, SE4ALL_SCENARIO, PROG_SCENARIO]:
                    # to compare greenhouse gas emissions with BaU scenario
                    df_bau = pd.read_json(cur_data[BAU_SCENARIO])
                    df_bau = df_bau.loc[df_bau.country_iso == country_iso]

                if df_bau is None:
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

                # gather the values of the results to display in the table
                ghg_res = np.squeeze(df[GHG].values).round(0)
                ghg2_res = np.squeeze(df[GHG_CAP].values).round(0)
                if df_bau is not None:
                    ghg_comp_res = ghg_res - np.squeeze(df_bau[GHG].values).round(0)
                    ghg2_comp_res = ghg2_res - np.squeeze(df_bau[GHG_CAP].values).round(0)
                    ghg_results_data = np.vstack([ghg_res, ghg_comp_res, ghg2_res, ghg2_comp_res])
                else:
                    ghg_results_data = np.vstack([ghg_res, ghg2_res])

                total = np.nansum(ghg_results_data, axis=1)

                # prepare a DataFrame
                ghg_results_data = pd.DataFrame(data=ghg_results_data,
                                                columns=ELECTRIFICATION_OPTIONS)

                # sums of the rows
                ghg_results_data['total'] = pd.Series(total)
                # label of the table rows
                ghg_results_data['labels'] = pd.Series(ghg_rows)
                ghg_results_data.iloc[:, 0:4] = ghg_results_data.iloc[:, 0:4].applymap(add_comma)
                answer_table = ghg_results_data[GHG_COLUMNS_ID].to_dict('records')

        return answer_table

    @app_handle.callback(
        Output('aggregate-basic-results-table', 'data'),
        [
            Input('region-input', 'value'),
            Input('scenario-input', 'value'),
        ],
        [State('data-store', 'data')]
    )
    def update_aggregate_basic_results_table(
            region_id,
            scenario,
            cur_data,
    ):
        """Display information and study's results for a country."""
        answer_table = []
        if region_id is not None:
            if scenario in SCENARIOS:

                df = pd.read_json(cur_data[scenario])
                if region_id != WORLD_ID:
                    # narrow to the region if the scope is not on the whole world
                    df = df.loc[df.region == REGIONS_NDC[region_id]]

                # aggregate the results
                df = df[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

                # compute the percentage of population with electricity access
                df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0)
                # gather the values of the results to display in the table
                pop_res = np.squeeze(df[POP_GET].values * 100).round(1)
                hh_res = np.squeeze(df[HH_GET].values).round(0)
                cap_res = np.squeeze(df[HH_CAP].values * 1e-3).round(0)
                cap2_res = np.squeeze(df[HH_SCN2].values * 1e-3).round(0)
                invest_res = np.squeeze(df[INVEST].values).round(0)
                invest_res = np.append(np.NaN, invest_res)
                invest2_res = np.squeeze(df[INVEST_CAP].values).round(0)
                invest2_res = np.append(np.NaN, invest2_res)
                basic_results_data = np.vstack(
                    [pop_res, hh_res, cap_res, cap2_res, invest_res, invest2_res]
                )

                total = np.nansum(basic_results_data, axis=1)

                # prepare a DataFrame
                basic_results_data = pd.DataFrame(
                    data=basic_results_data,
                    columns=ELECTRIFICATION_OPTIONS
                )
                # sums of the rows
                basic_results_data['total'] = pd.Series(total)
                # label of the table rows
                basic_results_data['labels'] = pd.Series(BASIC_ROWS)
                basic_results_data.iloc[1:, 0:4] = basic_results_data.iloc[1:, 0:4].applymap(
                    add_comma
                )
                answer_table = basic_results_data[BASIC_COLUMNS_ID].to_dict('records')

        return answer_table

    @app_handle.callback(
        Output('aggregate-ghg-results-table', 'data'),
        [
            Input('region-input', 'value'),
            Input('scenario-input', 'value'),
        ],
        [State('data-store', 'data')]
    )
    def update_aggregate_ghg_results_table(
            region_id,
            scenario,
            cur_data,
    ):
        """Display information and study's results for a country."""
        answer_table = []
        if region_id is not None:
            if scenario in SCENARIOS:

                df = pd.read_json(cur_data[scenario])
                df_bau = None
                if region_id != WORLD_ID:
                    # narrow to the region if the scope is not on the whole world
                    df = df.loc[df.region == REGIONS_NDC[region_id]]

                if scenario in [SE4ALL_FLEX_SCENARIO, SE4ALL_SCENARIO, PROG_SCENARIO]:

                    # to compare greenhouse gas emissions with BaU scenario
                    df_bau = pd.read_json(cur_data[BAU_SCENARIO])

                    if region_id != WORLD_ID:
                        # narrow to the region if the scope is not on the whole world
                        df_bau = df_bau.loc[df_bau.region == REGIONS_NDC[region_id]]

                if df_bau is None:
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
                    # aggregate the results
                    df_bau = df_bau[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

                # aggregate the results
                df = df[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

                # gather the values of the results to display in the table
                ghg_res = np.squeeze(df[GHG].values).round(0)
                ghg2_res = np.squeeze(df[GHG_CAP].values).round(0)

                if df_bau is not None:
                    ghg_comp_res = ghg_res - np.squeeze(df_bau[GHG].values).round(0)
                    ghg2_comp_res = ghg2_res - np.squeeze(df_bau[GHG_CAP].values).round(0)
                    ghg_results_data = np.vstack([ghg_res, ghg_comp_res, ghg2_res, ghg2_comp_res])
                else:
                    ghg_results_data = np.vstack([ghg_res, ghg2_res])

                total = np.nansum(ghg_results_data, axis=1)

                # prepare a DataFrame
                ghg_results_data = pd.DataFrame(data=ghg_results_data,
                                                columns=ELECTRIFICATION_OPTIONS)
                # sums of the rows
                ghg_results_data['total'] = pd.Series(total)
                ghg_results_data['labels'] = pd.Series(ghg_rows)
                # label of the table rows
                ghg_results_data.iloc[:, 0:4] = ghg_results_data.iloc[:, 0:4].applymap(add_comma)
                answer_table = ghg_results_data[GHG_COLUMNS_ID].to_dict('records')

        return answer_table

    @app_handle.callback(
        Output('country-input', 'value'),
        [Input('data-store', 'data')],
        [State('country-input', 'value')]
    )
    def update_selected_country_on_map(cur_data, cur_val):

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
        if scenario in SCENARIOS and country_iso is not None:
            df = pd.read_json(cur_data[scenario])
            pop_2017 = df.loc[df.country_iso == country_iso].pop_2017.values[0]
            name = df.loc[df.country_iso == country_iso].country.values[0]
            image_filename = 'icons/{}.png'.format(country_iso)
            encoded_image = base64.b64encode(open(image_filename, 'rb').read())

            divs = [
                html.Div(
                    id='results-info-header-div',
                    children=[
                        html.Div(name),
                        html.Img(
                            src='data:image/png;base64,{}'.format(encoded_image.decode()),
                            className='country__info__flag',
                            style={'width': '30%'}
                        )
                    ],
                ),
                html.P(
                    'Population (2017) : {} or whatever information we think '
                    'pertinent to add information information information information information'
                    'information information information information information information '
                    'information information information information information information '
                    'information information information information information information '
                    'information information information information information information '
                    'information information information'.format(pop_2017)),
            ]

        return divs

    @app_handle.callback(
        Output('country-basic-results-title', 'children'),
        [Input('country-input', 'value')],
        [
            State('scenario-input', 'value'),
            State('data-store', 'data')]
    )
    def country_basic_results_title(country_iso, scenario, cur_data):

        answer = 'Results'
        if scenario in SCENARIOS and country_iso is not None:
            df = pd.read_json(cur_data[scenario])
            answer = 'Results for {}'.format(
                df.loc[df.country_iso == country_iso].country.values[0])
        return answer

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
        Output('scenario-input-div', 'title'),
        [Input('scenario-input', 'value')]
    )
    def update_scenario_description(scenario):
        return SCENARIOS_DESCRIPTIONS[scenario]


if __name__ == '__main__':
    app.run_server(debug=True)
