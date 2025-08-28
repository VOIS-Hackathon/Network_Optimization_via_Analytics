import pickle
import pandas as pd
from pathlib import Path
import dash #type: ignore
from dash import dcc, html #type:ignore
import os 

dash.register_page(__name__, path="/optimize tower")

