"""Independent R02 input consumer. Never import or patch the historical pipeline.

The producer is paper_revision_work_v2/code/run_r02.py. All scientific model
execution remains outside R02; this module only reads the verified event table.
"""
from pathlib import Path
import sys

REPAIR_DIR = Path(__file__).resolve().parent
if str(REPAIR_DIR) not in sys.path:
    sys.path.insert(0, str(REPAIR_DIR))
from r02_events import load_active_events


def step0_build_sample():
    event, manifest = load_active_events()
    matched = event.loc[event['new_in_study_utc'] & event['weather_numeric_available']].copy()
    summary = {
        'input_version': manifest['run_id'],
        'event_manifest': str(REPAIR_DIR.parents[1] / 'paper_revision_work_v2/R02/data/EVENT_MANIFEST.json'),
        'event_sha256': manifest['event_table']['sha256'],
        'n_total_events_v3': len(event),
        'n_weather_matched_events': len(matched),
        'weather_matched_pct': 100 * len(matched) / len(event),
        'cause_group_counts_in_matched_sample': matched['cause_group_event'].value_counts(dropna=False).to_dict(),
        'scope': 'R02 input only; independent of historical v9 and its output directories',
        'models_run': 0,
    }
    return matched, summary


def step1_lad_gapfill(matched):
    if 'input_version' not in matched or not matched['input_version'].eq('R02_20260905').all():
        raise ValueError('This independent reader accepts verified R02 inputs only')
    return matched, {
        'n_events_in_sample': len(matched),
        'n_missing_LAD21CD_after': int(matched['LAD21CD'].isna().sum()),
        'gapfill_performed': False,
        'note': 'R02 producer already rejoined LAD and population; read-only coverage check',
    }


def step2_build_folds(sample):
    raise RuntimeError('R02 provides inputs only. Implement R03 in an independent revision pipeline before model execution.')
