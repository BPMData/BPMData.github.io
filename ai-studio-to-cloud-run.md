# Moving your Google AI Studio app to GitHub (and deploying it yourself)

You built an app in Google AI Studio and clicked **Deploy**. It's live on Google Cloud Run. Now you want:

- your code on GitHub, where you (or Claude Code, Codex, Gemini CLI or Cursor) can work on it;
- every change you push to GitHub to go live automatically, with no AI Studio "Publish" button;
- tests that run before each deploy, so a broken change never reaches your users.

This guide does that. It keeps your existing app address (`https://<your-app>-<numbers>.<region>.run.app`) and any API keys you've already set.

> **The short version:** you do the clicking in Google Cloud and GitHub (Part 1, about 20 minutes). Then hand this file to your AI coding agent and let it do the code part (Part 2). Then you merge one pull request and watch it go live (Part 3).

It's based on moving three real AI Studio apps. Every problem in the troubleshooting table at the end actually happened.

---

## Before you start

You need:

- **A Google Cloud project with billing turned on.** If AI Studio already deployed your app, you have one. Cloud Run has a free monthly allowance that small apps usually stay inside, but Google requires a billing account anyway.
- **A GitHub account.**
- **Your app's code in a GitHub repository** (Part 1, step 1).
- Ideally, **an AI coding agent** that can read your repo and run commands, such as Claude Code, Codex, Gemini CLI or Cursor. You can do Part 2 by hand, but it's the fiddly part.

### Words you'll see

| Word | What it means here |
|---|---|
| **Cloud Run** | The Google service that actually runs your app. AI Studio's Deploy button put it there. |
| **Service** | Your app's name inside Cloud Run, for example `my-cool-app`. |
| **Project ID** | Your Google Cloud project's name, for example `my-project-123456`. Different from the display name. |
| **Region** | Where your app runs, for example `us-central1` or `us-east1`. |
| **Service account** | A robot Google account that GitHub uses to deploy for you. |
| **GitHub Actions** | GitHub's built-in robot that runs steps (test, build, deploy) whenever you push code. |
| **Buildpacks** | Google's tool that turns your code into a runnable app without you writing a "Dockerfile". |
| **Workflow** | A `.yml` file in `.github/workflows/` that tells GitHub Actions what to do. |

---

# Part 1: Clicking around (you do this; about 20 minutes)

An AI agent shouldn't do these steps for you. They involve creating credentials and granting permissions, and your agent shouldn't ever see the key you create.

## Step 1. Get your code onto GitHub

In AI Studio, open your app in **Build** mode and use the **GitHub** icon in the top bar to create a new repository (or link an existing one). The first time, you'll be asked to let AI Studio access your GitHub account. You can manage the link later under **Settings → GitHub** in AI Studio. If you can't find the button, download the project as a ZIP, create an empty repository on github.com, and upload the files.

Good to know:
- AI Studio **doesn't** copy your API keys to GitHub. That's on purpose. They stay on the Cloud Run service, which is where we want them.
- AI Studio usually doesn't save a `package-lock.json` file, and that's fine; the workflow below handles it.
- AI Studio can keep syncing to GitHub after this. Once the move is done, every AI Studio commit to `main` will deploy automatically.

## Step 2. Write down four facts

Open <https://console.cloud.google.com/run> (choose the right project at the top of the page) and find your app in the list.

| Fact | Where to find it | Write it here |
|---|---|---|
| **Project ID** | Click the project picker at the top. Use the **ID** column, not the name. | |
| **Service name** | The **Name** column in the Cloud Run list. | |
| **Region** | The **Region** column in the Cloud Run list. | |
| **App URL** | Click the service; the URL is at the top. | |

Also click the service, then **Edit & deploy new revision → Variables & Secrets**, and note the **names** (not the values) of any keys there, such as `GEMINI_API_KEY`. You'll check that they're still there at the end.

## Step 3. Turn on the Google APIs that deploying needs

Open this link (replace `YOUR_PROJECT_ID`), check the project, and click **Enable**:

```
https://console.cloud.google.com/flows/enableapi?apiid=run.googleapis.com,cloudbuild.googleapis.com,artifactregistry.googleapis.com,cloudresourcemanager.googleapis.com,iam.googleapis.com&project=YOUR_PROJECT_ID
```

## Step 4. Create the robot account (service account)

1. Go to **IAM & Admin → Service Accounts**: <https://console.cloud.google.com/iam-admin/serviceaccounts>
2. Click **+ Create service account**.
3. Name it `github-deployer`. Click **Create and continue**.
4. Under **Grant this service account access to project**, add each of these roles. Use the search box and click **+ Add another role** between them.
   - **Cloud Run Admin**
   - **Service Account User**
   - **Cloud Build Editor**
   - **Artifact Registry Administrator**
   - **Storage Admin**
   - **Service Usage Consumer**
   - **Viewer**
5. Click **Done**.

> Why so many roles? Deploying from source uploads your code (Storage), builds it (Cloud Build), stores the result (Artifact Registry), and runs it (Cloud Run). If you're comfortable with Google Cloud, you can narrow these down later.

**One more permission, for the builder.** Google builds your app as a *different* robot account: the "Compute Engine default service account". Give that one a role too:

1. Go to **IAM & Admin → IAM**: <https://console.cloud.google.com/iam-admin/iam>
2. Find the account ending in `-compute@developer.gserviceaccount.com`. (Tick **Include Google-provided role grants** at the top right if you don't see it.)
3. Click the pencil next to it, then **+ Add another role → Cloud Run Builder → Save**. If it already has **Cloud Run Builder** or **Editor**, skip this.

It can take a couple of minutes to take effect.

## Step 5. Make a key and give it to GitHub

1. On the Service Accounts list, click `github-deployer`.
2. Open the **Keys** tab and choose **Add key → Create new key → JSON → Create**. A `.json` file downloads.
3. In your GitHub repository, go to **Settings → Secrets and variables → Actions → New repository secret**.
4. Name: `GCP_SA_KEY`. Value: open the downloaded `.json` file in a text editor, copy **everything**, and paste it in. Click **Add secret**.
5. Store the `.json` file somewhere safe **outside** your code folder, or delete it. GitHub has it now.

> ⚠️ **Treat that key like a password.** Never commit it, never paste it into an AI chat, never put it in an issue or a screenshot. If it ever leaks, go back to the **Keys** tab, delete it, and make a new one.

> **"Key creation is disabled" error?** Work and school Google accounts often block downloadable keys. Personal accounts usually don't. If you're blocked, ask your agent to set up **Workload Identity Federation** instead; it's keyless. See the [`google-github-actions/auth` README](https://github.com/google-github-actions/auth#workload-identity-federation-through-a-service-account). The rest of this guide stays the same.

## Step 6. Hand over to your agent

Open your repository in your AI coding agent and paste:

> Read `ai-studio-to-cloud-run.md` (attached, or at https://bpmdata.github.io/ai-studio-to-cloud-run.md) and do **Part 2** for this repo. My Cloud Run details are: project ID `___`, region `___`, service `___`, app URL `___`. The GitHub secret `GCP_SA_KEY` is already set. Work on a new branch, run every check locally, open a pull request, and **don't merge it**. Never print or ask me for any key or secret value.

---

# Part 2: The code part (your agent can do this)

> **If you're an AI agent, read this first.**
> - Never print, log, echo or commit secret values. That includes container env vars from `gcloud run services describe`, `.env` files and key files. Refer to secrets by name only.
> - Don't ask the user for the contents of `GCP_SA_KEY` or any API key. You don't need them.
> - Work on a branch. Open a pull request. **Don't merge it**; merging deploys to production.
> - Don't run `gcloud run deploy` yourself. GitHub Actions does that after the merge.
> - Before changing anything, make sure the local folder matches GitHub: `git fetch && git status -sb`. AI Studio pushes to GitHub directly, so local copies are often behind. Stash local changes rather than discarding them.

## Step 7. Work out what kind of app this is

Look at the repository and answer these. They decide the rest.

| Question | How to tell | Why it matters |
|---|---|---|
| **A. Does it have its own server?** | A `server.ts`/`server.js` (often Express) and a `"start"` script that runs it | Buildpacks run `npm start`. If there's no server, see 7a. |
| **B. Which port does the server listen on?** | Look for `listen(` and `process.env.PORT` | The deploy step needs it. Prefer `process.env.PORT \|\| <number>`. |
| **C. Does the browser code use an API key?** | `process.env.GEMINI_API_KEY` / `API_KEY` in front-end files, or `define:` in `vite.config.*` | See 7b. This is the biggest trap. |
| **D. Does the server keep anything in memory or on disk?** | rate limits, sessions, rooms, websockets, files written to local disk | If yes, keep `MAX_INSTANCES: "1"`. |
| **E. Which Node version?** | `engines` in `package.json`, or any existing CI workflow | Set `NODE_VERSION`. `node server.ts` (no build step) needs Node 22.18 or later. |
| **F. Which check scripts exist?** | `scripts` in `package.json` | The workflow runs `typecheck`, `lint`, `build`, `test` and `smoke` if they exist. |
| **G. Does it use Google sign-in or the Drive Picker?** | `google.accounts`, `gapi`, `picker` | See Part 3, step 13. |

### 7a. No server of its own (front-end only)

Buildpacks need something to run. Add a small Express server (`server.js`) that serves the built `dist/` folder and listens on `process.env.PORT`. Add `"start": "node server.js"`, and put `express` in `dependencies`, not `devDependencies`.

### 7b. The API key trap

AI Studio quietly provides your Gemini key at runtime, often through a proxy, so the key never reaches the browser. Many AI Studio templates also have this in `vite.config.ts`:

```ts
define: { 'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY) }
```

Once you leave AI Studio, that line either **builds an empty key into your app**, which breaks it, or **builds the real key into public JavaScript** for anyone to copy. Neither is OK.

**The fix:** move every call to Gemini (or any paid API) into the server, as an endpoint like `POST /api/generate`. The server reads `process.env.GEMINI_API_KEY`, which Cloud Run already provides because the key is set on the service. The browser calls your endpoint, never Gemini directly. Remove the `define:` line. If the app has no server yet, do 7a first.

## Step 8. Update `package.json`

1. Add `"gcp-build": "npm run build"` to `scripts`, if a `build` script exists. Buildpacks run this to build your app before starting it. Don't change the other scripts.
2. Make sure `"start"` runs the server, for example `"node server.js"` or `"node server.ts"`.
3. Pin Node to one major version, matching `NODE_VERSION` in the workflow: `"engines": { "node": "22.x" }`. Without a pin, Buildpacks may choose a brand-new Node version.
4. Whatever `npm start` needs at runtime must be in `dependencies`, not `devDependencies`. Common examples are `express`, `dotenv`, and `tsx` if `start` uses it.

**Peer-dependency check:** copy just `package.json` (plus any folder that `overrides` points at with `file:`) into an empty temporary folder, and run:

```bash
npm install --dry-run --no-audit --no-fund
```

Only if that shows `ERESOLVE` or peer-dependency errors, add a file called `.npmrc` containing `legacy-peer-deps=true`.

## Step 9. Make sure the server knows it's in production

AI Studio's deploys sometimes don't set `NODE_ENV`. Cloud Run always sets `K_SERVICE`, so use that as a backup:

```js
const isProduction = process.env.NODE_ENV
  ? process.env.NODE_ENV === 'production'
  : Boolean(process.env.K_SERVICE);
```

## Step 10. Add `.gcloudignore`

This file lists what **not** to upload when building. Create `.gcloudignore` in the repository root:

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

# Uncomment only if package-lock.json is NOT committed to the repo:
# package-lock.json

# Add any private or bulky folders: personal photos, test data, research notes...
```

> ⚠️ **Never ignore anything the build needs.** If `overrides` in `package.json` points at a `file:./something` folder, keep that folder. If `npm run build` runs a script in `scripts/`, keep `scripts/`. When in doubt, don't ignore it.

## Step 11. Add `.github/workflows/deploy.yml`

Copy this file and change **only the `env:` block**. The rest is built to handle the strange leftovers AI Studio leaves on a Cloud Run service.

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
  SERVICE: my-app                 # Cloud Run service name (step 2)
  PROJECT: my-project-123456      # Project ID (step 2)
  REGION: us-central1             # Region (step 2)
  APP_PORT: "8080"                # Port your server listens on (step 7, question B)
  MAX_INSTANCES: "1"              # Keep "1" if the server keeps anything in memory (step 7, question D)
  NODE_VERSION: "22"              # Match "engines" in package.json

jobs:
  deploy:
    name: Check and deploy
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-node@v6
        with:
          node-version: ${{ env.NODE_VERSION }}

      # AI Studio repos often have no lock file. Use it when there is one.
      - name: Install dependencies
        run: |
          if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

      # Each check runs only if the script exists in package.json.
      - run: npm run --if-present typecheck
      - run: npm run --if-present lint
      - run: npm run --if-present build
      - run: npm test --if-present
      - name: Check the server loads under plain Node
        run: |
          if [ -f server.ts ]; then node -e "import('./server.ts').then(() => console.log('OK'))"; fi
      - run: npm run --if-present smoke

      - uses: google-github-actions/auth@v3
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - uses: google-github-actions/setup-gcloud@v2

      # One-time cleanup of AI Studio leftovers. Skipped once the service has the
      # managed-by=github-actions label, or if the service doesn't exist yet.
      # Never prints container env vars, because they hold API keys.
      - name: Clear AI Studio leftovers before the first GitHub deploy
        id: migrate
        run: |
          if ! gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format export > /tmp/service.yaml 2>/dev/null; then
            echo "No existing service called $SERVICE in $REGION; nothing to clean up."
            exit 0
          fi
          if [ "$(yq '.metadata.labels["managed-by"] // ""' /tmp/service.yaml)" != "github-actions" ]; then
            echo "Inspecting pre-migration annotations and container entrypoints:"
            yq '.spec.template.metadata.annotations' /tmp/service.yaml
            yq '.spec.template.spec.containers[].name' /tmp/service.yaml
            yq '.spec.template.spec.containers[].image' /tmp/service.yaml
            yq '.spec.template.spec.containers[].command' /tmp/service.yaml
            yq '.spec.template.spec.containers[].args' /tmp/service.yaml

            # AI Studio sometimes deploys two containers (nginx + your app). Keep only the app.
            ORIG_CONTAINER_COUNT="$(yq '.spec.template.spec.containers | length' /tmp/service.yaml)"
            if [ "$ORIG_CONTAINER_COUNT" -gt 1 ]; then
              echo "Collapsing $ORIG_CONTAINER_COUNT-container AI Studio service to a single app container"
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
              # AI Studio source deploys can leave a placeholder image. Build a real one first.
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
                  echo "Replacing placeholder image with a Buildpacks image: $IMAGE"
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

      # Deploy with gcloud directly. The deploy-cloudrun action mangles empty --command/--args.
      # --command "" / --args "" clear AI Studio's leftover startup command so `npm start` runs.
      # There's deliberately no --set-env-vars or --clear-env-vars: your existing API keys stay put.
      # For websockets or live "rooms", also add: --session-affinity
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
            --max-instances "$MAX_INSTANCES" \
            --command "" \
            --args "" \
            --update-labels "managed-by=github-actions,commit-sha=${GITHUB_SHA}" \
            --quiet
```

If the repository already has a CI workflow that runs the same checks, leave it alone. This file only runs on `main`.

## Step 12. Check everything locally, then open a pull request

Run whichever of these exist, and make sure all of them pass:

```bash
npm install && npm run gcp-build && npm test && npm start
```

With `npm start` running, open the app in a browser at `http://localhost:<APP_PORT>`, then stop it. If `gcloud` is installed, list what would be uploaded, and make sure there's no `.env`, key file, `node_modules` or private folder in it:

```bash
gcloud meta list-files-for-upload .
```

Commit only the files from this part, push the branch, and open a pull request. Explain what each file does in plain words. **Don't merge it.**

---

# Part 3: Go live (you do this; about 10 minutes)

## Step 13. Before merging: Google sign-in (only if the app uses it)

If your app uses **Sign in with Google** or the **Google Drive Picker**, open **APIs & Services → Credentials** (<https://console.cloud.google.com/apis/credentials>):

- Click your **OAuth 2.0 Client ID** and add your app URL (from step 2, without a trailing slash) under **Authorized JavaScript origins**.
- If an **API key** has **Website restrictions**, add the URL there too.

Otherwise sign-in fails with an `origin_mismatch` error.

## Step 14. Merge and watch

1. Merge the pull request.
2. On GitHub, open the **Actions** tab and click the running **Deploy to Cloud Run**. The first run takes longer because it does the one-time cleanup and may build an image first. Later runs take a few minutes.
3. When it shows a green tick, open your app URL and try the main features.
4. In the Cloud Run console, click your service and check that:
   - **Labels** include `managed-by: github-actions`;
   - **Variables & Secrets** still lists your keys (names from step 2);
   - the latest revision is serving 100% of traffic.

## Step 15. Stop using AI Studio's Deploy / Publish button

From now on, **pushing to `main` on GitHub is how you deploy**. If you publish from AI Studio again, it overwrites the GitHub-built version and puts the leftovers back. (If that ever happens, remove the `managed-by` label in the Cloud Run console and push any change; the cleanup step runs again.)

You can keep prototyping in AI Studio if it commits to GitHub. Every commit to `main` deploys.

## Optional: a nicer link

The `run.app` address is long. Options:

- **A free redirect on GitHub Pages:** create a repository named `<your-username>.github.io`, and add a folder named after your app (for example `myapp/`) containing this `index.html`. Then `https://<your-username>.github.io/myapp/` opens your app.

  ```html
  <!doctype html>
  <meta charset="utf-8">
  <title>Opening My App…</title>
  <script>location.replace('https://YOUR-APP-URL.run.app/' + location.search + location.hash);</script>
  <meta http-equiv="refresh" content="0; url=https://YOUR-APP-URL.run.app/">
  <a href="https://YOUR-APP-URL.run.app/">Open My App →</a>
  ```

- **Your own domain:** see Cloud Run's **Manage custom domains** page.

---

## When something goes wrong

Open the failed run in GitHub's **Actions** tab and read the red step. Then find it here:

| What you see | Why | Fix |
|---|---|---|
| A check step fails (typecheck, test, build) | Your code has a real problem, and the deploy was stopped on purpose | Fix the code and push again. Your live app hasn't changed. |
| `Permission denied` / `PERMISSION_DENIED` during auth or deploy | The robot account is missing a role, or the secret is wrong | Re-check the roles in step 4. Re-create the key and secret in step 5. |
| Build fails mentioning the **Compute Engine default service account** | Google builds as that account, and it lacks rights | Do the "one more permission" part of step 4. Wait two minutes, then re-run. |
| `API ... has not been used in project ... or it is disabled` | An API isn't turned on | Redo step 3, wait two minutes, then re-run the workflow |
| "Container failed to start and listen on the port" | The port is wrong, or AI Studio's old startup command is still there | Make `APP_PORT` match the server. Make sure the server uses `process.env.PORT`. Keep `--command "" --args ""`. |
| `npm ERR! ERESOLVE` in the build log | Strict peer dependencies | Add `.npmrc` with `legacy-peer-deps=true` (step 8) |
| Build can't find a file, or `file:./...` | `.gcloudignore` left out a folder the build needs | Remove that line from `.gcloudignore` |
| App loads but AI features say "API key missing" or 401 | The API key trap: the key was built into the front end | Do step 7b: move API calls to the server |
| API keys gone from the service after deploy | Someone added `--set-env-vars` or `--clear-env-vars` | Re-add the keys in the console. Never use those flags in this workflow. |
| `spec.template.spec.containers[0].env: ... PORT is reserved` | AI Studio set a variable that Cloud Run reserves | The cleanup step removes these. Make sure that step is unchanged. |
| `--allow-unauthenticated` fails with a policy error | A work or school account blocks public apps | Ask your Google Workspace admin; this can't be worked around from your side |
| Rate limits, logins or "rooms" act strangely | Several copies of the app, each with its own memory | Keep `MAX_INSTANCES: "1"` |
| Local build fails, but GitHub's passes | Your local copy has stale `node_modules` or old generated files | Delete `node_modules` (and `package-lock.json` if git ignores it), then run `npm install` |

## Going back to a version that worked

Cloud Run keeps every version. In the console: click your service, open **Revisions**, choose the last good one, then **Manage traffic → 100%**. Then fix the problem in code and push. The next deploy moves traffic to the new version.

## What this costs

Cloud Run, Cloud Build and Artifact Registry all have free monthly allowances. A small personal app often costs nothing or a few cents a month. Two things add up over time:

- **Old app images** in Artifact Registry. Add a **cleanup policy** in the Artifact Registry console to keep only the last few.
- **Traffic**, if your app gets popular.

To be safe, set a **budget alert** under **Billing → Budgets & alerts**.
