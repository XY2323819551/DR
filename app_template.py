import re
import json
import time
import urllib3
import requests
from openai import OpenAI
from tavily import TavilyClient
urllib3.disable_warnings()


USER_TAG = "<｜User｜>"
ASSISTANT_TAG = "<｜Assistant｜>"

TOOL_CALLS_BEGIN = "<｜tool calls begin｜>"
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

search_time = 2
client_search = TavilyClient("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") 

client = OpenAI(
    base_url='https://api.siliconflow.cn/v1',
    api_key="sk-atyahnnvfgxogwfopseezxavxrvjqolunozksdlngdwlnzse"
)


tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "搜索互联网上的信息",
            "arguments": '{"search_query": "要搜索的查询内容"}'
        }
    }
]


def chinese_ratio(text):
    if not isinstance(text, str):
        return 0
    # 统计中文字符数量
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    # 计算总字符数（不包括空格）
    total_chars = len(''.join(text.split()))
    # 计算比例
    ratio = chinese_chars / total_chars if total_chars > 0 else 0
    return ratio

def tavily_search(search_query):
    max_retries = 3
    retry_delay = 2  # 秒
    
    for attempt in range(max_retries):
        try:
            response = client_search.search(query=search_query, include_raw_content=True, verify=False)
            # 如果成功就继续执行后面的代码
            response_result = ""
            file_name=re.sub(r'[^\w\.\u4e00-\u9fff]+', '_', search_query).strip()
            with open('search_query/'+file_name+'.json', 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=4)
            i=1
            for result in response['results']:
                if chinese_ratio(result['content'])>0.8:
                    title=result['title']
                    url=result['url']
                    content=result['content']
                    if len(content)>10000:
                        content=content[:5000]
                    if len(content)<200 and chinese_ratio(result['raw_content'])>0.8:
                        content=result['raw_content'][:2000]
                    response_result+=f'\n{i}.title:{title}\nurl:{url}\ncontent:{content}\n'
                    i+=1
            if len(response_result)==0:
                response_result="没有搜索到相关内容"
            return response_result
            
        except requests.exceptions.SSLError as e:
            if attempt == max_retries - 1:  # 如果是最后一次尝试
                print(f"搜索失败: {str(e)}")
                return "搜索过程中遇到网络问题，请稍后重试"
            time.sleep(retry_delay)  # 等待一段时间后重试
            continue
        except Exception as e:
            print(f"未预期的错误: {str(e)}")
            return "搜索过程中遇到错误，请稍后重试"

def generate_research_report(query):
    """
    生成调研报告的主函数
    
    Args:
        query: 调研问题
        
    Returns:
        dict: 包含思考过程和最终报告的字典
    """
    print("\n" + "="*50)
    print(f"开始调研问题: {query}")
    print("="*50 + "\n")
    
    searched_query = []
    think_output = ""
    flag = True
    messages = []
    
    while flag:
        try:
            time.sleep(2)  # API调用延迟
            
            searched_query_str = f"已经搜索的话题：{searched_query}，已经搜索了{len(searched_query)}次" if len(searched_query) > 0 else ""
            system_prompt = f'''
            # 调研大师
            针对"{query}"进行调研
            **核心目标**：模拟专业调研员的完整决策流程，自主完成任意领域的深度调研
            ##注意事项：
            生成内容时请慎重，忽略你已有的过时的数据等信息，
            信息来源主要以检索内容为主。
            现在时间是2025年2月！
            你的知识只截止到2023年,不要编造2023年之后的内容！
            ## 执行流程
            1. [问题分析]
            问题分析，仔细分析调研问题，从多个角度多个层面反思分析。
            2. [持续搜索分析资料]
            格式为:SEARCH(资料)SEARCH
            至少查找3次资料，最多查找5次，不要搜索之前搜索过的资料
            每轮搜索一条信息。
            搜索的结果是若干个网站的资料，要分析资料从中找到对调研问题有帮助的内容。
            不要持续搜索同一话题的重复内容，
            {searched_query_str}
            搜索的资料不要陷入某个子问题，要尽可能全面。
            当资料不够时,只需要分析出还需要什么资料,格式为 SEARCH(资料)SEARCH,至少进行3轮搜索和分析。
            请注意格式为：SEARCH(资料)SEARCH
            资料前后有括号和SEARCH
            获取到搜索结果后要进行分析。
            直到达到五次限制或者收集资料完整。
            '''
            
            if len(messages) == 0:
                messages.append({
                    "content": system_prompt,
                    "role": "user"
                })
                print("初始化系统提示...\n")
            elif len(messages) == 1:
                messages.append({
                    "content": think_output,
                    "role": "assistant"
                })
            else:
                messages[1]["content"] = think_output
            
            # 在调用API前添加延迟
            time.sleep(2)  # 添加2秒延迟
            print("-"*50)
            print(f"第 {len(searched_query) + 1} 轮思考中...")
            
            response = client.chat.completions.create(
                model="Pro/deepseek-ai/DeepSeek-R1",
                messages=messages,
                stop=[")SEARCH"],
                stream=True) # 启用流式输出)
            answer_dict={"reasoning_content":"","content":""}
            
            for chunk in response:
                chunk_message = chunk.choices[0].delta.content
                chunk_message_reasoning = chunk.choices[0].delta.reasoning_content
                if chunk_message_reasoning:
                    answer_dict["reasoning_content"]+=chunk_message_reasoning
                if chunk_message:
                    answer_dict["content"]+=chunk_message
                    # 实时打印内容
                    print(chunk_message, end="", flush=True)
                
                think_output1=answer_dict['reasoning_content']
                think_output2=answer_dict['content']
                think_output_temp=(think_output+think_output1+think_output2)
            
            print("\n")  # 打印一个换行，使输出更清晰
            
            think_output=think_output_temp
            think_output+=')'
            print("===========think_output==============")
            print(think_output)
            print("\n\n")
            
            pattern = r'SEARCH\((.*?)\)'
            matches = re.findall(pattern, think_output)
            think_output+="SEARCH"
            
            if matches:
                print(f"\n识别到搜索请求: {matches[-1]}")
            
            if len(matches)==len(searched_query) or len(searched_query)>=search_time:
                print("\n已达到搜索次数上限或没有新的搜索请求，结束搜索过程")
                flag=False
            else:
                search_query=matches[-1]
                searched_query.append(search_query)
                
                print(f"\n开始搜索: {search_query}")
                print("-"*50)
                
                # 在调用搜索API前添加延迟
                time.sleep(2)  # 添加2秒延迟
                
                # 添加工具调用的特殊标记
                tool_call_text = f"{TOOL_CALLS_BEGIN}{TOOL_CALL_BEGIN}function{TOOL_SEP}tavily_search\n```json\n{{\"search_query\": \"{search_query}\"}}\n```{TOOL_CALL_END}{TOOL_CALLS_END}"
                
                # 将工具调用添加到think_output
                think_output += tool_call_text
                
                search_result=tavily_search(search_query=search_query)
                
                # 添加工具输出的特殊标记
                tool_output_text = f"{TOOL_OUTPUTS_BEGIN}{TOOL_OUTPUT_BEGIN}"
                
                if search_result !="没有搜索到相关内容":
                    print(f"搜索成功，获取到相关内容")
                    tool_output_text += search_result
                    tool_output_text += f"{TOOL_OUTPUT_END}{TOOL_OUTPUTS_END}"
                    
                    # 将工具输出添加到think_output
                    think_output += tool_output_text
                    
                    # 添加分析提示
                    think_output += f"\n\n针对搜索【{search_query}】返回的结果进行分析:"
                else:
                    print(f"搜索未找到相关内容")
                    tool_output_text += "没有搜索到相关内容"
                    tool_output_text += f"{TOOL_OUTPUT_END}{TOOL_OUTPUTS_END}"
                    
                    # 将工具输出添加到think_output
                    think_output += tool_output_text
                    
                    # 添加生成其他搜索请求的提示
                    think_output += f"\n\n生成其他搜索请求:"
                
        except Exception as e:
            print(f"\n错误: {str(e)}")
            print("等待2秒后重试...")
            time.sleep(2)  # 错误发生时等待一段时间
            continue
    
    # 移除最后一个SEARCH标记
    think_output = think_output.replace(f'SEARCH({searched_query[-1]})SEARCH', '')
    
    print("\n" + "="*50)
    print("思考过程完成，开始生成最终报告")
    print("="*50 + "\n")
    print(f"think_output:{think_output}")

    
    report_prompt = f'''
你是一个专业的调研报告撰写助手。
完成对问题[{query}]的深入研究，并提出可行的解决方案。
提供的资料和分析如下:

{think_output}

撰写一份调研报告。报告无需按固定格式组织，请根据内容灵活安排结构，要求尽可能全面，但要突出重点。
请确保格式整齐，语言清晰流畅，逻辑合理，既满足专业要求，也方便普通读者理解。开始撰写调研报告。
'''
    messages=[{"content": report_prompt,"role": "user"}]
    
    # 使用流式调用生成报告
    report = ""
    response = client.chat.completions.create(
        model="Pro/deepseek-ai/DeepSeek-R1",
        messages=messages,
        stream=True)  # 启用流式输出
    
    # 创建一个结果字典，用于存储思考过程和报告
    result = {
        "thinking_process": think_output,
        "final_report": ""
    }
    
    print("生成最终报告中...\n")
    print("-"*50 + "\n")
    
    # 流式处理报告生成
    for chunk in response:
        chunk_message = chunk.choices[0].delta.content
        if chunk_message:
            report += chunk_message
            # 实时更新结果字典中的报告内容
            result["final_report"] = report
            # 实时打印报告内容
            print(chunk_message, end="", flush=True)
    
    print("\n\n" + "="*50)
    print("报告生成完成!")
    print("="*50)
    return result

if __name__ == '__main__':
    # 示例使用
    query = "中国新能源汽车发展现状"
    result = generate_research_report(query)
    result = generate_research_report(query)
    print("思考过程:")
    print(result["thinking_process"])
    print("\n\n最终报告:")
    
    print(result["final_report"])
