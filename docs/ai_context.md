# docs/ai_context.md — Olive MMS (Mosque & Madrassa Management System)

> **Status**: GREEN — Phases 0–4 complete; Phase 5 (Events & Inventory) next.
> **Last updated**: August 2026
> **Source of truth for plan**: `docs/plan.md`

---

## 1. Project Overview

Lightweight, single-tenant **Mosque & Madrassa Management System** for tracking members,
donations, fund accounting, madrassa (students/classes/attendance/fees), events, and
distribution inventory. Built with Django + Bootstrap 5 + HTMX + Chart.js.

**Design stance**: "ERP conventions, CRM lightness." Use a service layer, signals,
context-processor navigation, tenant-scoping (single mosque), and CRUD conventions — but keep
a small dependency footprint and single-tenant model. No tax engine, no Celery, no Wagtail for
business pages, fund-based accounting only (initially).

> The `samples/` folder (olive_crm / olive_erp reference codebases) has been **deleted**.
> The "ERP conventions + CRM lightness" design decision was already adopted and is now the
> fixed baseline; the codebase comparison is no longer maintained.

---

## 2. Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Backend | Python 3.11+, Django 5.0.x | venv-based; see `requirements` |
| Frontend | Django Templates, Bootstrap 5.3, Bootstrap Icons, HTMX 1.9, Chart.js, Inter font | CDN or vendored static |
| Database | SQLite (dev) / MySQL 8 (prod) | `django-environ` / `DATABASE_URL` |
| Auth | Custom `core.User` (email login) + Django Groups | `AUTH_USER_MODEL = "core.User"` |
| Config | `django-environ` + `.env` | settings split `base.py`/`dev.py`/`prod.py` |
| Static | `static/css/olive-theme.css`, `static/js/navigation.js`, `templates/base.html` | Two-row nav shell |
| API (deferred) | DRF | Optional Phase 7 |
| Async (deferred) | — | No Celery/Redis initially |

---

## 3. Architecture & Key Decisions

- **Pattern**: Modular monolith — one Django project `config`, domain apps under project root.
- **Tenant scoping**: single mosque per install. `institution.MosqueProfile` singleton provides
  config via `core/utils.get_current_mosque(request)`.
- **Navigation**: data-driven module registry in `core/context_processors.py`; modules filtered
  by `MosqueProfile.enabled_modules`.
- **Business logic**: `services.py` per module + Django `signals.py` for cross-module posting
  (e.g. Donation → Fund Income; FeePayment → Fund Income; StockMovement → StockLevel).
- **Views**: CBV with `LoginRequiredMixin`; querysets scoped by current mosque; forms accept
  mosque kwarg on create/update.
- **UI**: Two-row fixed top nav shell in `templates/base.html` (utility row + module ribbon),
  KPI card grid, inlined critical CSS, mobile hamburger.
- **Accounting scope**: **Fund-based** (Fund, Income, Expense, FundTransfer). Full double-entry
  (`Account`/`JournalEntry`) is an explicit future upgrade, not part of v1.

---

## 4. Module Map (planned)

| Module | Responsibility | Key Models (planned) |
|--------|----------------|----------------------|
| `core` | Auth, dashboard, audit, mixins, nav context processor | `User`, `AuditLog` |
| `institution` | Mosque profile, settings, HIJRI utils | `MosqueProfile` |
| `members` | Families & members | `Family`, `Member` |
| `donations` | Donations, pledges, receipts | `DonationType`, `Donation`, `Pledge` |
| `finance` | Fund accounting | `Fund`, `Income`, `Expense`, `FundTransfer` |
| `madrassa` | Students, classes, attendance, fees | `Class`, `Student`, `Enrollment`, `Attendance`, `Fee`, `FeePayment` |
| `events` | Programs, volunteers, RSVP | `Event`, `EventAttendance` |
| `inventory` | Items, stock, distribution | `Item`, `StockLevel`, `StockMovement` |
| `reporting` | Dashboards & CSV export | (exports, no heavy models) |

---

## 5. Current State

### ✅ Completed
- **Design decision** — lightweight approach adopted: "ERP conventions + CRM lightness"
  (documented in `docs/plan.md`). Reference `samples/` folder deleted; codebase comparison
  removed from the plan.
- **Data model sketch** for all modules (`docs/plan.md` §4).
- **Phased delivery plan** Phases 0–7 (`docs/plan.md` §5).
- **Docs scaffolded**: `docs/plan.md`, `docs/ai_context.md`, `docs/prompt.md`, `.gitignore`.
- **Phase 0 — Foundation (complete)**:
  - Django 5.0.14 scaffold in `.venv`; settings split `config/settings/{base,dev,prod}.py`
    (`django-environ`); `requirements.txt`.
  - `core` app: custom `User` (email login, `AUTH_USER_MODEL="core.User"`), `AuditLog`,
    `TimeStampedModel`, `core/utils.get_current_mosque`, `core/context_processors.navigation_menu`
    module registry, `core` admin (User + AuditLog).
  - Two-row nav shell `templates/base.html` (utility row + module ribbon), `olive-theme.css`,
    `navigation.js`, `favicon.svg`.
  - Login/logout via Django auth views; `templates/core/index.html` dashboard with KPI grid.
  - Seed admin: `admin@olive.local` / `admin123` (dev only).
  - Exit criteria met: `manage.py check` green, two-row nav renders (test client + `runserver`
    boot verified), login flow works.
- **Deployment config (complete)**:
  - `render.yaml` Render blueprint: Postgres + web service (no Redis/Celery), `build.sh`/`run.sh`
    (`PYTHON_VERSION=3.11`, `config.settings.prod`, generated secret, `DATABASE_URL`,
    superuser env vars).
  - `Dockerfile` (python:3.11-slim) + `.dockerignore`.
  - `gunicorn` + `whitenoise` in `requirements.txt`; WhiteNoise wired in
    `config/settings/base.py` (middleware + `STORAGES`).
- **Phase 1 — Institution & Members (complete)**:
  - `institution` app: `MosqueProfile` singleton (`get_solo`, save-time duplicate guard),
    setup wizard + `ProfileEditView`, admin; `core/utils.get_current_mosque` now returns the
    singleton.
  - `members` app: `Family` + `Member` full CRUD (list/create/update/detail/delete), search
    (`q` filter), KPI grid (total/active members, families, volunteers), pagination, HTMX
    deletes returning empty 200 (via `HTMXDeleteMixin.form_valid` — Django 5.0 `BaseDeleteView`
    deletes in `form_valid`, not `delete()`), Django admin.
  - Registered both apps in `INSTALLED_APPS`, URLs, and the nav registry (auto-resolves).
  - Exit criteria met: member add/edit/view/delete verified, search + KPIs verified via test
    client.
- **Modal UX + members hardening (complete)**:
  - Reusable HTMX modal infra: `#genericModal`/`#genericModalBody` in `templates/base.html`,
    partial `templates/includes/htmx_modal_form.html`, `closeModal` listener in
    `static/js/navigation.js`. Buttons `hx-get` forms into the modal body; submit posts back;
    success returns 204 + `HX-Trigger: {"closeModal":"","listChanged":""}`; lists auto-refresh
    via root div `hx-trigger="listChanged from:body"`.
  - `members` and `institution` converted to `HTMXPartialMixin`/`HTMXModalFormMixin`/
    `HTMXDeleteMixin` (`core/mixins.py`); lists split into `templates/*/partials/*_content.html`.
  - Member `phone` + `email` now required (`members/0002`); `Member.whatsapp_number()` /
    `whatsapp_url(message=None)`; WhatsApp links in member list + detail.
- **Phase 2 — Donations (complete)**:
  - `finance` app: `Fund` (with `balance` property aggregating opening/income/expense/transfers),
    `Income` (OneToOne → `donations.Donation`, `on_delete=CASCADE` so donation delete removes
    auto-posted income), `Expense` (status PENDING/APPROVED/REJECTED), `FundTransfer`.
  - `donations` app: `DonationType` (SADQAH/ZAKAT/LILLAH/FITRA/QURBANI/BUILDING/GENERAL via
    `seed_defaults`), `Donation` (auto `receipt_number` `RCP-YYYYMMDD-NNNN` in `save()`),
    `Pledge` (frequency/start_date). `post_donation_to_fund` signal (`donations/apps.py` `ready()`)
    does `Income.objects.update_or_create(donation=instance, ...)`.
  - Donation list with filters (type/method/date range/q) + KPI totals; HTML print receipt view
    (`window.print`); pledge + donation-type management. All with modal add/edit + partial lists.
  - Registered both apps + URLs; migrations applied; `seed_defaults` command (7 types, 4 funds:
    GEN/ZAK/BLD/EDU).
  - Exit criteria met via test client: modal create 204 + trigger, donation→Income posting,
    receipt print, filters/totals, fund balance reflects income, delete cascades income.
- **Money rounding fix + Phase 3 — Finance (complete)**:
  - Fixed SQLite float artifact in `Sum()` aggregates (rendered `5,000.03000000000`): added
    `core.utils.money()` (rounds to 2 dp, `ROUND_HALF_UP`, guards invalid values); applied in
    `Fund.balance`, `total_balance`, and donation/expense/income/transfer totals.
  - `FinanceDashboardView` is now `finance:index`: KPI cards (total balance, month income/expense,
    fund count), per-fund balance table, Chart.js 6-month income-vs-expense bar chart (via
    `json_script`), quick links to Income/Expenses/Transfers/Funds.
  - Expenses: list with filters (fund/status/date range) + KPIs (filtered total, pending,
    approved), modal create/edit, one-click HTMX approve (`ExpenseApproveView` → 204 + `listChanged`).
  - Income: list with filters (fund/date) + manual income entry (IncomeForm, `source` required),
    links auto-posted donation income back to the receipt.
  - FundTransfer: list + modal create with same-fund validation; affects both fund balances.
  - Funds page moved from index to `finance:funds`; nav auto-resolves `finance:index` → dashboard.
  - Exit criteria met via test client: dashboard renders with chart, record expense → pending →
    approve, manual income, transfer moves balances, same-fund blocked.
- **Phase 4 — Madrassa (complete)**:
  - `madrassa` app: `Class` (teacher FK → `members.Member`), `Student` (member/family FKs,
    guardian, admission_date, status), `Enrollment` (unique per student/class/academic_year),
    `Attendance` (PRESENT/ABSENT/LATE/EXCUSED, unique per student/day), `Fee`, `FeePayment`
    (auto `PAY-YYYYMMDD-NNNN` receipt; amount defaults to selected fee in `save()`).
  - `finance.Income.fee_payment` OneToOne (`on_delete=CASCADE`); `post_fee_payment_to_fund`
    signal (`madrassa/apps.py` `ready()`) posts income, falling back to EDU fund; income list
    links fee payments back to the student.
  - Attendance grid (class × date) in `madrassa/attendance.html` + `partials/attendance_grid.html`:
    per-cell status buttons POST `attendance_set` (204 + `attendanceChanged`), grid root
    auto-refreshes KPIs + grid; prev/next date nav; "Mark all present" (`attendance_mark_all`).
  - Madrassa dashboard (student/class/active-enrollment/fee KPIs, class table w/ enrolled counts,
    recent payments); Class/Student/Enrollment/Fee/FeePayment lists with filters + modal CRUD;
    Student detail report card (details, enrollments, attendance + fee history).
  - Registered app + URLs; migrations `madrassa/0001`, `finance/0003`; `madrassa/tests.py`
    (signal posting + EDU fallback, amount default, receipt generation, unique constraints,
    delete cascade) — 7 tests green.
  - Fixes while there: added Chart.js CDN to `base.html` (finance dashboard chart had no library
    loaded); added CSRF meta tag + htmx `configRequest` header wiring in `navigation.js` so
    `hx-post` delete/attendance buttons work in a browser.
  - Exit criteria met via test client: enroll student → take attendance (set + mark-all) → record
    fee → income auto-posted on EDU fund; edge cases (blank capacity, amount default) fixed.

### 🔄 In Progress
- **This session (Prompt 5 — Phase 4 Madrassa)**: done — see below.

### ⏭️ Next (Phase 5 — Events & Inventory)

---

## 6. Conventions & Coding Standards

- **Naming**: Models PascalCase; views `XxxListView`/`XxxCreateView`/`XxxUpdateView`/`XxxDeleteView`/`XxxDetailView`; URL names `module:view`; templates lowercase snake (`donations/donation_list.html`); CSS kebab-case.
- **Money**: `DecimalField` always; display with `{{ value|intcomma }}` and `{% load humanize %}`; run aggregate sums through `core.utils.money()` to round to 2 dp (SQLite float artifacts).
- **Module layout**: `models.py`, `views.py`, `forms.py`, `urls.py`, `admin.py`, optional `services.py`/`signals.py`, `templates/<module>/`, `tests.py`.
- **Scoping**: every list/create view filters via `get_current_mosque(request)`; forms set `instance.mosque` in `form_valid`.
- **Auth**: `LoginRequiredMixin` on all views; permission checks via Django Groups (Admin, Treasurer, Registrar, Teacher, Volunteer).
- **Nav**: only `core/context_processors.py` changes — never hardcode nav in templates.
- **HTMX**: add/edit forms open in `#genericModal` (hx-get → partial; submit posts back; success
  returns 204 + `closeModal`/`listChanged` triggers); deletes return 204 + `listChanged`; list
  roots listen for `listChanged from:body` to auto-refresh.
- **Charts**: guard every Chart.js canvas with `{% if %}` in template + `getElementById` null-check in JS.

---

## 7. What NOT to Change

1. **Design system**: keep the two-row top nav shell and `olive-theme.css` KPI/card tokens.
2. **Single-tenant scoping**: `MosqueProfile` singleton + `get_current_mosque()` — do not introduce
   multi-mosque tenancy in v1.
3. **Fund-based accounting** as the v1 source of truth — don't bolt on full double-entry mid-build.
4. **Custom `core.User`**: don't fall back to the default Django user.
5. **Data-driven navigation** via context processor — don't hardcode the ribbon in templates.
6. **Money as Decimal**: never use float for amounts.

---

## 8. Known Risks / Watch Items

- Scope creep toward full ERP/accounting → keep v1 to fund accounting; upgrade path documented.
- HIJRI calendar: store Gregorian dates; add `institution` HIJRI helpers, no calendar lib in v1.
- Two nav systems (business UI vs Django admin) — business models use Django templates only.
- Attendance UX must be fast (HTMX partial, "mark all present" default) or adoption drops.

---

## 9. Session Protocol (how to use this file)

1. Read `docs/ai_context.md` first (full context), then `docs/plan.md` (phases/exit criteria).
2. When starting/continuing a coding task, keep the **Completed / In Progress / Next** state in
   §5 updated at every milestone.
3. Never start Phase N before Phase N−1 exit criteria pass.
4. On interruption: mark state with exact stopping point (file, line, next action) in §5.

---

*Live document — append changes with date and description. Keep §5 state accurate at all times.*
