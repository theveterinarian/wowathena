# Athena DUI Academy & Family Enrichment — W.O.W.

Static marketing site for Athena DUI Academy & Family Enrichment (Athens, GA).
One page, no build step: plain HTML + CSS, fonts from Google Fonts.

## Structure

```
index.html            the entire site
img/logo.png          nav logo      -- SUPPLY THIS FILE
img/justice.png       hero artwork  -- SUPPLY THIS FILE
.nojekyll             serve files as-is on GitHub Pages
.github/workflows/deploy.yml   Pages deployment
```

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
workflow. Add a `/bin/cp` line there for any new file.

### GitHub Pages

Every push to the repository's **default branch** runs
`.github/workflows/deploy.yml`, which publishes the repository root to GitHub
Pages. Pushes to other branches run the workflow but skip the deploy job. The
live URL is printed on the workflow run summary (and under **Settings → Pages**).

Pages is enabled on this repo with **Settings → Pages → Build and deployment →
Source: *GitHub Actions***. If Pages is ever turned off, the *Configure Pages*
step fails with `Get Pages site failed … Not Found`; a workflow's `GITHUB_TOKEN`
is not allowed to re-enable it, so that switch has to be set by hand.

You can also trigger a deploy by hand from the **Actions** tab
(*Deploy site to GitHub Pages* → *Run workflow*).

## Custom domain on GitHub Pages (optional)

The live site is served from cPanel at wow-athena.com, so this is only needed
if you ever move hosting to GitHub Pages.

1. Add a `CNAME` file at the repo root containing just `wowathena.com`.
2. At the DNS host, point the apex `A` records at GitHub Pages
   (`185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`)
   and `www` at a `CNAME` of `<owner>.github.io`.
3. In **Settings → Pages**, set the custom domain and tick *Enforce HTTPS*.

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

- The page currently carries `<meta name="robots" content="noindex, nofollow">`.
  Remove those two meta tags when the site should be indexed by search engines.
- Course prices, the "4.9 · 1,200+ reviews" trust badge, and the testimonials
  are placeholder copy — confirm them before the site goes public.
- Enrollment buttons link to the `#enroll` section; wire them to the real
  registration/Stripe flow when it exists.
