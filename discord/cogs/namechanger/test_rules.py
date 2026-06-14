from typing import Optional
import logging
import pytest
from . import rules


def run_test(handle: str, handles: list[str]) -> list[rules.ValidationResult]:
    validator = rules.HandleValidator(handles)
    return validator.validate(handle)


# pylint: disable-next=too-many-arguments
def assert_result(
    handle: str,
    expected_error: bool,
    expected_rule: type[rules.BaseRule],
    expected_context: Optional[str] = None,
    *,
    handles: Optional[list[str]] = None
):
    results = run_test(handle, handles or [])
    assert len(results) == 1, results
    assert results[0] == rules.ValidationResult(
        expected_error, expected_rule().description, expected_context
    )


def assert_ok(handle: str, *, handles: Optional[list[str]] = None):
    results = run_test(handle, handles or [])
    assert len(results) == 0, results


def test_duplicate():
    assert_result(
        "efgh",
        False,
        rules.DuplicateRule,
        "EXACTLY eFgh",
        handles=["eFgh", "ijkl", "mnop"],
    )

    assert_result(
        "abcdeFg",
        False,
        rules.DuplicateRule,
        "VERY close to abcdeF, VERY close to bcdeFg",
        handles=["abcdeF", "bcdeFg"],
    )

    assert_result(
        "abcdeFghijk",
        False,
        rules.DuplicateRule,
        "close to abcdeFg, close to efghijk",
        handles=["abcdeFg", "efghijk"],
    )

    assert_result(
        "abcdeFghijk",
        False,
        rules.DuplicateRule,
        "VERY close to Fghijkabcde",
        handles=["Fghijkabcde"],
    )

    # match due to BaseRule.sanitise_handle
    assert_result(
        "abcdeFgh01357",
        False,
        rules.DuplicateRule,
        "EXACTLY abcdeFghoiest",
        handles=["abcdeFghoiest"],
    )

    assert_ok("abcd", handles=["efgh", "ijkl", "mnop"])


def test_profane():
    assert_result("butts", False, rules.ProfaneRule)
    assert_result("hahabutts", False, rules.ProfaneRule)
    assert_result("buttshaha", False, rules.ProfaneRule)

    assert_ok("hello world")


def test_digit_limit():
    assert_result("abc123", False, rules.DigitLimitRule, "3 of 6 characters are digits")
    assert_result("123456", False, rules.DigitLimitRule, "6 of 6 characters are digits")

    assert_ok("abc")
    assert_ok("abc12")


def test_length():
    assert_result("ab", True, rules.LengthRule, "Length: 2 characters")
    assert_result(
        "abcdefghijklmnopqrstu", True, rules.LengthRule, "Length: 21 characters"
    )
    assert_ok("abc")
    assert_ok("abcdefghijklmnopqrst")


def test_invalid_characters():
    assert_result(
        "abc!@#$%^&*()=+def",
        True,
        rules.InvalidCharactersRule,
        "Invalid characters: !, #, $, %, &, (, ), *, +, =, @, ^",
    )
    assert_result(
        ",<>;:'\"[]\\{}|def",
        True,
        rules.InvalidCharactersRule,
        "Invalid characters: \", ', ,, :, ;, <, >, [, \\, ], {, |, }",
    )

    assert_ok("abcdefghij klmn56789")
    assert_ok("ABCDEFGHIJ.KLMN56789")
    assert_ok("tuvwxyz-01234opqrs")
    assert_ok("TUVWXYZ_01234OPQRS")


def test_sequential_punctuation():
    assert_result("ab--cd", True, rules.SequentialPunctuationRule)
    assert_result("ab__cd", True, rules.SequentialPunctuationRule)
    assert_result("ab..cd", True, rules.SequentialPunctuationRule)
    assert_result("ab  cd", True, rules.SequentialPunctuationRule)
    assert_result("ab-_cd", True, rules.SequentialPunctuationRule)
    assert_result("ab. cd", True, rules.SequentialPunctuationRule)

    assert_ok("a-b_c.d e")


def test_leading_trailing_punctuation():
    assert_result("-abc", True, rules.LeadingTrailingPunctuationRule)
    assert_result("_abc", True, rules.LeadingTrailingPunctuationRule)
    assert_result(".abc", True, rules.LeadingTrailingPunctuationRule)
    assert_result(" abc", True, rules.LeadingTrailingPunctuationRule)
    assert_result("abc-", True, rules.LeadingTrailingPunctuationRule)
    assert_result("abc_", True, rules.LeadingTrailingPunctuationRule)
    assert_result("abc.", True, rules.LeadingTrailingPunctuationRule)
    assert_result("abc ", True, rules.LeadingTrailingPunctuationRule)

    assert_ok("a-b_c.d e")


def test_all():
    results = run_test(
        "..$abcd1234567890butts123456789", ["abcd1234567890butts123456789"]
    )
    assert len(results) == 7, results

    assert results[0] == rules.ValidationResult(
        False,
        rules.DuplicateRule().description,
        "VERY close to abcd1234567890butts123456789",
    )

    assert results[1] == rules.ValidationResult(False, rules.ProfaneRule().description)

    assert results[2] == rules.ValidationResult(
        False,
        rules.DigitLimitRule().description,
        "19 of 31 characters are digits",
    )

    assert results[3] == rules.ValidationResult(
        True, rules.LengthRule().description, "Length: 31 characters"
    )

    assert results[4] == rules.ValidationResult(
        True, rules.InvalidCharactersRule().description, "Invalid characters: $"
    )

    assert results[5] == rules.ValidationResult(
        True, rules.SequentialPunctuationRule().description
    )

    assert results[6] == rules.ValidationResult(
        True, rules.LeadingTrailingPunctuationRule().description
    )


def test_errors(caplog: pytest.LogCaptureFixture):
    with pytest.raises(ValueError, match="handle cannot be empty"):
        rules.HandleValidator([]).validate("")

    with pytest.raises(NotImplementedError):
        rules.BaseRule().validate("not implemented")

    caplog.clear()
    rules.HandleValidator([""]).validate("empty handles")
    assert (
        "namechanger.rules",
        logging.WARNING,
        "Empty handle in DuplicateRule handles list, skipping",
    ) in caplog.record_tuples
