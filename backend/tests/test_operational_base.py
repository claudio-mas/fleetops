from app.models.base import OperationalBase


def test_operational_base_is_abstract_with_standard_columns():
    assert OperationalBase.__abstract__ is True
    cols = set(OperationalBase.__annotations__)
    assert {"id", "tenant_id"}.issubset(cols)


def test_operational_base_mixes_in_soft_delete_and_version():
    from app.models.base import OperationalMixin

    assert issubclass(OperationalBase, OperationalMixin)
