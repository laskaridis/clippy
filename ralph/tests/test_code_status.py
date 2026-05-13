from __future__ import annotations

import unittest

from ralph.errors import MalformedStatusError
from ralph.lifecycle.phases.code.status import CodeStatus, parse_code_status
from ralph.lifecycle.phases.base import PhaseOutcome


class CodeStatusTests(unittest.TestCase):
    def test_parse_code_status_normalizes_crlf_and_preserves_body(self) -> None:
        result = parse_code_status("RALPH_STATUS=COMPLETE\r\nfirst line\r\nsecond line\r\n")

        self.assertEqual(result.status, CodeStatus.COMPLETE)
        self.assertEqual(result.outcome, PhaseOutcome.COMPLETED)
        self.assertEqual(result.phase_outcome, PhaseOutcome.COMPLETED)
        self.assertEqual(result.response_body, "first line\nsecond line\n")
        self.assertIsNone(result.blocker_line)

    def test_parse_code_status_rejects_unknown_first_line(self) -> None:
        with self.assertRaises(MalformedStatusError):
            parse_code_status("RALPH_STATUS=NOPE\nbody\n")


if __name__ == "__main__":
    unittest.main()
