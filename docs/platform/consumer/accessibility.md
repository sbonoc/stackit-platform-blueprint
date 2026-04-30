# Accessibility Testing and Conformance

This page describes the accessibility testing infrastructure, the Accessibility
Conformance Report (ACR) workflow, and the WCAG 2.1 AA quality gate that the
blueprint provides to generated-consumer repositories.

## Why

EU Accessibility Act (Directive 2019/882/EU) mandates EN 301 549 / WCAG 2.1 AA
conformance for private-sector digital products and services from June 2025.
The blueprint encodes this as a first-class NFR so every work item captures
conformance evidence by default, without manual scaffold assembly.

---

## Make Targets

| Target | Purpose |
|---|---|
| `make touchpoints-test-a11y` | Full-page axe WCAG 2.1 AA scan against a live app URL |
| `make apps-a11y-smoke` | Axe smoke scan with default routes; included in `test-smoke-all-local` |
| `make quality-a11y-acr-check` | Validate ACR exists, is dated, and is within the staleness window |
| `make quality-a11y-acr-sync` | Regenerate ACR criterion rows from the bundled W3C list (preserves your support/notes/evidence) |

### Environment variables for `touchpoints-test-a11y` / `apps-a11y-smoke`

| Variable | Default | Meaning |
|---|---|---|
| `A11Y_BASE_URL` | `http://localhost:3000` | Base URL of the running app |
| `A11Y_ROUTES` | `/` | Comma-separated routes to scan |
| `A11Y_FAIL_ON_IMPACT` | `critical,serious` (`touchpoints-test-a11y`) / `critical` (`apps-a11y-smoke`) | Impact levels that cause a non-zero exit |

---

## WCAG 2.1 AA Ruleset

All blueprint axe scans use the explicit tag array:

```
runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }
```

The default axe ruleset omits `wcag21a` and `wcag21aa` (WCAG 2.1-specific
criteria). Using the default would silently skip SC 2.1.4, 1.3.4, 1.3.5, and
others that are required for EN 301 549 compliance.

---

## Consumer Setup

### 1. Add the axe Playwright dependency

Add `@axe-core/playwright` to your touchpoints `package.json`:

```bash
cd touchpoints && pnpm add -D @axe-core/playwright
```

### 2. Import the preset in component tests

```typescript
import { assertAxeWcag21AA } from 'scripts/lib/platform/touchpoints/axe_preset';

it('has no WCAG 2.1 AA violations', async () => {
  const wrapper = mount(MyComponent, {
    attachTo: document.body,  // required — axe needs live DOM context
  });
  await assertAxeWcag21AA(wrapper.element);
});
```

`attachTo: document.body` is required. Without it, axe cannot detect label
relationships, landmark violations, or focus-order issues.

### 3. Run the full-page scan

```bash
A11Y_BASE_URL=http://localhost:3000 A11Y_ROUTES=/,/dashboard make touchpoints-test-a11y
```

The scan writes `artifacts/a11y/axe-report-<route>.json` per route and prints a
human-readable violation summary to stdout.

---

## Accessibility Conformance Report (ACR)

`docs/platform/accessibility/acr.md` is a VPAT® 2.4 scaffold pre-populated with
all 50 WCAG 2.1 Level A and AA success criteria rows. It is created once by
`make blueprint-upgrade-consumer` and is **not overwritten on subsequent upgrades**.

### Keeping the ACR current

1. **Update `Report date (last reviewed):`** after each accessibility review
   cycle. `quality-hooks-fast` will fail if the date is a placeholder or older
   than the configured staleness window (default: 90 days).

2. **Update support status** in the `Support` column for each criterion you
   have evaluated (`Supports` / `Partially Supports` / `Does Not Support` /
   `Not Applicable`).

3. **Sync new criteria** when the blueprint's bundled W3C list is updated:

   ```bash
   make quality-a11y-acr-sync
   ```

   This regenerates criterion rows from the bundled list while preserving your
   existing `Support`, `Notes`, and `Evidence` cell content.

### Staleness window

The default is **90 days**. Override per-repo in `blueprint/contract.yaml`:

```yaml
spec:
  quality:
    accessibility:
      acr_staleness_days: 180
```

Or override for a single run:

```bash
ACR_STALENESS_DAYS=180 make quality-a11y-acr-check
```

---

## SDD Integration

Every spec scaffolded with `make spec-scaffold` includes:

- **`NFR-A11Y-001`** in `spec.md` — define WCAG 2.1 AA compliance scope; write
  `N/A — <reason>` for non-UI specs.
- **T-A01 through T-A05** in `tasks.md` — accessibility task checklist.
- **Accessibility Gate** in `hardening_review.md` — six SC checklist items;
  mark non-applicable items `N/A` for non-UI specs.
- **`WCAG SC`** column in `traceability.md` — link requirements to specific
  success criteria.

`quality-spec-pr-ready` blocks PR packaging if any Accessibility Gate checklist
item is unchecked and not marked `N/A`.
