# Security protections and limitations

## Implemented safeguards

- Werkzeug salted adaptive password hashing, private-generated Flask session secret, HttpOnly/SameSite cookies, server-side session identity, role decorators and protected POST endpoints.
- A per-session CSRF token on all mutating forms, and response headers for CSP, no-sniff, frame denial and referrer policy.
- Parameterized SQLite queries, unique constraints and foreign keys; `BEGIN IMMEDIATE` for atomic one-vote transactions.
- Voter approval, eligibility, candidate-to-election membership and schedule verified during the write transaction.
- A receipt that contains no candidate choice, and no user identity stored inside ballots.
- No candidate totals exposed before results are published, including to admins; admins see safe participation counts only.
- CSV export restricted to published aggregate results and prefixed when text could become spreadsheet formulas.
- No third-party API keys or CDNs. Admin accounts are set up using a private CLI with no published default password.

## Limitations

- **Not a high-assurance voting system:** No independent audits, hardware protection, public cryptographic verifiability, homomorphic tallying, coercion resistance, authentication of real identities, or secret-ballot certification.
- **Trusted administrator model:** An operator with full host/database access may correlate submission timestamps, database write ordering, backups, or application logs. No claim of perfect anonymity.
- **Local demo:** Flask's built-in development server is not intended for public deployment. For a real campus LAN/server, configure HTTPS, a suitable WSGI server, protection against brute-force sign-in, rate limits, monitoring and access controls.
- **User vetting is manual:** Administrator approval is not proof of identity; no paid OTP, Aadhaar or biometrics are used.
- **Single-host SQLite:** Good for coursework and small local demos; it is not a horizontally scalable distributed datastore.
- **Flask endpoint/browser integration tests in the artifact-authoring environment were not executed (standalone browser layout checks were run)** because Flask was unavailable and could not be installed offline. Follow the test instructions after installing requirements on your Windows machine.
