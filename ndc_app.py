import numpy as np
import pandas as pd
import geopandas as gpd
import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from data_preparation import (
    SCENARIOS,
    BAU_SENARIO,
    SE4ALL_SHIFT_SENARIO,
    PROG_SENARIO,
    SCENARIOS_DICT,
    MG,
    GRID,
    SHS,
    HH_CAP,
    compute_ndc_results_from_raw_data,
    prepare_endogenous_variables,
    prepare_bau_data,
    prepare_se4all_data,
    prepare_prog_data,
    extract_results_scenario
)

from app_components import (
    country_div,
    scenario_div,
    controls_div,
    general_info_div
)


# A dict with the data for each scenario in json format
SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce).to_json() for sce in SCENARIOS
}
REGIONS_GPD = dict(WD='World', SA='South America', AF='Africa', AS='Asia')

REGIONS_NDC = dict(WD=['LA', 'SSA', 'DA'], SA='LA', AF='SSA', AS='DA')

VIEW_GENERAL = 'general'
VIEW_COUNTRY = 'specific'


# World countries maps
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

for col in world.columns:
    world[col] = world[col].astype(str)

world['text'] = world['name'] + '<br>' + 'Pop ' + world['pop_est'] + ' GDP ' + world[
    'gdp_md_est'] + \
                '<br>'


def country_hover_text(input_df):

    df = input_df.copy()
    return df.country + '<br>'
# Dummy variable for testing pie chart
world['results'] = np.random.rand(len(world.index), 4).tolist()

scl = [
    [0.0, 'rgb(242,240,247)'],
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
        lakecolor='rgb(255, 255, 255)',
        projection=dict(type='equirectangular')
    )
)

fig_map = go.Figure(data=data, layout=layout)


labels = list(SCENARIOS_DICT.keys())
values = [4500, 2500, 1053, 500]

piechart = go.Figure(data=[go.Pie(labels=labels, values=values)])

# Initializes dash app
app = dash.Dash(__name__)

app.layout = html.Div(
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
                    children=scenario_div(BAU_SENARIO, GRID)
                ),
                html.Div(
                    id='controls-div',
                    className='app__controls',
                    style={'display': 'none'},
                    children=controls_div(BAU_SENARIO),
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
                            id='region-selection-div',
                            className='app__dropdown',
                            children=[
                                dcc.Dropdown(
                                    id='region-input',
                                    options=[
                                        {'label': v, 'value': k}
                                        for k, v in REGIONS_GPD.items()
                                    ],
                                    value='SA'
                                )
                            ]
                        ),
                        html.Div(
                            id='logo-div',
                            className='app__logo',
                        ),
                    ]
                ),
                dcc.Dropdown(
                    id='country-input',
                    className='app__input__dropdown',
                    options=[],
                    value=None,
                    multi=False
                ),
                html.Div(
                    id='map-div',
                    className='app__map',
                    children=dcc.Graph(
                        id='map',
                        figure=fig_map,
                        style={'width': '90vh', 'height': '90vh'}
                    ),
                ),
                html.Div(
                    id='country-div',
                    className='app__country',
                    children=country_div(),
                )
            ]

        )
    ],
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

    region_name = REGIONS_GPD[region_id]
    df = pd.read_json(cur_data[scenario])
    df = df.loc[df.region == REGIONS_NDC[region_id]]
    z = df['pop_get_%s_2030' % elec_opt].div(df.pop_newly_electrified_2030, axis=0)

    fig['data'][0].update(
        {
            'locations': df['country_iso'],
            'z': z.astype(float),
            'text': country_hover_text(df),
            'colorbar': go.choropleth.ColorBar(title="2030<br>%% %s<br>access" % elec_opt),
        }
    )
    fig['layout']['geo'].update({'scope': region_name.lower()})
    return fig


@app.callback(
    Output('view-store', 'data'),
    [
        Input('region-input', 'value'),
        Input('country-input', 'value')
    ],
    [State('view-store', 'data')]
)
def update_view(region_id, country_sel, cur_view):
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
    return cur_view


@app.callback(
    Output('map-div', 'style'),
    [Input('view-store', 'data')],
    [State('map-div', 'style')]
)
def toggle_map_div_display(cur_view, cur_style):
    """Change the display of map-div between the app's views."""
    if cur_style is None:
        cur_style = {'app_view': VIEW_GENERAL}

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
def toggle_country_div_display(cur_view, cur_style):
    """Change the display of country-div between the app's views."""
    if cur_style is None:
        cur_style = {'app_view': VIEW_GENERAL}

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
        cur_style = {'app_view': VIEW_GENERAL}

    if cur_view['app_view'] == VIEW_GENERAL:
        cur_style.update({'display': 'none'})
    elif cur_view['app_view'] == VIEW_COUNTRY:
        cur_style.update({'display': 'flex'})
    return cur_style


@app.callback(
    Output('general-info-div', 'style'),
    [Input('view-store', 'data')],
    [State('general-info-div', 'style')]
)
def toggle_general_info_div_display(cur_view, cur_style):
    """Change the display of general-info-div between the app's views."""
    if cur_style is None:
        cur_style = {'app_view': VIEW_GENERAL}

    if cur_view['app_view'] == VIEW_GENERAL:
        cur_style.update({'display': 'flex'})
    elif cur_view['app_view'] == VIEW_COUNTRY:
        cur_style.update({'display': 'none'})
    return cur_style


@app.callback(
    Output('country-div', 'children'),
    [
        Input('country-input', 'value'),
        Input('scenario-input', 'value'),
        Input('mentis-gdp-input', 'value'),
        Input('mentis-mobile-money-input', 'value'),
        Input('tier-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_country_div_content(
        country_sel,
        scenario,
        gdp_class,
        mm_class,
        tier_level,
        cur_data
):
    """Display information and study's results for a country."""

    df = None
    country_iso = country_sel
    # in case of country_iso is a list of one element
    if np.shape(country_iso) and len(country_iso) == 1:
        country_iso = country_iso[0]

    # extract the data from the selected scenario if a country was selected
    if country_iso is not None:
        if scenario in SCENARIOS:
            df = pd.read_json(cur_data[scenario])
            df = df.loc[df.country_iso == country_iso]

            if scenario in [SE4ALL_SHIFT_SENARIO, PROG_SENARIO]:
                # TODO: only recompute the tier if it has changed (with context)
                if tier_level is not None:
                    df = prepare_endogenous_variables(
                        input_df=df,
                        tier_level=tier_level
                    )

            if scenario == SE4ALL_SHIFT_SENARIO:

                if gdp_class is not None:
                    df.loc[:, 'gdp_class'] = gdp_class
                if mm_class is not None:
                    df.loc[:, 'mobile_money_class'] = mm_class
                print(df[['shift_pop_grid_to_mg', 'shift_pop_grid_to_shs']+HH_CAP])

                # recompute the results after updating the shift drives
                df = prepare_se4all_data(input_df=df, fixed_shift_drives=False)
                df = extract_results_scenario(df, scenario)
                print(df[['shift_pop_grid_to_mg', 'shift_pop_grid_to_shs']+HH_CAP])

    return country_div(df)


@app.callback(
    Output('controls-div', 'children'),
    [Input('scenario-input', 'value')],
    [State('data-store', 'data')]
)
def update_controls_div_content(scenario, cur_data):
    """Display information and study's results for a country."""

    df = None
    if scenario is None:
        scenario = BAU_SENARIO

    return controls_div(scenario)


@app.callback(
    Output('mentis-gdp-input', 'value'),
    [
        Input('scenario-input', 'value'),
        Input('country-input', 'value'),
    ],
    [State('data-store', 'data')]
)
def update_mentis_gdp_input(scenario, country_sel, cur_data):

    answer = 0
    country_iso = country_sel
    # in case of country_iso is a list of one element
    if np.shape(country_iso) and len(country_iso) == 1:
        country_iso = country_iso[0]

    # extract the data from the selected scenario if a country was selected
    if country_iso is not None:
        if scenario in SCENARIOS:
            df = pd.read_json(cur_data[scenario]).set_index('country_iso')
            answer = df.loc[country_iso, 'gdp_class']
    return answer


@app.callback(
    Output('piechart', 'figure'),
    [Input('map', 'hoverData')],
    [State('piechart', 'figure')]
)
def update_piechart(selected_data, fig):
    if selected_data is not None:
        chosen = [point['location'] if point['pointNumber'] != 0 else None for point in
                  selected_data['points']]
        if chosen[0] is not None:
            country_code = chosen[0]

            df = world.loc[world.iso_a3 == country_code]
            fig['data'][0].update(
                {
                    'values': df['results'].values[0]
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
    Output('country-input', 'options'),
    [Input('region-input', 'value')],
    [
        State('scenario-input', 'value'),
        State('data-store', 'data')
    ]
)
def update_country_selection_options(region_id, scenario, cur_data):
    countries_in_region = []
    if scenario is not None:
        df = pd.read_json(cur_data[scenario])

        for idx, row in df.loc[df.region == REGIONS_NDC[region_id]].iterrows():
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


if __name__ == '__main__':
    app.run_server(debug=True)
