# docs/prompt.md — Session Prompt Log

> Purpose: record each working prompt in a rephrased, actionable format so future sessions can
> pick up exactly where work stands. Newest at top under **Current Prompt**; older prompts are
> kept in **History**. Never delete history.

---

## Current Prompt (August 2026)

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
