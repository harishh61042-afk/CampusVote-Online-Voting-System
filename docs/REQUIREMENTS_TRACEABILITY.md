# Implementation traceability

| Requirement | Implementation | Automated verification supplied |
|---|---|---|
| Registration, unique ID, password hash | `auth/routes.py`, `database/schema.sql` | `test_home_login_registration_and_duplicate` |
| Student login, logout, password change | `auth/routes.py`, `templates/auth` | `test_invalid_credentials_and_csrf`, `test_password_change_and_logout` |
| Admin approval, audit | `admin/routes.py` | `test_admin_approval_and_lifecycle` |
| Election scheduling and state | `admin/routes.py`, `db.py` | `test_admin_approval_and_lifecycle`, `test_wrong_candidate_other_election_and_timing` |
| Candidate drafts and edit | `admin/routes.py`, `templates/admin/election_detail.html` | Static template parse and API route checks; no dedicated edit assertion yet |
| Ballot confirmation and receipt | `voting/routes.py`, `student/vote.html`, `main.js` | `test_one_vote_and_neutral_receipt`, `test_receipt_ownership` |
| Atomic vote, duplicate protection | `services/vote_service.py`, schema | `test_concurrent_writes_accept_one`, `test_rollback`, offline verification |
| Published results, tie, zero votes | `services/result_service.py`, `results/detail.html` | `test_publication_visibility_zero_votes_ties`, offline verification |
| Dashboard with real data | `admin/dashboard.html`, `student/dashboard.html` | Template compile and user role tests; visual browser test outstanding |
| Audit table and safe CSV | `admin/routes.py`, `templates/admin/audit.html` | `test_admin_approval_and_lifecycle` partial coverage |
| CSRF and server authorization | `campusvote/__init__.py`, role decorators | `test_invalid_credentials_and_csrf`, `test_student_admin_forbidden_and_escaping` |
| Responsive reference-inspired UI | `static/css/main.css`, `static/js/main.js`, `templates/base.html` | Static asset and template checks; browser visual test outstanding |

**Status:** Tests are delivered for running locally. The offline service checks were executed; Flask endpoint tests were not run during artifact creation due missing Flask dependency. See `TEST_REPORT.md`.
