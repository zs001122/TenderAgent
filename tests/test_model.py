import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from dataclasses import dataclass

# ===================== 配置项 =====================
OPENROUTER_API_KEY = "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"  # 替换为实际的API密钥
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "stepfun/step-3.5-flash:free"
CONCURRENT_REQUESTS = 5  # 并发请求数
TOTAL_REQUESTS = 25       # 总请求数
TIMEOUT = 30              # 请求超时时间（秒）
TOKEN_RATIO = 0.75        # 中文字符与Token的换算比例（1个中文字≈0.75Token）
# ==================================================

@dataclass
class RequestResult:
    """存储单个请求的结果"""
    success: bool
    response_time: float  # 响应时间（秒）
    total_tokens: int     # 总输出Token数（估算）
    token_speed: float    # Token输出速度（Token/秒）
    error: str = ""

def count_tokens(text: str) -> int:
    """
    估算文本的Token数量
    规则：中文字符 × 0.75，英文字符/数字/符号 × 1
    """
    if not text:
        return 0
    
    token_count = 0
    for char in text:
        # 判断是否为中文字符
        if '\u4e00' <= char <= '\u9fff':
            token_count += TOKEN_RATIO
        else:
            token_count += 1
    return int(token_count)

def make_api_call():
    """执行单次API调用（包含两次请求），并计算Token相关指标"""
    start_time = time.time()
    total_output_text = ""  # 存储两次请求的所有输出内容
    
    try:
        # 第一次API调用
        first_response = requests.post(
            url=API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": "单词 'strawberry' 中有多少个字母 r？"
                    }
                ],
                "reasoning": {"enabled": True}
            }),
            timeout=TIMEOUT
        )
        first_response.raise_for_status()  # 抛出HTTP错误
        
        # 提取第一次响应数据
        first_data = first_response.json()
        assistant_msg = first_data['choices'][0]['message']
        total_output_text += assistant_msg.get('content', '')  # 累加输出内容
        
        # 构造对话历史
        messages = [
            {"role": "user", "content": "单词 'strawberry' 中有多少个字母 r？"},
            {
                "role": "assistant",
                "content": assistant_msg.get('content'),
                "reasoning_details": assistant_msg.get('reasoning_details')
            },
            {"role": "user", "content": "你确定吗？再仔细想想。"}
        ]
        
        # 第二次API调用
        second_response = requests.post(
            url=API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL,
                "messages": messages,
                "reasoning": {"enabled": True}
            }),
            timeout=TIMEOUT
        )
        second_response.raise_for_status()
        
        # 提取第二次响应数据并累加输出内容
        second_data = second_response.json()
        total_output_text += second_data['choices'][0]['message'].get('content', '')
        
        # 计算核心指标
        response_time = time.time() - start_time
        total_tokens = count_tokens(total_output_text)
        token_speed = total_tokens / response_time if response_time > 0 else 0
        
        return RequestResult(
            success=True,
            response_time=response_time,
            total_tokens=total_tokens,
            token_speed=token_speed
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        return RequestResult(
            success=False,
            response_time=response_time,
            total_tokens=0,
            token_speed=0,
            error=str(e)
        )

def test_throughput():
    """测试并发吞吐量，新增Token输出速度统计"""
    print(f"开始测试 OpenRouter API 并发吞吐量")
    print(f"配置：并发数={CONCURRENT_REQUESTS}, 总请求数={TOTAL_REQUESTS}, Token换算比例={TOKEN_RATIO}")
    print("-" * 60)
    
    results = []
    start_total_time = time.time()
    
    # 使用线程池执行并发请求
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        # 提交所有任务
        futures = [executor.submit(make_api_call) for _ in range(TOTAL_REQUESTS)]
        
        # 实时输出进度
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            
            # 每完成10个请求输出一次进度
            if i % 10 == 0 or i == TOTAL_REQUESTS:
                success_count = sum(1 for r in results if r.success)
                fail_count = len(results) - success_count
                print(f"进度: {i}/{TOTAL_REQUESTS} | 成功: {success_count} | 失败: {fail_count}")
    
    # 计算核心统计数据
    total_time = time.time() - start_total_time
    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count
    success_rate = (success_count / TOTAL_REQUESTS) * 100 if TOTAL_REQUESTS > 0 else 0
    
    # 提取成功请求的指标
    success_responses = [r for r in results if r.success]
    avg_response_time = statistics.mean([r.response_time for r in success_responses]) if success_responses else 0
    min_response_time = min([r.response_time for r in success_responses]) if success_responses else 0
    max_response_time = max([r.response_time for r in success_responses]) if success_responses else 0
    total_tokens_all = sum([r.total_tokens for r in success_responses]) if success_responses else 0
    avg_token_speed = statistics.mean([r.token_speed for r in success_responses]) if success_responses else 0
    max_token_speed = max([r.token_speed for r in success_responses]) if success_responses else 0
    
    # 吞吐量（每秒成功处理的请求数）
    throughput = success_count / total_time if total_time > 0 else 0
    # 总Token吞吐量（每秒处理的Token数）
    total_token_throughput = total_tokens_all / total_time if total_time > 0 else 0
    
    # 输出测试结果
    print("-" * 60)
    print("测试结果汇总:")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"总请求数: {TOTAL_REQUESTS} | 成功: {success_count} | 失败: {fail_count}")
    print(f"成功率: {success_rate:.2f}%")
    print("=" * 60)
    print("响应时间指标:")
    print(f"平均响应时间: {avg_response_time:.2f} 秒")
    print(f"最小响应时间: {min_response_time:.2f} 秒")
    print(f"最大响应时间: {max_response_time:.2f} 秒")
    print("=" * 60)
    print("吞吐量指标:")
    print(f"请求吞吐量: {throughput:.2f} 请求/秒")
    print(f"总Token吞吐量: {total_token_throughput:.2f} Token/秒")
    print("=" * 60)
    print("Token输出速度指标:")
    print(f"平均Token输出速度: {avg_token_speed:.2f} Token/秒")
    print(f"最大Token输出速度: {max_token_speed:.2f} Token/秒")
    print(f"成功请求总输出Token数: {total_tokens_all}")
    
    # 输出错误详情（如果有）
    if fail_count > 0:
        print("\n错误详情（前5条）:")
        errors = [r.error for r in results if not r.success]
        for i, error in enumerate(errors[:5], 1):
            print(f"  错误 {i}: {error[:150]}...")  # 截断过长的错误信息

if __name__ == "__main__":
    # 设置requests重试次数，提升稳定性
    requests.adapters.DEFAULT_RETRIES = 2
    
    # 执行测试
    test_throughput()