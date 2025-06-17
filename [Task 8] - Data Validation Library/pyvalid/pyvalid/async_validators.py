"""
Модуль для асинхронной валидации данных.
"""

from typing import Any, Callable, Optional, TypeVar, Awaitable, Union
from functools import wraps
import asyncio
import logging
from .context import ValidationContext, get_current_context
from .metrics import metrics

logger = logging.getLogger(__name__)

T = TypeVar('T')
ValidatorFunc = Callable[[Any], Union[bool, tuple[bool, Optional[str]]]]
AsyncValidatorFunc = Callable[[Any], Awaitable[Union[bool, tuple[bool, Optional[str]]]]]

class AsyncValidator:
    """
    Базовый класс для асинхронных валидаторов.
    
    Attributes:
        validator: Функция валидации
        error_message: Сообщение об ошибке
    """
    
    def __init__(
        self,
        validator: AsyncValidatorFunc,
        error_message: Optional[str] = None
    ):
        self.validator = validator
        self.error_message = error_message
    
    async def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Выполняет асинхронную валидацию значения.
        
        Args:
            value: Проверяемое значение
        
        Returns:
            tuple[bool, Optional[str]]: Результат валидации и сообщение об ошибке
        """
        try:
            result = await self.validator(value)
            
            if isinstance(result, tuple):
                is_valid, error = result
                return is_valid, error or self.error_message
            
            return bool(result), None if result else self.error_message
        
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False, str(e)

def async_validator(error_message: Optional[str] = None):
    """
    Декоратор для создания асинхронных валидаторов.
    
    Args:
        error_message: Сообщение об ошибке
    
    Example:
        >>> @async_validator("Invalid email format")
        ... async def validate_email(email: str) -> bool:
        ...     # Асинхронная проверка email
        ...     return await check_email_exists(email)
    """
    def decorator(func: AsyncValidatorFunc) -> AsyncValidatorFunc:
        @wraps(func)
        async def wrapper(value: Any) -> tuple[bool, Optional[str]]:
            validator = AsyncValidator(func, error_message)
            return await validator.validate(value)
        return wrapper
    return decorator

class AsyncSchemaValidator:
    """
    Класс для асинхронной валидации схем.
    
    Attributes:
        validators: Словарь валидаторов для полей
        strict_mode: Режим строгой валидации
    """
    
    def __init__(
        self,
        validators: dict[str, AsyncValidatorFunc],
        strict_mode: bool = False
    ):
        self.validators = validators
        self.strict_mode = strict_mode
    
    async def validate(
        self,
        data: dict[str, Any],
        context: Optional[ValidationContext] = None
    ) -> tuple[bool, dict[str, str]]:
        """
        Выполняет асинхронную валидацию данных по схеме.
        
        Args:
            data: Данные для валидации
            context: Контекст валидации
        
        Returns:
            tuple[bool, dict[str, str]]: Результат валидации и словарь ошибок
        """
        errors: dict[str, str] = {}
        is_valid = True
        
        async def validate_field(field: str, value: Any) -> None:
            nonlocal is_valid
            validator = self.validators.get(field)
            
            if validator is None:
                if self.strict_mode:
                    errors[field] = "Unexpected field"
                    is_valid = False
                return
            
            try:
                result = await validator(value)
                
                if isinstance(result, tuple):
                    field_valid, error = result
                else:
                    field_valid, error = bool(result), None
                
                if not field_valid:
                    errors[field] = error or "Invalid value"
                    is_valid = False
                
                if context:
                    context.log_validation(field, field_valid, error)
            
            except Exception as e:
                errors[field] = str(e)
                is_valid = False
                if context:
                    context.log_validation(field, False, str(e))
        
        # Создаем задачи для параллельной валидации
        tasks = [
            validate_field(field, value)
            for field, value in data.items()
        ]
        
        # Запускаем все задачи параллельно
        await asyncio.gather(*tasks)
        
        return is_valid, errors

def create_async_schema(
    validators: dict[str, AsyncValidatorFunc],
    strict_mode: bool = False
) -> AsyncSchemaValidator:
    """
    Создает валидатор асинхронной схемы.
    
    Args:
        validators: Словарь валидаторов для полей
        strict_mode: Режим строгой валидации
    
    Returns:
        AsyncSchemaValidator: Валидатор схемы
    
    Example:
        >>> schema = create_async_schema({
        ...     "email": validate_email,
        ...     "age": validate_age
        ... }, strict_mode=True)
        >>> is_valid, errors = await schema.validate(user_data)
    """
    return AsyncSchemaValidator(validators, strict_mode)

async def validate_with_metrics(
    validator: AsyncValidatorFunc,
    value: Any,
    field_path: str
) -> tuple[bool, Optional[str]]:
    """
    Выполняет асинхронную валидацию с учетом метрик.
    
    Args:
        validator: Функция валидации
        value: Проверяемое значение
        field_path: Путь к полю
    
    Returns:
        tuple[bool, Optional[str]]: Результат валидации и сообщение об ошибке
    """
    start_time = metrics.start_validation()
    
    try:
        result = await validator(value)
        
        if isinstance(result, tuple):
            is_valid, error = result
        else:
            is_valid, error = bool(result), None
        
        metrics.end_validation(
            start_time,
            field_path,
            is_valid,
            type(error).__name__ if error else None
        )
        
        return is_valid, error
    
    except Exception as e:
        metrics.end_validation(
            start_time,
            field_path,
            False,
            type(e).__name__
        )
        raise 