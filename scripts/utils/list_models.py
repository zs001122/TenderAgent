from openai import OpenAI

client = OpenAI(
    api_key="sk-claDrMA1TOAB0p5UGXyezm05S3qNhHXdB4OUzhqO7r5hh0X8",
    base_url="https://apie.zhisuaninfo.com/v1"
)

try:
    print("Listing models...")
    models = client.models.list()
    for model in models.data:
        if "qwen" in model.id.lower():
            print(model.id)
except Exception as e:
    print(f"Error: {e}")
