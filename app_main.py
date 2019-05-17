import dash

URL_BASEPATH = 'NDC-visualization'

# Initializes dash app
app = dash.Dash(__name__)

# Load css file
external_css = [
    'https://raw.githack.com/rl-institut/WAM/dev/static/foundation/css/app.css',
]
for css in external_css:
    app.css.append_css({"external_url": css})

app.title = 'NDC visualisation'

server = app.server
app.config.suppress_callback_exceptions = True
