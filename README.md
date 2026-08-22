# Athena DUI Academy & Family Enrichment — W.O.W.

Static marketing site for Athena DUI Academy & Family Enrichment (Athens, GA).
One page, no build step: plain HTML + CSS, fonts from Google Fonts.

## Structure

```
index.html            the entire site
img/logo.svg          placeholder logo  (drop in img/logo.png to override)
img/justice.svg       placeholder hero art (drop in img/justice.png to override)
.nojekyll             serve files as-is on GitHub Pages
.github/workflows/deploy.yml   Pages deployment
```

## Deployment

Every push to the repository's **default branch** runs
`.github/workflows/deploy.yml`, which publishes the repository root to GitHub
Pages. Pushes to other branches run the workflow but skip the deploy job. The
live URL is printed on the workflow run summary (and under **Settings → Pages**).

One-time setup in the repo: **Settings → Pages → Build and deployment →
Source: GitHub Actions**. The workflow also tries to enable this automatically
on its first run.

You can also trigger a deploy by hand from the **Actions** tab
(*Deploy site to GitHub Pages* → *Run workflow*).

## Custom domain (wowathena.com)

1. Add a `CNAME` file at the repo root containing just `wowathena.com`.
2. At the DNS host, point the apex `A` records at GitHub Pages
   (`185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`)
   and `www` at a `CNAME` of `<owner>.github.io`.
3. In **Settings → Pages**, set the custom domain and tick *Enforce HTTPS*.

## Real images

`index.html` asks for `img/logo.png` and `img/justice.png` first and falls back
to the bundled SVG placeholders when those files are absent. Commit the real
PNGs at those paths and they take over with no code change.

## Notes

- The page currently carries `<meta name="robots" content="noindex, nofollow">`.
  Remove those two meta tags when the site should be indexed by search engines.
- Course prices, the "4.9 · 1,200+ reviews" trust badge, and the testimonials
  are placeholder copy — confirm them before the site goes public.
- Enrollment buttons link to the `#enroll` section; wire them to the real
  registration/Stripe flow when it exists.
