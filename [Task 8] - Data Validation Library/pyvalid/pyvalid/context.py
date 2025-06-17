"""
Модуль для управления контекстом валидации.
"""

from typing import Any, Dict, Optional, List, Callable
from contextlib import contextmanager
import logging
from .metrics import metrics

logger = logging.getLogger(__name__)

class ValidationContext:
    """
    Класс для управления контекстом валидации.
    
    Attributes:
        path: Текущий путь к полю
        data: Полный набор данных для валидации
        custom_validators: Пользовательские валидаторы
        strict_mode: Режим строгой валидации
    """
    
    def __init__(
        self,
        data: Any,
        path: str = "",
        custom_validators: Optional[Dict[str, Callable]] = None,
        strict_mode: bool = False
    ):
        self.path = path
        self.data = data
        self.custom_validators = custom_validators or {}
        self.strict_mode = strict_mode
        self._validation_stack: List[str] = []
    
    @contextmanager
    def enter_field(self, field_name: str):
        """
        Входит в контекст поля для валидации.
        
        Args:
            field_name: Имя поля
        
        Example:
            >>> with context.enter_field("user"):
            ...     validate_user(user_data)
        """
        old_path = self.path
        self.path = f"{old_path}.{field_name}" if old_path else field_name
        self._validation_stack.append(field_name)
        
        try:
            yield
        finally:
            self.path = old_path
            self._validation_stack.pop()
    
    def get_field_value(self, field_name: str) -> Any:
        """
        Получает значение поля из данных.
        
        Args:
            field_name: Имя поля
        
        Returns:
            Значение поля или None, если поле отсутствует
        """
        if isinstance(self.data, dict):
            return self.data.get(field_name)
        return None
    
    def get_full_path(self) -> str:
        """
        Возвращает полный путь к текущему полю.
        
        Returns:
            Полный путь в формате "field1.field2.field3"
        """
        return ".".join(self._validation_stack)
    
    def validate_with_metrics(self, validator: Callable, value: Any) -> tuple[bool, Optional[str]]:
        """
        Выполняет валидацию с учетом метрик.
        
        Args:
            validator: Функция валидации
            value: Проверяемое значение
        
        Returns:
            tuple[bool, Optional[str]]: Результат валидации и сообщение об ошибке
        """
        start_time = metrics.start_validation()
        
        try:
            is_valid, error = validator(value)
            metrics.end_validation(
                start_time,
                self.get_full_path(),
                is_valid,
                type(error).__name__ if error else None
            )
            return is_valid, error
        except Exception as e:
            metrics.end_validation(
                start_time,
                self.get_full_path(),
                False,
                type(e).__name__
            )
            raise
    
    def get_custom_validator(self, field_name: str) -> Optional[Callable]:
        """
        Получает пользовательский валидатор для поля.
        
        Args:
            field_name: Имя поля
        
        Returns:
            Функция валидации или None
        """
        return self.custom_validators.get(field_name)
    
    def is_strict_mode(self) -> bool:
        """
        Проверяет, включен ли режим строгой валидации.
        
        Returns:
            True, если включен режим строгой валидации
        """
        return self.strict_mode
    
    def log_validation(self, field_name: str, is_valid: bool, error: Optional[str] = None) -> None:
        """
        Логирует результат валидации.
        
        Args:
            field_name: Имя поля
            is_valid: Результат валидации
            error: Сообщение об ошибке
        """
        if is_valid:
            logger.debug(f"Validation successful for {self.get_full_path()}.{field_name}")
        else:
            logger.warning(
                f"Validation failed for {self.get_full_path()}.{field_name}: {error}"
            )

# Глобальный контекст валидации
current_context: Optional[ValidationContext] = None

def get_current_context() -> Optional[ValidationContext]:
    """
    Возвращает текущий контекст валидации.
    
    Returns:
        Текущий контекст валидации или None
    """
    return current_context

@contextmanager
def validation_context(
    data: Any,
    path: str = "",
    custom_validators: Optional[Dict[str, Callable]] = None,
    strict_mode: bool = False
):
    """
    Контекстный менеджер для создания контекста валидации.
    
    Args:
        data: Данные для валидации
        path: Начальный путь к полю
        custom_validators: Пользовательские валидаторы
        strict_mode: Режим строгой валидации
    
    Example:
        >>> with validation_context(user_data, strict_mode=True):
        ...     validate_user(user_data)
    """
    global current_context
    old_context = current_context
    current_context = ValidationContext(data, path, custom_validators, strict_mode)
    
    try:
        yield current_context
    finally:
        current_context = old_context 