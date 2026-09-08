"""Single immutable consumer release. Reuses only copied, delimited plotting code; no fit calls."""
from common import *
import importlib.util,shutil,ast
import matplotlib.pyplot as plt
from scipy import stats
from PIL import Image

def run():
    release=Q/'release_v1';assert not release.exists(),'Immutable release already exists; choose a new reviewed version'
    (release/'figures').mkdir(parents=True);(release/'frozen').mkdir();shutil.copytree(R4/'tables',release/'tables');shutil.copytree(R4/'frozen/geometry',release/'frozen/geometry')
    refs=read(R4/'frozen/GEOMETRY_MANIFEST.json')
    for r in refs:r['path']=str(release/'frozen/geometry'/Path(r['path']).name);assert sha(r['path'])==r['sha256']
    put(release/'frozen/GEOMETRY_MANIFEST.json',refs)
    # Initial 11 panels, followed by only the required final consumer sections.
    spec=importlib.util.spec_from_file_location('frozen_figure_base',Q/'frozen/R04_src/figures.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);base.Q=release;base.FIGS=[];base.run()
    contexts=[]
    for filename,stop in [('final_data.py','    table(Q/\'tables/residual_diagnostics.csv\''),('product_complete.py','    # Bind numerical captions'),('artifact_acceptance.py','    # Five-fold coefficient summaries')]:
        source=(Q/'frozen/R04_src'/filename).read_text(encoding='utf-8');body=source.split('def run():\n',1)[1].split(stop,1)[0];assert stop in source
        # Static allowlist review: these prefixes contain plotting/read-back only.
        calls=[n.func.id for n in ast.walk(ast.parse('def selected():\n'+body)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        assert not(set(calls)&{'fit_ols','run_model','run_group','fit','produce'})
        env=dict(globals());env['Q']=release
        extra="\n    save(Q/'figures/FIGURE_MANIFEST.json',mf)\n" if filename=='final_data.py' else ''
        exec(compile('def selected():\n'+body+extra, str(Q/'frozen/R04_src'/filename)+':consumer_prefix','exec'),env);env['selected']()
        contexts.append({'copied_source':record(Q/'frozen/R04_src'/filename),'stop_before':stop,'reason':'final_data final 02/03/D1/F1; product_complete final05/08; artifact_acceptance numeric D1'})
    mf=read(release/'figures/FIGURE_MANIFEST.json');assert len(mf)==12
    mf.sort(key=lambda x:x['figure']);rows=[]
    for r in mf:
        r['producer']=str(Path(__file__));r['consumer_release']='R05_release_v1';r['visual_review']='pending';r['source_model']='R04_B1_all_valid_v1'
        if r['figure']=='figure01':r['reference']='one eligible event; reported primary-substation coordinates; hexbin counts, not area-normalized density; no licence boundaries or GB inset'
        for ext in ['png','pdf']:
            p=release/'figures'/f"{r['figure']}.{ext}";old=R4/'figures'/p.name;row={'figure':r['figure'],'format':ext,'current':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'R04_sha256':sha(old),'byte_identical_to_R04':sha(p)==sha(old),'data_equivalence':'same frozen inputs; no model/data change','pixel_equal':None}
            if ext=='png':
                a=np.array(Image.open(p));b=np.array(Image.open(old));row['pixel_equal']=a.shape==b.shape and np.array_equal(a,b);row['image_shape']=str(a.shape)
            rows.append(row)
    put(release/'figures/FIGURE_MANIFEST.json',mf);table(Q/'tables/FIGURE_RELEASE_COMPARISON.csv',pd.DataFrame(rows))
    fig,axs=plt.subplots(4,3,figsize=(18,19))
    for ax,r in zip(axs.flat,mf):ax.imshow(plt.imread(release/'figures'/f"{r['figure']}.png"));ax.set_title(r['figure']);ax.axis('off')
    fig.tight_layout();fig.savefig(release/'figures/visual_contact_sheet.png',dpi=115);plt.close(fig)
    deps=[record(p) for p in (RUN).rglob('*') if p.is_file() and (p.suffix in ['.json','.csv'])]
    put(release/'CONSUMER_INPUTS.json',{'source_code':contexts,'base':record(Q/'frozen/R04_src/figures.py'),'frozen_model_and_data':deps,'event_master':read(CORE/'configs/R04_primary.json'),'new_fits':0})
    put(Q/'CURRENT_CONSUMER_RELEASE.json',{'release':'release_v1','entry':'R05/cli.py render_release','manifest':record(release/'figures/FIGURE_MANIFEST.json'),'supersedes_consumers_only':'R04/figures','no_model_successor':True,'policy':'release_v1 is immutable; old renderers cannot update this R05 pointer. A further reviewed render must use a new release directory.'})
    put(Q/'checks/consumer_reproduction.json',{'passed':True,'figure_groups':12,'PNG_PDF_files':24,'new_fits':0,'all_sources_frozen':True,'order':['base 11','02/03/D1/F1 final data','05/08 paired panels','D1 actual numerical bins'],'pixel_identical_count':sum(r['pixel_equal'] is True for r in rows),'byte_identical_count':sum(r['byte_identical_to_R04'] for r in rows)})
    print('12 final figure groups reproduced in independent immutable release; zero fits',flush=True)
if __name__=='__main__':run()
