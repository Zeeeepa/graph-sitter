"""
System monitors for error detection.
"""

import asyncio
import psutil
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ..models.events import HealthMetric
from ..models.enums import HealthStatus


class BaseMonitor(ABC):
    """Base class for system monitors."""
    
    def __init__(self, threshold_warning: Optional[float] = None, threshold_critical: Optional[float] = None):
        """
        Initialize monitor with thresholds.
        
        Args:
            threshold_warning: Warning threshold value
            threshold_critical: Critical threshold value
        """
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def get_current_value(self) -> float:
        """Get current metric value."""
        pass
    
    @abstractmethod
    def get_metric_name(self) -> str:
        """Get metric name."""
        pass
    
    def get_component_name(self) -> str:
        """Get component name."""
        return "system"
    
    async def get_metric(self) -> Optional[HealthMetric]:
        """
        Get current health metric.
        
        Returns:
            HealthMetric object with current status
        """
        try:
            current_value = await self.get_current_value()
            
            metric = HealthMetric(
                metric_name=self.get_metric_name(),
                current_value=current_value,
                threshold_warning=self.threshold_warning,
                threshold_critical=self.threshold_critical,
                component=self.get_component_name(),
                measured_at=datetime.utcnow()
            )
            
            # Evaluate status based on thresholds
            metric.evaluate_status()
            
            return metric
            
        except Exception as e:
            self.logger.error(f"Error getting metric {self.get_metric_name()}: {e}")
            return None


class CPUMonitor(BaseMonitor):
    """Monitor CPU usage."""
    
    def __init__(self, threshold_critical: float = 90.0, threshold_warning: float = 80.0):
        """
        Initialize CPU monitor.
        
        Args:
            threshold_critical: Critical CPU usage threshold (%)
            threshold_warning: Warning CPU usage threshold (%)
        """
        super().__init__(threshold_warning, threshold_critical)
        self._last_measurement = None
        self._measurement_interval = 1.0  # seconds
    
    async def get_current_value(self) -> float:
        """Get current CPU usage percentage."""
        # Use non-blocking CPU measurement
        if self._last_measurement is None:
            # First measurement, need to wait for interval
            psutil.cpu_percent(interval=None)  # Initialize
            await asyncio.sleep(self._measurement_interval)
        
        cpu_percent = psutil.cpu_percent(interval=None)
        self._last_measurement = time.time()
        return cpu_percent
    
    def get_metric_name(self) -> str:
        """Get metric name."""
        return "cpu_usage"


class MemoryMonitor(BaseMonitor):
    """Monitor memory usage."""
    
    def __init__(self, threshold_critical: float = 95.0, threshold_warning: float = 85.0):
        """
        Initialize memory monitor.
        
        Args:
            threshold_critical: Critical memory usage threshold (%)
            threshold_warning: Warning memory usage threshold (%)
        """
        super().__init__(threshold_warning, threshold_critical)
    
    async def get_current_value(self) -> float:
        """Get current memory usage percentage."""
        memory = psutil.virtual_memory()
        return memory.percent
    
    def get_metric_name(self) -> str:
        """Get metric name."""
        return "memory_usage"


class DiskMonitor(BaseMonitor):
    """Monitor disk usage."""
    
    def __init__(self, path: str = "/", threshold_critical: float = 95.0, threshold_warning: float = 85.0):
        """
        Initialize disk monitor.
        
        Args:
            path: Path to monitor disk usage for
            threshold_critical: Critical disk usage threshold (%)
            threshold_warning: Warning disk usage threshold (%)
        """
        super().__init__(threshold_warning, threshold_critical)
        self.path = path
    
    async def get_current_value(self) -> float:
        """Get current disk usage percentage."""
        disk = psutil.disk_usage(self.path)
        return (disk.used / disk.total) * 100
    
    def get_metric_name(self) -> str:
        """Get metric name."""
        return f"disk_usage_{self.path.replace('/', '_')}"
    
    def get_component_name(self) -> str:
        """Get component name."""
        return f"disk_{self.path}"


class NetworkMonitor(BaseMonitor):
    """Monitor network performance."""
    
    def __init__(self, threshold_critical: float = 5000.0, threshold_warning: float = 2000.0):
        """
        Initialize network monitor.
        
        Args:
            threshold_critical: Critical response time threshold (ms)
            threshold_warning: Warning response time threshold (ms)
        """
        super().__init__(threshold_warning, threshold_critical)
        self._last_stats = None
        self._last_time = None
    
    async def get_current_value(self) -> float:
        """Get current network latency/response time."""
        try:
            # Simple network check - measure time to get network stats
            start_time = time.time()
            net_io = psutil.net_io_counters()
            end_time = time.time()
            
            # Calculate response time in milliseconds
            response_time = (end_time - start_time) * 1000
            
            # If we have previous stats, calculate packet loss rate
            if self._last_stats and self._last_time:
                time_diff = end_time - self._last_time
                if time_diff > 0:
                    # Calculate network throughput as a proxy for health
                    bytes_sent_diff = net_io.bytes_sent - self._last_stats.bytes_sent
                    bytes_recv_diff = net_io.bytes_recv - self._last_stats.bytes_recv
                    
                    # Store for next calculation
                    self._last_stats = net_io
                    self._last_time = end_time
                    
                    # Return response time for now
                    return response_time
            
            self._last_stats = net_io
            self._last_time = end_time
            return response_time
            
        except Exception as e:
            self.logger.error(f"Error measuring network performance: {e}")
            return 0.0
    
    def get_metric_name(self) -> str:
        """Get metric name."""
        return "network_response_time"
    
    def get_component_name(self) -> str:
        """Get component name."""
        return "network"


class ErrorRateMonitor(BaseMonitor):
    """Monitor application error rate."""
    
    def __init__(self, threshold_critical: float = 10.0, threshold_warning: float = 5.0):
        """
        Initialize error rate monitor.
        
        Args:
            threshold_critical: Critical error rate threshold (%)
            threshold_warning: Warning error rate threshold (%)
        """
        super().__init__(threshold_warning, threshold_critical)
        self.error_count = 0
        self.total_requests = 0
        self.window_start = time.time()
        self.window_duration = 300  # 5 minutes
    
    async def get_current_value(self) -> float:
        """Get current error rate percentage."""
        current_time = time.time()
        
        # Reset window if needed
        if current_time - self.window_start > self.window_duration:
            self.error_count = 0
            self.total_requests = 0
            self.window_start = current_time
        
        # Calculate error rate
        if self.total_requests == 0:
            return 0.0
        
        return (self.error_count / self.total_requests) * 100
    
    def record_request(self, is_error: bool = False) -> None:
        """
        Record a request and whether it was an error.
        
        Args:
            is_error: True if the request resulted in an error
        """
        self.total_requests += 1
        if is_error:
            self.error_count += 1
    
    def get_metric_name(self) -> str:
        """Get metric name."""
        return "error_rate"
    
    def get_component_name(self) -> str:
        """Get component name."""
        return "application"


class ProcessMonitor(BaseMonitor):
    """Monitor specific process metrics."""
    
    def __init__(self, process_name: str, threshold_critical: float = 95.0, threshold_warning: float = 85.0):
        """
        Initialize process monitor.
        
        Args:
            process_name: Name of process to monitor
            threshold_critical: Critical threshold
            threshold_warning: Warning threshold
        """
        super().__init__(threshold_warning, threshold_critical)
        self.process_name = process_name
        self._process = None
    
    def _find_process(self) -> Optional[psutil.Process]:
        """Find the process by name."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == self.process_name:
                    return psutil.Process(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
    
    async def get_current_value(self) -> float:
        """Get current process CPU usage."""
        try:
            if self._process is None or not self._process.is_running():
                self._process = self._find_process()
            
            if self._process:
                return self._process.cpu_percent()
            else:
                return 0.0  # Process not found
                
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.warning(f"Cannot access process {self.process_name}: {e}")
            return 0.0
    
    def get_metric_name(self) -> str:
        """Get metric name."""
        return f"process_cpu_{self.process_name}"
    
    def get_component_name(self) -> str:
        """Get component name."""
        return f"process_{self.process_name}"

