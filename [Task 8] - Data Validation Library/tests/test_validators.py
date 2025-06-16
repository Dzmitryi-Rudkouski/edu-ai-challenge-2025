"""
Тесты для валидаторов PyValid.
"""

import pytest
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any, Optional

from pyvalid import (
    Schema,
    validation_context,
    setup_logging,
    async_validator,
    cached_validator,
    ValidationLogger
)
from pyvalid.validators import (
    StringValidator,
    NumberValidator,
    BooleanValidator,
    DateValidator,
    ObjectValidator,
    ArrayValidator
)
from pyvalid.async_validators import AsyncValidator, create_async_schema
from pyvalid.cache import get_cached_regex, clear_regex_cache
from pyvalid.metrics import metrics

# Настройка логирования для тестов
setup_logging(
    log_file="test_validation.log",
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
        "created_at": datetime.now()
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

# Тесты для базовых валидаторов
class TestStringValidator:
    """Тесты для валидатора строк."""
    
    def test_valid_string(self):
        """Тест валидной строки."""
        validator = StringValidator(
            min_length=3,
            max_length=50,
            pattern=r"^[a-zA-Z0-9_]+$"
        )
        
        is_valid, error = validator.validate("john_doe")
        assert is_valid
        assert error is None
    
    def test_invalid_length(self):
        """Тест неверной длины строки."""
        validator = StringValidator(min_length=3, max_length=50)
        
        is_valid, error = validator.validate("jo")
        assert not is_valid
        assert "length" in error.lower()
    
    def test_invalid_pattern(self):
        """Тест неверного шаблона строки."""
        validator = StringValidator(pattern=r"^[a-zA-Z0-9_]+$")
        
        is_valid, error = validator.validate("john@doe")
        assert not is_valid
        assert "pattern" in error.lower()
    
    def test_empty_string(self):
        """Тест пустой строки."""
        validator = StringValidator(min_length=1)
        
        is_valid, error = validator.validate("")
        assert not is_valid
        assert "empty" in error.lower()

class TestNumberValidator:
    """Тесты для валидатора чисел."""
    
    def test_valid_number(self):
        """Тест валидного числа."""
        validator = NumberValidator(min_value=0, max_value=100)
        
        is_valid, error = validator.validate(50)
        assert is_valid
        assert error is None
    
    def test_invalid_range(self):
        """Тест числа вне диапазона."""
        validator = NumberValidator(min_value=0, max_value=100)
        
        is_valid, error = validator.validate(150)
        assert not is_valid
        assert "range" in error.lower()
    
    def test_invalid_type(self):
        """Тест неверного типа."""
        validator = NumberValidator()
        
        is_valid, error = validator.validate("50")
        assert not is_valid
        assert "type" in error.lower()

class TestBooleanValidator:
    """Тесты для валидатора булевых значений."""
    
    def test_valid_boolean(self):
        """Тест валидного булевого значения."""
        validator = BooleanValidator()
        
        is_valid, error = validator.validate(True)
        assert is_valid
        assert error is None
        
        is_valid, error = validator.validate(False)
        assert is_valid
        assert error is None
    
    def test_invalid_type(self):
        """Тест неверного типа."""
        validator = BooleanValidator()
        
        is_valid, error = validator.validate("true")
        assert not is_valid
        assert "type" in error.lower()

class TestDateValidator:
    """Тесты для валидатора дат."""
    
    def test_valid_date(self):
        """Тест валидной даты."""
        validator = DateValidator()
        
        is_valid, error = validator.validate(datetime.now())
        assert is_valid
        assert error is None
    
    def test_invalid_type(self):
        """Тест неверного типа."""
        validator = DateValidator()
        
        is_valid, error = validator.validate("2023-01-01")
        assert not is_valid
        assert "type" in error.lower()
    
    def test_date_range(self):
        """Тест диапазона дат."""
        now = datetime.now()
        validator = DateValidator(
            min_value=now - timedelta(days=30),
            max_value=now + timedelta(days=30)
        )
        
        is_valid, error = validator.validate(now)
        assert is_valid
        assert error is None
        
        is_valid, error = validator.validate(now - timedelta(days=60))
        assert not is_valid
        assert "range" in error.lower()

# Тесты для сложных валидаторов
class TestObjectValidator:
    """Тесты для валидатора объектов."""
    
    def test_valid_object(self, user_schema, valid_user_data):
        """Тест валидного объекта."""
        is_valid, errors = user_schema.validate(valid_user_data)
        assert is_valid
        assert errors is None
    
    def test_invalid_object(self, user_schema, invalid_user_data):
        """Тест невалидного объекта."""
        is_valid, errors = user_schema.validate(invalid_user_data)
        assert not is_valid
        assert errors
        assert len(errors) > 0
    
    def test_missing_required_field(self, user_schema):
        """Тест отсутствующего обязательного поля."""
        data = {
            "username": "john_doe",
            "email": "john@example.com",
            "age": 25,
            "is_active": True
            # Отсутствует created_at
        }
        
        is_valid, errors = user_schema.validate(data)
        assert not is_valid
        assert "created_at" in errors
    
    def test_extra_field(self, user_schema, valid_user_data):
        """Тест дополнительного поля."""
        data = valid_user_data.copy()
        data["extra_field"] = "value"
        
        is_valid, errors = user_schema.validate(data)
        assert is_valid  # По умолчанию дополнительные поля разрешены
        assert errors is None
        
        # Тест строгого режима
        with validation_context(data, strict_mode=True) as context:
            is_valid, errors = user_schema.validate(data)
            assert not is_valid
            assert "extra_field" in errors

class TestArrayValidator:
    """Тесты для валидатора массивов."""
    
    def test_valid_array(self):
        """Тест валидного массива."""
        validator = ArrayValidator(
            StringValidator(pattern=r"^[a-zA-Z]+$"),
            min_length=1,
            max_length=3
        )
        
        is_valid, error = validator.validate(["abc", "def"])
        assert is_valid
        assert error is None
    
    def test_invalid_length(self):
        """Тест неверной длины массива."""
        validator = ArrayValidator(min_length=2, max_length=3)
        
        is_valid, error = validator.validate(["abc"])
        assert not is_valid
        assert "length" in error.lower()
    
    def test_invalid_items(self):
        """Тест неверных элементов массива."""
        validator = ArrayValidator(StringValidator(pattern=r"^[a-zA-Z]+$"))
        
        is_valid, error = validator.validate(["abc", "123"])
        assert not is_valid
        assert "items" in error.lower()

# Тесты для асинхронных валидаторов
class TestAsyncValidator:
    """Тесты для асинхронных валидаторов."""
    
    @pytest.mark.asyncio
    async def test_valid_async_validation(self):
        """Тест асинхронной валидации."""
        @async_validator("Invalid email")
        async def validate_email(email: str) -> bool:
            await asyncio.sleep(0.1)
            return email in {"john@example.com", "jane@example.com"}
        
        validator = AsyncValidator(validate_email)
        is_valid, error = await validator.validate("john@example.com")
        assert is_valid
        assert error is None
        
        is_valid, error = await validator.validate("invalid@example.com")
        assert not is_valid
        assert error == "Invalid email"
    
    @pytest.mark.asyncio
    async def test_async_schema(self):
        """Тест асинхронной схемы."""
        async def validate_username(username: str) -> bool:
            await asyncio.sleep(0.1)
            return len(username) >= 3
        
        async_schema = create_async_schema({
            "username": validate_username,
            "email": lambda x: (len(x) >= 5, "Email too short")
        })
        
        data = {
            "username": "john",
            "email": "short"
        }
        
        is_valid, errors = await async_schema.validate(data)
        assert not is_valid
        assert "email" in errors
        assert "username" not in errors

# Тесты для кэширования
class TestCaching:
    """Тесты для кэширования."""
    
    def test_regex_cache(self):
        """Тест кэширования регулярных выражений."""
        pattern = r"^[a-zA-Z0-9_]+$"
        
        # Первый вызов компилирует регулярное выражение
        regex1 = get_cached_regex(pattern)
        assert regex1.pattern == pattern
        
        # Второй вызов использует кэш
        regex2 = get_cached_regex(pattern)
        assert regex1 is regex2  # Тот же объект
        
        # Очистка кэша
        clear_regex_cache()
        regex3 = get_cached_regex(pattern)
        assert regex3 is not regex1  # Новый объект
    
    def test_validator_cache(self):
        """Тест кэширования валидаторов."""
        @cached_validator(maxsize=128)
        def validate_email(email: str) -> tuple[bool, Optional[str]]:
            return "@" in email, "Invalid email format"
        
        # Первый вызов
        is_valid1, error1 = validate_email("john@example.com")
        assert is_valid1
        assert error1 is None
        
        # Второй вызов использует кэш
        is_valid2, error2 = validate_email("john@example.com")
        assert is_valid2
        assert error2 is None
        
        # Проверка информации о кэше
        cache_info = validate_email.cache_info()
        assert cache_info.hits > 0
        assert cache_info.misses > 0

# Тесты для метрик
class TestMetrics:
    """Тесты для метрик валидации."""
    
    def test_validation_metrics(self, user_schema, valid_user_data):
        """Тест сбора метрик валидации."""
        # Сброс метрик
        metrics._total_validations = 0
        metrics._total_time = 0
        metrics._success_count = 0
        metrics._failure_count = 0
        metrics._field_times.clear()
        metrics._error_counts.clear()
        
        # Выполнение валидации
        with validation_context(valid_user_data) as context:
            is_valid, errors = user_schema.validate(valid_user_data)
        
        # Проверка метрик
        assert metrics._total_validations > 0
        assert metrics._total_time > 0
        assert metrics._success_count > 0
        assert metrics._failure_count == 0
        
        # Проверка статистики
        stats = metrics.get_summary()
        assert stats["total_validations"] > 0
        assert stats["success_rate"] == 1.0
        assert stats["average_time"] > 0
    
    def test_field_metrics(self, user_schema, invalid_user_data):
        """Тест метрик для полей."""
        # Сброс метрик
        metrics._field_times.clear()
        metrics._error_counts.clear()
        
        # Выполнение валидации
        with validation_context(invalid_user_data) as context:
            is_valid, errors = user_schema.validate(invalid_user_data)
        
        # Проверка метрик полей
        field_stats = metrics.get_field_stats()
        assert len(field_stats) > 0
        
        # Проверка подсчета ошибок
        error_counts = metrics._error_counts
        assert len(error_counts) > 0
        assert sum(error_counts.values()) > 0

# Тесты для логирования
class TestLogging:
    """Тесты для логирования."""
    
    def test_validation_logging(self, user_schema, valid_user_data):
        """Тест логирования валидации."""
        logger = ValidationLogger()
        
        # Логирование начала валидации
        logger.log_validation_start(valid_user_data)
        
        # Логирование валидации полей
        with validation_context(valid_user_data) as context:
            for field, value in valid_user_data.items():
                logger.log_field_validation(field, value, True, None)
        
        # Логирование завершения валидации
        logger.log_validation_end(True, None)
    
    def test_error_logging(self, user_schema, invalid_user_data):
        """Тест логирования ошибок."""
        logger = ValidationLogger()
        
        try:
            with validation_context(invalid_user_data) as context:
                is_valid, errors = user_schema.validate(invalid_user_data)
                if not is_valid:
                    raise ValueError("Validation failed")
        except Exception as e:
            logger.log_validation_error(e, {"data": invalid_user_data})
    
    def test_log_formatting(self):
        """Тест форматирования логов."""
        from pyvalid.logging import ValidationFormatter
        
        formatter = ValidationFormatter(include_metrics=True)
        record = logging.LogRecord(
            "test",
            logging.INFO,
            "test.py",
            1,
            "Test message",
            (),
            None
        )
        
        # Добавление дополнительных полей
        record.validation_path = "user.email"
        record.validation_data = {"value": "test@example.com"}
        
        # Форматирование записи
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["message"] == "Test message"
        assert log_data["validation_path"] == "user.email"
        assert log_data["validation_data"]["value"] == "test@example.com"
        assert "metrics" in log_data 