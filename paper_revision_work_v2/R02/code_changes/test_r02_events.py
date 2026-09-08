"""Targeted regressions for the known event/time/input failure modes."""
import sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT.parent/'.venv/Lib/site-packages'))
import numpy as np
import pandas as pd
import r02_events as m

def stages():
    data=[]
    for sn,start,end in [(8,'2023-07-01T01:00:00+01:00','2023-07-01T02:00:00+01:00'),(2,'2023-07-01T00:30:00+00:00','2023-07-01T03:00:00+00:00'),(5,'2023-07-01T00:00:00+00:00','2023-07-01T04:00:00+00:00')]:
        d={m.ID:'TEST','source_row_number':sn,'Restoration Stage':str(sn),'Start Date and Time':start,'End Date and Time':end,'Number of Customers Restored':'2','Re-interruption Stage':'N','Cause Code':'71','unique_identifier':f'TEST{sn}','Spatial Coordinates':'51.5, 0.1','licence_area':'LPN','regulatory_year':'2023-24','substation':'station','SiteFunctionalLocation':'loc','cause_group_official':'technical_asset',m.C:6.,m.D:4.,m.A:2.5,'wx_time_used_utc':pd.Timestamp(start).tz_convert('UTC').floor('h'),'request_key':'51.5_0.1_2023-07-01','weather_status_v3':'matched','lat':51.5,'lon':.1,'population':100.,'LAD21CD':'LAD','LAD21NM':'name','income_deprivation_rate':.1,'deprivation_gap_pct':.2,'morans_i':.3,'rural_urban_classification':'Urban'}
        d.update({x:1. for x in m.WX});data.append(d)
    return pd.DataFrame(data)

class EventRules(unittest.TestCase):
    def build(self,s):return m.construct_events(s,'sha',{'technical_asset':['71'],'non_fault_or_unknown':['98']})[0]
    def test_shuffle_stable_absolute_time_and_ties(self):
        s=stages();a=self.build(s);b=self.build(s.sample(frac=1,random_state=901))
        pd.testing.assert_frame_equal(a,b)
        self.assertEqual(a.selected_source_row.iloc[0],5) # times 5 and 8 tie in UTC, stable row 5 wins
        self.assertEqual(a.old_source_row.iloc[0],2)
        self.assertEqual(a.earliest_tie_count.iloc[0],2)
    def test_tied_coordinate_conflict_not_weather_tiebreak(self):
        s=stages();s.loc[s.source_row_number.eq(8),'Spatial Coordinates']='52.0, 0.1'
        e=self.build(s).iloc[0];self.assertEqual(e.selected_source_row,5)
        self.assertTrue(e.coordinate_conflict);self.assertFalse(e.weather_query_eligible)
    def test_sourceid_and_cause_conflicts_preserve_stages(self):
        s=stages();s.loc[0,'unique_identifier']=s.loc[1,'unique_identifier'];s.loc[1,'Cause Code']='98'
        e=self.build(s).iloc[0];self.assertEqual(e.n_stages,3);self.assertEqual(e[m.C],6.)
        self.assertTrue(e.source_id_conflict);self.assertTrue(e.event_identity_unresolved);self.assertEqual(e.cause_group_event,'unresolved')
    def test_repeat_and_empty_customer_set(self):
        s=stages();s.loc[0,'Re-interruption Stage']='Y';self.assertEqual(self.build(s)[m.C].iloc[0],4.)
        s['Re-interruption Stage']='1';self.assertTrue(pd.isna(self.build(s)[m.C].iloc[0]))
    def test_no_offset_not_silently_localized(self):
        t,o=m.parse_offset_time(pd.Series(['2023-10-29T01:30:00','2023-10-29T01:30:00+01:00','2023-10-29T01:30:00+00:00']))
        self.assertTrue(pd.isna(t.iloc[0]));self.assertEqual((t.iloc[2]-t.iloc[1]).total_seconds(),3600)
    def test_calendar_boundaries_include_full_end_day(self):
        x=m.temporal_columns(pd.Series(['2023-09-29T23:59:59Z','2023-09-30T00:00:00Z','2024-03-31T23:59:59Z','2024-04-01T00:00:00Z']))
        self.assertEqual(list(x.period),['development','later','later','outside_study'])
        self.assertEqual(list(x.in_study_utc),[True,True,True,False])
        self.assertFalse(x.in_study_london.iloc[2]) # retained alternate calendar exposes the 1-hour boundary difference
    def test_cross_boundary_end_retained_in_D(self):
        s=stages().iloc[:1].copy();s['Start Date and Time']='2024-03-31T23:00:00Z';s['End Date and Time']='2024-04-02T01:00:00Z'
        e=self.build(s).iloc[0];self.assertTrue(e.new_in_study_utc);self.assertEqual(e[m.D],26.);self.assertTrue(e.recovery_crosses_study_end)
    def test_population_uses_new_year_and_unique_keys(self):
        e=pd.DataFrame({'LAD21CD':['LAD'],'new_year':[2022],'population':[2023.]})
        p=pd.DataFrame({'LAD23CD':['LAD','LAD'],'year':[2022,2023],'population':[122.,123.]})
        self.assertEqual(m.reconnect_population(e,p).population.iloc[0],122.)
        with self.assertRaises(ValueError):m.reconnect_population(e,pd.concat([p,p.iloc[:1]]))
    def test_missing_C_is_false_eligibility_with_explicit_reason(self):
        e=self.build(stages());e[m.C]=pd.Series([pd.NA],dtype='Int64')
        e['log_population']=np.log(e.population);e['weather_numeric_available']=True
        e['weather_validation_tier']='strict_cache_checked'
        e=m.qualify(e)
        self.assertFalse(e.candidate_main_E0.iloc[0]);self.assertFalse(e.candidate_main_R0c.iloc[0])
        self.assertFalse(e.candidate_main_E0.isna().any())
        self.assertIn('C_invalid_or_missing',e.E0_exclusion_reasons.iloc[0])

class WeatherRules(unittest.TestCase):
    def hourly(self):
        return pd.DataFrame({'time_utc':pd.date_range('2023-01-01T01:00Z',periods=24,freq='h'),'precipitation':np.ones(24),'wind_gusts_10m':np.ones(24)*4,'temperature_2m':np.ones(24)*8,'pressure_msl':np.ones(24)*1000})
    def test_exact_hour_and_rain_window(self):
        h=self.hourly();r=m.inspect_hourly(h,'2023-01-02T00:00Z');self.assertEqual(r['precipitation_24h_sum'],24.)
        h.loc[0,'precipitation']=np.nan;r=m.inspect_hourly(h,'2023-01-02T00:00Z');self.assertIsNone(r['precipitation_24h_sum']);self.assertEqual(r['rain_valid_values'],23)
    def test_duplicate_hour_is_not_24_valid_hours(self):
        h=self.hourly();h.loc[0,'time_utc']=h.loc[1,'time_utc'];r=m.inspect_hourly(h,'2023-01-02T00:00Z')
        self.assertEqual(r['rain_window_status'],'duplicate_hour');self.assertIsNone(r['precipitation_24h_sum'])
    def test_absent_exact_hour_never_uses_nearest(self):
        r=m.inspect_hourly(self.hourly(),'2023-01-02T01:00Z');self.assertEqual(r['exact_hour_count'],0);self.assertIsNone(r['gust_0h'])
    def test_v3_only_preserved_and_explicitly_unverified(self):
        row={'earliest_v3_'+c:1. for c in m.WX};r=m.resolve_weather(row,None,'missing_file')
        self.assertTrue(r['weather_numeric_available']);self.assertEqual(r['weather_validation_tier'],'v3_only_window_not_reverified')
    def test_missing_earliest_weather_does_not_borrow_later(self):
        row={'earliest_v3_'+c:np.nan for c in m.WX};row.update({'old_'+c:9. for c in m.WX})
        r=m.resolve_weather(row,None,'missing_file');self.assertFalse(r['weather_numeric_available'])
    def test_invalid_readable_cache_not_hidden_by_v3_fallback(self):
        row={'earliest_v3_'+c:9. for c in m.WX};h=self.hourly();h.loc[0,'precipitation']=np.nan
        r=m.resolve_weather(row,m.inspect_hourly(h,'2023-01-02T00:00Z'),'readable');self.assertFalse(r['weather_numeric_available'])

if __name__=='__main__':unittest.main(verbosity=2)
