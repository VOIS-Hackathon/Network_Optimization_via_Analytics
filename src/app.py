import dash #type: ignore
from dash import html #type: ignore
import dash_bootstrap_components as dbc #type: ignore

# Create Dash app
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container(
    className="dark",
    id="theme-container",
    children=[
    html.H2("Network Optimization", className="my-3"),
    dbc.Nav(
        [
            dbc.NavLink("Analytics", href="/", active="exact"),
            dbc.NavLink("Tower Optimization", href="/page2", active="exact"),
        ],
        pills=True,
    ),
    dash.page_container
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)
