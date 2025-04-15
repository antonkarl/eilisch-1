from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_message(role, content):
    return {"role": role, "content": content}

def get_response(messages):
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages
    )
    content = completion.choices[0].message.content
    return content