import json
import os
import numpy as np
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt


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
            "words" : words_info # 각각의 단어에 대한 바운딩 박스와 텍스트 정보가 담긴 리스트
        })
    return dataset


img_dir = r"/Users/kimhyoyoung/Desktop/my-ai-project/backend/다양한 형태의 한글 글자 ocr/원천데이터/[원천]Training_인쇄체/001"
label_dir = r"/Users/kimhyoyoung/Desktop/my-ai-project/backend/다양한 형태의 한글 글자 ocr/라벨링데이터/001"
my_data = parse_ai_hub_data(img_dir, label_dir)


def preprocess_data(image_path, bboxes):
    img = tf.io.read_file(image_path)
    img = tf.image.decode_jpeg(img, channels=3)  
    img = tf.image.resize(img, [640, 640])/255.0
    bboxes = tf.cast(bboxes, dtype=tf.float32)
    x1 = bboxes[0] / 640.0
    y1 = bboxes[1] / 640.0
    x2 = bboxes[2] / 640.0
    y2 = bboxes[3] / 640.0
    bboxes = tf.stack([x1, y1, x2, y2])
    
    return img, bboxes

BATCH_SIZE = 16

def create_dataset(data):
    image_paths = [item['image_path'] for item in data]
    bboxes = [item['words'][0]['bbox'] for item in data] 
    dataset = tf.data.Dataset.from_tensor_slices((image_paths, bboxes))
    dataset = dataset.map(preprocess_data)
    dataset = dataset.batch(BATCH_SIZE)
    return dataset
train_dataset = create_dataset(my_data)
    
# for images, bboxes in train_dataset.take(1):
#     img = images[0].numpy()
#     bbox = bboxes[0].numpy()
#     x1, y1, x2, y2 = bbox*640

#     img_to_show = (img * 255).astype(np.uint8)
#     img_to_show = cv2.rectangle(img_to_show, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

#     # plt.figure(figsize=(6, 6)) : 그래프의 크기를 설정하는 함수입니다. figsize는 가로와 세로의 크기를 인치 단위로 지정합니다. 예를 들어, figsize=(6, 6)은 가로와 세로가 각각 6인치인 정사각형 그래프를 생성합니다. 이 함수를 사용하여 그래프의 크기를 조절할 수 있습니다.
#     plt.figure(figsize=(6, 6))
#     # plt.imshow() : 이미지를 화면에 표시하는 함수입니다. img_to_show는 표시할 이미지 데이터를 나타냅니다. 이 함수는 이미지 데이터를 시각적으로 표현하여 화면에 출력합니다. plt.imshow(img_to_show)를 사용하여 img_to_show 이미지를 그래프에 표시할 수 있습니다.
#     plt.imshow(img_to_show)
#     plt.show()

#     break


