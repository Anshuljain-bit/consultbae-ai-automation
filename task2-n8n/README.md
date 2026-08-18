# Task 2 - n8n Automation

## Status

Task 2 is complete. The exported n8n workflow is committed at `task2-n8n/workflow.json`.

## Requirement

Build one no-code/low-code automation using n8n, Make, or Zapier and export the workflow JSON into this repository.

## Workflow Overview

The workflow is named `ConsultBae - CSV Deduplication + Alerts`.

- Trigger: `Webhook - CSV Upload3` receives a POST request with a CSV file.
- File handling: `Prepare CSV Binary3` normalizes the binary input name and `Extract CSV3` parses the CSV with a header row.
- Existing data lookup: `Read Existing Rows` reads the configured Google Sheet.
- Duplicate detection: `Detect Duplicates` normalizes email values and phone digits, then flags rows already present in the sheet.
- Duplicate branch: `Duplicate Found?2` routes duplicate records to a Gmail alert node.
- New-candidate branch: `Summarize Candidate` uses OpenAI to generate a concise recruiter summary.
- Output: `Merge Summary Into Row` adds the generated summary, then `Write Results to Sheet` appends the row to Google Sheets.

## Files

- `task2-n8n/workflow.json`: exported n8n workflow JSON.
- `task2-n8n/screenshots/`: optional screenshots of the workflow canvas and test run.

## Import Steps

1. Open n8n.
2. Choose **Import from File**.
3. Select `task2-n8n/workflow.json`.
4. Reconnect credentials for Google Sheets, Gmail, and OpenAI in your own n8n workspace.
5. Confirm the target Google Sheet and duplicate alert email are correct.
6. Run a test execution with a CSV that includes `Full Name`, `Email`, `Phone`, `City`, `Experience (Years)`, `Current CTC`, `Applied Date`, and `Skills` columns.

## Required Configuration

The committed export does not include OAuth tokens, API keys, or execution data. After importing, configure these values in n8n:

- Google Sheets OAuth credential for reading and appending applicant rows.
- Gmail OAuth credential for duplicate alerts.
- OpenAI credential for candidate summary generation.
- Target Google Sheet used by `Read Existing Rows` and `Write Results to Sheet`.
- Recipient email address used by the duplicate alert node.

Do not commit real OAuth tokens, API keys, or n8n execution data.
