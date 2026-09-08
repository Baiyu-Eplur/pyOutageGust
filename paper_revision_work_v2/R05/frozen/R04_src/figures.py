from common import *
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
import struct,shutil

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight','svg.fonttype':'none','pdf.fonttype':42})
FIGS=[]
def finish(fig,num,title,source,scale,reference):
    if num=='figure03':fig.axes[0].set_ylim(0,1.6)
    if num=='figure08':fig.axes[0].set_ylabel('Conditional ΔR² (percentage points)')
    if num=='figure10':
        for ax in fig.axes:ax.set_ylabel('Quadratic gust term [(m/s)⁻²]')
    fig.suptitle(title,fontsize=14);fig.tight_layout(rect=[0,.045,1,.95]);fig.text(.01,.008,'B1 all-valid | Retrospective description / date-group OOF | No process validation',fontsize=8,color='#555555')
    paths=[]
    for ext in ['png','pdf']:
        p=Q/'figures'/f'{num}.{ext}';fig.savefig(p,dpi=180);paths.append(str(p))
    FIGS.append({'figure':num,'title':title,'source':source,'scale':scale,'reference':reference,'files':paths,'run_id':'R04_B1_all_valid_v1','visual_review':'pending'});plt.close(fig)
def geometry():
    ref=next(x for x in read(CORE/'frozen/REFERENCE_DATA_MANIFEST.json') if x['original_path'].endswith('LAD_DEC_2021_UK_BGC.dbf'));base=Path(ref['original_path']);folder=Q/'frozen/geometry';folder.mkdir(exist_ok=True);refs=[]
    manifest=Q/'frozen/GEOMETRY_MANIFEST.json'
    if manifest.exists():
        refs=read(manifest)
        for ref in refs:assert sha(ref['path'])==ref['sha256'],'frozen geometry changed'
    else:
        for ext in ['.shp','.shx','.dbf','.prj','.cpg']:
            p=base.with_suffix(ext)
            if p.exists():dest=folder/p.name;shutil.copyfile(p,dest);refs.append({'original':str(p),'path':str(dest),'sha256':sha(dest)})
        save(manifest,refs)
    raw=(folder/base.name).read_bytes();n=struct.unpack_from('<I',raw,4)[0];head,width=struct.unpack_from('<HH',raw,8);fields=[];pos=32
    while raw[pos]!=13:
        name=raw[pos:pos+11].split(b'\0')[0].decode();length=raw[pos+16];fields.append((name,length));pos+=32
    attrs=[]
    for i in range(n):
        rec=raw[head+i*width:head+(i+1)*width];at=1;d={}
        for name,length in fields:d[name]=rec[at:at+length].decode('utf-8',errors='replace').strip();at+=length
        attrs.append(d)
    raw=(folder/base.with_suffix('.shp').name).read_bytes();pos=100;out={};i=0
    while pos<len(raw):
        _,words=struct.unpack_from('>ii',raw,pos);s=raw[pos+8:pos+8+2*words];pos+=8+words*2;typ=struct.unpack_from('<i',s)[0]
        if typ in [5,15,25]:
            parts,points=struct.unpack_from('<ii',s,36);indices=list(struct.unpack_from('<'+'i'*parts,s,44))+[points];xy=np.frombuffer(s,dtype='<f8',count=points*2,offset=44+4*parts).reshape(-1,2)/1000
            vertices=[];codes=[]
            for a,b in zip(indices[:-1],indices[1:]):
                ring=xy[a:b];vertices.extend(ring);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(ring)-2)+[MPath.CLOSEPOLY])
            out[attrs[i]['LAD21CD']]=MPath(np.array(vertices),codes)
        i+=1
    return out
def run():
    e=events();d=members(e,'main','E0');metrics=pd.read_csv(Q/'tables/core_metrics.csv');period=pd.read_csv(Q/'tables/period_comparison.csv');geo=geometry()
    # 1: mapped event locations, one row per eligible incident.
    fig,ax=plt.subplots(figsize=(7,6));good=d[['lon','lat']].notna().all(axis=1);h=ax.hexbin(d.loc[good,'lon'],d.loc[good,'lat'],gridsize=70,mincnt=1,bins='log',cmap='viridis');fig.colorbar(h,ax=ax,label='Incident count (log color)');ax.set(xlabel='Longitude (degrees)',ylabel='Latitude (degrees)',title=f'Main E0 / R0c population: n={len(d):,}');finish(fig,'figure01','Locations of eligible incidents','R02 candidate_main_E0','count','one event per incident; observed coordinates')
    fig,axs=plt.subplots(1,2,figsize=(10,4));axs[0].hist(np.log1p(d[C]),bins=55,color='#2878a5');axs[0].set(xlabel='ln(1 + affected customers)',ylabel='Incidents');axs[1].hist(np.log(d[D]),bins=55,color='#d87930');axs[1].set(xlabel='ln(restoration span / hours)',ylabel='Incidents');finish(fig,'figure02','Outcome distributions: all valid tails retained','R02 main candidates','log1p C; log D','n=60,436 in both panels; different outcomes')
    fig,ax=plt.subplots(figsize=(10,3.4));a=pd.Timestamp('2021-04-01');b=pd.Timestamp('2023-09-30');c=pd.Timestamp('2024-04-01');ax.barh([1,1],[(b-a).days,(c-b).days],left=[a,b],height=.45,color=['#2878a5','#d87930']);ax.text(a+pd.Timedelta(days=320),1,'Earlier period',ha='center',va='center',color='white');ax.text(b+pd.Timedelta(days=85),1,'Later period',ha='center',va='center',color='white');ax.set(yticks=[],xlabel='UTC analysis calendar');ax.text(.01,.05,'Later observations contributed to historical development; this is not an untouched confirmation set.',transform=ax.transAxes,fontsize=9);fig.autofmt_xdate();finish(fig,'figure03','Retrospective analysis periods','frozen calendar contract','UTC dates','study half-open [2021-04-01, 2024-04-01)')
    fig,axs=plt.subplots(2,2,figsize=(10,7))
    for i,g in enumerate(['main','weather']):
      for j,t in enumerate(['E0','R0c']):
        cv=pd.read_csv(RUN/f'{g}_{t}/figure4_curve_data.csv');axs[i,j].plot(cv.value,cv.exp_mean_eta,color=['#2878a5','#d87930'][j]);axs[i,j].set(xlabel='Gust proxy (m/s)',ylabel='exp(mean fitted log response)',title=f'{g} {t}; n={len(members(e,g,t)):,}');axs[i,j].grid(alpha=.15)
    finish(fig,'figure04','Gust reference curves — no minimum confidence intervals','formal figure4_curve_data/reference','exp(mean eta)','each model estimation population; per-row raw gust grid, fixed mean physical pressure')
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for ax,g in zip(axs,['main','weather']):
        q=metrics[(metrics.group==g)&(metrics.target=='R0c')];ax.bar(q.block,q.pooled_R2,color=['#888888','#2878a5','#d87930','#596e3c']);ax.set(title=f'{g} recovery',ylabel='Pooled OOF R²',xlabel='Nested variable block');ax.axhline(0,color='black',lw=.6)
    finish(fig,'figure05','Recovery information under paired evaluation','core metrics.json','pooled OOF R2','control / +gust / +customers / both; separate populations')
    fig,axs=plt.subplots(1,2,figsize=(10,6));bounds=[]
    for ax,t in zip(axs,['E0','R0c']):
        dat=pd.read_csv(RUN/f'main_{t}/figure6_regional_reference.csv');dat=dat[dat.status.eq('descriptive_common_calendar')];patches=[];values=[]
        for row in dat.itertuples():
            if row.LAD21CD in geo:patches.append(PathPatch(geo[row.LAD21CD]));values.append(row.exp_mean_eta);bounds.append(geo[row.LAD21CD].vertices)
        pc=PatchCollection(patches,cmap='viridis',edgecolor='white',linewidth=.18);pc.set_array(np.array(values));ax.add_collection(pc);ax.autoscale_view();ax.set_aspect('equal');ax.set(title=t,xlabel='Easting (km, British National Grid)',ylabel='Northing (km)');fig.colorbar(pc,ax=ax,shrink=.65,label='exp(weighted mean eta)')
    finish(fig,'figure06','Regional reference surfaces; Buckinghamshire proxy retained','formal figure6 data; copied LAD21 geometry','exp(weighted mean eta)','common calendar; weather/log-C center; LAD21/23 compatibility unresolved')
    ratios=[]
    for g in ['main','weather']:
      for t in ['E0','R0c']:
        vals=read(RUN/f'{g}_{t}/figure7_gust_ratio.json');ratios.append((g+' '+t+' gust',vals['exponentiated_grid_max_min_ratio']))
        if t=='R0c':ratios.append((g+' R0c customers',read(RUN/f'{g}_{t}/figure7_reference.json')['exponentiated_grid_max_min_ratio']))
    fig,ax=plt.subplots(figsize=(9,4));ax.barh([r[0] for r in ratios],[r[1] for r in ratios],color='#2878a5');ax.set_xlabel('exp(max mean eta − min mean eta), 50-point p1–p99 grid');finish(fig,'figure07','Range of the fitted reference curves','formal figure7 reference JSON','exponentiated grid max/min ratio','not endpoint ratio or causal importance')
    fig,ax=plt.subplots(figsize=(8,4));xp=np.arange(2)
    for dx,key,label,color in [(-.17,'gust_given_customers','Gust | customers','#2878a5'),(.17,'customers_given_gust','Customers | gust','#d87930')]:ax.bar(xp+dx,[read(RUN/f'{g}_R0c/contributions.json')[key]*100 for g in ['main','weather']],width=.34,label=label,color=color)
    ax.set(xticks=xp,xticklabels=['Main','Weather'],ylabel='Conditional increment in pooled R² (percentage points)');ax.legend();finish(fig,'figure08','Conditional information contributions — point estimates','formal contributions.json','R2 percentage points','paired within each population; no uncertainty/stability claim')
    fig,axs=plt.subplots(2,2,figsize=(10,8))
    for i,kind in enumerate(['descriptive','OOF_diagnostic']):
      for j,t in enumerate(['E0','R0c']):
        s=pd.read_csv(RUN/f'main_{t}/figure9_{kind}_events.csv');assert s[ID].is_unique;ax=axs[i,j];h=ax.hexbin(s.y,s.prediction_eta,gridsize=45,mincnt=1,bins='log',cmap='viridis');lim=[min(s.y.min(),s.prediction_eta.min()),max(s.y.max(),s.prediction_eta.max())];ax.plot(lim,lim,'--',color='#c6543c',lw=.9);ax.set(xlabel='Observed ln(1+C)' if t=='E0' else 'Observed ln(D / hours)',ylabel='Predicted eta',title=f'{t}: {kind}; unique n={len(s):,}')
        assert s.was_in_this_fit.eq(kind=='descriptive').all();fig.colorbar(h,ax=ax,label='Count (log color)',shrink=.75)
    finish(fig,'figure09','Named-window predictions: distinct descriptive and date-OOF identities','formal figure9 event CSVs','eta vs log target; no double log','UNIQUE_ANY; overlaps listed once; no true process holdout')
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for ax,t in zip(axs,['E0','R0c']):
        for i,g in enumerate(['main','weather']):
            p=period[(period.group==g)&(period.target==t)];ax.plot(p.period,p.physical_quadratic_gust,marker='o',label=g)
        ax.set(title=t,ylabel='Quadratic coefficient in physical gust units (m/s)⁻²');ax.legend()
    finish(fig,'figure10','Period comparison using equivalent full-rank calendar bases','periods_v2 archives; period_comparison.csv','physical quadratic coefficient','each period own training scale; no overlapping-CV nominal intervals')
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,g in zip(axs,['main','weather']):
        tab=pd.read_csv(RUN/f'{g}_R0c/stage_composition.csv')
        for st,z in tab.groupby('stage_group'):ax.plot(z.customer_bin,z['mean'],marker='o',label=str(st))
        ax.set(title=g,xlabel='Common customer bins',ylabel='Mean recorded span (hours)');ax.tick_params(axis='x',rotation=25);ax.legend(title='Stage rows')
    finish(fig,'figureD1','Stage composition and restoration spans','formal stage_composition.csv','mean D hours','shared bins within population; descriptive, not repair actions')
    save(Q/'figures/FIGURE_MANIFEST.json',FIGS)
    # Contact sheet for visual review; scientific plots above remain standalone.
    fig,axs=plt.subplots(4,3,figsize=(16,16))
    for ax,row in zip(axs.flat,FIGS):ax.imshow(plt.imread(row['files'][0]));ax.set_title(row['figure']);ax.axis('off')
    axs.flat[-1].axis('off');fig.tight_layout();fig.savefig(Q/'figures/visual_contact_sheet.png',dpi=100);plt.close(fig)
    print('exported',len(FIGS),'figures, PNG/PDF',flush=True)
if __name__=='__main__':run()
