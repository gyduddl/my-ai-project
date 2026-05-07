import json
import os
import cv2
import numpy as np

def parse_ai_hub_data(img_dir, label_dir):
    #
    dataset =[]

    # json 파일을 하나씩 읽는것 .endswith : 특정 문자가 참인지 아닌지
    json_files = [f for f in os.listdir(label_dir) if f.endswith('.json')]

    
    for j_file in json_files:
        with open(os.path.join(label_dir, j_file), 'r',encoding='utf-8') as f:
            data = json.load(f)
        # 로컬 디스크에 있는 json 파일 읽음
        # 텐설플로우가 학습할 수 있도록 좌표값, 텍스트만 고르기
        # 변환된 데이터를 메모리에 올려 학습을 시작
        image_name = data['image']['file_name']
        # 완벽한 경로로 만들기
        image_path = os.path.join(img_dir, image_name)

        if not os.path.exists(image_path):
            continue

        # 데이터
        words_info = []
        # word_box, value
        for word_data in data['text']['word']:
            bbox = word_data['wordbox'] 
            text = word_data['value']

            words_info.append({
                'bbox' : bbox,
                "text" : text
            })
        dataset.append({
            "image_path" : image_path,
            "words" : words_info
        })
    return dataset


img_dir = r"C:\Users\2class_9\Desktop\my-ai-project\backend\다양한 형태의 한글 글자 ocr\원천데이터\[원천]Training_인쇄체\001"
label_dir = r"C:\Users\2class_9\Desktop\my-ai-project\backend\다양한 형태의 한글 글자 ocr\라벨링데이터\001"
my_data = parse_ai_hub_data(img_dir, label_dir)
print(my_data[:10])