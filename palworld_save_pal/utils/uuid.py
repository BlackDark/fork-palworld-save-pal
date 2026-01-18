from typing import Any
import uuid


def is_valid_uuid(uuid_test: Any) -> bool:
    try:
        uuid.UUID(str(uuid_test))
        return True
    except ValueError:
        return False


def is_empty_uuid(uuid_test: Any) -> bool:
    return str(uuid_test) == "00000000-0000-0000-0000-000000000000"


def are_equal_uuids(uuid1: Any, uuid2: Any) -> bool:
    return str(uuid1).lower() == str(uuid2).lower()


def parse_uuid_from_string(uuid_str: str) -> uuid.UUID:
    """
    Parse a UUID string that may or may not contain dashes.
    Handles both formats: "5F34119C000000000000000000000000" and "5F34119C-0000-0000-0000-000000000000"
    """
    uuid_str = str(uuid_str).strip()
    if len(uuid_str) == 32:  # UUID without dashes (32 hex chars)
        # Insert dashes to make it a valid UUID format
        uuid_str = f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:]}"
    return uuid.UUID(uuid_str)
