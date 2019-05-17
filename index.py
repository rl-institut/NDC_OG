import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app_main import app, URL_BASEPATH
from app_layouts import intro_layout, static_layout, flex_layout

# the app and its options are defined in the main_app module
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# define the callbacks
static_layout.callbacks(app)

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    """Manage the url path between the different layouts"""
    if pathname == '/{}'.format(URL_BASEPATH) \
            or pathname == '/{}/'.format(URL_BASEPATH) \
            or pathname == '/' or pathname is None:
        return intro_layout.layout
    elif pathname == '/{}/{}'.format(URL_BASEPATH, static_layout.URL_PATHNAME):
        return static_layout.layout
    elif pathname == '/{}/{}'.format(URL_BASEPATH, flex_layout.URL_PATHNAME):
        return flex_layout.layout


if __name__ == '__main__':
    app.run_server(debug=True)
