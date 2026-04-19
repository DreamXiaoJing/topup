"""微信小账本收入查询"""
from topup.core.base import PlatformBase, OrderResult, OrderStatus
from typing import List, Dict, Optional
import base64
import time


class WechatIncomePlatform(PlatformBase):
    """微信小账本收入查询"""

    name = "wechat_income"

    def _init_headers(self):
        """初始化请求头"""
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541113) XWEB/16815",
            'Content-Type': "application/json",
            'Sec-Fetch-Site': "cross-site",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Dest': "empty",
            'Referer': "https://servicewechat.com/wx28be8489b7a36aaa/1129/page-frame.html",
            'Accept-Language': "zh-CN,zh;q=0.9"
        }
        self.session.headers.update(headers)

        # 配置
        self.sid: str = None
        self.eqid: str = "TA821E0BADE5B8A38C1F1776593655542"
        self.v: str = "7.9.15"

    def set_sid(self, sid: str, eqid: str = None):
        """
        设置微信会话ID

        Args:
            sid: 微信小账本会话ID（从请求中获取）
            eqid: 追踪ID（可选）
        """
        self.sid = sid
        if eqid:
            self.eqid = eqid
        self.session.headers.update({
            'X-Track-Id': self.eqid,
            'X-Appid': "unknown",
            'X-Module-Name': "mmpaysmbpdreceiptassistmp",
            'X-Page': "pages/record3/record3",
        })

    @staticmethod
    def base64_decode(encoded_data: str) -> bytes:
        """Base64解码"""
        try:
            if isinstance(encoded_data, str):
                encoded_data = encoded_data.encode('utf-8')
            return base64.b64decode(encoded_data)
        except Exception as e:
            raise ValueError(f"Base64解码失败: {e}")

    def fetch_income_data(
        self,
        start_time: int = 0,
        end_time: int = None,
        page_size: int = 10,
        sort: str = "desc"
    ) -> Dict:
        """
        获取收入数据

        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳（默认当前）
            page_size: 每页数量
            sort: 排序方式 asc/desc

        Returns:
            dict: 原始响应数据
        """
        if not self.sid:
            raise ValueError("请先调用 set_sid() 设置会话ID")

        url = "https://smallbook.wxpapp.weixin.qq.com/qrappzd/user/incomelist2"
        params = {
            "sid": self.sid,
            "v": self.v
        }

        end_time = end_time or int(time.time())

        payload = {
            "v": self.v,
            "start_time": start_time,
            "end_time": end_time,
            "last_bill_id": None,
            "last_roll_id": None,
            "page_size": page_size,
            "sort": sort,
            "is_first": True,
            "last_create_time": 0,
            "last_id": "",
            "sid": self.sid
        }

        response = self.session.post(url, params=params, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_income_list(
        self,
        sid: str = None,
        start_time: int = 0,
        end_time: int = None,
        page_size: int = 10
    ) -> List[Dict]:
        """
        获取收入列表（已解码）

        Args:
            sid: 会话ID（可选，已设置则不需）
            start_time: 开始时间戳
            end_time: 结束时间戳
            page_size: 每页数量

        Returns:
            List[dict]: 收入记录列表
        """
        if sid:
            self.set_sid(sid)

        data = self.fetch_income_data(
            start_time=start_time,
            end_time=end_time,
            page_size=page_size
        )

        result = []
        for item in data.get("data", {}).get("data_list", []):
            # 解码付款人名称
            payer_name = item.get("payer_user_name", "")
            try:
                decoded_name = self.base64_decode(payer_name).decode('utf-8')
            except:
                decoded_name = payer_name

            result.append({
                "payer_user_name": decoded_name,
                "payer_remark": item.get("payer_remark"),
                "real_fee": item.get("real_fee"),  # 金额（分）
                "timestamp": item.get("timestamp"),
                "trans_id": item.get("trans_id"),
                "raw": item
            })

        return result

    def get_income_summary(
        self,
        sid: str = None,
        start_time: int = 0,
        end_time: int = None
    ) -> Dict:
        """
        获取收入统计

        Args:
            sid: 会话ID（可选，已设置则不需）
            start_time: 开始时间戳
            end_time: 结束时间戳

        Returns:
            dict: 统计信息
        """
        income_list = self.get_income_list(
            sid=sid,
            start_time=start_time,
            end_time=end_time,
            page_size=100  # 获取更多数据用于统计
        )

        total_fee = sum(item.get("real_fee", 0) for item in income_list)
        count = len(income_list)

        return {
            "total_count": count,
            "total_fee": total_fee,  # 分
            "total_fee_yuan": total_fee / 100,  # 元
            "start_time": start_time,
            "end_time": end_time or int(time.time()),
            "records": income_list
        }

    # 基类接口（微信小账本不支持创建订单）
    def create_order(self, user_id: str, amount: float, **kwargs) -> OrderResult:
        """微信小账本不支持创建订单"""
        return OrderResult(
            success=False,
            message="微信小账本平台仅支持收入查询，不支持创建订单"
        )

    def query_order(self, order_id: str) -> OrderResult:
        """请使用 get_income_list() 查询收入"""
        return OrderResult(
            success=False,
            message="请使用 get_income_list() 查询收入"
        )
