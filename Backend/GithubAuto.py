from __future__ import annotations
import os
import subprocess
import webbrowser
from typing import Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
from dotenv import dotenv_values
from github import Github, GithubException

# Load env
_env = dotenv_values(".env")
GITHUB_TOKEN = _env.get("GitHubToken") or os.environ.get("GitHubToken")
GITHUB_USERNAME = _env.get("GitHubUsername") or os.environ.get("GitHubUsername")

if not GITHUB_TOKEN:
    raise RuntimeError("GitHubToken not found in .env or environment variables.")

# --------------------- Helpers & Types ---------------------

@dataclass
class RepoInfo:
    name: str
    full_name: str
    private: bool
    html_url: str

@lru_cache(maxsize=1)
def _get_client() -> Github:
    """Return a cached Github client."""
    return Github(GITHUB_TOKEN)

def _run_git(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

# --------------------- Repo Management ---------------------
def create_repo(name: str, private: bool = False) -> RepoInfo:
    """Create a repo on your GitHub account.

    Args:
        name: repository name
        private: True -> private repo

    Returns RepoInfo
    """
    gh = _get_client()
    user = gh.get_user()
    try:
        repo = user.create_repo(name=name, private=private)
        return RepoInfo(name=repo.name, full_name=repo.full_name, private=repo.private, html_url=repo.html_url)
    except GithubException as e:
        raise RuntimeError(f"Failed to create repo: {e.data if hasattr(e, 'data') else str(e)}")

def delete_repo(name: str, confirm: bool = True) -> bool:
    """Delete repo from your account. confirm must be True to proceed.

    Returns True on success.
    """
    if confirm is not True:
        raise RuntimeError("Delete requires explicit confirmation (confirm=True).")
    gh = _get_client()
    user = gh.get_user()
    try:
        repo = user.get_repo(name)
        repo.delete()
        return True
    except GithubException as e:
        raise RuntimeError(f"Failed to delete repo: {e.data if hasattr(e, 'data') else str(e)}")

def list_repos(visibility: Optional[str] = None) -> List[RepoInfo]:
    """List repos from your account.

    visibility: None|"public"|"private"
    """
    gh = _get_client()
    user = gh.get_user()
    repos = []
    for r in user.get_repos():
        if visibility == "public" and r.private:
            continue
        if visibility == "private" and not r.private:
            continue
        repos.append(RepoInfo(name=r.name, full_name=r.full_name, private=r.private, html_url=r.html_url))
    return repos

def find_repo_by_name(name: str) -> Optional[RepoInfo]:
    gh = _get_client()
    user = gh.get_user()
    try:
        r = user.get_repo(name)
        return RepoInfo(name=r.name, full_name=r.full_name, private=r.private, html_url=r.html_url)
    except GithubException:
        return None

def open_repo_in_browser(name: str) -> bool:
    """Open repo page in browser if it exists on your account."""
    info = find_repo_by_name(name)
    if not info:
        return False
    webbrowser.open(info.html_url)
    return True

# --------------------- Clone (only from your account) ---------------------
def clone_repo(name: str, dest_path: str) -> str:
    """Clone a repository from your account to dest_path.

    Returns the path to the cloned repo on success.
    """
    info = find_repo_by_name(name)
    if not info:
        raise RuntimeError("Repository not found on your account.")

    dest = Path(dest_path).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / name
    if target.exists():
        raise RuntimeError(f"Target path already exists: {target}")

    # Use HTTPS clone with token in URL for private repos (safer to use local ssh keys if available)
    repo_url = info.html_url
    if info.private:
        # insert token into https url: https://{token}@github.com/owner/repo.git
        repo_url = repo_url.replace("https://", f"https://{GITHUB_TOKEN}@")

    code, out, err = _run_git(["git", "clone", repo_url, str(target)])
    if code != 0:
        raise RuntimeError(f"Git clone failed: {err or out}")
    return str(target)

# --------------------- Local Git Operations ---------------------

def _assert_cloned_repo(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.exists():
        raise RuntimeError("Local path does not exist.")
    if not (p / ".git").exists():
        raise RuntimeError("Not a git repository (missing .git).")
    return p

def git_commit(path: str, message: str) -> None:
    p = _assert_cloned_repo(path)
    code, out, err = _run_git(["git", "add", "-A"], cwd=str(p))
    if code != 0:
        raise RuntimeError(f"git add failed: {err or out}")
    code, out, err = _run_git(["git", "commit", "-m", message], cwd=str(p))
    if code != 0:
        # if nothing to commit, Git returns specific messages; surfacing that
        raise RuntimeError(f"git commit failed: {err or out}")

def git_push(path: str, remote: str = "origin", branch: str = "main") -> None:
    p = _assert_cloned_repo(path)
    code, out, err = _run_git(["git", "push", remote, branch], cwd=str(p))
    if code != 0:
        raise RuntimeError(f"git push failed: {err or out}")

def git_pull(path: str, remote: str = "origin", branch: str = "main") -> None:
    p = _assert_cloned_repo(path)
    code, out, err = _run_git(["git", "pull", remote, branch], cwd=str(p))
    if code != 0:
        raise RuntimeError(f"git pull failed: {err or out}")

def git_create_branch(path: str, branch: str) -> None:
    p = _assert_cloned_repo(path)
    code, out, err = _run_git(["git", "checkout", "-b", branch], cwd=str(p))
    if code != 0:
        raise RuntimeError(f"git branch create failed: {err or out}")

def git_checkout_branch(path: str, branch: str) -> None:
    p = _assert_cloned_repo(path)
    code, out, err = _run_git(["git", "checkout", branch], cwd=str(p))
    if code != 0:
        raise RuntimeError(f"git checkout failed: {err or out}")

# --------------------- Search / Star / Unstar ---------------------

def search_repos(query: str, limit: int = 10) -> List[RepoInfo]:
    gh = _get_client()
    res = gh.search_repositories(query)  # returns PaginatedList
    out = []
    for i, r in enumerate(res):
        if i >= limit:
            break
        out.append(RepoInfo(name=r.name, full_name=r.full_name, private=r.private, html_url=r.html_url))
    return out

def search_users(query: str, limit: int = 10) -> List[Tuple[str, str]]:
    gh = _get_client()
    res = gh.search_users(query)
    out = []
    for i, u in enumerate(res):
        if i >= limit:
            break
        out.append((u.login, u.html_url))
    return out

if __name__ == "__main__":
    while True:
        print("\n==== GitHub Manager Test Menu ====")
        print("1. Create Repo")
        print("2. Delete Repo")
        print("3. List Repos")
        print("4. Find Repo by Name")
        print("5. Open Repo in Browser")
        print("6. Clone Repo")
        print("7. Git Commit")
        print("8. Git Push")
        print("9. Git Pull")
        print("10. Create Branch")
        print("11. Checkout Branch")
        print("12. Search Repos")
        print("13. Search Users")
        print("0. Exit")
        choice = input("Select option: ").strip()

        try:
            if choice == "1":
                name = input("Repo name: ")
                private = input("Private? (y/n): ").lower() == "y"
                info = create_repo(name, private)
                print("Created:", info)
            elif choice == "2":
                name = input("Repo name: ")
                ok = delete_repo(name, confirm=True)
                print("Deleted:", ok)
            elif choice == "3":
                repos = list_repos()
                for r in repos:
                    print(r)
            elif choice == "4":
                name = input("Repo name: ")
                print(find_repo_by_name(name))
            elif choice == "5":
                name = input("Repo name: ")
                print("Opened:", open_repo_in_browser(name))
            elif choice == "6":
                name = input("Repo name: ")
                dest = input("Destination path: ")
                print("Cloned to:", clone_repo(name, dest))
            elif choice == "7":
                path = input("Repo path: ")
                msg = input("Commit message: ")
                git_commit(path, msg)
                print("Committed.")
            elif choice == "8":
                path = input("Repo path: ")
                git_push(path)
                print("Pushed.")
            elif choice == "9":
                path = input("Repo path: ")
                git_pull(path)
                print("Pulled.")
            elif choice == "10":
                path = input("Repo path: ")
                branch = input("Branch name: ")
                git_create_branch(path, branch)
                print("Branch created.")
            elif choice == "11":
                path = input("Repo path: ")
                branch = input("Branch name: ")
                git_checkout_branch(path, branch)
                print("Checked out.")
            elif choice == "12":
                query = input("Search query: ")
                for r in search_repos(query):
                    print(r)
            elif choice == "13":
                query = input("Search users: ")
                for u in search_users(query):
                    print(u)
            elif choice == "0":
                break
            else:
                print("Invalid choice")
        except Exception as e:
            print("Error:", e)
