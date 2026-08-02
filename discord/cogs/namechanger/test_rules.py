from typing import Optional
import logging
import pytest
from . import rules


def run_test(handle: str, handles: list[str]) -> list[rules.ValidationResult]:
    validator = rules.HandleValidator(handles)
    return validator.validate(handle)


@pytest.mark.parametrize(
    argnames=("handle", "handles"),
    argvalues=[
        # duplicate: ok
        ("abcd", ["efgh", "ijkl", "mnop"]),
        # profane: ok
        ("hello world", None),
        # digit limit: ok
        ("onetwothree", None),
        ("abc12", None),
        # length: ok
        ("abc", None),
        ("abcdefghijklmnopqrst", None),
        # characters: ok
        ("abcdefghij klmn56789", None),
        ("ABCDEFGHIJ.KLMN56789", None),
        ("tuvwxyz-01234opqrs", None),
        ("TUVWXYZ_01234OPQRS", None),
        # sequential punctuation: ok, leading/trailing punctuation: ok
        ("a-b_c.d e", None),
    ],
)
def test_pass(handle: str, handles: Optional[list[str]]):
    results = run_test(handle, handles or [])
    assert len(results) == 0, results


@pytest.mark.parametrize(
    argnames=("handle", "expected_rule", "expected_context", "handles"),
    argvalues=[
        ("efgh", rules.DuplicateRule, "EXACTLY eFgh", ["eFgh", "ijkl", "mnop"]),
        (
            "abcdeFg",
            rules.DuplicateRule,
            "VERY close to abcdeF, VERY close to bcdeFg",
            ["abcdeF", "bcdeFg"],
        ),
        (
            "abcdeFghijk",
            rules.DuplicateRule,
            "close to abcdeFg, close to efghijk",
            ["abcdeFg", "efghijk"],
        ),
        (
            "abcdeFghijk",
            rules.DuplicateRule,
            "VERY close to Fghijkabcde",
            ["Fghijkabcde"],
        ),
        # match due to BaseRule.sanitise_handle
        (
            "abcdeFgh01357",
            rules.DuplicateRule,
            "EXACTLY abcdeFghoiest",
            ["abcdeFghoiest"],
        ),
        ("butts", rules.ProfaneRule, None, None),
        ("hahabutts", rules.ProfaneRule, None, None),
        ("buttshaha", rules.ProfaneRule, None, None),
        ("abc123", rules.DigitLimitRule, "3 of 6 characters are digits", None),
        ("123456", rules.DigitLimitRule, "6 of 6 characters are digits", None),
    ],
)
def test_warning(
    handle: str,
    expected_rule: type[rules.BaseRule],
    expected_context: Optional[str],
    handles: Optional[list[str]],
):
    results = run_test(handle, handles or [])
    assert len(results) == 1, results
    assert results[0] == rules.ValidationResult(
        False, expected_rule().description, expected_context
    )


@pytest.mark.parametrize(
    argnames=("handle", "expected_rule", "expected_context"),
    argvalues=[
        ("ab", rules.LengthRule, "Length: 2 characters"),
        ("abcdefghijklmnopqrstu", rules.LengthRule, "Length: 21 characters"),
        (
            "abc!@#$%^&*()=+def",
            rules.InvalidCharactersRule,
            "Invalid characters: !, #, $, %, &, (, ), *, +, =, @, ^",
        ),
        (
            ",<>;:'\"[]\\{}|def",
            rules.InvalidCharactersRule,
            "Invalid characters: \", ', ,, :, ;, <, >, [, \\, ], {, |, }",
        ),
        ("ab--cd", rules.SequentialPunctuationRule, None),
        ("ab__cd", rules.SequentialPunctuationRule, None),
        ("ab..cd", rules.SequentialPunctuationRule, None),
        ("ab  cd", rules.SequentialPunctuationRule, None),
        ("ab-_cd", rules.SequentialPunctuationRule, None),
        ("ab. cd", rules.SequentialPunctuationRule, None),
        ("-abc", rules.LeadingTrailingPunctuationRule, None),
        ("_abc", rules.LeadingTrailingPunctuationRule, None),
        (".abc", rules.LeadingTrailingPunctuationRule, None),
        (" abc", rules.LeadingTrailingPunctuationRule, None),
        ("abc-", rules.LeadingTrailingPunctuationRule, None),
        ("abc_", rules.LeadingTrailingPunctuationRule, None),
        ("abc.", rules.LeadingTrailingPunctuationRule, None),
        ("abc ", rules.LeadingTrailingPunctuationRule, None),
    ],
)
def test_error(
    handle: str, expected_rule: type[rules.BaseRule], expected_context: Optional[str]
):
    results = run_test(handle, [])
    assert len(results) == 1, results
    assert results[0] == rules.ValidationResult(
        True, expected_rule().description, expected_context
    )


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


def test_exceptions(caplog: pytest.LogCaptureFixture):
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
