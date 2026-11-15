# BPMData.github.io

GitHub Pages site: https://bpmdata.github.io/

The home page for the classroom apps:

| App | Where it lives |
|---|---|
| AllAboard | https://allaboard.ai.studio |
| OverBoard | https://bpmdata.github.io/OverBoard/ ([repo](https://github.com/BPMData/OverBoard)) |
| BibleViz | https://bpmdata.github.io/BibleViz/ ([repo](https://github.com/BPMData/BibleViz)) |
| OverHeard | https://over-heard.ai.studio |

Also here:

- `privacy.html` and `terms.html`: the privacy policy and terms of service for all the apps. Google's OAuth
  consent screen links to them, so keep these URLs stable.
- `icons/`: app icons, copied from `branding/exports/` in the app repos. To change an icon, edit
  `branding/generate-icons.mjs` there, rebuild, and copy the new files here.

Plain HTML and CSS; no build step. `.nojekyll` turns off GitHub's Jekyll processing.
