"""Land an agent branch on the default branch from the agent's own environment, without GitHub Actions.

Same result as workflows/land.yml: the branch is validated, squashed onto the default branch with its
commit messages, validated again together with it, pushed, and deleted; the statuses `check` and `land`
are posted on the branch tip. Run inside a clone whose origin is the GitHub repository:

    GH_TOKEN=... python .system/tools/plyn_land.py [branch]

The branch defaults to the current one. Project checks (.github/workflows/check-<name>.yml, still run by
Actions) are waited for through their statuses check/<name>, as land.yml does; a project check that skips
private repositories is run in the agent's environment as the repository's AGENTS.md says. Exit code 0 means landed."""
import json, os, re, subprocess, sys, tempfile, time, urllib.request

def git(*a, cwd=".", check=True):
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(a)} failed: {r.stderr.strip()}")
    return r.stdout.strip()

def slug():
    url = git("remote", "get-url", "origin")
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    if not m: raise SystemExit("origin is not a GitHub repository")
    return m.group(1)

def status(repo, sha, context, state, desc):
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(f"(no GH_TOKEN: status {context}={state} not posted)"); return
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/statuses/{sha}", method="POST",
        data=json.dumps({"state": state, "context": context, "description": desc[:139]}).encode(),
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"})
    urllib.request.urlopen(req).read()

def api_get(path):
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Authorization": f"token {token}"} if token else {})
    return json.loads(urllib.request.urlopen(req).read())

def project_checks(repo, sha, path, attempts=60, interval=10):
    wf = os.path.join(path, ".github", "workflows")
    names = sorted(f[6:-4] for f in os.listdir(wf) if f.startswith("check-") and f.endswith(".yml")
                   and "repository.private" not in open(os.path.join(wf, f)).read()) if os.path.isdir(wf) else []
    for attempt in range(attempts):
        states = {s["context"]: s["state"] for s in reversed(api_get(f"repos/{repo}/commits/{sha}/status").get("statuses", []))}
        pending = []
        for n in names:
            st = states.get(f"check/{n}", "pending")
            if st in ("failure", "error"): return f"Check check/{n} failed"
            if st != "success": pending.append(n)
        if not pending: return ""
        time.sleep(interval)
    return "Checks did not finish: " + " ".join(pending)

def validate(path):
    v = next((p for p in (".system/tools/plyn_validate.py", "tools/plyn_validate.py") if os.path.exists(os.path.join(path, p))), None)
    if v is None:
        return (False, "Validator expected but missing") if os.path.exists(os.path.join(path, "system.yaml")) else (True, "")
    f = "formats" if os.path.isdir(os.path.join(path, "formats")) else ".system/formats"
    r = subprocess.run([sys.executable, v, ".", "--formats", f], cwd=path, capture_output=True, text=True,
                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    out = r.stdout + r.stderr
    first = next((l for l in out.splitlines() if "ERROR" in l), "Checks failed")
    return r.returncode == 0, ("" if r.returncode == 0 else first[:130]) + ("\n" + out if r.returncode else "")

def main():
    repo = slug()
    branch = sys.argv[1] if len(sys.argv) > 1 else git("rev-parse", "--abbrev-ref", "HEAD")
    main_branch = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD").split("/", 1)[1]
    for b in (main_branch, branch):  # explicit refspecs: single-branch and shallow clones fetch only main
        git("fetch", "-q", "origin", f"+refs/heads/{b}:refs/remotes/origin/{b}", check=b == main_branch)
    if branch == main_branch: raise SystemExit("Give the agent branch, not the default branch")
    if git("ls-remote", "--heads", "origin", branch) == "":
        raise SystemExit(f"origin/{branch} does not exist: push the branch first")
    tip = git("rev-parse", f"origin/{branch}")
    with tempfile.TemporaryDirectory() as wt:
        git("worktree", "add", "-q", "--detach", wt, tip)
        try:
            ok, why = validate(wt)
            status(repo, tip, "check", "success" if ok else "failure", "Checks passed" if ok else why.split("\n")[0])
            if not ok:
                print(why); status(repo, tip, "land", "failure", "Not landed: check failed"); return 1
            why = project_checks(repo, tip, wt)
            if why:
                print(why); status(repo, tip, "land", "failure", "Not landed: " + why); return 1
            base = git("merge-base", f"origin/{main_branch}", tip)
            msgs = git("log", "--reverse", "--format=%B", f"{base}..{tip}").splitlines()
            seen, lines = set(), []
            for l in msgs:
                l = re.sub(r" *\[ready\]", "", l).rstrip()
                if not l.strip() or l.startswith("Co-authored-by:") or l in seen: continue
                seen.add(l); lines.append(l)
            msg = (lines[0] + "\n\n" + "\n".join(lines[1:])).strip() if lines else "Agent changes"
            author = git("log", "-1", "--format=%an <%ae>", tip)
            for attempt in range(3):
                git("fetch", "-q", "origin", f"+refs/heads/{main_branch}:refs/remotes/origin/{main_branch}")
                git("checkout", "-q", "--detach", f"origin/{main_branch}", cwd=wt)
                r = subprocess.run(["git", "merge", "--squash", tip], cwd=wt, capture_output=True, text=True)
                if r.returncode:
                    print(r.stdout + r.stderr); status(repo, tip, "land", "failure", "Not landed: Conflicts with the default branch"); return 1
                if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=wt).returncode == 0:
                    print("Nothing to land: the default branch already has these changes"); break
                git("commit", "-q", f"--author={author}", "-m", msg, cwd=wt)
                ok, why = validate(wt)
                if not ok:
                    print(why); status(repo, tip, "land", "failure", "Not landed: Checks fail together with the default branch"); return 1
                if subprocess.run(["git", "push", "-q", "origin", f"HEAD:{main_branch}"], cwd=wt).returncode == 0: break
                time.sleep(5 * (attempt + 1))
            else:
                status(repo, tip, "land", "failure", "Not landed: the default branch kept moving"); return 1
        finally:
            git("worktree", "remove", "--force", wt, check=False)
    git("push", "-q", "origin", "--delete", branch, check=False)
    status(repo, tip, "land", "success", "Landed")
    print(f"Landed {branch} on {main_branch} of {repo}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
