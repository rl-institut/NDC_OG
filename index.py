import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app_main import app, server, URL_BASEPATH, LOGOS, HDR_LOGO
from app_layouts import intro_layout, static_layout, flex_layout

server = server

# the app and its options are defined in the main_app module
app.layout = html.Div(
    className='grid-x app_style',
    children=[
        dcc.Location(id='url', refresh=False),
        html.Div(
            id='header-div',
            className='cell header header_style',
            children=[
                dcc.Link(
                    id='back-intro-link',
                    className='btn btn--hollow',
                    style={'display': 'none'},
                    children='back to intro',
                    href='/{}/'.format(URL_BASEPATH)
                ),
                html.Div(
                    id='header-content',
                    className='grid-x',
                    children=[
                        html.Div(
                            className='cell large-10 small-offset-1 hdr__h2',
                            children='NDC Off-Grid Alternatives'
                        ),
                        html.H1(
                            className='cell large-10 small-offset-1',
                            children='Renewable Energy Off-Grid Explorer',
                        ),
                        html.Div(
                            className='cell large-10 small-offset-1 hdr__h2',
                            children='Visualization of Electrification Scenarios until 2030',
                        ),
                    ]
                ),
                html.Div(
                    className='show-for-large',
                    children=html.Img(
                        className='hdr__logo',
                        src='data:image/png;base64,{}'.format(HDR_LOGO.decode())

                    )
                ),
                html.Div(
                    className='hide-for-large',
                    children=html.Img(
                        className='hdr__logo__small',
                        src='data:image/png;base64,{}'.format(HDR_LOGO.decode())

                    )
                )
            ]
        ),
        html.Div(
            id='page-div',
            className='cell',
            children=[
                html.Div(id='page-content'),
            ]
        ),
        html.Div(
            id='footer-div',
            className='cell footer',
            children=[
                html.Div(
                    className='footer-logo',
                    children=html.Img(
                        src='data:image/png;base64,{}'.format(logo.decode()),
                    )
                )
                for logo in LOGOS
            ]
        ),
    ]
)

# define the callbacks
static_layout.callbacks(app)
flex_layout.callbacks(app)


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
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


@app.callback(
    Output('back-intro-link', 'style'),
    [Input('url', 'pathname')],
    [State('back-intro-link', 'style')]
)
def display_page(pathname, cur_style):
    """Manage display of the return to index button between the different layouts"""
    if cur_style is None:
        cur_style = {'display': 'none'}

    if pathname == '/{}'.format(URL_BASEPATH) \
            or pathname == '/{}/'.format(URL_BASEPATH) \
            or pathname == '/' or pathname is None:
        cur_style.update({'display': 'none'})
    elif pathname == '/{}/{}'.format(URL_BASEPATH, static_layout.URL_PATHNAME):
        cur_style.update({'display': 'block'})
    elif pathname == '/{}/{}'.format(URL_BASEPATH, flex_layout.URL_PATHNAME):
        cur_style.update({'display': 'block'})
    return cur_style


if __name__ == '__main__':
    app.run_server(debug=True)
