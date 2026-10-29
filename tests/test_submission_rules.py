"""Hackathon hard rules checked on every CI run (T148), so a late change cannot break them unnoticed:
Meta models only at runtime, no keys in git, no .env in git, and no "detects AI / fake videos" claims."""
import re
import subprocess

RUNTIME = ["backend", "meta_client", "physics", "frontend/src"]
USER_FACING = ["README.md", "frontend/src"]


def tracked(*paths):
    out = subprocess.run(["git", "ls-files", *paths], capture_output=True, text=True, check=True).stdout.split()
    return [p for p in out if not re.search(r"(^|/)tests?/|\.test\.|_test\.|\.(png|jpg|mp4|mov|ico|lock)$", p)]


def grep(paths, pattern, flags=re.I):
    rx = re.compile(pattern, flags)
    hits = []
    for p in tracked(*paths):
        try:
            text = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        hits += [f"{p}: {m.group(0)}" for m in rx.finditer(text)]
    return hits


def test_runtime_calls_meta_models_only():
    assert not grep(RUNTIME, r"api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis|"
                             r"\b(gpt-[34]|claude-[a-z0-9]|gemini-[0-9]|llama-?api)\b")
    models = {m.split(": ")[1].strip('"') for m in grep(["meta_client", "backend"], r'"(muse|sam)-[a-z0-9.\-]+"')}
    allowed = {"muse-spark-1.1", "muse-spark-1.2", "muse-spark-1.3", "muse-spark-1.2-contributor",
               "muse-spark-1.3-contributor", "muse-wonder-1.0", "muse-voice-transcribe-1.0", "sam-3.1"}
    assert models <= allowed, models - allowed
    assert not grep(["meta_client"], r"base_url\s*=\s*['\"]https?://(?!api\.meta\.ai)")


def test_no_keys_or_env_files_in_git():
    assert ".env" not in tracked(".env")
    assert not grep(["."], r"\b(sk-[A-Za-z0-9]{24,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})\b", 0)
    assert not grep(["."], r"MODEL_API_KEY\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}")


def test_no_authenticity_claims_in_user_facing_text():
    claims = (r"detects? (ai|fake|generated)|ai[- ]detector|fake[- ]video detector|lie detector|spot(s)? fakes|"
              r"tells? (if|whether) a video is (real|fake)|works on any video|抓假|測謊|辨識(AI|真偽)")
    assert not grep(USER_FACING, claims)
