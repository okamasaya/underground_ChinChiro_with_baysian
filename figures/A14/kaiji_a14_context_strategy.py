#!/usr/bin/env python3
"""A14: stakes, observed wins/losses, and two strategy posteriors.

This is one fixed-seed synthetic sequence, not a reconstruction of the manga
or an estimate of detection power. Fair opponent; both turns finish; profile A.
Inference uses suspect throws and pre-outcome context, never latent dice type.
Run from any working directory. Shared exact model is in analysis/.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()
from pathlib import Path
import sys, json, csv
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'analysis'))
from chinchiro_model import context_records, verify, PRIOR, ETA_CONSTANT, SEED, OPPONENT_SEED
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, StrMethodFormatter

OUT=Path(__file__).resolve().parent
NAME='kaiji_a14_context_strategy'
NAVY,AMBER,PURPLE,GRAY,INK='#285D79','#D88B35','#74539A','#6B7280','#17212B'
plt.rcParams.update({'font.family':'Article JP Sans','font.size':9,'axes.labelsize':9,
    'xtick.labelsize':9,'ytick.labelsize':9,'pdf.fonttype':42,'ps.fonttype':42,
    'text.color':INK,'axes.labelcolor':INK})

def main():
    verify(); rows=context_records()
    (OUT/(NAME+'.json')).write_text(json.dumps({'synthetic':True,'seed':SEED,'opponent_seed':OPPONENT_SEED,
        'prior':str(PRIOR),'eta_constant':str(ETA_CONSTANT),'records':rows},indent=2))
    with (OUT/(NAME+'.csv')).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    fig,axs=plt.subplots(3,1,figsize=(160/25.4,218/25.4),gridspec_kw={'height_ratios':[1,1,1.55]})
    fig.subplots_adjust(left=.14,right=.97,bottom=.17,top=.86,hspace=.58)
    fig.suptitle('Ordinary play and high-stakes opportunities',y=.971,fontsize=12,fontweight='bold')
    fig.text(.5,.932,'One synthetic sequence; contexts fixed before outcomes.',ha='center',color=GRAY)
    fig.text(.5,.906,'$H_0$: always fair  |  $H_{1,C}$: fair normally, 90.000% 456 at marked turns',ha='center',fontsize=9)
    xs=[r['turn'] for r in rows]
    for ax in axs:
        for r in rows:
            if r['high_stakes']:ax.axvspan(r['turn']-.35,r['turn']+.35,color=AMBER,alpha=.13,lw=0)
        ax.set_xlim(.5,20.5);ax.xaxis.set_major_locator(FixedLocator(list(range(2,21,2))))
        ax.xaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',color='#E2E6EB',lw=.7);ax.set_axisbelow(True)
    axs[0].bar(xs,[r['stake'] for r in rows],width=.55,
        color=[AMBER if r['high_stakes'] else NAVY for r in rows])
    axs[0].set_yticks([1,10]);axs[0].set_ylim(0,11.5);axs[0].set_ylabel('Stake units')
    axs[0].set_title('A   Pre-announced stakes: 1 normally, 10 every fourth turn',loc='left',fontsize=9,fontweight='bold',pad=10)
    y={'win':1,'draw':0,'loss':-1}
    for status,marker,col in [('win','o',NAVY),('draw','s',GRAY),('loss','v','#BC5557')]:
        sub=[r for r in rows if r['result']==status]
        axs[1].scatter([r['turn'] for r in sub],[y[status]]*len(sub),s=30,marker=marker,color=col,zorder=3)
    axs[1].set_yticks([-1,0,1],['Loss','Draw','Win']);axs[1].set_ylim(-1.55,1.55)
    axs[1].set_title('B   Observed result against a fair opponent (ranking A)',loc='left',fontsize=9,fontweight='bold',pad=10)
    axs[2].plot([0]+xs,[float(PRIOR)]+[r['posterior_context'] for r in rows],'-o',ms=3,color=PURPLE,label=r'Context strategy $H_{1,C}$')
    axs[2].plot([0]+xs,[float(PRIOR)]+[r['posterior_constant'] for r in rows],'-s',ms=2.8,color=NAVY,label=r'Constant-use strategy $H_{1,G}$')
    axs[2].set_xlim(0,20.5);axs[2].xaxis.set_major_locator(FixedLocator(list(range(0,21,2))))
    axs[2].set_yticks([0,.25,.5,.75,1]);axs[2].set_ylim(-.03,1.03)
    axs[2].set_ylabel('Strategy posterior');axs[2].set_xlabel('Number of fully observed turns')
    axs[2].set_title('C   Common prior 0.100; different alternative hypotheses',loc='left',fontsize=9,fontweight='bold',pad=32)
    axs[2].legend(loc='lower left',bbox_to_anchor=(-.02,1.005),ncol=2,fontsize=8.5,frameon=False)
    fig.text(.5,.115,r'$H_{1,G}$: constant 456-use probability $\bar\eta=0.225$ (same schedule average).',ha='center',fontsize=9)
    fig.text(.5,.087,'Under the context strategy, ordinary turns have Bayes factor 1.',ha='center',color=PURPLE,fontsize=9)
    fig.text(.5,.059,'Full throw histories are used; the generated latent type is hidden from inference.',ha='center',color=GRAY,fontsize=9)
    fig.text(.5,.031,'Win/loss is shown for interpretation; no payout multipliers or net profit are assumed.',ha='center',color=GRAY,fontsize=9)
    fig.savefig(OUT/(NAME+'.pdf'));fig.savefig(OUT/(NAME+'.png'),dpi=400);plt.close(fig)
    print(json.dumps({'last':rows[-1],'outputs':NAME},indent=2))

if __name__=='__main__':main()
