import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app_main import app, URL_BASEPATH
from . import static_layout, flex_layout

layout = html.Div(
    id='intro-div',
    children=[
        html.H3(
            id='intro-title',
            children='Visualization of New Electrification Scenarios by 2030 and the'
                     ' Relevance of Off-Grid Components in the NDCs',
        ),
        html.Div(
            id='intro-text-div',
            children='Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written. '
                     'Here is a disclaimer which remains to be written',
        ),
        html.Div(
            id='intro-link-div',
            children=[
                dcc.Link(
                    id='intro-link-static',
                    className='intro__link',
                    children='Explore the scenarios',
                    href='/{}/{}'.format(URL_BASEPATH, static_layout.URL_PATHNAME)
                ),
                dcc.Link(
                    id='intro-link-flex',
                    className='intro__link',
                    children='Change inputs',
                    href='/{}/{}'.format(URL_BASEPATH, flex_layout.URL_PATHNAME)
                ),
            ]
        )
    ]
)


@app.callback(
    Output('app-1-display-value', 'children'),
    [Input('app-1-dropdown', 'value')])
def display_value(value):
    return 'You have selected "{}"'.format(value)