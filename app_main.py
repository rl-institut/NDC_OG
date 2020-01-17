import base64
import os
from flask import Flask, send_from_directory

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

server = Flask(__name__)

# Initializes dash app
app = dash.Dash(server=server)

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


@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory('data', path, as_attachment=True)


css_directory = os.getcwd()
stylesheets = ['app.css', 'base.css', 'intro.css']
static_css_route = 'assets'


@app.server.route('/static/<stylesheet>')
def serve_stylesheet(stylesheet):
    if stylesheet not in stylesheets:
        raise Exception(
            '"{}" is excluded from the allowed static files'.format(
                stylesheet
            )
        )
    return send_from_directory(css_directory, stylesheet)


for stylesheet in stylesheets:
    app.css.append_css({"external_url": "/static/{}".format(stylesheet)})
