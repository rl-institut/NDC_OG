import base64
import os

import dash

URL_BASEPATH = 'NDC-visualization'

LOGOS = [
    base64.b64encode(open('logos/{}'.format(fn), 'rb').read())
    for fn in os.listdir('logos') if fn.endswith('.png')
]

INFO_ICON = base64.b64encode(open('icons/information.png', 'rb').read())

PLACEHOLDER = base64.b64encode(open('assets/placeholder.png', 'rb').read())

APP_BG_COLOR = '#FFFFFF'

# Initializes dash app
app = dash.Dash(__name__)

# Load css file
external_css = [
    'https://raw.githack.com/rl-institut/WAM/dev/static/foundation/css/app.css',
]
for css in external_css:
    app.css.append_css({"external_url": css})

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
            {%renderer%}
        </footer>
        </body>

    </html>
    '''

app.title = 'NDC visualisation'

app.config.suppress_callback_exceptions = True
