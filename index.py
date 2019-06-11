import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app_main import app, URL_BASEPATH, LOGOS
from app_layouts import intro_layout, static_layout, flex_layout

server = app.server

# the app and its options are defined in the main_app module
app.layout = html.Div(
    className='grid-y medium-grid-frame app_style',
    children=[
        dcc.Location(id='url', refresh=False),
        html.Div(
            id='header-div',
            className='cell shrink header header_style',
            children=[
                html.Div(
                    id='header-content',
                    className='grid-x grid-margin-x',
                    children=[
                        html.Div(
                            className='cell medium-3 text-justify',
                            children='NDC Off-Grid alternatives'
                        ),
                        html.Div(
                            className='cell medium-6 text-justify',
                            children='Visualization of New Electrification Scenarios by 2030 and the'
                                     ' Relevance of Off-Grid Components in the NDCs',
                        ),
                        html.Div(
                            className='cell medium-3 text-justify',
                            children=[
                                html.Img(
                                    src='data:image/png;base64,{}'.format(logo.decode()),
                                    style={'width': '90px'},
                                )
                                for logo in LOGOS
                            ],
                        )
                    ]
                ),
            ]
        ),
        html.Div(
            id='page-div',
            className='cell medium-10',
            children=[
                html.Div(id='page-content'),
            ]
        ),
        html.Div(
            id='footer-div',
            className='cell shrink footer',
            children=[
                html.Div(
                    id='footer-content',
                    className='grid-x grid-margin-x',
                    children=[
                        html.Div(
                            className='cell auto',
                            children=html.Img(
                                src='data:image/png;base64,{}'.format(logo.decode()),
                            )
                        )
                        for logo in LOGOS
                    ]
                )
            ]
        ),
    ]
)

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
