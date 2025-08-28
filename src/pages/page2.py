import pickle
import pandas as pd
from pathlib import Path
import os 

import dash #type: ignore
from dash import html, dcc, Input, Output, State, callback #type: ignore
import dash_bootstrap_components as dbc #type:ignore

dash.register_page(__name__, path="/page2")


# Get the current file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build full path to your CSV
DATA_PATH = os.path.join(BASE_DIR,"final_data.csv")

# Load data
df = pd.read_csv(DATA_PATH)

# ------------------------- User-configurable section -------------------------
MODEL_PATH = Path("model/tower_optimization_model.pkl")

# Feature names must match the model's expected order / names
FEATURE_COLS = [
    'latency_sec', 'bandwidth_mbps', 'dropped_calls', 'total_calls',
    'uptime_percent', 'users_connected', 'download_speed_mbps', 'upload_speed_mbps',
    'signal_strength.RSSI', 'signal_strength.RSRP', 'signal_strength.SINR',
    'tower_load_percent', 'average_call_duration_sec', 'handover_success_rate',
    'packet_loss_percent', 'jitter_ms', 'tower_temperature_c', 'battery_backup_hours',
    'tower_age_years'
]

FEATURE_RANGES = {}
for col in FEATURE_COLS:
    if col in df.columns:
        min_val = float(df[col].min())
        max_val = float(df[col].max())
        default_val = float(df[col].median())  # could also use mean()
        FEATURE_RANGES[col] = (min_val, max_val, default_val)
# -----------------------------------------------------------------------------

# Load model (safe handling)
model = None
model_load_error = None
if MODEL_PATH.exists():
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
    except Exception as e:
        model_load_error = str(e)
else:
    model_load_error = f"Model file not found at {MODEL_PATH.resolve()}"

# Helper to build a form row (label + numeric input)
def build_input_row(feature_name: str):
    low, high, default = FEATURE_RANGES.get(feature_name, (None, None, None))
    input_id = {'type': 'feature-input', 'index': feature_name}
    # Using dbc.Input so we get nice styling; type='number'
    return dbc.Row([
        dbc.Col(html.Label(feature_name, title=feature_name), width=5),
        dbc.Col(dbc.Input(
            id=input_id,
            type='number',
            min=low,
            max=high,
            step=(0.1 if isinstance(default, float) else 1),
            value=default,
            placeholder=f"{low} - {high}"
        ), width=7)
    ], className="mb-2")

# Build the form with all features
form_children = []
for feat in FEATURE_COLS:
    form_children.append(build_input_row(feat))

# App layout
layout = dbc.Container(
    className="dark",
    id="theme-container",
    children=[
        
    dcc.Store(id="selected-tower-data"),  
    html.H2("Tower Optimization Predictor", className="my-3"),

    dbc.Alert(
        f"Model load error: {model_load_error}",
        color="danger",
        id="model-error-alert",
        is_open=bool(model_load_error),
        style={"whiteSpace": "pre-wrap"}
    ),

    dbc.Card([
        dbc.CardBody([
            html.H5("Enter performance metrics"),
            html.Div(form_children, id='feature-form'),

            dbc.Row([
                dbc.Col(dbc.Button("Predict", id='predict-btn', color='primary'), width='auto'),
                dbc.Col(dbc.Button("Reset to defaults", id='reset-btn', color='secondary', outline=True), width='auto')
            ], className='mt-3'),

            html.Hr(),

            dbc.Row([
                dbc.Col(html.Div(id='prediction-output'), width=12)
            ])
        ])
    ], className='mb-4'),
], fluid=True)

# Callback: reset button sets inputs back to defaults
@callback(
    Output({'type': 'feature-input', 'index': dash.ALL}, 'value'),
    Input('reset-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_defaults(n_clicks):
    # Return default values in the same order as FEATURE_COLS
    return [FEATURE_RANGES.get(f, (None, None, None))[2] for f in FEATURE_COLS]

# Prediction callback
@callback(
    Output('prediction-output', 'children'),
    Input('predict-btn', 'n_clicks'),
    State({'type': 'feature-input', 'index': dash.ALL}, 'value'),
    prevent_initial_call=True
)
def predict(n_clicks, values):
    # values is a list aligned to FEATURE_COLS order
    if model is None:
        return dbc.Alert(f"No model loaded. {model_load_error}", color='danger')

    # Basic validation: check we have a value for every feature
    if values is None or len(values) != len(FEATURE_COLS):
        return dbc.Alert("Input error: missing feature values.", color='warning')

    # Build DataFrame for the model
    try:
        x = pd.DataFrame([values], columns=FEATURE_COLS)
        # If model expects specific dtypes or scaling, ensure those pre-processing steps happen here.
        # For example: x = scaler.transform(x) if you saved a scaler separately.
    except Exception as e:
        return dbc.Alert(f"Failed to construct feature vector: {e}", color='danger')

    # Try predict_proba -> probability of class 1 (needs optimization). Fall back to predict.
    try:
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(x)
            # assume class 1 is positive (needs optimization). Find index of class 1 if classes_ present
            if hasattr(model, 'classes_'):
                classes = list(model.classes_)
                if 1 in classes:
                    idx = classes.index(1)
                elif 'yes' in classes:
                    idx = classes.index('yes')
                else:
                    # fallback to second column
                    idx = 1 if proba.shape[1] > 1 else 0
            else:
                idx = 1 if proba.shape[1] > 1 else 0

            score = float(proba[0, idx])
            label = "The tower needs optimization" if score >= 0.5 else "No optimization needed"
            bar = dbc.Progress(value=round(score * 100, 2), children=f"{round(score*100,2)}%", striped=True, animated=True)

            return dbc.Card([
                dbc.CardBody([
                    html.H4(label),
                    html.P(f"Model probability (positive class): {score:.4f}"),
                    bar
                ])
            ], color='light')
        else:
            pred = model.predict(x)
            # interpret pred[0]
            positive_values = {1, 'yes', 'true', True}
            is_pos = pred[0] in positive_values
            label = "Needs optimization" if is_pos else "No optimization needed"
            return dbc.Alert(label, color='info')
    except Exception as e:
        # If model prediction fails (e.g., expecting scaled data), return helpful message.
        return dbc.Alert(
            [html.Div("Prediction failed:"), html.Pre(str(e)), html.Div("If your model expects pre-processing (scaling, encoding), make sure to load/perform the same preprocessing here." )],
            color='danger'
        )

# @callback(
#     [Output({"type": "feature-input", "index": col}, "value") for col in FEATURE_COLS],
#     Input("selected-tower-data", "data"),
#     prevent_initial_call=True
# )
# def autofill_inputs(selected_row):
#     if not selected_row:
#         raise dash.exceptions.PreventUpdate
#     # return values in the same order as FEATURE_COLS
#     return [selected_row.get(col, FEATURE_RANGES[col][2]) for col in FEATURE_COLS]