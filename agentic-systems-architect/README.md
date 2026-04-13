# Agentic Systems Architect

Retrieval-first architecture skill for brainstorming, design review, and trade-off analysis when
building agentic systems.

The skill does not preload the full course. It routes a query through `_index.md` and
`patterns-index.md`, then pulls only the most relevant modules and excerpts through the local
retriever.

## Contents

- `SKILL.md`: generic skill instructions
- `scripts/retrieve_course.py`: local retriever over this course repo
- `agents/openai.yaml`: optional Codex/OpenAI UI metadata
- `install-skill.sh`: convenience installer for folder-based skill registries

## Installation

The installer is target-directory based so it can work with any tool that expects skills as
folders on disk.

### Generic install

Copy the skill into a target skill directory:

```bash
./agentic-systems-architect/install-skill.sh --target /path/to/skills
```

Create a symlink instead of copying, which is useful while iterating on the skill locally:

```bash
./agentic-systems-architect/install-skill.sh --target /path/to/skills --link
```

Replace an existing installation:

```bash
./agentic-systems-architect/install-skill.sh --target /path/to/skills --force
```

### Codex example

Install into the local Codex skills directory:

```bash
./agentic-systems-architect/install-skill.sh --target ~/.codex/skills
```

For live iteration without recopying:

```bash
./agentic-systems-architect/install-skill.sh --target ~/.codex/skills --link
```

### Claude or other folder-based setups

If your agent runtime supports folder-based skills, prompts, or slash-command bundles, point the
installer at that directory:

```bash
./agentic-systems-architect/install-skill.sh --target /path/to/that/runtime/skills
```

If the runtime does not have a formal skill installer, you can still use the folder directly:

1. Copy `agentic-systems-architect/` into the runtime's skills or prompts directory.
2. Ensure `SKILL.md` remains at the folder root.
3. Keep `scripts/retrieve_course.py` alongside it so the skill can call the retriever locally.
4. Keep the course repo available on disk so the retriever can read `_index.md`,
   `patterns-index.md`, and the module files.

## Usage

Run the retriever directly:

```bash
./agentic-systems-architect/scripts/retrieve_course.py \
  --query "Review an agent runtime architecture for reliability, security, and evals"
```

JSON output:

```bash
./agentic-systems-architect/scripts/retrieve_course.py \
  --query "How should I secure a long-running autonomous agent?" \
  --format json
```

## Portability Notes

- The skill instructions are generic and do not assume Codex-specific tools.
- The retriever defaults `--course-root` to the repository root that contains the skill folder.
- If you move the skill outside this repo, pass `--course-root /path/to/course` or edit the command
  in `SKILL.md` to match your layout.
