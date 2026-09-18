#!/usr/bin/env python3
"""Screen a candidate resume/profile against a PwC job description.

Usage:
    python screen.py --job job_description.txt --resume resume.txt
    python screen.py --job job_description.txt --resume-dir resumes/
"""
import argparse
import glob
import os
import re
import sys
from dataclasses import dataclass, field

STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "are", "our", "will",
    "this", "that", "have", "from", "who", "job", "role", "work", "years",
    "experience", "ability", "skills", "including", "such", "into",
    "across", "within", "team", "teams", "using", "use", "used", "not",
    "all", "any", "can", "must", "than", "been", "were", "was", "has",
    "or", "as", "to", "of", "in", "on", "a", "an", "is", "be", "we",
    "at", "by", "it", "its", "their", "they", "them", "other",
}

REQUIRED_MARKERS = (
    "what you must have",
    "must have",
    "minimum qualifications",
    "required qualifications",
    "basic qualifications",
)
PREFERRED_MARKERS = (
    "what sets you apart",
    "preferred qualifications",
    "preferred",
    "nice to have",
    "bonus",
    "plus",
)


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}", text.lower())
    return {w.strip(".,") for w in words if w not in STOPWORDS and len(w) > 2}


def split_sections(job_text: str) -> tuple[str, str]:
    """Best-effort split of the job description into required vs preferred text."""
    lower = job_text.lower()
    req_idx = min(
        (lower.find(m) for m in REQUIRED_MARKERS if m in lower), default=-1
    )
    pref_idx = min(
        (lower.find(m) for m in PREFERRED_MARKERS if m in lower), default=-1
    )
    end = pref_idx if pref_idx > -1 else len(job_text)
    if req_idx > -1 and req_idx < end:
        required_text = job_text[req_idx:end]
    else:
        required_text = job_text[:end]
    preferred_text = job_text[pref_idx:] if pref_idx > -1 else ""
    return required_text, preferred_text


@dataclass
class ScreeningResult:
    candidate: str
    score: float
    matched_required: set = field(default_factory=set)
    missing_required: set = field(default_factory=set)
    matched_preferred: set = field(default_factory=set)

    def summary(self) -> str:
        lines = [
            f"Candidate: {self.candidate}",
            f"Fit score: {self.score:.0f}%",
            f"  Matched required keywords ({len(self.matched_required)}): "
            + ", ".join(sorted(self.matched_required)) or "  none",
            f"  Missing required keywords ({len(self.missing_required)}): "
            + ", ".join(sorted(self.missing_required)) or "  none",
            f"  Matched preferred keywords ({len(self.matched_preferred)}): "
            + ", ".join(sorted(self.matched_preferred)) or "  none",
        ]
        return "\n".join(lines)


def screen_resume(job_text: str, resume_text: str, candidate: str) -> ScreeningResult:
    required_text, preferred_text = split_sections(job_text)
    all_markers = REQUIRED_MARKERS + PREFERRED_MARKERS
    marker_words = {w for m in all_markers for w in tokenize(m)}
    required_kw = tokenize(required_text) - marker_words
    preferred_kw = tokenize(preferred_text) - marker_words - required_kw
    resume_kw = tokenize(resume_text)

    matched_required = required_kw & resume_kw
    missing_required = required_kw - resume_kw
    matched_preferred = preferred_kw & resume_kw

    if required_kw:
        base_score = len(matched_required) / len(required_kw) * 100
    else:
        base_score = 0.0
    bonus = min(len(matched_preferred), 10) * 1.0
    score = min(base_score + bonus, 100.0)

    return ScreeningResult(
        candidate=candidate,
        score=score,
        matched_required=matched_required,
        missing_required=missing_required,
        matched_preferred=matched_preferred,
    )


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True, help="Path to the job description text file")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--resume", help="Path to a single resume/profile text file")
    group.add_argument("--resume-dir", help="Directory of resume/profile .txt files to screen in bulk")
    parser.add_argument("--top", type=int, default=None, help="Only show the top N candidates (bulk mode)")
    args = parser.parse_args()

    if not os.path.isfile(args.job):
        print(f"Job description not found: {args.job}", file=sys.stderr)
        return 1
    job_text = read_file(args.job)

    if args.resume:
        if not os.path.isfile(args.resume):
            print(f"Resume not found: {args.resume}", file=sys.stderr)
            return 1
        candidate = os.path.splitext(os.path.basename(args.resume))[0]
        result = screen_resume(job_text, read_file(args.resume), candidate)
        print(result.summary())
        return 0

    paths = sorted(glob.glob(os.path.join(args.resume_dir, "*.txt")))
    if not paths:
        print(f"No .txt resumes found in {args.resume_dir}", file=sys.stderr)
        return 1

    results = []
    for path in paths:
        candidate = os.path.splitext(os.path.basename(path))[0]
        results.append(screen_resume(job_text, read_file(path), candidate))

    results.sort(key=lambda r: r.score, reverse=True)
    if args.top:
        results = results[: args.top]

    for i, result in enumerate(results, start=1):
        print(f"#{i}")
        print(result.summary())
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
