import os
from groq import Groq
import json
client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "how are you",
        } 
    ],
    model="llama3-8b-8192",
)
data = json.dumps(chat_completion.choices[0].message.content)
print(data)
print(chat_completion.choices[0].message.content)