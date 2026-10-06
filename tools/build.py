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
  schedule/index.html the class schedule (reads a Google Sheet live, see SCHEDULE_SHEET_ID)
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
        "text": "Athena teaches Georgia's state-approved 6-hour Driver Improvement course at our Athens office for $95, the DDS-set price. Call to find the next class.",
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
    <div class="nav-links" id="site-menu">
      <a href="/#courses">Courses</a>
      <a href="/dui-school-athens-ga/"{cur("dui")}>DUI School</a>
      <a href="/schedule/"{cur("schedule")}>Schedule</a>
      <a href="/guides/"{cur("guides")}>Guides</a>
      <a href="/#faq">FAQ</a>
    </div>
    <div class="nav-cta">
      <button class="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="site-menu">&#9776;</button>
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
        <li><a href="/schedule/">Class schedule</a></li>
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
</footer>
<script>
(function () {{
  var nav = document.querySelector('.nav'), btn = document.querySelector('.nav-toggle');
  if (!nav || !btn) return;
  btn.addEventListener('click', function () {{
    var open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    btn.innerHTML = open ? '&#10005;' : '&#9776;';
  }});
  nav.querySelectorAll('.nav-links a').forEach(function (a) {{ a.addEventListener('click', function () {{ nav.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); btn.innerHTML = '&#9776;'; }}); }});
}})();
</script>'''


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


# The class schedule is read live from a Google Sheet so the owner can add,
# change or cancel classes without touching the site. The sheet must be shared
# as "Anyone with the link: Viewer". Columns (first row, in this order):
# Program, Start date, End date, Days, Time, Format, Instructor, Status, Notes
SCHEDULE_SHEET_ID = "1U61fjwz8i6nx9GkNcC-wxEgjJyk8M7ngWe5MeJYt2t0"


def render_schedule():
    url = f"{SITE}/schedule/"
    title = "Class Schedule | DUI School & Driver Improvement, Athens GA"
    desc = ("Upcoming DUI Risk Reduction (RRP) and Driver Improvement class dates at Athena DUI Academy "
            "in Athens, Georgia. Register online for RRP or call 706.215.9661.")
    schema = [breadcrumb_schema([("Home", f"{SITE}/"), ("Class schedule", url)]),
              {"@context": "https://schema.org", "@type": "WebPage", "name": "Class schedule", "url": url,
               "description": desc, "publisher": ORG_REF}]
    csv_url = f"https://docs.google.com/spreadsheets/d/{SCHEDULE_SHEET_ID}/gviz/tq?tqx=out:csv&headers=1"
    return f"""{head(title, desc, url, "website", schema)}
<body>
{chrome_top("schedule")}
<header class="page-head">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span>Class schedule</nav>
    <span class="eyebrow">Athens, Georgia</span>
    <h1>Class schedule</h1>
    <p class="dek">Upcoming DUI Risk Reduction Program (<span class="cert">{CERT}</span>) and Driver Improvement classes. Register online for the Risk Reduction Program, or call <strong>{PHONE_DISPLAY}</strong>. You must call to register for Driver Improvement.</p>
    <div class="head-ctas"><a class="btn btn-primary" href="{REGISTER}" target="_blank" rel="noopener">Register for RRP online</a><a class="btn btn-ghost" href="tel:{PHONE_TEL}">Call {PHONE_DISPLAY}</a></div>
  </div>
</header>
<main class="wrap schedule" id="schedule" data-src="{csv_url}">
  <p class="sched-status" id="sched-status" role="status">Loading the current schedule…</p>
  <section class="sched-program" id="prog-rrp">
    <h2>DUI Risk Reduction Program (DUI school)</h2>
    <p class="sched-lead">The 20-hour state-approved course, $360. Weekend classes run Friday evening through Sunday or Saturday through Monday; weeknight classes run Monday through Friday evenings. <a href="/dui-school-athens-ga/">About the program</a>.</p>
    <div class="sched-rows" data-program="rrp"></div>
  </section>
  <section class="sched-program" id="prog-di">
    <h2>Driver Improvement (6-hour defensive driving)</h2>
    <p class="sched-lead">The DDS-approved 6-hour course, $95, taught in person at our Athens office. One Saturday, or two or three evenings. <strong>Call {PHONE_DISPLAY} to register for Driver Improvement.</strong> <a href="/driver-improvement-athens-ga/">About the course</a>.</p>
    <div class="sched-rows" data-program="di"></div>
  </section>
  <section class="sched-program" id="prog-other" hidden>
    <h2>Other classes</h2>
    <div class="sched-rows" data-program="other"></div>
  </section>
  <div class="callout note sched-note">
    <p><strong>Good to know.</strong> Classes need a minimum number of paid registrations, so a class can be rescheduled or cancelled; we will contact everyone registered. Arrive on time: DDS rules let the school turn away late students. Clinical evaluations and anger management classes are scheduled by appointment, so call us for those.</p>
  </div>
  <noscript><p class="sched-status">Please call {PHONE_DISPLAY} for the current class schedule.</p></noscript>
</main>
<script>
(function () {{
  var root = document.getElementById('schedule');
  var status = document.getElementById('sched-status');
  var REGISTER = {json.dumps(REGISTER)};
  var TEL = 'tel:{PHONE_TEL}';
  var PHONE = '{PHONE_DISPLAY}';
  var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

  function parseCSV(text) {{
    var rows = [], row = [], field = '', q = false;
    for (var i = 0; i < text.length; i++) {{
      var c = text[i];
      if (q) {{
        if (c === '"') {{ if (text[i + 1] === '"') {{ field += '"'; i++; }} else q = false; }}
        else field += c;
      }} else if (c === '"') q = true;
      else if (c === ',') {{ row.push(field); field = ''; }}
      else if (c === '\\n' || c === '\\r') {{
        if (c === '\\r' && text[i + 1] === '\\n') i++;
        row.push(field); rows.push(row); row = []; field = '';
      }} else field += c;
    }}
    if (field !== '' || row.length) {{ row.push(field); rows.push(row); }}
    return rows;
  }}

  function parseDate(s) {{
    s = (s || '').trim();
    if (!s) return null;
    var m = s.match(/^(\\d{{1,2}})[\\/\\-.](\\d{{1,2}})[\\/\\-.](\\d{{2,4}})$/);
    if (m) {{ var y = +m[3]; if (y < 100) y += 2000; return new Date(y, +m[1] - 1, +m[2]); }}
    m = s.match(/^(\\d{{4}})-(\\d{{1,2}})-(\\d{{1,2}})/);
    if (m) return new Date(+m[1], +m[2] - 1, +m[3]);
    var d = new Date(s);
    return isNaN(d) ? null : new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }}

  function fmt(d) {{ return MONTHS[d.getMonth()].slice(0, 3) + ' ' + d.getDate(); }}
  function dateRange(a, b) {{
    if (!b || a.getTime() === b.getTime()) return fmt(a);
    if (a.getMonth() === b.getMonth()) return MONTHS[a.getMonth()].slice(0, 3) + ' ' + a.getDate() + '–' + b.getDate();
    return fmt(a) + ' – ' + fmt(b);
  }}
  function esc(s) {{ return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {{ return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]; }}); }}

  function programKey(name) {{
    var n = (name || '').toLowerCase();
    if (/driver|defensive|\\bdi\\b/.test(n)) return 'di';
    if (/rrp|risk|dui/.test(n)) return 'rrp';
    return 'other';
  }}
  function statusKey(s) {{
    s = (s || '').toLowerCase().trim();
    if (!s || /open|avail|yes/.test(s)) return 'open';
    if (/cancel/.test(s)) return 'cancelled';
    if (/full|closed|sold/.test(s)) return 'full';
    if (/pend|tent|tba/.test(s)) return 'pending';
    return 'open';
  }}
  var LABEL = {{open: 'Open', cancelled: 'Cancelled', full: 'Full', pending: 'Pending'}};

  function render(rows) {{
    var header = rows.shift().map(function (h) {{ return h.toLowerCase().trim(); }});
    function col(r, name) {{ var i = header.indexOf(name); return i < 0 ? '' : (r[i] || '').trim(); }}
    var today = new Date(); today = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    var groups = {{rrp: [], di: [], other: []}};
    rows.forEach(function (r) {{
      if (!r.join('').trim()) return;
      var start = parseDate(col(r, 'start date')), end = parseDate(col(r, 'end date')) || start;
      if (!start) return;
      if (end < today) return;
      groups[programKey(col(r, 'program'))].push({{
        program: col(r, 'program'), start: start, end: end, days: col(r, 'days'), time: col(r, 'time'),
        format: col(r, 'format'), instructor: col(r, 'instructor'), status: statusKey(col(r, 'status')),
        notes: col(r, 'notes')
      }});
    }});
    var total = 0;
    Object.keys(groups).forEach(function (k) {{
      var list = groups[k].sort(function (a, b) {{ return a.start - b.start; }});
      var box = root.querySelector('[data-program="' + k + '"]');
      var section = box.parentNode;
      if (k === 'other') section.hidden = !list.length;
      if (!list.length) {{
        box.innerHTML = '<p class="sched-empty">No upcoming classes are posted yet. Call ' + PHONE + ' and we will put you in the next one.</p>';
        return;
      }}
      total += list.length;
      var html = '', month = '';
      list.forEach(function (c) {{
        var m = MONTHS[c.start.getMonth()] + ' ' + c.start.getFullYear();
        if (m !== month) {{ html += '<h3 class="sched-month">' + m + '</h3>'; month = m; }}
        var action = c.status === 'cancelled' ? '' : c.status === 'full'
          ? '<a class="btn btn-ghost" href="' + TEL + '">Call for the next class</a>'
          : k === 'di' || /call/i.test(c.notes)
            ? '<a class="btn btn-primary" href="' + TEL + '">Call to register</a>'
            : '<a class="btn btn-primary" href="' + REGISTER + '" target="_blank" rel="noopener">Register</a>';
        html += '<div class="sched-row is-' + c.status + '">' +
          '<div class="sched-when"><span class="sched-date">' + esc(dateRange(c.start, c.end)) + '</span>' +
          (c.days ? '<span class="sched-days">' + esc(c.days) + '</span>' : '') + '</div>' +
          '<div class="sched-info">' +
          (c.time ? '<div><span class="k">Time</span>' + esc(c.time) + '</div>' : '') +
          (c.format ? '<div><span class="k">Format</span>' + esc(c.format) + '</div>' : '') +
          (c.instructor ? '<div><span class="k">Instructor</span>' + esc(c.instructor) + '</div>' : '') +
          (c.notes && !/^call to register$/i.test(c.notes) ? '<div><span class="k">Note</span>' + esc(c.notes) + '</div>' : '') +
          '</div>' +
          '<div class="sched-act"><span class="badge badge-' + c.status + '">' + LABEL[c.status] + '</span>' + action + '</div>' +
          '</div>';
      }});
      box.innerHTML = html;
    }});
    status.textContent = total ? 'Showing ' + total + ' upcoming class' + (total === 1 ? '' : 'es') + '. Dates can change, so confirm when you register.' : 'No classes are posted right now. Call ' + PHONE + '.';
  }}

  function fail() {{
    status.innerHTML = 'We could not load the schedule just now. Please call <a href="' + TEL + '">' + PHONE + '</a> for class dates, or try again in a minute.';
    status.className += ' is-error';
  }}

  // /schedule/?demo=1 shows built-in sample rows so the layout can be previewed before the sheet is filled in.
  var DEMO = 'Program,Start date,End date,Days,Time,Format,Instructor,Status,Notes\\n' +
    'DUI Risk Reduction (RRP),10/9/2026,10/11/2026,Fri-Sun (Weekend),6:00 pm Fri,In person,Mike Oakes,Open,\\n' +
    'DUI Risk Reduction (RRP),10/19/2026,10/23/2026,Mon-Fri (Weeknight),6:00 pm - 10:00 pm,In person,Jimmy Wood,Open,\\n' +
    'DUI Risk Reduction (RRP),10/17/2026,10/19/2026,Sat-Mon (Weekend),9:00 am,In person,Mike Oakes,Cancelled,Rescheduled - call us\\n' +
    'DUI Risk Reduction (RRP),10/23/2026,10/25/2026,Fri-Sun (Weekend),9:00 am,In person,,Pending,Starts on Friday\\n' +
    'DUI Risk Reduction (RRP),11/6/2026,11/8/2026,Fri-Sun (Weekend),6:00 pm Fri,In person,Mike Oakes,Full,\\n' +
    'Driver Improvement,10/10/2026,10/10/2026,Saturday,10:00 am - 5:00 pm,In person,,Open,Call to register\\n' +
    'Driver Improvement,10/20/2026,10/21/2026,Tue & Wed,6:00 pm - 9:00 pm,In person,,Open,Call to register\\n' +
    'Driver Improvement,10/31/2026,10/31/2026,Saturday,10:00 am - 5:00 pm,In person,,Open,Call to register\\n';
  if (/[?&]demo=1/.test(location.search)) {{
    render(parseCSV(DEMO));
    status.textContent = 'SAMPLE SCHEDULE for preview only. These dates are not real. ' + status.textContent;
    return;
  }}

  try {{
    fetch(root.getAttribute('data-src') + '&_=' + Date.now(), {{cache: 'no-store'}})
      .then(function (r) {{ if (!r.ok) throw new Error(r.status); return r.text(); }})
      .then(function (t) {{ var rows = parseCSV(t); if (!rows.length || !rows[0].join('').trim()) rows = [['program']]; render(rows); }})
      .catch(fail);
  }} catch (e) {{ fail(); }}
}})();
</script>
{chrome_bottom()}
</body>
</html>
"""


def write_sitemap(pages):
    today = dt.date.today().isoformat()
    urls = [(f"{SITE}/", today, "1.0"), (f"{SITE}/schedule/", today, "0.9"), (f"{SITE}/guides/", today, "0.8")]
    for p in sorted(pages, key=lambda p: (p["type"] != "service", p["type"] != "pillar", p["slug"])):
        prio = {"service": "0.9", "pillar": "0.8"}.get(p["type"], "0.7")
        urls.append((f"{SITE}/{p['slug']}/", p["updated"], prio))
    body = "\n".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n    <priority>{pr}</priority>\n  </url>"
                     for u, d, pr in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n')


def write_cpanel(pages):
    dirs = ["assets", "guides", "schedule"] + sorted(p["slug"] for p in pages)
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
    (ROOT / "schedule").mkdir(exist_ok=True)
    (ROOT / "schedule" / "index.html").write_text(render_schedule(), encoding="utf-8")
    write_sitemap(pages)
    write_cpanel(pages)
    print(f"built {len(pages)} pages + guides hub, sitemap.xml, .cpanel.yml")


if __name__ == "__main__":
    main()
