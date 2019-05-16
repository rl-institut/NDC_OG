import dash_core_components as dcc
import dash_html_components as html

URL_PATHNAME = 'static'

layout = html.Div([
    html.H3('Static'),
    dcc.Link('Go back to index', href='/')
])
