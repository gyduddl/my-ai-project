# %%
#라이브러리 임포트 및 선언
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import data_roader_2
import torch

from transformers import TrOCRProcessor, VisionEncoderDecoderModel, AutoTokenizer
# import requests
# import unicodedata
from io import BytesIO
from PIL import Image


dr = data_roader_2.parse_ai_hub_data()[:10]

processor = TrOCRProcessor.from_pretrained("ddobokki/ko-trocr") 
model = VisionEncoderDecoderModel.from_pretrained("ddobokki/ko-trocr")
tokenizer = AutoTokenizer.from_pretrained("ddobokki/ko-trocr")



# img = #여기에 이미지를 넣어야 함
# pixel_values = processor(img, return_tensors="pt").pixel_values 
# generated_ids = model.generate(pixel_values, max_length=64)
# generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
# generated_text = unicodedata.normalize("NFC", generated_text)
# print(generated_text)

# 데이터셋 클래스 정의

from torch.utils.data import Dataset

class OCRDataSet(Dataset):
    def __init__(self, dr, processor, tokenizer):
        self.dr = dr
        self.processor = processor
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.dr)
    
    def __getitem__(self,idx):
        item = self.dr[idx]
        img = item['crop_img']
        text = item['text_value']

        # 학습시킬때 코드 
        # 이미지를 모델 입력값으로 변환
        pixel_values = self.processor(img, return_tensors='pt').pixel_values

        # # 2. 정답 텍스트를 토큰화 (labels)
        labels = self.tokenizer(text, padding="max_length", max_length=64,truncation=True).input_ids

        return {
            # "pixel_values": pixel_values.squeeze(),
            # "labels": torch.tensor(labels)
            "pixel_values": pixel_values,
            "labels": labels
        }
        
        # 정답 텍스트르 토근화(label)

        # 실제 데이터를 가지고 ai 서비스
        # pixel_values = self.processor(img, return_tensors="pt").pixel_values
        # generated_ids = model.generate(pixel_values, max_length=64) # 나중에 실제 사진 가지고와서 사용
        # generated_text = self.tokenizer.batch_decode(generated_ids, skip_special_token=True)[0] 
        # test_image = Image.open("actual_photo.jpg").convert("RGB")

# # 2. 이미지 전처리 (processor 사용)
# pixel_values = processor(test_image, return_tensors="pt").pixel_values

# # 3. 모델이 답을 지어내기 (generate 사용) - 여기서 등장!
# generated_ids = model.generate(pixel_values, max_length=64)

# # 4. 사람이 읽을 수 있게 번역 (decode & normalize 사용)
# generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
# final_text = unicodedata.normalize("NFC", generated_text)

# print(f"사진 속 글자: {final_text}")
        
train_data = OCRDataSet(dr, processor, tokenizer)
sample = train_data[0]
print(sample['pixel_values'].shape)

    

# # %%
# from transformers import Seq2SeqTrainingArguments,Seq2SeqTrainer

# # training_args = Seq2SeqTrainingArguments(
# #     output_dir="./results",          # 모델 및 체크포인트 저장 디렉토리
# #     per_device_train_batch_size=8,   # 학습 배치 사이즈
# #     per_device_eval_batch_size=8,    # 평가 배치 사이즈
# #     learning_rate=5e-5,              # 학습률
# #     num_train_epochs=3,              # 에폭 수
# #     logging_steps=100,               # 로그 출력 주기
# #     evaluation_strategy="epoch",     # 평가 주기
# #     save_strategy="epoch",           # 체크포인트 저장 주기
# #     load_best_model_at_end=True,     # 학습 종료 후 최고 모델 로드
# #     predict_with_generate=True,      # (중요) 평가 시 생성된 텍스트 사용
# #     push_to_hub=False,               # Hugging Face Hub에 업로드 여부
# # )
# # 학습 설정
# training_args = Seq2SeqTrainingArguments(
#     output_dir="./test_run",      # 학습 결과물(체크포인트)이 저장될 폴더
#     per_device_train_batch_size=4, # 한 번에 공부할 데이터 양 (컴퓨터 사양 좋으면 16, 32로 올림)
#     predict_with_generate=True,    # 학습 중에도 예측을 해보면서 성능 체크
#     num_train_epochs=3,            # 전체 데이터를 총 몇 번 반복해서 볼 것인가
#     logging_steps=10,              # 10번마다 "나 지금 잘하고 있어"라고 보고
#     save_steps=100,                # 100번마다 공부한 내용 중간 저장
#     report_to="none"               # 다른 외부 툴 연결 안 함
# )

# # 학습시작
# trainer = Seq2SeqTrainer(
#     model=model,                         # 아까 불러온 ko-trocr 모델
#     args=training_args,                  # 위에서 만든 학습 설정
#     train_dataset=train_data,         # 아까 만든 OCRDataset 객체
#     tokenizer=tokenizer,
#     processor=processor
# )

# # 이 줄을 실행하는 순간 컴퓨터가 열심히 공부를 시작합니다!
# trainer.train()

# # %%



