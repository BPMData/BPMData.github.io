# Moving a Google AI Studio app to GitHub → Cloud Run

How to stop publishing an app from Google AI Studio and deploy it from GitHub instead. After the move, every push to `main` checks the app and deploys it to Cloud Run. Google Cloud Buildpacks builds the container, so you don't write a Dockerfile.

This worked first time for **OverHeard**, **AllAboard** and **AllHail** (November 2026). The AllHail files are the most complete example:

- `BPMData/AllHail`: `.github/workflows/deploy.yml`, `.gcloudignore`, `package.json` (PR #4)
- `BPMData/BPMData.github.io`: `allhail/index.html` (PR #8)

---

## 0. Things already set up (one time only, don't redo)

For project `loyal-rookery-403218` (project number `606573080592`), region `us-east1`:

- [x] The GitHub secret `GCP_SA_KEY` holds a service-account JSON key. Each repo needs this secret. If it's missing from a new repo, add it under **Settings → Secrets and variables → Actions**. The key file is in `~/Documents/Github/Secrets/`; never paste its contents into chat, code or an issue.
- [x] These APIs are turned on: `run.googleapis.com`, `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com`, `cloudresourcemanager.googleapis.com`.
- [x] The service account has enough roles to build, push and deploy. The usual set is Cloud Run Admin, Service Account User, Cloud Build Editor, Artifact Registry Writer, Storage Admin and Service Usage Consumer.

If you ever use a **new Google Cloud project**, redo this section there first.

---

## 1. Collect the facts about the app

Look these up before you change anything:

| What | Where to find it | AllHail's value |
|---|---|---|
| Cloud Run service name | Cloud Run console, or the `*.run.app` URL | `allhail` |
| App URL | Cloud Run console | `https://allhail-606573080592.us-east1.run.app/` |
| Port the server listens on | `server.ts`: look for `process.env.PORT \|\| 3000` | `3000` |
| Node version | `.github/workflows/ci.yml` and `engines` in `package.json` | `24` |
| Check scripts | `scripts` in `package.json` | `typecheck`, `build`, `test`, `smoke` |
| Does the app keep state in memory or on local disk? | the server code (rate limits, sessions, rooms, `DATA_DIR`) | yes, an in-memory rate limit |
| Secrets the live app uses | Cloud Run console → service → **Variables & Secrets** (look; never print) | `OPENROUTER_API_KEY` |
| Google sign-in or Drive Picker? | look for `gapi`, `google.accounts`, `picker` | no |

Also check that the server decides "production" by `K_SERVICE` as well as `NODE_ENV`, because AI Studio sometimes drops `NODE_ENV`:

```ts
export function isProduction(env = process.env) {
  if (env.NODE_ENV) return env.NODE_ENV === 'production';
  return Boolean(env.K_SERVICE);
}
```

---

## 2. Get your local folder level with GitHub

AI Studio pushes commits straight to GitHub, so your local copy is often behind. Fix that first:

```bash
git fetch origin
```

```bash
git status -sb
```

If it says `behind N`, look at any uncommitted changes first. Then stash them (don't delete them) and fast-forward:

```bash
git stash push -m "local edits before syncing" -- <paths>
```

```bash
git merge --ff-only origin/main
```

If the build or tests then fail with odd "missing module" or "duplicate runtime" errors, the gitignored leftovers are out of date. Delete them and reinstall the way CI does:

```bash
rm -rf node_modules package-lock.json dist public/ort public/piper
```

```bash
npm install --no-audit --no-fund
```

(Only delete `package-lock.json` if the repo gitignores it. AI Studio repos do.)

Then run every check and confirm it passes before you add anything:

```bash
npm run typecheck && npm run build && npm test && npm run smoke
```

---

## 3. Make a branch and change `package.json`

```bash
git switch -c deploy-cloud-run
```

In `package.json`:

1. Add `"gcp-build": "npm run build"` to `scripts`. Buildpacks run this to build the app, keeping devDependencies installed until it finishes. Leave the other scripts alone.
2. Pin Node to the version CI uses, for example `"engines": { "node": "24.x" }`. A range like `>=22` lets Buildpacks choose the newest major version, which could break the app.

Keep `"start": "node server.ts"`. Buildpacks run `npm start`.

### Do you need `.npmrc`?

Do a clean dry run in an empty folder that holds only a copy of `package.json` (plus `stubs/` if `overrides` points at it):

```bash
npm install --dry-run --no-audit --no-fund
```

Only if it shows `ERESOLVE` or peer-dependency errors, add an `.npmrc` containing:

```
legacy-peer-deps=true
```

(OverHeard needed it. AllAboard and AllHail didn't.)

---

## 4. Add `.gcloudignore`

This lists the files that **don't** get uploaded for the Cloud Run build. Start from this and add each app's own private or bulky folders:

```gitignore
.git/
.github/
node_modules/
dist/
build/
coverage/
playwright-report/
test-results/
.DS_Store
*.log
.env*
!.env.example
bun.lock
package-lock.json

# Generated during the build (only if the app does this)
# public/ort/
# public/piper/

# Personal photos, test results, research notes: anything private
# sample_images/
# research_outputs/
```

⚠️ **Never ignore anything the build needs.** Before you finish, check:
- Does `overrides` in `package.json` point at a `file:./something` path? Then keep that folder (AllHail's `stubs/`).
- Does `npm run build` run a script, like `node scripts/check-ort.mjs`? Then keep `scripts/`.
- Leave out `package-lock.json` only if the repo gitignores it.

---

## 5. Add `.github/workflows/deploy.yml`

Copy this file and change **only** the four lines under `env:`. Everything else is the tested AllHail workflow; the service name, project, region and port are just read from `env:` here instead of typed into each command.

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: deploy-cloudrun-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

env:
  SERVICE: myapp                    # Cloud Run service name
  PROJECT: loyal-rookery-403218
  REGION: us-east1
  APP_PORT: "3000"                  # port the server listens on

jobs:
  deploy:
    name: Verify and deploy
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-node@v6
        with:
          node-version: 24

      # AI Studio repos have no package-lock.json, so use npm install (not npm ci).
      - run: npm install --no-audit --no-fund
      - run: npm run typecheck          # match the app's real script names
      - run: npm run build
      - run: npm test
      - name: Native Node TypeScript check
        run: node -e "import('./server.ts').then(() => console.log('OK'))"
      - run: npm run smoke              # or an inline curl boot check (see AllAboard)

      - uses: google-github-actions/auth@v3
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      # One-time AI Studio cleanup. Skipped once the service has the managed-by label.
      # Never print container env vars: they hold API keys.
      - name: Clear AI Studio source annotations before first GitHub deploy
        id: migrate
        run: |
          gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format export > /tmp/service.yaml
          if [ "$(yq '.metadata.labels["managed-by"] // ""' /tmp/service.yaml)" != "github-actions" ]; then
            echo "Inspecting pre-migration annotations and container entrypoints:"
            yq '.spec.template.metadata.annotations' /tmp/service.yaml
            yq '.spec.template.spec.containers[].name' /tmp/service.yaml
            yq '.spec.template.spec.containers[].image' /tmp/service.yaml
            yq '.spec.template.spec.containers[].command' /tmp/service.yaml
            yq '.spec.template.spec.containers[].args' /tmp/service.yaml

            ORIG_CONTAINER_COUNT="$(yq '.spec.template.spec.containers | length' /tmp/service.yaml)"
            if [ "$ORIG_CONTAINER_COUNT" -gt 1 ]; then
              echo "Collapsing $ORIG_CONTAINER_COUNT-container AI Studio service to single app container"
              yq -i '.spec.template.spec.containers = [(.spec.template.spec.containers[] | select(.name != "nginx-container" and .name != "nginx"))]' /tmp/service.yaml
              if [ "$(yq '.spec.template.spec.containers | length' /tmp/service.yaml)" -gt 1 ]; then
                yq -i '.spec.template.spec.containers = [.spec.template.spec.containers[0]]' /tmp/service.yaml
              fi
            fi

            CURRENT_IMAGE="$(yq '.spec.template.spec.containers[0].image // ""' /tmp/service.yaml)"
            HAS_SOURCES=false
            if yq -e '.spec.template.metadata.annotations["run.googleapis.com/sources"] != null or .spec.template.metadata.annotations["run.googleapis.com/base-images"] != null' /tmp/service.yaml >/dev/null 2>&1; then
              HAS_SOURCES=true
            fi

            if [ "$CURRENT_IMAGE" = "scratch" ] || [ -z "$CURRENT_IMAGE" ] || [ "$HAS_SOURCES" = "true" ] || [ "$ORIG_CONTAINER_COUNT" -gt 1 ]; then
              if [ "$CURRENT_IMAGE" = "scratch" ] || [ -z "$CURRENT_IMAGE" ]; then
                REPO_NAME="$(gcloud artifacts repositories list --project "$PROJECT" --location "$REGION" --filter='format=DOCKER' --format='value(name)' | grep '/cloud-run-source-deploy$' | head -n1 || true)"
                if [ -n "$REPO_NAME" ]; then
                  IMAGE="$REGION-docker.pkg.dev/$PROJECT/cloud-run-source-deploy/$SERVICE:${{ github.sha }}"
                else
                  IMAGE="gcr.io/$PROJECT/$SERVICE:${{ github.sha }}"
                fi
                if gcloud container images describe "$IMAGE" --project "$PROJECT" >/dev/null 2>&1; then
                  echo "Reusing existing Buildpacks image: $IMAGE"
                else
                  echo "Replacing placeholder image with Buildpacks image: $IMAGE"
                  gcloud builds submit --pack "image=$IMAGE" --project "$PROJECT" .
                fi
                yq -i ".spec.template.spec.containers[0].image = \"$IMAGE\"" /tmp/service.yaml
                echo "image=$IMAGE" >> "$GITHUB_OUTPUT"
              fi
              yq -i 'del(.spec.template.metadata.annotations["run.googleapis.com/sources"], .spec.template.metadata.annotations["run.googleapis.com/base-images"], .spec.template.metadata.annotations["run.googleapis.com/container-dependencies"], .spec.template.metadata.name, .spec.template.spec.runtimeClassName, .spec.template.spec.volumes, .spec.template.spec.containers[0].command, .spec.template.spec.containers[0].args, .spec.template.spec.containers[0].workingDir, .spec.template.spec.containers[0].dependsOn, .spec.template.spec.containers[0].volumeMounts, .spec.template.spec.containers[0].startupProbe, .spec.template.spec.containers[0].livenessProbe)' /tmp/service.yaml
              # Cloud Run sets these itself and rejects a service that tries to.
              if yq -e '.spec.template.spec.containers[0].env != null' /tmp/service.yaml >/dev/null 2>&1; then
                yq -i '.spec.template.spec.containers[0].env |= map(select(.name != "PORT" and .name != "K_SERVICE" and .name != "K_REVISION" and .name != "K_CONFIGURATION"))' /tmp/service.yaml
                if [ "$(yq '.spec.template.spec.containers[0].env | length' /tmp/service.yaml)" = "0" ]; then
                  yq -i 'del(.spec.template.spec.containers[0].env)' /tmp/service.yaml
                fi
              fi
              yq -i ".spec.template.spec.containers[0].name = \"$SERVICE\"" /tmp/service.yaml
              yq -i ".spec.template.spec.containers[0].ports = [{\"containerPort\": $APP_PORT}]" /tmp/service.yaml
              gcloud run services replace /tmp/service.yaml --region "$REGION" --project "$PROJECT"
            fi
          fi

      # Call gcloud directly. google-github-actions/deploy-cloudrun turns `--command=` into a
      # bare `--command`, which gcloud rejects. --command "" / --args "" clear AI Studio's
      # leftover entrypoint so the Buildpacks launcher runs `npm start`.
      # No --set-env-vars / --clear-env-vars, so the live API keys stay as they are.
      - name: Deploy to Cloud Run
        env:
          MIGRATED_IMAGE: ${{ steps.migrate.outputs.image }}
        run: |
          if [ -n "$MIGRATED_IMAGE" ]; then
            SOURCE_ARGS=(--image "$MIGRATED_IMAGE")
          else
            SOURCE_ARGS=(--source .)
          fi
          gcloud run deploy "$SERVICE" \
            "${SOURCE_ARGS[@]}" \
            --region "$REGION" \
            --project "$PROJECT" \
            --allow-unauthenticated \
            --port "$APP_PORT" \
            --max-instances 1 \
            --command "" \
            --args "" \
            --update-labels "managed-by=github-actions,commit-sha=${GITHUB_SHA}" \
            --quiet
```

### Flags that depend on the app

- **`--max-instances 1`:** keep this if the server holds anything in memory or on local disk that every user must share: rate limits, rooms, sessions, a `DATA_DIR`. All three apps so far needed it. Remove it only if the server is completely stateless.
- **`--session-affinity`:** add this for WebSockets or live rooms (AllAboard has it).
- **Check steps:** use the app's real script names. OverHeard uses `npm run lint` for typecheck and `bash scripts/smoke.sh`. AllAboard does an inline `curl` boot check against `/healthz`.

---

## 6. Check locally, then open the PR

```bash
npm run gcp-build && npm test && npm run smoke
```

```bash
npx -y yaml@2.8.1 valid < .github/workflows/deploy.yml
```

If gcloud is installed, check what will be uploaded. Your `stubs/` and `scripts/` should appear; `node_modules`, photos and `.env` should not.

```bash
gcloud meta list-files-for-upload . | sort | less
```

Commit **only** the deploy files, push, and open a PR. Don't merge it until you're ready: merging starts the first deploy.

---

## 7. Merge and watch the first deploy

1. Merge the PR. Watch **Actions → Deploy to Cloud Run**.
2. The first run includes the one-time cleanup step. It may build an image with `gcloud builds submit --pack` (a few extra minutes).
3. Later pushes skip cleanup and use `--source .`.
4. Check the live app:

```bash
curl -s https://<service>-606573080592.us-east1.run.app/api/health
```

5. In the Cloud Run console, check that:
   - the service shows the label `managed-by: github-actions`;
   - the secrets and env vars (API keys) are still there;
   - the revision runs one container, not two.

**After this, stop using AI Studio's Publish button for this app.** A Publish from AI Studio would overwrite the GitHub-built revision. You can keep editing code in AI Studio if it commits to GitHub; the push to `main` deploys it.

---

## 8. Short link on bpmdata.github.io

In `~/Documents/Github/BPMData.github.io`, on a new branch from an up-to-date `main`:

1. Copy `allhail/index.html` to `<app>/index.html`. Change the name, the URL (it appears three times), the icon path and the link `id`.
2. Replace any `https://<app>.ai.studio` links in `index.html`, `privacy.html` and `README.md` with the `run.app` URL. Add `(shortlink: https://bpmdata.github.io/<app>/)` to the README row.
3. Search for leftovers:

```bash
grep -rn "ai.studio" --include="*.html" --include="*.md" .
```

4. Open a PR and merge it. The `run.app` URL already works before the deploy PR, so the order doesn't matter.

---

## 9. Google sign-in / Drive Picker (only if the app uses them)

If the app uses Google OAuth or the Drive Picker (AllAboard does; OverHeard and AllHail don't), add the new origin `https://<service>-606573080592.us-east1.run.app` to:

- **APIs & Services → Credentials → OAuth client → Authorized JavaScript origins** (and the redirect URIs, if any);
- the API key's **website restrictions**, if it has any.

Otherwise sign-in fails with `origin_mismatch`.

---

## Problems we hit, and what fixes them

| Symptom | Cause | Fix (already in the workflow) |
|---|---|---|
| Container never listens on the port; "failed to start and listen" | AI Studio left a `/bin/sh -c "npm start"` command override, which skips the Buildpacks launcher (no `node` on PATH) | `--command "" --args ""`, and delete `command`/`args`/`workingDir` in the cleanup step |
| `deploy-cloudrun` action errors on `--command` | the action's flag parser breaks empty values | call `gcloud run deploy` directly |
| Image is `scratch`, deploy fails | AI Studio source deploys use a placeholder image | build one with `gcloud builds submit --pack`, then pass `--image` |
| Two containers (`nginx-container` + app) | AI Studio's template | keep only the app container; delete `volumes`, `dependsOn`, `volumeMounts`, probes and the `container-dependencies` annotation |
| `services replace` rejects `PORT` / `K_SERVICE` env | AI Studio set reserved variables | filter them out of `env` |
| API keys vanished after deploy | `--set-env-vars` or `--clear-env-vars` replaces everything | never pass those flags |
| `ERESOLVE` peer-dependency error in the Cloud Build log | strict peers | add `.npmrc` with `legacy-peer-deps=true` |
| Build can't find `file:./stubs/...` or a build script | `.gcloudignore` left out a folder the build needs | un-ignore it |
| Local build fails with "missing module" or "duplicate runtime", but CI passes | stale gitignored `package-lock.json`, `node_modules` or generated files | delete them and reinstall (section 2) |
| Rate limit or rooms act strangely | several instances, each with its own memory | `--max-instances 1` |

## Rolling back

Cloud Run keeps old revisions. In the console, open the service → **Revisions**, choose the last good one, and choose **Manage traffic → 100%**. Or run:

```bash
gcloud run services update-traffic <service> --to-revisions <revision>=100 --region us-east1 --project loyal-rookery-403218
```

---

## A ready-made request for Claude

> Move **\<App\>** (`BPMData/<App>`) off Google AI Studio onto GitHub Actions → Cloud Run with Buildpacks, following `AISTUDIO_TO_GITHUB.md` and copying `BPMData/AllHail` PR #4. Service `<service>`, project `loyal-rookery-403218`, region `us-east1`. First bring my local folder level with GitHub without losing local changes. Then inspect the repo: confirm the port, the Node version, the check scripts and whether `--max-instances 1` is needed, and test whether `.npmrc` is needed. Open a PR (don't merge it). Then open a PR on `BPMData.github.io` adding `/<app>/` and replacing the `ai.studio` links. Tell me whether any Google OAuth origins need adding. Credentials are in `~/Documents/Github/Secrets/`; never print them.
