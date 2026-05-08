"""Unit tests for Craft GitHub publishing helpers."""

from onyx.server.features.build.github_publish import (
    GithubFile,
    build_default_repo_name,
    with_default_github_files,
)


def test_default_repo_name_includes_session_suffix() -> None:
    repo_name = build_default_repo_name(
        "dbalderston@ucsd.edu",
        "Lab Dashboard",
        "019dfe74-0974-7da1-b74e-d83af92c4658",
    )

    assert repo_name == "onyx-dbalderston-lab-dashboard-019dfe74"


def test_default_repo_name_preserves_session_suffix_when_truncated() -> None:
    repo_name = build_default_repo_name(
        "dbalderston@ucsd.edu",
        "This Project Name Is Intentionally Long Enough To Need Truncation "
        "Before Publishing To GitHub",
        "019dfe74-0974-7da1-b74e-d83af92c4658",
    )

    assert len(repo_name) <= 100
    assert repo_name.startswith("onyx-dbalderston-this-project-name")
    assert repo_name.endswith("-019dfe74")


def test_default_github_files_do_not_include_security_workflow() -> None:
    files = with_default_github_files(
        [GithubFile("app/page.tsx", b"export default Page")]
    )
    paths = {file.path for file in files}

    assert ".github/workflows/onyx-craft-ci.yml" in paths
    assert ".github/dependabot.yml" in paths
    assert ".github/workflows/security.yml" not in paths
