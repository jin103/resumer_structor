import requests

# API基础URL
BASE_URL = "http://localhost:8000"

def test_api():
    """测试API功能"""
    print("🧪 开始测试LangChain DeepSeek API...")

    # 测试健康检查
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    # 测试聊天功能
    test_messages = [
        "你好，请介绍一下自己",
        "你还记得我刚才说什么吗？",
        "请用一句话总结我们的对话"
    ]

    print("\n💬 开始对话测试...")
    for i, message in enumerate(test_messages, 1):
        try:
            print(f"\n--- 测试 {i} ---")
            print(f"用户: {message}")

            response = requests.post(
                f"{BASE_URL}/chat",
                json={"message": message},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print("✅ 响应成功")
                print(f"   Trace ID: {data['trace_id']}")
                print(f"   AI回复: {data['response'][:100]}...")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"   错误: {response.text}")

        except requests.exceptions.Timeout:
            print("⏰ 请求超时")
        except Exception as e:
            print(f"❌ 错误: {e}")

    print("\n🎉 测试完成！")

if __name__ == "__main__":
    test_api()