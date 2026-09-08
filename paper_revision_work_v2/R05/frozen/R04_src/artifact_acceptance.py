from common import *
from diagnostics import cluster_covariance
from scipy import stats
import matplotlib.pyplot as plt
import shutil

def run():
    e=events();rows=[];checks=[];fig,axs=plt.subplots(2,2,figsize=(12,8));plt.rcParams['pdf.fonttype']=42
    for i,g in enumerate(['main','weather']):
        folder=RUN/f'{g}_R0c';d=members(e,g,'R0c');edges=read(folder/'stage_manifest.json')['shared_customer_bin_edges'];bins=pd.cut(d[C],edges,include_lowest=True);actual=d.groupby(bins,observed=True)[D].agg(['count','mean']);actual.index=actual.index.astype(str)
        p=pd.read_csv(folder/'stage_pooled.csv').set_index('customer_bin').loc[actual.index];assert np.array_equal(p['count'],actual['count']);assert np.allclose(p['mean'],actual['mean'],atol=1e-12)
        s=pd.read_csv(folder/'stage_composition.csv');s['numeric_lower']=s.customer_bin.map(lambda z:float(z[1:].split(',')[0]));s=s.sort_values('numeric_lower')
        for st,z in s.groupby('stage_group'):axs[i,0].plot(z.customer_bin,z['mean'],marker='o',label=str(st))
        axs[i,0].legend(title='Stage rows');axs[i,1].plot(p.index,p['mean'],marker='o',color='#d87930')
        for j in [0,1]:axs[i,j].set(title=g+(' by stage' if j==0 else ' pooled'),xlabel='Customer bins in numerical order',ylabel='Mean recorded span (hours)');axs[i,j].tick_params(axis='x',rotation=25)
        checks.append({'group':g,'bin_edges':edges,'bin_count_sum':int(p['count'].sum()),'n':len(d),'means_ascending_bins':p['mean'].tolist(),'actual_bin_counts_means_verified':True})
    fig.suptitle('Stage composition and pooled means within each population');fig.tight_layout(rect=[0,.04,1,.95]);fig.text(.01,.008,'B1 all-valid | Descriptive stage rows and spans | Shared numerical bins within each population',fontsize=8)
    ar=Q/'figures/archive_before_bin_order_fix';ar.mkdir(exist_ok=True)
    for ext in ['png','pdf']:
        p=Q/'figures'/f'figureD1.{ext}';shutil.copyfile(p,ar/p.name);fig.savefig(p,dpi=180,bbox_inches='tight')
    plt.close(fig)
    # Five-fold coefficient summaries use archived fits; main covariances reconstructed without refitting.
    summaries=[]
    for group in ['six_groups','main']:
        for fold in range(5):
            path=Q/'supplements_v1'/f'six_group_{fold}.json' if group=='six_groups' else RUN/'main_R0c'/f'model_fold{fold}_GK.json';m=read(path);co=np.array(m['parameters']);d=e[e[ID].isin(m['training_ids'])]
            if group=='six_groups':cov=np.array(m['LAD_CR1'])
            else:x=design(d,m['preprocessor'],'GK');cov=cluster_covariance(x,target(d,'R0c')-x.to_numpy()@co,d.LAD21CD)
            for term in ['zG','zG2']:
                j=m['columns'].index(term);se=np.sqrt(cov[j,j]);p=2*stats.norm.sf(abs(co[j]/se));rows.append({'group':group,'fold':fold,'term':term,'coefficient':co[j],'SE_LAD_CR1':se,'p_normal_Wald':p,'training_n':len(d),'source_archive':str(path)})
    rf=pd.DataFrame(rows)
    for (group,term),r in rf.groupby(['group','term']):summaries.append({'group':group,'term':term,'evaluation_n':117108 if group=='six_groups' else 60436,'folds':5,'positive_folds':int(r.coefficient.gt(0).sum()),'negative_folds':int(r.coefficient.lt(0).sum()),'significant_folds_p_normal_lt_005':int(r.p_normal_Wald.lt(.05).sum()),'mean_coefficient':r.coefficient.mean(),'SD_ddof1':r.coefficient.std(ddof=1),'coefficient_of_variation_pct':100*r.coefficient.std(ddof=1)/abs(r.coefficient.mean()),'interpretation':'overlapping training folds; descriptive summaries only; all_valid current counterpart'})
    table(Q/'tables/AppendixC_fold_coefficients.csv',rf);table(Q/'tables/AppendixC_fold_summary.csv',pd.DataFrame(summaries));save(Q/'checks/artifact_acceptance.json',{'fits':0,'bin_validation':checks,'fold_summary_source':'archived models; covariance only for main folds, no refit'})
    mf=read(Q/'figures/FIGURE_MANIFEST.json');row=next(x for x in mf if x['figure']=='figureD1');row.update(producer=str(Path(__file__)),reference='numerically ordered frozen edges; actual counts and means independently derived',visual_review='pending_bin_order_review');save(Q/'figures/FIGURE_MANIFEST.json',mf)
    print('bin ordering verified; five-fold summaries produced without fits',flush=True)
if __name__=='__main__':run()
