"""A22: BKT state probabilities, next-answer forecasts and future first passages.
A23: exact conditional-forecast calibration monitor illustration.
Use the stored model calculations; no simulation rerun is needed for plotting.
Select a single figure with --figure A22 or --figure A23 (default: both).
PDF text is Unicode-searchable TrueType.
"""
from pathlib import Path
from fractions import Fraction as F
from math import comb, log10
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator,FuncFormatter
from figure_fonts import configure
from display_precision import fixed

configure()
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'analysis/bkt_sequential_validation.json').read_text())
NAVY,ORANGE,GREEN,GRAY='#225577','#c46b29','#37816b','#65717a'
plt.rcParams.update({'font.size':9,'axes.labelsize':9,'axes.titlesize':10,
                     'legend.fontsize':9,'axes.spines.top':False,'axes.spines.right':False})


def style(ax):
    ax.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=6))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:fixed(x)))
    ax.grid(alpha=.17)


def save(fig,code,name):
    target=ROOT/'figures'/code
    target.mkdir(exist_ok=True)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    outside=[]
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text():continue
        bounds=text.get_window_extent(renderer)
        if bounds.x0<0 or bounds.y0<0 or bounds.x1>fig.bbox.width+1 or bounds.y1>fig.bbox.height+1:
            outside.append(text.get_text())
    assert not outside,(code,outside)
    for ext in ('pdf','png','svg'):
        fig.savefig(target/f'{name}.{ext}',dpi=350,facecolor='white')
    plt.close(fig)


def a22():
    from bkt_sequential_validation import OBS, PARAMS, exact_filter, hidden_enumeration
    curves={key:exact_filter(params,OBS) for key,params in PARAMS.items()}
    for key,params in PARAMS.items():
        for n,row in enumerate(curves[key],1):
            likelihood,posterior=hidden_enumeration(params,OBS[:n])
            assert likelihood==row['likelihood'] and posterior==row['posterior']
            for field in ('posterior','predict_next','q_next','likelihood'):
                assert row[field]==F(DATA['exact_eight_answer_rows'][key][n-1][field])
    fig=plt.figure(figsize=(160/25.4,250/25.4))
    fig.text(.5,.97,'過去の尤度が近くても、状態の解釈は分かれる',ha='center',fontsize=12,fontweight='bold')
    fig.text(.5,.935,'状態の推定・次回予測・将来のモデル比較を分ける',ha='center',color=GRAY)
    ax=fig.add_axes([.16,.69,.78,.18])
    for key,c,label in [('baseline',NAVY,'基準'),('alternative',ORANGE,'別解')]:
        rows=curves[key]
        ys=[float(F(row['posterior'])) for row in rows]
        ax.plot(range(1,9),ys,'-o',color=c,ms=3)
        ax.annotate(f'{label}：'+r'$p_8$'+f'={fixed(ys[-1])}',(8,ys[-1]),
                    xytext=(-4,6),textcoords='offset points',ha='right',color=c)
    ax.set(xlim=(.8,8.2),ylim=(0,1.16),xlabel='観測した解答数',ylabel='現在の習得状態の確率')
    ax.set_yticks([0,.25,.5,.75,1])
    ax.set_title('A　分数による厳密な状態推定',loc='left',pad=12)
    style(ax);ax.set_xticks(range(1,9))
    for x,y in enumerate(DATA['responses'],1):
        fig.text(.16+.78*(x-.8)/7.4,.907,'正' if y else '誤',ha='center',color=GREEN if y else ORANGE)
    forecast=fig.add_axes([.16,.425,.78,.17])
    for key,c,label in [('baseline',NAVY,'基準'),('alternative',ORANGE,'別解')]:
        ys=[float(row['predict_next']) for row in curves[key]]
        forecast.plot(range(1,9),ys,'-o',color=c,ms=3)
        forecast.annotate(f'{label}：'+r'$r_9$'+f'={fixed(ys[-1])}',(8,ys[-1]),
                          xytext=(-4,6),textcoords='offset points',ha='right',color=c)
    forecast.set(xlim=(.8,8.2),ylim=(0,1.16),xlabel='観測した解答数（その次の問題を予測）',
                 ylabel='次回正答の予測確率')
    forecast.set_yticks([0,.25,.5,.75,1])
    forecast.set_title('B　学習遷移後の観測予測：状態確率とは異なる',loc='left',pad=10)
    style(forecast);forecast.set_xticks(range(1,9))
    fig.text(.5,.365,'過去8回答の尤度比：1.000（差は約 '+r'$4.432\times10^{-5}$'+'）',ha='center')
    ax2=fig.add_axes([.16,.14,.78,.16])
    times=np.load(ROOT/'analysis/bkt_future_first_passage.npz')
    ns=np.arange(201)
    for key,c,label in [('baseline',NAVY,'基準が真'),('alternative',ORANGE,'別解が真')]:
        t=times[f'{key}_{key}_BF10']
        count=np.bincount(t,minlength=402).cumsum()[:201]
        p=count/len(t);z=1.959963984540054
        center=(p+z*z/(2*len(t)))/(1+z*z/len(t))
        half=z*np.sqrt(p*(1-p)/len(t)+z*z/(4*len(t)**2))/(1+z*z/len(t))
        ax2.fill_between(ns,center-half,center+half,color=c,alpha=.22,lw=0)
        ax2.plot(ns,p,color=c,label=label,lw=1.5)
    ax2.set(xlim=(0,200),ylim=(0,1.03),xlabel='追加の解答数',ylabel='正しいモデル側への初到達率')
    ax2.set_title('C　追加回答で、正しい方向の将来尤度比が10倍に達するまで',loc='left',pad=10)
    ax2.legend(loc='lower right',frameon=False);style(ax2)
    fig.text(.09,.068,'A/Bの2曲線は固定候補の比較であり、信用区間ではない。\nCは保存済み各20万系列。帯は到達率の点ごとの95.000% Wilson区間。\n同じスキル・固定パラメータの例であり、状態の正解を観測した検証ではない。',
             va='top',fontsize=9,color=GRAY,linespacing=1.65)
    save(fig,'A22','kaiji_a22_bkt_ambiguity_future')


def log_wealth_quantiles(p,n):
    if n==0:return [0.,0.,0.]
    cumulative=F(0);result=[]
    # k counts incorrect answers; wealth increases with k.
    targets=iter((F(1,10),F(1,2),F(9,10)))
    target=next(targets)
    for k in range(n+1):
        cumulative+=comb(n,k)*(1-p)**k*p**(n-k)
        while cumulative>=target:
            result.append((n-k)*log10(.75)+k*log10(2))
            try:target=next(targets)
            except StopIteration:return result
    raise AssertionError('quantile not found')


def a23():
    fig=plt.figure(figsize=(160/25.4,225/25.4))
    fig.text(.5,.971,'次回予測を、いつでも有効な検定で監視する',ha='center',fontsize=12,fontweight='bold')
    fig.text(.5,.932,'予測 r=0.800 ／ 比較する予測 s=0.600 ／ 警報閾値100',ha='center',color=GRAY)
    axes=[fig.add_axes([.17,.56,.77,.28]),fig.add_axes([.17,.20,.77,.25])]
    ns=np.arange(101)
    for p,c,label in [(F(4,5),NAVY,'真の正答率0.800'),(F(3,5),ORANGE,'真の正答率0.600')]:
        qs=np.array([log_wealth_quantiles(p,int(n)) for n in ns])
        axes[0].fill_between(ns,qs[:,0],qs[:,2],color=c,alpha=.13)
        axes[0].plot(ns,qs[:,1],color=c,label=label)
        rows=DATA['calibration_constant_forecast'][str(p)]
        axes[1].plot(ns,[0.]+[row['detection'] for row in rows],color=c,label=label)
    axes[0].axhline(2,color=GRAY,lw=1,ls='--')
    axes[0].set(xlim=(0,100),xlabel='観測した解答数',ylabel='証拠量 '+r'$\log_{10}M_n$')
    axes[0].set_title('A　中央値と各時点の10.000–90.000%分位帯',loc='left',pad=10)
    axes[0].legend(loc='lower left')
    axes[1].axhline(.01,color=GRAY,lw=1,ls='--')
    axes[1].set(xlim=(0,100),ylim=(0,1.03),xlabel='観測した解答数',ylabel='閾値100への初到達率')
    axes[1].set_title('B　整数再帰で求めた誤警報率と検知率',loc='left',pad=10)
    axes[1].legend(loc='upper left')
    for ax in axes:style(ax)
    fig.text(.09,.113,'上段の帯は観測系列のばらつき。計算誤差や信用区間ではない。\n下段は期間内の初到達確率。帰無仮説下では期間無制限でも1.000%以下。\nこの一定予測の数値例と、時変のBKT予測に使える定理を区別する。',
             va='top',fontsize=9,color=GRAY,linespacing=1.65)
    save(fig,'A23','kaiji_a23_predictive_calibration')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figure',choices=('A22','A23','all'),default='all')
    args=parser.parse_args()
    if args.figure in ('A22','all'): a22()
    if args.figure in ('A23','all'): a23()
