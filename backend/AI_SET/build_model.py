from tensorflow.keras import layers, models
from backend.AI_SET.data_roader import train_dataset
import tensorflow as tf

def build_model():
    # 모델의 입력 레이어를 정의합니다. 이 레이어는 640x640 크기의 RGB 이미지를 입력으로 받습니다. layers.Input() 함수를 사용하여 입력 레이어를 생성하며, shape 매개변수로 입력 데이터의 형태를 지정합니다. 여기서는 (640, 640, 3)으로 설정하여 640x640 크기의 이미지와 3개의 색상 채널(RGB)을 나타냅니다.
    input_layer = layers.Input(shape=(640, 640, 3))
    # 2. 이미지 특징 추출기
    # 이게 뭐야? : tf.keras.applications.MobileNeyV2는 TensorFlow Keras에서 제공하는 사전 학습된 모델 중 하나인 MobileNetV2를 나타냅니다. MobileNetV2는 경량화된 신경망 아키텍처로, 모바일 및 임베디드 장치에서 효율적으로 작동하도록 설계되었습니다. 이 모델은 이미지 분류, 객체 감지 등 다양한 컴퓨터 비전 작업에 사용될 수 있습니다. include_top=False는 모델의 최상위 레이어(분류 레이어)를 포함하지 않도록 설정하는 옵션입니다. weights='imagenet'는 ImageNet 데이터셋으로 사전 학습된 가중치를 사용하도록 지정하는 옵션입니다. 이를 통해 모델이 일반적인 이미지 특징을 이미 학습한 상태로 시작할 수 있습니다.
    base_model = tf.keras.applications.MobileNetV2(
        input_tensor=input_layer, # 입력 레이어를 모델의 입력으로 지정합니다. 이렇게 하면 MobileNetV2 모델이 input_layer에서 정의된 형태의 데이터를 입력으로 받게 됩니다.
        include_top=False, # 모델의 최상위 레이어(분류 레이어)를 포함하지 않도록 설정합니다. MobileNetV2는 일반적으로 이미지 분류 작업에 사용되며, include_top=False로 설정하면 모델의 마지막 분류 레이어가 제거됩니다. 이렇게 하면 모델이 이미지에서 특징을 추출하는 역할만 수행하게 됩니다.
        weights='imagenet' # 사전 학습된 가중치를 ImageNet 데이터셋으로 초기화하도록 지정하는 옵션입니다. ImageNet은 대규모 이미지 데이터셋으로, 다양한 객체와 장면을 포함하고 있습니다. weights='imagenet'로 설정하면 MobileNetV2 모델이 ImageNet 데이터셋에서 학습된 가중치를 사용하여 초기화됩니다. 이렇게 하면 모델이 일반적인 이미지 특징을 이미 학습한 상태로 시작할 수 있습니다.
    )

    base_model.trainable = True # MobileNetV2 모델의 가중치를 학습 가능하도록 설정합니다. 이렇게 하면 모델이 훈련 중에 가중치를 업데이트할 수 있게 됩니다. base_model.trainable = True로 설정하면 MobileNetV2 모델의 모든 레이어가 학습 가능하게 됩니다. 이를 통해 모델이 입력 이미지에서 특징을 추출하는 역할뿐만 아니라, 훈련 데이터에 맞게 가중치를 조정하여 더 나은 성능을 낼 수 있도록 합니다.

    x = layers.GlobalAveragePooling2D()(base_model.output) # MobileNetV2 모델의 출력에 글로벌 평균 풀링 레이어를 적용합니다. GlobalAveragePooling2D는 각 특징 맵의 평균값을 계산하여 고정된 크기의 벡터로 변환하는 레이어입니다. 이렇게 하면 모델의 출력이 고정된 크기의 벡터로 변환되어 다음 레이어에서 처리할 수 있게 됩니다.

    x = layers.Dense(128, activation='relu')(x) # 128개의 유닛과 ReLU 활성화 함수를 사용하는 완전 연결(Dense) 레이어를 추가합니다. 이 레이어는 글로벌 평균 풀링 레이어의 출력에 적용되어 특징을 더 추출하고, 모델이 더 복잡한 패턴을 학습할 수 있도록 합니다.
    x= layers.Dropout(0.2)(x) # 과적합 방지용 미들웨어 같은 역할

    output_layer = layers.Dense(4, activation='sigmoid')(x) # 4개의 유닛과 시그모이드 활성화 함수를 사용하는 완전 연결(Dense) 레이어를 추가합니다. 이 레이어는 모델의 최종 출력 레이어로, 4개의 유닛은 바운딩 박스의 좌표(x1, y1, x2, y2)를 나타냅니다. 시그모이드 활성화 함수는 출력값을 0과 1 사이로 제한하여 바운딩 박스 좌표가 이미지 크기에 비례하도록 합니다.

    model = models.Model(inputs=input_layer, outputs=output_layer) # 입력 레이어와 출력 레이어를 연결하여 모델을 생성합니다. 이렇게 하면 모델이 입력 이미지에서 특징을 추출하고, 바운딩 박스 좌표를 예측하는 역할을 수행할 수 있게 됩니다.
    return model

model =build_model()
model.summary()

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4), # Adam 옵티마이저를 사용하여 모델을 컴파일합니다. learning_rate=1e-4는 학습률을 0.0001로 설정하는 옵션입니다. Adam 옵티마이저는 적응형 학습률을 사용하여 모델의 가중치를 업데이트하는 알고리즘으로, 일반적으로 빠른 수렴과 좋은 성능을 제공합니다.
    loss='mean_squared_error', # 손실 함수로 평균 제곱 오차(mean squared error)를 사용하여 모델을 컴파일합니다. 이 손실 함수는 예측된 바운딩 박스 좌표와 실제 좌표 간의 차이를 제곱하여 평균을 계산합니다. 바운딩 박스 좌표 예측 문제에서는 일반적으로 회귀 문제로 간주되므로, mean_squared_error 손실 함수가 적합합니다.
    metrics=['mae']
)

EPOCHS = 3
history = model.fit(train_dataset, epochs=EPOCHS)

model.save('my_ocr_model.keras')
print("모델이 my_ocr_model.keras로 저장되었습니다./Users/kimhyoyoung/Desktop/my-ai-project/backend/my_ocr_model.keras 경로를 확인하세요.")

for images, bboxes in train_dataset.take(1):
    some_image = images[0:1]
    prediction = model.predict(some_image)
    print(prediction)
    break