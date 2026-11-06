"""Article-wide display precision; underlying numerical values are unchanged.

Decimals use three digits after the point and ROUND_HALF_UP. Counts and exact
fractions remain integers/fractions. Install before constructing Matplotlib
figures. Continuous probability/odds axes are formatted at save time.
"""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction
import re

PLACES = 3
_INSTALLED = False
_DECIMAL = re.compile(r'(?<![\d.])[-+]?\d+\.\d+(?!\d)')
_PERCENT = re.compile(r'(?<![\d.])([-+]?\d+(?:\.\d+)?)(\\?%|％)')


def as_decimal(value):
    if isinstance(value, Fraction):
        with localcontext() as ctx:
            ctx.prec = 60
            return Decimal(value.numerator)/Decimal(value.denominator)
    return value if isinstance(value, Decimal) else Decimal(str(value))


def fixed(value, percent=False):
    x = as_decimal(value)
    if percent: x *= 100
    with localcontext() as ctx:
        ctx.prec = 60
        result = format(x.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP), '.3f')
    return result + ('%' if percent else '')


def scientific(value):
    x = as_decimal(value)
    if not x: return '0.000e+00'
    exponent = x.copy_abs().adjusted()
    mantissa = x.scaleb(-exponent).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    if abs(mantissa) == 10:
        mantissa /= 10; exponent += 1
    return f'{mantissa:.3f}e{exponent:+03d}'


def format_text(text):
    text = str(text)
    def approximate_equality(match):
        value=match.group(2)
        if as_decimal(value)!=as_decimal(fixed(value)):
            return (r'\approx' if '$' in text else '≈')+match.group(1)+fixed(value)
        return match.group(0)
    text=re.sub(r'(?<![<>!])=(\s*)([-+]?\d+\.\d+)',approximate_equality,text)
    def decimal_match(match):
        original = match.group(0)
        # An explicit '+' can be an addition operator in a displayed formula.
        # Decimal formatting alone drops it, changing the mathematical meaning.
        return ('+' if original.startswith('+') else '') + fixed(original)
    text = _DECIMAL.sub(decimal_match, text)
    text = _PERCENT.sub(lambda m: fixed(m.group(1)) + m.group(2), text)
    from figure_japanese import localize
    return localize(text)


def install():
    global _INSTALLED
    if _INSTALLED: return
    _INSTALLED = True
    from figure_fonts import configure
    configure()
    from matplotlib.text import Text
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter, FixedFormatter
    original_text, original_save = Text.set_text, Figure.savefig
    def set_text(self, text):
        return original_text(self, format_text(text) if text is not None else text)
    def savefig(self, *args, **kwargs):
        for ax in self.axes:
            for axis, label in [(ax.xaxis,ax.get_xlabel()), (ax.yaxis,ax.get_ylabel())]:
                label = label.lower()
                if any(key in label for key in ('probability','posterior','odds','covariance','確率','事後','オッズ','共分散')):
                    # Explicit category labels (Win/Draw/Loss, role names) stay categorical.
                    if isinstance(axis.get_major_formatter(),FixedFormatter):
                        ticks = axis.get_ticklabels()
                        if ticks and any(re.search('[A-Za-z]',x.get_text()) for x in ticks):continue
                    axis.set_major_formatter(FuncFormatter(lambda value, pos: fixed(value)))
        return original_save(self,*args,**kwargs)
    Text.set_text = set_text
    Figure.savefig = savefig
