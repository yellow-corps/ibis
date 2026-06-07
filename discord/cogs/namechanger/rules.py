from typing import Optional
from dataclasses import dataclass
import string
from itertools import pairwise
import base64
from pathlib import Path
import re
from enum import Enum
from logging import getLogger

_log = getLogger(__name__)

_PUNCTUATION = "-_. "
_VALID_CHARACTERS = string.ascii_letters + string.digits + _PUNCTUATION

with Path(__file__).with_name("profanity.txt").open("r", encoding="ascii") as file:
    _PROFANITY_LIST = [
        re.escape(base64.b64decode(line).decode("utf-8")) for line in file
    ]
    _PROFANITY_STR = "|".join(_PROFANITY_LIST)
    _PROFANITY_REGEX = re.compile(rf"({_PROFANITY_STR})")


@dataclass
class ValidationResult:
    error: bool
    description: str
    context: Optional[str] = None

    def __str__(self):
        return " ".join(
            [
                "Error" if self.error else "Warning",
                self.description,
                *([f"({self.context}"] if self.context else []),
            ]
        )


class BaseRule:
    description: str

    def validate(self, handle: str) -> Optional[ValidationResult]:
        raise NotImplementedError

    def warning(self, context: Optional[str] = None) -> ValidationResult:
        return ValidationResult(False, self.description, context)

    def error(self, context: Optional[str] = None) -> ValidationResult:
        return ValidationResult(True, self.description, context)

    def sanitise_handle(self, handle: str):
        return (
            handle.lower()
            .replace("0", "o")
            .replace("1", "i")
            .replace("3", "e")
            .replace("5", "s")
            .replace("7", "t")
        )


class _DuplicateThreshold(float, Enum):
    EXACT = 1
    HIGH = 0.9
    LOW = 0.75


class DuplicateRule(BaseRule):
    def __init__(self, handles: list[str] = None):
        self.description = "Handle is similar to another handle and may cause confusion"
        self.handles = handles or []

    def validate(self, handle: str) -> Optional[ValidationResult]:
        matches: list[str] = []
        left = list(pairwise(self.sanitise_handle(handle)))
        for right_handle in self.handles:
            if not right_handle:
                _log.warning("Empty handle in DuplicateRule handles list, skipping")
                continue

            right = list(pairwise(self.sanitise_handle(right_handle)))
            length = len(left) + len(right)
            intersections = 0

            for left_pair in left:
                match = None
                for right_pair in right:
                    if left_pair == right_pair:
                        intersections += 1
                        match = right_pair
                        break

                if match:
                    right.remove(match)

            dice_coefficient = (2 * intersections) / length

            if dice_coefficient == _DuplicateThreshold.EXACT:
                matches.append(f"EXACTLY {right_handle}")
            elif dice_coefficient >= _DuplicateThreshold.HIGH:
                matches.append(f"VERY close to {right_handle}")
            elif dice_coefficient >= _DuplicateThreshold.LOW:
                matches.append(f"close to {right_handle}")

        if matches:
            return self.warning(", ".join(matches))
        return None


class ProfaneRule(BaseRule):
    def __init__(self):
        self.description = "Handle possibly contains swear words or slurs"

    def validate(self, handle: str) -> Optional[ValidationResult]:
        if _PROFANITY_REGEX.findall(self.sanitise_handle(handle)):
            return self.warning()
        return None


class DigitLimitRule(BaseRule):
    def __init__(self):
        self.description = "Handle contains too many digits (>50%)"

    def validate(self, handle: str) -> Optional[ValidationResult]:
        is_digits_list = [str.isdigit(c) for c in handle]
        digits_count = is_digits_list.count(True)
        non_digits_count = is_digits_list.count(False)

        if digits_count >= non_digits_count:
            return self.warning(
                f"{digits_count} of {len(handle)} characters are digits"
            )
        return None


class LengthRule(BaseRule):
    def __init__(self):
        self.description = "Handles must be between 3 and 20 characters in length"

    def validate(self, handle: str) -> Optional[ValidationResult]:
        length = len(handle)
        if length < 3 or length > 20:
            return self.error(f"Length: {length} characters")
        return None


class InvalidCharactersRule(BaseRule):
    def __init__(self):
        self.description = (
            "Handles must only contain letters, numbers, hyphens, underscores, "
            + "periods, and spaces"
        )

    def validate(self, handle: str) -> Optional[ValidationResult]:
        invalid_chars = list(set(handle) - set(_VALID_CHARACTERS))
        if invalid_chars:
            invalid_chars.sort()
            return self.error(f"Invalid characters: {', '.join(invalid_chars)}")
        return None


class SequentialPunctuationRule(BaseRule):
    def __init__(self):
        self.description = (
            "Handles cannot have sequential hyphens, underscores, periods, or spaces"
        )

    def validate(self, handle: str) -> Optional[ValidationResult]:
        for pair in pairwise(handle):
            if set(pair).issubset(_PUNCTUATION):
                return self.error()
        return None


class LeadingTrailingPunctuationRule(BaseRule):
    def __init__(self):
        self.description = (
            "Handles cannot start or end with hyphens, underscores, periods, or spaces"
        )

    def validate(self, handle: str) -> Optional[ValidationResult]:
        if handle[0] in _PUNCTUATION or handle[-1] in _PUNCTUATION:
            return self.error()


# pylint: disable=too-few-public-methods
class HandleValidator:
    validators: list[BaseRule]

    def __init__(self, handles: list[str]):
        self.validators = [
            DuplicateRule(handles),
            ProfaneRule(),
            DigitLimitRule(),
            LengthRule(),
            InvalidCharactersRule(),
            SequentialPunctuationRule(),
            LeadingTrailingPunctuationRule(),
        ]

    def validate(self, handle: str) -> list[ValidationResult]:
        if not handle:
            raise ValueError("handle cannot be empty")

        results = []
        for validator in self.validators:
            result = validator.validate(handle)
            if result:
                results.append(result)

        return results
