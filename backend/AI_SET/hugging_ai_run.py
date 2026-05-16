from transformers import TrOCRProcessor, VisionEncoderDecoderModel, AutoTokenizer
from io import BytesIO
from PIL import Image
import unicodedata
import backend.AI_SET.data_roader_2 as data_roader_2

# 모델 path
model_path = './my_best_model'
print("모델 로딩 시작...")

model = VisionEncoderDecoderModel.from_pretrained(model_path)
print(f"시작 토큰 ID: {model.config.decoder_start_token_id}")
processor = TrOCRProcessor.from_pretrained("ddobokki/ko-trocr") 
tokenizer = AutoTokenizer.from_pretrained("ddobokki/ko-trocr")

# img = './test_img.png'
# img = Image.open(img).convert("RGB")
dr = data_roader_2.parse_ai_hub_data()

item = dr[0] 
img = item['crop_img']

print("글자 읽는 중... 잠시만 기다려주세요.")
pixel_values = processor(img, return_tensors="pt").pixel_values 
generated_ids = model.generate(
    pixel_values, 
    max_length=64,
    decoder_start_token_id=2, # 강제 지정
    bad_words_ids=[[tokenizer.pad_token_id]] if tokenizer.pad_token_id is not None else None
)
print(f"모델이 뱉은 숫자들: {generated_ids[0].tolist()}")
generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
generated_text = unicodedata.normalize("NFC", generated_text)
print(f"출력값 :'{generated_text}'")