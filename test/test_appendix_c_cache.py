"""Cache validity/force checks use a source-reused component, never new fits."""
import json
import unittest
from unittest.mock import patch
from pathlib import Path
from threadpoolctl import threadpool_limits
from analysis_new.appendix.catalog import ROOT
from analysis_new.appendix.runner import temporary_folder
from analysis_new.appendix import c_models as cm
from analysis_new.appendix.c_completion import compute_one

class CacheTests(unittest.TestCase):
    def test_valid_corrupt_changed_configuration_and_force(self):
        base=ROOT/'results/Appendix/C';previous=base/'data/models/E0_all/H01'
        if not (previous/'result.json').exists():self.skipTest('Run C once before cache integration check')
        protocol=json.loads((base/'logs/protocol.json').read_text());d=cm.samples()['E0_all'];m=cm.MODELS[0]
        with threadpool_limits(limits=1),temporary_folder(ROOT/'test','.c-cache-test-') as tmp,patch('statsmodels.api.OLS',side_effect=AssertionError('No fit authorized in cache test')):
            valid=compute_one(tmp/'valid','E0_all',d,m,protocol,False,previous)
            self.assertTrue(valid['cache_used'])
            # Corrupt only the newly allocated scratch copy, never real outputs.
            (tmp/'valid/in_sample.csv.gz').write_bytes(b'test corruption')
            repaired=compute_one(tmp/'repaired','E0_all',d,m,protocol,False,tmp/'valid')
            self.assertFalse(repaired['cache_used'])
            forced=compute_one(tmp/'forced','E0_all',d,m,protocol,True,previous)
            self.assertFalse(forced['cache_used'])
            changed=json.loads(json.dumps(protocol));changed['samples'][0]['sample_id_sha256']='test different input fingerprint'
            invalid=compute_one(tmp/'changed','E0_all',d,m,changed,False,previous)
            self.assertFalse(invalid['cache_used'])

if __name__=='__main__':unittest.main()
