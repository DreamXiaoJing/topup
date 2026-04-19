"""DeepSeek充值实现"""
import time
import uuid
from typing import Dict, Any

from topup.core.base import PlatformBase, OrderResult, OrderStatus


class PaymentConfig:
    """支付配置"""
    default_amount: str = "1"
    currency: str = "CNY"
    primary_method: str = "CMB_UNIONPAY"
    fallback_method: str = "WECHAT"
    poll_interval_sec: float = 3.0
    max_poll_attempts: int = 40  # 约2分钟


class DeepSeekPlatform(PlatformBase):
    """DeepSeek充值平台"""
    
    name = "deepseek"
    BASE_URL = "https://platform.deepseek.com"
    
    def _init_headers(self):
        """初始化请求头 - 需要设置auth_token"""
        self.session.headers.update({
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://platform.deepseek.com",
            "referer": "https://platform.deepseek.com/top_up",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        })
        
        self._payment_order_id: str = None
        self._payment_url: str = None
        self._config = PaymentConfig()
    
    def set_auth_token(self, token: str):
        """设置认证Token"""
        self.session.headers.update({
            "authorization": f"Bearer {token}"
        })
    
    def _post(self, endpoint: str, json_data: dict) -> Dict[str, Any]:
        """发送POST请求"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            resp = self.session.post(url, json=json_data, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"code": -1, "msg": str(e), "error": True}
    
    def create_order(
        self, 
        user_id: str, 
        amount: float, 
        auth_token: str = None,
        payment_method: str = None,
        fallback_method: str = None,
        **kwargs
    ) -> OrderResult:
        """
        创建DeepSeek充值订单
        
        Args:
            user_id: 用户标识（用于记录，非必需）
            amount: 充值金额
            auth_token: Bearer Token（必需）
            payment_method: 主支付方式，默认 CMB_UNIONPAY
            fallback_method: 备用支付方式，默认 WECHAT
        
        Returns:
            OrderResult: 包含支付链接
        """
        # 设置token
        if auth_token:
            self.set_auth_token(auth_token)
        
        if "authorization" not in self.session.headers:
            return OrderResult(
                success=False,
                message="缺少认证Token，请通过auth_token参数传入"
            )
        
        request_id = str(uuid.uuid4())
        payload = {
            "order_info": {
                "payment_method_type": payment_method or self._config.primary_method,
                "fallback_method_type": fallback_method or self._config.fallback_method,
                "amount": str(int(amount)),
                "currency": self._config.currency,
                "request_id": request_id
            }
        }
        
        result = self._post("/api/v1/payments", payload)
        
        if result.get("code") != 0:
            return OrderResult(
                success=False,
                message=result.get("msg", "创建订单失败"),
                raw_data=result
            )
        
        biz = result.get("data", {}).get("biz_data", {})
        payment_order_id = biz.get("payment_order_id")
        payment_url = biz.get("url", "").strip()
        
        if not payment_order_id or not payment_url:
            return OrderResult(
                success=False,
                message="无法获取支付链接",
                raw_data=result
            )
        
        self._payment_order_id = payment_order_id
        self._payment_url = payment_url
        
        return OrderResult(
            success=True,
            order_id=payment_order_id,
            qrcode_url=payment_url,  # URL本身可作为二维码内容
            pay_url=payment_url,
            amount=amount,
            status=OrderStatus.PENDING,
            raw_data=result
        )
    
    def capture_payment(self, payment_order_id: str = None) -> Dict[str, Any]:
        """捕获支付状态"""
        order_id = payment_order_id or self._payment_order_id
        if not order_id:
            return {"code": -1, "msg": "缺少订单ID"}
        return self._post(f"/api/v1/payments/{order_id}/capture", {})
    
    def query_order(self, order_id: str = None) -> OrderResult:
        """
        查询订单状态
        
        通过capture接口获取状态
        """
        result = self.capture_payment(order_id)
        
        if result.get("code") != 0:
            return OrderResult(
                success=False,
                order_id=order_id or self._payment_order_id,
                status=OrderStatus.UNKNOWN,
                message=result.get("msg", "查询失败"),
                raw_data=result
            )
        
        status_str = result.get("data", {}).get("biz_data", {}).get("order", {}).get("status", "")
        
        status_map = {
            "SUCCESS": OrderStatus.SUCCESS,
            "PENDING": OrderStatus.PENDING,
            "FAILED": OrderStatus.FAILED,
            "CANCELLED": OrderStatus.CANCELLED,
            "EXPIRED": OrderStatus.EXPIRED,
        }
        
        status = status_map.get(status_str, OrderStatus.UNKNOWN)
        
        return OrderResult(
            success=status == OrderStatus.SUCCESS,
            order_id=order_id or self._payment_order_id,
            status=status,
            message=f"订单状态: {status_str}",
            raw_data=result
        )
    
    def poll_payment_status(
        self, 
        order_id: str = None,
        interval: float = None,
        max_attempts: int = None,
        callback=None
    ) -> OrderResult:
        """
        轮询支付状态
        
        Args:
            order_id: 订单ID
            interval: 轮询间隔（秒）
            max_attempts: 最大尝试次数
            callback: 状态变化回调函数
        
        Returns:
            OrderResult: 最终支付结果
        """
        interval = interval or self._config.poll_interval_sec
        max_attempts = max_attempts or self._config.max_poll_attempts
        
        for i in range(max_attempts):
            result = self.query_order(order_id)
            
            if callback:
                callback(i + 1, max_attempts, result.status)
            
            if result.status == OrderStatus.SUCCESS:
                return result
            
            if result.status in (OrderStatus.FAILED, OrderStatus.CANCELLED, OrderStatus.EXPIRED):
                return result
            
            time.sleep(interval)
        
        return OrderResult(
            success=False,
            order_id=order_id or self._payment_order_id,
            status=OrderStatus.UNKNOWN,
            message="轮询超时，未检测到支付完成"
        )

