"""平台基类和通用模型"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
from curl_cffi import requests


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


@dataclass
class OrderResult:
    """订单结果"""
    success: bool
    order_id: Optional[str] = None
    qrcode_url: Optional[str] = None
    pay_url: Optional[str] = None
    amount: Optional[float] = None
    status: OrderStatus = OrderStatus.UNKNOWN
    message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = field(default_factory=dict)


class PlatformBase(ABC):
    """平台基类"""

    name: str = ""

    def __init__(self):
        self.session = requests.Session()
        self._init_headers()
    
    @abstractmethod
    def _init_headers(self):
        """初始化请求头"""
        pass
    
    @abstractmethod
    def create_order(self, user_id: str, amount: float, **kwargs) -> OrderResult:
        """
        创建充值订单
        
        Args:
            user_id: 用户标识（快手号/邮箱/API Key等）
            amount: 金额
            **kwargs: 平台特定参数
        
        Returns:
            OrderResult: 订单结果
        """
        pass
    
    @abstractmethod
    def query_order(self, order_id: str) -> OrderResult:
        """查询订单状态"""
        pass
    
    def close(self):
        """关闭session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
