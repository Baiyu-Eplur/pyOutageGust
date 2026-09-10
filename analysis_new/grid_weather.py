"""P03 acquisition: one full-period ERA5 hourly request per LAD, strict UTC coverage.

No network activity on import. Raw responses are preserved with request provenance;
daily values are never filled from the incident-based proxy.
"""
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

START = '2021-04-01'
END = '2024-03-31'
FIELD = 'wind_gusts_10m'
API = 'https://archive-api.open-meteo.com/v1/archive'


class WeatherFailure(RuntimeError):
    """Acquisition cannot supply the predeclared complete panel."""


def query_params(lat, lon, start=START, end=END):
    return dict(latitude=float(lat), longitude=float(lon), start_date=start, end_date=end,
                hourly=FIELD, models='era5', wind_speed_unit='ms', timezone='GMT',
                cell_selection='nearest', elevation='nan')


def parse_hourly(payload, lad, start=START, end=END):
    """Validate all UTC hours (including leap day) BEFORE daily max aggregation."""
    if not isinstance(payload, dict) or payload.get('error'):
        raise WeatherFailure(f'{lad}: API error: {str(payload)[:250]}')
    if payload.get('utc_offset_seconds') != 0 or payload.get('hourly_units', {}).get(FIELD) != 'm/s':
        raise WeatherFailure(f'{lad}: unexpected timezone offset or wind unit')
    expected = pd.date_range(start, pd.Timestamp(end) + pd.Timedelta(days=1), freq='h', inclusive='left')
    try:
        hourly = payload['hourly']
        stamps = pd.DatetimeIndex(pd.to_datetime(hourly['time']))
        values = np.array(hourly[FIELD], dtype=float)
        grid = [float(payload['latitude']), float(payload['longitude'])]
    except (KeyError, ValueError, TypeError) as exc:
        raise WeatherFailure(f'{lad}: malformed hourly response') from exc
    if not stamps.equals(expected) or len(values) != len(expected):
        raise WeatherFailure(f'{lad}: missing, duplicated, reordered or non-UTC hours')
    if not np.isfinite(values).all() or (values < 0).any() or not np.isfinite(grid).all():
        raise WeatherFailure(f'{lad}: missing/negative/nonfinite wind or grid coordinates')
    if not (-90 <= grid[0] <= 90 and -180 <= grid[1] <= 180):
        raise WeatherFailure(f'{lad}: invalid returned grid coordinates')
    daily = pd.Series(values, index=stamps).resample('D').agg(['max', 'count'])
    if not daily['count'].eq(24).all():
        raise WeatherFailure(f'{lad}: not exactly 24 hours per UTC date')
    return pd.DataFrame(dict(LAD21CD=lad, date=daily.index.strftime('%Y-%m-%d'),
                             gust_grid=daily['max'].to_numpy(), hours=daily['count'].to_numpy(),
                             grid_lat=grid[0], grid_lon=grid[1]))


def boundary_centroids(boundary, lads):
    """Polygon area centroids in British National Grid, then WGS84; no event coordinates."""
    import geopandas as gpd
    g = gpd.read_file(boundary)
    g = g[g.LAD21CD.isin(lads)].copy()
    if g.crs is None or set(g.LAD21CD) != set(lads) or g.LAD21CD.duplicated().any():
        raise ValueError('Boundary CRS or unique LAD coverage invalid')
    if g.geometry.is_empty.any() or g.geometry.isna().any() or not g.geometry.is_valid.all():
        raise ValueError('Invalid LAD polygon geometry; no silent geometry repair')
    g = g.set_index('LAD21CD').loc[lads].to_crs(27700)
    c = g.geometry.centroid.to_crs(4326)
    return pd.DataFrame({'LAD21CD': lads, 'lat': c.y.to_numpy(), 'lon': c.x.to_numpy()})


def fetch_hourly(params, session, event, sleep=time.sleep, attempts=3):
    """Bounded retry; parameter errors fail immediately, 429/5xx have capped backoff."""
    import requests
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(API, params=params, timeout=(15, 90))
            event(dict(attempt=attempt, status_code=response.status_code))
            if response.status_code == 200:
                return response.json()
            if response.status_code != 429 and response.status_code < 500:
                raise WeatherFailure(f'HTTP {response.status_code}: {response.text[:250]}')
            delay = min(60, max(10 * attempt, float(response.headers.get('Retry-After', 0))))
        except (requests.RequestException, ValueError) as exc:
            event(dict(attempt=attempt, error=str(exc)[:250]))
            delay = min(60, 10 * attempt)
        if attempt < attempts:
            sleep(delay)
    raise WeatherFailure(f'API failed after {attempts} attempts; no substitute weather used')


def acquire(centroids, out, interval=10, cache=None, session=None, sleep=time.sleep):
    """Cache maps LAD to verified raw envelope path, supplied by the experiment runner."""
    import gzip
    import requests
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    cache = cache or {}
    owned = session is None
    session = session or requests.Session()
    tables, failures = [], []
    consecutive = 0
    calls = 0
    def event(record):
        with (out / 'requests.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(dict(time=datetime.now().astimezone().isoformat(), **record)) + '\n')
    try:
        for row in centroids.itertuples(index=False):
            params = query_params(row.lat, row.lon)
            try:
                if row.LAD21CD in cache:
                    with gzip.open(cache[row.LAD21CD], 'rt', encoding='utf-8') as f:
                        envelope = json.load(f)
                    if envelope['request'] != params or envelope['api'] != API:
                        raise WeatherFailure('Cached request does not match this centroid/model/period')
                    event(dict(lad=row.LAD21CD, reused=str(cache[row.LAD21CD])))
                else:
                    if calls:
                        sleep(interval)
                    calls += 1
                    payload = fetch_hourly(params, session, lambda r: event(dict(lad=row.LAD21CD, **r)), sleep)
                    envelope = dict(api=API, request=params, fetched_at=datetime.now().astimezone().isoformat(), response=payload)
                table = parse_hourly(envelope['response'], row.LAD21CD)
                raw = json.dumps(envelope, ensure_ascii=False).encode('utf-8')
                # Deterministic gzip header; outer run.json hashes every stored raw response.
                (out / f'{row.LAD21CD}.json.gz').write_bytes(gzip.compress(raw, mtime=0))
                event(dict(lad=row.LAD21CD, validated_hours=int(table.hours.sum()),
                           response_sha256=hashlib.sha256(raw).hexdigest()))
                tables.append(table); consecutive = 0
            except (WeatherFailure, OSError, ValueError, KeyError) as exc:
                failures.append(dict(lad=row.LAD21CD, error=str(exc)))
                consecutive += 1
                event(dict(lad=row.LAD21CD, failure=str(exc)))
                if consecutive >= 3:
                    break
    finally:
        if owned:
            session.close()
    if failures or len(tables) != len(centroids):
        raise WeatherFailure(f'Incomplete coverage: {len(tables)}/{len(centroids)} LADs; {failures}. '
                             'Validated raw responses retained for explicit resume.')
    return pd.concat(tables, ignore_index=True)
