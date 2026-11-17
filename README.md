# BPMData.github.io

GitHub Pages site: https://bpmdata.github.io/

The home page for the classroom apps:

| App | Where it lives |
|---|---|
| AllAboard | https://allaboard-606573080592.us-east1.run.app/ (shortlink: https://bpmdata.github.io/allaboard/) ([repo](https://github.com/BPMData/AllAboard)) |
| OverBoard | https://bpmdata.github.io/OverBoard/ ([repo](https://github.com/BPMData/OverBoard)) |
| OverHeard | https://over-heard-606573080592.us-east1.run.app/ (shortlink: https://bpmdata.github.io/overheard/) ([repo](https://github.com/BPMData/OverHeard)) |
| AllHail | https://allhail.ai.studio ([repo](https://github.com/BPMData/AllHail)) |

Also here:

- `privacy.html` and `terms.html`: the privacy policy and terms of service for all the apps. Google's OAuth
  consent screen links to them, so keep these URLs stable.
- `icons/`: app icons, copied from `branding/exports/` (or `public/icons/` for AllHail) in the app repos. To change an icon, edit
  the icon generator script there, rebuild, and copy the new files here.

Plain HTML and CSS; no build step. `.nojekyll` turns off GitHub's Jekyll processing.
