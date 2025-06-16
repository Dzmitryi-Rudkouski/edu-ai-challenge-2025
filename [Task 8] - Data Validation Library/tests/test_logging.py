"""
Тесты для логирования в PyValid.
"""

import pytest
import logging
import json
import os
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
from pyvalid.logging import (
    ValidationFormatter,
    setup_logging,
    log_validation,
    ValidationLogger
)

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

@pytest.fixture
def temp_log_file():
    """Фикстура для временного файла логов."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
        return f.name

# Тесты для форматирования логов
class TestValidationFormatter:
    """Тесты для форматирования логов."""
    
    def test_formatter_initialization(self):
        """Тест инициализации форматтера."""
        formatter = ValidationFormatter()
        assert formatter.include_metrics is False
        
        formatter_with_metrics = ValidationFormatter(include_metrics=True)
        assert formatter_with_metrics.include_metrics is True
    
    def test_format_record(self, temp_log_file):
        """Тест форматирования записи лога."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = logging.getLogger("pyvalid")
        formatter = ValidationFormatter(include_metrics=True)
        
        # Создаем тестовую запись
        record = logging.LogRecord(
            name="pyvalid",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Добавляем дополнительные поля
        record.validation_path = "user.username"
        record.validation_data = {"username": "john_doe"}
        record.metrics = {
            "validation_time": 0.1,
            "field_times": {"username": 0.05}
        }
        
        # Форматируем запись
        formatted = formatter.format(record)
        
        # Проверяем форматирование
        assert "Test message" in formatted
        assert "user.username" in formatted
        assert "john_doe" in formatted
        assert "0.1" in formatted
        assert "0.05" in formatted
    
    def test_format_without_metrics(self, temp_log_file):
        """Тест форматирования без метрик."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=False
        )
        
        logger = logging.getLogger("pyvalid")
        formatter = ValidationFormatter(include_metrics=False)
        
        # Создаем тестовую запись
        record = logging.LogRecord(
            name="pyvalid",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Добавляем дополнительные поля
        record.validation_path = "user.username"
        record.validation_data = {"username": "john_doe"}
        
        # Форматируем запись
        formatted = formatter.format(record)
        
        # Проверяем форматирование
        assert "Test message" in formatted
        assert "user.username" in formatted
        assert "john_doe" in formatted
        assert "metrics" not in formatted.lower()

# Тесты для настройки логирования
class TestLoggingSetup:
    """Тесты для настройки логирования."""
    
    def test_setup_logging(self, temp_log_file):
        """Тест настройки логирования."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = logging.getLogger("pyvalid")
        
        # Проверяем настройки
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0
        
        # Проверяем наличие файлового обработчика
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is not None
        assert file_handler.baseFilename == temp_log_file
    
    def test_setup_with_console(self, temp_log_file):
        """Тест настройки с выводом в консоль."""
        # Настройка логирования с выводом в консоль
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True,
            console_output=True
        )
        
        logger = logging.getLogger("pyvalid")
        
        # Проверяем наличие консольного обработчика
        console_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.StreamHandler)),
            None
        )
        assert console_handler is not None
    
    def test_setup_with_custom_format(self, temp_log_file):
        """Тест настройки с пользовательским форматом."""
        custom_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Настройка логирования с пользовательским форматом
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True,
            log_format=custom_format
        )
        
        logger = logging.getLogger("pyvalid")
        formatter = logger.handlers[0].formatter
        
        # Проверяем формат
        assert isinstance(formatter, ValidationFormatter)
        assert formatter._fmt == custom_format

# Тесты для логирования валидации
class TestValidationLogging:
    """Тесты для логирования валидации."""
    
    def test_log_validation(self, temp_log_file, user_schema, valid_user_data):
        """Тест логирования валидации."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Логирование валидации
        logger.log_validation_start(valid_user_data)
        is_valid, errors = user_schema.validate(valid_user_data)
        logger.log_validation_end(is_valid, errors)
        
        # Проверяем содержимое лог-файла
        with open(temp_log_file, "r") as f:
            log_content = f.read()
            
            assert "Starting validation" in log_content
            assert "Validation completed" in log_content
            assert "john_doe" in log_content
            assert "john@example.com" in log_content
    
    def test_log_validation_error(self, temp_log_file, user_schema, invalid_user_data):
        """Тест логирования ошибок валидации."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Логирование ошибки валидации
        logger.log_validation_start(invalid_user_data)
        is_valid, errors = user_schema.validate(invalid_user_data)
        logger.log_validation_end(is_valid, errors)
        
        # Проверяем содержимое лог-файла
        with open(temp_log_file, "r") as f:
            log_content = f.read()
            
            assert "Starting validation" in log_content
            assert "Validation failed" in log_content
            assert "jo" in log_content
            assert "invalid-email" in log_content
            assert "validation_errors" in log_content
    
    def test_log_validation_exception(self, temp_log_file):
        """Тест логирования исключений при валидации."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Логирование исключения
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.log_validation_error(e, {"data": {"test": "value"}})
        
        # Проверяем содержимое лог-файла
        with open(temp_log_file, "r") as f:
            log_content = f.read()
            
            assert "Validation error" in log_content
            assert "Test error" in log_content
            assert "test" in log_content
            assert "value" in log_content
    
    def test_log_validation_with_context(self, temp_log_file, user_schema, valid_user_data):
        """Тест логирования валидации в контексте."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Логирование в контексте
        with validation_context(valid_user_data) as context:
            logger.log_validation_start(valid_user_data)
            with context.enter_field("username"):
                is_valid, errors = user_schema.validate_field("username", valid_user_data["username"])
                logger.log_field_validation("username", is_valid, errors)
            is_valid, errors = user_schema.validate(valid_user_data)
            logger.log_validation_end(is_valid, errors)
        
        # Проверяем содержимое лог-файла
        with open(temp_log_file, "r") as f:
            log_content = f.read()
            
            assert "Starting validation" in log_content
            assert "Validating field: username" in log_content
            assert "Validation completed" in log_content
            assert "john_doe" in log_content

# Тесты для интеграции логирования
class TestLoggingIntegration:
    """Тесты для интеграции логирования."""
    
    def test_logging_with_metrics(self, temp_log_file, user_schema, valid_user_data):
        """Тест логирования с метриками."""
        from pyvalid.metrics import metrics
        
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Валидация с метриками и логированием
        logger.log_validation_start(valid_user_data)
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(valid_user_data)
            metrics.end_validation(is_valid, errors)
        logger.log_validation_end(is_valid, errors)
        
        # Проверяем содержимое лог-файла
        with open(temp_log_file, "r") as f:
            log_content = f.read()
            
            assert "Starting validation" in log_content
            assert "Validation completed" in log_content
            assert "metrics" in log_content.lower()
            assert "validation_time" in log_content.lower()
    
    def test_logging_with_caching(self, temp_log_file, user_schema, valid_user_data):
        """Тест логирования с кэшированием."""
        from pyvalid.cache import cached_validator
        
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Создаем кэшированный валидатор
        @cached_validator
        def validate_username(value: str) -> bool:
            return len(value) >= 3
        
        # Валидация с кэшированием и логированием
        logger.log_validation_start(valid_user_data)
        is_valid = validate_username(valid_user_data["username"])
        logger.log_validation_end(is_valid, None)
        
        # Повторная валидация (из кэша)
        logger.log_validation_start(valid_user_data)
        is_valid = validate_username(valid_user_data["username"])
        logger.log_validation_end(is_valid, None)
        
        # Проверяем содержимое лог-файла
        with open(temp_log_file, "r") as f:
            log_content = f.read()
            
            assert "Starting validation" in log_content
            assert "Validation completed" in log_content
            assert "cache" in log_content.lower()
    
    def test_logging_with_async_validation(self, temp_log_file, user_schema, valid_user_data):
        """Тест логирования с асинхронной валидацией."""
        import asyncio
        from pyvalid.async_validators import async_validator
        
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Создаем асинхронный валидатор
        @async_validator
        async def validate_async(value: str) -> bool:
            await asyncio.sleep(0.1)
            return len(value) >= 3
        
        async def validate_with_logging():
            logger.log_validation_start(valid_user_data)
            is_valid = await validate_async(valid_user_data["username"])
            logger.log_validation_end(is_valid, None)
        
        # Запускаем асинхронную валидацию
        asyncio.run(validate_with_logging())
        
        # Проверяем содержимое лог-файла
        with open(temp_log_file, "r") as f:
            log_content = f.read()
            
            assert "Starting validation" in log_content
            assert "Validation completed" in log_content
            assert "async" in log_content.lower()
    
    def test_logging_cleanup(self, temp_log_file):
        """Тест очистки логов."""
        # Настройка логирования
        setup_logging(
            log_file=temp_log_file,
            log_level=logging.DEBUG,
            include_metrics=True
        )
        
        logger = ValidationLogger()
        
        # Логируем тестовое сообщение
        logger.log_validation_start({"test": "value"})
        
        # Проверяем, что файл создан
        assert os.path.exists(temp_log_file)
        
        # Очищаем файл
        with open(temp_log_file, "w") as f:
            f.write("")
        
        # Проверяем, что файл пуст
        with open(temp_log_file, "r") as f:
            assert f.read() == ""
        
        # Удаляем временный файл
        os.unlink(temp_log_file)
        assert not os.path.exists(temp_log_file) 