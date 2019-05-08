import base64
import numpy as np
import pandas as pd
import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from data_preparation import (
    SCENARIOS,
    BAU_SCENARIO,
    SE4ALL_SCENARIO,
    SE4ALL_FLEX_SCENARIO,
    PROG_SCENARIO,
    SCENARIOS_DICT,
    SCENARIOS_DESCRIPTIONS,
    MG,
    GRID,
    SHS,
    ELECTRIFICATION_OPTIONS,
    ELECTRIFICATION_DICT,
    ELECTRIFICATION_DESCRIPTIONS,
    MENTI_DRIVES,
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
    prepare_endogenous_variables,
    prepare_se4all_data,
    extract_results_scenario,
    _find_tier_level,
)

from app_components import (
    results_div,
    scenario_div,
    controls_div,
    general_info_div,
    callback_generator
)


# A dict with the data for each scenario in json format
SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce).to_json() for sce in SCENARIOS
}
WORLD_ID = 'WD'
REGIONS_GPD = dict(WD='World', SA='South America', AF='Africa', AS='Asia')

REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')

VIEW_GENERAL = 'general'
VIEW_COUNTRY = 'specific'


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


scl = [
    [0.0, 'rgb(136, 136, 68)'],
    [0.001, 'rgb(242,240,247)'],
    [0.2, 'rgb(218,218,235)'],
    [0.4, 'rgb(188,189,220)'],
    [0.6, 'rgb(158,154,200)'],
    [0.8, 'rgb(117,107,177)'],
    [1.0, 'rgb(84,39,143)']
]

# Initial input data for the map
data = [
    go.Choropleth(
        colorscale=scl,
        autocolorscale=False,
        locationmode='ISO-3',
        marker=go.choropleth.Marker(
            line=go.choropleth.marker.Line(
                color='rgb(255,255,255)',
                width=1.5
            )),
        colorbar=go.choropleth.ColorBar(title="Pop."),

    ),
]

layout = go.Layout(
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


PIECHART_LABELS = list(ELECTRIFICATION_DICT.values())

piechart = go.Figure(data=[go.Pie(labels=PIECHART_LABELS, values=[4500, 2500, 1053], sort=False)])

# Initializes dash app
app = dash.Dash(__name__)

app.title = 'NDC visualisation'

app.layout = html.Div(
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
                            children=scenario_div(SE4ALL_FLEX_SCENARIO, GRID)
                        ),
                        html.Div(
                            id='controls-div',
                            className='app__controls',
                            style={'display': 'none'},
                            children=controls_div(),
                        ),
                        html.Div(
                            id='general-info-div',
                            className='app__info',
                            children=general_info_div()
                        ),
                        html.Div(
                            id='piechart-div',
                            className='app__piechart',
                            children=dcc.Graph(
                                id='piechart',
                                figure=piechart,
                                style={
                                    'height': '55vh',
                                }
                            ),
                        ),
                        html.Div(
                            id='aggregate-div',
                            className='app__aggregate',
                            children=results_div(aggregate=True),
                            style={'display': 'none'}
                        )
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
                                    className='app__logo',
                                ),
                            ]
                        ),
                        html.Div(
                            id='country-input-div',
                            className='app__dropdown',
                            title='country selection description',
                            children=dcc.Dropdown(
                                id='country-input',
                                className='app__input__dropdown__map',
                                options=[],
                                value=None,
                                multi=False
                            )
                        ),
                        html.Div(
                            id='map-div',
                            className='app__map',
                            title='Hover over a country to display information.\n'
                                  + 'Click on it to access detailed report.',
                            children=dcc.Graph(
                                id='map',
                                figure=fig_map,
                                style={'width': '90vh', 'height': '90vh'}
                            ),
                        ),
                        html.Div(
                            id='country-div',
                            className='app__country',
                            children=results_div(),
                            style={'display': 'none'}
                        ),
                    ]

                )
            ],
        )
    ]
)


@app.callback(
    Output('map', 'figure'),
    [
        Input('region-input', 'value'),
        Input('scenario-input', 'value'),
        Input('electrification-input', 'value')
    ],
    [
        State('map', 'figure'),
        State('data-store', 'data')
    ]
)
def update_map(region_id, scenario, elec_opt, fig, cur_data):
    """Plot color map of the percentage of people with a given electrification option."""

    # load the data of the scenario
    df = pd.read_json(cur_data[scenario])

    if region_id != WORLD_ID:
        # narrow to the region if the scope is not on the whole world
        df = df.loc[df.region == REGIONS_NDC[region_id]]
        # color of country boundaries
        line_color = 'rgb(255,255,255)'
    else:
        # color of country boundaries
        line_color = 'rgb(179,179,179)'

    # compute the percentage of people with the given electrification option
    z = df['pop_get_%s_2030' % elec_opt].div(df.pop_newly_electrified_2030, axis=0).round(3)

    if region_id == 'SA':
        region_name = REGIONS_GPD[WORLD_ID]
        geo = 'geo2'
    else:
        region_name = REGIONS_GPD[region_id]
        geo = 'geo'

    fig['data'][0].update(
        {
            'locations': df['country_iso'],
            'z': z * 100,
            'zmin': 0,
            'zmax': 100,
            'text': country_hover_text(df),
            'geo': geo,
            'marker': {'line': {'color': line_color}},
            'colorbar': go.choropleth.ColorBar(
                title="2030<br>%% %s<br>access" % elec_opt,
                tickmode="array",
                tickvals=[10 * i for i in range(11)]
            ),
        }
    )

    fig['layout']['geo'].update({'scope': region_name.lower()})
    return fig


@app.callback(
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
    the left panel and results details as well as country-specific information on the right panel.

    The app start in the VIEW_GENERAL. The VIEW_COUNTRY can be accessed by cliking on a
    specific country or selecting it with the country dropdown,

    The controls_display is set to 'flex' only for the se4all+shift scenario and is set to 'none'
    for the other scenarios (these scenarios do not have variables).
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


@app.callback(
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


@app.callback(
    Output('country-div', 'style'),
    [Input('view-store', 'data')],
    [State('country-div', 'style')]
)
def toggle_results_div_display(cur_view, cur_style):
    """Change the display of country-div between the app's views."""
    if cur_style is None:
        cur_style = {'display': 'none'}

    if cur_view['app_view'] == VIEW_GENERAL:
        cur_style.update({'display': 'none'})
    elif cur_view['app_view'] == VIEW_COUNTRY:
        cur_style.update({'display': 'flex'})
    return cur_style


@app.callback(
    Output('controls-div', 'style'),
    [Input('view-store', 'data')],
    [State('controls-div', 'style')]
)
def toggle_controls_div_display(cur_view, cur_style):
    """Change the display of controls-div between the app's views."""
    if cur_style is None:
        cur_style = {'display': 'none'}

    if cur_view['app_view'] == VIEW_GENERAL:
        cur_style.update({'display': 'none'})
    elif cur_view['app_view'] == VIEW_COUNTRY:
        cur_style.update({'display': cur_view['controls_display']})
    return cur_style


@app.callback(
    Output('general-info-div', 'style'),
    [Input('view-store', 'data')],
    [State('general-info-div', 'style')]
)
def toggle_general_info_div_display(cur_view, cur_style):
    """Change the display of general-info-div between the app's views."""
    if cur_style is None:
        cur_style = {'display': 'flex'}

    if cur_view['app_view'] == VIEW_GENERAL:
        cur_style.update({'display': 'flex'})
    elif cur_view['app_view'] == VIEW_COUNTRY:
        cur_style.update({'display': 'none'})
    return cur_style


@app.callback(
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


@app.callback(
    Output('piechart-div', 'style'),
    [
        Input('view-store', 'data'),
        Input('aggregate-input', 'values'),
    ],
    [State('piechart-div', 'style')]
)
def toggle_piechart_div_display(cur_view, aggregate, cur_style):
    """Change the display of piechart-div between the app's views."""
    if cur_style is None:
        cur_style = {'app_view': VIEW_GENERAL}

    if cur_view['app_view'] == VIEW_GENERAL:
        if aggregate:
            cur_style.update({'display': 'none'})
        else:
            cur_style.update({'display': 'flex'})
    elif cur_view['app_view'] == VIEW_COUNTRY:
        cur_style.update({'display': 'flex'})
    return cur_style


@app.callback(
    Output('country-basic-results-table', 'data'),
    [
        Input('country-input', 'value'),
        Input('scenario-input', 'value'),
        Input('mentis-weight-input', 'value'),
        Input('mentis-gdp-input', 'value'),
        Input('mentis-mobile-money-input', 'value'),
        Input('mentis-ease-doing-business-input', 'value'),
        Input('mentis-corruption-input', 'value'),
        Input('mentis-weak-grid-input', 'value'),
        Input('rise-mg-input', 'value'),
        Input('rise-shs-input', 'value'),
        Input('min-tier-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_country_basic_results_table(
        country_sel,
        scenario,
        weight_mentis,
        gdp_class,
        mm_class,
        edb_class,
        corruption_class,
        weak_grid_class,
        rise_mg,
        rise_shs,
        min_tier_level,
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

            if scenario in [SE4ALL_FLEX_SCENARIO, SE4ALL_SCENARIO, PROG_SCENARIO]:
                # TODO: only recompute the tier if it has changed (with context)
                if min_tier_level is not None:
                    df = prepare_endogenous_variables(
                        input_df=df,
                        min_tier_level=min_tier_level
                    )
            if scenario == SE4ALL_FLEX_SCENARIO:

                if gdp_class is not None:
                    df.loc[:, 'gdp_class'] = gdp_class
                if mm_class is not None:
                    df.loc[:, 'mobile_money_class'] = mm_class
                if edb_class is not None:
                    df.loc[:, 'ease_doing_business_class'] = edb_class
                if corruption_class is not None:
                    df.loc[:, 'corruption_class'] = corruption_class
                if weak_grid_class is not None:
                    df.loc[:, 'weak_grid_class'] = weak_grid_class
                if rise_mg is not None:
                    df.loc[:, 'rise_mg'] = rise_mg
                if rise_shs is not None:
                    df.loc[:, 'rise_shs'] = rise_shs

                # recompute the results after updating the shift drives
                df = prepare_se4all_data(
                    input_df=df,
                    weight_mentis=weight_mentis,
                    fixed_shift_drives=False
                )
                df = extract_results_scenario(df, scenario)

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
            # prepare a DataFrame
            basic_results_data = pd.DataFrame(
                data=basic_results_data,
                columns=ELECTRIFICATION_OPTIONS
            )
            # label of the table rows
            basic_results_data['labels'] = pd.Series(BASIC_ROWS)
            answer_table = basic_results_data[BASIC_COLUMNS_ID].to_dict('records')

    return answer_table


@app.callback(
    Output('country-ghg-results-table', 'data'),
    [
        Input('country-input', 'value'),
        Input('scenario-input', 'value'),
        Input('mentis-weight-input', 'value'),
        Input('mentis-gdp-input', 'value'),
        Input('mentis-mobile-money-input', 'value'),
        Input('mentis-ease-doing-business-input', 'value'),
        Input('mentis-corruption-input', 'value'),
        Input('mentis-weak-grid-input', 'value'),
        Input('rise-mg-input', 'value'),
        Input('rise-shs-input', 'value'),
        Input('min-tier-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_country_ghg_results_table(
        country_sel,
        scenario,
        weight_mentis,
        gdp_class,
        mm_class,
        edb_class,
        corruption_class,
        weak_grid_class,
        rise_mg,
        rise_shs,
        min_tier_level,
        cur_data,
):
    """Display information and study's results for a country."""
    answer_table = []
    df_comp = None
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
                df_comp = pd.read_json(cur_data[BAU_SCENARIO])
                df_comp = df_comp.loc[df_comp.country_iso == country_iso]

                # TODO: only recompute the tier if it has changed (with context)
                if min_tier_level is not None:
                    df = prepare_endogenous_variables(
                        input_df=df,
                        min_tier_level=min_tier_level
                    )

            if scenario == SE4ALL_FLEX_SCENARIO:

                if gdp_class is not None:
                    df.loc[:, 'gdp_class'] = gdp_class
                if mm_class is not None:
                    df.loc[:, 'mobile_money_class'] = mm_class
                if edb_class is not None:
                    df.loc[:, 'ease_doing_business_class'] = edb_class
                if corruption_class is not None:
                    df.loc[:, 'corruption_class'] = corruption_class
                if weak_grid_class is not None:
                    df.loc[:, 'weak_grid_class'] = weak_grid_class
                if rise_mg is not None:
                    df.loc[:, 'rise_mg'] = rise_mg
                if rise_shs is not None:
                    df.loc[:, 'rise_shs'] = rise_shs

                # recompute the results after updating the shift drives
                df = prepare_se4all_data(
                    input_df=df,
                    weight_mentis=weight_mentis,
                    fixed_shift_drives=False
                )
                df = extract_results_scenario(df, scenario)

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

            # gather the values of the results to display in the table
            ghg_res = np.squeeze(df[GHG].values).round(0)
            ghg2_res = np.squeeze(df[GHG_CAP].values).round(0)
            if df_comp is not None:
                ghg_comp_res = ghg_res - np.squeeze(df_comp[GHG].values).round(0)
                ghg2_comp_res = ghg2_res - np.squeeze(df_comp[GHG_CAP].values).round(0)
                ghg_results_data = np.vstack([ghg_res, ghg_comp_res, ghg2_res, ghg2_comp_res])
            else:
                ghg_results_data = np.vstack([ghg_res, ghg2_res])
            # prepare a DataFrame
            ghg_results_data = pd.DataFrame(data=ghg_results_data, columns=ELECTRIFICATION_OPTIONS)
            # label of the table rows
            ghg_results_data['labels'] = pd.Series(ghg_rows)
            answer_table = ghg_results_data[GHG_COLUMNS_ID].to_dict('records')

    return answer_table


@app.callback(
    Output('aggregate-basic-results-table', 'data'),
    [
        Input('region-input', 'value'),
        Input('scenario-input', 'value'),
        Input('min-tier-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_aggregate_basic_results_table(
        region_id,
        scenario,
        min_tier_level,
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

            if scenario in [SE4ALL_FLEX_SCENARIO, SE4ALL_SCENARIO, PROG_SCENARIO]:

                # TODO: only recompute the tier if it has changed (with context)
                if min_tier_level is not None:
                    df = prepare_endogenous_variables(
                        input_df=df,
                        min_tier_level=min_tier_level
                    )

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
            # prepare a DataFrame
            basic_results_data = pd.DataFrame(
                data=basic_results_data,
                columns=ELECTRIFICATION_OPTIONS
            )
            # label of the table rows
            basic_results_data['labels'] = pd.Series(BASIC_ROWS)
            answer_table = basic_results_data[BASIC_COLUMNS_ID].to_dict('records')

    return answer_table


@app.callback(
    Output('aggregate-ghg-results-table', 'data'),
    [
        Input('region-input', 'value'),
        Input('scenario-input', 'value'),
        Input('min-tier-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_aggregate_ghg_results_table(
        region_id,
        scenario,
        min_tier_level,
        cur_data,
):
    """Display information and study's results for a country."""
    answer_table = []
    if region_id is not None:
        if scenario in SCENARIOS:
            df = pd.read_json(cur_data[scenario])
            df_comp = None
            if region_id != WORLD_ID:
                # narrow to the region if the scope is not on the whole world
                df = df.loc[df.region == REGIONS_NDC[region_id]]

            if scenario in [SE4ALL_FLEX_SCENARIO, SE4ALL_SCENARIO, PROG_SCENARIO]:

                # to compare greenhouse gas emissions with BaU scenario
                df_comp = pd.read_json(cur_data[BAU_SCENARIO])

                if region_id != WORLD_ID:
                    # narrow to the region if the scope is not on the whole world
                    df_comp = df_comp.loc[df_comp.region == REGIONS_NDC[region_id]]

                # TODO: only recompute the tier if it has changed (with context)
                if min_tier_level is not None:
                    df = prepare_endogenous_variables(
                        input_df=df,
                        tier_level=min_tier_level
                    )

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
                # aggregate the results
                df_comp = df_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

            # aggregate the results
            df = df[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)

            # gather the values of the results to display in the table
            ghg_res = np.squeeze(df[GHG].values).round(0)
            ghg2_res = np.squeeze(df[GHG_CAP].values).round(0)

            if df_comp is not None:
                ghg_comp_res = ghg_res - np.squeeze(df_comp[GHG].values).round(0)
                ghg2_comp_res = ghg2_res - np.squeeze(df_comp[GHG_CAP].values).round(0)
                ghg_results_data = np.vstack([ghg_res, ghg_comp_res, ghg2_res, ghg2_comp_res])
            else:
                ghg_results_data = np.vstack([ghg_res, ghg2_res])
            # prepare a DataFrame
            ghg_results_data = pd.DataFrame(data=ghg_results_data, columns=ELECTRIFICATION_OPTIONS)
            ghg_results_data['labels'] = pd.Series(ghg_rows)
            # label of the table rows
            ghg_columns = ['labels'] + ELECTRIFICATION_OPTIONS
            answer_table = ghg_results_data[ghg_columns].to_dict('records')

    return answer_table


# generate callbacks for the mentis drives dcc.Input
for input_name in MENTI_DRIVES:
    callback_generator(app, 'mentis-%s' % input_name.replace('_', '-'), '%s_class' % input_name)

# generate callbacks for the mentis drives dcc.Input
for input_name in [MG, SHS]:
    callback_generator(app, 'rise-%s' % input_name.replace('_', '-'), 'rise_%s' % input_name)


@app.callback(
    Output('piechart', 'figure'),
    [Input('map', 'hoverData')],
    [
        State('piechart', 'figure'),
        State('scenario-input', 'value'),
        State('data-store', 'data')
    ]
)
def update_piechart(selected_data, fig, scenario, cur_data):
    if selected_data is not None:
        chosen = [point['location'] if point['pointNumber'] != 0 else None for point in
                  selected_data['points']]
        if chosen[0] is not None:
            country_iso = chosen[0]
            if scenario in SCENARIOS:
                # load the data of the scenario
                df = pd.read_json(cur_data[scenario])
                # narrow the selection to the selected country
                df = df.loc[df.country_iso == country_iso]

                # compute the percentage of people with the given electrification option
                df[POP_GET] = df[POP_GET].div(df.pop_newly_electrified_2030, axis=0).round(3)
                # TODO: need to implement https://en.wikipedia.org/wiki/Largest_remainder_method
                percentage = df[POP_GET].values[0] * 100
                labels = PIECHART_LABELS

                if scenario == BAU_SCENARIO:
                    diff = 100 - percentage.sum()
                    percentage = np.append(percentage, diff)
                    labels = PIECHART_LABELS + ['no electricity']

                fig['data'][0].update(
                    {
                        'values': percentage,
                        'labels': labels
                    }
                )
    return fig


@app.callback(
    Output('country-input', 'value'),
    [Input('data-store', 'data')],
    [State('country-input', 'value')]
)
def update_selected_country_on_map(cur_data, cur_val):

    country_iso = cur_data.get('selected_country')
    if country_iso is None:
        country_iso = cur_val
    return country_iso


@app.callback(
    Output('country-info-div', 'children'),
    [
        Input('scenario-input', 'value'),
        Input('country-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_country_info_div(scenario, country_iso, cur_data):

    divs = []
    if scenario in SCENARIOS and country_iso is not None:
        df = pd.read_json(cur_data[scenario])
        pop_2017 = df.loc[df.country_iso == country_iso].pop_2017.values[0]

        image_filename = 'icons/{}.png'.format(country_iso)
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())

        divs = [
            html.Img(
                src='data:image/png;base64,{}'.format(encoded_image.decode()),
                className='country__info__flag',
                style={'width': '100%'}
            ),
            html.Div('Population (2017) : {}'.format(pop_2017)),
        ]

    return divs


@app.callback(
    Output('country-basic-results-title', 'children'),
    [Input('country-input', 'value')],
    [
        State('scenario-input', 'value'),
        State('data-store', 'data')]
)
def country_basic_results_title(country_iso, scenario,  cur_data):

    answer = 'Results'
    if scenario in SCENARIOS and country_iso is not None:
        df = pd.read_json(cur_data[scenario])
        answer = 'Results for {}'.format(df.loc[df.country_iso == country_iso].country.values[0])
    return answer


@app.callback(
    Output('tier-value', 'children'),
    [Input('country-input', 'value')],
    [
        State('scenario-input', 'value'),
        State('data-store', 'data')]
)
def update_tier_value_div(country_iso, scenario, cur_data):
    """Find the actual tier level of the country based on its yearly electricity consumption"""
    answer = ''
    if scenario in SCENARIOS and country_iso is not None:
        df = pd.read_json(cur_data[scenario])
        answer = '{}'.format(
            _find_tier_level(
                df.loc[df.country_iso == country_iso].hh_yearly_electricity_consumption.values[0],
                1
            )
        )
    return answer


@app.callback(
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


@app.callback(
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


@app.callback(
    Output('data-store', 'data'),
    [Input('map', 'clickData')],
    [State('data-store', 'data')]
)
def update_data_store(clicked_data, cur_data):
    if clicked_data is not None:
        country_iso = clicked_data['points'][0]['location']
        cur_data.update({'selected_country': country_iso})
    return cur_data


@app.callback(
    Output('scenario-input-div', 'title'),
    [Input('scenario-input', 'value')]
)
def update_scenario_description(scenario):
    return SCENARIOS_DESCRIPTIONS[scenario]


@app.callback(
    Output('electrification-input-div', 'title'),
    [Input('electrification-input', 'value')]
)
def update_electrification_description(elec_opt):
    return ELECTRIFICATION_DESCRIPTIONS[elec_opt]


if __name__ == '__main__':
    app.run_server(debug=True)
