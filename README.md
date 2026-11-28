# BPMData.github.io

GitHub Pages site: https://bpmdata.github.io/

The home page for the classroom apps:

| App | Where it lives |
|---|---|
| AllAboard | https://allaboard-606573080592.us-east1.run.app/ (shortlink: https://bpmdata.github.io/allaboard/) ([repo](https://github.com/BPMData/AllAboard)) |
| OverBoard | https://bpmdata.github.io/OverBoard/ ([repo](https://github.com/BPMData/OverBoard)) |
| OverHeard | https://overheard-606573080592.us-east1.run.app/ (shortlink: https://bpmdata.github.io/overheard/) ([repo](https://github.com/BPMData/OverHeard)) |
| AllHail | https://allhail-606573080592.us-east1.run.app/ (shortlink: https://bpmdata.github.io/allhail/) ([repo](https://github.com/BPMData/AllHail)) |

Also here:

- `privacy.html` and `terms.html`: the privacy policy and terms of service for all the apps. Google's OAuth
  consent screen links to them, so keep these URLs stable.
- `404.html`: copied from OverHeard's `deploy/github-pages-404.html`. GitHub Pages serves it for any path with no
  file, so short links like https://bpmdata.github.io/murphy-p3 (3-40 letters, numbers or hyphens) forward to that
  OverHeard room; anything else shows "Page not found". If you add a new top-level page or Pages project site here,
  also add its name to `RESERVED_ROOM_CODES` in OverHeard's `src/rooms/protocol.ts`.
- `icons/`: app icons, copied from `branding/exports/` (or `public/icons/` for AllHail) in the app repos. To change an icon, edit
  the icon generator script there, rebuild, and copy the new files here.

Plain HTML and CSS; no build step. `.nojekyll` turns off GitHub's Jekyll processing.

## Hub checks

GitHub Actions checks pull requests and pushes to `main`. It opens a local copy in Chromium, checks
the homepage, theme toggle, policy pages, and local links and assets, and exercises app shortcuts
and an OverHeard room redirect. The checks use stub pages for the linked services.

To run the checks locally with Node.js 22 and Python 3:

```sh
cd .github/hub-checks
npm ci
npx playwright install --only-shell chromium
npm test
```
