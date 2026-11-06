"""Japanese scientific figures for exact detection-performance calculations."""
from pathlib import Path
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
from display_precision import fixed

ROOT = Path(__file__).resolve().parents[1]
NAVY, ORANGE, GREEN, GRAY = '#225577', '#c46b29', '#37816b', '#65717a'


def setup():
    from figure_fonts import configure
    configure()
    plt.rcParams.update({'font.family':'Article JP Sans','font.size':9,
        'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':9,
        'pdf.fonttype':42,'text.color':'#17212b','axes.spines.top':False,
        'axes.spines.right':False,'mathtext.fontset':'dejavusans'})


def style(ax, counts=True, percent=False):
    ax.grid(alpha=.18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:fixed(x)))
    if counts:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=6))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x:.0f}'))
    if percent:
        ax.set_ylim(-2,102)


def save(fig, code, name):
    dest=ROOT/'figures'/code
    dest.mkdir(exist_ok=True)
    for ext in ('pdf','png'):
        fig.savefig(dest/f'{name}.{ext}',dpi=250,facecolor='white')
    plt.close(fig)


def make_a16():
    setup()
    d=json.loads((ROOT/'analysis/sequential_performance.json').read_text())
    fig,axes=plt.subplots(2,1,figsize=(160/25.4,210/25.4))
    fig.subplots_adjust(left=.17,right=.96,top=.86,bottom=.25,hspace=.56)
    fig.suptitle('単一系列から、検知までの分布へ',x=.5,y=.975,fontsize=14,fontweight='bold')
    fig.text(.5,.930,'事前確率 0.100 ／ 使用率 0.900 ／ 事後確率の閾値 0.990',ha='center')
    q=d['pointwise_quantiles']; n=[r['n'] for r in q]
    ax=axes[0]
    ax.fill_between(n,[r['lo'] for r in q],[r['hi'] for r in q],color=NAVY,alpha=.18,label='各時点の 10.000–90.000% 分位帯')
    ax.plot(n,[r['median'] for r in q],color=NAVY,label='各時点の中央値')
    k=[t-(t>=12) for t in n]
    ax.plot(n,[math.log10(1/9)+v*math.log10(7.3)-(t-v) for t,v in zip(n,k)],color=ORANGE,lw=1.4,label='保存系列（一定使用率の例）')
    ax.axhline(math.log10(99),color=GRAY,ls='--',lw=1)
    ax.set(title='A　事後オッズの常用対数：系列間のばらつき',xlabel='観測した手番数',ylabel=r'$\log_{10}\{p_n/(1-p_n)\}$')
    ax.set_xlim(0,20);style(ax);ax.legend(loc='upper left',fontsize=8)
    ax=axes[1]
    x=[r['n'] for r in d['h1'][:20]]
    y=[100*r['detection'] for r in d['h1'][:20]]
    ax.step(x,y,where='post',color=GREEN,lw=2)
    ax.scatter([4,10,20],[y[3],y[9],y[19]],color=GREEN,zorder=3)
    ax.annotate('4手番まで：69.332%',(4,y[3]),xytext=(6,42),arrowprops={'arrowstyle':'-','color':GRAY},fontsize=9)
    ax.set(title='B　不正戦略の下で、一度でも閾値に到達する確率',xlabel='観測の上限 N（手番）',ylabel='累積検知率（%）')
    ax.set_xlim(0,20);style(ax,percent=True)
    fig.text(.11,.180,'通常賽だけの場合：20手番以内の誤警報率 0.041%\n'
             '時間を無制限に延ばした場合も、Ville上界は 0.112%\n'
             '検知時刻の中央値・最頻値：4手番\n'
             r'$E[\min(\tau,100)]\simeq4.856$ 手番',fontsize=9,va='top',linespacing=1.7)
    fig.text(.11,.040,'分位帯は各時点の系列間分布。全時点を同時に覆う帯とは異なる。\n全履歴を保持し、各手番で同じ率で独立に一式を選ぶモデル。',fontsize=8.5,color=GRAY,va='bottom')
    save(fig,'A16','kaiji_a16_detection_distribution')


def make_a17():
    setup()
    d=json.loads((ROOT/'analysis/sequential_performance.json').read_text())
    rows=d['frequency']; x=[r['eta']*100 for r in rows]
    fig,axes=plt.subplots(2,1,figsize=(160/25.4,205/25.4))
    fig.subplots_adjust(left=.17,right=.96,top=.85,bottom=.23,hspace=.56)
    fig.suptitle('使用率と観測者の仮説が検知率を変える',y=.975,fontsize=13,fontweight='bold')
    fig.text(.5,.928,'事前確率 0.100 ／ 事後確率の閾値 0.990 ／ 各手番で独立に選択',ha='center')
    ax=axes[0]
    for n,c in ((20,ORANGE),(100,NAVY),(1000,GREEN)):
        ax.plot(x,[100*r[f'matched_{n}'] for r in rows],color=c,marker='o',ms=2.6,label=f'{n}手番以内')
    ax.set(title='A　真の使用率を想定した仮説：観測期間による変化',xlabel='456賽の使用率（%）',ylabel='累積検知率（%）')
    ax.set_xlim(0,100);style(ax,counts=False,percent=True)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:fixed(x)))
    ax.legend(loc='lower right')
    ax=axes[1]
    for key,label,c in (('matched','真の使用率を想定',NAVY),('uniform','使用率は未知（一様事前分布）',GREEN),('fixed090','使用率を 90.000% に固定',ORANGE)):
        ax.plot(x,[100*r[f'{key}_100'] for r in rows],color=c,marker='o',ms=2.6,label=label)
    ax.set(title='B　100手番以内：比較する仮説による変化',xlabel='実際の456賽使用率（%）',ylabel='累積検知率（%）')
    ax.set_xlim(0,100);style(ax,counts=False,percent=True)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:fixed(x)))
    ax.legend(loc='lower right',fontsize=8.3)
    fig.text(.11,.170,'使用率 10.000%・100手番以内の例\n'
        '真の使用率を想定：9.915% ／ 未知率を積分：8.908%\n'
        '使用率90.000%に固定：0.483%',fontsize=9,va='top',linespacing=1.7)
    fig.text(.11,.040,'曲線は表示点を結んだもの。各点の初到達確率は整数再帰で計算。\n心理的な気付き率の実測値ではなく、明示した判定器の比較である。',fontsize=8.5,color=GRAY,va='bottom')
    save(fig,'A17','kaiji_a17_frequency_sensitivity')


if __name__=='__main__':
    make_a16();make_a17()
