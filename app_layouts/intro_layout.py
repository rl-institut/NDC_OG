import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app_main import app, URL_BASEPATH
from . import static_layout, flex_layout

description_content = [
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
]

layout = html.Div(
    id='intro-div',
    className='grid-y',
    children=[
        html.Div(
            id='intro-main-div',
            className='cell medium-8',
            children=[
                html.Div(
                    id='intro-main-content',
                    className='grid-x',
                    children=[
                        html.Div(
                            id='intro-placeholder-div',
                            className='cell medium-5 framed',
                            children=[
                                'Placeholder or video'
                            ]
                        ),
                        html.Div(
                            id='intro-text-div',
                            className='cell medium-7',
                            children=[
                                html.Div(
                                    id='intro-text-content',
                                    className='grid-y',
                                    children=[
                                        html.Div(
                                            id='intro-about-content',
                                            className='cell medium-4 framed',
                                            children='What the tool can do in simple words'
                                        ),
                                        html.Div(
                                            id='intro-description-content',
                                            className='cell medium-8 framed',
                                            children=description_content,
                                        )
                                    ]
                                )
                            ]
                        ),
                    ],
                ),
            ]
        ),
        html.Div(
            id='intro-disclaimer-div',
            className='cell medium-2 framed',
            children=[
                html.P(
                    'The presented scenarios and figures are meant to support informed policy \
                    and planning decisions, but do not represent official planning.'
                )
            ]
        ),
        html.Div(
            id='intro-link-div',
            className='cell medium-2',
            children=[
                html.Div(
                    id='intro-link-content',
                    className='grid-x grid-margin-x',
                    children=[
                        dcc.Link(
                            id='intro-link-static',
                            className='cell medium-4 framed',
                            children='Start tour',
                            href='/{}/{}'.format(URL_BASEPATH, static_layout.URL_PATHNAME)
                        ),
                        dcc.Link(
                            id='intro-link-flex',
                            className='cell medium-4 framed',
                            children='Advanced',
                            href='/{}/{}'.format(URL_BASEPATH, flex_layout.URL_PATHNAME)
                        ),
                    ]
                )]
        ),


    ]
)
