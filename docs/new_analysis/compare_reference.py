"""Read-only reference audit, deliberately outside the production analysis package.

Usage: python compare_reference.py --reference <advisor package> --run <own run>
       --output <audit JSON>. Reference files never become computational inputs.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image


def json_diff(a, b, at=''):
    differences = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in a.keys() | b.keys():
            if key not in a or key not in b:
                differences.append(dict(field=at+'/'+key, reason='key coverage', reference=a.get(key), actual=b.get(key)))
            else:
                differences.extend(json_diff(a[key], b[key], at+'/'+key))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            differences.append(dict(field=at, reason='length', reference=len(a), actual=len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                differences.extend(json_diff(x, y, at+f'/{i}'))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not np.isclose(a, b, rtol=1e-6, atol=1e-7, equal_nan=True):
            differences.append(dict(field=at, reason='numeric', reference=a, actual=b))
    elif a != b:
        differences.append(dict(field=at, reason='text/type', reference=a, actual=b))
    return differences


def frame_diff(a, b):
    out = []
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return [dict(reason='shape/columns', reference=[a.shape, list(a.columns)], actual=[b.shape, list(b.columns)])]
    for col in a:
        if pd.api.types.is_numeric_dtype(a[col]) and pd.api.types.is_numeric_dtype(b[col]):
            x, y = a[col].to_numpy(dtype=float), b[col].to_numpy(dtype=float)
            mask = ~np.isclose(x, y, atol=1e-7, rtol=1e-6, equal_nan=True)
            if mask.any():
                ids = np.flatnonzero(mask)
                out.append(dict(column=col, reason='numeric', cells=int(mask.sum()), max_abs=float(np.nanmax(np.abs(x-y))),
                                examples=[dict(row=int(i), reference=x[i], actual=y[i]) for i in ids[:4]]))
        else:
            x, y = a[col].fillna('').astype(str), b[col].fillna('').astype(str)
            mask = x != y
            if mask.any():
                out.append(dict(column=col, reason='text', cells=int(mask.sum()), reference=x[mask].iloc[0], actual=y[mask].iloc[0]))
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); records = []
    for reference in sorted((args.reference/'results').rglob('*')):
        if not reference.is_file():
            continue
        rel = reference.relative_to(args.reference/'results'); actual = args.run/'results'/rel
        record = dict(file=rel.as_posix(), reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest())
        if not actual.exists():
            record['status'] = 'missing'
        else:
            record['actual_sha256'] = hashlib.sha256(actual.read_bytes()).hexdigest()
            differences = []
            if reference.suffix == '.csv':
                differences = frame_diff(pd.read_csv(reference), pd.read_csv(actual))
            elif reference.suffix == '.json':
                differences = json_diff(json.loads(reference.read_text()), json.loads(actual.read_text()))
            elif reference.suffix == '.xlsx':
                ra = pd.read_excel(reference, sheet_name=None); rb = pd.read_excel(actual, sheet_name=None)
                for name in ra.keys() | rb.keys():
                    differences.extend([dict(sheet=name, **d) for d in frame_diff(ra[name], rb[name])]
                                       if name in ra and name in rb else [dict(sheet=name, reason='sheet missing')])
            elif reference.suffix == '.png':
                with Image.open(reference) as a, Image.open(actual) as b:
                    record['reference_dimensions'] = a.size; record['actual_dimensions'] = b.size
                    record['status'] = 'dimensions_match_visual_review_required' if a.size == b.size else 'dimensions_differ'
            else:
                record['status'] = 'byte_equal' if record['reference_sha256'] == record['actual_sha256'] else 'uncompared_format'
            record.setdefault('status', 'within_tolerance' if not differences else 'differences')
            if differences:
                record['differences'] = differences
        records.append(record)
    summary = pd.Series([r['status'] for r in records]).value_counts().to_dict()
    payload = dict(reference=str(args.reference.resolve()), run=str(args.run.resolve()),
                   numeric_tolerance=dict(rtol=1e-6, atol=1e-7), summary=summary, files=records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    print(json.dumps(summary))
    for r in records:
        if r['status'] == 'differences':
            print(r['file'], len(r['differences']), 'differences')


if __name__ == '__main__':
    main()
