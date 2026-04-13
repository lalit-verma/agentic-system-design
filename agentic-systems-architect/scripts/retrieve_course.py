#!/usr/bin/env python3
"""Retrieve the most relevant course material for an architecture query."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STOPWORDS = {
    "a",
    "an",
    "and",
    "agent",
    "agents",
    "are",
    "as",
    "at",
    "be",
    "because",
    "build",
    "building",
    "by",
    "can",
    "data",
    "for",
    "from",
    "help",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "long",
    "my",
    "of",
    "on",
    "or",
    "our",
    "running",
    "should",
    "system",
    "systems",
    "that",
    "the",
    "this",
    "to",
    "use",
    "using",
    "want",
    "we",
    "what",
    "when",
    "with",
}


MODULE_ENTRY_RE = re.compile(
    r"^### Module (?P<number>\d+): (?P<title>.+?)\n"
    r"- \*\*Path\*\*: `(?P<path>[^`]+)`\n"
    r"- \*\*SE Parallel\*\*: (?P<se_parallel>.+?)\n"
    r"- \*\*Builds on\*\*: (?P<builds_on>.+?)\n"
    r"(?:(?:- \*\*Patterns\*\*: (?P<patterns>.+?)\n))?"
    r"- \*\*Summary\*\*: (?P<summary>.+?)(?=\n### Module \d+:|\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)


@dataclass
class ModuleMeta:
    number: int
    title: str
    path: str
    se_parallel: str
    builds_on: str
    summary: str
    patterns: list[str]


@dataclass
class Cluster:
    title: str
    body: str
    modules: list[int]


@dataclass
class PatternEntry:
    name: str
    module: int
    section: str


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_token(token: str) -> str:
    token = token.lower()
    alias_map = {
        "autonomy": "autonom",
        "autonomous": "autonom",
        "coding": "code",
        "controls": "control",
        "eval": "eval",
        "evaluation": "eval",
        "evaluations": "eval",
        "evals": "eval",
        "orchestrate": "orchestr",
        "orchestration": "orchestr",
        "orchestrations": "orchestr",
        "router": "route",
        "routing": "route",
        "secure": "secur",
        "security": "secur",
        "tooling": "tool",
        "tools": "tool",
    }
    if token in alias_map:
        return alias_map[token]
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    return [normalize_token(token) for token in re.findall(r"[a-z0-9]+", text.lower())]


def query_terms(query: str) -> list[str]:
    seen = set()
    terms = []
    for token in tokenize(query):
        if len(token) < 3 or token in STOPWORDS or token in seen:
            continue
        seen.add(token)
        terms.append(token)
    return terms


def text_score(text: str, terms: list[str]) -> float:
    if not text:
        return 0.0
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    score = 0.0
    for term in terms:
        if term not in counts:
            continue
        score += 1.0 + min(counts[term], 5) * 0.75
    return score


def parse_module_number_list(raw_value: str) -> list[int]:
    if "nothing" in raw_value.lower():
        return []
    numbers: list[int] = []
    for match in re.finditer(r"\d+(?:-\d+)?", raw_value):
        token = match.group(0)
        if "-" in token:
            start, end = token.split("-", 1)
            numbers.extend(range(int(start), int(end) + 1))
        else:
            numbers.append(int(token))
    return sorted(set(numbers))


def parse_module_details(index_text: str) -> dict[int, ModuleMeta]:
    modules: dict[int, ModuleMeta] = {}
    for match in MODULE_ENTRY_RE.finditer(index_text):
        patterns_raw = match.group("patterns") or ""
        patterns = [normalize_whitespace(part) for part in patterns_raw.split(",") if part.strip()]
        module = ModuleMeta(
            number=int(match.group("number")),
            title=normalize_whitespace(match.group("title")),
            path=match.group("path").strip(),
            se_parallel=normalize_whitespace(match.group("se_parallel")),
            builds_on=normalize_whitespace(match.group("builds_on")),
            summary=normalize_whitespace(match.group("summary")),
            patterns=patterns,
        )
        modules[module.number] = module
    return modules


def parse_clusters(index_text: str) -> list[Cluster]:
    start = index_text.find("## Problem Clusters")
    end = index_text.find("## Module Details")
    if start == -1 or end == -1 or end <= start:
        return []
    problem_text = index_text[start:end]
    matches = list(
        re.finditer(
            r"^### (?P<title>.+?)\n(?P<body>.*?)(?=^### |\Z)",
            problem_text,
            re.MULTILINE | re.DOTALL,
        )
    )
    clusters: list[Cluster] = []
    for match in matches:
        body = match.group("body").strip()
        modules = sorted({int(found) for found in re.findall(r"\|\s*(\d+)\s*\|", body)})
        clusters.append(
            Cluster(
                title=normalize_whitespace(match.group("title")),
                body=body,
                modules=modules,
            )
        )
    return clusters


def parse_patterns(patterns_text: str) -> list[PatternEntry]:
    entries: list[PatternEntry] = []
    current_section = ""
    for line in patterns_text.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        if not line.startswith("|"):
            continue
        columns = [col.strip() for col in line.strip().strip("|").split("|")]
        if len(columns) != 2 or columns[0] == "Pattern" or columns[0].startswith("---"):
            continue
        match = re.search(r"Module\s+(\d+)", columns[1])
        if not match:
            continue
        entries.append(
            PatternEntry(
                name=columns[0],
                module=int(match.group(1)),
                section=current_section,
            )
        )
    return entries


def split_module_sections(module_text: str) -> list[tuple[str, str]]:
    lines = module_text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_title = "Module Overview"
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## ") or line.startswith("### "):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = line.lstrip("#").strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [(title, normalize_whitespace("\n".join(body))) for title, body in sections]


def truncate_excerpt(text: str, max_chars: int) -> str:
    text = normalize_whitespace(text)
    if len(text) <= max_chars:
        return text
    truncated = text[: max_chars - 3].rsplit(" ", 1)[0]
    if not truncated:
        truncated = text[: max_chars - 3]
    return truncated + "..."


def rank_clusters(clusters: list[Cluster], terms: list[str], limit: int) -> list[dict]:
    ranked = []
    for cluster in clusters:
        score = text_score(cluster.title, terms) * 3.0 + text_score(cluster.body, terms)
        if score <= 0:
            continue
        summary = cluster.body.split("\n| Pattern", 1)[0].strip()
        ranked.append(
            {
                "title": cluster.title,
                "score": round(score, 2),
                "modules": cluster.modules,
                "why": truncate_excerpt(summary or cluster.body, 280),
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]


def rank_patterns(patterns: list[PatternEntry], terms: list[str], limit: int) -> list[dict]:
    ranked = []
    for pattern in patterns:
        score = text_score(pattern.name, terms) * 3.0 + text_score(pattern.section, terms)
        if score <= 0:
            continue
        ranked.append(
            {
                "name": pattern.name,
                "module": pattern.module,
                "section": pattern.section,
                "score": round(score, 2),
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    deduped = []
    seen = set()
    for item in ranked:
        key = (item["name"], item["module"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def rank_modules(
    modules: dict[int, ModuleMeta],
    terms: list[str],
    top_clusters: list[dict],
    top_patterns: list[dict],
    limit: int,
) -> list[dict]:
    cluster_bonus = Counter()
    pattern_bonus = Counter()

    for cluster in top_clusters:
        for module_number in cluster["modules"]:
            cluster_bonus[module_number] += 5.0

    for pattern in top_patterns:
        pattern_bonus[pattern["module"]] += 4.0

    ranked = []
    for module in modules.values():
        text = " ".join([module.title, module.summary, module.se_parallel, " ".join(module.patterns)])
        lexical_score = text_score(text, terms) * 2.0
        routing_score = cluster_bonus[module.number] + pattern_bonus[module.number]
        score = lexical_score + routing_score
        if routing_score == 0 and lexical_score < 12.0:
            continue
        if score <= 0:
            continue
        ranked.append(
            {
                "number": module.number,
                "title": module.title,
                "path": module.path,
                "builds_on": module.builds_on,
                "summary": module.summary,
                "se_parallel": module.se_parallel,
                "score": round(score, 2),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]


def select_prerequisites(modules: dict[int, ModuleMeta], top_modules: list[dict]) -> list[dict]:
    prerequisites = []
    selected = {item["number"] for item in top_modules}
    seen = set()
    for module_item in top_modules:
        module = modules[module_item["number"]]
        prereq_numbers = parse_module_number_list(module.builds_on)
        if len(prereq_numbers) > 3:
            prereq_numbers = prereq_numbers[-3:]
        for prereq in prereq_numbers:
            if prereq in selected or prereq in seen or prereq not in modules:
                continue
            prereq_module = modules[prereq]
            prerequisites.append(
                {
                    "number": prereq_module.number,
                    "title": prereq_module.title,
                    "path": prereq_module.path,
                    "why": f"Direct prerequisite for Module {module.number}",
                }
            )
            seen.add(prereq)
    return prerequisites


def build_excerpts(course_root: Path, modules: dict[int, ModuleMeta], top_modules: list[dict], terms: list[str], max_chars: int) -> list[dict]:
    excerpts = []
    for module_item in top_modules:
        module = modules[module_item["number"]]
        content = (course_root / module.path).read_text(encoding="utf-8")
        sections = split_module_sections(content)
        ranked_sections = []
        for title, body in sections:
            score = text_score(title, terms) * 2.5 + text_score(body, terms)
            ranked_sections.append((score, title, body))
        ranked_sections.sort(key=lambda item: item[0], reverse=True)
        chosen = [section for section in ranked_sections if section[0] > 0][:2]
        if not chosen:
            chosen = ranked_sections[:1]

        excerpts.append(
            {
                "module": module.number,
                "title": module.title,
                "path": module.path,
                "sections": [
                    {
                        "heading": title,
                        "excerpt": truncate_excerpt(body, max_chars),
                    }
                    for _, title, body in chosen
                ],
            }
        )
    return excerpts


def render_markdown(packet: dict) -> str:
    lines = []
    lines.append("# Retrieval Packet")
    lines.append("")
    lines.append(f"- Query: {packet['query']}")
    lines.append(f"- Course root: `{packet['course_root']}`")
    lines.append(f"- Query terms: {', '.join(packet['query_terms']) or '(none)'}")
    lines.append("")

    lines.append("## Problem Clusters")
    if packet["clusters"]:
        for item in packet["clusters"]:
            modules = ", ".join(f"Module {number}" for number in item["modules"]) or "None"
            lines.append(f"- **{item['title']}** (score {item['score']})")
            lines.append(f"  Modules: {modules}")
            lines.append(f"  Why: {item['why']}")
    else:
        lines.append("- No strong cluster match found.")
    lines.append("")

    lines.append("## Candidate Patterns")
    if packet["patterns"]:
        for item in packet["patterns"]:
            lines.append(
                f"- **{item['name']}** — Module {item['module']} "
                f"({item['section']}, score {item['score']})"
            )
    else:
        lines.append("- No strong pattern match found.")
    lines.append("")

    lines.append("## Recommended Modules")
    if packet["modules"]:
        for item in packet["modules"]:
            lines.append(f"- **Module {item['number']}: {item['title']}** (score {item['score']})")
            lines.append(f"  Path: `{item['path']}`")
            lines.append(f"  Builds on: {item['builds_on']}")
            lines.append(f"  SE parallel: {item['se_parallel']}")
            lines.append(f"  Summary: {item['summary']}")
    else:
        lines.append("- No strong module match found.")
    lines.append("")

    lines.append("## Direct Prerequisites")
    if packet["prerequisites"]:
        for item in packet["prerequisites"]:
            lines.append(
                f"- **Module {item['number']}: {item['title']}** "
                f"(`{item['path']}`) — {item['why']}"
            )
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## Excerpts")
    if packet["excerpts"]:
        for item in packet["excerpts"]:
            lines.append(f"### Module {item['module']}: {item['title']}")
            lines.append(f"Path: `{item['path']}`")
            for section in item["sections"]:
                lines.append(f"- **{section['heading']}**: {section['excerpt']}")
            lines.append("")
    else:
        lines.append("- No excerpts available.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_packet(course_root: Path, query: str, top_clusters: int, top_patterns: int, top_modules: int, max_chars: int) -> dict:
    index_text = (course_root / "_index.md").read_text(encoding="utf-8")
    patterns_text = (course_root / "patterns-index.md").read_text(encoding="utf-8")

    modules = parse_module_details(index_text)
    clusters = parse_clusters(index_text)
    patterns = parse_patterns(patterns_text)

    terms = query_terms(query)
    ranked_clusters = rank_clusters(clusters, terms, top_clusters)
    ranked_patterns = rank_patterns(patterns, terms, top_patterns)
    ranked_modules = rank_modules(modules, terms, ranked_clusters, ranked_patterns, top_modules)
    prerequisites = select_prerequisites(modules, ranked_modules)
    excerpts = build_excerpts(course_root, modules, ranked_modules, terms, max_chars)

    return {
        "query": query,
        "query_terms": terms,
        "course_root": str(course_root),
        "clusters": ranked_clusters,
        "patterns": ranked_patterns,
        "modules": ranked_modules,
        "prerequisites": prerequisites,
        "excerpts": excerpts,
    }


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Architecture question or problem statement.")
    parser.add_argument(
        "--course-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Path to the course repository root.",
    )
    parser.add_argument("--top-clusters", type=int, default=3, help="Number of problem clusters to return.")
    parser.add_argument("--top-patterns", type=int, default=8, help="Number of patterns to return.")
    parser.add_argument("--top-modules", type=int, default=4, help="Number of modules to return.")
    parser.add_argument(
        "--max-chars-per-excerpt",
        type=int,
        default=500,
        help="Maximum characters per excerpt section.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    course_root = Path(args.course_root).resolve()
    required_files = [course_root / "_index.md", course_root / "patterns-index.md"]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        print(f"Missing required course files: {', '.join(missing)}", file=sys.stderr)
        return 1

    packet = build_packet(
        course_root=course_root,
        query=args.query,
        top_clusters=args.top_clusters,
        top_patterns=args.top_patterns,
        top_modules=args.top_modules,
        max_chars=args.max_chars_per_excerpt,
    )

    if args.format == "json":
        print(json.dumps(packet, indent=2))
    else:
        print(render_markdown(packet), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
