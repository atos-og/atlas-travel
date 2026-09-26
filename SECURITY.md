# Security

Atlas is a private prototype. Never publish `.env`, tokens, real phone numbers, raw payloads, conversation databases, or private logs in commits or issues. Use synthetic data to reproduce failures. Revoke exposed credentials with the provider; removing a file does not erase Git history.

Incoming events require a valid signature, the expected business phone-number ID, and an allowlisted sender. Replies are disabled by default. Data in `work/` remains until manually deleted with the server stopped; automatic retention expiry is not implemented.

Hosted language interpretation is disabled by default. When enabled, Atlas sends only the current traveler message and limited step context to Groq. Do not enable it for users who have not received the applicable privacy notice. The model cannot directly invoke providers or send a response: schema validation, an intent allowlist, a confidence gate, conversation validators, and deterministic fallback remain in the application. Never expose `GROQ_API_KEY` in code, logs, screenshots, frontend assets, or commits.

Report vulnerabilities through a private maintainer channel or GitHub private vulnerability reporting if available. Never include secrets in a public issue.
