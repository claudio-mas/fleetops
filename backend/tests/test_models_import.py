def test_models_importable() -> None:
    from app.models.base import Base, OperationalMixin, TimestampMixin  # noqa: F401

    assert Base is not None
