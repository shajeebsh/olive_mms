# Olive MMS — Mosque & Madrassa Management System — Implementation Plan

> Status: PHASES 0–6 COMPLETE (deployment optional, on demand)
> Last updated: August 2026

---

## 1. Purpose

Build a **lightweight, single-tenant Mosque & Madrassa Management System (MMS)**. The system
tracks members, donations, fund accounting, madrassa students/classes, events, and distribution
inventory — without the heavyweight machinery of a full ERP (no tax engine, no Celery, no
multi-company RBAC).

The design stance is **"ERP conventions, CRM lightness"**: a service layer, Django signals for
cross-module posting, a data-driven context-processor navigation registry, single-tenant
scoping, and a consistent two-row top-nav + KPI-card design system.

---

## 2. Decision: Best Approach for a Lightweight MMS

Adopt the "ERP conventions, CRM lightness" approach. The reference `samples/` codebases
(olive_crm / olive_erp) have been **deleted**; the decisions below are now the fixed baseline.

| Decision | Rationale |
|----------|-----------|
| **Modular monolith** with domain apps | Clear separation of concerns; easy to extend; single deployable |
| **Django 5.0.x** | Modern baseline; maintained patch releases |
| **Single tenant** | One mosque per install. Keep a `MosqueProfile` singleton for config, not multi-tenancy |
| **Service layer + signals** | Donation → receipt → fund ledger, and fee payment → income, benefit from signals/services; keeps views thin |
| **Context-processor module registry** | Navigation stays data-driven; modules toggle on/off via profile settings |
| **Two-row top nav + KPI dashboard + olive theme** | Consistent, lightweight UI shell across all modules |
| **HTMX + Chart.js** | SPA-like partials (search, tabbed reports) without a JS framework |
| **No Celery/Redis (initially)** | Everything is synchronous and small; defer async to Phase 6+ if needed |
| **No tax engine, no full double-entry** | Start with **fund-based accounting** (Fund, Income, Expense, Receipt). Upgrade path to full `finance.Account`/`JournalEntry` later |
| **SQLite default, `django-environ`** | Zero-friction local dev; swap to MySQL/PostgreSQL via env var |

### What is explicitly NOT carried over

- Tax engine
- Multi-company RBAC with `UserRole`/`PermissionMiddleware` (collapse to Django Groups + simple roles)
- Celery beat / async task infra (defer)
- Double-entry accounting initial scope (Fund accounting first)
- Wagtail CMS for business pages (use Django templates + admin)

---

## 3. Target Architecture

### 3.1 Module Map

```
olive_mms/
├── manage.py
├── config/                # Django project config (settings, urls, wsgi/asgi)
├── static/                # css (olive-theme.css, mms.css), js (navigation.js), images
├── templates/             # base.html, registration/*, includes/*
│
├── core/                  # BaseUser/Member-auth, AuditLog, mixins, context_processors, utils
├── institution/           # MosqueProfile (singleton), branches, settings, HIJRI date utils
├── members/               # Member, Family, roles (donor/volunteer/imam), contact info
├── donations/             # DonationType (Sadaqah/Zakat/Lillah/Fitra/Qurbani/Building),
│                          #   Donation, Pledge, Receipt, RecurringPledge
├── finance/               # Fund, Income, Expense, FundTransfer, simple budget
├── madrassa/              # Student, Class, Teacher, Enrollment, Attendance, Fee, FeePayment
├── events/                # Event, ProgramSession, Volunteer, Attendance/RSVP
├── inventory/             # Item, Category, StockLevel, StockMovement, Distribution
└── reporting/             # Dashboards, export views (CSV), simple report builder
```

### 3.2 Design Patterns

| Pattern | Where used |
|---------|------------|
| CBV + `LoginRequiredMixin` + current-mosque scoping | All list/create/update/delete views; scoped to `current_mosque` |
| `services.py` per module | Donation receipt generation, fee payment posting, stock distribution |
| Django `signals.py` | Donation → fund income; FeePayment → fund income; StockMovement → StockLevel |
| Context-processor module registry | `core/context_processors.py` builds nav from enabled modules |
| `TimeStampedModel` abstract base | Every model gets `created_at`/`updated_at` |
| HTMX-aware delete + partial tabs | Delete buttons, tabbed reporting page |
| KPI card grid + Chart.js | All dashboards |
| Two-row top nav shell | `templates/base.html` |

### 3.3 Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | Python 3.11+, Django 5.0.x |
| Frontend | Django Templates, Bootstrap 5.3, Bootstrap Icons, HTMX, Chart.js, Inter font |
| Database | SQLite (dev) / MySQL 8 (prod) via `django-environ` |
| Auth | Custom `core.User` (email login) + Django Groups |
| Config | `django-environ`, `.env` |
| API (optional later) | DRF |
| Deploy | Gunicorn + Whitenoise + Docker (optional), Render/Railway-ready |

---

## 4. Data Model Sketch

```
core.User                -- email login, groups (Admin, Treasurer, Registrar, Teacher, Volunteer)
institution.MosqueProfile-- singleton: name, address, phone, email, bank details,
                              HIJRI offset, enabled_modules (JSON)
members.Family           -- name, head, address, phone
members.Member           -- family FK, name, dob, phone, email, join_date,
                              membership_status, member_role (Imam/Muazzin/Teacher/Volunteer/Donor)
donations.DonationType   -- code (SADQAH, ZAKAT, LILLAH, FITRA, QURBANI, BUILDING, GENERAL),
                              is_active, default_account_hint
donations.Donation       -- member FK (nullable), type FK, amount, payment_method
                              (CASH, CARD, BANK, ONLINE), date, reference_no,
                              fund FK, receipt_number
donations.Pledge         -- member FK, type FK, amount, start/end, frequency, is_active
finance.Fund             -- name (General, Building, Zakat, Education), code, opening_balance
finance.Income           -- fund FK, date, amount, source (donation FK, fee FK, other),
                              description
finance.Expense          -- fund FK, date, amount, category, description, payee
finance.FundTransfer     -- from_fund, to_fund, amount, date, note
madrassa.Class           -- name, level, teacher FK, schedule, capacity
madrassa.Student         -- member FK, family FK, dob, guardian, admission_date, status
madrassa.Enrollment      -- student FK, class FK, academic_year, status
madrassa.Attendance      -- student FK, class FK, date, status (PRESENT/ABSENT/LATE/EXCUSED)
madrassa.Fee             -- name, amount, frequency (monthly/term/annual), class FK
madrassa.FeePayment      -- student FK, fee FK, amount, date, method, receipt_number
events.Event             -- name, type, date_from, date_to, location, budget, notes
events.EventAttendance   -- event FK, member FK, role (organizer/volunteer/guest)
inventory.Item           -- name, category FK, unit, price
inventory.StockLevel     -- item FK, quantity, updated_at
inventory.StockMovement  -- item FK, qty_change, movement_type (IN/OUT), date, purpose, event FK
reporting.Dashboard      -- (optional) saved dashboard/widget defs
```

---

## 5. Phased Delivery Plan

### Phase 0 — Scaffold (Foundation)
- [x] `django-admin startproject config .` with settings split (`base.py`, `dev.py`, `prod.py`)
- [x] Custom `core.User` (email auth), `AUTH_USER_MODEL = "core.User"`
- [x] Base template `templates/base.html` — two-row shell, `olive-theme.css`, `navigation.js`, favicon
- [x] `core/context_processors.py` module registry + `core/utils.py` (`get_current_mosque`)
- [x] Landing/login pages; `django.contrib.humanize`; static + media config
- **Exit criteria**: `manage.py check` passes ✔, two-row nav renders ✔, user can log in ✔.

### Phase 1 — Institution & Members
- [x] `institution.MosqueProfile` singleton + setup wizard
- [x] `members` app: Family + Member CRUD, search, member list with KPI metrics
- [x] Members dashboard with KPI grid (total members, families, active volunteers)
- **Exit criteria**: add/edit/view/delete a member; members list has search + KPIs. ✔

### Phase 2 — Donations
- [x] `donations` app: DonationType, Donation, Pledge, Receipt
- [x] Donation create flow → signals post donation → `finance.Income` on selected fund
- [x] Donation list with filters (type, method, date range) + totals
- [x] Receipt generation (HTML print view)
- **Exit criteria**: record a donation, see fund income auto-posted, print receipt. ✔

### Phase 3 — Finance (Fund Accounting)
- [x] `finance` app: Fund, Income, Expense, FundTransfer, budget
- [x] Fund dashboard: balances, monthly income vs expense chart (Chart.js)
- [x] Expense approval flag (simple `status` field; no workflow engine)
- **Exit criteria**: open fund balances, record expense, dashboard shows balance trend. ✔

### Phase 4 — Madrassa
- [x] `madrassa` app: Class, Teacher (via `members.Member`), Student, Enrollment, Attendance, Fee, FeePayment
- [x] Attendance grid (class × date) with quick check-in (HTMX partial)
- [x] Fee billing + payment posting → `finance.Income` (signal)
- [x] Student report card / progress notes (student detail with enrollments, attendance + fee history)
- **Exit criteria**: enroll student, take daily attendance, collect fee, see income posted. ✔
  (verified via test client: modal create → 204, attendance set/mark-all, fee payment auto-posts income to EDU fund, cascade on delete; 7 unit tests green)

### Phase 5 — Events & Inventory
- [x] `events` app: Event, EventAttendance, volunteers
- [x] `inventory` app: Item, Category, StockLevel, StockMovement, Distribution
- [x] Iftar/food-pack distribution workflow (movement OUT → recipients)
- **Exit criteria**: create event, register attendance, stock items in/out with history. ✔
  (verified via test client: modal create → 204, event detail attendance register/remove, stock IN → level sync,
   distribution OUT → level decrement + recipient; low-stock filter, insufficient-stock + duplicate-attendance
   rejected with visible errors; 14 unit tests green)

### Phase 6 — Reporting & Polish
- [x] `reporting` app: consolidated dashboard (cross-module KPIs + Chart.js), annual/zakat + madrassa fee-collection reports
- [x] CSV export views for members, donations, income, expenses, transfers, students, fee payments, events, items, movements + report exports; Export buttons wired into every module list partial
- [x] Mobile CSS pass (small-screen KPI/header tweaks), accessibility (skip link, `:focus-visible`, chart `role="img"`), empty states
- [x] Seed data command (`seed_demo`), reporting smoke tests (Django test style, matching repo convention)
- **Exit criteria**: every module has a dashboard; CSV exports work; `manage.py test` green. ✔
  (verified via test client: all 3 report pages + 12 CSV exports 200; seed_demo populates all modules; 27 unit tests green)

### Phase 7 — Deployment (optional, on demand)
- [ ] Gunicorn + Whitenoise + Dockerfile + `.env.example`
- [ ] Render/Railway deploy; MySQL/PostgreSQL swap via `DATABASE_URL`
- [ ] (Stretch) DRF API + Celery for email receipts

---

## 6. Conventions

- **Naming**: Models PascalCase; Views `XxxListView`/`XxxCreateView`; URL names `module:view`; templates lowercase snake (`donations/donation_list.html`); CSS kebab-case.
- **Per-module layout**: `models.py`, `views.py`, `forms.py`, `urls.py`, `admin.py`, `services.py` (if logic), `signals.py` (if needed), `templates/<module>/`, `tests.py`.
- **Money**: always `DecimalField(max_digits=..., decimal_places=2)`; format with `|intcomma` + `{% load humanize %}`.
- **Views**: `LoginRequiredMixin` everywhere; querysets scoped via `get_current_mosque(request)`.
- **Nav**: only edit `core/context_processors.py`, never hardcode in templates.
- **UI**: extend `base.html`; use `.kpi-card` for metrics; guard Chart.js canvases with `{% if %}` + JS null-checks; use HTMX for partials.

---

## 7. Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Scope creep toward full accounting/ERP | Explicit fund-based accounting only; document upgrade path |
| HIJRI/Islamic calendar complexity | Store Gregorian dates; expose HIJRI offset + month names util in `institution`; no full calendar lib initially |
| Losing "lightweight" feel | Keep deps minimal; no Celery/Redis until Phase 7 |
| Data entry for attendance is slow | HTMX partial + bulk "mark all present" default |

---

## 8. References

- Live state tracker: `docs/ai_context.md`
- Session prompt log: `docs/prompt.md`
- The `sample/olive_crm` and `sample/olive_erp` reference codebases were **deleted**; no longer
  available for reference.
