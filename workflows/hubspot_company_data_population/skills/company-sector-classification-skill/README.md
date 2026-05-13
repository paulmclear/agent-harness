# Company Sector Classification Skill

Minimal skill for classifying companies into a controlled financial-services sector and sub-sector taxonomy.

## Files

- `SKILL.md` – agent instructions, workflow and output schema.
- `references/sector_taxonomy.yaml` – approved sector/sub-sector mapping and keyword reference.

## Usage

Provide the agent with a company name and, where available, jurisdiction or context. The agent should research the company using public sources, compare the business activity to the reference taxonomy, and return the JSON output specified in `SKILL.md`.
