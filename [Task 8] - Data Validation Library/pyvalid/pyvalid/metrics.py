"""
Модуль для сбора и анализа метрик производительности валидации.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationMetrics:
    """
    Класс для сбора и анализа метрик производительности валидации.
    
    Attributes:
        total_validations: Общее количество валидаций
        total_time: Общее время валидации в секундах
        success_count: Количество успешных валидаций
        failure_count: Количество неуспешных валидаций
        field_times: Время валидации по полям
        error_counts: Количество ошибок по типам
    """
    total_validations: int = 0
    total_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    field_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def start_validation(self) -> float:
        """
        Начинает отсчет времени для валидации.
        
        Returns:
            Время начала валидации
        """
        return time.perf_counter()
    
    def end_validation(self, start_time: float, path: str, success: bool, error_type: Optional[str] = None) -> None:
        """
        Завершает отсчет времени и обновляет метрики.
        
        Args:
            start_time: Время начала валидации
            path: Путь к валидируемому полю
            success: Результат валидации
            error_type: Тип ошибки, если валидация не удалась
        """
        duration = time.perf_counter() - start_time
        
        self.total_validations += 1
        self.total_time += duration
        self.field_times[path].append(duration)
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error_type:
                self.error_counts[error_type] += 1
    
    def get_field_stats(self, path: str) -> Dict[str, float]:
        """
        Возвращает статистику по времени валидации для поля.
        
        Args:
            path: Путь к полю
        
        Returns:
            Словарь со статистикой (min, max, avg, median)
        """
        times = self.field_times[path]
        if not times:
            return {}
            
        return {
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "count": len(times)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Возвращает общую статистику валидации.
        
        Returns:
            Словарь с общей статистикой
        """
        return {
            "total_validations": self.total_validations,
            "total_time": self.total_time,
            "success_rate": self.success_count / self.total_validations if self.total_validations > 0 else 0,
            "average_time": self.total_time / self.total_validations if self.total_validations > 0 else 0,
            "error_distribution": dict(self.error_counts),
            "field_stats": {
                path: self.get_field_stats(path)
                for path in self.field_times
            }
        }
    
    def log_summary(self) -> None:
        """
        Логирует общую статистику валидации.
        """
        summary = self.get_summary()
        logger.info("Validation Metrics Summary:")
        logger.info(f"Total validations: {summary['total_validations']}")
        logger.info(f"Total time: {summary['total_time']:.3f}s")
        logger.info(f"Success rate: {summary['success_rate']:.2%}")
        logger.info(f"Average time: {summary['average_time']:.3f}s")
        logger.info("Error distribution:")
        for error_type, count in summary['error_distribution'].items():
            logger.info(f"  {error_type}: {count}")
        logger.info("Field statistics:")
        for path, stats in summary['field_stats'].items():
            logger.info(f"  {path}:")
            logger.info(f"    Count: {stats['count']}")
            logger.info(f"    Min: {stats['min']:.3f}s")
            logger.info(f"    Max: {stats['max']:.3f}s")
            logger.info(f"    Avg: {stats['avg']:.3f}s")
            logger.info(f"    Median: {stats['median']:.3f}s")

# Глобальный экземпляр метрик
metrics = ValidationMetrics() 