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

### Requirement: Deletes only what GitHub confirms
The cloud job MUST delete a GitHub-only summary only when all of these hold:
- no token failed in that run;
- the repo is missing from the listing;
- a direct lookup of that exact repo answers 404, or redirects to a new name.

For a repo that was private, the listing MUST also have shown at least one private repo of that owner. Otherwise the summary MUST be kept.

#### Scenario: A deleted repo while the PC is off
- **WHEN** the operator deletes a repo on GitHub
- **THEN** the next run removes its summary

#### Scenario: A token without private access
- **WHEN** the token lists only public repos
- **THEN** no summary of a private repo is removed

#### Scenario: A renamed repo
- **WHEN** a repo is renamed
- **THEN** the old summary is removed and the new name has its own

### Requirement: Public logs carry no memory
The job's output MUST be counts only. It MUST NOT include repo names, descriptions, READMEs or secrets. It MUST exit without changes when its secrets are not set.

#### Scenario: A fork runs the workflow
- **WHEN** the workflow runs without secrets
- **THEN** it reports that nothing was done and touches no store
