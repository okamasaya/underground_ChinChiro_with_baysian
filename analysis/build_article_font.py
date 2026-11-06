"""Build searchable TrueType figure fonts from the installed OFL CJK fonts.

The original CFF outlines cannot be embedded as TrueType by Matplotlib's PDF
backend. Convert cubic to quadratic curves with an error tolerance of one
font unit, preserve BMP Unicode mappings, and rename the derivative family.
Requires fontTools. The generated fonts and their license ship with the bundle.
"""
from pathlib import Path
import hashlib
import json
import shutil

from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / 'fonts'
    target.mkdir(exist_ok=True)
    records = []
    for style, weight in [('Regular', 400), ('Bold', 700)]:
        source = Path('/usr/share/fonts/opentype/noto') / f'NotoSansCJK-{style}.ttc'
        original = TTFont(source, fontNumber=0)
        assert original['name'].getDebugName(1) == 'Noto Sans CJK JP'
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        options = subset.Options()
        options.layout_features = []
        options.recalc_timestamp = False
        sub = subset.Subsetter(options=options)
        sub.populate(unicodes=[cp for cp in original.getBestCmap() if cp <= 0xFFFF])
        sub.subset(original)
        order = original.getGlyphOrder()
        glyph_set = original.getGlyphSet()
        glyphs = {}
        for name in order:
            pen = TTGlyphPen(glyph_set)
            quadratic = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
            glyph_set[name].draw(quadratic)
            glyphs[name] = pen.glyph()
        builder = FontBuilder(original['head'].unitsPerEm, isTTF=True)
        builder.setupGlyphOrder(order)
        builder.setupCharacterMap(original.getBestCmap())
        builder.setupGlyf(glyphs)
        builder.setupHorizontalMetrics(dict(original['hmtx'].metrics))
        hhea = original['hhea']
        builder.setupHorizontalHeader(ascent=hhea.ascent, descent=hhea.descent,
                                      lineGap=hhea.lineGap)
        names = {
            'familyName': 'Article JP Sans', 'styleName': style,
            'uniqueFontIdentifier': f'ArticleJPSans-{style}-1.0',
            'fullName': f'Article JP Sans {style}',
            'psName': f'ArticleJPSans-{style}', 'version': 'Version 1.000',
            'copyright': original['name'].getDebugName(0) or '',
            'licenseDescription': 'SIL Open Font License, Version 1.1; see OFL.txt',
            'licenseInfoURL': 'https://openfontlicense.org/',
        }
        builder.setupNameTable(names)
        os2 = original['OS/2']
        builder.setupOS2(sTypoAscender=os2.sTypoAscender,
                         sTypoDescender=os2.sTypoDescender,
                         sTypoLineGap=os2.sTypoLineGap,
                         usWinAscent=os2.usWinAscent,
                         usWinDescent=os2.usWinDescent,
                         usWeightClass=weight,
                         fsSelection=0x20 if weight == 700 else 0x40)
        builder.setupPost()
        builder.setupMaxp()
        builder.font['head'].macStyle = 1 if weight == 700 else 0
        builder.font.recalcTimestamp = False
        builder.font['head'].created = original['head'].created
        builder.font['head'].modified = original['head'].modified
        dest = target / f'ArticleJPSans-{style}.ttf'
        builder.save(dest)
        records.append({'file': dest.name, 'source': str(source),
                        'source_sha256': source_hash,
                        'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
                        'glyphs': len(order), 'cubic_to_quadratic_max_error_font_units': 1})
        print(dest.name, dest.stat().st_size, flush=True)
    copyright_text = Path('/usr/share/doc/fonts-noto-cjk/copyright').read_text()
    # Keep Debian's complete upstream copyright/license record, unmodified.
    (target / 'OFL.txt').write_text(copyright_text)
    (target / 'provenance.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
