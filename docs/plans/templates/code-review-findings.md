# PR Review Template (Agent-Authored)

Use this template to document local code review findings in a consistent, actionable format.

## Review metadata

- Branch:
- Review scope (files/areas):
  - <file path>
  - ...
- Review date (UTC):

## Review verdict

- Blocking issues present: `yes` / `no`
- Highest severity found: `Critical` / `High` / `Medium` / `Low` / `none`
- Summary:

## Severity legend

- `Critical`: Release-blocking correctness/security/data-loss risk
- `High`: High-impact bug or regression risk; should be fixed before merge
- `Medium`: Medium-impact maintainability/behavior risk; fix soon
- `Low`: Low-impact improvement or cleanup

## Findings 

> Repeat this section for each finding.

### ISSUE-01 - `<short title>`

- Severity: `Critical|High|Medium|Low` (**required**)
- Blocking: `yes|no` (**required**)
- Category: `correctness|security|accessibility|performance|reliability|maintainability|tests|ux|etc`
- Files:
  - `path/to/file[:line]`
- Impact: User/system impact if not fixed
- Recommended fix: Proposed approach
- Status: `Open|Fixed|Deferred|Won't fix`