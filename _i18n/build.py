#!/usr/bin/env python3
"""Build /en/ and /de/ page sets from the Danish root pages of the nybo-preview repo.
Only whole text nodes and a few attributes are translated (exact-match dictionary); markup is otherwise byte-identical.
Also: <html lang>, asset paths (../), language-selector links (also patched into the DA root pages), JS chat strings."""
import re, html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translations import EN, DE, JS

REPO = sys.argv[1]
PAGES = ["index.html","produkter.html","baeredygtighed.html","brancher.html","kataloger.html","find-forhandler.html","kontakt.html","om-os.html"]
LANGS = {"en": EN, "de": DE}
ASSET = r"[\w\-]+\.(?:jpg|jpeg|png|webp|svg)"
TOKEN = re.compile(r"<!--.*?-->|<(script|style|svg)\b[^>]*>.*?</\1\s*>|<[^>]+>|[^<]+", re.S | re.I)

def norm(t): return re.sub(r"\s+", " ", t).strip()

def translate(src, D, lang, jsmap):
    out = []
    for m in TOKEN.finditer(src):
        tok = m.group(0); low = tok[:7].lower()
        if tok.startswith("<!--"):
            out.append(tok); continue
        if low.startswith("<script") or low.startswith("<style") or low.startswith("<svg"):
            t = re.sub(r"url\((['\"]?)(?!https?:|data:|\.\./|/)(" + ASSET + r")\1\)", r"url(\1../\2\1)", tok)
            for a, b in jsmap.items(): t = t.replace(a, b)
            out.append(t); continue
        if tok.startswith("<"):
            t = tok
            if low.startswith("<html"): t = re.sub(r'lang="[a-zA-Z-]+"', f'lang="{lang}"', t)
            t = re.sub(r'(src=")(?!https?:|data:|\.\./|/)(' + ASSET + r')(")', r"\1../\2\3", t)
            def rep(mm):
                k = norm(html.unescape(mm.group(2)))
                return mm.group(1) + html.escape(D[k], quote=True) + mm.group(3) if k in D else mm.group(0)
            t = re.sub(r'((?:alt|placeholder|title|aria-label)=")([^"]*)(")', rep, t)
            out.append(t); continue
        k = norm(html.unescape(tok))
        if k and k in D:
            lead = tok[:len(tok) - len(tok.lstrip())]; trail = tok[len(tok.rstrip()):]
            out.append(lead + html.escape(D[k], quote=False) + trail)
        else:
            out.append(tok)
    return "".join(out)

LANG_LINKS = {  # label text in the selector -> language folder
 "Dansk — Danmark": "da", "English — United Kingdom": "en", "English — Ireland": "en",
 "Deutsch — Deutschland": "de", "Deutsch — Österreich": "de", "Deutsch — Schweiz": "de",
}
def patch_lang_links(src, page, here):
    """here = 'da' | 'en' | 'de'. Root pages link to en/<page>; subdir pages link with ../"""
    pre = {"da": "", "en": "en/", "de": "de/"} if here == "da" else {"da": "../", "en": "../en/", "de": "../de/"}
    def rep(m):
        label = m.group(1); lang = LANG_LINKS[label]
        active = ' style="font-weight:600;color:var(--red)"' if lang == here else ""
        return f'<a href="{pre[lang]}{page}"{active}>{label}</a>'
    pat = "|".join(re.escape(k) for k in LANG_LINKS)
    return re.sub(r'<a(?: href="[^"]*")?(?: style="[^"]*")?>(' + pat + r")</a>", rep, src)

for page in PAGES:
    da = open(os.path.join(REPO, page), encoding="utf-8").read()
    # patch the Danish root page's language links in place
    open(os.path.join(REPO, page), "w", encoding="utf-8").write(patch_lang_links(da, page, "da"))
    for lang, D in LANGS.items():
        os.makedirs(os.path.join(REPO, lang), exist_ok=True)
        out = translate(da, D, lang, JS[lang])
        out = patch_lang_links(out, page, lang)
        if lang == "de":  # German runs longer: keep the hero headline to three lines
            out = out.replace("</head>", '<style>html[lang="de"] .hero-copy h1{font-size:clamp(2.3rem,4.5vw,3.8rem)}</style>\n</head>', 1)
        open(os.path.join(REPO, lang, page), "w", encoding="utf-8").write(out)
    print("built", page)
print("done")
