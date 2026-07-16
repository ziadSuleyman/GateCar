# GateCar Platform Audit

**Scope:** production server (`76.13.151.203`), the `gatecar` Frappe app, and the Desk UI.

**Status:** ✅ fixed or verified · ⏸️ requires live-server approval · 🔲 open

This document records verified findings and current progress. It intentionally omits session history and duplicate observations.

## Executive summary

GateCar is reachable and usable, but production is still operated like a development environment. The highest risks are missing backups, disposable container data, the Frappe development server, weak credentials, manual deployment, and no company-owned repository or CI/CD pipeline.

The local environment is available as a staging bench. Code and database changes still need to be committed, tested, and reconciled with production before deployment.

## 1. Current progress

### ✅ Fixed or verified locally

- **Car status indicators:** the Car list indicator now uses the stored Car status, so a maintenance-threshold warning cannot contradict the status pill. Maintenance row highlighting remains separate.
- **Phone fields:** phone controls and read-only fetched values use LTR direction and isolated bidi rendering; authenticated light/dark Playwright checks passed.
- **Dark controls:** dark-theme read-only values and signature canvases have explicit readable surfaces and borders; authenticated Playwright checks passed.
- **Banner consolidation:** new role workspaces now use the shared `gate-car-banner` block instead of embedding another green banner; tracked workspace fixtures were updated similarly.
- **Regression coverage:** 6 static UI contract tests pass with `python -m pytest -q tests/test_platform_ui_contracts.py`; authenticated Playwright checks pass for dark and light phone/read-only/sidebar states; `node --check`, Python compilation, and `git diff --check` also pass.
- **Local refactor:** workspace creation in `setup_data.py` was split into small helpers without changing its generated IDs or records.
- **Arabic UI:** Admin Dashboard title and date-range validation now use Frappe translation/indicator APIs.
- **Security:** `get_car_activity_html` now checks Car read permission in `gatecar/api.py`.
- **Security:** public document share links now expire after 30 days.
- **Workspace fixtures:** all four tracked Gate Cars workspaces now reference the exported `gate-car-banner` Custom HTML Block; the complete live Custom HTML Block set is exported locally.
- **Navigation:** `home_page = "desk/gate-cars"` and `/` redirects to `/desk/gate-cars`.
- **Car Booking:** removed refresh-time field mutation that made records dirty on open.
- **Car Receipt:** removed refresh-time inspection mutation and corrected remaining-balance calculation.
- **Car Statistics:** added live statistics calculation and refresh behavior without marking the single dirty.
- **Branch Dashboard:** System Managers use company-wide dashboard methods; other users remain branch-scoped.
- **Dead links:** removed confirmed `Car Maintenance` and `Oil Change` sidebar links.
- **Data cleanup:** removed confirmed junk branch, fleet, employee/shift-assignment, and duplicate private workspace records. GC-002 was moved out of the junk fleet first.
- **Arabic UI:** added bounded translations for frequently encountered core labels and messages. Full Frappe translation coverage is not available in this installation.
- **Server scripts:** enabled locally with `server_script_enabled = 1`; production must be checked separately.
- **Dark sidebar UI:** the sidebar uses a dark emerald surface, the selected tab flushes with Frappe’s `--bg-color`, and the original curved light-theme geometry is preserved.
- **Sidebar interaction:** non-selected hover styling is disabled. The Frappe Users sidebar and workspace selector header remain neutral, while Gate Cars navigation items retain selected-tab curves.
- **Dark page header:** uses a dark-to-emerald gradient from the logo side toward the left.

### ⚠️ Local and uncommitted

The following changes are in the working tree and are not yet committed:

- `gatecar/api.py`
- `gatecar/fixtures/workspace.json`
- `gatecar/hooks.py`
- `gatecar/setup_data.py`
- `gatecar/fixtures/custom_html_block.json`
- Car Booking, Car Receipt, Car Statistics, Admin Dashboard, and Branch Dashboard code
- `gatecar/public/css/gatecar.css`
- `gatecar/gate_cars/doctype/car/car.js`
- `tests/test_platform_ui_contracts.py`
- deletion of `gatecar/public/css/admin_dashboard.css`

Verification note: the focused static tests pass. The host Python environment still lacks importable `frappe`; the local Frappe container was started, GateCar assets were rebuilt, and `bench --site gatecar.localhost run-tests --app gatecar` completed without an error. No production changes were made.
- local audit artifact rules in `.gitignore`

A read-only production inspection was completed on `76.13.151.203`. The complete current `Custom HTML Block` set was exported into the local fixture; no production data was modified. The live private workspace `مبيعات` for `saeed@gatecar.com`, generic workspaces, and pricing-doctype records remain database-only until approved for reconciliation.

## 2. Production and infrastructure risks

| Risk | Status | Required action |
|---|---:|---|
| No off-box backups for database and uploaded files | 🔴 🔲 | Configure nightly `bench backup --with-files` and copy backups off-server. |
| Production runs `bench start` with developer mode and watchers | 🔴 🔲 | Use production Frappe Docker images or gunicorn/supervisor; set `developer_mode: 0`. |
| MariaDB root password is `123` | 🟠 🔲 | Change it and rotate any dependent configuration. |
| Single CPU runs database, Redis, web, workers, scheduler, socketio, and watchers | 🟠 🔲 | Remove production watchers first; size the server after measuring. |
| No reliable staging-to-production workflow | 🔴 ⏸️ | Use this local bench as staging and deploy versioned builds. |
| Repository is under a personal GitHub account | 🔴 🔲 | Transfer it to a company-owned organization. |
| No CI/CD | 🟠 🔲 | Add linting, tests, build, and controlled deployment. |
| Configured gunicorn workers are unused by the dev server | 🟡 🔲 | Resolved by moving to a production server. |
| CSS cache-busting is not implemented | 🟢 🟡 | Reviewed locally; no custom cache layer added because Frappe’s asset build/versioning strategy must be verified with the bench build before changing hooks. |
| TLS/HTTPS through Caddy | ✅ | No action currently required. |

### Target production state

- Docker volumes contain code, site files, and database data.
- Backups run nightly and are stored off-box.
- Production uses gunicorn or the official production images, with no file watchers.
- Deployments build a versioned image from Git and recreate the application safely.
- No edits are made directly inside a live container.

## 3. Application and code findings

| Finding | Status |
|---|---:|
| Four hardcoded green banner copies remain in database/workspace content | 🟡 code and tracked fixtures consolidated; existing live role workspaces still require a write-enabled reconciliation |
| Fixture filters cover only four named workspaces; Custom HTML Blocks are now exported; generic/private Workspace records remain unportable | 🟡 tracked Gate Cars config exported; hidden/generic workspace export still requires approval |
| Generic ERPNext workspaces and duplicate Selling workspace are hidden live but not fully captured in fixtures | ⏸️ live-only; no production/database access |
| Oversized files and functions remain (`car_booking.js`, `admin_dashboard.js`, `build_vehicle_handover.py`) | 🟡 workspace creation was split in `setup_data.py`; remaining refactor needs dedicated regression coverage |
| AI-attributed historical commits need normal review discipline | 🔲 |
| Core Arabic translations are incomplete because this Frappe install has no bundled catalog | 🟡 bounded translations done; full catalog intentionally deferred |

## 4. UI and functional audit

### Verified findings

- Dead sidebar links previously returned 404s and have been removed.
- `/undefined` still occurs during `/desk` loading. Authenticated Playwright and CDP reproduce one 404 image request; its parser initiator is Frappe’s generated Desk markup at line 119, with no matching GateCar source or final-DOM value.
- Branch dashboard and Car Statistics had incorrect or empty data and were corrected locally.
- Submitted Car Booking and Car Receipt forms previously became dirty on open and were corrected locally.
- Phone fields now require LTR presentation in the RTL interface, including read-only fetched values; static tests pass and authenticated dark-theme Playwright verification measured `direction: ltr` and `text-align: left` on both fetched phone controls.
- Car status indicators now have one source of truth; static regression coverage passes.
- Dark-theme read-only controls and signature canvases now have explicit styling; authenticated Playwright verification measured the configured dark read-only surface and light signature canvas.
- Escaped error text still requires a reproducible failing message; tracked source contains newline escapes only in intentional WhatsApp/HTML payloads.
- Core Frappe/ERPNext labels remain partly English. Continue bounded, high-frequency translations rather than attempting a full catalog manually.
- Empty private workspaces, placeholder records, and near-duplicate pricing doctypes remain architectural/data-cleanup debt.

### Explicitly deferred

- `/undefined` trace remains open. Authenticated Playwright reproduces the single 404 image request; CDP identifies Frappe’s generated Desk markup (line 119) as the parser initiator, and no `/undefined` exists in GateCar source or final DOM.
- Export/hide generic and private workspaces: production read-only inspection found private `مبيعات` for `saeed@gatecar.com`; changing it requires approval/write access.
- Remove or consolidate the four live pricing doctypes (`Price Package`, `Price_pacage_monthly`, `Price_Package_Over`, `price_packge`): dependencies and migration target require approval.
- Placeholder-record cleanup and duplicate pricing-doctype removal until records and dependencies are inspected.
- Role-specific home pages.
- English/Arabic naming cleanup.
- Default ERPNext icon redesign.
- Responsive sidebar and workspace-launcher redesign.
- Shortcut semantics, collapsed dashboard sections, currency configuration, and empty workspace polish.
- Full core Arabic translation coverage.
- Consolidation of the four existing database-stored banner copies; new code and tracked fixtures now use the shared block.

## 5. Sidebar and theme progress

Current `gatecar/public/css/gatecar.css` keeps the original light-theme sidebar geometry and adds dark-mode overrides:

- Light theme: original mint sidebar and curved active item remain unchanged.
- Dark theme: sidebar uses vibrant dark emerald `#123d29`.
- Selected item uses Frappe’s `var(--bg-color)` so it flushes with the page.
- Curved cutouts use the same page-background variable.
- Non-selected hover backgrounds are disabled in both themes.
- The Gate Cars workspace selector header does not receive active-tab curves when opened.
- The Frappe Users contextual sidebar does not receive hover or active-tab decoration.
- Dark page header fades from a darker green near the logo into the sidebar green.

Assets must be rebuilt after CSS changes:

```bash
bench build --app gatecar
```

## 6. Production-to-local reconciliation

Production is currently the source of truth for changes not present in this checkout. Read-only SSH inspection was completed; no production files or database records were changed.

1. On production, inspect `apps/gatecar` with `git status` and preserve any uncommitted work.
2. Create a production backup with `bench --site <site> backup --with-files` and download the database and file archives.
3. Restore locally with `bench --site gatecar.localhost --force restore ...`.
4. Reconcile production code/data with the local fixes before committing or deploying. Read-only inspection confirmed the production container runs `bench start`; no production changes were made.
5. Run `bench build --app gatecar`, migrate, clear cache, and verify the critical routes in both themes.

## 7. Recommended order

1. Create and download a verified production backup immediately.
2. Transfer the repository to a company-owned GitHub organization.
3. Move production off `bench start` and developer mode.
4. Add volumes, off-box backups, and a staging deployment workflow.
5. Commit and test the local fixes before any production deployment.
6. Address the remaining application, translation, and data-cleanup items incrementally.
