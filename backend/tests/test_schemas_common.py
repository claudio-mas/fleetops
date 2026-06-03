from app.schemas.common import PaginatedResponse


def test_paginated_response_carries_items_and_total():
    page = PaginatedResponse[int](items=[1, 2, 3], total=10, limit=50, offset=0)
    assert page.items == [1, 2, 3]
    assert page.total == 10
    assert page.limit == 50
    assert page.offset == 0
