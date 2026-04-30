/**
 * Shared axe-core WCAG 2.1 AA preset for consumer vitest-axe component tests.
 *
 * Prerequisites:
 *   - Mount the component under test with `attachTo: document.body` so axe can
 *     detect label relationships, landmark structure, and focus order across the
 *     full document context. Tests that omit this precondition may pass while
 *     missing real WCAG 2.1 AA violations (SC 4.1.2, 1.3.1, 2.4.3).
 *
 * Usage:
 *   import { assertAxeWcag21AA } from "scripts/lib/platform/touchpoints/axe_preset";
 *
 *   it("has no WCAG 2.1 AA violations", async () => {
 *     const wrapper = mount(MyComponent, { attachTo: document.body });
 *     await assertAxeWcag21AA(wrapper.element);
 *     wrapper.unmount();
 *   });
 */

import { axe, toHaveNoViolations } from "vitest-axe";
import { expect } from "vitest";

expect.extend(toHaveNoViolations);

export const WCAG21AA_AXE_CONFIG = {
  runOnly: {
    type: "tag" as const,
    values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
  },
};

export async function assertAxeWcag21AA(element: Element): Promise<void> {
  const results = await axe(element, WCAG21AA_AXE_CONFIG);
  expect(results).toHaveNoViolations();
}
