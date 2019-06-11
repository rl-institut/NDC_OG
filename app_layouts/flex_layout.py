import base64
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
    ELECTRIFICATION_OPTIONS,
    NO_ACCESS,
    POP_GET,
    POP_RES,
    INVEST_RES,
    GHG,
    GHG_CAP,
    GHG_RES,
    GHG_ER_RES,
    EXO_RESULTS,
    _find_tier_level,
    compute_ndc_results_from_raw_data,
    extract_results_scenario,
    prepare_scenario_data,
    prepare_results_tables,
)

from .app_components import (
    scenario_div,
    results_div,
    controls_div,
    round_digits,
    format_percent,
    TABLES_COLUMNS_WIDTH,
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

URL_PATHNAME = 'flex'


def extract_centroids(reg):
    """Load the longitude and latitude of countries per region."""
    if not isinstance(reg, list):
        reg = [reg]
    centroids = pd.read_csv('data/centroid.csv')
    return centroids.loc[centroids.region.isin(reg)].copy()


WORLD_ID = 'WD'
REGIONS_GPD = dict(WD='World', SA='South America', AF='Africa', AS='Asia')

REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')

VIEW_COUNTRY_SELECT = 'country'
VIEW_CONTROLS = 'general'
VIEW_COMPARE = 'compare'

# A dict with the data for each scenario in json format
SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce, MIN_TIER_LEVEL).to_json() for sce in SCENARIOS
}
SCENARIOS_DATA.update(
    {reg: extract_centroids(REGIONS_NDC[reg]).to_json() for reg in REGIONS_NDC}
)

list_countries_dropdown = []
DF = pd.read_json(SCENARIOS_DATA[SE4ALL_SCENARIO])
DF = DF.sort_values('country')
for idx, row in DF.iterrows():
    list_countries_dropdown.append({'label': row['country'], 'value': row['country_iso']})


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
    [0.0, '#f0f0f0'],
    [0.001, '#d2fbd4'],
    [0.2, '#a5dbc2'],
    [0.4, '#7bbcb0'],
    [0.6, '#559c9e'],
    [0.8, '#3a7c89'],
    [1.0, '#235d72']
]

# Initial input data for the map
data = [
    go.Choropleth(
        colorscale=scl,
        autocolorscale=False,
        locationmode='ISO-3',
        hoverinfo='text',
        marker=go.choropleth.Marker(
            line=go.choropleth.marker.Line(
                color='rgb(255,255,255)',
                width=1.5
            )),
        colorbar=go.choropleth.ColorBar(title="Pop."),

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
    id='flex-main-div',
    className='grid-y',
    children=[
        dcc.Store(
            id='flex-data-store',
            storage_type='session',
            data=SCENARIOS_DATA.copy()
        ),
        dcc.Store(
            id='flex-country-store',
            storage_type='session',
            data={}
        ),
        dcc.Store(
            id='flex-view-store',
            storage_type='session',
            data={'app_view': VIEW_COUNTRY_SELECT}
        ),
        html.Div(
            id='flex-general-info-div',
            className='app__info',
            children=html.Div('Information here about what the user can do with '
                              'RISE')
        ),
        html.Div(
            id='flex-app-div',
            className='cell grid-x',
            # children=html.Div(
            #     id='flex-app-content',
            #     className='grid-x',
            children=[
                # dcc.Store(
                #     id='flex-data-store',
                #     storage_type='session',
                #     data=SCENARIOS_DATA.copy()
                # ),

                html.Div(
                    id='flex-left-panel-div',
                    className='cell medium-6',
                    children=[
                        html.Div(
                            id='flex-header-div',
                            className='app__header',
                            style={'display': 'none'},
                            children=[
                                html.Div(
                                    id='flex-region-label',
                                    className='app__input__label',
                                    children='Region:'
                                ),
                                html.Div(
                                    id='flex-region-input-div',
                                    className='app__dropdown',
                                    title='region selection description',
                                    children=dcc.Dropdown(
                                        id='flex-region-input',
                                        className='app__input__dropdown__map',
                                        options=[
                                            {'label': v, 'value': k}
                                            for k, v in REGIONS_GPD.items()
                                        ],
                                        value=WORLD_ID
                                    )
                                ),
                                # html.Div(
                                #     id='flex-logo-div',
                                #     children=[
                                #         html.Img(
                                #             src='data:image/png;base64,{}'.format(logo.decode()),
                                #             className='app__logo',
                                #             # style={'height': '5vh', 'padding': '10px'}
                                #         )
                                #         for logo in logos
                                #     ]
                                # ),
                            ]
                        ),

                        html.Div(
                            id='flex-country-input-div',
                            title='country selection description',
                            className='grid-x',
                            children=[
                                html.Div(
                                    id='flex-country-label',
                                    className='cell medium-3 app__input__label',
                                    children='Country:'
                                ),
                                dcc.Dropdown(
                                    id='flex-country-input',
                                    className='cell medium-6 app__input__dropdown__country',
                                    options=list_countries_dropdown,
                                    value=None,
                                    multi=False
                                ),



                                # html.Div(
                                #     id='flex-compare-input-div',
                                #     children=[
                                #         html.Div(
                                #             id='flex-country-comp-label',
                                #             className='app__input__label',
                                #             children='compare with:'
                                #         ),
                                #         dcc.Dropdown(
                                #             id='flex-compare-input',
                                #             className='app__input__dropdown__country',
                                #             options=COMPARE_OPTIONS,
                                #             value=None,
                                #             multi=False
                                #         )
                                #     ],
                                #     style={'display': 'none'}
                                # )

                            ]
                        ),
                        html.Div(
                            id='flex-options-div',
                            style={'display': 'none'},
                            className='grid-y',
                            children=[
                                html.Div(
                                    id='flex-country-info-div',
                                    className='cell medium-7 results__info',
                                    children=''
                                ),
                                html.Div(
                                    id='flex-controls-div',
                                    className='cell medium-3 app__controls',
                                    children=controls_div(),
                                ),
                                html.Div(
                                    id='flex-scenario-div',
                                    className='cell medium-2 app__options',
                                    children=scenario_div(BAU_SCENARIO, scenario_type='flex-')
                                ),

                            ]
                        )
                        # html.Div(
                        #     id='flex-compare-div',
                        #     children=compare_div(),
                        #     style={'display': 'none'}
                        # ),
                    ]

                ),
                html.Div(
                    id='flex-{}-div'.format(RES_COUNTRY),
                    className='cell medium-6',
                    children=html.Div(
                        className='grid-x',
                        children=[
                            results_div(RES_COUNTRY, res_category, scenario_type='flex-')
                            for res_category in [POP_RES, INVEST_RES, GHG_RES]
                        ]
                    ),

                ),
            ],
            # )
        )

    ]
)


def country_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = 'flex-{}-{}'.format('country', result_category)

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('{}-barplot-yaxis-input'.format(id_name), 'value'),
            Input('flex-country-store', 'data'),
            Input('flex-rise-grid-input', 'value'),
            Input('flex-rise-mg-input', 'value'),
            Input('flex-rise-shs-input', 'value'),
            Input('flex-min-tier-input', 'value'),
        ],
        [
            State('data-store', 'data'),
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def update_barplot(
            y_sel,
            country_data,
            rise_grid,
            rise_mg,
            rise_shs,
            min_tier_level,
            cur_data,
            fig

    ):
        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        country_iso = country_data.get('country_iso')
        if country_iso is not None:
            df = pd.read_json(country_data['selection'])
            x_vals = [SCENARIOS_DICT[sce] for sce in SCENARIOS]
            y_vals = []

            df.rise_grid = rise_grid
            df.rise_mg = rise_mg
            df.rise_shs = rise_shs

            df = prepare_scenario_data(
                df,
                SE4ALL_SCENARIO,
                min_tier_level,
                prepare_endogenous=True
            )

            df = extract_results_scenario(df, SE4ALL_SCENARIO, min_tier_level)
            # compute the percentage of population with electricity access
            results_data = prepare_results_tables(df, SE4ALL_SCENARIO, result_category)
            y = results_data[idx_y]

            fig['data'][0].update({'text': ['flex', 'flex', 'flex', 'flex']})
            fig['data'][0].update({'x': ELECTRIFICATION_OPTIONS.copy()})
            fig['data'][0].update({'y': y})
        return fig

    update_barplot.__name__ = 'update_%s_barplot' % id_name

    return update_barplot


def country_table_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = 'flex-{}-{}'.format(RES_COUNTRY, result_category)

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'data'),
        [
            Input('flex-country-store', 'data'),
            Input('flex-rise-grid-input', 'value'),
            Input('flex-rise-mg-input', 'value'),
            Input('flex-rise-shs-input', 'value'),
            Input('flex-min-tier-input', 'value'),
            Input('flex-scenario-input', 'value'),
        ],
        [State('data-store', 'data')]
    )
    def update_table(
            country_data,
            rise_grid,
            rise_mg,
            rise_shs,
            min_tier_level,
            scenario
    ):
        """Display information and study's results for a country."""

        result_cat = result_category

        answer_table = []
        country_iso = country_data.get('country_iso')

        # extract the data from the selected scenario if a country was selected
        if country_iso is not None:
            df = pd.read_json(country_data['selection'])

            df.rise_grid = rise_grid
            df.rise_mg = rise_mg
            df.rise_shs = rise_shs

            df = prepare_scenario_data(
                df,
                SE4ALL_SCENARIO,
                min_tier_level,
                prepare_endogenous=True
            )

            df = df.loc[df.country_iso == country_iso]

            ghg_er = False
            if result_cat == GHG_RES and scenario != BAU_SCENARIO:
                ghg_er = True
                result_cat = GHG_ER_RES

            results_data = prepare_results_tables(df, SE4ALL_SCENARIO, result_cat, ghg_er)

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

            answer_table = results_data[TABLE_COLUMNS_ID].to_dict('records')
        return answer_table

    update_table.__name__ = 'update_%s_table' % id_name
    return update_table


def callbacks(app_handle):
    for res_cat in [POP_RES, INVEST_RES, GHG_RES]:

        country_barplot_callback(app_handle, res_cat)
        country_table_callback(app_handle, res_cat)

    #     aggregate_barplot_callback(app_handle, res_cat)
    #     aggregate_table_callback(app_handle, res_cat)
    #
    #     compare_barplot_callback(app_handle, res_cat)
    #     compare_table_callback(app_handle, res_cat)
    #     compare_table_styling_callback(app_handle, res_cat)
    #     compare_table_columns_title_callback(app_handle, res_cat)
    #
    #     for res_type in [RES_COUNTRY, RES_AGGREGATE]:
    #         country_aggregate_title_callback(app_handle, res_type, res_cat)
    #     compare_title_callback(app_handle, res_cat)
    #
    # for res_type in [RES_COUNTRY, RES_AGGREGATE, RES_COMPARE]:
    #     ghg_dropdown_options_callback(app_handle, res_type)

    # @app_handle.callback(
    #     Output('flex-compare-barplot', 'figure'),
    #     [
    #         Input('flex-country-input', 'value'),
    #         Input('flex-compare-input', 'value'),
    #         Input('flex-scenario-input', 'value'),
    #         Input('flex-compare-barplot-yaxis-input', 'value'),
    #         Input('flex-country-store', 'data')
    #     ],
    #     [
    #         State('flex-compare-barplot', 'figure')
    #     ]
    # )
    # def update_compare_barplot(country_sel, comp_sel, scenario, y_sel, cur_data, fig):
    #     """update the barplot whenever the country changes"""
    #     if country_sel is not None:
    #         if comp_sel is not None:
    #
    #             comp_name = comp_sel
    #             df = pd.read_json(cur_data[scenario])
    #             df_comp = df.copy()
    #             df = df.loc[df.country_iso == country_sel]
    #             if comp_sel in REGIONS_NDC:
    #                 # compare the reference country to a region
    #                 if comp_sel != WORLD_ID:
    #                     df_comp = df_comp.loc[df_comp.region == REGIONS_NDC[comp_sel]]
    #                 df_comp = df_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)
    #                 comp_name = REGIONS_GPD[comp_sel]
    #             else:
    #                 # compare the reference country to a country
    #                 df_comp = df_comp.loc[df_comp.country_iso == comp_sel]
    #
    #             basic_results_data = prepare_results_tables(df)
    #             comp_results_data = prepare_results_tables(df_comp)
    #
    #             y = basic_results_data[BASIC_ROWS.index(y_sel)]
    #             y_comp = comp_results_data[BASIC_ROWS.index(y_sel)]
    #
    #             x_vals = ELECTRIFICATION_OPTIONS.copy()
    #
    #             if scenario == BAU_SCENARIO and y_sel == BASIC_ROWS[0]:
    #                 y = np.append(y, 0)
    #                 y_comp = np.append(y_comp, 0)
    #                 y[3] = 100 - y.sum()
    #                 y_comp[3] = 100 - y_comp.sum()
    #                 x_vals = ELECTRIFICATION_OPTIONS.copy() + ['No electricity']
    #             fs = 12
    #
    #             fig['data'] = [
    #                 go.Bar(
    #                     x=x_vals,
    #                     y=y,
    #                     text=[country_sel for i in range(4)],
    #                     insidetextfont={'size': fs},
    #                     textposition='auto',
    #                     marker=dict(
    #                         color=['#0000ff', '#ffa500', '#008000', 'red']
    #                     ),
    #                     hoverinfo='y+text'
    #                 ),
    #                 go.Bar(
    #                     x=x_vals,
    #                     y=y_comp,
    #                     text=[comp_name for i in range(4)],
    #                     insidetextfont={'size': fs},
    #                     textposition='auto',
    #                     marker=dict(
    #                         color=['#8080ff', '#ffd280', '#1aff1a', 'red']
    #                     ),
    #                     hoverinfo='y+text'
    #                 ),
    #             ]
    #
    #     return fig

    @app_handle.callback(
        Output('flex-view-store', 'data'),
        [
            Input('flex-country-input', 'value'),
        ],
        [State('flex-view-store', 'data')]
    )
    def flex_update_view(country_sel, cur_view):
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

        comp_sel = False  # for the moment

        ctx = dash.callback_context
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            # trigger comes from clicking on a country
            if 'country-input' in prop_id:
                if country_sel is not None:
                    if comp_sel:
                        cur_view.update({'app_view': VIEW_COMPARE})
                    else:
                        cur_view.update({'app_view': VIEW_CONTROLS})
                else:
                    cur_view.update({'app_view': VIEW_COUNTRY_SELECT})

            # # trigger comes from selection a comparison region/country
            # elif 'compare-input' in prop_id:
            #     if comp_sel:
            #         cur_view.update({'app_view': VIEW_COMPARE})
            #     else:
            #         if country_sel:
            #             cur_view.update({'app_view': VIEW_CONTROLS})
        return cur_view

    @app_handle.callback(
        Output('flex-results-div', 'style'),
        [Input('flex-view-store', 'data')],
        [State('flex-results-div', 'style')]
    )
    def flex_toggle_results_div_display(cur_view, cur_style):
        """Change the display of results-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if cur_view['app_view'] == VIEW_COUNTRY_SELECT:
            cur_style.update({'display': 'none'})
        elif cur_view['app_view'] in [VIEW_CONTROLS]:
            cur_style.update({'display': 'flex'})
        return cur_style

    @app_handle.callback(
        Output('flex-options-div', 'style'),
        [Input('flex-view-store', 'data')],
        [State('flex-options-div', 'style')]
    )
    def flex_toggle_results_info_div_display(cur_view, cur_style):
        """Change the display of results-info-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if cur_view['app_view'] == VIEW_COUNTRY_SELECT:
            cur_style.update({'display': 'none'})
        elif cur_view['app_view'] == VIEW_CONTROLS:
            cur_style.update({'display': 'flex'})
        # elif cur_view['app_view'] == VIEW_COMPARE:
        #     cur_style.update({'display': 'none'})
        return cur_style

    # @app_handle.callback(
    #     Output('flex-compare-input-div', 'style'),
    #     [
    #         Input('flex-view-store', 'data'),
    #     ],
    #     [State('flex-compare-input-div', 'style')]
    # )
    # def flex_toggle_compare_input_div_display(cur_view, cur_style):
    #     """Change the display of compare-input-div between the app's views."""
    #     if cur_style is None:
    #         cur_style = {'display': 'none'}
    #
    #     if cur_view['app_view'] == VIEW_GENERAL:
    #         cur_style.update({'display': 'none'})
    #     elif cur_view['app_view'] in [VIEW_COUNTRY, VIEW_COMPARE]:
    #         cur_style.update({'display': 'flex'})
    #     return cur_style

    # @app_handle.callback(
    #     Output('flex-compare-div', 'style'),
    #     [
    #         Input('flex-view-store', 'data'),
    #     ],
    #     [State('flex-compare-div', 'style')]
    # )
    # def flex_toggle_compare_div_display(cur_view, cur_style):
    #     """Change the display of compare-input-div between the app's views."""
    #     if cur_style is None:
    #         cur_style = {'display': 'none'}
    #
    #     if cur_view['app_view'] in [VIEW_GENERAL, VIEW_COUNTRY]:
    #         cur_style.update({'display': 'none'})
    #     elif cur_view['app_view'] == VIEW_COMPARE:
    #         cur_style.update({'display': 'flex'})
    #     return cur_style

    # @app_handle.callback(
    #     Output('flex-compare-basic-results-table', 'data'),
    #     [
    #         Input('flex-country-input', 'value'),
    #         Input('flex-compare-input', 'value'),
    #         Input('flex-scenario-input', 'value'),
    #         Input('flex-country-store', 'data')
    #     ]
    # )
    # def flex_update_compare_basic_results_table(country_sel, comp_sel, scenario, cur_data):
    #     """Display information and study's results comparison between countries."""
    #     answer_table = []
    #     country_iso = country_sel
    #     # in case of country_iso is a list of one element
    #     if np.shape(country_iso) and len(country_iso) == 1:
    #         country_iso = country_iso[0]
    #
    #     # extract the data from the selected scenario if a country was selected
    #     if country_iso is not None and comp_sel is not None:
    #         if scenario in SCENARIOS:
    #             df = pd.read_json(cur_data[scenario])
    #             df_comp = df.copy()
    #             df = df.loc[df.country_iso == country_sel]
    #             if comp_sel in REGIONS_NDC:
    #                 # compare the reference country to a region
    #                 if comp_sel != WORLD_ID:
    #                     df_comp = df_comp.loc[df_comp.region == REGIONS_NDC[comp_sel]]
    #                 df_comp = df_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)
    #             else:
    #                 # compare the reference country to a country
    #                 df_comp = df_comp.loc[df_comp.country_iso == comp_sel]
    #
    #             basic_results_data = prepare_results_tables(df)
    #             comp_results_data = prepare_results_tables(df_comp)
    #
    #             total = np.nansum(basic_results_data, axis=1)
    #             comp_total = np.nansum(comp_results_data, axis=1)
    #
    #             basic_results_data = 100 * np.divide(
    #                 comp_results_data - basic_results_data,
    #                 comp_results_data
    #             )
    #
    #             total = 100 * np.divide(
    #                 comp_total - total,
    #                 comp_total
    #             )
    #
    #             basic_results_data = np.hstack([comp_results_data, basic_results_data])
    #
    #             comp_ids = ['comp_{}'.format(c) for c in ELECTRIFICATION_OPTIONS]
    #             # prepare a DataFrame
    #             basic_results_data = pd.DataFrame(
    #                 data=basic_results_data,
    #                 columns=ELECTRIFICATION_OPTIONS + comp_ids
    #             )
    #
    #             # sums of the rows
    #             basic_results_data['total'] = pd.Series(comp_total)
    #             basic_results_data['comp_total'] = pd.Series(total)
    #             # label of the table rows
    #             basic_results_data['labels'] = pd.Series(BASIC_ROWS)
    #             basic_results_data.iloc[:, 0:8] = \
    #                 basic_results_data.iloc[:, 0:8].applymap(
    #                     add_comma
    #                 )
    #             basic_results_data.iloc[0, 0:8] = basic_results_data.iloc[0, 0:8].map(
    #                 lambda x: '{}%'.format(x)
    #             )
    #             basic_results_data[comp_ids + ['comp_total']] = \
    #                 basic_results_data[comp_ids + ['comp_total']].applymap(
    #                     lambda x: '' if x == '' else str(x) if '%' in x else '{}%'.format(x)
    #                 )
    #             answer_table = basic_results_data[COMPARE_COLUMNS_ID].to_dict('records')
    #
    #     return answer_table
    #
    # @app_handle.callback(
    #     Output('flex-compare-ghg-results-table', 'data'),
    #     [
    #         Input('flex-country-input', 'value'),
    #         Input('flex-compare-input', 'value'),
    #         Input('flex-scenario-input', 'value'),
    #         Input('flex-country-store', 'data')
    #     ]
    # )
    # def flex_update_compare_ghg_results_table(country_sel, comp_sel, scenario, cur_data):
    #     """Display information and study's results for a country."""
    #     answer_table = []
    #     df_bau_ref = None
    #     country_iso = country_sel
    #     # in case of country_iso is a list of one element
    #     if np.shape(country_iso) and len(country_iso) == 1:
    #         country_iso = country_iso[0]
    #
    #     # extract the data from the selected scenario if a country was selected
    #     if country_iso is not None and comp_sel is not None:
    #         if scenario in SCENARIOS:
    #             df = pd.read_json(cur_data[scenario])
    #             df_comp = df.copy()
    #             df = df.loc[df.country_iso == country_sel]
    #             if comp_sel in REGIONS_NDC:
    #                 # compare the reference country to a region
    #                 if comp_sel != WORLD_ID:
    #                     df_comp = df_comp.loc[df_comp.region == REGIONS_NDC[comp_sel]]
    #                 df_comp = df_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(axis=0)
    #             else:
    #                 # compare the reference country to a country
    #                 df_comp = df_comp.loc[df_comp.country_iso == comp_sel]
    #             df = df.loc[df.country_iso == country_iso]
    #
    #             if scenario in [SE4ALL_SCENARIO, PROG_SCENARIO]:
    #                 # to compare greenhouse gas emissions with BaU scenario
    #                 df_bau = pd.read_json(cur_data[BAU_SCENARIO])
    #                 df_bau_ref = df_bau.loc[df_bau.country_iso == country_iso]
    #
    #                 if comp_sel in REGIONS_NDC:
    #                     # compare the reference country to a region
    #                     df_bau_comp = df_bau.loc[df_bau.region == REGIONS_NDC[comp_sel]]
    #                     df_bau_comp = df_bau_comp[EXO_RESULTS + ['pop_newly_electrified_2030']].sum(
    #                         axis=0)
    #                 else:
    #                     # compare the reference country to a country
    #                     df_bau_comp = df_bau.loc[df_bau.country_iso == comp_sel]
    #
    #             if df_bau_ref is None:
    #                 ghg_rows = [
    #                     'GHG (Mio tCO2)',
    #                     'GHG (TIER +1) (Mio tCO2)',
    #                     # 'GHG CUMUL'
    #                 ]
    #             else:
    #                 ghg_rows = [
    #                     'GHG (Mio tCO2)',
    #                     'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
    #                     'GHG (TIER +1) (Mio tCO2)',
    #                     'Saved from {}'.format(SCENARIOS_DICT[BAU_SCENARIO]),
    #                 ]
    #
    #             # gather the values of the results to display in the table
    #             ghg_res = np.squeeze(df[GHG].values).round(0)
    #             ghg2_res = np.squeeze(df[GHG_CAP].values).round(0)
    #
    #             comp_res = np.squeeze(df_comp[GHG].values).round(0)
    #             comp2_res = np.squeeze(df_comp[GHG_CAP].values).round(0)
    #
    #             if df_bau_ref is not None:
    #                 ghg_diff_res = ghg_res - np.squeeze(df_bau_ref[GHG].values).round(0)
    #                 ghg2_diff_res = ghg2_res - np.squeeze(df_bau_ref[GHG_CAP].values).round(0)
    #                 ghg_results_data = np.vstack([ghg_res, ghg_diff_res, ghg2_res, ghg2_diff_res])
    #             else:
    #                 ghg_results_data = np.vstack([ghg_res, ghg2_res])
    #
    #             if df_bau_ref is not None:
    #                 ghg_diff_res = comp_res - np.squeeze(df_bau_comp[GHG].values).round(0)
    #                 ghg2_diff_res = comp2_res - np.squeeze(df_bau_comp[GHG_CAP].values).round(0)
    #                 ghg_comp_data = np.vstack([comp_res, ghg_diff_res, comp2_res, ghg2_diff_res])
    #             else:
    #                 ghg_comp_data = np.vstack([comp_res, comp2_res])
    #
    #             total = np.nansum(ghg_results_data, axis=1)
    #             comp_total = np.nansum(ghg_comp_data, axis=1)
    #
    #             ghg_results_data = 100 * np.divide(
    #                 ghg_comp_data - ghg_results_data,
    #                 ghg_comp_data
    #             )
    #
    #             total = 100 * np.divide(
    #                 comp_total - total,
    #                 comp_total
    #             )
    #
    #             ghg_results_data = np.hstack([ghg_comp_data, ghg_results_data])
    #
    #             comp_ids = ['comp_{}'.format(c) for c in ELECTRIFICATION_OPTIONS]
    #             # prepare a DataFrame
    #             ghg_results_data = pd.DataFrame(
    #                 data=ghg_results_data,
    #                 columns=ELECTRIFICATION_OPTIONS + comp_ids
    #             )
    #             print(ghg_results_data)
    #             # sums of the rows
    #             ghg_results_data['total'] = pd.Series(comp_total)
    #             ghg_results_data['comp_total'] = pd.Series(total)
    #             # label of the table rows
    #             ghg_results_data['labels'] = pd.Series(ghg_rows)
    #             ghg_results_data.iloc[:, 0:8] = \
    #                 ghg_results_data.iloc[:, 0:8].applymap(
    #                     add_comma
    #                 )
    #             ghg_results_data[comp_ids + ['comp_total']] = \
    #                 ghg_results_data[comp_ids + ['comp_total']].applymap(
    #                     lambda x: '' if x == '' else '{}%'.format(x)
    #                 )
    #             answer_table = ghg_results_data[COMPARE_COLUMNS_ID].to_dict('records')
    #
    #     return answer_table

    @app_handle.callback(
        Output('flex-country-info-div', 'children'),
        [
            Input('flex-country-store', 'data')
        ]
    )
    def flex_update_country_info_div(country_data):

        divs = []
        country_iso = country_data.get('country_iso')

        # extract the data if a country was selected
        if country_iso is not None:
            df = pd.read_json(country_data['selection'])
            pop_2017 = df.pop_2017.values[0]
            name = df.country.values[0]
            image_filename = 'icons/{}.png'.format(country_iso)
            encoded_image = base64.b64encode(open(image_filename, 'rb').read())

            divs = [
                html.Div(
                    id='flex-results-info-header-div',
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
        Output('flex-country-basic-results-title', 'children'),
        [Input('flex-country-store', 'data')],
        [State('flex-scenario-input', 'value')]
    )
    def flex_country_basic_results_title(country_data, scenario):

        answer = 'Results'
        country_iso = country_data.get('country_iso')

        # extract the data if a country was selected
        if country_iso is not None:
            df = pd.read_json(country_data['selection'])
            answer = 'Results for {}: electrification options'.format(
                df.country.values[0])
        return answer

    # @app_handle.callback(
    #     Output('flex-compare-basic-results-title', 'children'),
    #     [
    #         Input('flex-country-input', 'value'),
    #         Input('flex-compare-input', 'value')
    #     ],
    #     [
    #         State('flex-scenario-input', 'value'),
    #         State('flex-country-store', 'data')]
    # )
    # def flex_compare_basic_results_title(country_iso, comp_sel, scenario, cur_data):
    #
    #     answer = 'Results'
    #     if scenario in SCENARIOS and comp_sel is not None:
    #         df = pd.read_json(cur_data[scenario])
    #         if comp_sel in REGIONS_NDC:
    #             comp_name = REGIONS_GPD[comp_sel]
    #         else:
    #             comp_name = df.loc[df.country_iso == comp_sel].country.values[0]
    #         answer = 'Results for {} and relative difference with {}'.format(
    #             comp_name,
    #             df.loc[df.country_iso == country_iso].country.values[0]
    #         )
    #     return answer


    # @app_handle.callback(
    #     Output('flex-general-info-div', 'children'),
    #     [Input('flex-scenario-input', 'value')]
    # )
    # def flex_update_scenario_description(scenario):
    #     return
    # @app_handle.callback(
    #     Output('flex-store', 'data'),
    #     [
    #         Input('flex-rise-grid-input', 'value'),
    #         Input('flex-rise-mg-input', 'value'),
    #         Input('flex-rise-shs-input', 'value'),
    #         Input('flex-min-tier-input', 'value')
    #     ],
    #     [State('flex-store', 'data')]
    # )
    # def flex_update_flex_store(
    #         rise_grid,
    #         rise_mg,
    #         rise_shs,
    #         min_tier_level,
    #         flex_data
    # ):
    #
    #     if rise_grid is not None:
    #         flex_data.update({'rise_grid': rise_grid})
    #     if rise_mg is not None:
    #         flex_data.update({'rise_mg': rise_mg})
    #     if rise_shs is not None:
    #         flex_data.update({'rise_shs': rise_shs})
    #     if min_tier_level is not None:
    #         flex_data.update({'min_tier_level': min_tier_level})
    #     return flex_data

    @app_handle.callback(
        Output('flex-country-store', 'data'),
        [Input('flex-country-input', 'value')],
        [
            State('flex-data-store', 'data'),
            State('flex-country-store', 'data')
        ]
    )
    def flex_update_flex_store(country_iso, cur_data, country_data):
        if country_iso is not None:
            df = pd.read_json(cur_data[SE4ALL_SCENARIO])
            df = df.loc[df.country_iso == country_iso]
            country_data.update({'selection': df.to_json()})
            country_data.update({'country_iso': country_iso})
        return country_data

    @app_handle.callback(
        Output('flex-rise-grid-input', 'value'),
        [Input('flex-country-store', 'data')]
    )
    def flex_update_rise_grid(country_data):
        answer = None
        if 'selection' in country_data:
            df = pd.read_json(country_data['selection'])
            answer = df.rise_grid
        return answer

    @app_handle.callback(
        Output('flex-rise-mg-input', 'value'),
        [Input('flex-country-store', 'data')]
    )
    def flex_update_rise_mg(country_data):
        answer = None
        if 'selection' in country_data:
            df = pd.read_json(country_data['selection'])
            answer = df.rise_mg
        return answer

    @app_handle.callback(
        Output('flex-rise-shs-input', 'value'),
        [Input('flex-country-store', 'data')]
    )
    def flex_update_rise_shs(country_data):
        answer = None
        if 'selection' in country_data:
            df = pd.read_json(country_data['selection'])
            answer = df.rise_shs
        return answer


    @app_handle.callback(
        Output('flex-tier-value', 'children'),
        [Input('flex-country-input', 'value')],
        [
            State('flex-scenario-input', 'value'),
            State('flex-data-store', 'data')]
    )
    def flex_update_tier_value_div(country_iso, scenario, cur_data):
        """Find the actual tier level of the country based on its yearly electricity consumption"""
        answer = ''
        if scenario in SCENARIOS and country_iso is not None:
            df = pd.read_json(cur_data[scenario])
            answer = '{}'.format(
                _find_tier_level(
                    df.loc[df.country_iso == country_iso]
                        .hh_yearly_electricity_consumption.values[0],
                    1
                )
            )
        return answer


if __name__ == '__main__':
    app.run_server(debug=True)
