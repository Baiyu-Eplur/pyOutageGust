"""Paths supplied by main_new; never read the advisor package at runtime."""
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ['NEW_ANALYSIS_RUN']).resolve()
if not ROOT.is_relative_to(PROJECT / 'results' / 'new'):
    raise ValueError('NEW_ANALYSIS_RUN must be inside results/new')
DATA = PROJECT / 'review_package' / 'data'
KNOT_BOOTSTRAPS = int(os.environ.get('NEW_KNOT_BOOTSTRAPS', '500'))
PLATEAU_BOOTSTRAPS = int(os.environ.get('NEW_PLATEAU_BOOTSTRAPS', '300'))
