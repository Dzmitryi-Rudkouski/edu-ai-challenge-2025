"""
Тесты для метрик валидации в PyValid.
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import statistics

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
from pyvalid.metrics import (
    ValidationMetrics,
    metrics
)

# Настройка логирования для тестов
setup_logging(
    log_file="test_metrics.log",
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

# Тесты для базовых метрик
class TestValidationMetrics:
    """Тесты для базовых метрик валидации."""
    
    def test_metrics_initialization(self):
        """Тест инициализации метрик."""
        metrics = ValidationMetrics()
        
        assert metrics._total_validations == 0
        assert metrics._total_time == 0
        assert metrics._success_count == 0
        assert metrics._failure_count == 0
        assert metrics._field_times == {}
        assert metrics._error_counts == {}
    
    def test_validation_tracking(self, user_schema, valid_user_data, invalid_user_data):
        """Тест отслеживания валидации."""
        metrics = ValidationMetrics()
        
        # Валидация валидных данных
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(valid_user_data)
            metrics.end_validation(is_valid, errors)
        
        # Валидация невалидных данных
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(invalid_user_data)
            metrics.end_validation(is_valid, errors)
        
        # Проверка метрик
        assert metrics._total_validations == 2
        assert metrics._success_count == 1
        assert metrics._failure_count == 1
        assert metrics._total_time > 0
    
    def test_field_times_tracking(self, user_schema, valid_user_data):
        """Тест отслеживания времени валидации полей."""
        metrics = ValidationMetrics()
        
        with metrics.start_validation():
            with validation_context(valid_user_data) as context:
                # Валидация каждого поля
                for field in valid_user_data:
                    with context.enter_field(field):
                        start_time = time.time()
                        is_valid, errors = user_schema.validate_field(field, valid_user_data[field])
                        field_time = time.time() - start_time
                        metrics._field_times.setdefault(field, []).append(field_time)
        
        # Проверка метрик полей
        assert len(metrics._field_times) == len(valid_user_data)
        for field in valid_user_data:
            assert field in metrics._field_times
            assert len(metrics._field_times[field]) == 1
    
    def test_error_counts_tracking(self, user_schema, invalid_user_data):
        """Тест отслеживания количества ошибок."""
        metrics = ValidationMetrics()
        
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(invalid_user_data)
            metrics.end_validation(is_valid, errors)
        
        # Проверка подсчета ошибок
        assert len(metrics._error_counts) > 0
        assert sum(metrics._error_counts.values()) > 0

# Тесты для статистики метрик
class TestMetricsStatistics:
    """Тесты для статистики метрик."""
    
    def test_get_field_stats(self, user_schema, valid_user_data):
        """Тест получения статистики по полям."""
        metrics = ValidationMetrics()
        
        # Множественные валидации для накопления статистики
        for _ in range(3):
            with metrics.start_validation():
                with validation_context(valid_user_data) as context:
                    for field in valid_user_data:
                        with context.enter_field(field):
                            start_time = time.time()
                            is_valid, errors = user_schema.validate_field(field, valid_user_data[field])
                            field_time = time.time() - start_time
                            metrics._field_times.setdefault(field, []).append(field_time)
        
        # Получение статистики
        field_stats = metrics.get_field_stats()
        
        # Проверка статистики
        assert len(field_stats) == len(valid_user_data)
        for field, stats in field_stats.items():
            assert "min" in stats
            assert "max" in stats
            assert "avg" in stats
            assert "count" in stats
            assert stats["count"] == 3
    
    def test_get_summary(self, user_schema, valid_user_data, invalid_user_data):
        """Тест получения общего свода метрик."""
        metrics = ValidationMetrics()
        
        # Валидация валидных данных
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(valid_user_data)
            metrics.end_validation(is_valid, errors)
        
        # Валидация невалидных данных
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(invalid_user_data)
            metrics.end_validation(is_valid, errors)
        
        # Получение свода
        summary = metrics.get_summary()
        
        # Проверка свода
        assert summary["total_validations"] == 2
        assert summary["success_count"] == 1
        assert summary["failure_count"] == 1
        assert summary["success_rate"] == 0.5
        assert summary["average_time"] > 0
        assert "field_stats" in summary
    
    def test_metrics_reset(self, user_schema, valid_user_data):
        """Тест сброса метрик."""
        metrics = ValidationMetrics()
        
        # Заполняем метрики
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(valid_user_data)
            metrics.end_validation(is_valid, errors)
        
        # Сброс метрик
        metrics._total_validations = 0
        metrics._total_time = 0
        metrics._success_count = 0
        metrics._failure_count = 0
        metrics._field_times.clear()
        metrics._error_counts.clear()
        
        # Проверка сброса
        assert metrics._total_validations == 0
        assert metrics._total_time == 0
        assert metrics._success_count == 0
        assert metrics._failure_count == 0
        assert len(metrics._field_times) == 0
        assert len(metrics._error_counts) == 0

# Тесты для интеграции метрик с валидацией
class TestMetricsIntegration:
    """Тесты для интеграции метрик с валидацией."""
    
    def test_metrics_with_context(self, user_schema, valid_user_data, invalid_user_data):
        """Тест метрик в контексте валидации."""
        # Сброс глобальных метрик
        metrics._total_validations = 0
        metrics._total_time = 0
        metrics._success_count = 0
        metrics._failure_count = 0
        metrics._field_times.clear()
        metrics._error_counts.clear()
        
        # Валидация в контексте
        with validation_context(valid_user_data) as context:
            with metrics.start_validation():
                is_valid, errors = user_schema.validate(valid_user_data)
                metrics.end_validation(is_valid, errors)
        
        with validation_context(invalid_user_data) as context:
            with metrics.start_validation():
                is_valid, errors = user_schema.validate(invalid_user_data)
                metrics.end_validation(is_valid, errors)
        
        # Проверка метрик
        summary = metrics.get_summary()
        assert summary["total_validations"] == 2
        assert summary["success_count"] == 1
        assert summary["failure_count"] == 1
    
    def test_metrics_with_logging(self, user_schema, valid_user_data, invalid_user_data):
        """Тест метрик с логированием."""
        logger = ValidationLogger()
        
        # Валидация с логированием
        logger.log_validation_start(valid_user_data)
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(valid_user_data)
            metrics.end_validation(is_valid, errors)
        logger.log_validation_end(is_valid, errors)
        
        logger.log_validation_start(invalid_user_data)
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(invalid_user_data)
            metrics.end_validation(is_valid, errors)
        logger.log_validation_end(is_valid, errors)
        
        # Проверка метрик
        summary = metrics.get_summary()
        assert summary["total_validations"] == 2
        assert summary["success_count"] == 1
        assert summary["failure_count"] == 1
    
    def test_metrics_performance(self, user_schema, valid_user_data):
        """Тест производительности метрик."""
        # Валидация без метрик
        start_time = time.time()
        is_valid, errors = user_schema.validate(valid_user_data)
        base_time = time.time() - start_time
        
        # Валидация с метриками
        start_time = time.time()
        with metrics.start_validation():
            is_valid, errors = user_schema.validate(valid_user_data)
            metrics.end_validation(is_valid, errors)
        metrics_time = time.time() - start_time
        
        # Проверка, что время с метриками не слишком отличается
        assert abs(metrics_time - base_time) < 0.1
    
    def test_metrics_concurrent_validation(self, user_schema):
        """Тест метрик при параллельной валидации."""
        import threading
        
        def validate_data(data: Dict[str, Any]) -> None:
            with metrics.start_validation():
                is_valid, errors = user_schema.validate(data)
                metrics.end_validation(is_valid, errors)
        
        # Создаем несколько потоков для валидации
        threads = []
        test_data = [
            {
                "username": f"user_{i}",
                "email": f"user_{i}@example.com",
                "age": 20 + i,
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
            for i in range(5)
        ]
        
        # Запускаем валидацию в разных потоках
        for data in test_data:
            thread = threading.Thread(target=validate_data, args=(data,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем метрики
        summary = metrics.get_summary()
        assert summary["total_validations"] == len(test_data)
        assert summary["success_count"] == len(test_data)
        assert summary["failure_count"] == 0 