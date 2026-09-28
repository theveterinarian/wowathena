#!/usr/bin/env python3
"""Build the site's inner pages from content/pages/*.html.

Each content file starts with a META block of JSON, followed by the body HTML:

    <!--META
    { "slug": "...", "type": "article", "title": "...", ... }
    -->
    <h2>First section</h2>
    <p>...</p>

Running this script (python3 tools/build.py) writes:
  <slug>/index.html   for every content file
  guides/index.html   the hub page listing every guide
  sitemap.xml         every public page
  .cpanel.yml         the deploy manifest, so no page is left off the server

It uses only the Python standard library. Re-run it after editing any content.
"""

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "pages"
SITE = "https://wow-athena.com"
REGISTER = "https://garrp2.adeincorp.com/location/0x61b1374ea5da933164af8269b122cdd4/"
PHONE_DISPLAY = "706.215.9661"
PHONE_TEL = "7062159661"
CERT = "RRP Cert #10432"
ORG_NAME = "Athena DUI Academy & Family Enrichment"

REQUIRED = ["slug", "type", "title", "h1", "description", "dek", "category",
            "updated", "takeaways", "faqs", "sources", "related", "cta"]
TYPES = {"service", "article", "pillar"}

# Mid-article and sidebar calls to action, one per service.
CTAS = {
    "dui": {
        "title": "Need Georgia DUI school?",
        "text": f'Athena\'s DDS-certified Risk Reduction Program (<span class="cert">{CERT}</span>) is $360, taught live online or in person in Athens.',
        "page": "/dui-school-athens-ga/",
    },
    "driver": {
        "title": "Need a Driver Improvement course?",
        "text": "Athena teaches Georgia's state-approved 6-hour Driver Improvement course, live online or in person in Athens.",
        "page": "/driver-improvement-athens-ga/",
    },
    "clinical": {
        "title": "Need a clinical evaluation?",
        "text": "Athena offers DUI clinical evaluations in Athens for $150. Call to schedule yours.",
        "page": "/clinical-evaluation-athens-ga/",
    },
    "anger": {
        "title": "Need anger management classes?",
        "text": "Athena offers anger management classes for court, probation or personal goals, live online or in person in Athens.",
        "page": "/anger-management-athens-ga/",
    },
}

STRICT = "--strict" in sys.argv

CATEGORY_ORDER = ["Our services", "Georgia DUI school", "After a DUI in Georgia", "Anger management"]


def esc(s):
    return html.escape(s, quote=True)


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60].strip("-")


def parse(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--META\s*(\{.*?\})\s*-->\s*(.*)\Z", raw, re.S)
    if not m:
        sys.exit(f"{path.name}: missing <!--META {{...}} --> header")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        sys.exit(f"{path.name}: META is not valid JSON: {e}")
    missing = [k for k in REQUIRED if k not in meta]
    if missing:
        sys.exit(f"{path.name}: META missing {missing}")
    if meta["type"] not in TYPES:
        sys.exit(f"{path.name}: type must be one of {sorted(TYPES)}")
    if meta["cta"] not in CTAS:
        sys.exit(f"{path.name}: cta must be one of {sorted(CTAS)}")
    if meta["slug"] + ".html" != path.name:
        sys.exit(f"{path.name}: slug '{meta['slug']}' must match the file name")
    meta["body"] = m.group(2).strip()
    return meta


def add_heading_ids(body):
    """Give every <h2> an id and return (body, table_of_contents)."""
    toc, seen = [], set()

    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        if "id=" in attrs:
            hid = re.search(r'id="([^"]+)"', attrs).group(1)
        else:
            hid = slugify(inner) or "section"
            base, n = hid, 2
            while hid in seen:
                hid, n = f"{base}-{n}", n + 1
            attrs = f'{attrs} id="{hid}"'
        seen.add(hid)
        toc.append((hid, re.sub(r"<[^>]+>", "", inner)))
        return f"<h2{attrs}>{inner}</h2>"

    return re.sub(r"<h2([^>]*)>(.*?)</h2>", repl, body, flags=re.S), toc


def words(text):
    return len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", text)))


def inline_cta(kind, here):
    c = CTAS[kind]
    details = "" if c["page"] == here else f'<a class="btn btn-ghost" href="{c["page"]}">Learn more</a>'
    return f'''<aside class="inline-cta" aria-label="Enroll">
  <div><h3>{c["title"]}</h3><p>{c["text"]}</p></div>
  <div class="btns"><a class="btn btn-gold" href="{REGISTER}" target="_blank" rel="noopener">Register now</a>{details}<a class="btn btn-ghost" href="tel:{PHONE_TEL}">Call {PHONE_DISPLAY}</a></div>
</aside>'''


def chrome_top(active=None):
    cur = lambda name: ' aria-current="page"' if active == name else ""
    return f'''<div class="topbar">
  Class Now, Pay Later with <strong>Stripe</strong> for qualifying students
  <span class="sep">|</span>
  Call <strong>{PHONE_DISPLAY}</strong> for more info
</div>
<nav class="nav">
  <div class="wrap">
    <a href="/" class="brand" aria-label="{esc(ORG_NAME)} home"><img src="/img/logo.png" alt="{esc(ORG_NAME)}" class="brand-logo" width="222" height="60"></a>
    <div class="nav-links">
      <a href="/#courses">Courses</a>
      <a href="/dui-school-athens-ga/"{cur("dui")}>DUI School</a>
      <a href="/guides/"{cur("guides")}>Guides</a>
      <a href="/#faq">FAQ</a>
    </div>
    <div class="nav-cta">
      <a href="tel:{PHONE_TEL}" class="num">{PHONE_DISPLAY}</a>
      <a href="{REGISTER}" target="_blank" rel="noopener" class="btn btn-primary">Enroll Now</a>
    </div>
  </div>
</nav>'''


def chrome_bottom():
    year = dt.date.today().year
    return f'''<section class="band">
  <div class="wrap">
    <h2>Call now or click to register</h2>
    <p>Sign up and fill out your DDS paperwork online, then choose a class that fits your schedule. We are available in person or by phone.</p>
    <a href="tel:{PHONE_TEL}" class="phone-big">📞 {PHONE_DISPLAY}</a>
    <a href="{REGISTER}" target="_blank" rel="noopener" class="btn btn-gold">Register for Our Next Class →</a>
  </div>
</section>
<footer class="foot">
  <div class="wrap cols">
    <div>
      <a href="/" class="brand-foot" aria-label="{esc(ORG_NAME)} home"><img src="/img/logo.png" alt="{esc(ORG_NAME)}" loading="lazy"></a>
      <p>Georgia DDS-approved DUI Risk Reduction Program (<span class="cert">{CERT}</span>) and Driver Improvement, plus clinical evaluations and anger management.</p>
    </div>
    <div>
      <h4>Programs</h4>
      <ul>
        <li><a href="/dui-school-athens-ga/">DUI Risk Reduction Program</a></li>
        <li><a href="/driver-improvement-athens-ga/">Driver Improvement</a></li>
        <li><a href="/clinical-evaluation-athens-ga/">Clinical Evaluation</a></li>
        <li><a href="/anger-management-athens-ga/">Anger Management</a></li>
      </ul>
    </div>
    <div>
      <h4>Resources</h4>
      <ul>
        <li><a href="/guides/">All guides</a></li>
        <li><a href="/georgia-dui-school-guide/">Georgia DUI School Guide</a></li>
        <li><a href="/get-license-back-after-dui-georgia/">License Reinstatement</a></li>
        <li><a href="/#faq">FAQ</a></li>
      </ul>
    </div>
    <div>
      <h4>Contact</h4>
      <ul>
        <li><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></li>
        <li><a href="mailto:registration@wowathena.com">registration@wowathena.com</a></li>
        <li>Mon–Fri · 10am – 6pm</li>
        <li>110 Athens West Pkwy, Ste.C<br>Athens, GA 30606</li>
      </ul>
    </div>
  </div>
  <div class="wrap foot-bottom">© {year} {esc(ORG_NAME)} · Georgia DDS-Approved DUI Risk Reduction Program · {CERT}</div>
</footer>'''


def head(title, description, canonical, og_type, schema):
    ld = "\n".join(
        f'<script type="application/ld+json">\n{json.dumps(s, indent=2, ensure_ascii=False)}\n</script>'
        for s in schema)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#5b1d8e">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{esc(ORG_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{SITE}/img/logo.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><text y='52' font-size='52'>⚖️</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
{ld}
</head>'''


ORG_REF = {"@type": "EducationalOrganization", "@id": f"{SITE}/#organization", "name": ORG_NAME,
           "url": f"{SITE}/", "logo": f"{SITE}/img/logo.png"}


def breadcrumb_schema(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": name, "item": url}
                                for i, (name, url) in enumerate(trail)]}


def render_page(p, pages_by_slug):
    url = f"{SITE}/{p['slug']}/"
    body, toc = add_heading_ids(p["body"])
    if "<!--CTA-->" in body:
        body = body.replace("<!--CTA-->", inline_cta(p["cta"], f"/{p['slug']}/"), 1)
    total_words = words(body) + sum(words(q + a) for q, a in p["faqs"])
    minutes = max(1, round(total_words / 225))
    updated = dt.date.fromisoformat(p["updated"])
    updated_h = updated.strftime("%B %-d, %Y")

    section_name, section_url = ("Our services", f"{SITE}/#courses") if p["type"] == "service" \
        else ("Guides", f"{SITE}/guides/")
    trail = [("Home", f"{SITE}/"), (section_name, section_url), (p["h1"], url)]

    schema = [breadcrumb_schema(trail)]
    if p["type"] == "service":
        svc = {"@context": "https://schema.org", "@type": "Service", "name": p["h1"],
               "serviceType": p.get("service_name", p["h1"]), "description": p["description"],
               "url": url, "provider": ORG_REF,
               "areaServed": {"@type": "State", "name": "Georgia"}}
        if p.get("price"):
            svc["offers"] = {"@type": "Offer", "price": str(p["price"]), "priceCurrency": "USD", "url": REGISTER}
        schema.append(svc)
    else:
        schema.append({"@context": "https://schema.org", "@type": "Article", "headline": p["h1"],
                       "description": p["description"], "mainEntityOfPage": url,
                       "datePublished": p.get("published", p["updated"]), "dateModified": p["updated"],
                       "author": ORG_REF, "publisher": ORG_REF, "image": f"{SITE}/img/logo.png",
                       "inLanguage": "en-US"})
    if p["faqs"]:
        schema.append({"@context": "https://schema.org", "@type": "FAQPage",
                       "mainEntity": [{"@type": "Question", "name": q,
                                       "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faqs"]]})

    takeaways = "\n".join(f"<li>{t}</li>" for t in p["takeaways"])
    toc_html = "\n".join(f'<li><a href="#{hid}">{esc(label)}</a></li>' for hid, label in toc)
    if p["faqs"]:
        toc_html += '\n<li><a href="#faq">Frequently asked questions</a></li>'
    faq_html = ""
    if p["faqs"]:
        faq_html = '<section class="faq" id="faq"><h2>Frequently asked questions</h2>\n' + "\n".join(
            f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in p["faqs"]) + "\n</section>"
    sources_html = ""
    if p["sources"]:
        sources_html = '<section class="sources"><h2>Sources</h2><ul>\n' + "\n".join(
            f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(label)}</a></li>'
            for label, u in p["sources"]) + "\n</ul></section>"
    disclaimer = ('<p class="disclaimer">This page is general information about Georgia requirements, '
                  'not legal advice. Rules change and every case is different, so confirm the details '
                  'with the court, the Georgia DDS, or an attorney.</p>')
    related_cards = []
    for slug in p["related"]:
        r = pages_by_slug.get(slug)
        if not r:
            if STRICT:
                sys.exit(f"{p['slug']}: related page '{slug}' does not exist")
            print(f"  warning: {p['slug']} links to missing page '{slug}'")
            continue
        related_cards.append(f'<a class="related-card" href="/{slug}/"><span class="cat">{esc(r["category"])}</span>'
                             f'<h3>{esc(r["h1"])}</h3></a>')
    related_html = ('<section class="related"><h2>Keep reading</h2><div class="related-grid">'
                    + "".join(related_cards) + "</div></section>") if related_cards else ""

    c = CTAS[p["cta"]]
    here = f"/{p['slug']}/"
    side_details = "" if c["page"] == here else f'<a class="btn btn-ghost" href="{c["page"]}" style="color:#fff;border-color:rgba(255,255,255,.6)">Learn more</a>'
    head_ctas = ""
    if p["type"] == "service":
        head_ctas = (f'<div class="head-ctas"><a class="btn btn-primary" href="{REGISTER}" target="_blank" rel="noopener">Register now</a>'
                     f'<a class="btn btn-ghost" href="tel:{PHONE_TEL}">Call {PHONE_DISPLAY}</a></div>')

    kind = "Service" if p["type"] == "service" else "Guide"
    byline = (f'<span>By <strong>{esc(ORG_NAME)}</strong></span>'
              f'<span>Last reviewed <time datetime="{updated.isoformat()}">{updated_h}</time></span>'
              f'<span>{minutes} min read</span>')

    active = "dui" if p["slug"] == "dui-school-athens-ga" else ("guides" if p["type"] != "service" else None)
    return f'''{head(p["title"], p["description"], url, "article" if p["type"] != "service" else "website", schema)}
<body>
{chrome_top(active)}
<header class="page-head">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span><a href="{"/#courses" if p["type"] == "service" else "/guides/"}">{section_name}</a><span>›</span>{esc(p["h1"])}</nav>
    <span class="eyebrow">{esc(p["category"])}</span>
    <h1>{p["h1"]}</h1>
    <p class="dek">{p["dek"]}</p>
    <div class="byline">{byline}</div>
    {head_ctas}
  </div>
</header>
<div class="wrap layout">
  <article class="article">
    <section class="takeaways"><h2>Key takeaways</h2><ul>
{takeaways}
    </ul></section>
    <div class="article-body">
{body}
    </div>
    {faq_html}
    {sources_html}
    {disclaimer}
    {related_html}
  </article>
  <aside class="aside">
    <div class="side-card toc"><h3>On this page</h3><ol>
{toc_html}
    </ol></div>
    <div class="side-card cta">
      <h3>{c["title"]}</h3>
      <p>{c["text"]}</p>
      <a class="btn btn-gold" href="{REGISTER}" target="_blank" rel="noopener">Register now</a>
      {side_details}
      <a class="phone" href="tel:{PHONE_TEL}">📞 {PHONE_DISPLAY}</a>
    </div>
  </aside>
</div>
{chrome_bottom()}
</body>
</html>
'''


def render_hub(pages):
    url = f"{SITE}/guides/"
    groups = {}
    for p in pages:
        groups.setdefault(p["category"], []).append(p)
    order = [c for c in CATEGORY_ORDER if c in groups] + sorted(c for c in groups if c not in CATEGORY_ORDER)
    sections = []
    for cat in order:
        items = sorted(groups[cat], key=lambda p: (p["type"] != "pillar", p.get("order", 50), p["h1"]))
        cards = "".join(
            f'<a class="hub-card" href="/{p["slug"]}/"><span class="cat">{"Complete guide" if p["type"] == "pillar" else esc(p["category"])}</span>'
            f'<h3>{esc(p["h1"])}</h3><p>{esc(p["description"])}</p><span class="more">Read →</span></a>'
            for p in items)
        sections.append(f'<section class="hub-group"><h2>{esc(cat)}</h2><div class="hub-grid">{cards}</div></section>')
    schema = [breadcrumb_schema([("Home", f"{SITE}/"), ("Guides", url)]),
              {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Georgia DUI & court-class guides",
               "url": url, "publisher": ORG_REF,
               "hasPart": [{"@type": "WebPage", "name": p["h1"], "url": f"{SITE}/{p['slug']}/"} for p in pages]}]
    title = "Georgia DUI School & Court Class Guides | Athena DUI Academy"
    desc = ("Plain-English guides to Georgia DUI school, license reinstatement, clinical evaluations, "
            "Driver Improvement and anger management, from a DDS-certified Athens school.")
    return f'''{head(title, desc, url, "website", schema)}
<body>
{chrome_top("guides")}
<header class="page-head">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span>Guides</nav>
    <span class="eyebrow">Guides</span>
    <h1>Georgia DUI school &amp; court class guides</h1>
    <p class="dek">Straight answers about Georgia's DUI Risk Reduction Program, getting your license back, clinical evaluations, Driver Improvement and anger management, written by a DDS-certified school in Athens (<span class="cert">{CERT}</span>).</p>
  </div>
</header>
<main class="wrap">
{"".join(sections)}
</main>
{chrome_bottom()}
</body>
</html>
'''


def write_sitemap(pages):
    today = dt.date.today().isoformat()
    urls = [(f"{SITE}/", today, "1.0"), (f"{SITE}/guides/", today, "0.8")]
    for p in sorted(pages, key=lambda p: (p["type"] != "service", p["type"] != "pillar", p["slug"])):
        prio = {"service": "0.9", "pillar": "0.8"}.get(p["type"], "0.7")
        urls.append((f"{SITE}/{p['slug']}/", p["updated"], prio))
    body = "\n".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n    <priority>{pr}</priority>\n  </url>"
                     for u, d, pr in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n')


def write_cpanel(pages):
    dirs = ["assets", "guides"] + sorted(p["slug"] for p in pages)
    copies = "\n".join(f"    - /bin/cp -R {d} $DEPLOYPATH/" for d in dirs)
    (ROOT / ".cpanel.yml").write_text(f'''---
# cPanel "Git Version Control" deployment. GENERATED by tools/build.py:
# edit the template in that script rather than this file.
#
# cPanel runs these tasks when .github/workflows/deploy-cpanel.yml queues a
# deployment. They copy the public site into public_html.
#
# $HOME is your cPanel home directory (/home/<your-cpanel-username>).
deployment:
  tasks:
    - export DEPLOYPATH=$HOME/public_html
    - /bin/mkdir -p $DEPLOYPATH/img
    - /bin/cp    index.html   $DEPLOYPATH/
    - /bin/cp    404.html     $DEPLOYPATH/
    - /bin/cp    robots.txt   $DEPLOYPATH/
    - /bin/cp    sitemap.xml  $DEPLOYPATH/
    - /bin/cp -R img/.        $DEPLOYPATH/img/
    - /bin/rm -f              $DEPLOYPATH/img/.gitkeep
{copies}
''')


def check_internal_links(pages, by_slug):
    """Fail if any body links to an internal page that doesn't exist."""
    known = set(by_slug) | {"guides", ""}
    bad = []
    for p in pages:
        for target in re.findall(r'href="/([^"#?]*)', p["body"]):
            if target.strip("/") not in known:
                bad.append(f"{p['slug']} -> /{target}")
    if bad:
        sys.exit("broken internal links:\n  " + "\n  ".join(bad))


def main():
    files = sorted(CONTENT.glob("*.html"))
    if not files:
        sys.exit("no content in content/pages/")
    pages = [parse(f) for f in files]
    by_slug = {p["slug"]: p for p in pages}
    if STRICT:
        check_internal_links(pages, by_slug)
    for p in pages:
        out = ROOT / p["slug"]
        out.mkdir(exist_ok=True)
        (out / "index.html").write_text(render_page(p, by_slug), encoding="utf-8")
    (ROOT / "guides").mkdir(exist_ok=True)
    (ROOT / "guides" / "index.html").write_text(render_hub(pages), encoding="utf-8")
    write_sitemap(pages)
    write_cpanel(pages)
    print(f"built {len(pages)} pages + guides hub, sitemap.xml, .cpanel.yml")


if __name__ == "__main__":
    main()
