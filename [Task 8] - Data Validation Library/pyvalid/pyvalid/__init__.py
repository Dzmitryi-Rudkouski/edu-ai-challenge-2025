"""
PyValid - Мощная библиотека валидации для Python с поддержкой асинхронной валидации и метриками производительности.

Основные возможности:
- Строгая типизация с поддержкой Python type hints и TypeGuard
- Асинхронная валидация данных
- Метрики производительности
- Кэширование валидаторов
- Расширенное логирование
- Поддержка контекстной валидации
"""

import logging
from typing import Any, Optional, TypeVar, Union, Dict, List, Callable
from contextlib import contextmanager
from functools import lru_cache
from time import perf_counter

from .schema import Schema
from .validators import (
    Validator,
    StringValidator,
    NumberValidator,
    BooleanValidator,
    DateValidator,
    ObjectValidator,
    ArrayValidator,
    CustomValidator,
    AsyncValidator
)
from .exceptions import ValidationError, ValidatorError
from .metrics import ValidationMetrics
from .context import ValidationContext

# Настройка логирования
logger = logging.getLogger(__name__)

__version__ = "0.2.0"
__all__ = [
    # Основные классы
    "Schema",
    "Validator",
    "AsyncValidator",
    "ValidationContext",
    "ValidationMetrics",
    
    # Валидаторы
    "StringValidator",
    "NumberValidator",
    "BooleanValidator",
    "DateValidator",
    "ObjectValidator",
    "ArrayValidator",
    "CustomValidator",
    
    # Исключения
    "ValidationError",
    "ValidatorError",
    
    # Утилиты
    "validation_context",
    "get_cached_validator",
    "measure_validation_time"
]

# Типовые переменные
T = TypeVar('T')
StrT = TypeVar('StrT', bound=str)
NumT = TypeVar('NumT', bound=Union[int, float])
BoolT = TypeVar('BoolT', bound=bool)
DateT = TypeVar('DateT', bound='datetime')

# Контекстный менеджер для валидации
@contextmanager
def validation_context(path: str = ""):
    """
    Контекстный менеджер для валидации с поддержкой пути к полю.
    
    Args:
        path: Путь к текущему полю в структуре данных
    
    Example:
        >>> with validation_context("user.address"):
        ...     validate_address(address_data)
    """
    try:
        yield
    except ValidationError as e:
        e.path = f"{path}.{e.path}" if path else e.path
        raise

# Кэширование валидаторов
@lru_cache(maxsize=128)
def get_cached_validator(pattern: str) -> StringValidator:
    """
    Создает кэшированный валидатор строк с регулярным выражением.
    
    Args:
        pattern: Регулярное выражение для валидации
    
    Returns:
        Кэшированный StringValidator
    """
    return StringValidator().pattern(pattern)

# Измерение времени валидации
def measure_validation_time(func: Callable) -> Callable:
    """
    Декоратор для измерения времени выполнения валидации.
    
    Args:
        func: Функция валидации
    
    Returns:
        Обернутая функция с измерением времени
    """
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        result = func(*args, **kwargs)
        duration = perf_counter() - start_time
        logger.debug(f"Validation took {duration:.3f}s for {func.__name__}")
        return result
    return wrapper 