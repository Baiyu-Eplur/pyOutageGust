"""Offline P03/P04 validation only: synthetic fixtures and mocked HTTP, no experiment run."""
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from analysis_new import grid_weather as weather
from analysis_new import grid_fragility_validation as validation
from analysis_new.district_day_core import lad_folds, lognormal_mle, predict_lognormal
from analysis_new.p03_p04_grid_weather import merge_weather, validate_panel, verified_output


def payload(start='2024-02-28', end='2024-03-01'):
    stamps = pd.date_range(start, pd.Timestamp(end)+pd.Timedelta(days=1), freq='h', inclusive='left')
    return dict(latitude=52., longitude=.1, utc_offset_seconds=0, hourly_units={weather.FIELD: 'm/s'},
                hourly=dict(time=stamps.strftime('%Y-%m-%dT%H:%M').tolist(),
                            wind_gusts_10m=(np.arange(len(stamps)) % 24).astype(float).tolist()))


class HourlyContract(unittest.TestCase):
    def test_maximum_and_leap_day_not_average(self):
        frame = weather.parse_hourly(payload(), 'A', '2024-02-28', '2024-03-01')
        self.assertEqual(frame.date.tolist(), ['2024-02-28', '2024-02-29', '2024-03-01'])
        self.assertEqual(frame.gust_grid.tolist(), [23., 23., 23.])
        self.assertTrue(frame.hours.eq(24).all())

    def test_reject_incomplete_duplicate_missing_wrong_units_timezone(self):
        for change in ['missing_hour', 'duplicate_hour', 'null_value', 'unit', 'timezone', 'negative']:
            with self.subTest(change=change):
                p = payload()
                if change == 'missing_hour': p['hourly']['time'].pop()
                if change == 'duplicate_hour': p['hourly']['time'][1] = p['hourly']['time'][0]
                if change == 'null_value': p['hourly'][weather.FIELD][3] = None
                if change == 'negative': p['hourly'][weather.FIELD][3] = -1
                if change == 'unit': p['hourly_units'][weather.FIELD] = 'km/h'
                if change == 'timezone': p['utc_offset_seconds'] = 3600
                with self.assertRaises(weather.WeatherFailure):
                    weather.parse_hourly(p, 'A', '2024-02-28', '2024-03-01')

    def test_request_full_period_fixed_source_and_units(self):
        p = weather.query_params(52., .1)
        self.assertEqual((p['start_date'], p['end_date']), ('2021-04-01', '2024-03-31'))
        self.assertEqual((p['models'], p['hourly'], p['wind_speed_unit'], p['timezone']),
                         ('era5', 'wind_gusts_10m', 'ms', 'GMT'))
        self.assertNotIn('daily', p)

    def test_retry_is_bounded_and_400_does_not_retry(self):
        from unittest.mock import Mock
        session = Mock(); events = []
        session.get.return_value = Mock(status_code=429, headers={'Retry-After': '500'}, text='quota')
        sleep = Mock()
        with self.assertRaises(weather.WeatherFailure):
            weather.fetch_hourly({}, session, events.append, sleep=sleep)
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [60, 60])
        session.reset_mock(); session.get.return_value.status_code = 400
        with self.assertRaises(weather.WeatherFailure):
            weather.fetch_hourly({}, session, events.append, sleep=sleep)
        self.assertEqual(session.get.call_count, 1)

    def test_acquisition_one_full_request_per_lad_and_cache(self):
        from unittest.mock import Mock
        p = payload(weather.START, weather.END)
        session = Mock(); session.get.return_value = Mock(status_code=200)
        session.get.return_value.json.return_value = p
        cent = pd.DataFrame(dict(LAD21CD=['A', 'B'], lat=[52., 52.1], lon=[.1, .2]))
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp)/'first'; second = Path(tmp)/'second'
            daily = weather.acquire(cent, first, interval=0, session=session, sleep=lambda _: None)
            self.assertEqual(len(daily), 2*1096)
            self.assertEqual(session.get.call_count, 2)
            for call in session.get.call_args_list:
                self.assertEqual(call.kwargs['params']['end_date'], weather.END)
            session.get.side_effect = AssertionError('cache must not call HTTP')
            cached = weather.acquire(cent, second, cache={l: first/f'{l}.json.gz' for l in ['A','B']}, session=session)
            pd.testing.assert_frame_equal(daily, cached)
            cent.loc[0, 'lat'] += .5
            with self.assertRaises(weather.WeatherFailure):
                weather.acquire(cent, Path(tmp)/'bad', cache={l: first/f'{l}.json.gz' for l in ['A','B']}, session=session)

    def test_acquisition_stops_after_three_consecutive_failed_lads(self):
        from unittest.mock import Mock
        session=Mock(); session.get.return_value=Mock(status_code=400,text='unsupported',headers={})
        cent=pd.DataFrame(dict(LAD21CD=list('ABCDE'),lat=[52.]*5,lon=[.1]*5))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(weather.WeatherFailure):
                weather.acquire(cent,tmp,interval=0,session=session,sleep=lambda _:None)
            self.assertEqual(session.get.call_count,3)
            self.assertEqual(len(list(Path(tmp).glob('*.json.gz'))),0)


class PanelAndSpatial(unittest.TestCase):
    def test_merge_changes_only_gust_and_rejects_missing_or_duplicate(self):
        old = pd.DataFrame(dict(LAD21CD=['A','B'], date=['2024-01-01']*2, gust=[10., 12.], n_inc=[0,1], precip=[2., np.nan]))
        new = pd.DataFrame(dict(LAD21CD=['B','A'], date=['2024-01-01']*2, gust_grid=[20., 18.]))
        merged = merge_weather(old, new)
        self.assertEqual(merged.gust.tolist(), [18., 20.])
        self.assertEqual(merged.gust_proxy.tolist(), old.gust.tolist())
        pd.testing.assert_series_equal(merged.n_inc, old.n_inc)
        pd.testing.assert_series_equal(merged.precip, old.precip)
        for bad in [new.iloc[:1], pd.concat([new, new.iloc[:1]])]:
            with self.assertRaises(ValueError): merge_weather(old, bad)

    def test_zero_customer_any_event_preserved_and_labels_checked(self):
        events = pd.DataFrame(dict(LAD21CD=['A'], incident_date_utc=['2024-01-01T10:00:00Z'],
                                   customers_v2_event_excl_reinterruptions=[0], cause_group_official=['weather_natural']))
        panel = pd.DataFrame(dict(LAD21CD=['A'], date=['2024-01-01'], gust=[10.], n_inc=[1], maxc=[0], wmaxc=[0]))
        for target in validation.TARGETS: panel[target] = int(target.endswith('gt0'))
        validate_panel(panel, events, expected_lads=1, start='2024-01-01', end='2024-01-01')
        panel['any_gt0'] = 0
        with self.assertRaises(ValueError):
            validate_panel(panel, events, expected_lads=1, start='2024-01-01', end='2024-01-01')

    def test_spatial_loo_never_uses_held_out_value(self):
        cent = pd.DataFrame(dict(LAD21CD=['A','B','C'], lat=[52.,52.,52.], lon=[0.,.1,.2]))
        grid = pd.DataFrame(dict(LAD21CD=['A','B','C'], date=['2024-01-01']*3,
                                 gust_grid=[100.,10.,10.], grid_lat=[52.]*3, grid_lon=[0.,.1,.2]))
        result = validation.grid_loo(grid, cent).set_index('LAD21CD')
        self.assertAlmostEqual(result.loc['A','grid_loo'], 10.)
        grid.loc[0,'gust_grid'] = 200.
        result2 = validation.grid_loo(grid, cent).set_index('LAD21CD')
        self.assertAlmostEqual(result2.loc['A','grid_loo'], 10.)
        grid.loc[1,'grid_lon'] = 0.; grid.loc[1,'gust_grid'] = 200.
        cell = validation.grid_loo(grid, cent, exclude_shared_cells=True).set_index('LAD21CD')
        self.assertAlmostEqual(cell.loc['A','grid_loo'], 10.)

    def test_centroid_uses_polygon_geometry(self):
        import geopandas as gpd
        from shapely.geometry import box
        g = gpd.GeoDataFrame({'LAD21CD':['A']}, geometry=[box(530000, 180000, 532000, 182000)], crs=27700)
        with patch('geopandas.read_file', return_value=g):
            c = weather.boundary_centroids('unused', ['A'])
        from pyproj import Transformer
        lon, lat = Transformer.from_crs(27700, 4326, always_xy=True).transform(531000, 181000)
        self.assertAlmostEqual(c.lat.iloc[0], lat, places=8)
        self.assertAlmostEqual(c.lon.iloc[0], lon, places=8)

    def test_hash_mismatch_is_not_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'panel.csv').write_text('changed')
            with self.assertRaises(ValueError):
                verified_output(p, {'outputs':[{'path':'panel.csv','sha256':'bad'}]}, 'panel.csv')


class FittingAndDecision(unittest.TestCase):
    def test_shared_mle_predicts_and_objective_matches_formula(self):
        from scipy.special import ndtr
        rng = np.random.default_rng(71); g = rng.uniform(.1,40,600)
        y = rng.binomial(1, .08+.92*ndtr((np.log(np.clip(g,.3,None))-np.log(23))/.45))
        diagnostics=[]; fit=lognormal_mle(g,y,diagnostics=diagnostics)
        pred=predict_lognormal(g,fit)
        self.assertTrue(diagnostics[-1]['success'])
        self.assertAlmostEqual(fit['nll'], -float(np.sum(y*np.log(pred)+(1-y)*np.log(1-pred))), places=8)
        self.assertTrue(np.all(np.diff(predict_lognormal(np.arange(1.,41.),fit)) >= 0))

    def test_folds_match_existing_first_seen_shuffle(self):
        lads=np.repeat(['D','B','A','C','F','E'],4)
        unique=pd.unique(lads); np.random.default_rng(20260908).shuffle(unique)
        expected=pd.Series(lads).map(dict(zip(unique,np.arange(6)%5))).to_numpy()
        np.testing.assert_array_equal(lad_folds(lads),expected)
        for l in np.unique(lads): self.assertEqual(len(set(lad_folds(lads)[lads==l])),1)

    def test_evaluation_all_targets_paired_folds_no_leakage(self):
        panel=pd.DataFrame(dict(LAD21CD=np.repeat(list('ABCDE'),8), date=list(map(str,range(40))),
                                 gust_proxy=np.arange(1.,41.), gust=np.arange(1.,41.)+100))
        for target in validation.TARGETS: panel[target]=np.tile([0,1],20)
        folds=lad_folds(panel.LAD21CD.to_numpy())
        calls=[]
        def fake_fit(g,y,diagnostics):
            calls.append(g.copy()); diagnostics.append(dict(success=True))
            return dict(theta=20.,beta=.4,p0=.1,nll=1.)
        with patch.object(validation,'lognormal_mle',side_effect=fake_fit):
            result=validation.evaluate(panel,folds,repeats=100)
        self.assertEqual(len(result['parameters']),16)
        self.assertEqual(len(result['fold_scores']),80)
        self.assertEqual(len(calls),96)
        for start in range(0,96,6):
            full=set(calls[start])
            for k, training in zip(sorted(np.unique(folds)),calls[start+1:start+6]):
                held_out=full-set(training)
                indices=np.flatnonzero(folds==k)
                self.assertEqual(len(held_out),len(indices))
                self.assertEqual(held_out,set(calls[start][indices]))
        self.assertFalse(result['oof'].isna().any().any())

    def test_decision_no_automatic_promotion_or_hidden_worsening(self):
        scores=pd.DataFrame(dict(relative_improvement=[.1]*8, relative_gain_ci_high=[.15]*8,
                                 calibration_rmse_proxy=[.1]*8,calibration_rmse_grid=[.08]*8))
        uncertainty={'mean_relative_gain_ci95':[.05,.15]}; diagnostics=[{'success':True}]
        d=validation.decide(scores,uncertainty,[],diagnostics)
        self.assertEqual(d['status'],'intermediate'); self.assertTrue(d['numerical_candidate'])
        scores['relative_improvement']=-.1
        self.assertEqual(validation.decide(scores,uncertainty,[],diagnostics)['status'],'rollback')
        scores['relative_improvement']=.005
        self.assertEqual(validation.decide(scores,uncertainty,[],diagnostics)['status'],'rollback')
        scores['relative_improvement']=.1; scores.loc[0,'relative_gain_ci_high']=-.06
        self.assertEqual(validation.decide(scores,uncertainty,[],diagnostics)['status'],'rollback')
        self.assertEqual(validation.decide(scores,uncertainty,['inspect cells'],diagnostics)['status'],'intermediate')

    def test_disabled_entry_has_no_network_or_output(self):
        from analysis_new.runner import STAGES
        entry=importlib.import_module('main_new')
        self.assertEqual(list(entry.STEPS),STAGES)
        self.assertEqual(list(entry.STEPS)[16],'p03_p04_grid_weather')
        self.assertTrue(all(v==0 for v in entry.STEPS.values()))
        with patch('requests.sessions.Session.get',side_effect=AssertionError('No HTTP permitted')):
            self.assertEqual(entry.main(),0)

    def test_acquisition_failure_writes_rollback_without_fitting(self):
        import types
        from analysis_new import p03_p04_grid_weather as experiment
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp); root=project/'results/new/20990101000000'
            root.mkdir(parents=True)
            context=types.SimpleNamespace(PROJECT=project, ROOT=root, DATA=project/'data')
            panel=pd.DataFrame(dict(LAD21CD=['A']))
            cent=pd.DataFrame(dict(LAD21CD=['A'],lat=[52.],lon=[.1]))
            # Real experiment source hashes must still be recorded from the real code.
            import shutil
            (project/'analysis_new').mkdir()
            for f in ['grid_weather.py','grid_fragility_validation.py','district_day_core.py']:
                shutil.copyfile(Path(experiment.__file__).parent/f,project/'analysis_new'/f)
            with patch.dict('sys.modules', {'analysis_new.runtime':context}), \
                 patch.dict('os.environ', {'P03_SETTINGS':json.dumps({'base_run':'20980101000000'})}), \
                 patch.object(experiment,'load_baseline',return_value=(panel,pd.DataFrame(),{})), \
                 patch.object(experiment,'boundary_centroids',return_value=cent), \
                 patch.object(experiment,'acquire',side_effect=weather.WeatherFailure('mock missing hours')), \
                 patch.object(experiment,'evaluate') as fit:
                with self.assertRaises(weather.WeatherFailure): experiment.main()
                fit.assert_not_called()
            out=root/'results/p03_p04'
            self.assertEqual(json.loads((out/'decision.json').read_text(encoding='utf-8'))['status'],'rollback')
            self.assertEqual(json.loads((out/'experiment.json').read_text(encoding='utf-8'))['status'],'failed')
            self.assertTrue((out/'REPORT.md').exists())
            self.assertTrue((out/'inventory.json').exists())

    def test_synthetic_orchestration_saves_data_before_fit_and_outputs(self):
        import types
        import shutil
        from analysis_new import p03_p04_grid_weather as experiment
        panel=pd.DataFrame(dict(LAD21CD=np.repeat(list('ABCDE'),4), date=list(pd.date_range('2024-01-01',periods=4).strftime('%Y-%m-%d'))*5,
                                 gust=np.tile([8.,10.,12.,14.],5), n_inc=np.tile([0,1,0,1],5)))
        cent=pd.DataFrame(dict(LAD21CD=list('ABCDE'),lat=[52.]*5,lon=np.arange(5)*.2))
        grid=panel[['LAD21CD','date']].copy(); grid['gust_grid']=panel.gust+2
        grid=grid.merge(cent.rename(columns={'lat':'grid_lat','lon':'grid_lon'}),on='LAD21CD')
        for target in validation.TARGETS: panel[target]=panel.n_inc
        params=pd.DataFrame([dict(target=t,version=v,theta=20.,beta=.4,p0=.1,n=20,events=10,nll=5.)
                             for t in validation.TARGETS for v in ['proxy','era5_daily_max']])
        scores=pd.DataFrame(dict(target=validation.TARGETS,relative_improvement=[.1]*8,relative_gain_ci_high=[.15]*8,
                                 calibration_rmse_proxy=[.1]*8,calibration_rmse_grid=[.08]*8))
        bins=pd.DataFrame([dict(target=t,version=v,bin=b,n=10,mean_probability=p,observed_frequency=p+.01,events=1)
                           for t in validation.TARGETS for v in ['proxy','era5_daily_max'] for b,p in enumerate([.1,.2])])
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp); root=project/'results/new/20990101000000'; root.mkdir(parents=True)
            (project/'analysis_new').mkdir()
            for f in ['grid_weather.py','grid_fragility_validation.py','district_day_core.py']:
                shutil.copyfile(Path(experiment.__file__).parent/f,project/'analysis_new'/f)
            out=root/'results/p03_p04'
            def fake_evaluate(*args,**kwargs):
                self.assertTrue((out/'gust_comparison.json').exists())
                self.assertTrue((out/'spatial_validation.json').exists())
                self.assertIn('data_comparison_and_spatial_loo_saved_before_fits',json.loads((out/'experiment.json').read_text())['completed'])
                return dict(parameters=params,scores=scores,calibration=bins,fold_scores=pd.DataFrame({'brier':[.1]}),
                            oof=panel,diagnostics=[{'success':True}],uncertainty={'mean_relative_gain_ci95':[.05,.15]})
            context=types.SimpleNamespace(PROJECT=project,ROOT=root,DATA=project/'data')
            with patch.dict('sys.modules',{'analysis_new.runtime':context}), \
                 patch.dict('os.environ',{'P03_SETTINGS':json.dumps({'base_run':'20980101000000'})}), \
                 patch.object(experiment,'load_baseline',return_value=(panel,panel,{'old_interpolation_validation':{}})), \
                 patch.object(experiment,'boundary_centroids',return_value=cent), \
                 patch.object(experiment,'acquire',return_value=grid), \
                 patch.object(experiment,'evaluate',side_effect=fake_evaluate), \
                 patch('requests.sessions.Session.get',side_effect=AssertionError('No HTTP in fixture')):
                experiment.main()
            self.assertEqual(json.loads((out/'experiment.json').read_text())['status'],'completed')
            self.assertEqual(len(pd.read_csv(out/'parameters_comparison.csv')),8)
            self.assertEqual((out/'calibration.png').read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
            inventory=json.loads((out/'inventory.json').read_text())
            self.assertGreater(len(inventory['outputs']),15)


if __name__ == '__main__':
    unittest.main()
