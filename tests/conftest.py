"""Shared fixtures: every test gets its own freshly seeded temporary database."""
import pytest

from cart import ShoppingCart
from repository import StoreRepository
from setup_db import initialize

# Seed data: LAP-01 999.99 (stock 5), MOU-01 29.95 (stock 20), USB-01 9.99 (stock 50)


@pytest.fixture
def repo(tmp_path):
    db = tmp_path / 'test.db'
    initialize(str(db))
    return StoreRepository(str(db))


@pytest.fixture
def cart(repo):
    return ShoppingCart('alice', repo)
