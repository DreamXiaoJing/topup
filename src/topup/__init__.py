"""
TopUp - 统一充值SDK

支持平台：
- kuaishou: 快手充值快币
- deepseek: DeepSeek充值token

使用示例：
    from topup import TopUp
    
    # 快手充值
    topup = TopUp("kuaishou")
    result = topup.create_order(user_id="快手号", amount=10)
    print(result.qrcode_url)
    
    # DeepSeek充值
    topup = TopUp("deepseek")
    result = topup.create_order(
        user_id="xxx", 
        amount=10, 
        auth_token="your_bearer_token"
    )
    print(result.pay_url)
"""

from topup.core.base import PlatformBase, OrderResult, OrderStatus
from topup.platforms import PLATFORMS, KuaishouPlatform, DeepSeekPlatform


class TopUp:
    """统一充值入口"""
    
    def __init__(self, platform: str):
        """
        初始化充值平台
        
        Args:
            platform: 平台名称，支持: kuaishou, deepseek
        """
        if platform not in PLATFORMS:
            raise ValueError(
                f"不支持的平台: {platform}\n"
                f"支持的平台: {list(PLATFORMS.keys())}"
            )
        self._platform_name = platform
        self._platform: PlatformBase = PLATFORMS[platform]()
    
    @property
    def platform(self) -> PlatformBase:
        """获取平台实例"""
        return self._platform
    
    def create_order(self, user_id: str, amount: float, **kwargs) -> OrderResult:
        """
        创建充值订单
        
        Args:
            user_id: 用户标识
                - kuaishou: 快手号
                - deepseek: 任意标识（可选）
            amount: 充值金额
                - kuaishou: 元（1元=10快币）
                - deepseek: 元
            **kwargs: 平台特定参数
                - deepseek: auth_token (必需)
        
        Returns:
            OrderResult: 订单结果
        """
        return self._platform.create_order(user_id, amount, **kwargs)
    
    def query_order(self, order_id: str) -> OrderResult:
        """查询订单状态"""
        return self._platform.query_order(order_id)
    
    def close(self):
        """关闭连接"""
        self._platform.close()
    
    @classmethod
    def register_platform(cls, name: str, platform_class):
        """注册新平台"""
        PLATFORMS[name] = platform_class
    
    @classmethod
    def list_platforms(cls) -> list:
        """列出所有支持的平台"""
        return list(PLATFORMS.keys())
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def quick_pay(platform: str, user_id: str, amount: float, **kwargs) -> OrderResult:
    """
    快速充值（便捷函数）
    
    Args:
        platform: 平台名称
        user_id: 用户标识
        amount: 金额
        **kwargs: 其他参数
    
    Returns:
        OrderResult: 订单结果
    """
    with TopUp(platform) as topup:
        return topup.create_order(user_id, amount, **kwargs)


__all__ = [
    "TopUp",
    "quick_pay",
    "PlatformBase",
    "OrderResult",
    "OrderStatus",
    "KuaishouPlatform",
    "DeepSeekPlatform",
    "PLATFORMS",
]
