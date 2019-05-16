import dash_core_components as dcc
import dash_html_components as html

URL_PATHNAME = 'flex'

layout = html.Div([
    html.H3('Flex'),
    dcc.Link('Go back to index', href='/')
])
