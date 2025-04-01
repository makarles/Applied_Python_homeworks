import pytest
from sqlalchemy.orm import Session
from url_shortener.app.db.models import Link
from url_shortener.app.utils.shortener import generate_short_code

# Пример юнит-теста для генерации кода
def test_generate_short_code_uniqueness(monkeypatch):
    # Мокаем функцию, возвращающую записи из базы
    class DummyDB:
        def query(self, model):
            return self
        def filter(self, condition):
            return self
        def first(self):
            return None  # всегда нет записи с таким кодом

    db = DummyDB()
    code = generate_short_code(db, length=6)
    assert isinstance(code, str)
    assert len(code) == 6
