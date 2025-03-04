from flask import Flask, render_template, request, Response
import json
import time
from openai import OpenAI
from tavily import TavilyClient
import re
import json
import requests
import urllib3
urllib3.disable_warnings()

search_time=10
client_search = TavilyClient("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") 
app = Flask(__name__)

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
            response_result_show = ""
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
                    response_result_show+=f'<br><a href="{url}" target="_blank">{i}.{title[:20]}</a><br>'
                    i+=1
            if len(response_result)==0:
                response_result="没有搜索到相关内容"
                response_result_show="没有搜索到相关内容"
            return response_result, response_result_show
            
        except requests.exceptions.SSLError as e:
            if attempt == max_retries - 1:  # 如果是最后一次尝试
                print(f"搜索失败: {str(e)}")
                return "搜索过程中遇到网络问题，请稍后重试", "搜索过程中遇到网络问题，请稍后重试"
            time.sleep(retry_delay)  # 等待一段时间后重试
            continue
        except Exception as e:
            print(f"未预期的错误: {str(e)}")
            return "搜索过程中遇到错误，请稍后重试", "搜索过程中遇到错误，请稍后重试"

client = OpenAI(
    base_url='https://api.siliconflow.cn/v1',
    api_key="sk-atyahnnvfgxogwfopseezxavxrvjqolunozksdlngdwlnzse"
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/stream', methods=['GET'])
def stream():
    query = request.args.get('query')
    def generate(query):
        last_update_time = time.time()
        
        def send_heartbeat():
            nonlocal last_update_time
            current_time = time.time()
            if current_time - last_update_time >= 15:  # 每15秒发送一次心跳
                last_update_time = current_time
                return True
            return False
            
        searched_query = []
        think_output = ""
        think_output_show = ""
        flag = True
        messages = []
        
        while flag:
            try:
                # 发送心跳包
                if send_heartbeat():
                    data = {
                        'answer1': f"{think_output_show}",
                        'answer2': "处理中，请稍候...",
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                
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
                
                think = ""
                if len(messages) == 0:
                    messages.append({
                        "content": system_prompt,
                        "role": "system"
                    })
                elif len(messages) == 1:
                    messages.append({
                        "content": think_output,
                        "role": "assistant"
                    })
                else:
                    messages[1]["content"] = think_output
                
                # 在调用API前添加延迟
                time.sleep(2)  # 添加2秒延迟

                # print("--------------------messages----------------------------")
                # print(messages)
                # print("------------------------------------------------")

                
                response = client.chat.completions.create(
                    model="Pro/deepseek-ai/DeepSeek-R1",
                    messages=messages,
                    stop=[")SEARCH"],
                    stream=True) # 启用流式输出)
                answer_dict={"reasoning_content":"","content":""}
                for chunk in response:
                    chunk_message = chunk.choices[0].delta.content
                    chunk_message_reasoning = chunk.choices[0].delta.reasoning_content
                    if chunk_message_reasoning:answer_dict["reasoning_content"]+=chunk_message_reasoning
                    if chunk_message:answer_dict["content"]+=chunk_message
                    # print(answer_dict)
                    think_output1=answer_dict['reasoning_content']
                    # print("--------------------reasoning_content----------------------------")
                    # print(think_output1)
                    # print("------------------------------------------------")
                    think_output2=answer_dict['content']
                    # print("--------------------content----------------------------")
                    # print(think_output2)
                    # print("------------------------------------------------")
                    think_output_temp=(think_output+think_output1+think_output2)
                    think_output_show_temp=(think_output_show+think_output1+think_output2).replace('\n', '<br>')
                    data = {
                        'answer1': f"{think_output_show_temp}",
                        'answer2': "等待思考完成后生成最终报告...",#f"{}"
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                think_output=think_output_temp
                think_output_show=think_output_show_temp
                think_output+=')'
                think_output_show+=')'
                data = {
                    'answer1': f"{think_output_show}",
                    'answer2': "等待思考完成后生成最终报告...",#f"{}"
                }
                yield f"data: {json.dumps(data)}\n\n"
                pattern = r'SEARCH\((.*?)\)'
                matches = re.findall(pattern, think_output)
                think_output+="SEARCH"
                think_output_show+="SEARCH"
                if matches:
                    print(matches)
                if len(matches)==len(searched_query) or len(searched_query)>=search_time:
                    flag=False
                else:
                    search_query=matches[-1]
                    searched_query.append(search_query)
                    
                    # 在调用搜索API前添加延迟
                    time.sleep(2)  # 添加2秒延迟
                    
                    search_result,search_result_show=tavily_search(search_query=search_query)
                    if search_result !="没有搜索到相关内容":                    
                        think_output+=f"\n\n搜索【{search_query}】结果如下：\n{search_result}\n搜索【{search_query}】结果如上。\n\n针对针对搜索【{search_query}】返回的结果进行分析:"
                        think_output_show+=f"<br><br>------------------------------------------------------------<br><br>搜索【{search_query}】结果如下：<br>{search_result_show}<br><br>-------------------------------------------------------------<br><br>"
                    else:
                        think_output+=f"\n\n搜索【{search_query}】结果如下：\n没有搜索到相关内容\n生成其他搜索请求:"
                        think_output_show+=f"<br><br>------------------------------------------------------------<br><br>搜索【{search_query}】结果如下：<br>{search_result_show}<br><br>-------------------------------------------------------------<br><br>"     
                data = {
                    'answer1': f"{think_output_show}",
                    'answer2': "等待思考完成后生成最终报告...",#f"{}"
                }
                yield f"data: {json.dumps(data)}\n\n"
                
                # 每次有新的搜索结果时更新last_update_time
                last_update_time = time.time()
                
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                data = {
                    'answer1': f"{think_output_show}<br>处理过程中发生错误，正在重试...",
                    'answer2': "处理过程中发生错误，正在重试...",
                }
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(2)  # 错误发生时等待一段时间
                continue
        
        
        
        
        
        think_output.replace(f'SEARCH({searched_query[-1]})SEARCH', '')
        think_output_show.replace('SEARCH({searched_query[-1]})SEARCH', '')
        data = {
                'answer1': f"{think_output_show}",
                'answer2': "等待思考完成后生成最终报告...",#f"{}"
            }

        yield f"data: {json.dumps(data)}\n\n"
        
        
        report_prompt = f'''
你是一个专业的调研报告撰写助手。
完成对问题[{query}]的深入研究，并提出可行的解决方案。
提供的资料和分析如下:

{think_output}

撰写一份调研报告。报告无需按固定格式组织，请根据内容灵活安排结构，要求尽可能全面，但要突出重点。
请确保格式整齐，语言清晰流畅，逻辑合理，既满足专业要求，也方便普通读者理解。开始撰写调研报告。

'''
        messages=[{"content": report_prompt,"role": "user"}]
        response = client.chat.completions.create(
            model="Pro/deepseek-ai/DeepSeek-R1",  # Qwen/Qwen2.5-72B-Instruct-128K  
            messages=messages,
            stream=True) 
        report=""
        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            if chunk_message:
                report += chunk_message.replace("\n", "<br>")
                data = {
                    'answer1': f"{think_output_show}",
                    'answer2': f"{report}"
                }  
                yield f"data: {json.dumps(data)}\n\n"
        
        # 报告生成完毕，发送最后一条消息并关闭连接
        data = {
            'answer1': f"{think_output_show}",
            'answer2': f"{report}",
            'complete': True  # 添加标记表示完成
        }
        yield f"data: {json.dumps(data)}\n\n"
        return  # 结束生成器函数

    return Response(generate(query), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
