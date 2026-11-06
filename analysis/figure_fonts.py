"""Use the bundled TrueType family; preserve searchable Unicode PDF text."""
from pathlib import Path


def configure():
    import matplotlib
    from matplotlib import font_manager
    root = Path(__file__).resolve().parents[1] / 'fonts'
    for style in ('Regular', 'Bold'):
        filename = root / f'ArticleJPSans-{style}.ttf'
        if not filename.exists():
            raise FileNotFoundError(f'Bundled figure font missing: {filename}')
        font_manager.fontManager.addfont(str(filename))
    matplotlib.rcParams.update({'font.family': 'Article JP Sans',
                                'pdf.fonttype': 42, 'ps.fonttype': 42})
