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
            children=[
                html.P(
                    'In the Study on Renewable Energy Off-Grid Components of NDCs and their Role \
                    for Climate Change Mitigation financed by GIZ,  Reiner Lemoine Institute and \
                    the greenwerk develop strategies for the use of renewable energy that can \
                    support climate protection in developing countries.'
                ),
                html.P(
                    'The study targets the inclusion of off-grid components \
                   in the Nationally Determined Contributions (NDCs), in which the signatory \
                   states to the Paris Climate Change Convention commit themselves to elaborate \
                   national climate protection targets, should be achieved.'
                ),
                html.P(
                    'In this visualization tool a quantification of four different new \
                electrification until 2030 scenarios are presented for 52 countries. \
                These countries were selected through the criteria of having > 1 million people \
                without electricity access in 2017.'
                ),
                html.P(
                    'The presented scenarios and figures are meant to support informed policy \
                    and planning decisions, but do not represent official planning.'
                )
            ]
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
