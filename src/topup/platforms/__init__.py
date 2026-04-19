"""平台注册表"""
from topup.platforms.kuaishou import KuaishouPlatform
from topup.platforms.deepseek import DeepSeekPlatform
from topup.platforms.wechat import WechatIncomePlatform

# 平台注册表
PLATFORMS = {
    "kuaishou": KuaishouPlatform,
    "deepseek": DeepSeekPlatform,
    "wechat_income": WechatIncomePlatform,
}

__all__ = ["PLATFORMS", "KuaishouPlatform", "DeepSeekPlatform", "WechatIncomePlatform"]
