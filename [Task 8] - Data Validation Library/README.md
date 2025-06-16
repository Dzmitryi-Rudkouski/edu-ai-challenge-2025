# PyValid - Библиотека валидации данных для Python

PyValid - это мощная и гибкая библиотека для валидации данных в Python. Она предоставляет простой и интуитивно понятный API для создания и применения валидаторов к различным типам данных.

## Особенности

- Строгая типизация с поддержкой Python type hints и TypeGuard
- Валидация сложных вложенных структур данных (объекты, массивы)
- Поддержка пользовательских валидаторов
- Гибкая система сообщений об ошибках
- Поддержка опциональных и nullable полей
- Валидация массивов с проверкой типов элементов
- Интеграция с IDE (поддержка автодополнения)
- Подробная документация и примеры использования

## Требования к системе

- Python 3.8 или выше
- Зависимости:
  - typing-extensions >= 4.0.0
  - pytest (для запуска тестов)
  - mypy (для проверки типов)
  - flake8, black, isort (для проверки стиля кода)

## Установка

```bash
pip install pyvalid
```

## Быстрый старт

### Базовое использование

```python
from pyvalid import Schema
from pyvalid.validators import StringValidator, NumberValidator, BooleanValidator

# Создание схемы валидации
user_schema = Schema({
    "username": StringValidator(min_length=3, max_length=50),
    "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
    "age": NumberValidator(min_value=18, max_value=120),
    "is_active": BooleanValidator()
})

# Данные для валидации
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "age": 25,
    "is_active": True
}

# Валидация данных
is_valid, errors = user_schema.validate(user_data)
if is_valid:
    print("Данные валидны")
else:
    print("Ошибки валидации:", errors)
```

### Валидация вложенных объектов

```python
from pyvalid import Schema
from pyvalid.validators import StringValidator, ObjectValidator

# Создание схемы для адреса
address_schema = Schema({
    "street": StringValidator(),
    "city": StringValidator(),
    "postal_code": StringValidator(pattern=r"^\d{5}$"),
    "country": StringValidator()
})

# Создание схемы для пользователя с вложенным адресом
user_schema = Schema({
    "username": StringValidator(min_length=3),
    "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
    "address": ObjectValidator(address_schema)
})

# Валидация данных
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "address": {
        "street": "123 Main St",
        "city": "Anytown",
        "postal_code": "12345",
        "country": "USA"
    }
}

is_valid, errors = user_schema.validate(user_data)
```

### Асинхронная валидация

```python
from pyvalid import Schema
from pyvalid.async_validators import async_validator
import asyncio

@async_validator
async def validate_username(value: str) -> bool:
    # Имитация асинхронной проверки
    await asyncio.sleep(0.1)
    return len(value) >= 3

@async_validator
async def validate_email(value: str) -> bool:
    # Имитация асинхронной проверки
    await asyncio.sleep(0.1)
    return "@" in value and "." in value.split("@")[1]

# Создание схемы с асинхронными валидаторами
user_schema = Schema({
    "username": validate_username,
    "email": validate_email
})

# Асинхронная валидация
async def validate_user():
    user_data = {
        "username": "john_doe",
        "email": "john@example.com"
    }
    is_valid, errors = await user_schema.validate_async(user_data)
    return is_valid, errors

# Запуск валидации
result = asyncio.run(validate_user())
```

### Кэширование валидаторов

```python
from pyvalid import Schema
from pyvalid.cache import cached_validator
from pyvalid.validators import StringValidator

@cached_validator
def validate_username(value: str) -> bool:
    return len(value) >= 3

# Создание схемы с кэшированным валидатором
user_schema = Schema({
    "username": validate_username,
    "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$")
})

# Валидация (результаты будут кэшированы)
user_data = {
    "username": "john_doe",
    "email": "john@example.com"
}
is_valid, errors = user_schema.validate(user_data)
```

### Логирование валидации

```python
from pyvalid import Schema, setup_logging, ValidationLogger
from pyvalid.validators import StringValidator, NumberValidator

# Настройка логирования
setup_logging(
    log_file="validation.log",
    log_level="DEBUG",
    include_metrics=True
)

logger = ValidationLogger()

# Создание схемы
user_schema = Schema({
    "username": StringValidator(min_length=3),
    "age": NumberValidator(min_value=18)
})

# Валидация с логированием
user_data = {
    "username": "john_doe",
    "age": 25
}

logger.log_validation_start(user_data)
is_valid, errors = user_schema.validate(user_data)
logger.log_validation_end(is_valid, errors)
```

### Интеграция с веб-фреймворками

#### FastAPI

```python
from fastapi import FastAPI, HTTPException
from pyvalid import Schema
from pyvalid.validators import StringValidator, NumberValidator

app = FastAPI()

# Создание схемы
user_schema = Schema({
    "username": StringValidator(min_length=3),
    "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
    "age": NumberValidator(min_value=18)
})

@app.post("/users")
async def create_user(user_data: dict):
    is_valid, errors = user_schema.validate(user_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors)
    return {"status": "success", "data": user_data}
```

#### Django

```python
from django.http import JsonResponse
from pyvalid import Schema
from pyvalid.validators import StringValidator, NumberValidator

def validate_request(view_func):
    def wrapper(request, *args, **kwargs):
        schema = Schema({
            "username": StringValidator(min_length=3),
            "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
            "age": NumberValidator(min_value=18)
        })
        
        try:
            data = json.loads(request.body)
            is_valid, errors = schema.validate(data)
            if not is_valid:
                return JsonResponse({"errors": errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        return view_func(request, *args, **kwargs)
    return wrapper

@validate_request
def create_user(request):
    return JsonResponse({"status": "success"})
```

## Доступные валидаторы

### Базовые валидаторы

- `StringValidator` - валидация строк
  - `min_length` - минимальная длина
  - `max_length` - максимальная длина
  - `pattern` - регулярное выражение
  - `allowed_values` - разрешенные значения

- `NumberValidator` - валидация чисел
  - `min_value` - минимальное значение
  - `max_value` - максимальное значение
  - `integer_only` - только целые числа
  - `allowed_values` - разрешенные значения

- `BooleanValidator` - валидация булевых значений

- `DateValidator` - валидация дат
  - `min_date` - минимальная дата
  - `max_date` - максимальная дата
  - `format` - формат даты

### Сложные валидаторы

- `ObjectValidator` - валидация объектов
  - `schema` - схема валидации
  - `strict` - строгий режим
  - `allow_extra` - разрешить дополнительные поля

- `ArrayValidator` - валидация массивов
  - `item_validator` - валидатор элементов
  - `min_length` - минимальная длина
  - `max_length` - максимальная длина
  - `unique` - уникальные элементы

## Метрики и мониторинг

PyValid предоставляет встроенную систему метрик для отслеживания производительности валидации:

```python
from pyvalid.metrics import metrics

# Начало валидации
with metrics.start_validation():
    is_valid, errors = schema.validate(data)
    metrics.end_validation(is_valid, errors)

# Получение статистики
summary = metrics.get_summary()
print(f"Всего валидаций: {summary['total_validations']}")
print(f"Успешных: {summary['success_count']}")
print(f"Неуспешных: {summary['failure_count']}")

# Получение времени валидации полей
field_times = metrics.get_field_times()
for field, time in field_times.items():
    print(f"Поле {field}: {time:.3f} сек")
```

## Запуск тестов

```bash
# Запуск всех тестов
pytest tests/

# Запуск с отчетом о покрытии
pytest tests/ --cov=pyvalid --cov-report=html:coverage_report

# Запуск конкретного теста
pytest tests/test_validators.py -v
```

## Требования

- Python 3.7+
- Зависимости:
  - pytest (для тестов)
  - pytest-cov (для отчетов о покрытии)

## Лицензия

MIT License

## Поддержка

Если у вас возникли вопросы или проблемы, создайте issue в репозитории проекта. 