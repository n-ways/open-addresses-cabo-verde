# Security

Report a security problem privately to **hello@nways.ng**, with "Security" in the subject. Please do not open a public issue for it.

Tell us what is affected (the registry server, the engine, the data or the published registry), how to reproduce it, and what an attacker could do with it. We aim to acknowledge a report within three working days, keep you informed while we fix it, and credit you in the fix unless you prefer otherwise.

What counts as a security problem here:

- a way to issue, change or retire codes on a server without a valid issuer key, or to exceed a key's daily limit;
- a way to make a server return wrong codes, crash, or reveal its configuration or issuer keys;
- a registry file that the server imports although it does not match `MANIFEST.json`;
- anything in the published data that identifies a person or tells who lives where.

A wrong code, a misplaced entrance or a misclassified building is not a security problem: report it in the N-Ways app ("this is wrong"), where people's agreement corrects it, or open an issue.

## Running a deployment safely

- Serve the API over HTTPS behind a reverse proxy ([server/README.md](server/README.md)).
- Leave `ISSUE_KEYS` empty unless the deployment is the designated issuer; keep issuer keys out of version control and rotate them by restarting with a new list.
- Back up the database of an issuing deployment daily.
- Update to each new registry release; `import` refuses a registry whose files do not match its manifest.
