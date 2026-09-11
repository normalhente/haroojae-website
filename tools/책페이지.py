#!/usr/bin/env python3
"""책 한 권에 한 페이지 — `books/<슬러그>/index.html` 을 카드 데이터에서 찍어낸다.

    python3 tools/책페이지.py            # books/ 41장 + sitemap.xml 다시 생성, 카드에 실링크 삽입
    python3 tools/책페이지.py --확인      # 파일은 안 쓰고 슬러그·누락값만 출력

왜 있나 (2026-09-12)
  사이트가 한 파일(index.html)이고 책 상세가 `#book/…` 해시라 검색엔진엔 문서가 **1개**뿐이었다.
  누가 책 제목으로 검색하면 서점은 뜨고 우리는 안 떴다. 그래서 책마다 진짜 URL 을 만든다.
  덤으로 카톡·인스타에 책 링크를 보내면 표지가 미리보기로 뜬다(전엔 어떤 책이든 히어로 산 그림).

원천은 두 곳뿐 — 여기 말고 다른 데 서지를 적지 말 것
  * index.html 의 `.book-card` data-* (제목·저자·소개·인용·태그·저자소개·서점 링크·표지)  ← 화면과 같은 원천
  * tools/책_서지.json (ISBN·원제·역자·발간일·정가 — 카드엔 없는 것)
  신간: 카드 추가 → 책_서지.json 한 항목 → 이 스크립트 한 번.

메인 사이트와의 관계
  * 카드 안 표지 <img> 를 `<a class="book-link" href="books/…/">` 로 감싼다(멱등). 크롤러는 이 링크를 따라가고,
    사람이 클릭하면 JS 가 preventDefault 하고 지금처럼 오버레이(#book/…)를 연다. ⌘클릭·가운데클릭은 새 탭으로 페이지가 열린다
  * 페이지 슬러그는 해시 슬러그(공백→'-')에서 URL 에 못 쓰는 문자(? ' ( ) — 등)를 뺀 것이다.
    `정당화할 수 없는 위험?` 의 `?` 가 경로에서 쿼리 구분자가 되기 때문. 두 슬러그는 같지 않다
  * 페이지 CSS 는 index.html 의 토큰(:root 변수·상세뷰 규칙)을 옮겨 적은 것이다. 본체가 바뀌면 여기도 맞출 것

검증(--확인 없이 돌리면 끝에 자동): 41장 전부 <title>·og:image·canonical 이 있고, 표지 파일이 실제로 있는지.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
서지 = ROOT / "tools" / "책_서지.json"
OUT = ROOT / "books"
SITE = "https://haroojae.co.kr"

AWARDS = [("BANFF", "BANFF 수상"), ("세종도서", "세종도서"), ("황금피켈", "황금피켈상"), ("아카데미상", "아카데미상"), ("NOBA", "NOBA 수상")]


def hash_slug(title: str) -> str:
    """index.html 의 bookSlug() 와 같은 규칙 — 오버레이 링크(#book/…)용."""
    return re.sub(r"\s+", "-", unicodedata.normalize("NFC", title).strip())


def page_slug(title: str) -> str:
    """폴더 이름용. 한글·영문·숫자·한자만 남기고 나머지는 '-' 로."""
    s = unicodedata.normalize("NFC", title)
    s = re.sub(r"[^0-9A-Za-z가-힣一-鿿]+", "-", s).strip("-")
    return s


def cards() -> list[dict]:
    src = INDEX.read_text(encoding="utf-8")
    out = []
    for open_tag, body in re.findall(r'(<div class="book-card[^"]*"[^>]*>)(.*?)\n        </div>', src, re.S):
        d = {k: html.unescape(v) for k, v in re.findall(r'data-([a-z0-9-]+)="([^"]*)"', open_tag)}
        m = re.search(r'<div class="book-hover-sub">(.*?)</div>', body)
        d["sub"] = html.unescape(m.group(1)) if m else ""
        out.append(d)
    return out


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


CSS = """
    *{margin:0;padding:0;box-sizing:border-box}
    :root{
      --font-serif:'sandoll-myeongjoneo1','Noto Serif KR','Nanum Myeongjo',Georgia,serif;
      --font-sans:'Pretendard Variable',Pretendard,'Apple SD Gothic Neo',sans-serif;
      --fs-title:26px;--fs-body:15px;--fs-meta:13px;--lh-tight:1.4;--lh-body:1.85;--serif-strong:500;
      --bg:#F5F5F4;--text:#1A1A1A;--muted:#6F6F6F;--accent:#2C4A1E;--border:#E2E2E1;--dark:#1A2820;
      --m-ink:#1A1A1A;--m-body:#585858;--m-info:#6F6F6F;
    }
    html{-webkit-text-size-adjust:100%}
    body{background:var(--bg);color:var(--text);font-family:var(--font-sans);font-size:var(--fs-body);line-height:var(--lh-body);text-wrap:pretty}
    a{color:inherit}
    .nav{display:flex;align-items:center;justify-content:space-between;padding:22px 40px;border-bottom:1px solid var(--border)}
    .nav-logo img{height:26px;width:auto;display:block}
    .nav-links{display:flex;gap:28px;font-size:var(--fs-meta);letter-spacing:.03em}
    .nav-links a{text-decoration:none;color:var(--muted)}
    .nav-links a:hover{color:var(--text)}
    main{max-width:1080px;margin:0 auto;padding:64px 40px 96px}
    .crumb{font-size:var(--fs-meta);color:var(--m-info);margin-bottom:36px}
    .crumb a{text-decoration:none}
    .crumb a:hover{color:var(--text)}
    .grid{display:grid;grid-template-columns:38% 1fr;gap:64px;align-items:start}
    .cover{position:sticky;top:40px}
    .cover img{display:block;max-width:100%;height:auto;border:1px solid rgba(26,26,26,.10);box-shadow:0 18px 38px rgba(0,0,0,.16)}
    .lang,.label{font-size:var(--fs-meta);font-weight:600;letter-spacing:.09em;color:var(--m-info);text-transform:uppercase;margin-bottom:10px}
    h1{font-family:var(--font-serif);font-size:var(--fs-title);font-weight:var(--serif-strong);line-height:var(--lh-tight);margin:6px 0 6px;text-wrap:balance}
    .sub{font-family:var(--font-serif);font-size:17px;color:var(--m-body);margin-bottom:12px;line-height:var(--lh-tight)}
    .author{font-size:var(--fs-meta);color:var(--m-info);line-height:var(--lh-tight);margin-bottom:10px}
    .awards{display:flex;flex-wrap:wrap;gap:6px 16px;margin-bottom:12px;font-size:13px;font-weight:600;color:var(--m-ink)}
    .series{font-size:var(--fs-meta);color:var(--m-info);margin-bottom:24px}
    hr{border:0;border-top:1px solid var(--border);margin:0 0 28px}
    .desc{color:var(--m-ink);margin-bottom:28px}
    .quote{position:relative;padding-left:30px;margin-bottom:28px;font-family:var(--font-serif);color:var(--m-body);line-height:1.7}
    .quote::before{content:'\\201C';position:absolute;left:6px;top:-6px;font-size:56px;color:var(--muted);opacity:.25;line-height:1;font-family:var(--font-serif)}
    .bio{color:var(--m-body);margin-bottom:28px}
    dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 24px;font-size:var(--fs-meta);color:var(--m-info);margin-bottom:28px}
    dt{font-weight:600;letter-spacing:.03em}
    dd{color:var(--m-body)}
    .tags{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:var(--fs-meta);color:var(--m-info);margin-bottom:36px}
    .buy{display:flex;gap:8px;margin-bottom:56px}
    .buy a{flex:1;padding:13px 16px;font-size:var(--fs-meta);letter-spacing:.05em;text-align:center;text-decoration:none;border:1px solid var(--border);color:var(--text);transition:background .2s,color .2s,border-color .2s}
    .buy a:hover{background:var(--accent);color:#fff;border-color:var(--accent)}
    .club{border-top:1px solid var(--border);padding-top:28px}
    .club p{color:var(--m-body);margin:8px 0 16px}
    .club a{font-size:var(--fs-meta);letter-spacing:.03em;color:var(--accent);text-decoration:none;border-bottom:1px solid currentColor}
    .prevnext{display:flex;justify-content:space-between;gap:24px;margin-top:72px;padding-top:24px;border-top:1px solid var(--border);font-size:var(--fs-meta)}
    .prevnext a{text-decoration:none;color:var(--m-info);max-width:45%}
    .prevnext a:hover{color:var(--text)}
    .prevnext .t{display:block;font-family:var(--font-serif);font-size:15px;color:var(--text);margin-top:4px}
    footer{background:var(--dark);color:rgba(255,255,255,.72);font-size:var(--fs-meta);padding:40px}
    .fi{max-width:1080px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px 32px;line-height:1.9}
    footer a{color:inherit;text-decoration:none}
    @media (max-width:820px){
      .nav{padding:16px 20px}
      main{padding:40px 20px 72px}
      .grid{grid-template-columns:1fr;gap:32px}
      .cover{position:static;max-width:300px;margin:0 auto}
    }
"""

FONT_HEAD = """  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300..700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
  <script>
    (function(d) {
      var config = { kitId: 'dbx1ynp', scriptTimeout: 3000, async: true },
      h=d.documentElement,t=setTimeout(function(){h.className=h.className.replace(/\\bwf-loading\\b/g,"")+" wf-inactive";},config.scriptTimeout),tk=d.createElement("script"),f=false,s=d.getElementsByTagName("script")[0],a;h.className+=" wf-loading";tk.src='https://use.typekit.net/'+config.kitId+'.js';tk.async=true;tk.onload=tk.onreadystatechange=function(){a=this.readyState;if(f||a&&a!="complete"&&a!="loaded")return;f=true;clearTimeout(t);try{Typekit.load(config)}catch(e){}};s.parentNode.insertBefore(tk,s)
    })(document);
  </script>"""


def render(c: dict, meta: dict, prev: dict | None, nxt: dict | None) -> str:
    title = c["title"]
    slug = page_slug(title)
    url = f"{SITE}/books/{slug}/"
    img = c.get("img", "")
    img_url = f"{SITE}/{img}" if img else f"{SITE}/images/hero-ink.jpg"
    desc = c.get("desc", "")
    author = c.get("author", "")
    awards = [label for key, label in AWARDS if key in (c.get("tags") or "")]
    tags = [t.strip() for t in (c.get("tags") or "").split(",") if t.strip()]
    translator = meta.get("역자", "")
    price = meta.get("정가")
    isbn = meta.get("isbn", "")

    ld = {
        "@context": "https://schema.org", "@type": "Book",
        "name": title, "url": url, "image": img_url, "description": desc,
        "inLanguage": "ko",
        "publisher": {"@type": "Organization", "name": "하루재클럽", "url": SITE + "/"},
    }
    if author:
        ld["author"] = {"@type": "Person", "name": re.sub(r"\s*\(.*?\)\s*", "", author).split(" / ")[0]}
    if translator:
        ld["translator"] = {"@type": "Person", "name": translator}
    if isbn:
        ld["isbn"] = isbn
    if meta.get("발간일"):
        parts = re.findall(r"\d+", meta["발간일"])  # '2021.12.3' → ISO 로 (JSON-LD 는 0 채움 필요)
        if len(parts) == 3:
            ld["datePublished"] = f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    if price:
        ld["offers"] = {"@type": "Offer", "price": str(price), "priceCurrency": "KRW"}

    dl = []
    if meta.get("원제"):
        dl.append(("원제", meta["원제"]))
    if translator:
        dl.append(("옮긴이", translator))
    if meta.get("발간일"):
        dl.append(("발행", meta["발간일"]))
    if price:
        dl.append(("정가", f"{int(price):,}원"))
    if isbn:
        dl.append(("ISBN", f"{isbn[:3]}-{isbn[3:5]}-{isbn[5:10]}-{isbn[10:12]}-{isbn[12]}" if len(isbn) == 13 else isbn))
    dl.append(("발행처", "하루재클럽"))

    buy = []
    if c.get("yes24"):
        buy.append(f'<a href="{esc(c["yes24"])}" target="_blank" rel="noopener noreferrer">예스24</a>')
    if c.get("kyobo"):
        buy.append(f'<a href="{esc(c["kyobo"])}" target="_blank" rel="noopener noreferrer">교보문고</a>')

    def pn(b, arrow_left):
        if not b:
            return "<span></span>"
        return (f'<a href="/books/{page_slug(b["title"])}/">{"← 이전 책" if arrow_left else "다음 책 →"}'
                f'<span class="t">{esc(b["title"])}</span></a>')

    og_desc = desc if len(desc) <= 120 else desc[:117].rstrip() + "…"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} — 하루재클럽</title>
  <meta name="description" content="{esc(desc)}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="book">
  <meta property="og:site_name" content="하루재클럽">
  <meta property="og:title" content="{esc(title)} — 하루재클럽">
  <meta property="og:description" content="{esc(og_desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{img_url}">
  <meta property="og:locale" content="ko_KR">
  <meta name="twitter:card" content="summary">
  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{FONT_HEAD}
  <style>{CSS}  </style>
</head>
<body>
  <nav class="nav">
    <a href="/" class="nav-logo"><img src="/images/logo-sm.png" alt="하루재클럽"></a>
    <div class="nav-links">
      <a href="/#books">전체 도서</a>
      <a href="/#membership">북클럽</a>
      <a href="/#about">출판사</a>
    </div>
  </nav>
  <main>
    <div class="crumb"><a href="/">하루재클럽</a> › <a href="/#books">도서</a> › {esc(title)}</div>
    <div class="grid">
      <div class="cover">{f'<img src="/{esc(img)}" alt="{esc(title)} 표지" width="600">' if img else ''}</div>
      <article>
        {f'<div class="lang">{esc(c.get("lang", ""))}</div>' if c.get("lang") else ''}
        <h1>{esc(title)}</h1>
        {f'<div class="sub">{esc(c["sub"])}</div>' if c.get("sub") and c["sub"] != title else ''}
        {f'<div class="author">{esc(author)}</div>' if author else ''}
        {('<div class="awards">' + ''.join(f'<span>{a}</span>' for a in awards) + '</div>') if awards else ''}
        {f'<div class="series">{esc(c.get("year", ""))}</div>' if c.get("year") else ''}
        <hr>
        <p class="desc">{esc(desc)}</p>
        {f'<div class="quote">{esc(c["quote"])}</div>' if c.get("quote") else ''}
        {('<div class="label">저자 소개</div><p class="bio">' + esc(c["author-bio"]) + '</p>') if c.get("author-bio") else ''}
        <div class="label">서지</div>
        <dl>{''.join(f'<dt>{k}</dt><dd>{esc(v)}</dd>' for k, v in dl)}</dl>
        {('<div class="tags">' + ''.join(f'<span>{esc(t)}</span>' for t in tags) + '</div>') if tags else ''}
        {('<div class="label">구매처</div><div class="buy">' + ''.join(buy) + '</div>') if buy else ''}
        <div class="club">
          <div class="label">하루재북클럽</div>
          <p>월 1만 원의 회비로 하루재클럽의 새 책을 집으로 받아 보는 회원제입니다. 가입하시면 이 책을 포함한 기발간 도서 네 권을 먼저 보내드립니다.</p>
          <a href="/#membership">북클럽 안내 보기</a>
        </div>
        <div class="prevnext">{pn(prev, True)}{pn(nxt, False)}</div>
      </article>
    </div>
  </main>
  <footer>
    <div class="fi">
      <span>© {date.today().year} 하루재클럽</span>
      <span>서울특별시 서초구 나루터로 15길 6 신사 제2빌딩 801호</span>
      <a href="tel:02-521-0067">02-521-0067</a>
      <a href="mailto:haroojaeclub@naver.com">haroojaeclub@naver.com</a>
      <a href="https://www.instagram.com/haroojaeclub/" target="_blank" rel="noopener noreferrer">@haroojaeclub</a>
    </div>
  </footer>
</body>
</html>
"""


def sitemap(cs: list[dict]) -> str:
    today = date.today().isoformat()
    urls = [f"  <url>\n    <loc>{SITE}/</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>"]
    for c in cs:
        urls.append(f"  <url>\n    <loc>{SITE}/books/{page_slug(c['title'])}/</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"


def 카드링크(cs: list[dict]) -> int:
    """카드 안 표지 <img> 를 <a class="book-link"> 로 감싼다. 이미 감싸진 카드는 건너뛴다(멱등)."""
    src = INDEX.read_text(encoding="utf-8")
    n = 0
    for c in cs:
        img = c.get("img")
        if not img:
            continue
        href = f'books/{page_slug(c["title"])}/'
        if f'<a class="book-link" href="{href}"' in src:
            continue
        pat = re.compile(r'(<img loading="lazy" decoding="async" src="' + re.escape(img) + r'" alt="[^"]*">)(?=<div class="book-hover-info">)')
        new, k = pat.subn(lambda m: f'<a class="book-link" href="{href}" aria-label="{esc(c["title"])} 페이지">{m.group(1)}</a>', src, count=1)
        if k:
            src, n = new, n + 1
    if n:
        INDEX.write_text(src, encoding="utf-8")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--확인", action="store_true", help="쓰지 않고 점검만")
    a = ap.parse_args()

    cs = cards()
    metas = json.loads(서지.read_text(encoding="utf-8"))["책"]
    missing = [c["title"] for c in cs if c["title"] not in metas]
    slugs = [page_slug(c["title"]) for c in cs]
    dup = {s for s in slugs if slugs.count(s) > 1}
    print(f"카드 {len(cs)}장 · 서지 {len(metas)}건 · 서지 없는 카드 {len(missing)} {missing or ''} · 슬러그 중복 {dup or '없음'}")
    for c in cs:
        if c.get("img") and not (ROOT / c["img"]).exists():
            print("⚠ 표지 파일 없음:", c["title"], c["img"])
    if a.확인:
        for c in cs:
            print(f"  /books/{page_slug(c['title'])}/   ←  #book/{hash_slug(c['title'])}")
        return 0
    if dup:
        print("슬러그가 겹친다 — 제목을 확인할 것")
        return 1

    OUT.mkdir(exist_ok=True)
    for i, c in enumerate(cs):
        d = OUT / page_slug(c["title"])
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(render(c, metas.get(c["title"], {}), cs[i - 1] if i else None, cs[i + 1] if i + 1 < len(cs) else None), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(cs), encoding="utf-8")
    n = 카드링크(cs)
    stale = [p.name for p in OUT.iterdir() if p.is_dir() and p.name not in slugs]
    print(f"books/ {len(cs)}장 · sitemap {len(cs) + 1}개 · 카드 링크 새로 삽입 {n}곳" + (f" · ⚠ 카드에 없는 폴더 {stale} (직접 지울 것)" if stale else ""))

    # 검증
    bad = []
    for c in cs:
        t = (OUT / page_slug(c["title"]) / "index.html").read_text(encoding="utf-8")
        if not all(k in t for k in ("<title>", 'property="og:image"', 'rel="canonical"', "application/ld+json")):
            bad.append(c["title"])
    src = INDEX.read_text(encoding="utf-8")
    linked = len(re.findall(r'<a class="book-link" href="books/', src))
    print(f"검증: 메타 누락 {bad or '없음'} · index.html 카드 링크 {linked}/{len(cs)}")
    return 1 if bad or linked != len(cs) else 0


if __name__ == "__main__":
    sys.exit(main())
