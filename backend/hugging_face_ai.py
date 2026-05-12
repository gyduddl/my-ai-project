#라이브러리 임포트 및 선언
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import data_roader_2
import torch
from transformers import Seq2SeqTrainingArguments,Seq2SeqTrainer


from transformers import TrOCRProcessor, VisionEncoderDecoderModel, AutoTokenizer
# import requests
# import unicodedata
from io import BytesIO
from PIL import Image


dr = data_roader_2.parse_ai_hub_data()[:100]

processor = TrOCRProcessor.from_pretrained("ddobokki/ko-trocr") 
model = VisionEncoderDecoderModel.from_pretrained("ddobokki/ko-trocr")
tokenizer = AutoTokenizer.from_pretrained("ddobokki/ko-trocr")

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

        labels = [label if label != self.tokenizer.pad_token_id else -100 for label in labels]

        return {
            "pixel_values": pixel_values.squeeze(),
            "labels": torch.tensor(labels)
        }
        
train_data = OCRDataSet(dr, processor, tokenizer)
sample = train_data[0]
print(sample['pixel_values'].shape)
    
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

# 학습 설정
training_args = Seq2SeqTrainingArguments(
    output_dir="./test_run",
    predict_with_generate=True,
    per_device_train_batch_size=4, 
    learning_rate=2e-5,             # ⚠️ 더 낮췄습니다. 아주 조심스럽게 접근합니다.
    max_grad_norm=0.1,             # ⚠️ 핵심: 61.5였던 norm을 0.01에서 잘라버립니다.
    adam_epsilon=1e-8,              # ⚠️ 수치 안정성을 위해 크게 키움 (NaN 방지)
    weight_decay=0.1,               # 가중치가 커지지 않게 더 강하게 규제
    num_train_epochs=30,
    fp16=False,
    logging_steps=1,
    # 맥북 MPS 가속기에서 가끔 발생하는 문제를 줄이기 위해
    dataloader_num_workers=0,       
    gradient_accumulation_steps=1,
)

# 학습시작
trainer = Seq2SeqTrainer(
    model=model,                         # 아까 불러온 ko-trocr 모델
    args=training_args,                  # 위에서 만든 학습 설정
    train_dataset=train_data,         # 아까 만든 OCRDataset 객체
    processing_class=processor,
)

# 이 줄을 실행하는 순간 컴퓨터가 열심히 공부를 시작합니다!
trainer.train()
trainer.save_model("./my_best_model")




