"""
统一错误处理模块

提供自定义异常类和错误处理装饰器,用于统一管理系统错误。
"""

from loguru import logger
from functools import wraps
from typing import Callable, TypeVar, Any
import traceback


# ============ 自定义异常类 ============

class RambotException(Exception):
    """RAMBOT 基础异常类"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MediaProcessingError(RambotException):
    """媒体处理错误"""
    pass


class ASRError(RambotException):
    """语音识别错误"""
    pass


class TTSError(RambotException):
    """语音合成错误"""
    pass


class AgentError(RambotException):
    """Agent 处理错误"""
    pass


class ToolRetrievalError(RambotException):
    """工具检索错误"""
    pass


class DatabaseError(RambotException):
    """数据库操作错误"""
    pass


class ConfigurationError(RambotException):
    """配置错误"""
    pass


# ============ 错误处理装饰器 ============

T = TypeVar('T')


def handle_errors(
    default_return: Any = None,
    log_level: str = "error",
    raise_on_error: bool = False,
    error_message: str = None
):
    """
    统一错误处理装饰器
    
    Args:
        default_return: 发生错误时的默认返回值
        log_level: 日志级别 (debug/info/warning/error/critical)
        raise_on_error: 是否重新抛出异常
        error_message: 自定义错误消息前缀
    
    Usage:
        @handle_errors(default_return=None, log_level="error")
        def my_function():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except RambotException as e:
                # 自定义异常,记录详细信息
                msg = error_message or f"Error in {func.__name__}"
                log_msg = f"{msg}: {e.message}"
                if e.details:
                    log_msg += f" | Details: {e.details}"
                
                getattr(logger, log_level)(log_msg)
                
                if raise_on_error:
                    raise
                return default_return
            
            except Exception as e:
                # 未知异常,记录完整堆栈
                msg = error_message or f"Unexpected error in {func.__name__}"
                log_msg = f"{msg}: {type(e).__name__}: {str(e)}"
                
                getattr(logger, log_level)(log_msg)
                if log_level in ["error", "critical"]:
                    logger.debug(f"Traceback:\n{traceback.format_exc()}")
                
                if raise_on_error:
                    raise
                return default_return
        
        return wrapper
    return decorator


def handle_async_errors(
    default_return: Any = None,
    log_level: str = "error",
    raise_on_error: bool = False,
    error_message: str = None
):
    """
    异步函数错误处理装饰器
    
    Args:
        default_return: 发生错误时的默认返回值
        log_level: 日志级别
        raise_on_error: 是否重新抛出异常
        error_message: 自定义错误消息前缀
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except RambotException as e:
                msg = error_message or f"Error in {func.__name__}"
                log_msg = f"{msg}: {e.message}"
                if e.details:
                    log_msg += f" | Details: {e.details}"
                
                getattr(logger, log_level)(log_msg)
                
                if raise_on_error:
                    raise
                return default_return
            
            except Exception as e:
                msg = error_message or f"Unexpected error in {func.__name__}"
                log_msg = f"{msg}: {type(e).__name__}: {str(e)}"
                
                getattr(logger, log_level)(log_msg)
                if log_level in ["error", "critical"]:
                    logger.debug(f"Traceback:\n{traceback.format_exc()}")
                
                if raise_on_error:
                    raise
                return default_return
        
        return wrapper
    return decorator


# ============ 错误处理工具类 ============

class ErrorHandler:
    """错误处理工具类"""
    
    @staticmethod
    def safe_execute(
        func: Callable,
        *args,
        default_return: Any = None,
        error_message: str = None,
        **kwargs
    ) -> Any:
        """
        安全执行函数,捕获所有异常
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            default_return: 错误时的默认返回值
            error_message: 自定义错误消息
            **kwargs: 函数关键字参数
        
        Returns:
            函数返回值或默认返回值
        """
        try:
            return func(*args, **kwargs)
        except RambotException as e:
            msg = error_message or f"Error executing {func.__name__}"
            logger.error(f"{msg}: {e.message}")
            if e.details:
                logger.debug(f"Details: {e.details}")
            return default_return
        except Exception as e:
            msg = error_message or f"Unexpected error executing {func.__name__}"
            logger.error(f"{msg}: {type(e).__name__}: {str(e)}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return default_return
    
    @staticmethod
    def safe_cleanup(cleanup_func: Callable, *args, **kwargs):
        """
        安全执行清理函数,即使失败也不影响主流程
        
        Args:
            cleanup_func: 清理函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        try:
            cleanup_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Cleanup failed in {cleanup_func.__name__}: {e}")
    
    @staticmethod
    def log_and_raise(
        exception_class: type,
        message: str,
        details: dict = None,
        log_level: str = "error"
    ):
        """
        记录日志并抛出异常
        
        Args:
            exception_class: 异常类
            message: 错误消息
            details: 详细信息
            log_level: 日志级别
        """
        log_msg = message
        if details:
            log_msg += f" | Details: {details}"
        
        getattr(logger, log_level)(log_msg)
        
        if issubclass(exception_class, RambotException):
            raise exception_class(message, details)
        else:
            raise exception_class(message)
