from cumcm_py.types import CheckReport, ModelResult, ValidationIssue


def test_shared_types_are_importable() -> None:
    assert CheckReport.__name__ == "CheckReport"
    assert ModelResult.__name__ == "ModelResult"
    assert ValidationIssue.__name__ == "ValidationIssue"
