import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app_main import app, URL_BASEPATH, PLACEHOLDER

from . import static_layout, flex_layout

description_content = [
    html.H3('Universal Access to Electricity by 2030...'),
    html.P(['...cannot be achieved by grid extension alone. In 2019, we are still talking about almost 1 billion people worldwide living without access to electricity, most of them are living in rural areas of developing countries. Grid extension is slow, expensive, provides unreliable service, and it increases reliance on fossil-fuel based electricity generation. Grid extension is not a viable answer to the pressing needs of neglected populations.']),
    html.P(['What we need are ', html.Span('CLEANER, CHAPER & SMARTER'), ' solutions, if we want to ensure that access to electricity is provided sustainably and universally until 2030. And, we need to strengthen international commitment to implement these solutions on a larger scale.']),
    html.P(['This is what Researchers at the ', html.A(children='Reiner Lemoine Institute', href='https://reiner-lemoine-institut.de/en/', target='_blank'), ' (RLI) and the ', html.A(children='Greenwerk', href='https://www.thegreenwerk.net/', target='_blank'), ' have been working on over the last year. The RLI has developed feasible country-level scenarios for the deployment of off-grid renewable energy solutions that mitigate climate change, are more cost-effective than gird extension approaches, and leave no-one behind. The greenwerk’s analysis has shown that country-level realization of these scenarios is further accompanied by significant economic and social dividends to those most in need, which can propel development and build resilience to climate change. ']),
    html.P(['Most countries facing the access challenge already have rural electrification programmes; most of these countries have also acknowledged the acuteness of the problem. At the same time, off-grid renewable energy solutions find very little consideration in the same countries’ Nationally Determined Contributions (NDCs). The relevance of off-grid renewable energy solutions for climate action has so far been widely neglected. Through this project, the ',html.A(children='German Development Agency', href='https://www.giz.de/en/html/index.html', target='_blank') ,' (GIZ) seeks to establish this missing link, by offering new evidence for the exceptional benefits of off-grid renewable energy technologies, and by advocating for greater representation of holistic and sustainable off-grid solutions within countries’ NDCs. ']),
]

about_content = [
    html.H3('What can this tool do?'),
    html.P(['Off-grid renewable energy solutions are ', html.Span('CLEANER'), ', ',  html.Span('CHEAPER'), ' & ', html.Span('SMARTER'), ' – this is what our model aims to convey. The Reiner Lemoine Institute and the Greenwerk have collected and analysed huge amounts of data from all over the world. This data has been translated into interactive electrification scenarios that showcase feasible deployment pathways through which the universal access goal can be met. You can engage with these scenarios through this tool and alter underlying assumptions. The tool allows you to:']),
    html.P([html.Span('LEARN'), ' about the access gap of a given country and the mix of technology options (Grid Extension, Mini-Grids and Solar-Home-Systems) available to close it.']),
    html.P([html.Span('COMPARE'), ' the initial investment needs and the mitigation potential of different technology options in different scenarios and for different ESMAP TIER level assumptions.']),
    html.P([html.Span('UNDERSTAND'), ' how (the lack of) favourable technology-specific frameworks can alter electrification scenarios.']),
]

citation_content = [
    html.H3('Impressum and citation'),
    html.P(['This tool “Renewable Energy Off-Grid Explorer” has been developed in the framework '
            'of the project “Strategies for Renewable Energy for Climate Protection in Developing Countries”. It has been financed by the Federal Minister for the Environment, Nature Conservation, and Nuclear Safety (', html.A(children='BMU', href='https://www.bmu.de/en/ ', target='_blank'), ') and the German Development Agency (', html.A(children='GIZ', href='https://www.giz.de/en/html/index.html', target='_blank'), '). The presented scenarios are meant to support informed policy and planning decisions, but do not represent official planning.']),
    html.P(['The project was implemented by Reiner Lemoine Institut (',
           html.A(children='RLI', href='https://reiner-lemoine-institut.de/en/', target='_blank'),
           ') and the ', html.A(children='Greenwerk', href='https://www.thegreenwerk.net/', target='_blank'), '.']),
    html.P(['Back-and front-end development was led by Pierre-Francois Duc (', html.A(children='RLI', href='https://reiner-lemoine-institut.de/en/', target='_blank'),').']),
    html.P(['Cite this report if you wish to use some of the results displayed here : report link']),
]

layout = html.Div(
    id='intro-div',
    className='grid-x',
    children=[
        html.Div(
            id='intro-text-div',
            className='cell',
            children=[
                html.Div(
                    id='intro-text-content',
                    className='grid-x align-center',
                    children=[

                        html.Div(
                            id='intro-description-content',
                            className='cell medium-10 large-5',
                            children=description_content,
                        ),
                        html.Div(
                            className='cell medium-10 large-5',
                            children=[
                                html.Div(
                                    id='intro-about-content',
                                    children=about_content
                                ),
                                html.Div(
                                    id='intro-citation-content',
                                    children=citation_content
                                ),
                                html.Div(
                                    id='intro-mobile-disclaimer-content',
                                    className='show-for-medium-only',
                                    children='This app is not optimized for small screens'
                                )
                            ],
                        )

                    ]
                )
            ]
        ),
        html.Div(
            id="intro-disclaimer-wrap",
            className='cell',
            children=[
                html.Div(
                    className="grid-x grid-padding-x align-center",
                    children=[
                        html.Div(
                            className='cell intro-link-div',
                            children=[
                                dcc.Link(
                                    id='intro-link-static',
                                    className='btn btn-cta',
                                    children='Explore Scenarios',
                                    href='/{}/{}'.format(URL_BASEPATH, static_layout.URL_PATHNAME)
                                ),
                                html.P('Compare the results for different scenarios')
                            ]
                        ),
                        html.Div(
                            className='cell intro-link-div',
                            children=[
                                dcc.Link(
                                    id='intro-link-flex',
                                    className='btn btn--hollow',
                                    children='Create Scenarios',
                                    href='/{}/{}'.format(URL_BASEPATH, flex_layout.URL_PATHNAME)
                                ),
                                html.P('Vary model parameters to create your own scenario')
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
                        )
                    ]
                )
            ]
        )
    ]
)
