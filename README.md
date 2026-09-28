# Athena DUI Academy & Family Enrichment — W.O.W.

Static marketing site for Athena DUI Academy & Family Enrichment (Athens, GA).
One page, no build step: plain HTML + CSS, fonts from Google Fonts.

## Structure

```
index.html                 homepage (hand-edited; styles inline)
content/pages/*.html       source for every service page and guide
tools/build.py             turns content/pages into /<slug>/index.html
assets/site.css            styles for the generated pages
<slug>/index.html          GENERATED pages, one folder each
guides/index.html          GENERATED hub listing every guide
sitemap.xml                GENERATED
.cpanel.yml                GENERATED deploy manifest (what cPanel copies)
404.html, robots.txt
img/logo.png, img/justice.png   supplied by the owner
```

## Editing pages

Service pages and guides are written in `content/pages/<slug>.html`: a JSON
`META` block (title, description, key takeaways, FAQs, sources, related pages)
followed by the body HTML. After changing any of them, run:

```
python3 tools/build.py --strict
```

That rebuilds every page, the guides hub, `sitemap.xml` and `.cpanel.yml`.
`--strict` fails on broken internal links. Commit the generated files along
with the content. The script uses only the Python standard library.

To add a page: create `content/pages/<new-slug>.html` (copy an existing one as
a template), then run the build. It is added to the sitemap and the deploy
manifest automatically.

## Deployment

Every push to the default branch deploys to cPanel via
`.github/workflows/deploy-cpanel.yml`. The live site is
https://wow-athena.com.

The GitHub Pages preview was removed: it served the same page on a second
public URL, which would have competed with the real site in search results.

### cPanel

`deploy-cpanel.yml` calls cPanel's Git Version Control API: it pulls the branch
into the server-side clone (`VersionControl/update`), then queues a deployment
(`VersionControlDeployment/create`) which runs the tasks in `.cpanel.yml`.

It needs four repository secrets — `CPANEL_HOST`, `CPANEL_USER`,
`CPANEL_API_TOKEN`, `CPANEL_REPO_ROOT` — and a clone that already exists under
cPanel > Files > Git Version Control. `CPANEL_HOST` must be the hostname the
server's TLS certificate is issued for (usually `serverNNN.<host>.com`), not
`wow-athena.com`.

Which files reach `public_html` is decided by `.cpanel.yml`, not by the
workflow. `tools/build.py` regenerates it, so new pages are included
automatically. Removing a file from the repo does not delete it from the
server; add an `/bin/rm -f` task for that.

## Images

`index.html` references exactly two image files, and neither is in this repo:

| Path              | Where it appears | Suggested size          |
|-------------------|------------------|-------------------------|
| `img/logo.png`    | Nav bar, top left | ~1400 x 300 px, transparent background |
| `img/justice.png` | Hero, right side  | ~900 x 1200 px, transparent background |

Add the real artwork at those exact paths (lowercase `img/`, lowercase
filenames) and it renders with no code change. Until then the nav shows the
logo's alt text and the hero panel is empty.

## Notes

- Enroll and Register buttons go to the online registration system at
  garrp2.adeincorp.com, where students sign up, pay and complete their DDS
  paperwork.
- The DUI Risk Reduction Program is DDS-certified as RRP Cert #10432. The
  auditor requires that number on the site wherever state certification is
  mentioned; `CERT` in `tools/build.py` controls it on generated pages.
- The "4.9 · 1,200+ Reviews" trust badge and the three testimonials on the
  homepage are placeholder copy and should be replaced with real ones or removed.
- Driver Improvement and Anger Management prices are shown as "Call for
  pricing" until the owner supplies them.
