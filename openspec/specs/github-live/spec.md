# github-live

## Purpose

Flaxeon's memory and the SPARK SOL galaxy follow the operator's GitHub repos without a hand-started indexer run.

## Requirements

### Requirement: Repo changes trigger an index run
While the SPARK SOL server runs, it MUST compare the operator's repos and their last-push times with the last indexed state at a fixed interval. On any added, removed or pushed repo, it MUST run the indexer, which publishes to Flaxeon's memory and reloads the sky. The first check on a machine MUST only record a baseline.

#### Scenario: A new repo
- **WHEN** the operator creates a repo on GitHub
- **THEN** within one interval plus one index run, Flaxeon's memory has its summary and the galaxy shows its star

#### Scenario: Nothing changed
- **WHEN** a check finds the same repos and push times
- **THEN** no index run starts

### Requirement: Failures do not lose a change
An index run that fails MUST leave the last indexed state unchanged, so the next check runs it again. A check that cannot reach GitHub MUST be logged and MUST change nothing.

#### Scenario: GitHub offline
- **WHEN** a check cannot list the repos
- **THEN** the log names the failure and the next check proceeds normally

### Requirement: The passkey stays on this machine and account
The passkey for unattended runs MUST be stored only encrypted for the operator's Windows account on this machine, in a folder git ignores. It MUST be decrypted only into the environment of one index run, and MUST NOT appear in any log, health report or page. Without the store, the watch MUST report that a publish is pending and MUST NOT publish.

#### Scenario: No store
- **WHEN** the encrypted passkey file is missing
- **THEN** the watch logs that a publish is pending and Flaxeon's memory is unchanged

### Requirement: One writer at a time
The indexer MUST refuse to start while another run holds the index, and MUST say so.

#### Scenario: A manual run during a watch run
- **WHEN** the operator starts the indexer while the watch's run is writing
- **THEN** the second run exits and says another run is writing
