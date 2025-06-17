"""
Модуль схемы валидации PyValid.

Содержит класс Schema для описания и проверки сложных структур данных.
"""

from typing import Any, Dict, Tuple, Optional
from .validators import Validator
from .exceptions import ValidationError, SchemaError

class Schema:
    """
    Класс для описания схемы валидации сложных структур данных.
    
    Attributes:
        fields: Словарь валидаторов для каждого поля
        strict: Строгий режим (запрещает дополнительные поля)
    """
    def __init__(self, fields: Dict[str, Validator], strict: bool = False):
        self.fields = fields
        self.strict = strict

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Валидирует данные по схеме.
        
        Args:
            data: Словарь с данными для валидации
        
        Returns:
            (is_valid, errors):
                is_valid (bool): Валидны ли данные
                errors (dict): Словарь ошибок (None, если ошибок нет)
        """
        errors = {}
        # Проверка на неожиданные поля
        if self.strict:
            unknown_fields = set(data.keys()) - set(self.fields.keys())
            if unknown_fields:
                for field in unknown_fields:
                    errors[field] = "Unexpected field"
        # Проверка каждого поля по валидатору
        for field, validator in self.fields.items():
            value = data.get(field)
            is_valid, error = validator.validate(value)
            if not is_valid:
                errors[field] = error
        if errors:
            return False, errors
        return True, None 