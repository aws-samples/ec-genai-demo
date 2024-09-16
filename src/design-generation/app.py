import base64
import boto3
import io
import json
import os
from PIL import Image
import logging
from rembg import remove
from dotenv import load_dotenv
import streamlit as st

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# dotenv で環境変数を読み込む
def load_env_if_exists():
    """カレントディレクトリの .env ファイルから環境変数を読み込む。"""
    if os.path.exists('.env'):
        load_dotenv('.env')

load_env_if_exists()

THRESHOLD = 128 # 2 値化の閾値

def create_binary_mask(masked_image):
    """マスク画像を2値化する"""
    mask = masked_image.point(lambda x: 0 if x > THRESHOLD else 255)
    return mask

def remove_background(input_image):
    """背景を削除する"""
    # rembgを使用して背景を削除
    # only_mask=True でマスク画像のみを出力
    output_image = remove(input_image,only_mask=True, alpha_matting=True)

    return output_image

def convert_image_to_base64(image_input):
    """画像をBase64エンコードされた文字列に変換"""
    if isinstance(image_input, str):
        if not os.path.isfile(image_input):
            raise FileNotFoundError(f"指定されたファイルが見つかりません: {image_input}")
        with open(image_input, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")
    elif isinstance(image_input, Image.Image):
        buffer = io.BytesIO()
        image_input.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    else:
        raise ValueError("サポートされていない型です。str (ファイルパス) または PIL.Image.Image が必要です。")

def get_image_bytes(image, format="PNG"):
    """画像をバイト形式で取得する"""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()

class TranslationError(Exception):
    """Translateでエラーが発生した場合のカスタム例外クラス"""
    def __init__(self, message="Translateでエラーが発生しました。", errors=None):
        super().__init__(message)
        self.errors = errors

class Translator:
    def __init__(self, region_name='ap-northeast-1'):
        self.client = boto3.client(service_name="translate", region_name=region_name)

    def translate_text(self, text, source_language_code='ja', target_language_code='en'):
        """テキストを翻訳する"""
        try:
            result = self.client.translate_text(Text=text, SourceLanguageCode=source_language_code, TargetLanguageCode=target_language_code)
            return result.get('TranslatedText')
        except Exception as e:
            logging.error(f"翻訳中にエラーが発生しました: {e}")
            raise TranslationError(errors=e)

class BedrockAPI:
    def __init__(self):
        self.client = boto3.client(service_name="bedrock-runtime", region_name=os.environ['region'])

    def invoke_model(self, body, modelId):
        """Bedrockのモデルを呼び出す"""
        response = self.client.invoke_model(body=json.dumps(body), modelId=modelId, accept="application/json", contentType="application/json")
        response_body = json.loads(response.get("body").read())
        images = [Image.open(io.BytesIO(base64.b64decode(base64_image))) for base64_image in response_body.get("images")]
        return images

    def edit_image(self, task_type, prompt, negative_prompt, image, maskImage=None, num_images=1, seed=0):
        """画像編集タスクを実行する"""
        translator = Translator()
        translated_prompt = translator.translate_text(prompt)
        logging.info("Amazon Bedrock で画像生成を実行します。")
        logging.info(f"プロンプト（英訳前）: {prompt}")
        logging.info(f"プロンプト（英訳後）: {translated_prompt}")
        logging.info(f"ネガティブプロンプト: {negative_prompt}")
        logging.info(f"シード値: {seed}")

        body = {
            "taskType": task_type.upper(),
            "inPaintingParams": {
                "text": translated_prompt,
                "negativeText": negative_prompt,
                "image": convert_image_to_base64(image),
            },
            "imageGenerationConfig": {
                "numberOfImages": num_images,
                "quality": "standard",
                "cfgScale": 8.0,
                "seed": seed,
            }
        }
        if maskImage:
            body["inPaintingParams"]["maskImage"] = convert_image_to_base64(maskImage)
        return self.invoke_model(body, modelId="amazon.titan-image-generator-v1")

import random  # ランダムモジュールをインポート

MAX_IMAGE_DIMENSION = 1024  # 最大画像サイズ
MAX_SEED_VALUE = 2147483646  # 最大シード値

def save_image_to_session_state(image: Image.Image, image_key: str):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    st.session_state[image_key] = encoded_image

# セッションステートから画像を読み込む例
def load_image_from_session_state(image_key: str) -> Image.Image:
    encoded_image = st.session_state.get(image_key)
    if encoded_image:
        image_data = base64.b64decode(encoded_image)
        image = Image.open(io.BytesIO(image_data))
        return image
    return None

def load_default_image(default_image_path="./design-generation/img/shoe.png"):
    """デフォルト画像を読み込む関数"""
    if os.path.exists(default_image_path):
        with open(default_image_path, "rb") as file:
            default_bytes_data = file.read()
        return Image.open(io.BytesIO(default_bytes_data))
    else:
        st.error(f"デフォルト画像が見つかりません。")
        return None

def upload_image(default_image):
    """ユーザーに画像のアップロードを促し、アップロードされた画像またはデフォルト画像を返す関数"""
    uploaded_file = st.file_uploader("画像をアップロードしてください（任意）", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return Image.open(io.BytesIO(bytes_data))
    return default_image

def resize_image(image, max_dimension=MAX_IMAGE_DIMENSION):
    """画像のサイズを調整する関数"""
    if image.width > max_dimension or image.height > max_dimension:
        if image.width > image.height:
            return image.resize((max_dimension, int(image.height * max_dimension / image.width)))
        else:
            return image.resize((int(image.width * max_dimension / image.height), max_dimension))
    return image

def get_prompts():
    """プロンプトとネガティブプロンプトの入力を受け取る関数"""
    prompt = st.text_input("生成したい画像のイメージが伝わるよう、プロンプトを入力してください", "カラフルな革靴、白い紐、ハートロゴ")
    negative_prompt = st.text_input("ネガティブプロンプトを入力してください", "lowres, error, cropped, worst quality, low quality, jpeg artifacts, ugly, out of frame")
    return prompt, negative_prompt

def generate_images(image, prompt, negative_prompt, seed_value, num_images):
    """画像生成処理を実行する関数"""
    with st.spinner('画像を生成中です...'):
        bg_removed_image = remove_background(image)
        if bg_removed_image:
            mask = create_binary_mask(bg_removed_image)
            bedrock_api = BedrockAPI()
            generated_images = bedrock_api.edit_image("INPAINTING", prompt, negative_prompt, image, maskImage=mask, num_images=num_images, seed=seed_value)
            return generated_images, bg_removed_image
        else:
            st.error("画像の処理に失敗しました。")
            return [], None

def display_images(all_images, bg_removed_image=None):
    """画像を表示する関数"""
    for i, img in enumerate(all_images, start=1):
        if i == 1 and bg_removed_image:  # 元画像とマスク画像を表示
            cols = st.columns(2)
            with cols[0]:
                st.image(img, caption="元画像", use_column_width=True)
            with cols[1]:
                st.image(bg_removed_image, caption="マスク画像", use_column_width=True)
            continue
        if (i-1) % 2 == 1:
            cols = st.columns(2)
        with cols[(i-2) % 2]:
            caption = f"生成した画像 {i-1}"
            st.image(img, caption=caption, use_column_width=True)

def initialize_session_state():
    """セッションステートの初期化"""
    if 'seed_value' not in st.session_state:
        st.session_state.seed_value = 0
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = []

def main():
    st.title("Titanによる製品デザイン案生成")
    st.markdown("""
- 利用モデル
  - amazon.titan-image-generator-v1
- 仕組み
  - マスク画像の自動生成
    - Titan Image Generator の maskPrompt で指定することも可能ですが、輪郭を正確にマスクすることは難しいため、 rembgライブラリを使用
  - 日本語プロンプトへの対応
    - プロンプトを Amazon Bedrock に渡す際に Amazon Translate を利用して英訳しています。そのため、日本語プロンプトを入力しても問題なく動作
  - 画像生成
    - Amazon Bedrock の Titan Image Generator モデルを使用して、ユーザーが入力したプロンプトに基づいて画像を編集
    − Inpaint を利用することで、マスク部分以外の画像生成を行います
---
""")
    initialize_session_state()
    default_image = load_default_image()
    image = upload_image(default_image)
    image = resize_image(image)

    # アップロードされた画像またはデフォルト画像を表示
    if image:
        st.image(image, caption="選択された画像", use_column_width=True)

    prompt, negative_prompt = get_prompts()
    seed_value = st.number_input("シード値を入力してください (0 から " + str(MAX_SEED_VALUE) + ")", min_value=0, max_value=MAX_SEED_VALUE, value=st.session_state.seed_value, step=1)
    num_images = st.number_input("生成する画像の枚数を入力してください (1 から 3)", min_value=1, max_value=3, value=1, step=1)
    if st.button("画像を生成する") and image is not None:
        generated_images, bg_removed_image = generate_images(image, prompt, negative_prompt, seed_value, num_images)
        st.session_state.generated_images = generated_images
        all_images = [image] + st.session_state.generated_images
        display_images(all_images, bg_removed_image=bg_removed_image)
        logging.info("画像の処理が完了しました。")

main()

# if __name__ == "__main__":
#     main()
