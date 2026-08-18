# Task 2 - n8n Automation

## Status

Task 2 workflow JSON will be added manually by the author.

The current `workflow.json` file is only a placeholder and is not a working n8n export.

## Requirement

Build one no-code/low-code automation using n8n, Make, or Zapier and export the workflow JSON into this repository.

## Planned Automation

The intended automation is a duplicate-check workflow:

- Trigger: a new CSV file or new row is submitted.
- Input: person name, email if available, phone if available, city, and skills.
- Processing: normalize identifiers in the same spirit as Task 1.
- Database interaction: query the unified database for exact email or exact phone matches.
- Output: create a duplicate alert when a likely existing person is found; otherwise allow the row to continue for review/import.

## Expected Files

- `task2-n8n/workflow.json`: real exported n8n workflow JSON after manual upload.
- `task2-n8n/screenshots/`: optional screenshots of the workflow canvas and test run.

## Import Steps

1. Open n8n.
2. Choose **Import from File**.
3. Select `task2-n8n/workflow.json` after the placeholder has been replaced.
4. Configure credentials for the database and any file source.
5. Run a test execution and add screenshots if required.

## Required Configuration

The workflow should use environment variables or n8n credentials instead of hardcoded secrets:

- `DATABASE_URL` or separate MySQL host/user/password/database credentials.
- CSV source credential if the trigger reads from a cloud drive or webhook.
- Optional notification destination if duplicate alerts are sent to email/Slack.

Do not commit real n8n credentials or execution data.
