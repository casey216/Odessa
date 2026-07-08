import re

from sqlalchemy.exc import IntegrityError


def is_unique_violation(exc: IntegrityError) -> bool:
    return getattr(exc.orig, "sqlstate", None) == "23505"


def parse_unique_violation(e: IntegrityError):
    if not e.orig:
        return "Integrity error."
    detail: str = e.orig.args[0]
    match = re.search(r"\((.*?)\)=\((.*?)\)", detail)
    if match:
        field, value = match.group(1), match.group(2)
        return f"{field.replace('_', ' ').title()} '{value}' already exists!"
    return "Integrity error."
