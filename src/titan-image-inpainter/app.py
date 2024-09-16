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
import time

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
    mask = masked_image.point(lambda x: 0 if x < THRESHOLD else 255)
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
        if modelId == "amazon.titan-image-generator-v1":
            images = [Image.open(io.BytesIO(base64.b64decode(base64_image))) for base64_image in response_body.get("images")]
        elif modelId == "stability.stable-diffusion-xl-v1":
            images = [Image.open(io.BytesIO(base64.b64decode(response_body["artifacts"][0]["base64"])))]
        return images
    
    def generate_sd_prompt(self, prompt):
        system_prompt = """
あなたはStable Diffusionのプロンプトを生成するAIアシスタントです。
<step></step>の手順でStableDiffusionのプロンプトを生成してください。
<step>
* <rules></rules> を理解してください。ルールは必ず守ってください。例外はありません。
* ユーザは生成して欲しい画像の要件をチャットで指示します。チャットのやり取りを全て理解してください。
* チャットのやり取りから、生成して欲しい画像の特徴を正しく認識してください。
* 画像生成において重要な要素をから順にプロンプトに出力してください。ルールで指定された文言以外は一切出力してはいけません。例外はありません。
</step>
<rules>
* プロンプトは <output></output> の xml タグに囲われた通りに出力してください。
* 出力するプロンプトがない場合は、promptとnegativePromptを空文字にして、commentにその理由を記載してください。
* プロンプトは単語単位で、カンマ区切りで出力してください。長文で出力しないでください。プロンプトは必ず英語で出力してください。
* プロンプトには以下の要素を含めてください。
* 画像のクオリティ、被写体の情報、衣装・ヘアスタイル・表情・アクセサリーなどの情報、画風に関する情報、背景に関する情報、構図に関する情報、ライティングやフィルタに関する情報
* 画像に含めたくない要素については、negativePromptとして出力してください。なお、negativePromptは必ず出力してください。
* フィルタリング対象になる不適切な要素は出力しないでください。
* comment は <comment-rules></comment-rules> の通りに出力してください。
* recommendedStylePreset は <recommended-style-preset-rules></recommended-style-preset-rules> の通りに出力してください。
</rules>
<comment-rules>
* 必ず「以下が改善案です。」という文言を先頭に記載してください。
* 箇条書きで3つ画像の改善案を提案してください。
* 改行は\\nを出力してください。
</comment-rules>
<recommended-style-preset-rules>
* 生成した画像と相性の良いと思われるStylePresetを3つ提案してください。必ず配列で設定してください。
* StylePresetは、以下の種類があります。必ず以下のものを提案してください。
* 3d-model,analog-film,anime,cinematic,comic-book,digital-art,enhance,fantasy-art,isometric,line-art,low-poly,modeling-compound,neon-punk,origami,photographic,pixel-art,tile-texture
</recommended-style-preset-rules>
<output>
{
"prompt": string,
"negativePrompt": string,
"comment": string,
"recommendedStylePreset": string[]
}
</output>
出力は必ず prompt キー、 negativePrompt キー, comment キー, recommendedStylePreset キーを包有した JSON 文字列だけで終えてください。それ以外の情報を出力してはいけません。もちろん挨拶や説明を前後に入れてはいけません。例外はありません。
"""
        user_message = {"role": "user", "content": prompt}
        messages = [user_message]

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": messages,
                "stop_sequences": ['</output>']
            }
        )
        response = self.client.invoke_model(body=body, modelId="anthropic.claude-3-haiku-20240307-v1:0", accept="application/json", contentType="application/json")
        result = json.loads(response.get("body").read())

        logging.info(result["content"][0]["text"])

        extracted_text = result["content"][0]["text"].split("<output>", 1)[-1]

        if extracted_text:
            logging.info(extracted_text)
            return extracted_text
        else:
            print("No match <output></output> found in claud result prompt.")




    def edit_image(self, model_id, task_type, prompt, negative_prompt, image, maskImage=None, num_images=1, seed=0):
        """画像編集タスクを実行する"""
        translator = Translator()
        start = time.perf_counter()
        translated_prompt = translator.translate_text(prompt)
        end_translation = time.perf_counter()
        duration_translation = end_translation - start
        st.text("Translation by Amazon Translate 時間：{:.2f}秒".format(duration_translation))
        logging.info("Amazon Bedrock で画像生成を実行します。")
        logging.info(f"プロンプト（英訳前）: {prompt}")
        logging.info(f"プロンプト（英訳後）: {translated_prompt}")
        st.text_area(label="翻訳後のPrompt",value=translated_prompt)
        logging.info(f"ネガティブプロンプト: {negative_prompt}")
        logging.info(f"シード値: {seed}")

        if model_id == 'amazon.titan-image-generator-v1':
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
        elif model_id == 'stability.stable-diffusion-xl-v1':
            body = {
                "text_prompts": [
                    {
                        "text": translated_prompt,
                        # "weight": float
                    }
                ],
                "init_image" : convert_image_to_base64(image),
                "mask_source" : "MASK_IMAGE_BLACK",
                "mask_image" : convert_image_to_base64(maskImage),
                "cfg_scale": 8.0,
                # "clip_guidance_preset": string,
                # "sampler": string,
                "samples" : 1,
                "seed": seed,
                # "steps": int, #defalut 30
                "style_preset": "photographic",
                    # 3d-model, analog-film, anime, cinematic, comic-book, digital-art, enhance, fantasy-art, isometric, line-art, low-poly, modeling-compound, neon-punk, origami, photographic, pixel-art, tile-texture
                # "extras" : json object
            }

        result = self.invoke_model(body, modelId=model_id)
        end_imggen = time.perf_counter()
        duration_imggen = end_imggen - end_translation
        st.text("画像生成時間：{:.2f}秒".format(duration_imggen))
        return result

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

def load_default_image(default_image_path="./titan-image-inpainter/img/wine.png"):
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
    input_prompt = st.text_area("生成したい画像のイメージが伝わるよう、プロンプトを入力してください", "プロのカメラマンが撮影した商品画像、大理石のテーブルの上に、たくさんの果物が置かれている、背景は少しボケている")
    if st.toggle("Claude3 Haikuでプロンプトを生成する", False):
        bedrock_api = BedrockAPI()
        generated_prompt = bedrock_api.generate_sd_prompt(input_prompt)
        generated_prompt_dict = json.loads(generated_prompt)
        st.text_area(label="生成されたプロンプト", value=generated_prompt_dict["prompt"], height=50)
        st.text_area(label="改善案", value=generated_prompt_dict["comment"], height=100)
        prompt = generated_prompt_dict["prompt"]
    else:
        prompt = input_prompt
    negative_prompt = st.text_input("ネガティブプロンプトを入力してください", "lowres, error, cropped, worst quality, low quality, jpeg artifacts, ugly, out of frame")
    return prompt, negative_prompt

def generate_images(image, prompt, negative_prompt, seed_value, num_images, model_id):
    """画像生成処理を実行する関数"""
    with st.spinner('画像を生成中です...'):
        start = time.perf_counter()
        bg_removed_image = remove_background(image)
        if bg_removed_image:
            mask = create_binary_mask(bg_removed_image)
            end_mask = time.perf_counter()
            duration_mask = end_mask - start
            st.text("マスク処理時間：{:.2f}秒".format(duration_mask))
            bedrock_api = BedrockAPI()
            generated_images = bedrock_api.edit_image(model_id, "INPAINTING", prompt, negative_prompt, image, maskImage=mask, num_images=num_images, seed=seed_value)
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


    st.title("Titanによる商品画像背景修正")

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


    # model_id = st.selectbox(
    #     'モデル選択',
    #     ('amazon.titan-image-generator-v1', 'stability.stable-diffusion-xl-v1')
    # )
    model_id = 'amazon.titan-image-generator-v1'

    initialize_session_state()
    default_image = load_default_image()
    image = upload_image(default_image)
    image = resize_image(image)

    # アップロードされた画像またはデフォルト画像を表示
    if image:
        st.image(image, caption="選択された画像", use_column_width=True)

    prompt, negative_prompt = get_prompts()
    seed_rand_flag = st.toggle("シード値をランダムに設定する", value=False)
    if seed_rand_flag:
        seed_value = random.randrange(MAX_SEED_VALUE)
        st.text(seed_value)
    else:
        seed_value = st.number_input("シード値を入力してください (0 から " + str(MAX_SEED_VALUE) + ")", min_value=0, max_value=MAX_SEED_VALUE, value=st.session_state.seed_value, step=1)
    num_images = st.number_input("生成する画像の枚数を入力してください (1 から 3)　※Stable Diffusionの場合は最大1枚", min_value=1, max_value=3, value=1, step=1)
    if st.button("画像を生成する") and image is not None:
        generated_images, bg_removed_image = generate_images(image, prompt, negative_prompt, seed_value, num_images, model_id)
        st.session_state.generated_images = generated_images
        all_images = [image] + st.session_state.generated_images
        display_images(all_images, bg_removed_image=bg_removed_image)
        logging.info("画像の処理が完了しました。")

# if __name__ == "__main__":
main()
