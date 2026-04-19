"""快手充值实现"""
from topup.core.base import PlatformBase, OrderResult, OrderStatus
from typing import Dict, Any


class KuaishouPlatform(PlatformBase):
    """快手充值平台"""
    
    name = "kuaishou"
    
    def _init_headers(self):
        """初始化请求头"""
        common_headers = {
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
        
        # API请求头
        self.api_headers = common_headers.copy()
        self.api_headers.update({
            "Content-Type": "application/json",
            "Origin": "https://pay.ssl.kuaishou.com",
            "Referer": "https://pay.ssl.kuaishou.com/pay",
        })
        
        # 支付请求头
        self.pay_headers = common_headers.copy()
        self.pay_headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://pay.ssl.kuaishou.com",
            "Referer": "https://pay.ssl.kuaishou.com/pay",
        })
        
        self.session.headers.update(self.api_headers)
        
        # 内部状态
        self._user_id: str = None
        self._merchant_id: str = None
        self._ks_order_id: str = None
    
    def _get_user_id(self, user_id_prefix: str) -> str:
        """获取快手内部用户ID"""
        url = "https://pay.ssl.kuaishou.com/rest/k/pay/userInfo"
        data = {"id": user_id_prefix}
        
        try:
            resp = self.session.post(url, json=data, timeout=15)
            if resp.status_code == 200:
                user_id = resp.json().get("userId")
                if user_id:
                    return user_id
            return OrderResult(
                success=False,
                message=f"获取用户ID失败: HTTP {resp.status_code}"
            )
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"请求异常: {str(e)}"
            )
    
    def _create_ks_order(self, user_id: str, amount: float) -> Dict[str, Any]:
        """创建快手充值订单"""
        url = "https://pay.ssl.kuaishou.com/rest/k/pay/kscoin/deposit/nlogin/kspay/cashier"
        
        # 快手: 1元 = 10快币
        ks_coin = int(amount * 10)
        fen = int(amount * 100)
        
        data = {
            "ksCoin": ks_coin,
            "fen": fen,
            "customize": True,
            "userId": user_id,
            "kpn": "KUAISHOU",
            "kpf": "PC_WEB",
            "source": "PC_WEB"
        }
        
        try:
            resp = self.session.post(url, json=data, timeout=15)
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "success": True,
                    "merchant_id": result.get("merchantId"),
                    "ks_order_id": result.get("ksOrderId"),
                    "raw": result
                }
            return {
                "success": False,
                "message": f"创建订单失败: HTTP {resp.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"请求异常: {str(e)}"
            }
    
    def _get_cashier_info(self, merchant_id: str, order_id: str) -> Dict[str, Any]:
        """获取收银台支付信息"""
        url = "https://pay.kuaishou.com/pay/order/pc/trade/cashier"
        data = {
            "merchant_id": merchant_id,
            "out_order_no": order_id,
            "js_sdk_version": "3.1.1"
        }
        
        # 临时切换请求头
        original_headers = self.session.headers.copy()
        self.session.headers.update(self.pay_headers)
        
        try:
            resp = self.session.post(url, data=data, timeout=15)
            if resp.status_code == 200:
                result = resp.json()
                result['support_bank_infos'] = None  # 清理冗余数据
                return {"success": True, "data": result}
            return {
                "success": False,
                "message": f"获取收银台失败: HTTP {resp.status_code}"
            }
        except Exception as e:
            return {"success": False, "message": f"请求异常: {str(e)}"}
        finally:
            self.session.headers.update(original_headers)
    
    def create_order(self, user_id: str, amount: float, **kwargs) -> OrderResult:
        """
        创建快手充值订单
        
        Args:
            user_id: 快手号/用户ID前缀
            amount: 充值金额（元）
        
        Returns:
            OrderResult: 包含支付二维码链接
        """
        # 1. 获取内部用户ID
        user_result = self._get_user_id(user_id)
        if isinstance(user_result, OrderResult):
            return user_result
        
        internal_user_id = user_result
        
        # 2. 创建订单
        order_result = self._create_ks_order(internal_user_id, amount)
        if not order_result.get("success"):
            return OrderResult(
                success=False,
                message=order_result.get("message", "创建订单失败")
            )
        
        merchant_id = order_result["merchant_id"]
        ks_order_id = order_result["ks_order_id"]
        
        # 保存内部状态
        self._user_id = internal_user_id
        self._merchant_id = merchant_id
        self._ks_order_id = ks_order_id
        
        # 3. 获取收银台信息
        cashier_result = self._get_cashier_info(merchant_id, ks_order_id)
        if not cashier_result.get("success"):
            return OrderResult(
                success=False,
                message=cashier_result.get("message", "获取收银台失败")
            )
        
        cashier_data = cashier_result["data"]
        
        return OrderResult(
            success=True,
            order_id=ks_order_id,
            qrcode_url=cashier_data.get("qrcode_url"),
            pay_url=cashier_data.get("pay_url"),
            amount=amount,
            status=OrderStatus.PENDING,
            raw_data=cashier_data
        )
    
    def query_order(self, order_id: str = None) -> OrderResult:
        """
        查询订单状态
        
        快手平台暂不支持主动查询，需通过回调或收银台状态判断
        """
        return OrderResult(
            success=False,
            order_id=order_id or self._ks_order_id,
            status=OrderStatus.UNKNOWN,
            message="快手平台暂不支持主动查询订单状态，请通过支付回调确认"
        )
