import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";

type Severity = "minor" | "moderate" | "serious" | "critical";

type AccessibilityFinding = {
  id: string;
  impact: Severity | null;
  description: string;
  help: string;
  helpUrl: string;
  nodeCount: number;
  nodeTargets: string[];
};

function toReadableImpact(value: Severity | null): string {
  return value ?? "unknown";
}

export async function collectWcag21AALevelFindings(page: Page): Promise<AccessibilityFinding[]> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

  return results.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact ?? null,
    description: violation.description,
    help: violation.help,
    helpUrl: violation.helpUrl,
    nodeCount: violation.nodes.length,
    nodeTargets: violation.nodes.map((node) => node.target.join(" ")),
  }));
}

export function assertNoSeriousOrCriticalFindings(
  findings: AccessibilityFinding[],
  auditTarget: string
): void {
  if (findings.length === 0) {
    console.log(`[a11y] ${auditTarget}: no WCAG 2.1 A/AA findings`);
    return;
  }

  console.log(`[a11y] ${auditTarget}: ${findings.length} finding(s)`);
  findings.forEach((finding) => {
    console.log(
      `[a11y] - impact=${toReadableImpact(finding.impact)} rule=${finding.id} nodes=${finding.nodeCount} targets=${finding.nodeTargets.join(" | ")} help="${finding.help}" url=${finding.helpUrl}`
    );
  });

  const blockingFindings = findings.filter(
    (finding) => finding.impact === "critical" || finding.impact === "serious"
  );

  if (blockingFindings.length > 0) {
    throw new Error(
      `[a11y] ${auditTarget} has ${blockingFindings.length} blocking WCAG 2.1 finding(s) at serious/critical severity.`
    );
  }
}
