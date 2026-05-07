import ollama
import json

# 가상의 결과 데이터, tensorflow로 가공된 데이터.
raw_ocr_results = [
    {"box": [10, 20, 100, 50], "text": "가   격"},
    {"box": [110, 25, 200, 55], "text": "4 , 50 0 원"},
    {"box": [10, 80, 150, 110], "text": "일 자: 2026.05.07"}
]

def refine_with_llm(ocr_data):
    prompt=f"""
    아래는 OCR 모델이 추출한 데이터야.
    불필요한 공백과 오타를 수정해서 순수한 JSON 형식으로 만들어줘

    데이터 : {ocr_data}

    결과 형식:
    {{
        "data" : "YYYY-MM-DD",
        "price" : 숫자만
    }}
    """
    print('로컬 llm 데이터 정제중')

    response = ollama.chat(model='llama3:8b', messages=[
        {'role': 'user', 'content': prompt}
    ])

    return response['message']['content']

# 실행
refined_json = refine_with_llm(raw_ocr_results)
print("\n=== 최종 정제된 데이터 ===")
print(refined_json)