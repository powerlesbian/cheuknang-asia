#!/usr/bin/env python3
"""Reusable builder for the Traditional-Chinese (HK) /zh/ mirror of cheuknang.asia.

- build(slug, content_map, title_zh): copies the EN page, translates nav labels
  + page content, sets lang/title, writes /zh/<slug>/index.html.
- relink_all(): rewrites internal hrefs on every /zh/ page to their /zh/
  counterpart *iff that page exists* (else leaves the EN link — no 404s), and
  wires the EN<->中文 switcher on both sides for pages that have a zh version.

Official Chinese names (from cheuknang.com.hk/zh + repo):
  卓能集團 / 卓能(控股)有限公司, 新趙苑, 趙苑第二/三期, 壹號九龍山頂,
  卓能山莊, 卓能·雅苑, 趙世曾 (Cecil Chao)
"""
import re, pathlib, html

ROOT = pathlib.Path('.')

# nav menu labels (href-preserving; relink_all upgrades the hrefs later)
NAV = {
    '>Home</a>':            '>首頁</a>',
    '>About Us</a>':        '>關於我們</a>',
    '>Portfolio</a>':       '>發展項目</a>',
    '>Portfolio</span>':    '>發展項目</span>',
    '>New Villa Cecil</a>': '>新趙苑</a>',
    '>News &amp; Opinions</a>': '>新聞及觀點</a>',
    '>Reports</a>':         '>業績報告</a>',
    '>Contact Us</a>':      '>聯絡我們</a>',
}

def slug_dir(slug):
    return ROOT/'zh'/slug if slug else ROOT/'zh'

def build(slug, content_map, title_zh):
    src = (ROOT/(slug+'/index.html' if slug else 'index.html')).read_text('utf-8', 'ignore')
    t = src
    # nav labels
    for en, zh in NAV.items():
        t = t.replace(en, zh)
    # page content (longest-first so substrings don't clobber)
    for en in sorted(content_map, key=len, reverse=True):
        zh = content_map[en]
        if '<' in en:            # raw HTML block: exact replace
            t = t.replace(en, zh)
        else:                    # text node: whitespace-insensitive match
            pat = r'\s+'.join(re.escape(w) for w in en.split())
            t = re.sub(pat, lambda m: zh, t)
    # lang + title + canonical/og
    t = re.sub(r'(<html[^>]*\blang=")[^"]*(")', r'\1zh-Hant-HK\2', t)
    t = re.sub(r'<title>.*?</title>', f'<title>{title_zh}</title>', t, count=1, flags=re.S)
    canon = '/zh/' + (slug + '/' if slug else '')
    t = re.sub(r'(<link rel="canonical" href=")[^"]*(")', rf'\1{canon}\2', t)
    t = re.sub(r'(<meta property="og:url" content=")[^"]*(")', rf'\1{canon}\2', t)
    out = slug_dir(slug); out.mkdir(parents=True, exist_ok=True)
    (out/'index.html').write_text(t, 'utf-8')
    return canon

def _switcher_li(href, label):
    return (f'<li class="menu-item menu-item-type-custom menu-item-object-custom menu-item-langswitch">'
            f'<div class="wrap"><a href="{href}">{label}</a></div></li>')

def relink_all():
    """After all zh pages are built: point internal links to /zh/ where the
    target exists, and add the language switcher on both EN and zh sides."""
    zh_slugs = {p.parent.relative_to(ROOT/'zh').as_posix().rstrip('.')
                for p in (ROOT/'zh').rglob('index.html')}
    zh_slugs = {('' if s=='.' else s) for s in zh_slugs}
    def exists_zh(slug): return slug in zh_slugs
    # --- rewrite links on every zh page ---
    for p in (ROOT/'zh').rglob('index.html'):
        t = p.read_text('utf-8', 'ignore')
        def up(m):
            href = m.group(1)
            inner = href.strip('/')
            return f'href="/zh/{inner}/"' if (href.startswith('/') and not href.startswith('/zh/')
                    and not href.startswith('/wp-') and exists_zh(inner)) else m.group(0)
        t = re.sub(r'href="(/[^"]*/)"', up, t)
        # switcher -> English counterpart
        slug = p.parent.relative_to(ROOT/'zh').as_posix()
        slug = '' if slug=='.' else slug
        en_href = '/' + (slug + '/' if slug else '')
        if 'menu-item-langswitch' not in t:
            t = _inject_switcher(t, en_href, 'English')
        p.write_text(t, 'utf-8')
    # --- add 中文 switcher to EN pages that have a zh counterpart ---
    for slug in zh_slugs:
        en = ROOT/(slug+'/index.html' if slug else 'index.html')
        if not en.exists(): continue
        t = en.read_text('utf-8', 'ignore')
        if 'menu-item-langswitch' in t:
            t = re.sub(r'<li class="[^"]*menu-item-langswitch[^"]*">.*?</li>', '', t)
        t = _inject_switcher(t, '/zh/' + (slug+'/' if slug else ''), '中文')
        en.write_text(t, 'utf-8')

def _inject_switcher(t, href, label):
    li = _switcher_li(href, label)
    # insert before the Contact Us / 聯絡我們 menu item, in both desktop+mobile menus
    for anchor in ('>聯絡我們</a>', '>Contact Us</a>'):
        idx = t.find(anchor)
        if idx != -1:
            li_start = t.rfind('<li', 0, idx)
            t = t[:li_start] + li + t[li_start:]
    return t

if __name__ == '__main__':
    from zh_content import (HOME, ABOUTUS, CONTACT, PORTFOLIO, REPORTS,
                            NEWVILLACECIL, NEWS)
    pages = [
        ('',                HOME,          '卓能集團 — 於亞洲築建安居樂業之所'),
        ('about-us',        ABOUTUS,       '關於我們 — 卓能集團'),
        ('contact-us',      CONTACT,       '聯絡我們 — 卓能集團'),
        ('portfolio',       PORTFOLIO,     '發展項目 — 卓能集團'),
        ('reports',         REPORTS,       '業績及公告 — 卓能集團'),
        ('new-villa-cecil', NEWVILLACECIL, '新趙苑 — 卓能集團'),
        ('news',            NEWS,          '新聞及觀點 — 卓能集團'),
    ]
    for slug, cmap, title in pages:
        print('built', build(slug, cmap, title))
    relink_all()
    print('relinked; zh pages:', sorted(('' if (q.parent==ROOT/'zh') else q.parent.relative_to(ROOT/'zh').as_posix()) for q in (ROOT/'zh').rglob('index.html')))
