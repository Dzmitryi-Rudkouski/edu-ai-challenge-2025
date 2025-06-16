"""
Тесты для кэширования в PyValid.
"""

import pytest
import re
import time
from typing import Dict, Any, Optional, Pattern
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
from pyvalid.cache import (
    get_cached_regex,
    clear_regex_cache,
    cached_validator,
    ValidatorCache
)

# Настройка логирования для тестов
setup_logging(
    log_file="test_caching.log",
    log_level=logging.DEBUG,
    include_metrics=True
)

logger = ValidationLogger()

# Фикстуры
@pytest.fixture
def regex_patterns():
    """Фикстура для регулярных выражений."""
    return [
        r"^[^@]+@[^@]+\.[^@]+$",  # Email
        r"^\d{3}-\d{3}-\d{4}$",   # Phone
        r"^[A-Za-z0-9_]+$",       # Username
        r"^\d{4}-\d{2}-\d{2}$"    # Date
    ]

@pytest.fixture
def validator_cache():
    """Фикстура для кэша валидаторов."""
    return ValidatorCache()

# Тесты для кэширования регулярных выражений
class TestRegexCache:
    """Тесты для кэширования регулярных выражений."""
    
    def test_get_cached_regex(self, regex_patterns):
        """Тест получения кэшированного регулярного выражения."""
        # Первое получение - компиляция
        pattern = regex_patterns[0]
        regex1 = get_cached_regex(pattern)
        assert isinstance(regex1, Pattern)
        
        # Второе получение - из кэша
        regex2 = get_cached_regex(pattern)
        assert regex1 is regex2  # Тот же объект из кэша
    
    def test_multiple_patterns(self, regex_patterns):
        """Тест кэширования нескольких паттернов."""
        compiled_patterns = []
        
        # Компиляция всех паттернов
        for pattern in regex_patterns:
            regex = get_cached_regex(pattern)
            compiled_patterns.append(regex)
        
        # Повторное получение - все из кэша
        for pattern in regex_patterns:
            regex = get_cached_regex(pattern)
            assert regex in compiled_patterns
    
    def test_invalid_pattern(self):
        """Тест обработки неверного паттерна."""
        with pytest.raises(re.error):
            get_cached_regex(r"[invalid")
    
    def test_clear_regex_cache(self, regex_patterns):
        """Тест очистки кэша регулярных выражений."""
        # Заполняем кэш
        for pattern in regex_patterns:
            get_cached_regex(pattern)
        
        # Очищаем кэш
        clear_regex_cache()
        
        # Проверяем, что кэш пуст
        for pattern in regex_patterns:
            regex = get_cached_regex(pattern)
            assert isinstance(regex, Pattern)
            # Новый объект, не из кэша
            assert regex is not get_cached_regex(pattern)

# Тесты для кэширования валидаторов
class TestValidatorCache:
    """Тесты для кэширования валидаторов."""
    
    @cached_validator
    def validate_email(self, value: str) -> bool:
        """Валидация email с кэшированием."""
        time.sleep(0.1)  # Имитация долгой операции
        return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", value))
    
    @cached_validator
    def validate_phone(self, value: str) -> bool:
        """Валидация телефона с кэшированием."""
        time.sleep(0.1)  # Имитация долгой операции
        return bool(re.match(r"^\d{3}-\d{3}-\d{4}$", value))
    
    def test_cached_validator_decorator(self):
        """Тест декоратора кэширования валидатора."""
        validator = self.validate_email
        
        # Первый вызов - вычисление
        start_time = time.time()
        result1 = validator("test@example.com")
        first_call_time = time.time() - start_time
        
        # Второй вызов - из кэша
        start_time = time.time()
        result2 = validator("test@example.com")
        second_call_time = time.time() - start_time
        
        assert result1 is True
        assert result2 is True
        assert second_call_time < first_call_time
    
    def test_multiple_validators(self):
        """Тест нескольких кэшированных валидаторов."""
        email_validator = self.validate_email
        phone_validator = self.validate_phone
        
        # Первый вызов - вычисление
        start_time = time.time()
        email_result1 = email_validator("test@example.com")
        phone_result1 = phone_validator("123-456-7890")
        first_call_time = time.time() - start_time
        
        # Второй вызов - из кэша
        start_time = time.time()
        email_result2 = email_validator("test@example.com")
        phone_result2 = phone_validator("123-456-7890")
        second_call_time = time.time() - start_time
        
        assert email_result1 is True
        assert phone_result1 is True
        assert email_result2 is True
        assert phone_result2 is True
        assert second_call_time < first_call_time
    
    def test_cache_size_limit(self, validator_cache):
        """Тест ограничения размера кэша."""
        # Создаем валидаторы с ограниченным кэшем
        @cached_validator(max_size=2)
        def validate_small(value: str) -> bool:
            return bool(value)
        
        # Заполняем кэш
        validate_small("a")
        validate_small("b")
        validate_small("c")  # Должно вытеснить "a"
        
        # Проверяем, что "a" вытеснен
        assert "a" not in validate_small.__wrapped__.__cache__
        assert "b" in validate_small.__wrapped__.__cache__
        assert "c" in validate_small.__wrapped__.__cache__
    
    def test_cache_info(self, validator_cache):
        """Тест получения информации о кэше."""
        # Создаем валидатор
        @cached_validator
        def validate_with_info(value: str) -> bool:
            return bool(value)
        
        # Используем валидатор
        validate_with_info("test1")
        validate_with_info("test2")
        validate_with_info("test1")  # Из кэша
        
        # Получаем информацию о кэше
        cache_info = validate_with_info.__wrapped__.__cache_info__
        assert cache_info["hits"] == 1
        assert cache_info["misses"] == 2
        assert cache_info["size"] == 2

# Тесты для интеграции кэширования с валидацией
class TestValidationCaching:
    """Тесты для интеграции кэширования с валидацией."""
    
    def test_schema_with_cached_validators(self):
        """Тест схемы с кэшированными валидаторами."""
        # Создаем схему с кэшированными валидаторами
        schema = Schema({
            "email": StringValidator(
                pattern=r"^[^@]+@[^@]+\.[^@]+$",
                custom_validator=self.validate_email
            ),
            "phone": StringValidator(
                pattern=r"^\d{3}-\d{3}-\d{4}$",
                custom_validator=self.validate_phone
            )
        })
        
        # Валидные данные
        valid_data = {
            "email": "test@example.com",
            "phone": "123-456-7890"
        }
        
        # Первая валидация
        start_time = time.time()
        is_valid1, errors1 = schema.validate(valid_data)
        first_validation_time = time.time() - start_time
        
        # Вторая валидация
        start_time = time.time()
        is_valid2, errors2 = schema.validate(valid_data)
        second_validation_time = time.time() - start_time
        
        assert is_valid1 is True
        assert is_valid2 is True
        assert errors1 is None
        assert errors2 is None
        assert second_validation_time < first_validation_time
    
    def test_cached_regex_in_validators(self, regex_patterns):
        """Тест использования кэшированных регулярных выражений в валидаторах."""
        # Создаем валидаторы с разными паттернами
        validators = [
            StringValidator(pattern=pattern)
            for pattern in regex_patterns
        ]
        
        # Тестовые данные
        test_data = [
            "test@example.com",
            "123-456-7890",
            "valid_username",
            "2024-03-15"
        ]
        
        # Первая валидация
        start_time = time.time()
        results1 = [
            validator.validate(value)
            for validator, value in zip(validators, test_data)
        ]
        first_validation_time = time.time() - start_time
        
        # Вторая валидация
        start_time = time.time()
        results2 = [
            validator.validate(value)
            for validator, value in zip(validators, test_data)
        ]
        second_validation_time = time.time() - start_time
        
        assert all(results1)
        assert all(results2)
        assert second_validation_time < first_validation_time
    
    def test_cache_clear_integration(self):
        """Тест интеграции очистки кэша."""
        # Создаем валидатор
        @cached_validator
        def validate_with_clear(value: str) -> bool:
            return bool(value)
        
        # Используем валидатор
        validate_with_clear("test1")
        validate_with_clear("test2")
        
        # Очищаем кэш регулярных выражений
        clear_regex_cache()
        
        # Проверяем, что кэш валидатора не затронут
        assert "test1" in validate_with_clear.__wrapped__.__cache__
        assert "test2" in validate_with_clear.__wrapped__.__cache__
        
        # Очищаем кэш валидатора
        validate_with_clear.__wrapped__.__cache__.clear()
        
        # Проверяем, что кэш очищен
        assert len(validate_with_clear.__wrapped__.__cache__) == 0 