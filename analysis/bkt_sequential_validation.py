"""Finite-data BKT ambiguity, prospective separation, and calibration tests.

Eight-answer calculations use Fractions and independent hidden-path enumeration.
Prospective BKT first passages use independent Monte Carlo trajectories from the
conditional predictive law, keeping both filters and learning transitions active.
A separate constant-forecast calibration example has exact integer recursion.
All monitor choices are fixed before the future answers; future LR starts at 1.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
from math import log, sqrt, comb, factorial
import csv
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OBS = (1, 1, 0, 1, 0, 1, 1, 1)
PARAMS = {
    'baseline': dict(G=F(1,4), S=F(1,10), T=F(3,20), q1=F(1,5)),
    'alternative': dict(G=F(83,200), S=F(1,25), T=F(1,50), q1=F(1,10)),
}
SEED, REPLICATES, HORIZON = 2026110302, 200000, 400


def step(q, y, p):
    r = (1-p['S'])*q + p['G']*(1-q)
    likelihood = r if y else 1-r
    posterior = q*((1-p['S']) if y else p['S']) / likelihood
    return posterior+(1-posterior)*p['T'], posterior, likelihood


def exact_filter(p, obs):
    q, likelihood = p['q1'], F(1)
    rows = []
    for t, y in enumerate(obs, 1):
        q, posterior, factor = step(q, y, p)
        likelihood *= factor
        rows.append(dict(t=t, posterior=posterior, q_next=q,
                         predict_next=(1-p['S'])*q+p['G']*(1-q),
                         likelihood=likelihood))
    return rows


def hidden_enumeration(p, obs):
    evidence, mastered = F(0), F(0)
    for states in product((0, 1), repeat=len(obs)):
        w = p['q1'] if states[0] else 1-p['q1']
        for t, (state, y) in enumerate(zip(states, obs)):
            if t:
                previous = states[t-1]
                w *= (F(state == 1) if previous else
                      (p['T'] if state else 1-p['T']))
            correct = 1-p['S'] if state else p['G']
            w *= correct if y else 1-correct
        evidence += w
        if states[-1]: mastered += w
    return evidence, mastered/evidence


def binomial_summary(successes, total):
    p = successes/total
    se = sqrt(p*(1-p)/total)
    z = 1.959963984540054
    center = (p+z*z/(2*total))/(1+z*z/total)
    half = z*sqrt(p*(1-p)/total+z*z/(4*total*total))/(1+z*z/total)
    return dict(estimate=p, mcse=se, wilson95_lo=center-half,
                wilson95_hi=center+half, successes=int(successes), total=total)


def future_exact(curves, depth=10):
    """Independent exhaustive probabilities, including crossings, for MC checks."""
    qs = [curves[k][-1]['q_next'] for k in PARAMS]
    nodes = [(qs[0], qs[1], F(1), F(1), False, False)]
    normalization, crossings = [], {}
    for n in range(1, depth+1):
        new = []
        for qb, qa, wb, wa, crossb, crossa in nodes:
            for y in (0,1):
                nb, _, lb = step(qb, y, PARAMS['baseline'])
                na, _, la = step(qa, y, PARAMS['alternative'])
                b, a = wb*lb, wa*la
                new.append((nb, na, b, a, crossb or b>=10*a,
                            crossa or a>=10*b))
        nodes = new
        assert sum(x[2] for x in nodes) == sum(x[3] for x in nodes) == 1
        # E_baseline[L_alt/L_base] = E_alt[L_base/L_alt] = 1 exactly.
        assert sum(x[2]*(x[3]/x[2]) for x in nodes) == 1
        assert sum(x[3]*(x[2]/x[3]) for x in nodes) == 1
        normalization.append(n)
    for truth, wi in [('baseline',2),('alternative',3)]:
        for direction, ci in [('baseline',4),('alternative',5)]:
            crossings[f'{truth}_{direction}'] = float(sum(x[wi] for x in nodes if x[ci]))
    return {'depth': depth, 'leaf_paths': len(nodes),
            'exact_normalizations_and_LR_expectations': len(normalization)*4,
            'crossing_BF10': crossings}


def future_simulation(curves, exact):
    rngs = np.random.SeedSequence(SEED).spawn(2)
    result, raw_times, mean_paths, quantiles = [], {}, {}, {}
    checkpoints = (10,20,50,100,200,400)
    for truth, child_seed in zip(PARAMS, rngs):
        rng = np.random.default_rng(child_seed)
        qs = {k:np.full(REPLICATES,float(curves[k][-1]['q_next'])) for k in PARAMS}
        params = {k:{n:float(v) for n,v in p.items()} for k,p in PARAMS.items()}
        llr = np.zeros(REPLICATES)  # log P_baseline(future|past)/P_alternative(...)
        times = {(d,a):np.full(REPLICATES,HORIZON+1,dtype=np.int16)
                 for d in PARAMS for a in (10,100)}
        means = [0.0]
        bands = [[0.0,0.0,0.0]]
        for n in range(1,HORIZON+1):
            forecasts = {k:(1-p['S'])*qs[k]+p['G']*(1-qs[k]) for k,p in params.items()}
            y = rng.random(REPLICATES)<forecasts[truth]
            llr += np.where(y, np.log(forecasts['baseline']/forecasts['alternative']),
                            np.log((1-forecasts['baseline'])/(1-forecasts['alternative'])))
            for k,p in params.items():
                likelihood = np.where(y,forecasts[k],1-forecasts[k])
                posterior = qs[k]*np.where(y,1-p['S'],p['S'])/likelihood
                qs[k] = posterior+(1-posterior)*p['T']
            for (direction,a),t in times.items():
                crosses = llr>=log(a) if direction=='baseline' else llr<=-log(a)
                t[(t==HORIZON+1)&crosses] = n
            means.append(float(llr.mean()))
            bands.append(np.quantile(llr,[.1,.5,.9]).tolist())
            if n in checkpoints:
                for (direction,a),t in times.items():
                    summary = binomial_summary(int(np.count_nonzero(t<=n)),REPLICATES)
                    limited = np.minimum(t,n)
                    row = dict(truth=truth,direction=direction,threshold=a,n=n,**summary,
                               mean_min=float(limited.mean()),
                               mean_min_mcse=float(limited.std(ddof=1)/sqrt(REPLICATES)))
                    result.append(row)
                    if n==10 and a==10:
                        expected = exact['crossing_BF10'][f'{truth}_{direction}']
                        assert abs(summary['estimate']-expected) <= 5*max(summary['mcse'],1/REPLICATES)
        mean_paths[truth] = means
        quantiles[truth] = bands
        for (direction,a),t in times.items():
            raw_times[f'{truth}_{direction}_BF{a}'] = t
    np.savez_compressed(ROOT/'analysis/bkt_future_first_passage.npz',**raw_times)
    return {'rows':result,'mean_logLR_baseline_over_alternative':mean_paths,
            'pointwise_logLR_10_50_90_percentiles':quantiles,
            'sample_quantiles_BF10_correct':{
                truth:{str(q):int(np.quantile(raw_times[f'{truth}_{truth}_BF10'],q,
                                           method='inverted_cdf')) for q in (.25,.5,.75,.9)}
                for truth in PARAMS}}


def calibration_integer(true_probability, nmax=100):
    """r=4/5 vs s=3/5. Factor=3/4 for correct, 2 for incorrect."""
    p = F(true_probability)
    base, correct, wrong = p.denominator,p.numerator,p.denominator-p.numerator
    states, den, absorbed = [1],1,0  # state k counts incorrect answers
    rows=[]
    for n in range(1,nmax+1):
        nxt=[0]*(n+1)
        for k,w in enumerate(states):
            nxt[k] += correct*w
            nxt[k+1] += wrong*w
        new = 0
        for k in range(n+1):
            # (3/4)^(n-k)*2^k >= 100, no floating point threshold decisions.
            if 3**(n-k)*2**k >= 100*4**(n-k):
                new += nxt[k];nxt[k]=0
        den *= base
        absorbed=base*absorbed+new
        states=nxt
        assert sum(states)+absorbed==den
        rows.append({'n':n,'detection':float(F(absorbed,den)),
                     'detection_exact':str(F(absorbed,den)),
                     'first_hit':float(F(new,den))})
    return rows


def calibration_bruteforce(p, nmax=10):
    total=F(0)
    for path in product((0,1),repeat=nmax):
        wealth,prob,crossed=F(1),F(1),False
        for y in path:
            wealth*=F(3,4) if y else F(2)
            prob*=p if y else 1-p
            crossed |= wealth>=100
        if crossed:total+=prob
    return total


def independent_uniform_boundaries(boundaries):
    """Verify every finite-horizon boundary using a positive beta expansion."""
    for n,b in enumerate(boundaries[1:],1):
        def bf(k):
            return sum((F(comb(k,j)*7**j*factorial(j)*factorial(n-k),
                          factorial(n-k+j+1)) for j in range(k+1)),F(0))
        assert b==n+1 or bf(b)>=891
        assert b==0 or bf(b-1)<891
    return 2*(len(boundaries)-1)


def generate():
    curves = {k:exact_filter(p,OBS) for k,p in PARAMS.items()}
    checks=0
    for k,p in PARAMS.items():
        for n in range(1,len(OBS)+1):
            evidence,posterior=hidden_enumeration(p,OBS[:n])
            assert evidence==curves[k][n-1]['likelihood']
            assert posterior==curves[k][n-1]['posterior']
            checks+=2
    ratio=curves['alternative'][-1]['likelihood']/curves['baseline'][-1]['likelihood']
    exact=future_exact(curves)
    future=future_simulation(curves,exact)
    calib={str(p):calibration_integer(p) for p in (F(4,5),F(3,5))}
    for p in (F(4,5),F(3,5)):
        assert F(calib[str(p)][9]['detection_exact'])==calibration_bruteforce(p)
    # Nonnegativity and mean-one identity of the generic betting factor.
    for r in (F(1,10),F(1,2),F(9,10)):
        for s in (F(1,20),F(1,2),F(19,20)):
            lam=(s-r)/(r*(1-r))
            assert -1/(1-r)<=lam<=1/r
            assert 1+lam*(1-r)==s/r and 1-lam*r==(1-s)/(1-r)
            assert r*(1+lam*(1-r))+(1-r)*(1-lam*r)==1
    data={
        'responses':OBS,'parameters':{k:{n:str(v) for n,v in p.items()} for k,p in PARAMS.items()},
        'exact_eight_answer_rows':{k:[{n:str(v) if isinstance(v,F) else v for n,v in row.items()}
                                     for row in rows] for k,rows in curves.items()},
        'log_likelihoods':{k:log(float(rows[-1]['likelihood'])) for k,rows in curves.items()},
        'alternative_over_baseline_likelihood_ratio':str(ratio),
        'likelihood_ratio_float':float(ratio),
        'log_likelihood_difference':log(float(ratio)),
        'future_design':{'seed':SEED,'numpy_version':np.__version__,
                         'bit_generator':'PCG64','replicates_per_truth':REPLICATES,
                         'horizon':HORIZON,'same_skill':True,'learning_continues':True,
                         'condition_on_observed_eight':True,'future_LR_initial_value':1,
                         'intervals':'pointwise Wilson 95%, Monte Carlo only'},
        'future':future,'calibration_constant_forecast':calib,
        'validation':{'exact_likelihood_and_posterior_path_checks':checks,
                      'future_enumeration':exact,'calibration_bruteforce_cases':2,
                      'generic_bet_identity_cases':9},
    }
    from sequential_performance import first_passage,known_boundaries,uniform_boundaries
    data['dice_detector_false_alarm_100']={str(eta):first_passage(F(1,8),known_boundaries(eta,100))[-1]['detection']
                                         for eta in (F(1,10),F(9,40),F(1,2),F(9,10))}
    uniform = uniform_boundaries(100)
    data['validation']['independent_uniform_beta_boundary_checks'] = independent_uniform_boundaries(uniform)
    data['dice_detector_false_alarm_100']['uniform']=first_passage(F(1,8),uniform)[-1]['detection']
    (ROOT/'analysis/bkt_sequential_validation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'analysis/bkt_future_first_passage.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(future['rows'][0]));writer.writeheader();writer.writerows(future['rows'])
    print('log likelihoods',data['log_likelihoods'],'ratio',float(ratio))
    print('correct BF10 quantiles',future['sample_quantiles_BF10_correct'])
    for row in future['rows']:
        if row['n'] in (20,50,100,400) and row['truth']==row['direction'] and row['threshold']==10:
            print(row)
    print('calibration N20/50/100', {p:[100*v[n-1]['detection'] for n in (20,50,100)] for p,v in calib.items()})
    print('dice false alarms',data['dice_detector_false_alarm_100'])


if __name__=='__main__':
    generate()
