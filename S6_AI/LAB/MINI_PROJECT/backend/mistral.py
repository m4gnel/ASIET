from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234",
    api_key="mistral-7b-instruct-v0.2"
)

def ask_mistral(prompt):
    response = client.chat.completions.create(
        model="mistral-7b-instruct-v0.2",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content