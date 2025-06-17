"""
Исключения для библиотеки PyValid.
"""

from typing import Any, Optional, Dict, List


class ValidationError(Exception):
    """
    Базовое исключение для ошибок валидации.
    
    Attributes:
        message: Сообщение об ошибке
        field: Поле, в котором произошла ошибка
        value: Значение, которое вызвало ошибку
        path: Путь к полю в структуре данных
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        path: str = ""
    ):
        self.message = message
        self.field = field
        self.value = value
        self.path = path
        
        # Формируем полное сообщение об ошибке
        full_message = message
        if field:
            full_message = f"Field '{field}': {message}"
        if path:
            full_message = f"Path '{path}': {full_message}"
        
        super().__init__(full_message)
    
    def __str__(self) -> str:
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует исключение в словарь."""
        return {
            "message": self.message,
            "field": self.field,
            "value": self.value,
            "path": self.path
        }


class ValidatorError(ValidationError):
    """
    Исключение для ошибок в валидаторах.
    
    Attributes:
        validator_type: Тип валидатора
        validator_params: Параметры валидатора
    """
    
    def __init__(
        self,
        message: str,
        validator_type: Optional[str] = None,
        validator_params: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        value: Any = None,
        path: str = ""
    ):
        self.validator_type = validator_type
        self.validator_params = validator_params or {}
        
        super().__init__(message, field, value, path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует исключение в словарь."""
        base_dict = super().to_dict()
        base_dict.update({
            "validator_type": self.validator_type,
            "validator_params": self.validator_params
        })
        return base_dict


class SchemaError(ValidationError):
    """
    Исключение для ошибок в схемах валидации.
    
    Attributes:
        schema: Схема, в которой произошла ошибка
        field_validators: Валидаторы полей
    """
    
    def __init__(
        self,
        message: str,
        schema: Optional[Dict[str, Any]] = None,
        field_validators: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        value: Any = None,
        path: str = ""
    ):
        self.schema = schema
        self.field_validators = field_validators or {}
        
        super().__init__(message, field, value, path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует исключение в словарь."""
        base_dict = super().to_dict()
        base_dict.update({
            "schema": self.schema,
            "field_validators": list(self.field_validators.keys())
        })
        return base_dict


class AsyncValidationError(ValidationError):
    """
    Исключение для ошибок асинхронной валидации.
    
    Attributes:
        async_validator: Асинхронный валидатор
        task_info: Информация о задаче
    """
    
    def __init__(
        self,
        message: str,
        async_validator: Optional[str] = None,
        task_info: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        value: Any = None,
        path: str = ""
    ):
        self.async_validator = async_validator
        self.task_info = task_info or {}
        
        super().__init__(message, field, value, path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует исключение в словарь."""
        base_dict = super().to_dict()
        base_dict.update({
            "async_validator": self.async_validator,
            "task_info": self.task_info
        })
        return base_dict


class CacheError(Exception):
    """
    Исключение для ошибок кэширования.
    
    Attributes:
        cache_type: Тип кэша
        operation: Операция, которая вызвала ошибку
    """
    
    def __init__(
        self,
        message: str,
        cache_type: Optional[str] = None,
        operation: Optional[str] = None
    ):
        self.cache_type = cache_type
        self.operation = operation
        
        super().__init__(message)


class ContextError(Exception):
    """
    Исключение для ошибок контекста валидации.
    
    Attributes:
        context_type: Тип контекста
        context_data: Данные контекста
    """
    
    def __init__(
        self,
        message: str,
        context_type: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        self.context_type = context_type
        self.context_data = context_data or {}
        
        super().__init__(message)


# Утилитарные функции для работы с исключениями
def format_validation_errors(errors: List[ValidationError]) -> Dict[str, str]:
    """
    Форматирует список исключений валидации в словарь ошибок.
    
    Args:
        errors: Список исключений валидации
    
    Returns:
        Dict[str, str]: Словарь с полями и сообщениями об ошибках
    """
    formatted_errors = {}
    
    for error in errors:
        field = error.field or error.path or "unknown"
        formatted_errors[field] = error.message
    
    return formatted_errors


def collect_validation_errors(
    validation_func,
    data: Any,
    *args,
    **kwargs
) -> List[ValidationError]:
    """
    Собирает все исключения валидации из функции.
    
    Args:
        validation_func: Функция валидации
        data: Данные для валидации
        *args: Дополнительные аргументы
        **kwargs: Дополнительные именованные аргументы
    
    Returns:
        List[ValidationError]: Список исключений валидации
    """
    errors = []
    
    try:
        validation_func(data, *args, **kwargs)
    except ValidationError as e:
        errors.append(e)
    except Exception as e:
        # Преобразуем общие исключения в ValidationError
        errors.append(ValidationError(str(e)))
    
    return errors 