"""GitHub publishing helpers for Onyx Craft generated apps."""

import base64
import os
import re
from dataclasses import dataclass
from typing import Any

import httpx


GITHUB_API_URL = "https://api.github.com"
DEFAULT_GITHUB_OWNER = os.environ.get("ONYX_CRAFT_GITHUB_OWNER", "dbaldersapps")


class GithubPublishError(Exception):
    """Raised when publishing an app to GitHub fails."""


@dataclass(frozen=True)
class GithubFile:
    path: str
    content: bytes


@dataclass(frozen=True)
class GithubPublishResult:
    owner: str
    repo_name: str
    html_url: str
    commit_url: str
    commit_sha: str
    created_repo: bool


def slugify_repo_part(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def build_default_repo_name(user_email: str | None, session_name: str | None) -> str:
    username = slugify_repo_part((user_email or "user").split("@", 1)[0], "user")
    project = slugify_repo_part(session_name or "app", "app")
    repo_name = f"onyx-craft-{username}-{project}"
    return repo_name[:100].rstrip("-")


def craft_ci_workflow() -> bytes:
    return b"""name: Onyx Craft CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run lint --if-present
      - run: npm run test --if-present
      - run: npm run build --if-present
"""


def security_workflow() -> bytes:
    return b"""name: Security Review

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write

jobs:
  dependency-review:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4

  codeql:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript-typescript
      - uses: github/codeql-action/analyze@v3

  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2

  filesystem-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: fs
          scan-ref: .
          severity: HIGH,CRITICAL
          exit-code: "1"
"""


def dependabot_config() -> bytes:
    return b"""version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
"""


def with_default_github_files(files: list[GithubFile]) -> list[GithubFile]:
    generated_paths = {file.path for file in files}
    default_files = [
        GithubFile(".github/workflows/onyx-craft-ci.yml", craft_ci_workflow()),
        GithubFile(".github/workflows/security.yml", security_workflow()),
        GithubFile(".github/dependabot.yml", dependabot_config()),
    ]
    return files + [file for file in default_files if file.path not in generated_paths]


class GithubPublisher:
    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ.get("ONYX_CRAFT_GITHUB_TOKEN")
        if not self._token:
            raise GithubPublishError(
                "GitHub publishing is not configured. "
                "Set ONYX_CRAFT_GITHUB_TOKEN on the backend."
            )

    def publish(
        self,
        *,
        owner: str,
        repo_name: str,
        description: str,
        files: list[GithubFile],
        private: bool = True,
    ) -> GithubPublishResult:
        with httpx.Client(
            base_url=GITHUB_API_URL,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        ) as client:
            repo, created_repo = self._ensure_repo(
                client, owner, repo_name, description, private
            )
            repo = self._ensure_repo_has_initial_commit(client, owner, repo_name, repo)
            default_branch = repo.get("default_branch") or "main"
            commit = self._commit_files(
                client=client,
                owner=owner,
                repo_name=repo_name,
                branch=default_branch,
                files=files,
            )

        html_url = str(
            repo.get("html_url") or f"https://github.com/{owner}/{repo_name}"
        )
        commit_sha = str(commit["sha"])
        return GithubPublishResult(
            owner=owner,
            repo_name=repo_name,
            html_url=html_url,
            commit_url=f"{html_url}/commit/{commit_sha}",
            commit_sha=commit_sha,
            created_repo=created_repo,
        )

    def _ensure_repo(
        self,
        client: httpx.Client,
        owner: str,
        repo_name: str,
        description: str,
        private: bool,
    ) -> tuple[dict[str, Any], bool]:
        existing = client.get(f"/repos/{owner}/{repo_name}")
        if existing.status_code == 200:
            return existing.json(), False
        if existing.status_code not in (404, 403):
            self._raise_for_response(existing, "Failed to check GitHub repository")

        create_path = self._repo_create_path(client, owner)
        created = client.post(
            create_path,
            json={
                "name": repo_name,
                "description": description,
                "private": private,
                "auto_init": True,
            },
        )
        if created.status_code == 201:
            return created.json(), True

        self._raise_for_response(created, "Failed to create GitHub repository")
        raise AssertionError("unreachable")

    def _repo_create_path(self, client: httpx.Client, owner: str) -> str:
        authenticated_user = client.get("/user")
        self._raise_for_response(
            authenticated_user, "Failed to load authenticated GitHub user"
        )
        if str(authenticated_user.json().get("login", "")).lower() == owner.lower():
            return "/user/repos"
        return f"/orgs/{owner}/repos"

    def _ensure_repo_has_initial_commit(
        self,
        client: httpx.Client,
        owner: str,
        repo_name: str,
        repo: dict[str, Any],
    ) -> dict[str, Any]:
        branch = str(repo.get("default_branch") or "main")
        ref = client.get(f"/repos/{owner}/{repo_name}/git/ref/heads/{branch}")
        if ref.status_code == 200:
            return repo
        if ref.status_code not in (404, 409):
            self._raise_for_response(ref, "Failed to load Git branch")

        readme = client.put(
            f"/repos/{owner}/{repo_name}/contents/README.md",
            json={
                "message": "Initialize repository",
                "content": base64.b64encode(
                    f"# {repo_name}\n\nGenerated by Onyx Craft.\n".encode("utf-8")
                ).decode("ascii"),
                "branch": branch,
            },
        )
        self._raise_for_response(readme, "Failed to initialize GitHub repository")

        refreshed = client.get(f"/repos/{owner}/{repo_name}")
        self._raise_for_response(refreshed, "Failed to reload GitHub repository")
        return refreshed.json()

    def _commit_files(
        self,
        *,
        client: httpx.Client,
        owner: str,
        repo_name: str,
        branch: str,
        files: list[GithubFile],
    ) -> dict[str, Any]:
        base_commit_sha: str | None = None
        base_tree_sha: str | None = None
        ref = client.get(f"/repos/{owner}/{repo_name}/git/ref/heads/{branch}")
        if ref.status_code == 200:
            base_commit_sha = ref.json()["object"]["sha"]
            base_commit = client.get(
                f"/repos/{owner}/{repo_name}/git/commits/{base_commit_sha}"
            )
            self._raise_for_response(base_commit, "Failed to load base Git commit")
            base_tree_sha = base_commit.json()["tree"]["sha"]
        elif ref.status_code not in (404, 409):
            self._raise_for_response(ref, "Failed to load Git branch")

        tree_items: list[dict[str, str]] = []
        for file in files:
            blob = client.post(
                f"/repos/{owner}/{repo_name}/git/blobs",
                json={
                    "content": base64.b64encode(file.content).decode("ascii"),
                    "encoding": "base64",
                },
            )
            self._raise_for_response(blob, f"Failed to upload {file.path}")
            tree_items.append(
                {
                    "path": file.path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob.json()["sha"],
                }
            )

        tree_payload: dict[str, Any] = {"tree": tree_items}
        if base_tree_sha:
            tree_payload["base_tree"] = base_tree_sha
        tree = client.post(
            f"/repos/{owner}/{repo_name}/git/trees",
            json=tree_payload,
        )
        self._raise_for_response(tree, "Failed to create Git tree")

        commit_payload: dict[str, Any] = {
            "message": "Publish Onyx Craft app",
            "tree": tree.json()["sha"],
        }
        if base_commit_sha:
            commit_payload["parents"] = [base_commit_sha]
        commit = client.post(
            f"/repos/{owner}/{repo_name}/git/commits",
            json=commit_payload,
        )
        self._raise_for_response(commit, "Failed to create Git commit")

        commit_json = commit.json()
        if base_commit_sha:
            update_ref = client.patch(
                f"/repos/{owner}/{repo_name}/git/refs/heads/{branch}",
                json={"sha": commit_json["sha"]},
            )
            self._raise_for_response(update_ref, "Failed to update Git branch")
        else:
            create_ref = client.post(
                f"/repos/{owner}/{repo_name}/git/refs",
                json={"ref": f"refs/heads/{branch}", "sha": commit_json["sha"]},
            )
            self._raise_for_response(create_ref, "Failed to create Git branch")

        return commit_json

    @staticmethod
    def _raise_for_response(response: httpx.Response, message: str) -> None:
        if response.is_success:
            return
        detail = response.text
        try:
            detail = response.json().get("message", detail)
        except ValueError:
            pass
        raise GithubPublishError(f"{message}: {response.status_code} {detail}")
