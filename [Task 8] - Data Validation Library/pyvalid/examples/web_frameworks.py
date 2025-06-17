"""
Примеры интеграции PyValid с веб-фреймворками.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from django.http import JsonResponse
from django.views import View
from django.core.exceptions import ValidationError

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
    DateValidator,
    ObjectValidator,
    ArrayValidator
)

# Настройка логирования
setup_logging(
    log_file="web_validation.log",
    log_level=logging.DEBUG,
    include_metrics=True
)

logger = ValidationLogger()

# Общие схемы валидации
user_schema = Schema({
    "username": StringValidator(min_length=3, max_length=50),
    "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
    "age": NumberValidator(min_value=18, max_value=120),
    "is_active": BooleanValidator(),
    "created_at": DateValidator()
})

# Пример 1: Интеграция с FastAPI
app = FastAPI(title="PyValid FastAPI Example")

class UserModel(BaseModel):
    """Модель пользователя для FastAPI."""
    username: str
    email: str
    age: int
    is_active: bool
    created_at: datetime

def validate_user_data(data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, str]]]:
    """
    Валидация данных пользователя.
    
    Args:
        data: Данные пользователя
    
    Returns:
        tuple[bool, Optional[Dict[str, str]]]: Результат валидации и ошибки
    """
    logger.log_validation_start(data)
    
    with validation_context(data) as context:
        is_valid, errors = user_schema.validate(data)
        logger.log_validation_end(is_valid, errors)
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={"validation_errors": errors}
            )
        
        return is_valid, errors

@app.post("/users/")
async def create_user(user: UserModel):
    """
    Создание пользователя с валидацией.
    
    Args:
        user: Данные пользователя
    
    Returns:
        Dict[str, Any]: Результат создания
    """
    try:
        # Валидация данных
        is_valid, errors = validate_user_data(user.dict())
        
        # Здесь была бы логика создания пользователя
        return {
            "status": "success",
            "message": "User created successfully",
            "user": user.dict()
        }
    
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
    except Exception as e:
        logger.log_validation_error(e, {"user_data": user.dict()})
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

# Пример 2: Интеграция с Django
class UserValidationView(View):
    """Представление для валидации пользователя в Django."""
    
    def post(self, request):
        """
        Обработка POST-запроса для создания пользователя.
        
        Args:
            request: HTTP-запрос
        
        Returns:
            JsonResponse: Ответ с результатом валидации
        """
        try:
            # Получение данных из запроса
            user_data = request.POST.dict()
            
            # Валидация данных
            logger.log_validation_start(user_data)
            
            with validation_context(user_data) as context:
                is_valid, errors = user_schema.validate(user_data)
                logger.log_validation_end(is_valid, errors)
                
                if not is_valid:
                    return JsonResponse(
                        {
                            "status": "error",
                            "validation_errors": errors
                        },
                        status=400
                    )
            
            # Здесь была бы логика создания пользователя
            return JsonResponse({
                "status": "success",
                "message": "User created successfully",
                "user": user_data
            })
        
        except ValidationError as e:
            logger.log_validation_error(e, {"user_data": user_data})
            return JsonResponse(
                {
                    "status": "error",
                    "message": str(e)
                },
                status=400
            )
        
        except Exception as e:
            logger.log_validation_error(e, {"user_data": user_data})
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Internal server error"
                },
                status=500
            )

# Пример 3: Middleware для FastAPI
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware для валидации запросов в FastAPI.
    
    Attributes:
        schema: Схема валидации
    """
    
    def __init__(self, app, schema: Schema):
        super().__init__(app)
        self.schema = schema
    
    async def dispatch(
        self,
        request: Request,
        call_next
    ):
        """
        Обработка запроса с валидацией.
        
        Args:
            request: HTTP-запрос
            call_next: Следующий обработчик
        
        Returns:
            Response: HTTP-ответ
        """
        try:
            # Получение данных из запроса
            if request.method in ("POST", "PUT", "PATCH"):
                body = await request.json()
                
                # Валидация данных
                logger.log_validation_start(body)
                
                with validation_context(body) as context:
                    is_valid, errors = self.schema.validate(body)
                    logger.log_validation_end(is_valid, errors)
                    
                    if not is_valid:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "status": "error",
                                "validation_errors": errors
                            }
                        )
            
            # Продолжение обработки запроса
            response = await call_next(request)
            return response
        
        except Exception as e:
            logger.log_validation_error(e)
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Internal server error"
                }
            )

# Пример использования middleware
app.add_middleware(
    ValidationMiddleware,
    schema=user_schema
)

# Пример 4: Декоратор для валидации в Django
from functools import wraps
from django.http import HttpRequest, HttpResponse

def validate_request(schema: Schema):
    """
    Декоратор для валидации запросов в Django.
    
    Args:
        schema: Схема валидации
    
    Returns:
        Callable: Декорированная функция
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            try:
                # Получение данных из запроса
                if request.method in ("POST", "PUT", "PATCH"):
                    data = request.POST.dict()
                    
                    # Валидация данных
                    logger.log_validation_start(data)
                    
                    with validation_context(data) as context:
                        is_valid, errors = schema.validate(data)
                        logger.log_validation_end(is_valid, errors)
                        
                        if not is_valid:
                            return JsonResponse(
                                {
                                    "status": "error",
                                    "validation_errors": errors
                                },
                                status=400
                            )
                
                # Вызов оригинальной функции
                return view_func(request, *args, **kwargs)
            
            except Exception as e:
                logger.log_validation_error(e)
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Internal server error"
                    },
                    status=500
                )
        
        return wrapper
    return decorator

# Пример использования декоратора
@validate_request(user_schema)
def create_user_view(request: HttpRequest) -> HttpResponse:
    """
    Представление для создания пользователя с валидацией.
    
    Args:
        request: HTTP-запрос
    
    Returns:
        HttpResponse: HTTP-ответ
    """
    # Здесь была бы логика создания пользователя
    return JsonResponse({
        "status": "success",
        "message": "User created successfully"
    }) 