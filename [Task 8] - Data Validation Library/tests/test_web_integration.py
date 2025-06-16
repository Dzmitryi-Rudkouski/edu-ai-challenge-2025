"""
Тесты для интеграции PyValid с веб-фреймворками.
"""

import pytest
from datetime import datetime
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from django.test import Client, RequestFactory
from django.http import HttpRequest, HttpResponse

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
    DateValidator
)
from pyvalid.examples.web_frameworks import (
    app as fastapi_app,
    UserValidationView,
    ValidationMiddleware,
    validate_request
)

# Настройка логирования для тестов
setup_logging(
    log_file="test_web_validation.log",
    log_level=logging.DEBUG,
    include_metrics=True
)

logger = ValidationLogger()

# Фикстуры
@pytest.fixture
def user_schema():
    """Фикстура для схемы пользователя."""
    return Schema({
        "username": StringValidator(min_length=3, max_length=50),
        "email": StringValidator(pattern=r"^[^@]+@[^@]+\.[^@]+$"),
        "age": NumberValidator(min_value=18, max_value=120),
        "is_active": BooleanValidator(),
        "created_at": DateValidator()
    })

@pytest.fixture
def valid_user_data():
    """Фикстура для валидных данных пользователя."""
    return {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 25,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def invalid_user_data():
    """Фикстура для невалидных данных пользователя."""
    return {
        "username": "jo",  # Слишком короткое имя
        "email": "invalid-email",  # Неверный формат email
        "age": 15,  # Слишком молодой
        "is_active": "yes",  # Неверный тип
        "created_at": "invalid-date"  # Неверный формат даты
    }

# Тесты для FastAPI
class TestFastAPI:
    """Тесты для интеграции с FastAPI."""
    
    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента FastAPI."""
        return TestClient(fastapi_app)
    
    def test_create_valid_user(self, client, valid_user_data):
        """Тест создания валидного пользователя."""
        response = client.post(
            "/users/",
            json=valid_user_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user"] == valid_user_data
    
    def test_create_invalid_user(self, client, invalid_user_data):
        """Тест создания невалидного пользователя."""
        response = client.post(
            "/users/",
            json=invalid_user_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "validation_errors" in data
        assert len(data["validation_errors"]) > 0
    
    def test_middleware_validation(self, client, user_schema):
        """Тест валидации через middleware."""
        # Создаем тестовое приложение с middleware
        app = FastAPI()
        app.add_middleware(
            ValidationMiddleware,
            schema=user_schema
        )
        
        @app.post("/test/")
        async def test_endpoint(data: Dict[str, Any]):
            return {"status": "success", "data": data}
        
        test_client = TestClient(app)
        
        # Тест валидных данных
        valid_data = {
            "username": "john_doe",
            "email": "john@example.com",
            "age": 25,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        response = test_client.post("/test/", json=valid_data)
        assert response.status_code == 200
        
        # Тест невалидных данных
        invalid_data = {
            "username": "jo",
            "email": "invalid-email",
            "age": 15,
            "is_active": "yes",
            "created_at": "invalid-date"
        }
        
        response = test_client.post("/test/", json=invalid_data)
        assert response.status_code == 400
        data = response.json()
        assert "validation_errors" in data

# Тесты для Django
class TestDjango:
    """Тесты для интеграции с Django."""
    
    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента Django."""
        return Client()
    
    @pytest.fixture
    def factory(self):
        """Фикстура для фабрики запросов Django."""
        return RequestFactory()
    
    def test_validation_view(self, factory, valid_user_data, invalid_user_data):
        """Тест представления валидации."""
        view = UserValidationView.as_view()
        
        # Тест валидных данных
        request = factory.post(
            "/validate/",
            data=valid_user_data,
            content_type="application/json"
        )
        response = view(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "success"
        assert data["user"] == valid_user_data
        
        # Тест невалидных данных
        request = factory.post(
            "/validate/",
            data=invalid_user_data,
            content_type="application/json"
        )
        response = view(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert "validation_errors" in data
    
    def test_validation_decorator(self, factory, user_schema):
        """Тест декоратора валидации."""
        @validate_request(user_schema)
        def test_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse(
                json.dumps({"status": "success"}),
                content_type="application/json"
            )
        
        # Тест валидных данных
        valid_data = {
            "username": "john_doe",
            "email": "john@example.com",
            "age": 25,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        request = factory.post(
            "/test/",
            data=valid_data,
            content_type="application/json"
        )
        response = test_view(request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "success"
        
        # Тест невалидных данных
        invalid_data = {
            "username": "jo",
            "email": "invalid-email",
            "age": 15,
            "is_active": "yes",
            "created_at": "invalid-date"
        }
        
        request = factory.post(
            "/test/",
            data=invalid_data,
            content_type="application/json"
        )
        response = test_view(request)
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert "validation_errors" in data
    
    def test_error_handling(self, factory, user_schema):
        """Тест обработки ошибок."""
        @validate_request(user_schema)
        def error_view(request: HttpRequest) -> HttpResponse:
            raise ValueError("Test error")
        
        request = factory.post(
            "/error/",
            data={},
            content_type="application/json"
        )
        
        response = error_view(request)
        assert response.status_code == 500
        data = json.loads(response.content)
        assert data["status"] == "error"
        assert "message" in data

# Тесты для общих компонентов
class TestWebComponents:
    """Тесты для общих компонентов веб-интеграции."""
    
    def test_validation_context(self, user_schema, valid_user_data):
        """Тест контекста валидации в веб-запросе."""
        with validation_context(valid_user_data) as context:
            is_valid, errors = user_schema.validate(valid_user_data)
            assert is_valid
            assert errors is None
            
            # Проверка пути валидации
            assert context.get_full_path() == ""
            
            # Проверка значения поля
            assert context.get_field_value("username") == "john_doe"
    
    def test_logging_integration(self, user_schema, valid_user_data, invalid_user_data):
        """Тест интеграции логирования с веб-запросами."""
        logger = ValidationLogger()
        
        # Логирование валидного запроса
        logger.log_validation_start(valid_user_data)
        with validation_context(valid_user_data) as context:
            is_valid, errors = user_schema.validate(valid_user_data)
            logger.log_validation_end(is_valid, errors)
        
        # Логирование невалидного запроса
        logger.log_validation_start(invalid_user_data)
        with validation_context(invalid_user_data) as context:
            is_valid, errors = user_schema.validate(invalid_user_data)
            logger.log_validation_end(is_valid, errors)
        
        # Логирование ошибки
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.log_validation_error(e, {"data": invalid_user_data})
    
    def test_metrics_integration(self, user_schema, valid_user_data, invalid_user_data):
        """Тест интеграции метрик с веб-запросами."""
        from pyvalid.metrics import metrics
        
        # Сброс метрик
        metrics._total_validations = 0
        metrics._total_time = 0
        metrics._success_count = 0
        metrics._failure_count = 0
        metrics._field_times.clear()
        metrics._error_counts.clear()
        
        # Валидация валидных данных
        with validation_context(valid_user_data) as context:
            is_valid, errors = user_schema.validate(valid_user_data)
        
        # Валидация невалидных данных
        with validation_context(invalid_user_data) as context:
            is_valid, errors = user_schema.validate(invalid_user_data)
        
        # Проверка метрик
        stats = metrics.get_summary()
        assert stats["total_validations"] == 2
        assert stats["success_count"] == 1
        assert stats["failure_count"] == 1
        assert stats["success_rate"] == 0.5
        assert stats["average_time"] > 0
        
        # Проверка метрик полей
        field_stats = metrics.get_field_stats()
        assert len(field_stats) > 0
        
        # Проверка подсчета ошибок
        error_counts = metrics._error_counts
        assert len(error_counts) > 0
        assert sum(error_counts.values()) > 0 