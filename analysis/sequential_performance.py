"""Finite-horizon first-passage probabilities, with exact integer recursions.

Observation Y=1 means that all three dice are High in the first throw.
For the complete-turn model this is a sufficient statistic for the type LR.
One unknown use rate is shared across turns in the uniform-mixture detector.
All thresholds are fixed before observing data. No Monte Carlo is used.
Run this file to regenerate A16/A17 numerical inputs and validation results.
"""
from fractions import Fraction as F
from math import ceil, comb, factorial, log, log10
from itertools import product
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
PRIOR, THRESHOLD = F(1, 10), F(99, 100)
BF_THRESHOLD = THRESHOLD * (1-PRIOR) / ((1-THRESHOLD)*PRIOR)
assert BF_THRESHOLD == 891


def known_boundaries(eta, nmax):
    """Minimum High count crossing the LR threshold; exact comparisons.

    A logarithm suggests a candidate only. Integer comparisons determine the
    final boundary, including equality, so no floating-point decision is used.
    """
    eta = F(eta)
    if not 0 <= eta <= 1:
        raise ValueError('eta must be in [0,1]')
    if eta == 0:
        return [n+1 for n in range(nmax+1)]
    if eta == 1:
        return [n if 8**n >= BF_THRESHOLD else n+1 for n in range(nmax+1)]
    d, a, b = eta.denominator, eta.denominator+7*eta.numerator, eta.denominator-eta.numerator
    ap, bp = [a**k for k in range(nmax+1)], [b**k for k in range(nmax+1)]
    result = [1]
    for n in range(1, nmax+1):
        target = BF_THRESHOLD.numerator * d**n
        k = max(0, min(n+1, ceil((log(float(BF_THRESHOLD))-n*log(b/d))/log(a/b))))
        def crosses(j):
            return j <= n and ap[j]*bp[n-j]*BF_THRESHOLD.denominator >= target
        while k > 0 and crosses(k-1):
            k -= 1
        while k <= n and not crosses(k):
            k += 1
        result.append(k)
    return result


def uniform_boundaries(nmax):
    """Exact Bayes factor integrated over a single eta~Uniform[0,1].

    M(n,k) = integral (1+7 eta)^k (1-eta)^(n-k) d eta
           = S(n,k)/[(n+1) C(n,k) 7^(n-k+1)],
    S(n,k) = sum_{j=0}^k C(n+1,j) 7^(n+1-j).
    The LR is increasing in k. This is integration, not maximization.
    """
    result = [1]
    p7 = [7**j for j in range(nmax+2)]
    for n in range(1, nmax+1):
        s = 0
        boundary = n+1
        for k in range(n+1):
            s += comb(n+1, k)*p7[n+1-k]
            denominator = (n+1)*comb(n, k)*p7[n-k+1]
            if s*BF_THRESHOLD.denominator >= BF_THRESHOLD.numerator*denominator:
                boundary = k
                break
        result.append(boundary)
    return result


def first_passage(q, boundaries):
    """Exact path weights of unabsorbed states and first crossings.

    Output floats are serialization only. Every recursion and normalization
    check uses integers, with probability denominator q.denominator**n.
    mean_min is E[min(tau,n)], not a mean conditional on detected paths.
    """
    q = F(q)
    high, base = q.numerator, q.denominator
    low = base-high
    states, den, hit, truncated = [1], 1, 0, 0
    result = []
    for n in range(1, len(boundaries)):
        truncated = base*(truncated+sum(states))
        nxt = [0]*(len(states)+1)
        for k, weight in enumerate(states):
            nxt[k] += low*weight
            nxt[k+1] += high*weight
        new = sum(nxt[boundaries[n]:])
        states = nxt[:boundaries[n]]
        den *= base
        hit = base*hit+new
        survival = sum(states)
        assert hit+survival == den
        result.append(dict(n=n, detection=float(F(hit, den)),
                           survival=float(F(survival, den)),
                           survival_log10=log10(survival)-log10(den) if survival else None,
                           first_hit=float(F(new, den)),
                           mean_min=float(F(truncated, den))))
    return result


def q_eta(eta):
    return (1+7*F(eta))/8


def exact_bruteforce(q, boundaries, n):
    total = F(0)
    for path in product((0, 1), repeat=n):
        k, crossed, weight = 0, False, F(1)
        for t, value in enumerate(path, 1):
            k += value
            weight *= q if value else 1-q
            crossed |= k >= boundaries[t]
        if crossed:
            total += weight
    return total


def payoff_coefficients():
    from chinchiro_model import turn_distribution, strength
    fair, cheat = turn_distribution(range(1,7)), turn_distribution((4,5,6))
    group = lambda r: 'P' if r=='pin' else 'T' if r.startswith('triple') else 'S' if r=='456' else 'D'
    coef = {g:F(0) for g in ('P','T','S','D')}
    for r,p in cheat.items():
        for s,q in fair.items():
            delta = strength(r)-strength(s)
            if delta:
                coef[group(r if delta>0 else s)] += p*q*(1 if delta>0 else -1)
    assert coef == {'P':-F(7,864),'T':F(271,3888),'S':F(109,648),'D':F(155,432)}
    # Independently compute the payoff for several multiplier assignments.
    cases = []
    for multipliers in ((1,1,1,1), (5,3,2,1), (5,5,2,1)):
        m = dict(zip(('P','T','S','D'), map(F, multipliers)))
        direct = sum(p*q*(m[group(r)] if strength(r)>strength(s) else
                         -m[group(s)] if strength(r)<strength(s) else 0)
                     for r,p in cheat.items() for s,q in fair.items())
        assert direct == sum(coef[g]*m[g] for g in coef)
        symmetric = sum(p*q*(m[group(r)] if strength(r)>strength(s) else
                            -m[group(s)] if strength(r)<strength(s) else 0)
                        for r,p in fair.items() for s,q in fair.items())
        assert symmetric == 0
        cases.append({'multipliers':multipliers,'K_exact':str(direct),'K':float(direct)})
    return coef, cases


def posterior_logodds_quantiles(nmax=20, q=F(73,80)):
    result = []
    for n in range(nmax+1):
        weights = [comb(n,k)*q.numerator**k*(q.denominator-q.numerator)**(n-k) for k in range(n+1)]
        den, cumulative, found = q.denominator**n, 0, {}
        for k, weight in enumerate(weights):
            cumulative += weight
            for label, u in (('lo',F(1,10)),('median',F(1,2)),('hi',F(9,10))):
                if label not in found and cumulative*u.denominator >= u.numerator*den:
                    found[label] = log10(float(PRIOR/(1-PRIOR)))+k*log10(7.3)-(n-k)
        result.append({'n':n,**found})
    return result


def generate():
    nmax = 1000
    boundaries = known_boundaries(F(9,10), nmax)
    mixture = uniform_boundaries(nmax)
    h0 = first_passage(F(1,8), boundaries)
    h1 = first_passage(F(73,80), boundaries)
    checks = 0
    # Independent polynomial integration and H0 normalization of the mixture.
    for n in range(9):
        expected_lr = F(0)
        for k in range(n+1):
            integral = sum(F(comb(k,j)*7**j*factorial(j)*factorial(n-k),
                             factorial(n-k+j+1)) for j in range(k+1))
            closed = F(sum(comb(n+1,j)*7**(n+1-j) for j in range(k+1)),
                       (n+1)*comb(n,k)*7**(n-k+1))
            assert integral == closed
            expected_lr += F(comb(n,k)*7**(n-k),8**n)*closed
        assert expected_lr == 1
    for eta in (F(1,10),F(1,2),F(9,10),F(1)):
        for b in (known_boundaries(eta,10), mixture[:11]):
            for q in (F(1,8),q_eta(eta)):
                value = first_passage(q,b)[-1]['detection']
                assert abs(float(exact_bruteforce(q,b,10))-value) < 1e-15
                checks += 1
    coefficients, payoffs = payoff_coefficients()
    rows = []
    rates = sorted(set([F(i,20) for i in range(21)]+[F(9,40)]))
    for eta in rates:
        matched = first_passage(q_eta(eta), known_boundaries(eta,nmax))
        fixed = first_passage(q_eta(eta), boundaries)
        mixed = first_passage(q_eta(eta), mixture)
        rows.append({'eta_exact':str(eta), 'eta':float(eta),
                     'unit_EV':float(eta*F(4577,7776)),
                     **{f'{model}_mean_min100':series[99]['mean_min']
                        for model,series in (('matched',matched),('fixed090',fixed),('uniform',mixed))},
                     'KL_nats':float(q_eta(eta))*log(float(q_eta(eta)*8))+
                        (float(1-q_eta(eta))*log(float((1-q_eta(eta))*8/7)) if eta<1 else 0),
                     **{f'{model}_{n}':series[n-1]['detection']
                        for model,series in (('matched',matched),('fixed090',fixed),('uniform',mixed))
                        for n in (20,100,1000)},
                     **{f'{model}_{n}_survival_log10':series[n-1]['survival_log10']
                        for model,series in (('matched',matched),('fixed090',fixed),('uniform',mixed))
                        for n in (20,100,1000)}})
    result = {'prior':str(PRIOR),'posterior_threshold':str(THRESHOLD),
              'BF_threshold':str(BF_THRESHOLD),'false_alarm_bound':float(1/BF_THRESHOLD),
              'reference_eta':'9/10','h0':h0,'h1':h1,
              'pointwise_quantiles':posterior_logodds_quantiles(), 'frequency':rows,
              'payoff_coefficients':{k:str(v) for k,v in coefficients.items()},'payoff_cases':payoffs,
              'validation':{'bruteforce_10_turn_cases':checks,
                            'uniform_polynomial_integral_cases':45,
                            'uniform_null_expectation_cases':9,
                            'integer_normalization':'all steps/all scenarios'}}
    (ROOT/'analysis/sequential_performance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'analysis/frequency_sensitivity.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    for n in (4,10,20,100,1000):
        print(n, 'H0',h0[n-1], 'H1',h1[n-1])
    for row in rows:
        if row['eta_exact'] in ('1/10','9/40','1/2','9/10','1'):
            print(row)
    print('payoff',payoffs,'validation',result['validation'])


if __name__ == '__main__':
    generate()
