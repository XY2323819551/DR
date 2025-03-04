from openai import AsyncOpenAI
import asyncio  

# 非流式，调用siliconflow api
async def mf_chat(messages):
    client = AsyncOpenAI(
        base_url='https://api.siliconflow.cn/v1',
        api_key="sk-atyahnnvfgxogwfopseezxavxrvjqolunozksdlngdwlnzse"
    )    
    response = await client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        messages=messages
    )
    return response.choices[0].message.content

# 流式，调用siliconflow api
async def mf_chat_stream(messages):
    client = AsyncOpenAI(
        base_url='https://api.siliconflow.cn/v1',
        api_key="sk-atyahnnvfgxogwfopseezxavxrvjqolunozksdlngdwlnzse"
    )    
    answer_dict = {"reasoning_content": "", "content": ""}
    response = await client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        messages=messages,
        stream=True  # 启用流式输出
    )

    async for chunk in response:
        chunk_message = chunk.choices[0].delta.content or ""
        chunk_message_reasoning = chunk.choices[0].delta.reasoning_content or ""
        answer_dict["reasoning_content"] += chunk_message_reasoning
        answer_dict["content"] += chunk_message
        yield answer_dict

# 测试函数
async def test_mf_chat():
    messages = [
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
    response = await mf_chat(messages)
    print("非流式回复:", response)

async def test_mf_chat_stream():
    messages = [
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
    async for chunk in mf_chat_stream(messages):
        print("流式回复片段:", chunk)

async def test_concurrent_stream():
    messages1 = [{"role": "user", "content": "你是谁？"}]
    messages2 = [{"role": "user", "content": "请介绍一下自己"}]
    messages3 = [{"role": "user", "content": "你能做什么？"}]
    
    async def process_stream(messages, name):
        print(f"\n开始处理 {name}:")
        async for chunk in mf_chat_stream(messages):
            print(f"{name} 回复片段:", chunk)
    
    # 并发执行三个流式调用
    await asyncio.gather(
        process_stream(messages1, "res1"),
        process_stream(messages2, "res2"),
        process_stream(messages3, "res3")
    )

async def main():
    print("开始并发流式调用测试:")
    await test_concurrent_stream()

if __name__ == "__main__":
    asyncio.run(main())
    