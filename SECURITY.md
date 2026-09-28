# Security

Atlas is a private prototype. Never publish `.env`, tokens, real phone numbers, raw payloads, conversation databases, or private logs in commits or issues. Use synthetic data to reproduce failures. Revoke exposed credentials with the provider; removing a file does not erase Git history.

Incoming events require a valid signature, the expected business phone-number ID, and an allowlisted sender. Replies are disabled by default. Atlas deletes inbox, delivery-progress, session, preference, and receipt records older than `ATLAS_RETENTION_DAYS`; the bounded default is 30 days. The worker checks retention every six hours. It also creates an online, integrity-checked SQLite snapshot at startup and every 24 hours, retaining `ATLAS_BACKUP_COPIES` per database; the bounded default is seven. Backups live under ignored `work/backups/` and contain the same private data as the source databases, so protect or delete them with the same care.

Hosted language interpretation is disabled by default. When enabled, Atlas sends only the current traveler message and limited step context to Groq. Do not enable it for users who have not received the applicable privacy notice. The model cannot directly invoke providers or send a response: schema validation, an intent allowlist, a confidence gate, conversation validators, and deterministic fallback remain in the application. Never expose `GROQ_API_KEY` in code, logs, screenshots, frontend assets, or commits.

Retention, snapshots, aggregate status, and readiness checks reduce operational risk but are not a managed backup or monitoring service. Before public use, add consent and user-requested deletion, off-device encrypted backups, alerting, stable hosting, and a provider-terms review.

Report vulnerabilities through a private maintainer channel or GitHub private vulnerability reporting if available. Never include secrets in a public issue.
