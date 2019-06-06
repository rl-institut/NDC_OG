import base64
import os

import dash

URL_BASEPATH = 'NDC-visualization'

LOGOS = [
    base64.b64encode(open('logos/{}'.format(fn), 'rb').read())
    for fn in os.listdir('logos') if fn.endswith('.png')
]

PLACEHOLDER = base64.b64encode(open('assets/placeholder.png', 'rb').read())


# Initializes dash app
app = dash.Dash(__name__)

# Load css file
external_css = [
    'https://raw.githack.com/rl-institut/WAM/dev/static/foundation/css/app.css',
]
for css in external_css:
    app.css.append_css({"external_url": css})



app.title = 'NDC visualisation'

app.config.suppress_callback_exceptions = True
