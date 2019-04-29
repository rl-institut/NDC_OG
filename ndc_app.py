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
    MG,
    GRID,
    SHS,
    ELECTRIFICATION_DICT,
    MENTI_DRIVES,
    POP_GET,
    compute_ndc_results_from_raw_data,
    prepare_endogenous_variables,
    prepare_se4all_data,
    extract_results_scenario
)

from app_components import (
    country_div,
    scenario_div,
    controls_div,
    general_info_div,
    callback_generator
)


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

# A dict with the data for each scenario in json format
SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce).to_json() for sce in SCENARIOS
}

SCENARIOS_DATA.update(
    {reg: extract_centroids(REGIONS_NDC[reg]).to_json() for reg in REGIONS_NDC}
)


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

    )
]


centroid = pd.read_csv('data/centroid.csv')

points = [
    go.Scattergeo(
        lon=centroid['Longitude'],
        lat=centroid['Latitude'],
        text=centroid['country_iso'],
        marker=go.scattergeo.Marker(
            size=25,
            color='black',
            line=go.scattergeo.marker.Line(width=0)
        ),
    )
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


fig_map = go.Figure(data=data + points, layout=layout)


PIECHART_LABELS = list(ELECTRIFICATION_DICT.values())

piechart = go.Figure(data=[go.Pie(labels=PIECHART_LABELS, values=[4500, 2500, 1053], sort=False)])

# Initializes dash app
app = dash.Dash(__name__)

app.title = 'NDC visualisation'

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
    """Plot color map of the percentage of people with a given electrification option."""

    # load the data of the scenario
    df = pd.read_json(cur_data[scenario])

    centroids = pd.read_json(cur_data[region_id])

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

    fig['data'][1].update(
        {
            'lon': centroids['Longitude'],
            'lat': centroids['Latitude'],
            'text': centroids['country_iso'],
            'geo': geo
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
        Input('mentis-weight-input', 'value'),
        Input('mentis-gdp-input', 'value'),
        Input('mentis-mobile-money-input', 'value'),
        Input('mentis-ease-doing-business-input', 'value'),
        Input('mentis-corruption-input', 'value'),
        Input('mentis-weak-grid-input', 'value'),
        Input('rise-mg-input', 'value'),
        Input('rise-shs-input', 'value'),
        Input('tier-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_country_div_content(
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

            if scenario in [SE4ALL_FLEX_SCENARIO, SE4ALL_SCENARIO, PROG_SCENARIO]:
                # TODO: only recompute the tier if it has changed (with context)
                if tier_level is not None:
                    df = prepare_endogenous_variables(
                        input_df=df,
                        tier_level=tier_level
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

    return country_div(df)


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


if __name__ == '__main__':
    app.run_server(debug=True)
