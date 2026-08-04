# docs/prompt.md — Session Prompt Log

> Purpose: record each working prompt in a rephrased, actionable format so future sessions can
> pick up exactly where work stands. Newest at top under **Current Prompt**; older prompts are
> kept in **History**. Never delete history.

---

## Current Prompt (August 2026)

**Task:** Phase 6 (Reporting & Polish) — consolidated reporting + CSV exports + polish.

**Steps:**

1. **`reporting` app** (registered in `INSTALLED_APPS` + URLs at `/reporting/`; nav entry already
   in the module registry):
   - `ReportingDashboardView` (`reporting:index`): cross-module KPI cards (members, year
     donations, total balance, students, upcoming events, low stock, month income/expense),
     donation-by-type doughnut + 6-month income-vs-expense bar chart (Chart.js, `json_script`
     data), recent donations / fee payments / expenses / distributions lists with empty states.
   - `AnnualZakatReportView` (year filter; grand/zakat totals + share %, by-type table with Zakat
     badge, monthly bar chart) and `FeeCollectionReportView` (year + class filters; collected
     total, class collection rate, per-class expected-vs-collected table with rate badges, top
     payers, monthly chart).
   - CSV exports: `BaseCSVExportView` + `csv_response` helper; export views for members (honors
     `q`), donations (type/method/date range), income (fund/date), expenses (fund/status/date),
     transfers, students (`q`), fee payments, events, items, movements (type/item), and the
     annual-zakat + fee-collection reports (honor year/class). "Export" buttons added to every
     module list partial header.
   - Gotchas fixed: use `objects.dates("date", "year")` (date columns are `DateField`, not
     `DateTimeField` — `datetimes()` raises); compute `overall_rate` + `has_payments` in the fee
     report.
2. **Polish**: `base.html` skip link (`#main-content`) + `id` on `<main>`, `:focus-visible`
   outline, responsive KPI/header tweaks for small screens in `olive-theme.css`, chart canvases
   get `role="img"` + `aria-label`.
3. **`seed_demo` command** (`core/management/commands/seed_demo.py`): idempotent-ish demo data
   across all modules (reuses `seed_defaults`; families, members with roles, classes/enrollments/
   fees/payments, donations + pledge, expenses + transfer, events + attendance, inventory in/out).
   Prefer `.filter(...).first()` over `.get()` (dev DB has pre-existing records).
4. **Tests**: `reporting/tests.py` in Django test style (repo has no pytest) — login-gating,
   dashboard KPIs, zakat + fee totals, all 12 CSV exports (content-type + 200), donation export
   honors filters.
5. **Docs** — tick Phase 6 in `docs/plan.md`, re-label stale "Current Prompt" headers into
   History, add this prompt, keep `docs/ai_context.md` current.

**Exit criteria:** all 3 report pages + 12 CSV exports 200; `seed_demo` populates all modules;
`manage.py check` + `manage.py test` (27 tests) green; Phase 6 checklist ticked. — *Complete:
Phase 6 done and verified via test client (reports + exports 200 with seeded data, all module
list pages 200); 6 new reporting tests green (suite 27); docs updated; collected static.*

---

### Prompt 2 (August 2026) — Render/Docker deployment config + Phase 1 (Institution & Members)

**Task:** Add Render/Docker deployment config and continue Phase 1 implementation.

**Steps:**

1. **Create `render.yaml`** modeled on `olive_erp/render.yaml` for Render.com deployment, but
   adapted for the lightweight stack:
   - PostgreSQL service (free).
   - Web service using `./build.sh` / `./run.sh`, `PYTHON_VERSION=3.11`,
     `DJANGO_SETTINGS_MODULE=config.settings.prod`, generated `DJANGO_SECRET_KEY`,
     `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL` from the Postgres service,
     optional superuser env vars.
   - **No** Redis or Celery worker (deferred).
2. **Add Docker deployment files:**
   - `Dockerfile` (python:3.11-slim, install `requirements.txt`, `CMD ["./run.sh"]`).
   - `.dockerignore`.
   - `build.sh` (pip install + `collectstatic`) and `run.sh` (migrate + seed superuser +
     gunicorn on `$PORT`), both executable.
   - Add `gunicorn` + `whitenoise` to `requirements.txt`; wire WhiteNoise into
     `config/settings/base.py` (middleware + `STORAGES`).
3. **Maintain prompt history** in `docs/prompt.md` — move the previous prompt to History, add
   this one as Current.
4. **Continue with Phase 1 — Institution & Members** per `docs/plan.md`:
   - `institution` app: `MosqueProfile` singleton + setup wizard; wire
     `core/utils.get_current_mosque` to it.
   - `members` app: `Family` + `Member` CRUD, search, member list with KPI metrics.
   - Wire both apps into the `core` module registry (automatic once apps exist).
5. **Keep `docs/ai_context.md` current** — update Completed / In Progress / Next in §5 at the
   start and end of the work.

**Exit criteria for the session:** `render.yaml` + `Dockerfile` present and consistent with the
stack; `manage.py check` green; Phase 1 exit criteria met (add/edit/view/delete a member, list
has search + KPIs); `docs/ai_context.md` reflects the finished state. — *Complete: render.yaml +
Dockerfile + build/run.sh added, WhiteNoise wired, Phase 1 done and verified via test client
(incl. HTMX delete fix for Django 5.0 `BaseDeleteView`).*

---

### Prompt 3 (August 2026) — Modal dialogs, mandatory member contact + WhatsApp, Phase 2 (Donations)

**Task:** Convert add/edit screens to modal-dialog popups, make member phone/email mandatory
with WhatsApp messaging options, and continue into Phase 2 (Donations) implementation.

**Steps:**

1. **Modal dialogs for add/edit** — build reusable HTMX modal infra: `#genericModal` in
   `templates/base.html`, partial `templates/includes/htmx_modal_form.html`, `closeModal`
   listener in `static/js/navigation.js`. List buttons `hx-get` create/update forms into the
   modal body; submit posts back to the same path; success returns 204 +
   `HX-Trigger: {"closeModal":"","listChanged":""}`; lists auto-refresh via root div
   `hx-trigger="listChanged from:body"`.
2. **Members hardening** — `phone`/`email` required (migration `members/0002`); add
   `whatsapp_number()` / `whatsapp_url(message=None)` on `Member`; show WhatsApp links in
   member list + detail.
3. **Convert existing apps** — `members` (member + family lists split into `partials/*_content.html`),
   `institution` (profile edit + index partial) to the modal mixins
   (`HTMXPartialMixin`/`HTMXModalFormMixin`/`HTMXDeleteMixin` in `core/mixins.py`).
4. **Phase 2 — Donations** — create `finance` app (Fund with `balance` property, Income,
   Expense, FundTransfer) and `donations` app (DonationType, Donation with auto `receipt_number`,
   Pledge). `Donation.save()` posts `finance.Income` via `post_donation_to_fund` signal
   (`donations/apps.py` `ready()` import). Add list filters (type/method/date + totals), HTML
   print receipt view, pledge + donation-type management. Register apps/URLs, run migrations,
   `seed_defaults` command (7 types, 4 funds).
5. **Keep `docs/ai_context.md` and `docs/plan.md` current** at start and end of the session.

**Exit criteria:** all add/edit screens open in modals; member phone/email required with
WhatsApp links; record a donation → fund income auto-posted → printable receipt; pledge/type/fund
CRUD working; Phase 2 checklist ticked. — *Complete: Phase 2 done and verified via test client
(modal create 204 + trigger, donation→Income posting, receipt print, filters/totals; fixed
stray `{% endblock %}` in new partials and `Income.donation` → `on_delete=CASCADE` so donation
delete also removes auto-posted income).*

---

### Prompt 6 (August 2026) — Phase 5 (Events & Inventory)

**Task:** Continue to the next phase — Phase 5 (Events & Inventory) implementation.

**Steps:**

1. **Update `docs/ai_context.md`** at start and end of the session (completed / in progress /
   next).
2. **Phase 5 — Events & Inventory** per `docs/plan.md`:
   - `events` app: `Event` (event_type/status choices, date range validation), `EventAttendance`
     (role choices, `unique_event_member` constraint), event list with filters + KPIs, event
     detail with attendee register/remove, volunteers list. Same conventions as prior apps.
   - `inventory` app: `Category`, `Item` (unit, price, `low_stock_threshold`,
     `quantity`/`is_low_stock`/`stock_value` properties), `StockLevel` (OneToOne),
     `StockMovement` (IN/OUT, optional event FK + recipient FK/name). `inventory/signals.py`
     recomputes `StockLevel` on movement post_save/post_delete.
   - Distribution workflow = movement OUT: `DistributionForm` forces OUT, requires a recipient
     (member or name), rejects quantity above available stock; `DistributionListView` + modal
     create. Item/movement/category lists with filters + KPI totals.
   - Register both apps in `INSTALLED_APPS` + URLs; run migrations; `events/tests.py` +
     `inventory/tests.py` (constraints, stock sync, validation).
   - Fixes while there: partials kept flat (no stray `{% endblock %}` — that broke rendering),
     `ItemListView` needs `context_object_name="item_list"` because the low-stock filter returns a
     plain list (Django then stops setting the default context name), movement form prefills item
     from `?item=`, and `templates/includes/form_fields.html` gained a non-field errors block so
     validation errors (duplicate attendance, insufficient stock) are visible.
3. **Docs** — tick Phase 5 in `docs/plan.md`, log this prompt, keep `docs/ai_context.md` current.

**Exit criteria:** create event, register attendance, stock items in/out with history;
insufficient-stock and duplicate-attendance rejected with visible errors; `manage.py check` +
`manage.py test` green; Phase 5 checklist ticked. — *Complete: Phase 5 done and verified via test
client (event + attendee modal create 204, stock IN → level 100, distribution OUT to member →
level 70, all pages + HTMX partials 200, low-stock filter, oversell + dup attendance rejected with
visible errors); 14 new unit tests green (suite 21).*

---

### Prompt 4 (August 2026) — Money rounding fix + Phase 3 (Finance)

**Task:** Fix total balance showing `5,000.03000000000` (round to 2 decimal places) and continue
into Phase 3 (Finance) implementation.

**Steps:**

1. **Update `docs/ai_context.md`** at start and end of the session (completed / in progress /
   next).
2. **Rounding fix** — root cause: SQLite returns `Sum()` of DecimalFields as a float, converted
   back to Decimal with floating-point artifacts. Add `core/utils.money()` (quantize to 2 dp,
   `ROUND_HALF_UP`, guards invalid values) and apply it to `Fund.balance`,
   `FinanceDashboardView.total_balance`, and the donation/expense/income/transfer aggregate
   totals.
3. **Phase 3 — Finance** per `docs/plan.md`:
   - `FinanceDashboardView` becomes `finance:index`: KPI cards (total balance, month income,
     month expense, fund count), per-fund balance table, Chart.js 6-month income-vs-expense bar
     chart fed via `json_script`, quick links to Income/Expenses/Transfers/Funds.
   - Expenses: list with filters (fund/status/date range) + KPIs (filtered total, pending,
     approved count), modal create/edit (`ExpenseForm`), one-click HTMX approve
     (`ExpenseApproveView` returns 204 + `listChanged`).
   - Income: list with filters (fund/date) + manual income entry (`IncomeForm`, `source`
     required); donation-posted income links back to its receipt.
   - FundTransfer: list + modal create (`FundTransferForm`) with same-fund validation.
   - Funds page moves from index to `finance:funds`; nav registry auto-resolves `finance:index`.
4. **Docs** — tick Phase 3 in `docs/plan.md`, log this prompt, keep `docs/ai_context.md` current.

**Exit criteria:** total balance shows 2 decimals; open fund balances on dashboard, record
expense (pending → approve), dashboard shows balance trend chart; Phase 3 checklist ticked. —
*Complete: rounding verified (raw aggregate `10000.0600000000` → rendered `10,000.06`); Phase 3
flows verified via test client (dashboard + chart, expense create/approve, manual income,
transfer moves balances, same-fund blocked); test data cleaned up.*

---

### Prompt 5 (August 2026) — Phase 4 (Madrassa)

**Task:** Continue to the next phase — Phase 4 (Madrassa) implementation.

**Steps:**

1. **Update `docs/ai_context.md`** at start and end of the session (completed / in progress /
   next).
2. **Phase 4 — Madrassa** per `docs/plan.md`:
   - `madrassa` app: `Class` (teacher FK → `members.Member`), `Student` (member/family FKs,
     guardian, admission), `Enrollment` (unique per student/class/year), `Attendance` (unique per
     student/day, PRESENT/ABSENT/LATE/EXCUSED), `Fee`, `FeePayment` (auto `PAY-…` receipt number;
     amount defaults to selected fee in `save()`). Same conventions as prior apps (TimeStampedModel,
     BootstrapFormMixin, modal CRUD, partial lists).
   - Add `finance.Income.fee_payment` OneToOne (`on_delete=CASCADE`); `post_fee_payment_to_fund`
     signal (`madrassa/apps.py` `ready()`) posts income, falling back to the EDU fund.
   - Attendance grid (class × date): `attendance.html` + `partials/attendance_grid.html`;
     per-cell status buttons POST to `attendance_set` (204 + `attendanceChanged`), grid root
     auto-refreshes; "Mark all present" posts to `attendance_mark_all`.
   - Views: Madrassa dashboard (KPIs + class table + recent payments), Class/Student/Enrollment/
     Fee/FeePayment lists with filters + modal CRUD, Student detail (report-card style).
   - Register app in `INSTALLED_APPS` + URLs; run migrations; `madrassa/tests.py` (signal, amount
     default, unique constraints, cascade).
   - Fixes while there: Chart.js CDN was missing from `base.html` (finance dashboard chart);
     add CSRF meta + htmx `configRequest` header wiring in `navigation.js` so `hx-post` buttons
     work in a real browser.
3. **Docs** — tick Phase 4 in `docs/plan.md`, log this prompt, keep `docs/ai_context.md` current.

**Exit criteria:** enroll student, take daily attendance (grid + quick check-in + mark-all),
collect fee and see income auto-posted on the EDU fund; `manage.py check` + `manage.py test`
green; Phase 4 checklist ticked. — *Complete: Phase 4 done and verified via test client (modal
create 204 + triggers, attendance set/mark-all with `attendanceChanged`, fee→Income posting +
EDU fallback, cascade on delete, student detail); capacity-blank and amount-default edge cases
fixed; 7 unit tests green.*

---

## History

### Prompt 1 (August 2026) — Kickoff + Phase 0

**Task:** Kick off implementation of the Olive MMS using the lightweight approach, and tidy the
repo/docs to match that decision.

**Steps:**

1. **Adopt the lightweight approach** — the `samples/` folder (olive_crm / olive_erp reference
   codebases) has been **deleted**. Remove the "Codebase Comparison" section from
   `docs/plan.md` and drop all references to the deleted samples.
2. **Add a `.gitignore`** appropriate for a Django/Python project.
3. **Record the prompt** in `docs/prompt.md` in rephrased, structured format.
4. **Start Phase 0 implementation** per `docs/plan.md`:
   - Scaffold the Django project with a `config` package and settings split into
     `base.py` / `dev.py` / `prod.py`.
   - Create the `core` app with a custom `User` (email login, `AUTH_USER_MODEL`), `AuditLog`,
     `TimeStampedModel` base, `core/utils.py` (`get_current_mosque`), and
     `core/context_processors.py` module registry.
   - Build the two-row top-nav shell in `templates/base.html`, `static/css/olive-theme.css`,
     `static/js/navigation.js`.
   - Add login/landing pages and a seed admin user.
   - Verify: `manage.py check` passes, two-row nav renders, login works.
5. **Keep `docs/ai_context.md` current** — update the Completed / In Progress / Next state in
   §5 at the start and end of the work.

**Exit criteria:** Phase 0 checklist in `docs/plan.md` fully done, `manage.py check` green,
`runserver` renders the nav shell, and `docs/ai_context.md` reflects the finished state. —
*Complete: Phase 0 done, verified via test client + runserver boot.*
