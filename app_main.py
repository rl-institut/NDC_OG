import base64
import os

import dash

URL_BASEPATH = 'NDC-visualization'

LOGOS = [
    base64.b64encode(open('logos/{}'.format(fn), 'rb').read())
    for fn in os.listdir('logos') if fn.endswith('.png')
]

HDR_LOGO = base64.b64encode(open('icons/header-logo.png', 'rb').read())

INFO_ICON = base64.b64encode(open('icons/information.png', 'rb').read())

PLACEHOLDER = base64.b64encode(open('assets/placeholder.png', 'rb').read())

APP_BG_COLOR = '#FFFFFF'

# Initializes dash app
app = dash.Dash(__name__)

app.index_string = '''
    <!DOCTYPE html>
    <html>

        <head>
            <meta charset="UTF-8">
            <meta description="NDC visualisation">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {%favicon%}
            {%css%}
        </head>

        <body>
            {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
        </footer>
        </body>

    </html>
    '''

app.title = 'NDC visualisation'

app.config.suppress_callback_exceptions = True
