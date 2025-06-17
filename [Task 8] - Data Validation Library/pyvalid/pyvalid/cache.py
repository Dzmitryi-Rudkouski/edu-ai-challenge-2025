"""
Модуль для кэширования валидаторов и регулярных выражений.
"""

from typing import Any, Callable, Optional, TypeVar, Dict, Pattern
from functools import lru_cache, wraps
import re
import logging
from threading import Lock

logger = logging.getLogger(__name__)

T = TypeVar('T')
ValidatorFunc = Callable[[Any], tuple[bool, Optional[str]]]

# Глобальный кэш для регулярных выражений
_regex_cache: Dict[str, Pattern] = {}
_regex_lock = Lock()

def get_cached_regex(pattern: str, flags: int = 0) -> Pattern:
    """
    Получает скомпилированное регулярное выражение из кэша.
    
    Args:
        pattern: Шаблон регулярного выражения
        flags: Флаги компиляции
    
    Returns:
        Pattern: Скомпилированное регулярное выражение
    """
    cache_key = f"{pattern}:{flags}"
    
    with _regex_lock:
        if cache_key not in _regex_cache:
            try:
                _regex_cache[cache_key] = re.compile(pattern, flags)
            except re.error as e:
                logger.error(f"Invalid regex pattern: {pattern}")
                raise ValueError(f"Invalid regex pattern: {str(e)}")
        
        return _regex_cache[cache_key]

def clear_regex_cache() -> None:
    """
    Очищает кэш регулярных выражений.
    """
    with _regex_lock:
        _regex_cache.clear()

def cached_validator(maxsize: Optional[int] = 128):
    """
    Декоратор для кэширования результатов валидаторов.
    
    Args:
        maxsize: Максимальный размер кэша
    
    Example:
        >>> @cached_validator(maxsize=256)
        ... def validate_email(email: str) -> tuple[bool, Optional[str]]:
        ...     # Валидация email
        ...     return is_valid, error
    """
    def decorator(func: ValidatorFunc) -> ValidatorFunc:
        @lru_cache(maxsize=maxsize)
        def cached_func(value: Any) -> tuple[bool, Optional[str]]:
            return func(value)
        
        @wraps(func)
        def wrapper(value: Any) -> tuple[bool, Optional[str]]:
            try:
                return cached_func(value)
            except TypeError:
                # Если значение не хешируемое, выполняем валидацию без кэша
                logger.warning(
                    f"Non-hashable value passed to cached validator {func.__name__}"
                )
                return func(value)
        
        # Добавляем методы для управления кэшем
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear
        
        return wrapper
    return decorator

class ValidatorCache:
    """
    Класс для управления кэшем валидаторов.
    
    Attributes:
        validators: Словарь кэшированных валидаторов
    """
    
    def __init__(self):
        self.validators: Dict[str, Callable] = {}
        self._lock = Lock()
    
    def get_validator(
        self,
        validator_type: str,
        **params: Any
    ) -> Callable:
        """
        Получает валидатор из кэша или создает новый.
        
        Args:
            validator_type: Тип валидатора
            **params: Параметры валидатора
        
        Returns:
            Callable: Функция валидации
        """
        cache_key = f"{validator_type}:{str(sorted(params.items()))}"
        
        with self._lock:
            if cache_key not in self.validators:
                # Создаем новый валидатор
                validator = self._create_validator(validator_type, **params)
                self.validators[cache_key] = validator
            
            return self.validators[cache_key]
    
    def _create_validator(
        self,
        validator_type: str,
        **params: Any
    ) -> Callable:
        """
        Создает новый валидатор указанного типа.
        
        Args:
            validator_type: Тип валидатора
            **params: Параметры валидатора
        
        Returns:
            Callable: Функция валидации
        
        Raises:
            ValueError: Если тип валидатора не поддерживается
        """
        # Здесь должна быть логика создания валидаторов разных типов
        # Это заглушка, которую нужно реализовать в зависимости от типов валидаторов
        raise ValueError(f"Unsupported validator type: {validator_type}")
    
    def clear(self) -> None:
        """
        Очищает кэш валидаторов.
        """
        with self._lock:
            self.validators.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о кэше.
        
        Returns:
            Dict[str, Any]: Информация о кэше
        """
        with self._lock:
            return {
                "validator_count": len(self.validators),
                "validator_types": list(set(
                    key.split(":")[0] for key in self.validators.keys()
                ))
            }

# Глобальный экземпляр кэша валидаторов
validator_cache = ValidatorCache() 