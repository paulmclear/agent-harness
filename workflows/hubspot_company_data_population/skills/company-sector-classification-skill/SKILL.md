### Purpose

Classify a company into a standardised `sector` and `sub_sector` using the reference taxonomy in `references/sector_taxonomy.yaml`.

Use this skill when you are given a company name and need to deduce its business type from public information, then map it to one of the approved sector/sub-sector combinations.

### Inputs

Expected input:

```json
{
  "company_name": "string",
  "jurisdiction": "optional string",
  "known_context": "optional string"
}
```

The `jurisdiction` and `known_context` fields are optional, but should be used where provided to disambiguate companies with similar names.

### Reference file

Use `references/sector_taxonomy.yaml` as the authoritative classification map. Do not invent new sectors or sub-sectors unless the output is explicitly marked as `out_of_taxonomy`.

Each taxonomy entry contains:

- `sector` – the approved top-level sector
- `sub_sector` – the approved sub-sector
- `keywords` – indicative business terms, products, services and phrases associated with that category

### Classification workflow

1. **Identify the company**
   - Use the company name, jurisdiction and any known context to identify the correct legal entity or trading business.
   - If the name is ambiguous, prioritise the entity matching the supplied jurisdiction or context.
   - If ambiguity remains, state this in the output and classify only if there is enough evidence.

2. **Research the business type**
   - Use public web searches where available.
   - Prefer authoritative sources, in this order:
     1. the company’s own website, annual report, investor relations pages or regulatory disclosures;
     2. financial regulator registers or licensing pages;
     3. reputable business information sources;
     4. recent credible news coverage.
   - Capture concise evidence about what the company actually does, not just how it markets itself.

3. **Match to the taxonomy**
   - Compare the researched business activities against the taxonomy keywords.
   - Classify by core business activity, not by incidental products.
   - Prefer the most specific matching sub-sector.
   - Do not treat keyword matching as mechanical: use the keywords as classification signals, then reason from the company’s actual business model.

4. **Resolve overlaps**
   - If a company plausibly fits multiple sub-sectors, choose the sub-sector representing the dominant business activity.
   - Use the following tie-breakers:
     1. regulated/licensed activity, if clear;
     2. revenue-generating core product or service;
     3. primary customer base;
     4. how the company describes its principal business.
   - Record alternative candidates where materially plausible.

5. **Confidence scoring**
   Confidence reflects how certain you are in the *assigned label* — including when the assigned label is `out_of_taxonomy`. It is NOT a score of how satisfying or specific the answer is.

   Return `confidence` as a float between `0.0` and `1.0` (inclusive). Use these bands:
   - `0.80`–`1.00` (high): you are confident in the assigned label. This includes cases where the company is well-known and clearly does not fit the taxonomy — assign `out_of_taxonomy` with high confidence.
   - `0.50`–`0.79` (medium): the label is likely but evidence is incomplete, or multiple adjacent in-taxonomy categories are plausible.
   - `0.00`–`0.49` (low): you genuinely cannot identify the company or cannot determine whether it fits the taxonomy at all. Do NOT use a low score merely because the answer is `out_of_taxonomy`.

   Do not return a string label (e.g. `"high"`); always return a numeric value.

   Worked examples:
   - "KPMG" → `sector: out_of_taxonomy, confidence: 0.95, suggested_sector: "Professional Services", suggested_sub_sector: "Accounting & Audit"` (well-known professional-services firm, clearly not in taxonomy — populate suggested fields).
   - "Salesforce" → `sector: out_of_taxonomy, confidence: 0.95, suggested_sector: "Technology", suggested_sub_sector: "Enterprise Software / SaaS"` (technology company, not financial services).
   - "McKinsey & Company" → `sector: out_of_taxonomy, confidence: 0.95, suggested_sector: "Professional Services", suggested_sub_sector: "Management Consulting"`.
   - "Acme Holdings Ltd" with no public footprint → `sector: out_of_taxonomy, confidence: 0.2, flags: [ambiguous_company_name, insufficient_public_information]` (exception: suggested fields may be omitted when company cannot be identified).

6. **Out-of-taxonomy handling**
   - If the company does not fit the taxonomy, use:
     - `sector`: `out_of_taxonomy`
     - `sub_sector`: `out_of_taxonomy`
   - Explain why no taxonomy category fits.
   - **You MUST always populate `suggested_sector` and `suggested_sub_sector`** whenever `sector` is `out_of_taxonomy`. These fields are not optional — only omit them if the company cannot be identified at all (confidence < 0.3 and `insufficient_public_information` flag set).
   - Use plain, widely-understood business English for the suggestion. Draw on common industry classification vocabularies (GICS sectors, NAICS, SIC) as a guide, but express the result in natural language — not a numeric code.
   - Aim for the level of granularity that would be useful to a sales or research team: broad enough to be meaningful, specific enough to differentiate (e.g. prefer "Professional Services / Management Consulting" over just "Services").
   - Examples of suggested vocabulary for common out-of-taxonomy categories:
     - Professional services: Accounting & Audit, Management Consulting, Legal Services, Recruitment, Public Relations
     - Technology: Enterprise Software, SaaS, Cybersecurity, Cloud Infrastructure, Data Analytics, AI/ML
     - Real Estate: Commercial Real Estate, Real Estate Investment, PropTech
     - Media & Publishing: Digital Media, Broadcasting, Publishing, Marketing & Advertising
     - Healthcare: Healthcare Services, MedTech, Pharmaceuticals, Health Insurance
     - Government / Public Sector: Central Government, Local Government, Regulatory Body, Public Sector Technology
     - Education: Higher Education, EdTech, Professional Training
     - Retail & Consumer: E-commerce, Retail, Consumer Goods, Hospitality, Food & Beverage
     - Energy & Utilities: Energy, Oil & Gas, Utilities, CleanTech / Renewables
     - Infrastructure & Industry: Logistics, Manufacturing, Construction, Transport

### Output format

Return only valid JSON using this schema:

```json
{
   "sector": "string",
   "sub_sector": "string",
   "confidence": 0.85,
   "rationale": "short explanation of the classification decision",
   "flags": ["optional list of relevant flags such as 'ambiguous_company_name', 'insufficient_public_information', 'multiple_business_lines', 'out_of_taxonomy', 'jurisdiction_unclear'"],
   "suggested_sector": "required when sector is out_of_taxonomy — a sector name from outside the taxonomy using plain business English",
   "suggested_sub_sector": "required when sector is out_of_taxonomy — a sub-sector name from outside the taxonomy using plain business English"
}
```

## Output rules

- Use exactly one primary `sector` and one primary `sub_sector`.
- Use sector and sub-sector names exactly as written in the reference file.
- Keep the rationale concise and evidence-led.
- Apply `flags` only when they genuinely apply. Each flag has a strict meaning:
  - `ambiguous_company_name`: the name maps to multiple distinct real entities and you cannot tell which one is meant.
  - `insufficient_public_information`: you searched and there is little or no public information about the company. Do NOT apply this flag when the company is well-known.
  - `multiple_business_lines`: the company has several material business lines spanning different taxonomy categories.
  - `out_of_taxonomy`: the company is identified but does not fit any taxonomy category. Always apply together with `sector: out_of_taxonomy`.
  - `jurisdiction_unclear`: classification depends on regulatory jurisdiction and the jurisdiction cannot be determined.
- If the company is out-of-taxonomy, always populate `suggested_sector` and `suggested_sub_sector` — the only exception is when the company cannot be identified at all.