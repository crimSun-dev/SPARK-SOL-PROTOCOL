## Purpose

Flaxeon's shared memory follows the operator's GitHub-only repos on a schedule, without the operator's PC.

## ADDED Requirements

### Requirement: GitHub-only repos are kept current from the cloud
On a schedule, the cloud job MUST list the repos visible to its tokens. It MUST write one summary per repo that is not cloned on the PC, using the same document format as the PC's indexer. It MUST leave the summaries of repos cloned on the PC unchanged.

#### Scenario: A new repo while the PC is off
- **WHEN** the operator creates a repo and the PC is off
- **THEN** within one schedule interval, Flaxeon's memory has that repo's summary

#### Scenario: Nothing changed
- **WHEN** GitHub matches what Neon holds
- **THEN** the job writes nothing

### Requirement: The cloud job never deletes
The cloud job MUST NOT delete any document. A repo missing from its listing MUST be left to the PC's indexer, because the cloud job's tokens may not see every repo.

#### Scenario: A token without private access
- **WHEN** the token lists only public repos
- **THEN** no summary of a private repo is removed

### Requirement: Public logs carry no memory
The job's output MUST be counts only. It MUST NOT include repo names, descriptions, READMEs or secrets. It MUST exit without changes when its secrets are not set.

#### Scenario: A fork runs the workflow
- **WHEN** the workflow runs without secrets
- **THEN** it reports that nothing was done and touches no store
