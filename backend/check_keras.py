from tensorflow.keras.models import load_model
from data_roader import train_dataset
import matplotlib.pyplot as plt
import matplotlib.patches as patches
# patches는 matplotlib에서 제공하는 모듈로, 그래프나 이미지에 다양한 형태의 패치를 추가할 수 있도록 도와주는 기능을 제공합니다. 예를 들어, 사각형, 원, 다각형 등의 패치를 생성하여 이미지나 그래프에 시각적으로 강조하거나 구분할 때 사용됩니다. patches 모듈을 사용하면 이미지 위에 바운딩 박스나 기타 시각적 요소를 쉽게 추가할 수 있습니다.

model = load_model('my_ocr_model.keras')

for images, labels in train_dataset.take(1):
    prediction = model.predict(images[:1])

    print("\n---예측 결과---")
    print(f"모델이 찾은 좌표: {prediction}")
    print(f"실제 정답 좌표: {labels[0].numpy()}")
    #image
    plt.imshow(images[0].numpy())
    plt.show()
    #imshow와 show는 matplotlib.pyplot에서 제공하는 함수입니다. imshow는 이미지를 화면에 표시하는 함수로, 이미지 데이터를 입력으로 받아 해당 이미지를 시각적으로 표현합니다. show는 imshow로 표시된 이미지를 실제로 화면에 출력하는 함수입니다. 일반적으로 imshow로 이미지를 설정한 후, show를 호출하여 이미지를 화면에 나타내는 방식으로 사용됩니다.

    break