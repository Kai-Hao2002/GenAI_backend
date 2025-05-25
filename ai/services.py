# import openai

# def call_openai(prompt):
#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "你是一個活動企劃助手"},
#             {"role": "user", "content": prompt}
#         ]
#     )
#     return response['choices'][0]['message']['content']
