import numpy as np
import pandas as pd
import geopandas as gpd
import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objs as go
from data_preparation import (
    SCENARIOS,
    BAU_SENARIO,
    SE4ALL_SHIFT_SENARIO,
    PROG_SENARIO,
    compute_ndc_results_from_raw_data
)

from app_components import country_div

# Input from the user
SCENARIOS_DICT = {
    BAU_SENARIO: 'BaU',
    SE4ALL_SHIFT_SENARIO: 'SE4All',
    PROG_SENARIO: 'prOG',
    # 'indiv': 'Individual'
}
# A dict with the data for each scenario in json format
SCENARIOS_DATA = {
    sce: compute_ndc_results_from_raw_data(sce).to_json() for sce in SCENARIOS
}
REGIONS = dict(WD='World', SA='South America', AF='Africa', AS='Asia')

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
            data={'view': VIEW_GENERAL}
        ),
        html.Div(
            id='controls-div',
            className='app__container',
            children=[
                html.Div(
                    id='senario-div',
                    className='app__input',
                    children=[
                        html.Div(
                            id='senario-label',
                            className='app__input__label',
                            children='Senario'
                        ),
                        dcc.Dropdown(
                            id='scenario-input',
                            className='app__input__dropdown',
                            options=[
                                {'label': SCENARIOS_DICT[k], 'value': k}
                                for k in SCENARIOS_DICT
                            ],
                            value='bau',
                        ),
                    ]
                ),
                html.Div(
                    id='rise-shs-div',
                    className='app__input__slider',
                    children=[
                        html.Div(
                            id='rise-shs-label',
                            className='app__input__label',
                            children='RISE-SHS'
                        ),
                        daq.Slider(
                            id='rise-shs-input',
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
                    children=[
                        html.Div(
                            id='rise-label',
                            className='app__input__label',
                            children='RISE-MG'
                        ),
                        daq.Slider(
                            id='rise-mg-input',
                            min=0,
                            max=100,
                            value=67,
                            handleLabel={
                                "showCurrentValue": True, "label": "VALUE"},
                            step=1,
                        ),
                    ]
                ),
                html.Div(
                    id='framework-div',
                    className='app__input__slider',
                    children=[
                        html.Div(
                            id='framework-label',
                            className='app__input__label',
                            children='Framework'
                        ),
                        daq.Slider(
                            id='framework-input',
                            min=0,
                            max=10,
                            value=4,
                            handleLabel={
                                "showCurrentValue": True, "label": "VALUE"},
                            step=1,
                        ),
                    ]
                ),
                html.Div(
                    id='tier-div',
                    className='app__input',
                    children=[
                        html.Div(
                            id='tier-label',
                            className='app__input__label',
                            children='TIER'
                        ),
                        daq.NumericInput(
                            id='tier-input',
                            value=2
                        ),
                    ]
                ),
                html.Div(
                    id='invest-div',
                    className='app__input',
                    children=[
                        html.Div(
                            id='invest-label',
                            className='app__input__label',
                            children='Invest'
                        ),
                        daq.NumericInput(
                            id='invest-input',
                            label='USD/kW',
                            labelPosition='right'
                        ),
                    ]
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
            ],
        ),
        html.Div(
            id='visualization-div',
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
                                        {'label': REGIONS[k], 'value': k}
                                        for k in REGIONS
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
    [Input('region-input', 'value')],
    [State('map', 'figure')]
)
def update_map(region_id, fig):

    region_name = REGIONS[region_id]

    df = world.loc[world.continent == region_name]

    fig['data'][0].update(
        {
            'locations': df['iso_a3'],
            'z': df['pop_est'].astype(float),
            'text': df['text'],
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
    print(ctx)
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id']
        # trigger comes from clicking on a country
        if 'country-input' in prop_id:
            if country_sel:
                cur_view.update({'view': VIEW_COUNTRY})
            else:
                cur_view.update({'view': VIEW_GENERAL})

        # trigger comes from selecting a region
        elif 'region-input' in prop_id:
            cur_view.update({'view': VIEW_GENERAL})
    return cur_view


@app.callback(
    Output('map-div', 'style'),
    [Input('view-store', 'data')],
    [State('map-div', 'style')]
)
def toggle_map_div_display(cur_view, cur_style):
    """Change the display of map-div between the app's views."""
    if cur_style is None:
        cur_style = {'view': VIEW_GENERAL}

    if cur_view['view'] == VIEW_GENERAL:
        cur_style.update({'display': 'flex'})
    elif cur_view['view'] == VIEW_COUNTRY:
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
        cur_style = {'view': VIEW_GENERAL}

    if cur_view['view'] == VIEW_GENERAL:
        cur_style.update({'display': 'none'})
    elif cur_view['view'] == VIEW_COUNTRY:
        cur_style.update({'display': 'flex'})
    return cur_style


@app.callback(
    Output('country-div', 'children'),
    [
        Input('country-input', 'value'),
        Input('scenario-input', 'value')
    ],
    [State('data-store', 'data')]
)
def update_country_div_content(country_sel, scenario, cur_data):
    """Display information and study's results for a country."""

    df = None
    country_iso = country_sel
    # in case of country_iso is a list of one element
    if np.shape(country_iso) and len(country_iso) == 1:
        country_iso = country_iso[0]

    # extract the data from the selected scenario if a country was selected
    if country_iso is not None:
        if scenario in SCENARIOS:
            df = pd.read_json(cur_data[scenario]).set_index('country_iso')

    return country_div(df, country_iso)


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
