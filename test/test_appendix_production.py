"""Lifecycle tests use disposable directories, never the real Appendix outputs."""
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch
from analysis_new.appendix.runner import publish, OWNER, safe_child, run, temporary_folder
from analysis_new.appendix.catalog import ROOT
from analysis_new.appendix.mapping import write_json, digest

class AppendixPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='appendix-test-')
        self.root=Path(self.temp.name).resolve()
        self.output=self.root/'Appendix';self.output.mkdir()

    def tearDown(self): self.temp.cleanup()

    def staged(self,name,files):
        p=self.root/name;p.mkdir()
        for rel,text in files.items():
            f=safe_child(p,rel);f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
        write_json(p/'manifest.json',dict(owner=OWNER,managed_files=[*files,'manifest.json'],outputs=[],status='success',update_state='本次已更新'))
        return p

    def test_selected_cleanup_and_human_preservation(self):
        target=self.output/'J'
        publish(self.staged('first',{'tables/current.csv':'old','figures/obsolete.png':'obsolete'}),target)
        (target/'human.md').write_text('notes')
        a=self.output/'A';a.mkdir();(a/'sentinel').write_text('A stays unchanged')
        before=digest(a/'sentinel')
        publish(self.staged('second',{'tables/current.csv':'new'}),target)
        self.assertEqual((target/'tables/current.csv').read_text(),'new')
        self.assertFalse((target/'figures/obsolete.png').exists())
        self.assertEqual((target/'human.md').read_text(),'notes')
        self.assertEqual(digest(a/'sentinel'),before)
        self.assertEqual(sorted(p.name for p in self.output.iterdir()),['A','J'])

    def test_transaction_rolls_back_after_directory_move(self):
        target=self.output/'J'
        publish(self.staged('first',{'tables/current.csv':'complete'}),target)
        before={p.relative_to(target).as_posix():digest(p) for p in target.rglob('*') if p.is_file()}
        stage=self.staged('second',{'tables/current.csv':'new'})
        import os
        original=os.replace
        def fail_publish(src,dst):
            if Path(src).name=='merged': raise OSError('simulated rename failure')
            return original(src,dst)
        with patch('analysis_new.appendix.runner.os.replace',side_effect=fail_publish):
            with self.assertRaises(OSError): publish(stage,target)
        self.assertEqual(before,{p.relative_to(target).as_posix():digest(p) for p in target.rglob('*') if p.is_file()})

    def test_human_collision_is_not_overwritten(self):
        target=self.output/'J';target.mkdir();(target/'README.md').write_text('manual')
        with self.assertRaisesRegex(ValueError,'Unmanaged human file'):
            publish(self.staged('first',{'README.md':'generated'}),target)
        self.assertEqual((target/'README.md').read_text(),'manual')

    def test_repeated_publication_stable_paths(self):
        target=self.output/'J'
        publish(self.staged('first',{'tables/current.csv':'same'}),target)
        before=digest(target/'tables/current.csv')
        publish(self.staged('second',{'tables/current.csv':'same'}),target)
        self.assertEqual(before,digest(target/'tables/current.csv'))
        self.assertEqual(sorted(p.name for p in self.output.iterdir()),['J'])
        self.assertFalse(list(self.output.glob('.appendix-*')))

    def test_manifest_traversal_is_rejected(self):
        target=self.output/'J';target.mkdir()
        write_json(target/'manifest.json',dict(owner=OWNER,managed_files=['../A/important.csv']))
        with self.assertRaises(ValueError): publish(self.staged('first',{'table.csv':'new'}),target)

    def test_access_denied_does_not_spin_in_temp_creation(self):
        with patch('analysis_new.appendix.runner.Path.mkdir',side_effect=PermissionError('denied')) as create:
            with self.assertRaises(PermissionError):
                with temporary_folder(self.root,'.appendix-test-'): pass
            self.assertEqual(create.call_count,1)

    def test_failed_generator_records_preserved_state_and_can_retry(self):
        def complete(letter,stage,checks):
            (stage/'data').mkdir();(stage/'data/value.csv').write_text('value\n1\n')
            write_json(stage/'manifest.json',dict(owner=OWNER,appendix=letter,last_attempt='test',status='success',update_state='本次已更新',
                requirements={'A01':'已生成'},managed_files=['data/value.csv','manifest.json'],
                outputs=[dict(path='data/value.csv',requirement_id='A01',claim_id='CL_A01',source_sha256={})]))
        run(['A'],out=self.output,generator=complete)
        before=digest(self.output/'A/data/value.csv')
        def fail(letter,stage,checks):
            (stage/'incomplete.csv').write_text('partial')
            raise RuntimeError('simulated exporter failure')
        manifest,failures=run(['A'],out=self.output,generator=fail)
        self.assertTrue(failures['A']);self.assertEqual(manifest['appendices']['A']['artifact_status'],'failed_preserved')
        self.assertEqual(digest(self.output/'A/data/value.csv'),before)
        self.assertFalse((self.output/'A/incomplete.csv').exists())
        manifest,failures=run(['A'],out=self.output,generator=complete)
        self.assertFalse(failures['A']);self.assertEqual(manifest['appendices']['A']['artifact_status'],'success')

    def test_check_only_from_other_cwd_does_not_mutate_outputs_or_log(self):
        def snapshot():
            files=[ROOT/'LOG.md',*(ROOT/'results/Appendix').rglob('*')]
            return {str(p):(digest(p),p.stat().st_mtime_ns) for p in files if p.is_file()}
        before=snapshot()
        result=subprocess.run([sys.executable,'-B',str(ROOT/'main_appendix.py'),'--appendices','A','J','--check-only'],cwd=self.root,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertEqual(before,snapshot())

if __name__=='__main__': unittest.main()
