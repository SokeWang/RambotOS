"""
并发控制管理器

提供线程池和请求队列管理,防止资源耗尽。
"""

from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Full
from threading import Lock
from typing import Callable, Any, Optional
from loguru import logger
import time


class ConcurrencyManager:
    """
    并发控制管理器 (单例模式)
    
    功能:
    1. 限制同时运行的任务数量
    2. 提供请求队列
    3. 防止资源耗尽
    """
    
    _instance: Optional['ConcurrencyManager'] = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, max_workers: int = 2, max_queue_size: int = 10):
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="rambot_worker"
        )
        
        # 请求队列
        self.request_queue = Queue(maxsize=max_queue_size)
        
        # 当前运行的任务
        self.active_tasks: dict[str, Future] = {}
        self.active_tasks_lock = Lock()
    
    def submit_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        **kwargs
    ) -> Optional[Future]:
        """
        提交任务到线程池
        
        Args:
            task_id: 任务唯一标识
            func: 要执行的函数
            *args: 函数参数
            on_complete: 完成回调
            on_error: 错误回调
            **kwargs: 函数关键字参数
            
        Returns:
            Future 对象,如果队列已满则返回 None
        """
        # 检查是否已有相同任务在运行
        with self.active_tasks_lock:
            if task_id in self.active_tasks:
                existing_future = self.active_tasks[task_id]
                if not existing_future.done():
                    logger.warning(f"Task {task_id} is already running, skipping")
                    return None
                else:
                    # 清理已完成的任务
                    del self.active_tasks[task_id]
        
        # 提交任务
        try:
            future = self.executor.submit(self._task_wrapper, task_id, func, on_complete, on_error, *args, **kwargs)
            
            with self.active_tasks_lock:
                self.active_tasks[task_id] = future
            return future
        
        except Exception as e:
            logger.error(f"Failed to submit task {task_id}: {type(e).__name__}: {e}")
            return None
    
    def _task_wrapper(
        self,
        task_id: str,
        func: Callable,
        on_complete: Optional[Callable],
        on_error: Optional[Callable],
        *args,
        **kwargs
    ) -> Any:
        """
        任务包装器,处理回调和清理
        """
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            
            if on_complete:
                try:
                    on_complete(result)
                except Exception as e:
                    logger.error(f"Error in on_complete callback for task {task_id}: {e}")
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Task {task_id} failed after {duration:.2f}s: {type(e).__name__}: {e}")
            
            if on_error:
                try:
                    on_error(e)
                except Exception as callback_error:
                    logger.error(f"Error in on_error callback for task {task_id}: {callback_error}")
            
            raise
        
        finally:
            # 清理任务
            with self.active_tasks_lock:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否成功取消
        """
        with self.active_tasks_lock:
            if task_id in self.active_tasks:
                future = self.active_tasks[task_id]
                if future.cancel():
                    logger.info(f"Task {task_id} cancelled")
                    del self.active_tasks[task_id]
                    return True
                else:
                    logger.warning(f"Task {task_id} could not be cancelled (already running)")
                    return False
            else:
                logger.warning(f"Task {task_id} not found")
                return False
    
    def get_stats(self) -> dict:
        """
        获取并发统计信息
        
        Returns:
            统计信息字典
        """
        with self.active_tasks_lock:
            active_count = len(self.active_tasks)
        
        return {
            "max_workers": self.max_workers,
            "active_tasks": active_count,
            "queue_size": self.request_queue.qsize(),
            "max_queue_size": self.max_queue_size,
        }
    
    def shutdown(self, wait: bool = True):
        """
        关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        logger.info("Shutting down ConcurrencyManager...")
        self.executor.shutdown(wait=wait)
        logger.info("ConcurrencyManager shutdown complete")


# 全局单例实例
_concurrency_manager = None


def get_concurrency_manager(max_workers: int = 2, max_queue_size: int = 10) -> ConcurrencyManager:
    """
    获取并发控制管理器单例
    
    Args:
        max_workers: 最大工作线程数
        max_queue_size: 最大队列大小
        
    Returns:
        ConcurrencyManager 实例
    """
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager(max_workers, max_queue_size)
    return _concurrency_manager
