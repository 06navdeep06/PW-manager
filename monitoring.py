"""
Monitoring and error handling utilities for the Discord bot.
"""

import logging
import time
import asyncio
from typing import Dict, Any
from collections import defaultdict, deque

class BotMonitor:
    """Monitor bot performance and health."""
    
    def __init__(self):
        self.metrics = {
            "messages_processed": 0,
            "commands_executed": 0,
            "errors_occurred": 0,
            "ocr_operations": 0,
            "database_operations": 0,
            "start_time": time.time()
        }
        
        self.error_counts = defaultdict(int)
        self.performance_data = deque(maxlen=100)  # Keep last 100 operations
        self.logger = logging.getLogger(__name__)
    
    def record_message(self):
        """Record a processed message."""
        self.metrics["messages_processed"] += 1
    
    def record_command(self):
        """Record a command execution."""
        self.metrics["commands_executed"] += 1
    
    def record_error(self, error_type: str, error_message: str = ""):
        """Record an error occurrence."""
        self.metrics["errors_occurred"] += 1
        self.error_counts[error_type] += 1
        self.logger.error(f"Error recorded: {error_type} - {error_message}")
    
    def record_ocr_operation(self, duration: float):
        """Record an OCR operation."""
        self.metrics["ocr_operations"] += 1
        self.performance_data.append({
            "operation": "ocr",
            "duration": duration,
            "timestamp": time.time()
        })
    
    def record_database_operation(self, operation: str, duration: float):
        """Record a database operation."""
        self.metrics["database_operations"] += 1
        self.performance_data.append({
            "operation": f"db_{operation}",
            "duration": duration,
            "timestamp": time.time()
        })
    
    def get_uptime(self) -> float:
        """Get bot uptime in seconds."""
        return time.time() - self.metrics["start_time"]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        uptime = self.get_uptime()
        
        return {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "messages_per_hour": (self.metrics["messages_processed"] / uptime) * 3600 if uptime > 0 else 0,
            "commands_per_hour": (self.metrics["commands_executed"] / uptime) * 3600 if uptime > 0 else 0,
            "error_rate": self.metrics["errors_occurred"] / max(self.metrics["messages_processed"], 1),
            "total_operations": sum(self.metrics.values()) - self.metrics["start_time"],
            "error_breakdown": dict(self.error_counts),
            "recent_performance": list(self.performance_data)[-10:] if self.performance_data else []
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check."""
        uptime = self.get_uptime()
        error_rate = self.metrics["errors_occurred"] / max(self.metrics["messages_processed"], 1)
        
        health_status = "healthy"
        if error_rate > 0.1:  # More than 10% error rate
            health_status = "degraded"
        if error_rate > 0.3:  # More than 30% error rate
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "uptime": uptime,
            "error_rate": error_rate,
            "total_messages": self.metrics["messages_processed"],
            "total_errors": self.metrics["errors_occurred"],
            "timestamp": time.time()
        }

# Global monitor instance
monitor = BotMonitor()

def record_operation(operation_type: str):
    """Decorator to record operation metrics."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if operation_type == "ocr":
                    monitor.record_ocr_operation(duration)
                elif operation_type.startswith("db_"):
                    monitor.record_database_operation(operation_type[3:], duration)
                
                return result
            except Exception as e:
                monitor.record_error(f"{operation_type}_error", str(e))
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if operation_type == "ocr":
                    monitor.record_ocr_operation(duration)
                elif operation_type.startswith("db_"):
                    monitor.record_database_operation(operation_type[3:], duration)
                
                return result
            except Exception as e:
                monitor.record_error(f"{operation_type}_error", str(e))
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
