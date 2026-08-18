# Scalability Plan - 5,000 Worker Weekend Launch

The demo app is suitable for a take-home assignment, but a weekend launch to 5,000 workers would stress uploads, storage, CPU-heavy audio analysis, duplicate handling, and support operations.

## Likely Failure Points

1. Upload traffic: mobile users may submit large files at the same time, causing slow requests and timeouts.
2. File storage: local server disk can fill, and files disappear if the app server is replaced.
3. Database connections: synchronous requests can exhaust the MySQL connection pool during bursts.
4. Concurrent requests: Flask should run behind a production WSGI server with multiple workers, not the development server.
5. Large files: long or high-bitrate recordings can exceed request limits and raise storage cost.
6. Duplicate submissions: users may retry, refresh, or submit multiple recordings after uncertain network failures.
7. Failed uploads: partial uploads need clear retry behavior and cleanup.
8. Retry strategy: retries need idempotency keys so they do not create duplicate rows.
9. Background processing: FFmpeg analysis should not block the upload request.
10. Audio metadata extraction: CPU spikes from concurrent FFmpeg jobs can slow the app.
11. Queue architecture: analysis jobs need retry counts, dead-letter handling, and operator visibility.
12. Database indexing: phone, campaign/task ID, status, and created-at indexes are needed for review workflows.
13. Object storage: audio should move to S3, Cloudflare R2, GCS, or similar storage using pre-signed upload URLs.
14. Monitoring and logging: upload failures, analysis failures, queue depth, latency, file sizes, and storage cost should be tracked.
15. Rate limiting: per-phone/IP limits reduce accidental retry storms and abuse.
16. Security: uploads need type/size validation, private buckets, signed playback URLs, and secret-managed credentials.
17. Cost control: duration caps, compression/transcoding, retention policies, and cleanup jobs keep storage and compute predictable.
18. Backup and recovery: database backups and object-storage lifecycle/versioning protect submissions.

## Proposed Production Architecture

Use the backend to create an upload intent, then let the browser upload audio directly to object storage with a pre-signed URL. After upload completion, the frontend calls the API to create a submission row with an idempotency key, normalized phone, campaign/task ID, storage key, and status `pending_analysis`.

A queue worker processes audio asynchronously: download or stream from object storage, run FFmpeg metadata extraction, update the database, and mark the job `complete` or `failed`. Failed jobs should retry with backoff and move to a dead-letter queue after repeated failures.

The database should add campaign/task tables and a unique key such as `(campaign_id, normalized_phone)` or `(campaign_id, normalized_phone, attempt_number)` depending on whether replacements are allowed. Reviewers need filters for failed analysis, duplicate phones, poor quality, silence/low loudness, and pending submissions.

For operations, run the API behind a load balancer, store secrets in a managed secret store, use managed MySQL with backups, send logs/metrics to a monitoring system, and alert on elevated upload failures, analysis failures, queue age, database errors, and storage growth.
