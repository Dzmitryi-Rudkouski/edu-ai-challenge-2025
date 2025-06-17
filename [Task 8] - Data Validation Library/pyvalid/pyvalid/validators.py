"""
Валидаторы для библиотеки PyValid.

Этот модуль содержит все валидаторы для различных типов данных:
- Примитивные типы: строки, числа, булевы значения, даты
- Сложные типы: объекты, массивы
- Пользовательские валидаторы
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Any, Optional, Union, Dict, List, Callable, Tuple, TypeVar, Generic
from typing_extensions import TypeGuard

from .exceptions import ValidationError, ValidatorError

# Типовые переменные
T = TypeVar('T')
StrT = TypeVar('StrT', bound=str)
NumT = TypeVar('NumT', bound=Union[int, float])
BoolT = TypeVar('BoolT', bound=bool)
DateT = TypeVar('DateT', bound=Union[datetime, date])


class Validator(ABC, Generic[T]):
    """
    Базовый абстрактный класс для всех валидаторов.
    
    Attributes:
        required: Обязательное ли поле
        nullable: Может ли поле быть None
        custom_validator: Пользовательская функция валидации
        error_message: Кастомное сообщение об ошибке
    """
    
    def __init__(
        self,
        required: bool = True,
        nullable: bool = False,
        custom_validator: Optional[Callable[[T], Union[bool, Tuple[bool, Optional[str]]]]] = None,
        error_message: Optional[str] = None
    ):
        self.required = required
        self.nullable = nullable
        self.custom_validator = custom_validator
        self.error_message = error_message
    
    @abstractmethod
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Валидирует значение.
        
        Args:
            value: Значение для валидации
        
        Returns:
            Tuple[bool, Optional[str]]: (валидно ли, сообщение об ошибке)
        """
        pass
    
    def _validate_required(self, value: Any) -> bool:
        """Проверяет, что поле присутствует, если оно обязательное."""
        if self.required and value is None:
            return False
        return True
    
    def _validate_nullable(self, value: Any) -> bool:
        """Проверяет, что значение не None, если поле не nullable."""
        if not self.nullable and value is None:
            return False
        return True
    
    def _validate_custom(self, value: T) -> Tuple[bool, Optional[str]]:
        """Выполняет пользовательскую валидацию."""
        if self.custom_validator is None:
            return True, None
        
        try:
            result = self.custom_validator(value)
            
            if isinstance(result, tuple):
                return result
            else:
                return bool(result), None
        except Exception as e:
            return False, str(e)
    
    def _format_error(self, message: str) -> str:
        """Форматирует сообщение об ошибке."""
        if self.error_message:
            return self.error_message
        return message


class StringValidator(Validator[str]):
    """
    Валидатор для строк.
    
    Attributes:
        min_length: Минимальная длина строки
        max_length: Максимальная длина строки
        pattern: Регулярное выражение для проверки
        allowed_values: Разрешенные значения
        trim_whitespace: Удалять ли пробелы в начале и конце
    """
    
    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        allowed_values: Optional[List[str]] = None,
        trim_whitespace: bool = False,
        required: bool = True,
        nullable: bool = False,
        custom_validator: Optional[Callable[[str], Union[bool, Tuple[bool, Optional[str]]]]] = None,
        error_message: Optional[str] = None
    ):
        super().__init__(required, nullable, custom_validator, error_message)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.allowed_values = allowed_values
        self.trim_whitespace = trim_whitespace
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Валидирует строковое значение."""
        # Проверка обязательности
        if not self._validate_required(value):
            return False, self._format_error("Field is required")
        
        # Проверка nullable
        if not self._validate_nullable(value):
            return False, self._format_error("Field cannot be null")
        
        # Если значение None и поле nullable, то валидно
        if value is None:
            return True, None
        
        # Проверка типа
        if not isinstance(value, str):
            return False, self._format_error("Value must be a string")
        
        # Удаление пробелов
        if self.trim_whitespace:
            value = value.strip()
        
        # Проверка минимальной длины
        if self.min_length is not None and len(value) < self.min_length:
            return False, self._format_error(
                f"String length must be at least {self.min_length} characters"
            )
        
        # Проверка максимальной длины
        if self.max_length is not None and len(value) > self.max_length:
            return False, self._format_error(
                f"String length must be at most {self.max_length} characters"
            )
        
        # Проверка пустой строки
        if self.min_length and self.min_length > 0 and len(value) == 0:
            return False, self._format_error("String cannot be empty")
        
        # Проверка регулярного выражения
        if self.pattern is not None:
            if not re.match(self.pattern, value):
                return False, self._format_error(f"String does not match pattern: {self.pattern}")
        
        # Проверка разрешенных значений
        if self.allowed_values is not None and value not in self.allowed_values:
            return False, self._format_error(
                f"Value must be one of: {', '.join(self.allowed_values)}"
            )
        
        # Пользовательская валидация
        return self._validate_custom(value)


class NumberValidator(Validator[Union[int, float]]):
    """
    Валидатор для чисел.
    
    Attributes:
        min_value: Минимальное значение
        max_value: Максимальное значение
        integer_only: Только целые числа
        allowed_values: Разрешенные значения
    """
    
    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        integer_only: bool = False,
        allowed_values: Optional[List[Union[int, float]]] = None,
        required: bool = True,
        nullable: bool = False,
        custom_validator: Optional[Callable[[Union[int, float]], Union[bool, Tuple[bool, Optional[str]]]]] = None,
        error_message: Optional[str] = None
    ):
        super().__init__(required, nullable, custom_validator, error_message)
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
        self.allowed_values = allowed_values
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Валидирует числовое значение."""
        # Проверка обязательности
        if not self._validate_required(value):
            return False, self._format_error("Field is required")
        
        # Проверка nullable
        if not self._validate_nullable(value):
            return False, self._format_error("Field cannot be null")
        
        # Если значение None и поле nullable, то валидно
        if value is None:
            return True, None
        
        # Проверка типа
        if not isinstance(value, (int, float)):
            return False, self._format_error("Value must be a number")
        
        # Проверка целых чисел
        if self.integer_only and not isinstance(value, int):
            return False, self._format_error("Value must be an integer")
        
        # Проверка минимального значения
        if self.min_value is not None and value < self.min_value:
            return False, self._format_error(
                f"Value must be at least {self.min_value}"
            )
        
        # Проверка максимального значения
        if self.max_value is not None and value > self.max_value:
            return False, self._format_error(
                f"Value must be at most {self.max_value}"
            )
        
        # Проверка разрешенных значений
        if self.allowed_values is not None and value not in self.allowed_values:
            return False, self._format_error(
                f"Value must be one of: {', '.join(map(str, self.allowed_values))}"
            )
        
        # Пользовательская валидация
        return self._validate_custom(value)


class BooleanValidator(Validator[bool]):
    """
    Валидатор для булевых значений.
    
    Attributes:
        strict: Строгая проверка (только True/False)
    """
    
    def __init__(
        self,
        strict: bool = True,
        required: bool = True,
        nullable: bool = False,
        custom_validator: Optional[Callable[[bool], Union[bool, Tuple[bool, Optional[str]]]]] = None,
        error_message: Optional[str] = None
    ):
        super().__init__(required, nullable, custom_validator, error_message)
        self.strict = strict
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Валидирует булево значение."""
        # Проверка обязательности
        if not self._validate_required(value):
            return False, self._format_error("Field is required")
        
        # Проверка nullable
        if not self._validate_nullable(value):
            return False, self._format_error("Field cannot be null")
        
        # Если значение None и поле nullable, то валидно
        if value is None:
            return True, None
        
        # Проверка типа
        if self.strict and not isinstance(value, bool):
            return False, self._format_error("Value must be a boolean")
        
        # Нестрогая проверка (разрешает строки "true"/"false", числа 0/1)
        if not self.strict:
            if isinstance(value, str):
                if value.lower() not in ("true", "false", "1", "0"):
                    return False, self._format_error("Value must be a valid boolean")
            elif isinstance(value, (int, float)):
                if value not in (0, 1):
                    return False, self._format_error("Value must be 0 or 1")
            elif not isinstance(value, bool):
                return False, self._format_error("Value must be a valid boolean")
        
        # Пользовательская валидация
        return self._validate_custom(bool(value))


class DateValidator(Validator[Union[datetime, date]]):
    """
    Валидатор для дат.
    
    Attributes:
        min_value: Минимальная дата
        max_value: Максимальная дата
        format: Формат даты (для строк)
        allow_strings: Разрешать ли строки
    """
    
    def __init__(
        self,
        min_value: Optional[Union[datetime, date]] = None,
        max_value: Optional[Union[datetime, date]] = None,
        format: Optional[str] = None,
        allow_strings: bool = False,
        required: bool = True,
        nullable: bool = False,
        custom_validator: Optional[Callable[[Union[datetime, date]], Union[bool, Tuple[bool, Optional[str]]]]] = None,
        error_message: Optional[str] = None
    ):
        super().__init__(required, nullable, custom_validator, error_message)
        self.min_value = min_value
        self.max_value = max_value
        self.format = format
        self.allow_strings = allow_strings
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Валидирует значение даты."""
        # Проверка обязательности
        if not self._validate_required(value):
            return False, self._format_error("Field is required")
        
        # Проверка nullable
        if not self._validate_nullable(value):
            return False, self._format_error("Field cannot be null")
        
        # Если значение None и поле nullable, то валидно
        if value is None:
            return True, None
        
        # Преобразование строки в дату
        if isinstance(value, str) and self.allow_strings:
            try:
                if self.format:
                    value = datetime.strptime(value, self.format)
                else:
                    # Попытка автоматического парсинга
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return False, self._format_error("Invalid date format")
        
        # Проверка типа
        if not isinstance(value, (datetime, date)):
            return False, self._format_error("Value must be a date or datetime")
        
        # Проверка минимальной даты
        if self.min_value is not None and value < self.min_value:
            return False, self._format_error(
                f"Date must be at least {self.min_value}"
            )
        
        # Проверка максимальной даты
        if self.max_value is not None and value > self.max_value:
            return False, self._format_error(
                f"Date must be at most {self.max_value}"
            )
        
        # Пользовательская валидация
        return self._validate_custom(value)


class ObjectValidator(Validator[Dict[str, Any]]):
    """
    Валидатор для объектов.
    
    Attributes:
        schema: Схема валидации объекта
        strict: Строгий режим (запрещает дополнительные поля)
        allow_unknown: Разрешать неизвестные поля
    """
    
    def __init__(
        self,
        schema: Dict[str, Validator],
        strict: bool = False,
        allow_unknown: bool = True,
        required: bool = True,
        nullable: bool = False,
        custom_validator: Optional[Callable[[Dict[str, Any]], Union[bool, Tuple[bool, Optional[str]]]]] = None,
        error_message: Optional[str] = None
    ):
        super().__init__(required, nullable, custom_validator, error_message)
        self.schema = schema
        self.strict = strict
        self.allow_unknown = allow_unknown
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Валидирует объект."""
        # Проверка обязательности
        if not self._validate_required(value):
            return False, self._format_error("Field is required")
        
        # Проверка nullable
        if not self._validate_nullable(value):
            return False, self._format_error("Field cannot be null")
        
        # Если значение None и поле nullable, то валидно
        if value is None:
            return True, None
        
        # Проверка типа
        if not isinstance(value, dict):
            return False, self._format_error("Value must be an object")
        
        # Проверка строгого режима
        if self.strict:
            unknown_fields = set(value.keys()) - set(self.schema.keys())
            if unknown_fields:
                return False, self._format_error(
                    f"Unknown fields: {', '.join(unknown_fields)}"
                )
        
        # Валидация полей
        errors = {}
        for field_name, validator in self.schema.items():
            field_value = value.get(field_name)
            
            try:
                is_valid, error = validator.validate(field_value)
                if not is_valid:
                    errors[field_name] = error
            except Exception as e:
                errors[field_name] = str(e)
        
        if errors:
            return False, self._format_error(f"Validation errors: {errors}")
        
        # Пользовательская валидация
        return self._validate_custom(value)


class ArrayValidator(Validator[List[Any]]):
    """
    Валидатор для массивов.
    
    Attributes:
        item_validator: Валидатор для элементов массива
        min_length: Минимальная длина массива
        max_length: Максимальная длина массива
        unique: Должны ли элементы быть уникальными
    """
    
    def __init__(
        self,
        item_validator: Validator,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        unique: bool = False,
        required: bool = True,
        nullable: bool = False,
        custom_validator: Optional[Callable[[List[Any]], Union[bool, Tuple[bool, Optional[str]]]]] = None,
        error_message: Optional[str] = None
    ):
        super().__init__(required, nullable, custom_validator, error_message)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
        self.unique = unique
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Валидирует массив."""
        # Проверка обязательности
        if not self._validate_required(value):
            return False, self._format_error("Field is required")
        
        # Проверка nullable
        if not self._validate_nullable(value):
            return False, self._format_error("Field cannot be null")
        
        # Если значение None и поле nullable, то валидно
        if value is None:
            return True, None
        
        # Проверка типа
        if not isinstance(value, list):
            return False, self._format_error("Value must be an array")
        
        # Проверка минимальной длины
        if self.min_length is not None and len(value) < self.min_length:
            return False, self._format_error(
                f"Array must have at least {self.min_length} items"
            )
        
        # Проверка максимальной длины
        if self.max_length is not None and len(value) > self.max_length:
            return False, self._format_error(
                f"Array must have at most {self.max_length} items"
            )
        
        # Проверка уникальности
        if self.unique and len(value) != len(set(value)):
            return False, self._format_error("Array items must be unique")
        
        # Валидация элементов
        errors = []
        for i, item in enumerate(value):
            try:
                is_valid, error = self.item_validator.validate(item)
                if not is_valid:
                    errors.append(f"Item {i}: {error}")
            except Exception as e:
                errors.append(f"Item {i}: {str(e)}")
        
        if errors:
            return False, self._format_error(f"Validation errors: {errors}")
        
        # Пользовательская валидация
        return self._validate_custom(value)


class CustomValidator(Validator[T]):
    """
    Пользовательский валидатор.
    
    Attributes:
        validator_func: Функция валидации
    """
    
    def __init__(
        self,
        validator_func: Callable[[T], Union[bool, Tuple[bool, Optional[str]]]],
        required: bool = True,
        nullable: bool = False,
        error_message: Optional[str] = None
    ):
        super().__init__(required, nullable, validator_func, error_message)
        self.validator_func = validator_func
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Валидирует значение с помощью пользовательской функции."""
        # Проверка обязательности
        if not self._validate_required(value):
            return False, self._format_error("Field is required")
        
        # Проверка nullable
        if not self._validate_nullable(value):
            return False, self._format_error("Field cannot be null")
        
        # Если значение None и поле nullable, то валидно
        if value is None:
            return True, None
        
        # Пользовательская валидация
        return self._validate_custom(value)


# Утилитарные функции
def is_valid_string(value: Any) -> TypeGuard[str]:
    """Type guard для проверки, что значение является строкой."""
    return isinstance(value, str)


def is_valid_number(value: Any) -> TypeGuard[Union[int, float]]:
    """Type guard для проверки, что значение является числом."""
    return isinstance(value, (int, float))


def is_valid_boolean(value: Any) -> TypeGuard[bool]:
    """Type guard для проверки, что значение является булевым."""
    return isinstance(value, bool)


def is_valid_date(value: Any) -> TypeGuard[Union[datetime, date]]:
    """Type guard для проверки, что значение является датой."""
    return isinstance(value, (datetime, date))


def is_valid_object(value: Any) -> TypeGuard[Dict[str, Any]]:
    """Type guard для проверки, что значение является объектом."""
    return isinstance(value, dict)


def is_valid_array(value: Any) -> TypeGuard[List[Any]]:
    """Type guard для проверки, что значение является массивом."""
    return isinstance(value, list) 