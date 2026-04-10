"""Classify changes as major, minor, or patch for Annex IV purposes."""

MAJOR_KEYWORDS = [
    "breaking", "major", "architecture", "redesign", "replace", "rewrite",
    "new model", "retrain", "dataset change", "algorithm change",
]
MINOR_KEYWORDS = [
    "feature", "improvement", "enhance", "improve", "new capability",
    "fine-tune", "optimize", "add new",
]


def classify_change(commit_message: str) -> str:
    msg = commit_message.lower()
    for kw in MAJOR_KEYWORDS:
        if kw in msg:
            return "major"
    for kw in MINOR_KEYWORDS:
        if kw in msg:
            return "minor"
    return "patch"


def classify_commits(commits: list[dict]) -> list[dict]:
    return [
        {**commit, "classification": classify_change(commit.get("message", ""))}
        for commit in commits
    ]


def requires_annex_iv_update(classification: str) -> bool:
    return classification in ("major", "minor")
