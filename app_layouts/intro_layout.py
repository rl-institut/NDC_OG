import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app_main import app, URL_BASEPATH, PLACEHOLDER

from . import static_layout, flex_layout

description_content = [
    html.H2('Universal Access to Electricity by 2030...'),
    html.P(['...cannot be achieved by grid extension alone. In 2019, we are still talking about almost 1 billion people worldwide living without access to electricity, most of them are living in rural areas of developing countries. Grid extension is slow, expensive, provides unreliable service, and it increases reliance on fossil-fuel based electricity generation. Grid extension is not a viable answer to the pressing needs of neglected populations.']),
    html.P(['What we need are CLEANER, CHAPER & SMARTER solutions, if we want to ensure that access to electricity is provided sustainably and universally until 2030. And, we need to strengthen international commitment to implement these solutions on a larger scale.']),
    html.P(['This is what Researchers at the ', html.A(children='Reiner Lemoine Institute', href='https://reiner-lemoine-institut.de/en/'), ' (RLI) and the greenwerk have been working on over the last year. The RLI has developed feasible country-level scenarios for the deployment of off-grid renewable energy solutions that mitigate climate change, are more cost-effective than gird extension approaches, and leave no-one behind. The greenwerk’s analysis has shown that country-level realization of these scenarios is further accompanied by significant economic and social dividends to those most in need, which can propel development and build resilience to climate change. ']),
    html.P(['Most countries facing the access challenge already have rural electrification programmes; most of these countries have also acknowledged the acuteness of the problem. At the same time, off-grid renewable energy solutions find very little consideration in the same countries’ Nationally Determined Contributions (NDCs). The relevance of off-grid renewable energy solutions for climate action has so far been widely neglected. Through this project, the ',html.A(children='German Development Corporation', href='https://www.giz.de/en/html/index.html') ,' (GIZ) seeks to establish this missing link, by offering new evidence for the exceptional benefits of off-grid renewable energy technologies, and by advocating for greater representation of holistic and sustainable off-grid solutions within countries’ NDCs. ']),
]

about_content = [
    html.H2('What can this tool do?'),
    html.P('Off-grid renewable energy solutions are CLEANER, CHEAPER & SMARTER – this is what our model aims to convey. The Reiner Lemoine Institute and the greenwerk have collected and analysed huge amounts of data from all over the world. This data has been translated into interactive electrification scenarios that showcase feasible deployment pathways through which the universal access goal can be met. You can engage with these scenarios through this tool and alter underlying assumptions. The tool allows you to:'),
    html.P('LEARN about the access gap of a given country and the mix of technology options (Grid Extension, Mini-Grids and Solar-Home-Systems) available to close it.'),
    html.P('COMPARE the initial investment needs and the mitigation potential of different technology options in different scenarios and for different ESMAP TIER level assumptions.'),
    html.P('UNDERSTAND how (the lack of) favourable technology-specific frameworks can alter electrification scenarios.'),
]

layout = html.Div(
    id='intro-div',
    className='grid-x',
    children=[
        html.Div(
            id='intro-main-div',
            className='cell',
            children=[
                html.Div(
                    id='intro-main-content',
                    className='grid-x',
                    children=[
                        html.Div(
                            id='intro-text-div',
                            className='cell',
                            children=[
                                html.Div(
                                    id='intro-text-content',
                                    className='grid-y',
                                    children=[

                                        html.Div(
                                            id='intro-description-content',
                                            className='cell medium-8 framed',
                                            children=description_content,
                                        ),
                                        html.Div(
                                            id='intro-about-content',
                                            className='cell medium-4 framed',
                                            children=about_content
                                        ),
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
            className='cell medium-8 large-6',
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
                            className='cell btn btn-cta',
                            children='Start tour',
                            href='/{}/{}'.format(URL_BASEPATH, static_layout.URL_PATHNAME)
                        ),
                        dcc.Link(
                            id='intro-link-flex',
                            className='cell btn btn--hollow',
                            children='Advanced',
                            href='/{}/{}'.format(URL_BASEPATH, flex_layout.URL_PATHNAME)
                        ),
                    ]
                )]
        ),


    ]
)
