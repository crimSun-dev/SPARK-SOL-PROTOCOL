## Purpose

Every skill and experience module on this PC is recallable from Flaxeon's shared memory by name, and visible as its own star on the SPARK SOL galaxy.

## ADDED Requirements

### Requirement: Every skill folder on this PC
The indexer MUST discover skills, meaning folders that contain `SKILL.md`, under `~/.cursor/skills`, `~/.claude/skills`, `~/.claude/plugins`, `~/.gemini/skills`, `~/.codex/skills` and `~/.agents/skills`. It MUST skip dependency, VCS and hidden folders. It MUST NOT treat a `SKILL.md` inside a pruned folder, such as `node_modules`, as a skill.

#### Scenario: A plugin skill
- **WHEN** a skill exists only under `~/.claude/plugins`
- **THEN** it has a document in Flaxeon's shared memory and a star in the Skills region

### Requirement: One capped document per skill
Each skill MUST be one document of kind `skill`. It MUST hold `SKILL.md` first, then that skill's reference `.md` files, scrubbed of secrets, with text kept under Flaxeon's document cap. A skill whose references do not fit MUST name the omitted files at the end. Identical copies of one skill in several folders MUST be one document that lists every location. Same-named skills with different content MUST be separate documents.

#### Scenario: A large skill
- **WHEN** a skill's files exceed the cap together
- **THEN** its document holds the full `SKILL.md` and as many references as fit, and lists the rest by name

#### Scenario: The same skill in two folders
- **WHEN** an identical skill is in `~/.cursor/skills` and `~/.claude/skills`
- **THEN** one document exists, and it names both locations

### Requirement: Experience modules in full
Each experience module MUST be one document of kind `experience` holding its scrubbed text within the cap. Modules found only in `~/.claude/skills/POOL` MUST be included. Files identical to those in `~/.cursor/skills/POOL` MUST NOT be indexed twice.

#### Scenario: A module only in the Claude POOL
- **WHEN** an experience module exists only under `~/.claude/skills/POOL`
- **THEN** it has a document and a star

### Requirement: Published like the summaries
Skill and experience documents MUST be written only by the indexer, through Flaxeon's memory path, with the passkey gate open. They MUST be counted in Neon after writing, and forgotten when their source is gone. They MUST NOT change any other fact or document.

#### Scenario: A skill deleted
- **WHEN** a skill folder is deleted and the indexer runs
- **THEN** its document is forgotten and its star is gone after the galaxy reloads
