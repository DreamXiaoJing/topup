"""使用示例"""
from topup import quick_pay, TopUp


def example_kuaishou():
    """快手充值示例"""
    print("=== 快手充值示例 ===")

    # 方式1: 完整流程
    with TopUp("kuaishou") as topup:
        result = topup.create_order(
            user_id="快手号",  # 替换为实际快手号
            amount=10  # 10元 = 100快币
        )

        if result.success:
            print(f"订单ID: {result.order_id}")
            print(f"支付二维码: {result.qrcode_url}")
        else:
            print(f"创建订单失败: {result.message}")

    # 方式2: 快捷函数
    result = quick_pay("kuaishou", "快手号", 10)
    print(f"支付链接: {result.pay_url}")


def example_deepseek():
    """DeepSeek充值示例"""
    print("=== DeepSeek充值示例 ===")

    token = "your_bearer_token"  # 替换为实际token

    with TopUp("deepseek") as topup:
        # 创建订单
        result = topup.create_order(
            user_id="user@example.com",  # 可选
            amount=10,  # 10元
            auth_token=token
        )

        if result.success:
            print(f"订单ID: {result.order_id}")
            print(f"支付链接: {result.pay_url}")

            # 生成二维码图片
            qr_path = topup.platform.generate_qrcode("payment_qr.png")
            print(f"二维码已保存: {qr_path}")

            # 轮询支付状态
            print("等待支付...")
            final_result = topup.platform.poll_payment_status(
                callback=lambda i, total, status: print(f"[{i}/{total}] 状态: {status.value}")
            )
            print(f"支付结果: {final_result.status.value}")
        else:
            print(f"创建订单失败: {result.message}")


def example_wechat_income():
    """微信小账本收入查询示例"""
    print("=== 微信小账本收入查询示例 ===")

    # 需要先获取sid（从微信小程序请求中抓取）
    sid = "替换为实际sid"  # 替换为实际sid

    with TopUp("wechat_income") as topup:
        # 设置会话ID
        topup.platform.set_sid(sid)

        # 获取收入列表
        income_list = topup.platform.get_income_list()

        print(f"共 {len(income_list)} 条收入记录:")
        for item in income_list:
            print(item)





def example_batch():
    """批量充值示例"""
    print("=== 批量充值示例 ===")

    platforms = TopUp.list_platforms()
    print(f"支持的平台: {platforms}")

    # 为多个平台创建订单
    orders = []
    for platform in ["kuaishou", "deepseek"]:
        try:
            topup = TopUp(platform)
            # 这里需要传入正确的参数
            # orders.append(topup.create_order(...))
            print(f"{platform}: 就绪")
        except Exception as e:
            print(f"{platform}: 错误 - {e}")


if __name__ == "__main__":
    # example_kuaishou()
    # example_deepseek()
    # asyncio.run(example_wechat_income())
    example_wechat_income()
