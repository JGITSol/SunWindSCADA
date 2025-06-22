import dash
import dash_bootstrap_components as dbc
import requests
from dash import html, dcc, Input, Output, State

# The API URL must use the Django service name from docker-compose
API_URL = "http://django:8000/api/hello/"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("SunWindSCADA - Dash Frontend"),
    html.P("This is the new frontend for the SCADA system."),
    html.Hr(),
    dbc.Button("Fetch Data from Django API", id="fetch-button", n_clicks=0),
    html.Div(id='api-response-output', style={'marginTop': '20px'})
])

@app.callback(
    Output('api-response-output', 'children'),
    Input('fetch-button', 'n_clicks'),
    prevent_initial_call=True
)
def fetch_data(n_clicks):
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return f"API Response: {data.get('message', 'No message found')}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to API: {e}"

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=3000)
