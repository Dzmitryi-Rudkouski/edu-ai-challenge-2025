"""
Модуль для расширенного логирования валидации.
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys
from .metrics import metrics

# Настройка базового логгера
logger = logging.getLogger("pyvalid")
logger.setLevel(logging.DEBUG)

# Форматтер для логов
class ValidationFormatter(logging.Formatter):
    """
    Форматтер для логов валидации.
    
    Attributes:
        include_metrics: Включать ли метрики в логи
    """
    
    def __init__(self, include_metrics: bool = True):
        super().__init__()
        self.include_metrics = include_metrics
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует запись лога.
        
        Args:
            record: Запись лога
        
        Returns:
            str: Отформатированное сообщение
        """
        # Базовая информация
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем метрики, если включены
        if self.include_metrics:
            metrics_data = metrics.get_summary()
            if metrics_data:
                log_data["metrics"] = metrics_data
        
        # Добавляем дополнительные поля
        if hasattr(record, "validation_path"):
            log_data["validation_path"] = record.validation_path
        
        if hasattr(record, "validation_data"):
            log_data["validation_data"] = record.validation_data
        
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1])
            }
        
        return json.dumps(log_data, ensure_ascii=False)

def setup_logging(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    include_metrics: bool = True,
    console_output: bool = True
) -> None:
    """
    Настраивает систему логирования.
    
    Args:
        log_file: Путь к файлу логов
        log_level: Уровень логирования
        include_metrics: Включать ли метрики в логи
        console_output: Выводить ли логи в консоль
    
    Example:
        >>> setup_logging(
        ...     log_file="validation.log",
        ...     log_level=logging.DEBUG,
        ...     include_metrics=True
        ... )
    """
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Создаем форматтер
    formatter = ValidationFormatter(include_metrics=include_metrics)
    
    # Настраиваем вывод в файл
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # Настраиваем вывод в консоль
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

def log_validation(
    message: str,
    level: int = logging.INFO,
    validation_path: Optional[str] = None,
    validation_data: Optional[Dict[str, Any]] = None,
    exc_info: Optional[Exception] = None
) -> None:
    """
    Логирует информацию о валидации.
    
    Args:
        message: Сообщение для логирования
        level: Уровень логирования
        validation_path: Путь к полю валидации
        validation_data: Данные валидации
        exc_info: Информация об исключении
    
    Example:
        >>> log_validation(
        ...     "Validation failed",
        ...     level=logging.WARNING,
        ...     validation_path="user.email",
        ...     validation_data={"value": "invalid@email"}
        ... )
    """
    extra = {}
    
    if validation_path:
        extra["validation_path"] = validation_path
    
    if validation_data:
        extra["validation_data"] = validation_data
    
    logger.log(
        level,
        message,
        extra=extra,
        exc_info=exc_info
    )

class ValidationLogger:
    """
    Класс для логирования процесса валидации.
    
    Attributes:
        validation_path: Текущий путь валидации
    """
    
    def __init__(self, validation_path: str = ""):
        self.validation_path = validation_path
    
    def log_validation_start(self, data: Dict[str, Any]) -> None:
        """
        Логирует начало валидации.
        
        Args:
            data: Данные для валидации
        """
        log_validation(
            "Starting validation",
            level=logging.DEBUG,
            validation_path=self.validation_path,
            validation_data=data
        )
    
    def log_validation_end(
        self,
        is_valid: bool,
        errors: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Логирует завершение валидации.
        
        Args:
            is_valid: Результат валидации
            errors: Словарь ошибок
        """
        message = "Validation successful" if is_valid else "Validation failed"
        level = logging.INFO if is_valid else logging.WARNING
        
        log_validation(
            message,
            level=level,
            validation_path=self.validation_path,
            validation_data={"errors": errors} if errors else None
        )
    
    def log_field_validation(
        self,
        field: str,
        value: Any,
        is_valid: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Логирует валидацию отдельного поля.
        
        Args:
            field: Имя поля
            value: Значение поля
            is_valid: Результат валидации
            error: Сообщение об ошибке
        """
        field_path = f"{self.validation_path}.{field}" if self.validation_path else field
        level = logging.DEBUG if is_valid else logging.WARNING
        
        log_validation(
            f"Field validation {'successful' if is_valid else 'failed'}",
            level=level,
            validation_path=field_path,
            validation_data={
                "value": value,
                "error": error
            } if error else {"value": value}
        )
    
    def log_validation_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Логирует ошибку валидации.
        
        Args:
            error: Исключение
            context: Дополнительный контекст
        """
        log_validation(
            "Validation error occurred",
            level=logging.ERROR,
            validation_path=self.validation_path,
            validation_data=context,
            exc_info=error
        ) 