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
    FLEX_SCENARIO_NAME,
    SCENARIOS_DICT,
    SCENARIOS_NAMES,
    ELECTRIFICATION_OPTIONS,
    NO_ACCESS,
    RISE_INDICES,
    POP_GET,
    _find_tier_level,
    compute_ndc_results_from_raw_data,
    prepare_results_tables,
    prepare_scenario_data,
    extract_results_scenario,
    POP_RES,
    INVEST_RES,
    GHG_RES,
    GHG_ER_RES,
    RISE_SUB_INDICATOR_STRUCTURE
)

from .app_components import (
    results_div,
    controls_div,
    format_percent,
    round_digits,
    TABLES_LABEL_STYLING,
    BARPLOT_ELECTRIFICATION_COLORS,
    RES_COMPARE,
    TABLE_ROWS,
    TABLE_COLUMNS_ID,
    COMPARE_COLUMNS_ID,
    TABLE_COLUMNS_LABEL,
    REGIONS_NDC,
)

URL_PATHNAME = 'flex'


def extract_centroids(reg):
    """Load the longitude and latitude of countries per region."""
    if not isinstance(reg, list):
        reg = [reg]
    centroids = pd.read_csv('data/centroid.csv')
    return centroids.loc[centroids.region.isin(reg)].copy()


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

RISE_SUB_INDICATOR_SCORES = pd.read_csv('data/RISE_subindicators_country.csv')

list_countries_dropdown = []
DF = pd.read_json(SCENARIOS_DATA[SE4ALL_SCENARIO])
DF = DF.sort_values('country')
for idx, row in DF.iterrows():
    list_countries_dropdown.append({'label': row['country'], 'value': row['country_iso']})


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

# colors for hightlight of comparison
COLOR_BETTER = '#218380'
COLOR_WORSE = '#8F2D56'

fig_map = go.Figure(data=data, layout=layout)

layout = html.Div(
    id='flex-main-div',
    children=[
        dcc.Store(
            id='flex-store',
            storage_type='session',
            data=SCENARIOS_DATA.copy()
        ),
        dcc.Store(
            id='flex-view-store',
            storage_type='session',
            data={
                'app_view': VIEW_COUNTRY_SELECT,
                'sub_indicators_view': '',
                'sub_indicators_change': True
            }
        ),
        dcc.Store(
            id='flex-rise-store',
            storage_type='session',
            data={}
        ),
        html.Div(
            id='flex-main-content',
            className='grid-x',
            children=[
                html.Div(
                    id='flex-main-head-div',
                    className='cell',
                    children=html.Div(
                        id='flex-main-head-content',
                        className='grid-x grid-padding-x',
                        children=[
                            html.Div(
                                id='flex-left-header-div',
                                className='cell medium-6',
                                children=[
                                    html.Div(
                                        id='flex-general-info-div',
                                        className='scenario__info',
                                        children=[
                                            html.H4('Custom Scenarios'),
                                            '''Complementary to the static evaluation of the modelled scenarios, the *Off-Grid Tool* allows the exploration and creation of your own scenarios. The universal-Electricity-Access scneario and the progressive-Off-Grid scenraio are based on the RISE indicators, reflecting countries' regulatory framework conditions. Through the alteration of RISE subindicators, one can simulate how technology-specific framework changes may affect a country's electrification development until 2030.'''
                                        ]
                                    ),
                                ]
                            ),
                            html.Div(
                                id='flex-right-header-div',
                                className='cell medium-6',
                                children=[
                                    html.Div(
                                        id='flex-scenario-input-div',
                                        className='grid-x input-div',
                                        children=[
                                            html.Div(
                                                id='flex-scenario-label',
                                                className='cell medium-3',
                                                children='Explore a scenario:'
                                            ),
                                            html.Div(
                                                id='flex-scenario-input-wrapper',
                                                className='cell medium-9',
                                                children=dcc.Dropdown(
                                                    id='flex-scenario-input',
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
                                        id='flex-country-input-div',
                                        title='country selection description',
                                        className='grid-x input-div',
                                        children=[
                                            html.Div(
                                                id='flex-country-label',
                                                className='cell medium-3',
                                                children='Country:'
                                            ),
                                            html.Div(
                                                id='flex-country-input-wrapper',
                                                className='cell medium-9',
                                                children=dcc.Dropdown(
                                                    id='flex-country-input',
                                                    options=list_countries_dropdown,
                                                    value=None,
                                                    multi=False
                                                )
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id='flex-specific-info-div',
                                        className='instructions',
                                        children=[
                                            html.H4('What you can do'),
                                            '''Select a starting scenario and choose a country from the dropdown menu. Select one of the technology-specific RISE indicators to customize its subindicators (RISE Grid, RISE MG, RISE SHS).'''
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ),
                html.Div(
                    id='flex-controls-div',
                    className='cell',
                    children=html.Div(
                        className='grid-x',
                        children=controls_div(),
                    )
                ),
                html.Div(
                    id='flex-main-results-div',
                    className='cell',
                    children=html.Div(
                        id='flex-main-results-contents',
                        className='grid-x align-center',
                        children=[
                            results_div(RES_COMPARE, res_category, 'flex-')
                            for res_category in [POP_RES, INVEST_RES, GHG_RES]
                        ]
                    ),
                ),
            ]
        ),
    ]
)


def result_title_callback(app_handle, result_category):

    id_name = 'flex-{}-{}'.format(RES_COMPARE, result_category)

    if result_category == POP_RES:
        description = 'Electrification Mix {}'
    elif result_category == INVEST_RES:
        description = 'Initial Investments Needed {} (in billion USD)'
    else:
        description = 'Cumulated GHG Emissions (2017-2030) {} (in million tons CO2)'

    @app_handle.callback(
        Output('{}-results-title'.format(id_name), 'children'),
        [
            Input('flex-store', 'data'),
            Input('flex-scenario-input', 'value')
        ],
        [State('flex-country-input', 'value')]
    )
    def flex_update_title(cur_data, scenario, country_iso):

        answer = 'Results'
        if scenario in SCENARIOS and country_iso is not None:
            country = cur_data.get('country_name')
            answer = '{}: Comparison of {}'.format(
                country,
                description.format(
                    'between {} and {} scenarios'.format(
                        FLEX_SCENARIO_NAME,
                        SCENARIOS_DICT[scenario]
                    )
                )
            )
        return answer

    flex_update_title.__name__ = 'flex_update_%s_title' % id_name
    return flex_update_title


def table_title_callback(app_handle, result_category):

    id_name = 'flex-{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-results-table-title'.format(id_name), 'children'),
        [Input('flex-scenario-input', 'value')],
    )
    def update_title(scenario):

        answer = 'Detailed results'
        if scenario in SCENARIOS:
            answer = 'Detailed Results'

        return answer

    update_title.__name__ = 'update_%s_title' % id_name
    return update_title


def compare_barplot_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = 'flex-{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-barplot'.format(id_name), 'figure'),
        [
            Input('{}-barplot-yaxis-input'.format(id_name), 'value'),
            Input('flex-store', 'data'),
            Input('flex-scenario-input', 'value'),
        ],
        [
            State('flex-country-input', 'value'),
            State('{}-barplot'.format(id_name), 'figure')
        ]
    )
    def flex_update_barplot(y_sel, cur_data, scenario, country_iso, fig):

        if y_sel is None:
            idx_y = 0
        else:
            idx_y = TABLE_ROWS[result_category].index(y_sel)

        if scenario is not None and country_iso is not None:

            df_flex = pd.read_json(cur_data[SE4ALL_FLEX_SCENARIO])
            df_comp = pd.read_json(cur_data[scenario])
            # narrow to the country's results
            df_flex = df_flex.loc[df_flex.country_iso == country_iso]
            df_comp = df_comp.loc[df_comp.country_iso == country_iso]

            flex_results_data = prepare_results_tables(
                df_flex,
                SE4ALL_FLEX_SCENARIO,
                result_category
            )
            comp_results_data = prepare_results_tables(df_comp, scenario, result_category)

            x = [opt.upper() for opt in ELECTRIFICATION_OPTIONS] + [NO_ACCESS]
            y_flex = flex_results_data[idx_y]
            y_comp = comp_results_data[idx_y]

            fs = 12

            fig.update(
                {'data': [
                    go.Bar(
                        x=x,
                        y=y_flex,
                        text=[FLEX_SCENARIO_NAME for i in range(4)],
                        name=SE4ALL_FLEX_SCENARIO,
                        showlegend=False,
                        insidetextfont={'size': fs, 'color': 'white'},
                        textposition='inside',
                        marker=dict(
                            color=list(BARPLOT_ELECTRIFICATION_COLORS.values())
                        ),
                        hoverinfo='y+text'
                    ),
                    go.Bar(
                        x=x,
                        y=y_comp,
                        text=[SCENARIOS_DICT[scenario] for i in range(4)],
                        name=scenario,
                        showlegend=False,
                        insidetextfont={'size': fs, 'color': 'white'},
                        textposition='inside',
                        marker=dict(
                            color=['#a062d0', '#9ac1e5', '#f3a672', '#cccccc']
                        ),
                        hoverinfo='y+text'
                    ),
                ]
                }
            )
        return fig

    flex_update_barplot.__name__ = 'flex_update_%s_barplot' % id_name
    return flex_update_barplot


def compare_table_callback(app_handle, result_category):
    """Generate a callback for input components."""

    id_name = 'flex-{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'data'),
        [
            Input('flex-store', 'data'),
            Input('flex-scenario-input', 'value'),
        ],
        [State('flex-country-input', 'value')]
    )
    def flex_update_table(cur_data, scenario, country_iso):
        """Display information and study's results comparison between countries."""
        answer_table = []

        result_cat = result_category

        # extract the data from the selected scenario if a country was selected
        if scenario is not None and country_iso is not None:

            df_flex = pd.read_json(cur_data[SE4ALL_FLEX_SCENARIO])
            df_comp = pd.read_json(cur_data[scenario])
            # narrow to the country's results
            df_flex = df_flex.loc[df_flex.country_iso == country_iso]
            df_comp = df_comp.loc[df_comp.country_iso == country_iso]

            ghg_er = False
            if result_cat == GHG_RES:
                ghg_er = True
                result_cat = GHG_ER_RES

            flex_results_data = prepare_results_tables(
                df_flex,
                SE4ALL_FLEX_SCENARIO,
                result_cat,
                ghg_er
            )
            comp_results_data = prepare_results_tables(
                df_comp,
                scenario,
                result_cat,
                ghg_er
            )

            flex_total = np.nansum(flex_results_data, axis=0)
            comp_total = np.nansum(comp_results_data, axis=0)

            results_data = np.hstack([flex_results_data, comp_results_data])

            comp_ids = ['comp_{}'.format(c) for c in ELECTRIFICATION_OPTIONS] \
                + ['comp_{}'.format(NO_ACCESS)]
            # prepare a DataFrame
            results_data = pd.DataFrame(
                data=results_data,
                columns=ELECTRIFICATION_OPTIONS + [NO_ACCESS] + comp_ids
            )
            # sums of the rows
            results_data['total'] = pd.Series(flex_total)
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

    flex_update_table.__name__ = 'flex_update_%s_table' % id_name
    return flex_update_table


def compare_table_columns_title_callback(app_handle, result_category):

    id_name = 'flex-{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'columns'),
        [Input('flex-scenario-input', 'value')]
    )
    def flex_update_table_columns_title(scenario):
        columns_ids = []
        if scenario is not None:
            flex_sce = FLEX_SCENARIO_NAME
            comp_sce = SCENARIOS_DICT[scenario]
            table_columns = TABLE_COLUMNS_ID[result_category]
            for col in table_columns:
                if col != 'labels':
                    columns_ids.append(
                        {'name': [TABLE_COLUMNS_LABEL[col], flex_sce], 'id': col}
                    )
                    columns_ids.append(
                        {'name': [TABLE_COLUMNS_LABEL[col], comp_sce], 'id': 'comp_{}'.format(col)}
                    )
                else:
                    columns_ids.append({'name': TABLE_COLUMNS_LABEL[col], 'id': col})
        return columns_ids

    flex_update_table_columns_title.__name__ = 'flex_update_%s_table_columns_title' % id_name
    return flex_update_table_columns_title


def compare_table_styling_callback(app_handle, result_category):

    id_name = 'flex-{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-results-table'.format(id_name), 'style_data_conditional'),
        [Input('{}-results-table'.format(id_name), 'data')],
        [
            State('{}-results-table'.format(id_name), 'style_data_conditional'),
            State('flex-country-input', 'value')
        ]
    )
    def flex_update_table_styling(cur_data, cur_style, country_iso):
        if country_iso is not None:
            table_data = pd.DataFrame.from_dict(cur_data)
            table_columns = TABLE_COLUMNS_ID[result_category]

            col_ref = table_columns[1:]
            col_comp = ['comp_{}'.format(col) for col in col_ref]
            table_data = table_data[col_ref + col_comp].applymap(
                lambda x: 0 if x == '' else float(x.replace(',', '').replace('%', '')))
            ref = table_data[col_ref]
            comp = table_data[col_comp]

            compare_results_styling = []
            for j, col in enumerate(col_ref):
                for i in range(len(ref.index)):
                    apply_condition = True
                    if ref.iloc[i, j] > comp.iloc[i, j]:
                        color = COLOR_BETTER
                        font = 'bold'
                        if result_category == GHG_RES:
                            if np.mod(i, 2) == 0:
                                color = COLOR_WORSE
                                font = 'normal'
                    elif ref.iloc[i, j] < comp.iloc[i, j]:
                        color = COLOR_WORSE
                        font = 'normal'
                        if result_category == GHG_RES:
                            if np.mod(i, 2) == 0:
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

    flex_update_table_styling.__name__ = 'flex_update_%s_table_styling' % id_name
    return flex_update_table_styling


def toggle_results_div_callback(app_handle, result_category):

    id_name = 'flex-{}-{}'.format(RES_COMPARE, result_category)

    @app_handle.callback(
        Output('{}-div'.format(id_name), 'style'),
        [Input('flex-view-store', 'data')],
        [State('{}-div'.format(id_name), 'style')]
    )
    def toggle_results_div_display(cur_view, cur_style):
        """Change the display of results-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}

        if cur_view['app_view'] in [VIEW_COUNTRY_SELECT]:
            cur_style.update({'display': 'none'})
        else:
            cur_style = {}
        return cur_style

    toggle_results_div_display.__name__ = 'flex-toggle_%s_display' % id_name
    return toggle_results_div_display


def rise_slider_callback(app_handle, id_name):

    @app_handle.callback(
        Output('flex-rise-{}-value'.format(id_name), 'children'),
        [Input('flex-rise-{}-input'.format(id_name), 'value')]
    )
    def display_slider_value(slider_val):
        """Change the display of results-div between the app's views."""

        answer = '0'
        if slider_val is not None:
            answer = '{:.2f}'.format(slider_val)

        return answer

    display_slider_value.__name__ = 'display_slider_%s_value' % id_name
    return display_slider_value


def rise_sub_indicator_display_callback(app_handle, id_name):

    @app_handle.callback(
        Output('flex-rise-sub-{}-div'.format(id_name), 'style'),
        [Input('flex-view-store', 'data')],
        [State('flex-rise-sub-{}-div'.format(id_name), 'style')]
    )
    def toggle_rise_sub_indicator_display(cur_view, cur_style):
        """Change the display of results-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}
        if cur_view['sub_indicators_view'] == id_name:
            if cur_view['sub_indicators_change']:
                cur_style = {}
            else:
                if cur_style['display'] == 'none':
                    cur_style = {}
                else:
                    cur_style.update({'display': 'none'})
        else:
            cur_style.update({'display': 'none'})
        return cur_style

    toggle_rise_sub_indicator_display.__name__ = 'toggle_rise_%s_sub_indicator_display' % id_name
    return toggle_rise_sub_indicator_display


def rise_sub_indicator_button_style_callback(app_handle, id_name):

    @app_handle.callback(
        Output('flex-rise-{}-btn'.format(id_name), 'style'),
        [Input('flex-view-store', 'data')],
        [State('flex-rise-{}-btn'.format(id_name), 'style')]
    )
    def rise_update_button_style(cur_view, cur_style):
        """Change the display of results-div between the app's views."""
        if cur_style is None:
            cur_style = {'fontWeight': 'normal'}
        if cur_view['sub_indicators_view'] == id_name:
            cur_style.update({'fontWeight': 'bold'})
        else:
            cur_style.update({'fontWeight': 'normal'})
        return cur_style

    rise_update_button_style.__name__ = 'rise_%s_update_button_style' % id_name
    return rise_update_button_style


def rise_update_scores(app_handle, id_name):

    @app_handle.callback(
        Output('flex-rise-{}-input'.format(id_name), 'value'),
        [
            Input('flex-country-input', 'value'),
            Input('flex-rise-store', 'data')
        ],
        [
            State('flex-store', 'data'),
            State('flex-view-store', 'data'),
            State('flex-rise-{}-input'.format(id_name), 'value')
        ]
    )
    def flex_update_rise_value(country_iso, cur_rise_data, cur_data, cur_view, cur_val):
        ctx = dash.callback_context
        answer = cur_val
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            # trigger comes from selecting a country
            if 'country-input' in prop_id:
                if country_iso is not None:
                    df = pd.read_json(cur_data[SE4ALL_SCENARIO])
                    answer = df.loc[
                        df.country_iso == country_iso, 'rise_{}'.format(id_name)
                    ].values[0]
            if 'rise-store' in prop_id:
                answer = cur_rise_data.get(id_name)

        if answer is None:
            answer = cur_val
        return answer

    flex_update_rise_value.__name__ = 'flex_update_rise_%s_value' % id_name
    return flex_update_rise_value


def rise_update_set_all_upon_country_selection(app_handle, id_name):
    """When a country is selected, the rise subindicators values are displayed

    :param app_handle:
    :param id_name:
    :return:
    """
    @app_handle.callback(
        Output('flex-rise-{}-general-toggle'.format(id_name), 'value'),
        [Input('flex-country-input', 'value')]
    )
    def flex_update_set_all(_):
        return -1  # correspond to default value of the dropdown

    flex_update_set_all.__name__ = 'flex_update_set_all_{}'.format(id_name)
    return flex_update_set_all


def rise_update_subscore_values(app_handle, id_name, p, q):
    """Update the values of the RISE subindicators upon country selection

        flex-country-input triggers the callback rise_update_set_all_upon_country_selection
        which triggers this call back
    :param app_handle: handle to the dash app
    :param id_name: one the ELECTRIFICATION_OPTIONS
    :param p: the index of the rise sub-indicator's group
    :param q: the index of the question within the rise sub-indicator's group
    :return: callback function
    """
    @app_handle.callback(
        Output('flex-rise-{}-sub-group{}-{}-toggle'.format(id_name, p, q), 'value'),
        [
            Input('flex-rise-{}-general-toggle'.format(id_name), 'value'),
        ],
        [
            State('flex-country-input', 'value'),
            State('flex-rise-store', 'data')
        ]
    )
    def flex_update_subscore_value(set_all, country_iso, cur_rise_data):
        answer = 0
        if set_all is not None and country_iso is not None:
            if set_all == 1:
                answer = float(1./RISE_SUB_INDICATOR_STRUCTURE[id_name][p])
            elif set_all == 0:
                answer = 0
            elif set_all == -1:
                # select country
                sub_df = RISE_SUB_INDICATOR_SCORES.loc[
                    RISE_SUB_INDICATOR_SCORES.country_iso == country_iso
                    ]
                # select electrification option
                sub_df = sub_df.loc[sub_df.indicator == 'rise_{}'.format(id_name)]
                # select sub-indicator group
                sub_group = sub_df.sub_indicator_group.unique()[p]
                sub_df = sub_df.loc[sub_df.sub_indicator_group == sub_group]
                # select question within sub-indicator group
                value = sub_df.iloc[q].value

                if value:
                    answer = float(1. / value)
        return answer

    flex_update_subscore_value.__name__ = 'flex_update_subscore_value_{}_{}_{}'.format(
        id_name,
        p,
        q
    )
    return flex_update_subscore_value


def callbacks(app_handle):

    for res_cat in [POP_RES, INVEST_RES, GHG_RES]:
        result_title_callback(app_handle, res_cat)
        compare_barplot_callback(app_handle, res_cat)
        compare_table_callback(app_handle, res_cat)
        compare_table_columns_title_callback(app_handle, res_cat)
        compare_table_styling_callback(app_handle, res_cat)
        toggle_results_div_callback(app_handle, res_cat)
        table_title_callback(app_handle, res_cat)

    for opt in ELECTRIFICATION_OPTIONS:
        rise_slider_callback(app_handle, opt)
        rise_sub_indicator_display_callback(app_handle, opt)
        rise_update_scores(app_handle, opt)
        rise_sub_indicator_button_style_callback(app_handle, opt)
        rise_update_set_all_upon_country_selection(app_handle, opt)
        for p, m in enumerate(RISE_SUB_INDICATOR_STRUCTURE[opt]):
            for q in range(m):
                rise_update_subscore_values(app_handle, opt, p, q)

    @app_handle.callback(
        Output('flex-view-store', 'data'),
        [
            Input('flex-country-input', 'value'),
            Input('flex-rise-grid-btn', 'n_clicks'),
            Input('flex-rise-mg-btn', 'n_clicks'),
            Input('flex-rise-shs-btn', 'n_clicks'),
        ],
        [State('flex-view-store', 'data')]
    )
    def flex_update_view(country_sel, grid_sub, mg_sub, shs_sub, cur_view):
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

            if 'flex-rise' in prop_id:
                id_name = prop_id.split('-')[2]
                if id_name == cur_view['sub_indicators_view']:
                    indicator_change = False
                    id_name = ''
                else:
                    indicator_change = True

                cur_view.update({'sub_indicators_view': id_name})
                cur_view.update({'sub_indicators_change': indicator_change})
        return cur_view

    @app_handle.callback(
        Output('flex-rise-sub-indicators-div', 'style'),
        [Input('flex-view-store', 'data')],
        [State('flex-rise-sub-indicators-div', 'style')]
    )
    def toggle_rise_sub_indicator_div_display(cur_view, cur_style):
        """Change the display of results-div between the app's views."""
        if cur_style is None:
            cur_style = {'display': 'none'}
        if cur_view['sub_indicators_view'] in ELECTRIFICATION_OPTIONS:
            cur_style = {}
        else:
            cur_style.update({'display': 'none'})
        return cur_style

    @app_handle.callback(
        Output('flex-store', 'data'),
        [
            Input('flex-rise-grid-input', 'value'),
            Input('flex-rise-mg-input', 'value'),
            Input('flex-rise-shs-input', 'value'),
            Input('flex-min-tier-mg-input', 'value'),
            Input('flex-min-tier-shs-input', 'value')
        ],
        [
            State('flex-country-input', 'value'),
            State('flex-store', 'data')
        ]
    )
    def flex_update_flex_store(
            rise_grid,
            rise_mg,
            rise_shs,
            min_tier_mg_level,
            min_tier_shs_level,
            country_iso,
            flex_data
    ):
        """Recompute the exogenous results with the updated RISE scores"""
        if rise_grid is not None:
            flex_data.update({'rise_grid': rise_grid})
        if rise_mg is not None:
            flex_data.update({'rise_mg': rise_mg})
        if rise_shs is not None:
            flex_data.update({'rise_shs': rise_shs})
        if min_tier_mg_level is not None:
            flex_data.update({'min_tier_mg_level': min_tier_mg_level})
        if min_tier_shs_level is not None:
            flex_data.update({'min_tier_shs_level': min_tier_shs_level})

        if country_iso is not None:
            min_tier_mg_level = flex_data.get('min_tier_mg_level')
            # Load data from csv
            df = pd.read_json(flex_data[SE4ALL_SCENARIO])
            for opt in RISE_INDICES:
                if opt in flex_data:
                    df.loc[df.country_iso == country_iso, opt] = flex_data[opt]
            # restrict recalculation to one country to save time
            df = df.loc[df.country_iso == country_iso]
            # Compute endogenous results for the given scenario
            df = prepare_scenario_data(
                df,
                SE4ALL_SCENARIO,
                min_tier_mg_level,
                prepare_endogenous=True
            )
            # Compute the exogenous results
            df = extract_results_scenario(df, SE4ALL_SCENARIO, min_tier_mg_level)
            flex_data.update({SE4ALL_FLEX_SCENARIO: df.to_json()})
            flex_data.update({'country_name': df.country.values[0]})

        return flex_data

    # prepare the inputs of the RISE sub indicators
    sub_indicators_inputs = []
    sub_indicators_num = {}
    num = 0
    for opt in ELECTRIFICATION_OPTIONS:
        sub_indicators_num[opt] = [num]
        for p, m in enumerate(RISE_SUB_INDICATOR_STRUCTURE[opt]):
            for q in range(m):
                sub_indicators_inputs.append(
                    Input('flex-rise-{}-sub-group{}-{}-toggle'.format(opt, p, q), 'value')
                )
                num = num + 1
        sub_indicators_num[opt].append(num)

    @app_handle.callback(
        Output('flex-rise-store', 'data'),
        sub_indicators_inputs
    )
    def flex_update_rise_sub_indicators(*args):
        """Change the display of results-div between the app's views."""

        cur_rise_data = {}

        for id_name in ELECTRIFICATION_OPTIONS:

            # find the position of the sub-indicators values in the arguments' list
            idx_start, idx_end = sub_indicators_num[id_name]
            sub_indicator_values = args[idx_start:idx_end]

            rise_score = 0
            idx = 0
            n_sub_groups = len(RISE_SUB_INDICATOR_STRUCTURE[id_name])
            for j, n in enumerate(RISE_SUB_INDICATOR_STRUCTURE[id_name]):
                sub_indicator_value = 0
                for i in range(n):
                    sub_indicator_value = sub_indicator_value + sub_indicator_values[idx]
                    idx = idx + 1
                rise_score = rise_score + sub_indicator_value / n_sub_groups
            rise_score = (100 * rise_score)

            # round the total score to 100 if it was 99.999999 due to floating point error
            if 100 - rise_score < 1e-5:
                rise_score = 100
            cur_rise_data[id_name] = round(rise_score, 2)
        return cur_rise_data


if __name__ == '__main__':
    app.run_server(debug=True)
