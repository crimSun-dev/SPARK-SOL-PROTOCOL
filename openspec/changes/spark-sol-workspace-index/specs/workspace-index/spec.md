## Purpose

SPARK SOL keeps a full-text index of the operator's Workspace, pools, skills and GitHub repos on this machine, and gives Flaxeon's shared memory and the galaxy one short summary per project.

## ADDED Requirements

### Requirement: Local full text, four roots
The indexer MUST read only these roots: the Workspace folder that contains F.L.A.X.E.O.N, the CrimSun POOL under `~/.cursor/skills`, `~/.cursor/skills`, and `~/.claude/skills`. Full text MUST stay in a local index on this machine that is never committed or uploaded. The indexer MUST NOT read the PC's Documents, Desktop, Downloads or any other folder outside those roots.

#### Scenario: A file under the Workspace
- **WHEN** a text file under the Workspace is indexed
- **THEN** its scrubbed text is searchable in the local index by the words it contains

#### Scenario: A folder outside the roots
- **WHEN** a file exists only in the PC's Documents folder
- **THEN** it is not in the index

### Requirement: Secrets never enter the index or memory
The indexer MUST skip files whose names mark them as secret holders, such as `.env`, key files, credential files and service-account files, and MUST NOT store their names. In every other file it MUST replace key-shaped strings, private keys and connection strings before storing text or summaries.

#### Scenario: A secret file
- **WHEN** a folder holds `.env` and `config/api_keys.json`
- **THEN** neither name nor content appears in the index or in any summary

#### Scenario: A key inside source code
- **WHEN** a source file contains a string shaped like an API key
- **THEN** the stored text shows a removal marker in its place

### Requirement: Noise is pruned, large files are named only
The indexer MUST prune dependency, VCS and build folders and the pool's duplicate chunk copies. Generated files, text over its size cap, and binaries MUST be stored by name and path only. PDF, Word, PowerPoint and Excel files MUST be stored as extracted text when they have any.

#### Scenario: A dependency folder
- **WHEN** a project contains `node_modules`
- **THEN** nothing under it is indexed

#### Scenario: A scanned PDF
- **WHEN** a PDF has no extractable text
- **THEN** its name and path are still findable

### Requirement: Re-runs are incremental and honest
A re-run MUST skip files whose size and modification time are unchanged, re-index changed files, and remove files that no longer exist.

#### Scenario: Unchanged tree
- **WHEN** the indexer runs twice with no file changes in between
- **THEN** the second run writes no file and reports them unchanged

#### Scenario: A deleted file
- **WHEN** a file is deleted and the indexer runs
- **THEN** that file is no longer in the index

### Requirement: GitHub repos join their projects
The indexer MUST list the repos of the signed-in GitHub account and its organisations, with their README. A repo cloned under the Workspace MUST join that local project. A repo that is not cloned MUST become a project of its own. The indexer MUST NOT clone repos. When GitHub is unreachable, the run MUST continue without it and say so.

#### Scenario: Repo not cloned here
- **WHEN** a repo exists on GitHub but not under the Workspace
- **THEN** it appears as its own project with its README searchable

### Requirement: One summary per project in shared memory
The indexer MUST write exactly one short `repo_index` document per project to Flaxeon's shared memory, through Flaxeon's own memory path, and MUST NOT write full text there. It MUST forget summaries it published earlier for projects that no longer exist, and MUST NOT touch any other document or fact. It MUST report how many summaries were saved, how many were forgotten, and how many were read back from the store after writing.

#### Scenario: Publish succeeds
- **WHEN** a full run publishes summaries
- **THEN** each project has one `repo_index` document in Neon
- **AND** the report's read-back count matches what Neon holds

#### Scenario: A project removed
- **WHEN** a project folder is deleted and the indexer runs again
- **THEN** its summary is forgotten from shared memory

### Requirement: The galaxy shows and searches the projects
Each published summary MUST appear on the galaxy as a star in the Workspace, Pools, Experience or Skills region. SPARK SOL's chat MUST answer questions about project contents from the local index. A run MUST ask a running galaxy to reload, and MUST report when it is not running.

#### Scenario: After a full run
- **WHEN** the indexer finishes and the galaxy is running
- **THEN** the sky shows the project regions without a restart
