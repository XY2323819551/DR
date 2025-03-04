# -*- coding: utf-8 -*-

def format_chat_template(messages, add_generation_prompt=False, bos_token=""):
    """
    将聊天消息格式化为特定格式的字符串，与原始Jinja模板逻辑完全一致
    
    参数:
        messages: 消息列表，每个消息是一个字典，包含'role'和'content'键
        add_generation_prompt: 是否添加生成提示，默认为False
        bos_token: 开始标记，默认为空字符串
    
    返回:
        格式化后的字符串
    """
    # 定义特殊标记 - 使用与原始模板完全一致的标记
    USER_TAG = "<｜User｜>"
    ASSISTANT_TAG = "<｜Assistant｜>"
    TOOL_CALLS_BEGIN = "<｜tool▁calls▁begin｜>"
    TOOL_CALLS_END = "<｜tool▁calls▁end｜>"
    TOOL_CALL_BEGIN = "<｜tool▁call▁begin｜>"
    TOOL_CALL_END = "<｜tool▁call▁end｜>"
    TOOL_SEP = "<｜tool▁sep｜>"
    TOOL_OUTPUTS_BEGIN = "<｜tool▁outputs▁begin｜>"
    TOOL_OUTPUTS_END = "<｜tool▁outputs▁end｜>"
    TOOL_OUTPUT_BEGIN = "<｜tool▁output▁begin｜>"
    TOOL_OUTPUT_END = "<｜tool▁output▁end｜>"
    END_OF_SENTENCE = "<｜end▁of▁sentence｜>"
    THINK_TAG = "<think>"
    
    # 初始化命名空间变量
    is_first = False
    is_tool = False
    is_output_first = True
    system_prompt = ''
    
    # 处理系统消息
    for message in messages:
        if message.get('role') == 'system':
            system_prompt = message.get('content', '')
    
    # 初始化结果字符串
    result = bos_token + system_prompt
    
    # 处理所有消息
    for message in messages:
        role = message.get('role', '')
        content = message.get('content')
        
        if role == 'user':
            is_tool = False
            result += USER_TAG + content
        
        elif role == 'assistant':
            if content is None and 'tool_calls' in message:
                is_tool = False
                tool_calls = message.get('tool_calls', [])
                
                for tool in tool_calls:
                    if not is_first:
                        result += (ASSISTANT_TAG + TOOL_CALLS_BEGIN + TOOL_CALL_BEGIN + 
                                tool.get('type', '') + TOOL_SEP + tool['function']['name'] + 
                                '\n```json\n' + tool['function']['arguments'] + '\n```' + 
                                TOOL_CALL_END)
                        is_first = True
                    else:
                        result += ('\n' + TOOL_CALL_BEGIN + tool.get('type', '') + 
                                TOOL_SEP + tool['function']['name'] + 
                                '\n```json\n' + tool['function']['arguments'] + '\n```' + 
                                TOOL_CALL_END)
                result += TOOL_CALLS_END + END_OF_SENTENCE
            
            elif content is not None:
                if is_tool:
                    result += TOOL_OUTPUTS_END + content + END_OF_SENTENCE
                    is_tool = False
                else:
                    if '</think>' in content:
                        content = content.split('</think>')[-1]
                    result += ASSISTANT_TAG + content + END_OF_SENTENCE
        
        elif role == 'tool':
            is_tool = True
            if is_output_first:
                result += TOOL_OUTPUTS_BEGIN + TOOL_OUTPUT_BEGIN + content + TOOL_OUTPUT_END
                is_output_first = False
            else:
                result += '\n' + TOOL_OUTPUT_BEGIN + content + TOOL_OUTPUT_END
    
    # 处理结尾
    if is_tool:
        result += TOOL_OUTPUTS_END
    
    if add_generation_prompt and not is_tool:
        result += ASSISTANT_TAG + THINK_TAG + '\n'
    
    return result


# 测试代码
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
    print(formatted_result)

    