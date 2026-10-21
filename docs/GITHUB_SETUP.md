# Putting Clause on GitHub

Do the steps in order. GitHub Desktop comes first; the terminal version is at the end. App menus change their names from time to time, so wherever there's a direct link, use it.

## At a glance

| Step | Where | Time |
|---|---|---|
| 1. Check the folder | Finder | 2 min |
| 2. Make it a repository | GitHub Desktop | 2 min |
| 3. Publish it | GitHub Desktop | 1 min |
| 4. Add a description and topics | github.com | 2 min |
| 5. Check CI is green | github.com | 3 min, mostly waiting |
| 6. Pin it to your profile | github.com | 1 min |
| 7. Turn on the webpage (optional) | github.com | 2 min |
| Later | The freeze tag, the API key secret | When the build plan gets there |

## 1. Check the folder

The repo is the `clause` folder, wherever you unzipped it. In Finder, press `Cmd + Shift + .` to show hidden files, then check two things:

- There is **no `.env` file**, only `.env.example`, which has no key in it. If you made a `.env` with your API key, that's fine: `.gitignore` keeps it out. You'll confirm it in step 2.
- There's no `.cache` or `.venv` folder you want to keep private. Both are ignored too.

## 2. Make it a repository

1. Install GitHub Desktop if you don't have it: <https://desktop.github.com>. Sign in as sumitd07.
2. Choose **File → Add Local Repository…** and pick the `clause` folder.
3. Desktop says the folder isn't a Git repository and offers to **create a repository**. Click it.
4. Fill in the form. Name: `clause`. Description: `Ask what your health insurance policy covers and pays, and see the clause behind every answer.` Leave **Git ignore** and **License** as None, because the folder already has both. Click **Create Repository**.
5. The left panel lists the files in the first commit. Scroll through it once. You should see `src/`, `docs/`, `data/` and `tests/`, and no `.env`.

Desktop makes the first commit itself. If it shows the files under **Changes** instead, type the summary `Clause day 0: engine, answer form, scoring, docs` and click **Commit to main**.

## 3. Publish it

1. Click **Publish repository** at the top.
2. Name it `clause`. Untick **Keep this code private** so it's public. Click **Publish Repository**.
3. Open it in the browser: **Repository → View on GitHub**, or go to <https://github.com/sumitd07/clause>.

If you chose a different name, change `sumitd07/clause` in the CI badge at the top of `README.md` to match.

## 4. Add a description and topics

On <https://github.com/sumitd07/clause>, click the gear icon next to **About** on the right.

| Field | Value |
|---|---|
| Description | Ask what your health insurance policy covers and pays. Every answer shows the clause behind it, word for word. |
| Website | `https://sumitd07.github.io/clause/` once step 7 is done, or leave it empty |
| Topics | `llm`, `evals`, `health-insurance`, `rules-engine`, `document-ai`, `anthropic`, `india`, `consumer`, `explainability` |

## 5. Check CI is green

Open <https://github.com/sumitd07/clause/actions>. CI ("continuous integration") is GitHub running the project's checks on a fresh machine. The first run starts when you publish. It installs Clause on Python 3.11 and 3.13, runs the style checks and the 58 tests, checks that every rule quote is word for word, and checks that perfect reading scores 100%. A green tick means the repo works on a clean machine, not just on yours.

If it fails, open the failed step. The log names the file and the line. The most likely cause is a file edited after these docs were written that the formatter disagrees with. Run `make format`, then commit.

## 6. Pin it to your profile

On <https://github.com/sumitd07>, click **Customize your pins** and tick `clause`. It then shows at the top of your profile.

## 7. Turn on the webpage (optional)

The repo includes a one-page site that explains Clause, at `docs/index.html`.

1. Open <https://github.com/sumitd07/clause/settings/pages>.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Set the branch to `main` and the folder to `/docs`. Click **Save**.
4. After a minute or two, the page is live at <https://sumitd07.github.io/clause/>.

The `docs/.nojekyll` file tells GitHub to serve the page as it is, without running its own site builder over it. Leave it in.

## Later steps

**The freeze tag** (build plan task 2.3). Once the test cases and their expected answers are committed, open **History** in GitHub Desktop. Right-click the latest commit, choose **Create Tag…**, name it `eval-frozen-v1`, then click **Push origin**. Check that it appears at <https://github.com/sumitd07/clause/tags>. The tag's date proves the test set existed before any system ran on it.

**The API key secret.** You only need this if you want to run the manual `eval` workflow on GitHub instead of on your machine. Add a secret named `ANTHROPIC_API_KEY` at <https://github.com/sumitd07/clause/settings/secrets/actions>. The workflow runs only when you start it from the Actions tab, because each run costs money. Never put the key in a file in the repo.

**Day to day.** After each work session, GitHub Desktop shows the changed files. Write a one-line summary, click **Commit to main**, then **Push origin**.

## The terminal version

If you prefer the command line and have the GitHub CLI (`brew install gh`, then `gh auth login`):

```bash
cd path/to/clause
git init -b main
git add .
git status                       # check there is no .env in the list
git commit -m "Clause day 0: engine, answer form, scoring, docs"
gh repo create sumitd07/clause --public --source=. --push \
  --description "Ask what your health insurance policy covers and pays, and see the clause behind every answer."
gh repo edit sumitd07/clause --add-topic llm,evals,health-insurance,rules-engine,document-ai,anthropic,india,consumer,explainability
gh run watch                     # follow the first CI run
```

The freeze tag, later: `git tag eval-frozen-v1 && git push origin eval-frozen-v1`.

## Watch-outs

- Publishing makes the history public too. If a key ever lands in a commit, deleting the file isn't enough. Revoke the key in the Anthropic console first, then clean the history.
- GitHub Desktop sometimes shows the first commit's files under **Changes** instead of committing them. The fallback in step 2 covers that.
- Running the fetch script fills `data/policies/raw/` with insurer PDFs. That folder is ignored on purpose, so don't force-add it.
