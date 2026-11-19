# UI design guide — based on the supplied reference image

The reference image is a bright analytics dashboard with a slim left navigation, top search bar, pill controls, white rounded metric cards, shaded striped columns, a green performance gauge, dense tables, avatars and soft background gradients. CampusVote replaces the store/commerce nouns with election-management concepts while preserving the visual rhythm.

## Color tokens

| UI role | Hex |
|---|---|
| Primary white | `#FFFFFF` |
| Charcoal action/navigation | `#11111F` |
| Emerald/turnout green | `#0AAF65` |
| Soft mint | `#E6FAED` |
| Soft peach | `#FFF1E9` |
| Muted silver gray | `#8D8D98` |
| Hairline border | `#EEEEEF` |

Source: `campusvote/static/css/main.css`, root CSS custom properties. Font: system UI stack, so no network font download is required.

## Layout mapping

- Store logo → custom CampusVote ticked-ballot mark (bundled SVG).
- Sales dashboard side navigation → Admin Dashboard / Elections / Verification / Reports / Audit and student-specific pages.
- Profit overview graph → **Participation Overview**, with actual ballots counted by election, no early candidate-ranking leakage.
- Sales goal gauge → **Voter Turnout**, computed from counted participation and eligible-voter records.
- Recent transaction table → **Recent Elections** or **My Elections**, server-driven and searchable where relevant.
- Top market/product cards → **Pending Approvals**, **Recent Activity**, and **Published Results**.
- Dark/light toggle → persisted preference on each browser.
- Mobile → collapsible sidebar, two-column small KPI strip and vertically stacked cards.

UI breakpoints: 1250, 1070, 850 and 650 px; designed to accommodate desktops and mobile-sized viewports.

## Editing in VS Code

- Change colors, spacing or animations in `campusvote/static/css/main.css`.
- Change dashboard layout in `templates/admin/dashboard.html` and `templates/student/dashboard.html`.
- Change icon shape in `static/images/icons.svg`.
- Change dialog/theme/navigation behavior in `static/js/main.js`.
- Use `templates/base.html` for common sidebar/topbar/flash messages.

No picture from the provided third-party dashboard is copied into the app; the interface is implemented from HTML/CSS/SVG instead of reusing the screenshot as a background.

## Design preview screenshots

`docs/Preview_Desktop.png`, `docs/Preview_Student.png`, `docs/Preview_Voting.png` and `docs/Preview_Mobile.png` show fictional sample numbers rendered by an inlined design preview, **not live election data**. The actual Flask dashboard always queries SQLite. Use `CampusVote_UI_Preview.html` (separately included with your deliverables) for a quick offline visual check.
