"""
Тесты для асинхронных валидаторов PyValid.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

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
from pyvalid.async_validators import (
    AsyncValidator,
    async_validator,
    AsyncSchemaValidator,
    create_async_schema,
    validate_with_metrics
)

# Настройка логирования для тестов
setup_logging(
    log_file="test_async_validation.log",
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
def async_user_schema():
    """Фикстура для асинхронной схемы пользователя."""
    return create_async_schema({
        "username": StringValidator(min_length=3, max_length=50),
        "email": StringValidator(pattern=r"^[^@]+\.[^@]+\.[^@]+$"),
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

# Тесты для базового асинхронного валидатора
class TestAsyncValidator:
    """Тесты для базового асинхронного валидатора."""
    
    @async_validator
    async def validate_username(self, value: str) -> bool:
        """Асинхронная валидация имени пользователя."""
        await asyncio.sleep(0.1)  # Имитация асинхронной операции
        return len(value) >= 3
    
    @async_validator
    async def validate_email(self, value: str) -> bool:
        """Асинхронная валидация email."""
        await asyncio.sleep(0.1)  # Имитация асинхронной операции
        return "@" in value and "." in value
    
    def test_async_validator_decorator(self):
        """Тест декоратора асинхронного валидатора."""
        validator = self.validate_username
        
        # Проверка валидного значения
        result = asyncio.run(validator("john_doe"))
        assert result is True
        
        # Проверка невалидного значения
        result = asyncio.run(validator("jo"))
        assert result is False
    
    def test_multiple_async_validators(self):
        """Тест нескольких асинхронных валидаторов."""
        username_validator = self.validate_username
        email_validator = self.validate_email
        
        async def validate_user(username: str, email: str) -> bool:
            username_valid = await username_validator(username)
            email_valid = await email_validator(email)
            return username_valid and email_valid
        
        # Проверка валидных данных
        result = asyncio.run(validate_user("john_doe", "john@example.com"))
        assert result is True
        
        # Проверка невалидных данных
        result = asyncio.run(validate_user("jo", "invalid-email"))
        assert result is False

# Тесты для асинхронной схемы валидации
class TestAsyncSchemaValidator:
    """Тесты для асинхронной схемы валидации."""
    
    def test_async_schema_validation(self, async_user_schema, valid_user_data, invalid_user_data):
        """Тест валидации асинхронной схемы."""
        # Проверка валидных данных
        is_valid, errors = asyncio.run(async_user_schema.validate(valid_user_data))
        assert is_valid
        assert errors is None
        
        # Проверка невалидных данных
        is_valid, errors = asyncio.run(async_user_schema.validate(invalid_user_data))
        assert not is_valid
        assert errors is not None
        assert len(errors) > 0
    
    def test_async_schema_strict_mode(self, async_user_schema):
        """Тест строгого режима асинхронной схемы."""
        # Создаем схему в строгом режиме
        strict_schema = create_async_schema(
            {
                "username": StringValidator(min_length=3),
                "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$")
            },
            strict=True
        )
        
        # Данные с лишним полем
        data = {
            "username": "john_doe",
            "email": "john@example.com",
            "extra_field": "value"
        }
        
        # Проверка в строгом режиме
        is_valid, errors = asyncio.run(strict_schema.validate(data))
        assert not is_valid
        assert "extra_field" in str(errors)
    
    def test_async_schema_nested_validation(self):
        """Тест валидации вложенных объектов."""
        # Создаем схему с вложенными объектами
        nested_schema = create_async_schema({
            "user": {
                "username": StringValidator(min_length=3),
                "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
                "profile": {
                    "age": NumberValidator(min_value=18),
                    "is_active": BooleanValidator()
                }
            }
        })
        
        # Валидные данные
        valid_data = {
            "user": {
                "username": "john_doe",
                "email": "john@example.com",
                "profile": {
                    "age": 25,
                    "is_active": True
                }
            }
        }
        
        # Невалидные данные
        invalid_data = {
            "user": {
                "username": "jo",
                "email": "invalid-email",
                "profile": {
                    "age": 15,
                    "is_active": "yes"
                }
            }
        }
        
        # Проверка валидных данных
        is_valid, errors = asyncio.run(nested_schema.validate(valid_data))
        assert is_valid
        assert errors is None
        
        # Проверка невалидных данных
        is_valid, errors = asyncio.run(nested_schema.validate(invalid_data))
        assert not is_valid
        assert errors is not None
        assert len(errors) > 0

# Тесты для метрик асинхронной валидации
class TestAsyncValidationMetrics:
    """Тесты для метрик асинхронной валидации."""
    
    def test_validate_with_metrics(self, async_user_schema, valid_user_data, invalid_user_data):
        """Тест валидации с метриками."""
        from pyvalid.metrics import metrics
        
        # Сброс метрик
        metrics._total_validations = 0
        metrics._total_time = 0
        metrics._success_count = 0
        metrics._failure_count = 0
        metrics._field_times.clear()
        metrics._error_counts.clear()
        
        # Валидация валидных данных
        is_valid, errors = asyncio.run(
            validate_with_metrics(async_user_schema, valid_user_data)
        )
        assert is_valid
        assert errors is None
        
        # Валидация невалидных данных
        is_valid, errors = asyncio.run(
            validate_with_metrics(async_user_schema, invalid_user_data)
        )
        assert not is_valid
        assert errors is not None
        
        # Проверка метрик
        stats = metrics.get_summary()
        assert stats["total_validations"] == 2
        assert stats["success_count"] == 1
        assert stats["failure_count"] == 1
        assert stats["success_rate"] == 0.5
        assert stats["average_time"] > 0
        
        # Проверка метрик полей
        field_stats = metrics.get_field_stats()
        assert len(field_stats) > 0
        
        # Проверка подсчета ошибок
        error_counts = metrics._error_counts
        assert len(error_counts) > 0
        assert sum(error_counts.values()) > 0
    
    def test_async_validation_performance(self, async_user_schema, valid_user_data):
        """Тест производительности асинхронной валидации."""
        import time
        
        # Валидация без метрик
        start_time = time.time()
        is_valid, errors = asyncio.run(async_user_schema.validate(valid_user_data))
        base_time = time.time() - start_time
        
        # Валидация с метриками
        start_time = time.time()
        is_valid, errors = asyncio.run(
            validate_with_metrics(async_user_schema, valid_user_data)
        )
        metrics_time = time.time() - start_time
        
        # Проверка, что время с метриками не слишком отличается
        assert abs(metrics_time - base_time) < 0.1

# Тесты для логирования асинхронной валидации
class TestAsyncValidationLogging:
    """Тесты для логирования асинхронной валидации."""
    
    def test_async_validation_logging(self, async_user_schema, valid_user_data, invalid_user_data):
        """Тест логирования асинхронной валидации."""
        logger = ValidationLogger()
        
        async def validate_with_logging(data: Dict[str, Any]) -> None:
            logger.log_validation_start(data)
            try:
                is_valid, errors = await async_user_schema.validate(data)
                logger.log_validation_end(is_valid, errors)
            except Exception as e:
                logger.log_validation_error(e, {"data": data})
        
        # Логирование валидных данных
        asyncio.run(validate_with_logging(valid_user_data))
        
        # Логирование невалидных данных
        asyncio.run(validate_with_logging(invalid_user_data))
        
        # Логирование ошибки
        async def validate_with_error():
            logger.log_validation_start(invalid_user_data)
            try:
                raise ValueError("Test error")
            except Exception as e:
                logger.log_validation_error(e, {"data": invalid_user_data})
        
        asyncio.run(validate_with_error()) 