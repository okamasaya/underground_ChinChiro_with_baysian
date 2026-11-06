"""Four reproducible Japanese figures; no article PDF is changed or created.

A18: hypothesis comparison versus dynamic knowledge-state estimation.
A19: distinct sources of uncertainty and validation.
A20: an assumed causal graph, not an identified empirical result.
A21: exact BKT parameter-sensitivity illustration, not a credible interval.
Run with Python 3 + Matplotlib. Outputs SVG/PNG/searchable PDF, CSV/JSON and checks.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal, localcontext, ROUND_HALF_UP
from itertools import product
import csv
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import MaxNLocator, FuncFormatter

from figure_fonts import configure
configure()

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures'
INK,NAVY,ORANGE,GREEN,PURPLE,GRAY,RED='#17212b','#2b5d7e','#d98c3f','#37816b','#6f4a8e','#6b7280','#c4474b'
plt.rcParams.update({'font.family':'Article JP Sans','font.size':9,
    'text.color':INK,'axes.labelcolor':INK,'axes.titlesize':10,
    'svg.fonttype':'path','mathtext.fontset':'dejavusans'})
RESPONSES=(1,1,0,1,0,1,1,1)
MODELS={
 'baseline':{'label':'基準の仮定','p0':F(1,5),'learn':F(3,20),'guess':F(1,4),'slip':F(1,10)},
 'higher_guess':{'label':'偶然正答が多い仮定','p0':F(1,5),'learn':F(3,20),'guess':F(2,5),'slip':F(1,10)},
 'higher_slip':{'label':'習得後の誤答が多い仮定','p0':F(1,5),'learn':F(3,20),'guess':F(1,4),'slip':F(3,10)},
}


def fixed(x):
    with localcontext() as ctx:
        ctx.prec=60
        if isinstance(x,F):x=Decimal(x.numerator)/Decimal(x.denominator)
        else:x=Decimal(str(x))
        return format(x.quantize(Decimal('.001'),rounding=ROUND_HALF_UP),'.3f')


def canvas(title,subtitle,height=210):
    fig=plt.figure(figsize=(160/25.4,height/25.4),dpi=400)
    fig.patch.set_facecolor('white')
    fig.text(.5,.967,title,ha='center',va='top',fontsize=13,fontweight='bold')
    fig.text(.5,.925,subtitle,ha='center',va='top',fontsize=9,color=GRAY)
    return fig


def box(fig,x,y,w,h,text,fill='#f4f7fa',edge='#c6d0d9',color=INK,size=9,dashed=False):
    patch=FancyBboxPatch((x-w/2,y-h/2),w,h,transform=fig.transFigure,
        boxstyle='round,pad=0.008,rounding_size=0.008',facecolor=fill,
        edgecolor=edge,linewidth=.9,linestyle='--' if dashed else '-')
    fig.add_artist(patch)
    fig.text(x,y,text,ha='center',va='center',color=color,fontsize=size,linespacing=1.55)


def arrow(fig,a,b,color=GRAY,dashed=False,rad=0):
    fig.add_artist(FancyArrowPatch(a,b,transform=fig.transFigure,
        arrowstyle='-|>',mutation_scale=10,color=color,lw=1.25,
        linestyle='--' if dashed else '-',connectionstyle=f'arc3,rad={rad}'))


def save(fig,code,basename):
    target=OUT/code;target.mkdir(parents=True,exist_ok=True)
    fig.canvas.draw()
    # Check all text extents, including mathematical labels, before export.
    renderer=fig.canvas.get_renderer();bad=[]
    for item in fig.findobj(matplotlib.text.Text):
        if not item.get_visible() or not item.get_text():continue
        bbox=item.get_window_extent(renderer)
        if bbox.x0 < -2 or bbox.y0 < -2 or bbox.x1>fig.bbox.width+2 or bbox.y1>fig.bbox.height+2:
            bad.append(item.get_text())
    assert not bad,(code,bad)
    for ext in ('svg','png','pdf'):
        fig.savefig(target/f'{basename}.{ext}',dpi=400,facecolor='white')
    plt.close(fig)


def a18():
    fig=canvas('見えない状態を、記録から推定する','カイジの仮説比較と ALP-BKT の状態推定',210)
    fig.text(.07,.858,'A　カイジ：固定した戦略仮説の比較',fontweight='bold',fontsize=10)
    columns=(.19,.50,.81)
    for x,title,body in zip(columns,('隠れた対象','観測記録','推定する量'),
       ('通常賽だけか\n456賽を混ぜるか','出目・賭け金・局面\n三好が残す記録',r'$P(H_1\mid D_{1:t})$'+'\n戦略仮説の事後確率')):
        fig.text(x,.814,title,ha='center',fontsize=9,color=NAVY)
        box(fig,x,.738,.256,.116,body)
    arrow(fig,(.328,.738),(.36,.738));arrow(fig,(.638,.738),(.67,.738))
    fig.text(.5,.655,'カイジの着眼点は、比較する仮説と局面の選び方に対応する。',ha='center',fontsize=9)
    fig.text(.07,.594,'B　ALP-BKT：学習で変化する状態の推定',fontweight='bold',fontsize=10)
    for x,title,body in zip(columns,('隠れた対象','観測記録','推定する量'),
       ('特定スキルの\n習得状態 '+r'$L_t$','正誤・項目・提示条件\n基本BKTは正誤列',r'$P(L_t=1\mid Y_{1:t})$'+'\n現在の習得状態の確率')):
        fig.text(x,.552,title,ha='center',fontsize=9,color=GREEN)
        box(fig,x,.476,.256,.116,body,fill='#f0f7f4',edge='#b3d1c5')
    arrow(fig,(.328,.476),(.36,.476),GREEN);arrow(fig,(.638,.476),(.67,.476),GREEN)
    fig.text(.5,.393,'正誤で状態を更新し、次の機会までの学習遷移を別に入れる。',ha='center',fontsize=9)
    box(fig,.5,.274,.85,.13,'共通する設計\n観測ログと推定結果を分ける ／ 尤度・事前分布・対象を明示する\n将来の記録で検証し、推定を支援の判断へつなぐ',size=9)
    fig.text(.07,.141,'対応するのは推論の構造。戦略の確率と時変状態の確率は別の対象。\n正答率・自己申告の自信・一般的な理解度も、それぞれ区別する。',fontsize=9,color=GRAY,linespacing=1.6)
    save(fig,'A18','kaiji_a18_latent_state_bridge')


def a19():
    fig=canvas('不確かさと誤差を、発生源ごとに評価する','同じ「誤差」という言葉で、異なる対象を混ぜない',225)
    rows=[
      ('観測列のばらつき','同じ条件でも正誤や出目は変動する。','反復生成・将来予測の較正・系列間の分布',NAVY),
      ('状態・パラメータの不確かさ','習得状態 '+r'$L_t$'+' と未知の '+r'$\theta$'+' を区別する。','状態事後確率・パラメータ事後分布・予測分布',PURPLE),
      ('近似計算の誤差','有限回のMCMC、数値積分、丸めに由来する。','MCSE・ESS・独立実装との照合・厳密再帰',GREEN),
      ('モデル・測定・選択によるずれ','難易度・忘却・採点・欠測・出題方針の不一致。','感度分析・外部検証・共通項目・条件別評価',ORANGE),
    ]
    for j,(title,body,method,c) in enumerate(rows):
        y=.804-j*.157
        box(fig,.5,y,.85,.128,'',edge=c,fill='#fafbfd')
        fig.text(.095,y+.039,title,color=c,fontweight='bold',fontsize=10,va='center')
        fig.text(.095,y,body,fontsize=9,va='center')
        fig.text(.095,y-.038,'評価：'+method,fontsize=9,va='center')
    fig.text(.5,.202,r'$\mathrm{Var}(L_t\mid D)=E_{\theta\mid D}[p_t(\theta)\{1-p_t(\theta)\}]$'+'\n'+
        r'$+\ \mathrm{Var}_{\theta\mid D}[p_t(\theta)]$',ha='center',va='center',fontsize=10,linespacing=1.7)
    fig.text(.5,.137,r'$p_t(\theta)=P(L_t=1\mid D,\theta)$',ha='center',fontsize=9)
    fig.text(.07,.075,'上式はモデル内の全分散の分解。計算誤差やモデルのずれまで含まない。\n計算を長く回しても、未知の系統的なずれが自動的に小さくなるわけではない。',fontsize=9,color=GRAY,linespacing=1.5)
    save(fig,'A19','kaiji_a19_uncertainty_layers')


def a20():
    fig=canvas('状態を推定することと、介入の効果を知ること','例：解説を変えると、次回の共通問題の成績は改善するか',220)
    box(fig,.5,.785,.44,.095,'観測履歴 '+r'$H_t$'+'\n過去の正誤・問題・提示条件',edge=NAVY)
    box(fig,.20,.565,.285,.105,'介入 '+r'$A_t$'+'\n解説・出題方法の選択',edge=GREEN,fill='#f0f7f4')
    box(fig,.80,.565,.285,.105,'外部の結果 '+r'$Y_{t+1}$'+'\n次回の共通問題で確認',edge=NAVY)
    box(fig,.5,.345,.44,.095,'未観測の要因 '+r'$U$'+'\n準備度・動機・環境など',edge=ORANGE,fill='#fff8f0',dashed=True)
    arrow(fig,(.37,.73),(.22,.625),NAVY);arrow(fig,(.63,.73),(.78,.625),NAVY)
    arrow(fig,(.35,.565),(.65,.565),GREEN)
    arrow(fig,(.37,.4),(.22,.505),ORANGE,True);arrow(fig,(.63,.4),(.78,.505),ORANGE,True)
    fig.text(.5,.596,'効果を知りたい経路',ha='center',color=GREEN,fontsize=9)
    fig.text(.5,.247,r'$P(Y_{t+1}\mid A_t,H_t)\quad\overset{?}{=}\quad P(Y_{t+1}\mid\mathrm{do}(A_t),H_t)$',ha='center',va='center',fontsize=10)
    fig.text(.07,.205,'図は想定した因果構造であり、実データから同定した結果ではない。\n無作為割付、または交換可能性・正値性・一貫性などの条件を検討する。\nBKTの推定値だけで調整しても、未観測の交絡が消えるとは限らない。',fontsize=9,va='top',linespacing=1.7)
    fig.text(.07,.055,'効果の評価先は共通の将来課題。推定した習得確率を、そのまま真値に使わない。',fontsize=9,color=GRAY)
    save(fig,'A20','kaiji_a20_causal_extension')


def filter_bkt(params):
    prior=params['p0'];g,s,t=params['guess'],params['slip'],params['learn']
    rows=[{'trial':0,'response':None,'prior':prior,'posterior':prior,
           'predict_next':g+(1-s-g)*prior}]
    for i,y in enumerate(RESPONSES,1):
        a=(1-s if y else s)*prior
        b=(g if y else 1-g)*(1-prior)
        posterior=a/(a+b)
        prior_next=posterior+(1-posterior)*t
        rows.append({'trial':i,'response':y,'prior':prior,'posterior':posterior,
                     'predict_next':g+(1-s-g)*prior_next})
        prior=prior_next
    return rows


def enumerate_posterior(params,observations):
    evidence=numerator=F(0)
    for states in product((0,1),repeat=len(observations)):
        w=params['p0'] if states[0] else 1-params['p0']
        for i,(l,y) in enumerate(zip(states,observations)):
            if i:
                prev=states[i-1]
                w*=F(l==1) if prev else (params['learn'] if l else 1-params['learn'])
            correct=1-params['slip'] if l else params['guess']
            w*=correct if y else 1-correct
        evidence+=w
        numerator+=w*states[-1]
    assert evidence>0
    return numerator/evidence


def a21():
    curves={k:filter_bkt(v) for k,v in MODELS.items()};checks=0
    for key,params in MODELS.items():
        for t in range(1,len(RESPONSES)+1):
            assert enumerate_posterior(params,RESPONSES[:t])==curves[key][t]['posterior']
            checks+=1
    assert curves['baseline'][1]['posterior']==F(9,19)
    assert curves['baseline'][1]['predict_next']==F(463,760)
    raw=[]
    for key,rows in curves.items():
        for r in rows:
            raw.append({'model':key,**{k:str(v) if isinstance(v,F) else v for k,v in r.items()},
                'posterior_float':float(r['posterior']),'predict_next_float':float(r['predict_next'])})
    (ROOT/'analysis/bkt_sensitivity.json').write_text(json.dumps({'responses':RESPONSES,
        'parameters':{k:{n:str(v) if isinstance(v,F) else v for n,v in p.items()} for k,p in MODELS.items()},
        'rows':raw,'validation':{'exact_filter_vs_state_path_enumeration':checks}},ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'analysis/bkt_sensitivity.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(raw[0]));writer.writeheader();writer.writerows(raw)
    fig=canvas('同じ正誤列でも、仮定で推定が変わる','基本BKT・忘却なし・1問題1スキルの説明用計算',220)
    fig.text(.5,.867,r'$P(L_1=1)=0.200,\quad T=0.150$',ha='center',fontsize=10)
    fig.text(.5,.829,'基準 G=0.250, S=0.100 ／ 高い偶然正答 G=0.400 ／ 高い誤答 S=0.300',ha='center',fontsize=9)
    colors=(NAVY,ORANGE,PURPLE)
    ax=fig.add_axes([.16,.485,.80,.25]);ax2=fig.add_axes([.16,.155,.80,.235])
    for (key,params),c in zip(MODELS.items(),colors):
        rows=curves[key];x=[r['trial'] for r in rows]
        ax.plot(x,[float(r['posterior']) for r in rows],'-o',ms=3,c=c,label=params['label'])
        ax2.plot(x,[float(r['predict_next']) for r in rows],'-o',ms=3,c=c)
    for target in (ax,ax2):
        target.set_xlim(0,8);target.set_ylim(0,1.03);target.grid(alpha=.17)
        target.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=8))
        target.yaxis.set_major_formatter(FuncFormatter(lambda x,p:fixed(x)))
        target.spines[['top','right']].set_visible(False)
        target.set_xlabel('観測した解答数（0は初期値）')
        for t in (3,5):target.axvline(t,ls=':',color=RED,alpha=.5,lw=.8)
    ax.set_ylabel('現在の習得状態の確率');ax.set_title('A　正誤を観測した後の状態推定',loc='left')
    ax.legend(loc='lower right',fontsize=9)
    ax2.set_ylabel('次の問題の正答確率');ax2.set_title('B　状態と観測モデルから作る次回予測',loc='left')
    for i,y in enumerate(RESPONSES,1):
        fig.text(.16+.80*i/8,.774,'正' if y else '誤',ha='center',color=GREEN if y else RED,fontsize=9)
    fig.text(.07,.067,'線の違いはパラメータの感度比較。信用区間や実測の理解度ではない。\n有限状態の厳密再帰を全状態経路の列挙と照合。MCMCは使用していない。',fontsize=9,color=GRAY,linespacing=1.6)
    save(fig,'A21','kaiji_a21_bkt_sensitivity')
    print('BKT exact comparisons:',checks)
    for key,rows in curves.items():print(key,'p8',fixed(rows[-1]['posterior']),'predict9',fixed(rows[-1]['predict_next']))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('figure',nargs='?',choices=('A18','A19','A20','A21','all'),default='all')
    selected=parser.parse_args().figure
    for code,func in (('A18',a18),('A19',a19),('A20',a20),('A21',a21)):
        if selected in ('all',code):func()
