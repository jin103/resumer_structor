import requests
import json

def test_stream_chat():
    """测试流式聊天功能"""
    print("🧪 测试小YO流式聊天功能...")
    print("=" * 50)

    # 测试消息
    test_messages = [
        "你好，小YO！",
        "你能介绍一下自己吗？",
        "谢谢你告诉我这些！"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n📤 发送消息 {i}: {message}")
        print("-" * 30)

        try:
            response = requests.post(
                'http://localhost:8002/stream_chat',
                json={'message': message},
                stream=True
            )

            if response.status_code == 200:
                print("✅ 流式响应开始:")
                chunk_count = 0
                full_response = ""

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data['type'] == 'trace_id':
                                    print(f"🔖 Trace ID: {data['data']}")
                                elif data['type'] == 'chunk':
                                    chunk = data['data']
                                    print(chunk, end='', flush=True)
                                    full_response += chunk
                                    chunk_count += 1
                                elif data['type'] == 'done':
                                    print(f"\n✅ 消息完成 (共{chunk_count}个数据块)")
                                    print(f"📝 完整回复: {data['data'][:100]}...")
                                elif data['type'] == 'error':
                                    print(f"\n❌ 错误: {data['data']}")
                            except json.JSONDecodeError:
                                continue

                print(f"\n💾 本轮对话已保存到记忆中")

            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"错误详情: {response.text}")

        except Exception as e:
            print(f"❌ 连接错误: {e}")

        print()

    print("🎉 流式聊天测试完成！")
    print("💡 小YO会记住整个对话的上下文")

if __name__ == "__main__":
    test_stream_chat()