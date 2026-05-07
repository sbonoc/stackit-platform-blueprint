#!/usr/bin/env node
/**
 * Full-page axe WCAG 2.1 AA scan using @axe-core/playwright.
 *
 * Usage (via test_a11y.sh or directly):
 *   node axe_page_scan.mjs --base-url http://localhost:3000 --routes / --fail-on-impact critical,serious
 *
 * Environment variables (override CLI flags):
 *   A11Y_BASE_URL        Base URL of the running app (default: http://localhost:3000)
 *   A11Y_ROUTES          Comma-separated route paths to scan (default: /)
 *   A11Y_FAIL_ON_IMPACT  Comma-separated impact levels that cause a non-zero exit (default: critical,serious)
 *   A11Y_REPORT_DIR      Directory for axe-report.json files (default: artifacts/a11y)
 *
 * Requires: @axe-core/playwright, @playwright/test (consumer devDependencies)
 */

import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { writeFileSync, mkdirSync } from "fs";
import { join, resolve } from "path";

const WCAG21AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

function parseArgs() {
  const args = process.argv.slice(2);
  const get = (flag) => {
    const idx = args.indexOf(flag);
    return idx !== -1 ? args[idx + 1] : undefined;
  };
  return {
    baseUrl: get("--base-url") || process.env.A11Y_BASE_URL || "http://localhost:3000",
    routes: (get("--routes") || process.env.A11Y_ROUTES || "/").split(",").map((r) => r.trim()),
    failOnImpact: (get("--fail-on-impact") || process.env.A11Y_FAIL_ON_IMPACT || "critical,serious")
      .split(",")
      .map((i) => i.trim()),
    reportDir: process.env.A11Y_REPORT_DIR || "artifacts/a11y",
  };
}

async function scanPage(page, url) {
  await page.goto(url, { waitUntil: "networkidle" });
  const results = await new AxeBuilder({ page })
    .withTags(WCAG21AA_TAGS)
    .analyze();
  return results;
}

function printViolationSummary(violations, failOnImpact) {
  const failing = violations.filter((v) => failOnImpact.includes(v.impact));
  if (failing.length === 0) {
    console.log(`  [a11y] no ${failOnImpact.join("/")} violations`);
    return;
  }
  for (const v of failing) {
    console.error(`  [a11y] ${v.impact.toUpperCase()} — ${v.id}: ${v.description}`);
    for (const node of v.nodes.slice(0, 3)) {
      console.error(`    target: ${node.target}`);
    }
  }
}

async function main() {
  const { baseUrl, routes, failOnImpact, reportDir } = parseArgs();
  const absReportDir = resolve(process.cwd(), reportDir);
  mkdirSync(absReportDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage();

  let totalFailing = 0;

  for (const route of routes) {
    const url = `${baseUrl}${route}`;
    console.log(`[a11y] scanning ${url}`);
    const results = await scanPage(page, url);

    const reportPath = join(absReportDir, `axe-report${route.replace(/\//g, "-") || "-root"}.json`);
    writeFileSync(reportPath, JSON.stringify(results, null, 2), "utf-8");
    console.log(`[a11y] report written: ${reportPath}`);

    const failingViolations = results.violations.filter((v) => failOnImpact.includes(v.impact));
    printViolationSummary(results.violations, failOnImpact);

    if (failingViolations.length > 0) {
      console.error(
        `[a11y] FAIL — ${failingViolations.length} violation(s) at impact [${failOnImpact.join(",")}] on ${route}`
      );
      totalFailing += failingViolations.length;
    }
  }

  await browser.close();

  if (totalFailing > 0) {
    console.error(`[a11y] ${totalFailing} total failing violation(s) — see reports in ${reportDir}`);
    process.exit(1);
  }

  console.log(`[a11y] all routes passed WCAG 2.1 AA scan`);
}

main().catch((err) => {
  console.error("[a11y] unexpected error:", err);
  process.exit(1);
});
