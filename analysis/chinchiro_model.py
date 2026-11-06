"""Exact role probabilities and a reproducible illustrative context sequence.

All stakes and contexts are fixed before outcomes. One dice set is retained
within a turn. Both players finish their turns; equal strength is a draw.
No payoff multiplier is assumed, so this module does not calculate profit.
"""
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import product
import random

SEED = 20261103
# This illustrative opponent seed includes a high-stakes loss. It was selected
# to illustrate that mechanism; this one sequence does not estimate frequencies.
OPPONENT_SEED = 20261108
PRIOR = F(1, 10)
N_TURNS = 20
HIGH_TURNS = (4, 8, 12, 16, 20)
ETA_HIGH, ETA_LOW = F(9, 10), F(0)
ETA_CONSTANT = (len(HIGH_TURNS)*ETA_HIGH + (N_TURNS-len(HIGH_TURNS))*ETA_LOW)/N_TURNS
CHEAT_ROLES = ('triple4', 'triple5', 'triple6', '456', 'point6', 'point5', 'point4')


def role(x):
    x = tuple(sorted(x))
    if len(x) != 3 or any(v not in range(1, 7) for v in x):
        raise ValueError('Expected three integer faces on 1..6')
    c = Counter(x)
    if len(c) == 1:
        return 'pin' if x[0] == 1 else f'triple{x[0]}'
    if x == (4, 5, 6):
        return '456'
    if x == (1, 2, 3):
        return '123'
    if len(c) == 2:
        return 'point' + str(next(v for v, n in c.items() if n == 1))
    return 'none'


def strength(r, profile='A'):
    if profile not in ('A', 'B'):
        raise ValueError(profile)
    if r == 'pin': return 20
    if r.startswith('triple'): return 10 if profile == 'A' else 10+int(r[-1])
    if r == '456': return 9
    if r.startswith('point'): return 2+int(r[-1])
    return {'none': 1, '123': 0}[r]


def roll_distribution(faces):
    faces = tuple(faces)
    counts = Counter(role(x) for x in product(faces, repeat=3))
    return {r: F(n, len(faces)**3) for r, n in counts.items()}


def turn_distribution(faces):
    p = roll_distribution(faces)
    q = p.get('none', F(0))
    return {r: q**3 if r == 'none' else a*(1+q+q*q) for r,a in p.items()}


def turn_distribution_by_recursion(faces):
    """Independent absorbing-state calculation, used as a verification."""
    one = roll_distribution(faces)
    result, surviving = defaultdict(F), F(1)
    for throw in range(1, 4):
        for r,a in one.items():
            if r != 'none' or throw == 3:
                result[r] += surviving*a
        surviving *= one.get('none', F(0))
    return dict(result)


def conditional_wdl(own_role, profile='A'):
    ans = {'win': F(0), 'draw': F(0), 'loss': F(0)}
    for other, prob in turn_distribution(range(1, 7)).items():
        d = strength(own_role, profile)-strength(other, profile)
        ans['win' if d>0 else 'loss' if d<0 else 'draw'] += prob
    assert sum(ans.values()) == 1
    return ans


def overall_wdl(profile='A'):
    result = {'win': F(0), 'draw': F(0), 'loss': F(0)}
    for r,p in turn_distribution((4,5,6)).items():
        for key,q in conditional_wdl(r,profile).items(): result[key] += p*q
    return result


def play_turn(rng, faces):
    history = []
    for _ in range(3):
        x = tuple(rng.choice(faces) for _ in range(3))
        history.append(x)
        if role(x) != 'none': break
    return history


def turn_likelihoods(history):
    if not 1 <= len(history) <= 3: raise ValueError('Invalid number of throws')
    if any(role(x) != 'none' for x in history[:-1]): raise ValueError('Stopped too late')
    if len(history)<3 and role(history[-1])=='none': raise ValueError('Stopped too early')
    lf = F(1,216)**len(history)
    lc = F(1,27)**len(history) if all(min(x)>=4 for x in history) else F(0)
    return lf,lc


def bayes_factor(history, eta):
    lf,lc = turn_likelihoods(history)
    return (eta*lc+(1-eta)*lf)/lf


def context_records():
    rng, opponent_rng = random.Random(SEED), random.Random(OPPONENT_SEED)
    o_context = o_constant = PRIOR/(1-PRIOR)
    records = []
    for t in range(1,N_TURNS+1):
        high = t in HIGH_TURNS
        eta = ETA_HIGH if high else ETA_LOW
        latent = '456' if rng.random()<float(eta) else 'fair'
        history = play_turn(rng, (4,5,6) if latent=='456' else (1,2,3,4,5,6))
        opponent = play_turn(opponent_rng,(1,2,3,4,5,6))
        own_role,other_role = role(history[-1]),role(opponent[-1])
        d = strength(own_role)-strength(other_role)
        bc,bg = bayes_factor(history,eta),bayes_factor(history,ETA_CONSTANT)
        o_context *= bc; o_constant *= bg
        records.append(dict(turn=t, high_stakes=high, stake=10 if high else 1,
            eta=str(eta), latent_for_reproducibility_only=latent,
            suspect_history=history, opponent_history=opponent,
            suspect_role=own_role, opponent_role=other_role,
            result='win' if d>0 else 'loss' if d<0 else 'draw',
            bf_context=str(bc), bf_constant=str(bg),
            posterior_context=float(o_context/(1+o_context)),
            posterior_constant=float(o_constant/(1+o_constant))))
    return records


def verify():
    for faces in (range(1,7),(4,5,6)):
        assert turn_distribution(faces)==turn_distribution_by_recursion(faces)
        assert sum(roll_distribution(faces).values())==1
        assert sum(turn_distribution(faces).values())==1
    f,c = turn_distribution(range(1,7)),turn_distribution((4,5,6))
    assert f['none']==F(1,8) and f['pin']==F(7,864)
    assert f['456']==F(7,144) and c.get('none',F(0))==0
    assert set(c)==set(CHEAT_ROLES)
    assert conditional_wdl('point6')['loss']==F(7,72)
    assert conditional_wdl('point5')['loss']==F(7,32)
    assert conditional_wdl('point4')['loss']==F(49,144)
    assert conditional_wdl('triple4','A')['loss']==F(7,864)
    assert conditional_wdl('triple4','B')['loss']==F(7,288)
    for profile in ('A','B'):
        win=loss=F(0)
        for r,p in f.items():
            q=conditional_wdl(r,profile)
            win+=p*q['win'];loss+=p*q['loss']
        assert win==loss
        assert sum(overall_wdl(profile).values())==1
    for rec in context_records():
        if not rec['high_stakes']: assert F(rec['bf_context'])==1
        h=rec['suspect_history']
        assert bayes_factor(h,F(0))==1
        if all(min(x)>=4 for x in h):
            assert len(h)==1 and bayes_factor(h,ETA_HIGH)==F(73,10)
        else: assert bayes_factor(h,ETA_HIGH)==F(1,10)
    return True


if __name__ == '__main__':
    import json
    verify()
    print(json.dumps({'verified':True,'seed':SEED,
        'eta_constant':str(ETA_CONSTANT),
        'overall':{p:{k:str(v) for k,v in overall_wdl(p).items()} for p in ('A','B')},
        'context_final':context_records()[-1]},indent=2))
