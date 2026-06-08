from typing import Optional
import unittest
from . import rules


class HandleValidatorTest(unittest.TestCase):
    def run_test(self, handle: str, handles: list[str]) -> list[rules.ValidationResult]:
        validator = rules.HandleValidator(handles)
        return validator.validate(handle)

    # pylint: disable-next=too-many-arguments
    def assert_result(
        self,
        handle: str,
        expected_error: bool,
        expected_rule: type[rules.BaseRule],
        expected_context: Optional[str] = None,
        *,
        handles: Optional[list[str]] = None
    ):
        results = self.run_test(handle, handles or [])
        self.assertEqual(len(results), 1, results)
        self.assertEqual(
            results[0],
            rules.ValidationResult(
                expected_error, expected_rule().description, expected_context
            ),
        )

    def assert_ok(self, handle: str, *, handles: Optional[list[str]] = None):
        results = self.run_test(handle, handles or [])
        self.assertEqual(len(results), 0, results)

    def test_duplicate(self):
        self.assert_result(
            "efgh",
            False,
            rules.DuplicateRule,
            "EXACTLY eFgh",
            handles=["eFgh", "ijkl", "mnop"],
        )

        self.assert_result(
            "abcdeFg",
            False,
            rules.DuplicateRule,
            "VERY close to abcdeF, VERY close to bcdeFg",
            handles=["abcdeF", "bcdeFg"],
        )

        self.assert_result(
            "abcdeFghijk",
            False,
            rules.DuplicateRule,
            "close to abcdeFg, close to efghijk",
            handles=["abcdeFg", "efghijk"],
        )

        self.assert_result(
            "abcdeFghijk",
            False,
            rules.DuplicateRule,
            "VERY close to Fghijkabcde",
            handles=["Fghijkabcde"],
        )

        # match due to BaseRule.sanitise_handle
        self.assert_result(
            "abcdeFgh01357",
            False,
            rules.DuplicateRule,
            "EXACTLY abcdeFghoiest",
            handles=["abcdeFghoiest"],
        )

        self.assert_ok("abcd", handles=["efgh", "ijkl", "mnop"])

    def test_profane(self):
        self.assert_result("butts", False, rules.ProfaneRule)
        self.assert_result("hahabutts", False, rules.ProfaneRule)
        self.assert_result("buttshaha", False, rules.ProfaneRule)

        self.assert_ok("hello world")

    def test_digit_limit(self):
        self.assert_result(
            "abc123", False, rules.DigitLimitRule, "3 of 6 characters are digits"
        )
        self.assert_result(
            "123456", False, rules.DigitLimitRule, "6 of 6 characters are digits"
        )

        self.assert_ok("abc")
        self.assert_ok("abc12")

    def test_length(self):
        self.assert_result("ab", True, rules.LengthRule, "Length: 2 characters")
        self.assert_result(
            "abcdefghijklmnopqrstu", True, rules.LengthRule, "Length: 21 characters"
        )
        self.assert_ok("abc")
        self.assert_ok("abcdefghijklmnopqrst")

    def test_invalid_characters(self):
        self.assert_result(
            "abc!@#$%^&*()=+def",
            True,
            rules.InvalidCharactersRule,
            "Invalid characters: !, #, $, %, &, (, ), *, +, =, @, ^",
        )
        self.assert_result(
            ",<>;:'\"[]\\{}|def",
            True,
            rules.InvalidCharactersRule,
            "Invalid characters: \", ', ,, :, ;, <, >, [, \\, ], {, |, }",
        )

        self.assert_ok("abcdefghij klmn56789")
        self.assert_ok("ABCDEFGHIJ.KLMN56789")
        self.assert_ok("tuvwxyz-01234opqrs")
        self.assert_ok("TUVWXYZ_01234OPQRS")

    def test_sequential_punctuation(self):
        self.assert_result("ab--cd", True, rules.SequentialPunctuationRule)
        self.assert_result("ab__cd", True, rules.SequentialPunctuationRule)
        self.assert_result("ab..cd", True, rules.SequentialPunctuationRule)
        self.assert_result("ab  cd", True, rules.SequentialPunctuationRule)
        self.assert_result("ab-_cd", True, rules.SequentialPunctuationRule)
        self.assert_result("ab. cd", True, rules.SequentialPunctuationRule)

        self.assert_ok("a-b_c.d e")

    def test_leading_trailing_punctuation(self):
        self.assert_result("-abc", True, rules.LeadingTrailingPunctuationRule)
        self.assert_result("_abc", True, rules.LeadingTrailingPunctuationRule)
        self.assert_result(".abc", True, rules.LeadingTrailingPunctuationRule)
        self.assert_result(" abc", True, rules.LeadingTrailingPunctuationRule)
        self.assert_result("abc-", True, rules.LeadingTrailingPunctuationRule)
        self.assert_result("abc_", True, rules.LeadingTrailingPunctuationRule)
        self.assert_result("abc.", True, rules.LeadingTrailingPunctuationRule)
        self.assert_result("abc ", True, rules.LeadingTrailingPunctuationRule)

        self.assert_ok("a-b_c.d e")

    def test_all(self):
        results = self.run_test(
            "..$abcd1234567890butts123456789", ["abcd1234567890butts123456789"]
        )
        self.assertEqual(len(results), 7, results)

        self.assertEqual(
            results[0],
            rules.ValidationResult(
                False,
                rules.DuplicateRule().description,
                "VERY close to abcd1234567890butts123456789",
            ),
        )

        self.assertEqual(
            results[1],
            rules.ValidationResult(False, rules.ProfaneRule().description),
        )

        self.assertEqual(
            results[2],
            rules.ValidationResult(
                False,
                rules.DigitLimitRule().description,
                "19 of 31 characters are digits",
            ),
        )

        self.assertEqual(
            results[3],
            rules.ValidationResult(
                True, rules.LengthRule().description, "Length: 31 characters"
            ),
        )

        self.assertEqual(
            results[4],
            rules.ValidationResult(
                True, rules.InvalidCharactersRule().description, "Invalid characters: $"
            ),
        )

        self.assertEqual(
            results[5],
            rules.ValidationResult(True, rules.SequentialPunctuationRule().description),
        )

        self.assertEqual(
            results[6],
            rules.ValidationResult(
                True, rules.LeadingTrailingPunctuationRule().description
            ),
        )


if __name__ == "__main__":
    unittest.main()
