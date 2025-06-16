"""
Тесты для контекста валидации в PyValid.
"""

import pytest
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import tempfile

from pyvalid import (
    Schema,
    validation_context,
    setup_logging,
    ValidationLogger
)
from pyvalid.validators import (
    StringValidator,
    NumberValidator,
    BooleanValidator,
    DateValidator
)
from pyvalid.context import (
    ValidationContext,
    current_context
)

# Настройка логирования для тестов
setup_logging(
    log_file="test_context.log",
    log_level=logging.DEBUG,
    include_metrics=True
)

logger = ValidationLogger()

# Фикстуры
@pytest.fixture
def user_schema():
    """Фикстура для схемы пользователя."""
    return Schema({
        "username": StringValidator(min_length=3, max_length=50),
        "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
        "age": NumberValidator(min_value=18, max_value=120),
        "is_active": BooleanValidator(),
        "created_at": DateValidator()
    })

@pytest.fixture
def valid_user_data():
    """Фикстура для валидных данных пользователя."""
    return {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 25,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def invalid_user_data():
    """Фикстура для невалидных данных пользователя."""
    return {
        "username": "jo",  # Слишком короткое имя
        "email": "invalid-email",  # Неверный формат email
        "age": 15,  # Слишком молодой
        "is_active": "yes",  # Неверный тип
        "created_at": "invalid-date"  # Неверный формат даты
    }

# Тесты для базового контекста
class TestValidationContext:
    """Тесты для базового контекста валидации."""
    
    def test_context_initialization(self, valid_user_data):
        """Тест инициализации контекста."""
        context = ValidationContext(valid_user_data)
        
        assert context._field_path == []
        assert context._data == valid_user_data
        assert context._custom_validators == {}
        assert context._strict_mode is False
    
    def test_context_with_strict_mode(self, valid_user_data):
        """Тест контекста в строгом режиме."""
        context = ValidationContext(valid_user_data, strict=True)
        
        assert context._strict_mode is True
        assert context.is_strict_mode() is True
    
    def test_context_with_custom_validators(self, valid_user_data):
        """Тест контекста с пользовательскими валидаторами."""
        custom_validators = {
            "username": lambda x: len(x) >= 3,
            "email": lambda x: "@" in x
        }
        
        context = ValidationContext(
            valid_user_data,
            custom_validators=custom_validators
        )
        
        assert context._custom_validators == custom_validators
        assert context.get_custom_validator("username") is not None
        assert context.get_custom_validator("email") is not None
        assert context.get_custom_validator("age") is None

# Тесты для работы с полями
class TestFieldContext:
    """Тесты для работы с полями в контексте."""
    
    def test_enter_field(self, valid_user_data):
        """Тест входа в контекст поля."""
        context = ValidationContext(valid_user_data)
        
        with context.enter_field("username"):
            assert context._field_path == ["username"]
            assert context.get_full_path() == "username"
            
            with context.enter_field("nested"):
                assert context._field_path == ["username", "nested"]
                assert context.get_full_path() == "username.nested"
        
        assert context._field_path == []
        assert context.get_full_path() == ""
    
    def test_get_field_value(self, valid_user_data):
        """Тест получения значения поля."""
        context = ValidationContext(valid_user_data)
        
        # Получение значения корневого поля
        assert context.get_field_value("username") == "john_doe"
        assert context.get_field_value("email") == "john@example.com"
        
        # Получение значения вложенного поля
        nested_data = {
            "user": {
                "profile": {
                    "name": "John Doe"
                }
            }
        }
        context = ValidationContext(nested_data)
        
        with context.enter_field("user"):
            with context.enter_field("profile"):
                assert context.get_field_value("name") == "John Doe"
    
    def test_get_full_path(self, valid_user_data):
        """Тест получения полного пути поля."""
        context = ValidationContext(valid_user_data)
        
        assert context.get_full_path() == ""
        
        with context.enter_field("user"):
            assert context.get_full_path() == "user"
            
            with context.enter_field("profile"):
                assert context.get_full_path() == "user.profile"
                
                with context.enter_field("name"):
                    assert context.get_full_path() == "user.profile.name"
        
        assert context.get_full_path() == ""

# Тесты для валидации в контексте
class TestContextValidation:
    """Тесты для валидации в контексте."""
    
    def test_validate_with_context(self, user_schema, valid_user_data):
        """Тест валидации в контексте."""
        with validation_context(valid_user_data) as context:
            is_valid, errors = user_schema.validate(valid_user_data)
            assert is_valid
            assert errors is None
            
            # Проверка пути валидации
            assert context.get_full_path() == ""
            
            # Проверка значения поля
            assert context.get_field_value("username") == "john_doe"
    
    def test_validate_nested_fields(self, user_schema):
        """Тест валидации вложенных полей."""
        nested_data = {
            "user": {
                "username": "john_doe",
                "email": "john@example.com",
                "profile": {
                    "age": 25,
                    "is_active": True
                }
            }
        }
        
        nested_schema = Schema({
            "user": {
                "username": StringValidator(min_length=3),
                "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
                "profile": {
                    "age": NumberValidator(min_value=18),
                    "is_active": BooleanValidator()
                }
            }
        })
        
        with validation_context(nested_data) as context:
            is_valid, errors = nested_schema.validate(nested_data)
            assert is_valid
            assert errors is None
            
            with context.enter_field("user"):
                assert context.get_field_value("username") == "john_doe"
                
                with context.enter_field("profile"):
                    assert context.get_field_value("age") == 25
                    assert context.get_field_value("is_active") is True
    
    def test_validate_with_custom_validators(self, valid_user_data):
        """Тест валидации с пользовательскими валидаторами."""
        custom_validators = {
            "username": lambda x: len(x) >= 3 and x.isalnum(),
            "email": lambda x: "@" in x and "." in x.split("@")[1]
        }
        
        with validation_context(
            valid_user_data,
            custom_validators=custom_validators
        ) as context:
            # Проверка пользовательских валидаторов
            username_validator = context.get_custom_validator("username")
            email_validator = context.get_custom_validator("email")
            
            assert username_validator(valid_user_data["username"]) is True
            assert email_validator(valid_user_data["email"]) is True
            
            # Проверка несуществующего валидатора
            assert context.get_custom_validator("age") is None

# Тесты для интеграции контекста
class TestContextIntegration:
    """Тесты для интеграции контекста."""
    
    def test_context_with_metrics(self, user_schema, valid_user_data):
        """Тест контекста с метриками."""
        from pyvalid.metrics import metrics
        
        with validation_context(valid_user_data) as context:
            with metrics.start_validation():
                is_valid, errors = user_schema.validate(valid_user_data)
                metrics.end_validation(is_valid, errors)
            
            # Проверка метрик
            summary = metrics.get_summary()
            assert summary["total_validations"] == 1
            assert summary["success_count"] == 1
            assert summary["failure_count"] == 0
    
    def test_context_with_logging(self, user_schema, valid_user_data):
        """Тест контекста с логированием."""
        logger = ValidationLogger()
        
        with validation_context(valid_user_data) as context:
            logger.log_validation_start(valid_user_data)
            
            with context.enter_field("username"):
                is_valid, errors = user_schema.validate_field(
                    "username",
                    valid_user_data["username"]
                )
                logger.log_field_validation("username", is_valid, errors)
            
            is_valid, errors = user_schema.validate(valid_user_data)
            logger.log_validation_end(is_valid, errors)
    
    def test_context_with_caching(self, valid_user_data):
        """Тест контекста с кэшированием."""
        from pyvalid.cache import cached_validator
        
        @cached_validator
        def validate_username(value: str) -> bool:
            return len(value) >= 3
        
        with validation_context(valid_user_data) as context:
            # Первая валидация
            is_valid1 = validate_username(valid_user_data["username"])
            
            # Вторая валидация (из кэша)
            is_valid2 = validate_username(valid_user_data["username"])
            
            assert is_valid1 is True
            assert is_valid2 is True
    
    def test_context_with_async_validation(self, valid_user_data):
        """Тест контекста с асинхронной валидацией."""
        import asyncio
        from pyvalid.async_validators import async_validator
        
        @async_validator
        async def validate_async(value: str) -> bool:
            await asyncio.sleep(0.1)
            return len(value) >= 3
        
        async def validate_in_context():
            with validation_context(valid_user_data) as context:
                is_valid = await validate_async(valid_user_data["username"])
                assert is_valid is True
                
                with context.enter_field("username"):
                    assert context.get_field_value("username") == "john_doe"
        
        asyncio.run(validate_in_context())
    
    def test_nested_contexts(self, valid_user_data):
        """Тест вложенных контекстов."""
        with validation_context(valid_user_data) as outer_context:
            assert outer_context.get_full_path() == ""
            
            with validation_context({"nested": "value"}) as inner_context:
                assert inner_context.get_full_path() == ""
                assert inner_context.get_field_value("nested") == "value"
            
            assert outer_context.get_full_path() == ""
            assert outer_context.get_field_value("username") == "john_doe"
    
    def test_context_error_handling(self, user_schema, invalid_user_data):
        """Тест обработки ошибок в контексте."""
        with validation_context(invalid_user_data) as context:
            try:
                with context.enter_field("username"):
                    is_valid, errors = user_schema.validate_field(
                        "username",
                        invalid_user_data["username"]
                    )
                    assert not is_valid
                    assert errors is not None
            except Exception as e:
                pytest.fail(f"Unexpected exception: {e}")
            
            assert context.get_full_path() == ""
    
    def test_context_cleanup(self, valid_user_data):
        """Тест очистки контекста."""
        context = ValidationContext(valid_user_data)
        
        with context.enter_field("username"):
            assert context.get_full_path() == "username"
        
        # Проверяем, что контекст очищен
        assert context.get_full_path() == ""
        assert context._field_path == []
        
        # Проверяем, что глобальный контекст не затронут
        assert current_context.get() is None 