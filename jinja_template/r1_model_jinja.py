# -*- coding: utf-8 -*-
from transformers import AutoTokenizer
import jinja2
import json
import re

def format_chat_template(messages, add_generation_prompt=True):
    """
    使用DeepSeek-R1模型的chat_template将消息格式化为模型输入
    
    参数:
        messages: 消息列表，每个消息是一个字典包含role和content
        add_generation_prompt: 是否添加生成提示符
    
    返回:
        格式化后的字符串
    """
    # 加载DeepSeek-R1模型的tokenizer
    tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-R1")
    
    # 获取模型的chat_template
    chat_template = tokenizer.chat_template
    print("Chat template:", chat_template)
    
    # 创建jinja2环境并加载模板
    env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        autoescape=False,
        keep_trailing_newline=True
    )
    
    # 定义strip_count过滤器
    def strip_count(s):
        count = 0
        for char in s:
            if char == " ":
                count += 1
            else:
                break
        return count

    env.filters["strip_count"] = strip_count
    
    # 定义json_encode过滤器
    def json_encode(obj):
        return json.dumps(obj, ensure_ascii=False)
    
    env.filters["json_encode"] = json_encode
    
    # 加载模板
    template = env.from_string(chat_template)
    
    # 处理带有tool_calls的消息
    processed_messages = []
    for msg in messages:
        processed_msg = msg.copy()
        
        # 确保每个消息都有content字段
        if "content" not in processed_msg:
            processed_msg["content"] = ""
            
        # 处理工具调用消息，添加content字段如果没有
        if processed_msg.get("role") == "assistant" and "tool_calls" in processed_msg and not processed_msg.get("content"):
            processed_msg["content"] = ""
            
        processed_messages.append(processed_msg)
    
    # 打印处理后的消息进行调试
    print("Processed messages:", json.dumps(processed_messages, ensure_ascii=False, indent=2))
    
    # 渲染模板
    formatted_prompt = template.render(
        messages=processed_messages,
        add_generation_prompt=add_generation_prompt
    )
    
    return formatted_prompt

if __name__ == "__main__":
    # 测试消息
    test_messages = [
        {"role": "system", "content": "你是一个有用的AI助手"},
        {"role": "user", "content": "你能帮我查询天气吗？"},
        {"role": "assistant", "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "北京", "date": "today"}'
                }
            }
        ]},
        {"role": "tool", "content": "北京今天晴朗，温度25°C"},
        {"role": "assistant", "content": "根据查询，北京今天天气晴朗，温度25°C。"}
    ]
    
    # 格式化并打印结果
    formatted_result = format_chat_template(test_messages, add_generation_prompt=True)
    print("\n\n\n")
    print(formatted_result)

   