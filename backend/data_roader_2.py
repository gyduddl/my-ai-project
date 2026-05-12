import numpy as np
import pandas as pd
import os
import json
import cv2

img_dir = r"/Users/kimhyoyoung/Desktop/my-ai-project/backend/다양한 형태의 한글 글자 ocr/원천데이터/[원천]Training_인쇄체/001"
label_dir = r"/Users/kimhyoyoung/Desktop/my-ai-project/backend/다양한 형태의 한글 글자 ocr/라벨링데이터/001"

# 내가 전처리해야할 데이터
# {
#     "id": "00001",
#     "image_path": "path/to/img_001.jpg",
#     "text": "가",
#     "bbox": [x, y, w, h] 
#   }

# [이미지 경로, id, 텍스트, 좌표]이 코드를 활용해서 이미지에서 해당 부분 crop
# [해당 이미지 부분, 정답 텍스트, 고유 id]를 가지고 학습
def parse_ai_hub_data(img_dir = img_dir, label_dir = label_dir):
    json_file = [f for f in os.listdir(label_dir) if f.endswith('.json')]
    
    train_list = list()
    for j_file in json_file:
        first_processed_data = list()
        with open(os.path.join(label_dir,j_file), 'r', encoding='utf-8') as j_f:
            data = json.load(j_f)

        image_path =data['image']['file_name']
        image_name = data['image']['file_name'].split('.')[0]
        count_id = 0

        for l in data['text']['word']:
            for i in l['letter']:
                charbox_data = i['charbox']
                text_value = i['value']
                        
                first_processed_data.append({
                    'id': f"{image_name}_{count_id:04d}",
                    'image_path':image_path,
                    'text':text_value,
                    'bbox': charbox_data
                })
                count_id+=1

                # 이미지 전처리
                
        img = cv2.imread(os.path.join(img_dir, image_path))
        if img is not None:
            for idx in first_processed_data:
                
                # y1:y2, x1:x2
                crop_img = img[idx['bbox'][1]:idx['bbox'][3],idx['bbox'][0]:idx['bbox'][2]]
                # cv2.imshow('img', crop_img)
                # cv2.waitKey(1000)
                # cv2.destoryAllWindows()

                # BGR을 RGB로 변환하기
                if(len(crop_img.shape) ==3):
                    crop_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)

                # hugging face ai에 넣을 훈련 데이터로 넣기
                train_list.append({
                    'crop_img':crop_img, 
                    'text_value':idx['text'], 
                    'id': idx['id']
                })
                
    return train_list


if __name__ == "__main__":
    parse_ai_hub_data()
