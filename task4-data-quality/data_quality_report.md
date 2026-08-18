# Data Quality Report

## Executive Summary

The repository includes three source CSVs:

- `source1_naukri_applicants.csv`: 42 rows.
- `source2_gig_workers.csv`: 32 rows, 31 usable after skipping one blank row.
- `source3_cbnexus_contacts.csv`: 31 rows, 30 usable after skipping one repeated header row.

The Task 1 ingest loads 103 usable source rows into `source_records` and creates 55 canonical people. The main data-quality challenge is that no single identifier exists across all sources: source 1 has email and phone, source 2 has email only, and source 3 has phone only.

## Issue 1 - No Shared ID

### Problem

The three systems do not share a universal person ID.

### Example

Source 2 has `email_id` but no phone column. Source 3 has `Phone Number` but no email column.

### Impact

Records cannot be merged safely by a single primary key.

### Detection

Column inspection of the three CSV headers.

### Resolution

The pipeline matches by normalized email first, normalized phone second, and exact normalized name plus canonical city only when one safe candidate exists.

### Reason for Decision

Strong identifiers reduce false positives. Name/city is only used when unambiguous.

## Issue 2 - Mixed Phone Formats

### Problem

Phone numbers appear with different prefixes and punctuation.

### Example

`9000000104`, `919000000143`, `+91-9000000131`, and `09000000287`.

### Impact

The same phone could be treated as multiple people without normalization.

### Detection

Inspection of source 1 and source 3 phone fields.

### Resolution

Phones are stripped to digits, local leading zeroes are removed, Indian `91` prefixes are normalized, and valid 10-digit numbers are stored as `+91XXXXXXXXXX`.

### Reason for Decision

The dataset appears to use Indian phone numbers, so E.164-style normalization gives stable matching keys.

## Issue 3 - Email Casing

### Problem

Email addresses use inconsistent casing.

### Example

`DEEPAK.NAIR44@EXAMPLE.COM` and uppercase source 2 email variants.

### Impact

Case-sensitive matching would miss duplicate people.

### Detection

Inspection of source 1 and source 2 email fields.

### Resolution

Emails are trimmed, lowercased, and validated for a basic `@` plus domain pattern before matching.

### Reason for Decision

Email local-part casing is rarely meaningful in operational systems, and lowercasing is appropriate for this assignment's deduplication workflow.

## Issue 4 - City Variants And Whitespace

### Problem

Cities include casing differences, aliases, and trailing spaces.

### Example

`Bangalore`, `bangalore`, `Bengaluru`, `GURGAON`, `gurugram `, `Delhi`, `New Delhi`, `Delhi NCR`, and `Noida `.

### Impact

Name plus city matching and reporting would fragment across equivalent locations.

### Detection

Unique city value review across all three CSV files.

### Resolution

Cities are trimmed and mapped to canonical values such as `Bengaluru`, `Gurugram`, `Delhi NCR`, `Noida`, and `Pune`.

### Reason for Decision

Only obvious aliases present in the supplied data are mapped.

## Issue 5 - Blank Source Row

### Problem

Source 2 contains a fully blank row.

### Example

`,,,,,`

### Impact

Loading it would create an invalid person or noisy issue record.

### Detection

The source 2 reader checks whether every field in a row is blank.

### Resolution

The blank row is skipped.

### Reason for Decision

There is no usable person data to preserve.

## Issue 6 - Shifted Source 2 Row

### Problem

One source 2 row has fields shifted into the wrong columns.

### Example

The row containing `react, javascript, mysql` appears under `email_id`, while the actual email appears under `worker_name`.

### Impact

Without repair, the row would lose the worker name, email, rate, status, and skills.

### Detection

The pipeline detects a source 2 row where `worker_name` looks like an email and `location` looks like a rate.

### Resolution

The row is shifted back into the expected source 2 columns and marked with `repaired shifted source2 row`.

### Reason for Decision

The pattern is specific and recoverable, so repair preserves a valid source record without pretending the row was clean.

## Issue 7 - Repeated Header Row

### Problem

Source 3 contains a repeated header inside the data.

### Example

`Name,Phone Number,City,Verified,Projects Completed`

### Impact

The repeated header could become a fake person record.

### Detection

The source 3 reader checks for `Name` in the `Name` column after trimming and lowercasing.

### Resolution

The repeated header row is skipped.

### Reason for Decision

It is metadata, not a person.

## Issue 8 - Mixed Date Formats

### Problem

Source 1 application dates use several formats.

### Example

`24-07-2026`, `2026-08-08`, `7 Jul 2026`, and `08/21/2026`.

### Impact

Dates could parse incorrectly or fail ingestion.

### Detection

Review of source 1 `Applied Date` values.

### Resolution

The parser tries explicit date formats before falling back to pandas parsing.

### Reason for Decision

Explicit formats make the expected interpretation visible. Slash dates are treated as month/day/year because examples include days greater than 12.

## Issue 9 - Mixed Rate Units

### Problem

Source 2 rates mix hourly and monthly values.

### Example

`1415/hr` and `15k/month`.

### Impact

Rates cannot be compared as one raw number.

### Detection

Review of source 2 `rate` values.

### Resolution

The pipeline stores `gig_rate_amount` and `gig_rate_period` separately.

### Reason for Decision

Keeping the period prevents hourly and monthly rates from being conflated.

## Issue 10 - Mixed Current CTC Scale

### Problem

Source 1 `Current CTC` appears to mix full annual amounts and small decimal lakh-style values.

### Example

`417964` appears alongside `4.2`, `8.3`, and `11.2`.

### Impact

Parsing all values as integers would turn `4.2` into `4`, losing the likely intended salary scale.

### Detection

Review of `Current CTC` values showed both six/seven-digit values and small decimals.

### Resolution

The parser treats values below `1000` as lakhs and converts them to rupee-like annual amounts. Larger values are rounded as already-annual amounts.

### Reason for Decision

The mixed scale is visible in the data, and preserving comparable annual values is more useful than truncating decimals. This remains an assumption because the CSV does not include a unit column.

## Issue 11 - Duplicate Identities

### Problem

Some people appear multiple times across sources or within source 1.

### Example

`R. Verma` and `Rohit Verma` share the same email/phone. `Nikhil Chopra` appears with an alternate email but the same phone.

### Impact

Duplicates would inflate person counts and split skills/source history.

### Detection

Exact normalized email and phone matching during ingestion.

### Resolution

Records are merged into one canonical person when exact email or phone matches. Alternate emails and phones are retained in identifier tables.

### Reason for Decision

Email and phone are strong enough identifiers for this assignment's merge.

## Issue 12 - Same Name Collision Risk

### Problem

Some rows share names and cities but have conflicting identifiers.

### Example

`Arjun Mehta` appears in Noida with different phone numbers.

### Impact

Loose fuzzy matching could merge different people.

### Detection

Matching review of name/city candidates with phone conflicts.

### Resolution

The pipeline does not auto-merge name/city candidates when phone conflicts are present or when more than one candidate exists.

### Reason for Decision

False positives are more damaging than leaving a possible duplicate for manual review.

## Issue 13 - Value Casing And Skills

### Problem

Statuses, booleans, and skills use inconsistent casing and spacing.

### Example

`Active`, `ACTIVE`, `active`, `Y`, `yes`, `No`, `REST APIs`, and `rest apis`.

### Impact

Aggregations and filters would fragment equivalent values.

### Detection

Review of source 2 status, source 3 verified values, and skill lists.

### Resolution

Statuses are lowercased, booleans are parsed to true/false, and skills are lowercased, trimmed, and deduplicated.

### Reason for Decision

These are deterministic representation differences, not meaningful domain differences.

## Matching Challenges

The hard matching case is source 2 versus source 3: one side lacks phone and the other lacks email. The pipeline therefore only falls back to name plus canonical city when it has exactly one candidate and no identifier conflict.

## Missing Data

Source 2 lacks phone numbers. Source 3 lacks email addresses. Some rows contain invalid or missing values after parsing; rows without a usable name are not imported as people.

## Formatting Inconsistencies

Phone numbers, city names, email casing, dates, CTC scale, rates, statuses, booleans, and skill tags all require normalization.

## Duplicate Records

Confirmed duplicates are merged by exact normalized email or phone. The pipeline stores all source lineage in `source_records` so merged people remain auditable.

## Conflicting Records

Potential same-name conflicts are not merged unless a stronger identifier supports the match. This is intentional to avoid false positives.

## Assumptions

- Indian phone numbers are normalized using country code `+91`.
- Slash dates in source 1 are interpreted as `MM/DD/YYYY`.
- Small decimal `Current CTC` values are interpreted as lakhs.
- City alias mappings are limited to variants visible in the provided data.

## Remaining Limitations

- Task 2 findings cannot be verified until the author adds the real n8n workflow.
- Name/city fallback may leave some true duplicates unmerged when identifiers are missing.
- The CTC unit assumption should be confirmed with the source owner if this were a production migration.
