import dash

URL_BASEPATH = 'NDC-visualization'

# Initializes dash app
app = dash.Dash(__name__)

app.title = 'NDC visualisation'

server = app.server
app.config.suppress_callback_exceptions = True
