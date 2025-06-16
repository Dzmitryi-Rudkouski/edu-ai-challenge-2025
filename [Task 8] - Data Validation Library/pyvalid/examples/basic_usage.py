"""
Примеры базового использования библиотеки PyValid.
"""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import logging

from pyvalid import (
    Schema,
    validation_context,
    setup_logging,
    async_validator,
    cached_validator,
    ValidationLogger
)
from pyvalid.validators import (
    StringValidator,
    NumberValidator,
    BooleanValidator,
    DateValidator,
    ObjectValidator,
    ArrayValidator
)

# Настройка логирования
setup_logging(
    log_file="validation.log",
    log_level=logging.DEBUG,
    include_metrics=True
)

logger = ValidationLogger()

# Пример 1: Базовая валидация строки
def validate_string_example():
    """Пример валидации строки."""
    validator = StringValidator(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    
    # Валидация с контекстом
    with validation_context({"username": "john_doe"}, strict_mode=True) as context:
        is_valid, error = validator.validate("john_doe")
        logger.log_field_validation("username", "john_doe", is_valid, error)
        
        is_valid, error = validator.validate("jo")  # Слишком короткое имя
        logger.log_field_validation("username", "jo", is_valid, error)
        
        is_valid, error = validator.validate("john@doe")  # Недопустимые символы
        logger.log_field_validation("username", "john@doe", is_valid, error)

# Пример 2: Валидация объекта
def validate_user_example():
    """Пример валидации объекта пользователя."""
    user_schema = Schema({
        "username": StringValidator(min_length=3, max_length=50),
        "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
        "age": NumberValidator(min_value=18, max_value=120),
        "is_active": BooleanValidator(),
        "created_at": DateValidator()
    })
    
    user_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 25,
        "is_active": True,
        "created_at": datetime.now()
    }
    
    logger.log_validation_start(user_data)
    
    with validation_context(user_data) as context:
        is_valid, errors = user_schema.validate(user_data)
        logger.log_validation_end(is_valid, errors)

# Пример 3: Кэшированный валидатор
@cached_validator(maxsize=128)
def validate_email_domain(email: str) -> tuple[bool, Optional[str]]:
    """
    Валидация домена email с кэшированием результатов.
    
    Args:
        email: Email для валидации
    
    Returns:
        tuple[bool, Optional[str]]: Результат валидации и сообщение об ошибке
    """
    if not email or "@" not in email:
        return False, "Invalid email format"
    
    domain = email.split("@")[1]
    allowed_domains = {"example.com", "gmail.com", "yahoo.com"}
    
    if domain not in allowed_domains:
        return False, f"Domain {domain} is not allowed"
    
    return True, None

# Пример 4: Асинхронная валидация
@async_validator("Invalid email")
async def validate_email_exists(email: str) -> bool:
    """
    Асинхронная проверка существования email.
    
    Args:
        email: Email для проверки
    
    Returns:
        bool: True, если email существует
    """
    # Имитация асинхронной проверки
    await asyncio.sleep(0.1)
    return email in {"john@example.com", "jane@example.com"}

async def validate_user_async():
    """Пример асинхронной валидации пользователя."""
    from pyvalid.async_validators import create_async_schema
    
    async_schema = create_async_schema({
        "email": validate_email_exists,
        "username": lambda x: (len(x) >= 3, "Username too short")
    })
    
    user_data = {
        "email": "john@example.com",
        "username": "john"
    }
    
    logger.log_validation_start(user_data)
    
    with validation_context(user_data) as context:
        is_valid, errors = await async_schema.validate(user_data)
        logger.log_validation_end(is_valid, errors)

# Пример 5: Валидация вложенных объектов
def validate_nested_object_example():
    """Пример валидации вложенных объектов."""
    address_schema = Schema({
        "street": StringValidator(min_length=5),
        "city": StringValidator(min_length=2),
        "zip_code": StringValidator(pattern=r"^\d{5}$")
    })
    
    user_schema = Schema({
        "name": StringValidator(min_length=2),
        "address": ObjectValidator(address_schema),
        "phones": ArrayValidator(
            StringValidator(pattern=r"^\+1\d{10}$"),
            min_length=1
        )
    })
    
    user_data = {
        "name": "John Doe",
        "address": {
            "street": "123 Main St",
            "city": "New York",
            "zip_code": "10001"
        },
        "phones": ["+11234567890", "+19876543210"]
    }
    
    logger.log_validation_start(user_data)
    
    with validation_context(user_data) as context:
        is_valid, errors = user_schema.validate(user_data)
        logger.log_validation_end(is_valid, errors)

def main():
    """Запуск всех примеров."""
    print("Пример 1: Валидация строки")
    validate_string_example()
    print("\nПример 2: Валидация объекта")
    validate_user_example()
    print("\nПример 3: Кэшированный валидатор")
    print(validate_email_domain("john@example.com"))
    print(validate_email_domain("john@example.com"))  # Из кэша
    print("\nПример 4: Асинхронная валидация")
    asyncio.run(validate_user_async())
    print("\nПример 5: Валидация вложенных объектов")
    validate_nested_object_example()

if __name__ == "__main__":
    main() 