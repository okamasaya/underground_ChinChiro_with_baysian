#!/usr/bin/env python3
"""A15: exact loss probabilities conditional on each possible 456-dice role.

Profile A: pin > all other triples equally > 456 > points 6..1 > none > 123.
Profile B: pin > 666 > 555 > 444 > 333 > 222 > 456 > remaining roles.
Opponent is fair, at most three throws; equal strength draws, both finish.
"""

# Shared presentation policy: three decimals; counts and fractions stay exact.
import sys as _precision_sys
from pathlib import Path as _PrecisionPath
_precision_sys.path.insert(0, str(_PrecisionPath(__file__).resolve().parents[2] / 'analysis'))
from display_precision import install as _install_precision, fixed as _fmt_number, scientific as _fmt_scientific
_install_precision()
from pathlib import Path
import sys,csv,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'analysis'))
from chinchiro_model import CHEAT_ROLES,conditional_wdl,turn_distribution,overall_wdl,verify
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT=Path(__file__).resolve().parent;NAME='kaiji_a15_conditional_loss'
NAVY,AMBER,INK,GRAY='#285D79','#D88B35','#17212B','#6B7280'
LABELS=['Triple 444','Triple 555','Triple 666','456 role','Point 6','Point 5','Point 4']
plt.rcParams.update({'font.family':'Article JP Sans','font.size':9,'pdf.fonttype':42,
    'ps.fonttype':42,'text.color':INK,'axes.labelcolor':INK})

def main():
    verify();probs=turn_distribution((4,5,6));rows=[]
    for r in CHEAT_ROLES:
        item={'role':r,'p_456_role':str(probs[r])}
        for p in ('A','B'):
            for k,v in conditional_wdl(r,p).items():item[p+'_'+k]=str(v)
        rows.append(item)
    with (OUT/(NAME+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/(NAME+'.json')).write_text(json.dumps({'conditional':rows,
        'overall':{p:{k:str(v) for k,v in overall_wdl(p).items()} for p in ('A','B')}},indent=2))
    fig=plt.figure(figsize=(160/25.4,205/25.4));ax=fig.add_axes([.20,.43,.63,.36])
    fig.text(.5,.963,'Even 456 dice can lose',ha='center',fontsize=13,fontweight='bold')
    fig.text(.5,.929,'Loss probability conditional on your completed role',ha='center',fontsize=10)
    fig.text(.5,.899,'Fair opponent; at most three throws; both turns completed.',ha='center',color=GRAY)
    ys=np.arange(7)
    for profile,dy,col in [('A',-.16,NAVY),('B',.16,AMBER)]:
        vals=[float(conditional_wdl(r,profile)['loss']) for r in CHEAT_ROLES]
        ax.barh(ys+dy,vals,height=.27,color=col,label='A: equal triples' if profile=='A' else 'B: ordered triples')
        for yy,v in zip(ys+dy,vals):ax.text(v+.006,yy,f'{_fmt_number(100 * v)}%',va='center',fontsize=9,color=col)
    ax.set_yticks(ys,LABELS);ax.invert_yaxis();ax.set_xlim(0,.43)
    ax.set_xticks([0,.1,.2,.3,.4]);ax.set_xlabel('Probability of losing')
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',color='#E2E6EB');ax.set_axisbelow(True)
    ax.legend(loc='lower left',bbox_to_anchor=(-.1,1.01),ncol=2,frameon=False,fontsize=9)
    table_ax=fig.add_axes([.05,.16,.90,.20]);table_ax.axis('off')
    data=[]
    for label,r in zip(LABELS,CHEAT_ROLES):
        data.append([label,str(probs[r]),str(conditional_wdl(r,'A')['loss']),str(conditional_wdl(r,'B')['loss'])])
    tab=table_ax.table(cellText=data,colLabels=['Your role','P(role | 456)','Loss A','Loss B'],
        loc='center',cellLoc='center',colWidths=[.28,.27,.22,.23])
    tab.auto_set_font_size(False);tab.set_fontsize(9);tab.scale(1,1.35)
    for (row,col),cell in tab.get_celld().items():
        cell.set_edgecolor('#D8E1E8');cell.set_linewidth(.5)
        cell.set_facecolor('#EEF3F7' if row==0 else ('#FFFFFF' if row%2 else '#F7F9FB'))
        if row==0:cell.set_text_props(fontweight='bold')
    fig.text(.5,.103,'A: pin > all triples 2-6 equally > 456 > points 6...1 > none > 123.',ha='center',fontsize=9)
    fig.text(.5,.076,'B: pin > 666 > 555 > 444 > 333 > 222 > 456 > remaining roles.',ha='center',fontsize=9)
    fig.text(.5,.044,'Same strength is a draw. Fractions are exact; percentages are rounded.',ha='center',color=GRAY,fontsize=9)
    fig.text(.5,.020,'These are outcome probabilities, not payout-weighted expected net gains.',ha='center',color=GRAY,fontsize=9)
    fig.savefig(OUT/(NAME+'.pdf'));fig.savefig(OUT/(NAME+'.png'),dpi=400);plt.close(fig)
    print(json.dumps({'rows':rows,'overall':{p:{k:str(v) for k,v in overall_wdl(p).items()} for p in ('A','B')}},indent=2))

if __name__=='__main__':main()
