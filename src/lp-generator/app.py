import base64
import boto3
import io
import json
from PIL import Image
import logging
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import glob
import shutil
import uuid


# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# dotenv で環境変数を読み込む
def load_env_if_exists():
    """カレントディレクトリの .env ファイルから環境変数を読み込む。"""
    load_dotenv('.env')

load_env_if_exists()

class BedrockAPI:
    def __init__(self):
        self.client = boto3.client(service_name="bedrock-runtime", region_name=os.environ['region'])

    def invoke_model(self, body, modelId):
        """Bedrockのモデルを呼び出す"""
        response = self.client.invoke_model(body=body, modelId=modelId, accept="application/json", contentType="application/json")
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]
    async def image_invoke_model(self, body, modelId):
        """Bedrock の image モデルを呼び出す"""
        response = self.client.invoke_model(body=body, modelId=modelId, accept="application/json", contentType="application/json")
        response_body = json.loads(response.get("body").read())
        images = [Image.open(io.BytesIO(base64.b64decode(base64_image))) for base64_image in response_body.get("images")]
        return images

import random  # ランダムモジュールをインポート

MAX_IMAGE_DIMENSION = 8000  # 最大画像サイズ
MAX_SEED_VALUE = 2147483646  # 最大シード値
MAX_OUTPUT_TOKENS = 100000 # 最大出力トークン
bedrock_api = BedrockAPI()
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
# sonnetId = "anthropic.claude-3-sonnet-20240229-v1:0"
sonnetId = "anthropic.claude-3-5-sonnet-20240620-v1:0"

async def titan_image_generator(image_dict: dict,seed):
    for file in glob.glob("static/*"):
        os.remove(file)
    for dict_key, prompt in list(image_dict.items()):
        body = json.dumps(
            {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": f"{prompt[:511]}",   # Required
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,   # Range: 1 to 5 
                    "quality": "premium",  # Options: standard or premium
                    "height": 768,         # Supported height list in the docs 
                    "width": 1280,         # Supported width list in the docs
                    "cfgScale": 7.5,       # Range: 1.0 (exclusive) to 10.0
                    "seed": seed           # Range: 0 to 214783647
                }
            }
        )
        try:

            response = await bedrock_api.image_invoke_model(
                body=body, 
                modelId="amazon.titan-image-generator-v1"
            )
            for _, img in enumerate(response):
                img.save(f"static/{dict_key}.png")
                # bytes_data = img.getvalue()
                # image = Image.open(io.BytesIO(bytes_data))

                # # アップロードされた画像を MAX_IMAGE_DIMENSION x MAX_IMAGE_DIMENSION 以下にする
                # if image.width > MAX_IMAGE_DIMENSION or image.height > MAX_IMAGE_DIMENSION:
                #     # 画像の縦横比を維持したまま、長辺を MAX_IMAGE_DIMENSION にする
                #     if image.width > image.height:
                #         image = image.resize((MAX_IMAGE_DIMENSION, int(image.height * MAX_IMAGE_DIMENSION / image.width)))
                #     else:
                #         image = image.resize((int(image.width * MAX_IMAGE_DIMENSION / image.height), MAX_IMAGE_DIMENSION))

                st.image(img, caption=f"生成された画像 {dict_key}")
        except Exception as e:
            print("error", e.response['Error']['Code'])
            st.error(f"エラーが発生しました、LPからこの画像を除きます: {e}")
            image_dict.pop(dict_key)


def generate_random_hash(length=10):
    return "image_"+str(uuid.uuid4())[:length]

def main():
    st.title("Bedrock LP Generator")

    # セッションステートでシード値を管理
    if 'seed_value' not in st.session_state:
        st.session_state.seed_value = 0  # 初期値を設定
    # セッションステートで生成する画像数を管理
    if 'image_num' not in st.session_state:
        st.session_state.image_num = 3  # 初期値を設定

    # ユーザーに画像のアップロードを促す
    uploaded_file = st.file_uploader("デザインの参考画像も入力する場合は、画像をアップロードしてください", type=["png", "jpg", "jpeg"])
    # アップロードされた画像を表示
    if uploaded_file is not None:
        # アップロードされた画像を読み込む
        bytes_data = uploaded_file.getvalue()
        image = Image.open(io.BytesIO(bytes_data))

        # アップロードされた画像を MAX_IMAGE_DIMENSION x MAX_IMAGE_DIMENSION 以下にする
        if image.width > MAX_IMAGE_DIMENSION or image.height > MAX_IMAGE_DIMENSION:
            # 画像の縦横比を維持したまま、長辺を MAX_IMAGE_DIMENSION にする
            if image.width > image.height:
                image = image.resize((MAX_IMAGE_DIMENSION, int(image.height * MAX_IMAGE_DIMENSION / image.width)))
            else:
                image = image.resize((int(image.width * MAX_IMAGE_DIMENSION / image.height), MAX_IMAGE_DIMENSION))

        st.image(image, caption="アップロードされた画像")
        image_base64 = base64.b64encode(bytes_data).decode("utf-8")
    image_num = st.number_input("LP 内で使用する画像数を入力してください (0 から 20)", min_value=0, max_value=20, value=st.session_state.image_num, step=1)
    if image_num != 0:
        seed_value = st.number_input("シード値を入力してください (0 から " + str(MAX_SEED_VALUE) + ")", min_value=0, max_value=MAX_SEED_VALUE, value=st.session_state.seed_value, step=1)

    # 1回目のユーザの入力文
    user_prompt_1 = st.text_area("生成したいLPのイメージが伝わるよう、プロンプトを入力してください","""あなたはある<item></item>を訴求する<media></media>を作成するメディアライターです。
<target></target>に<item></item>を使った<contents></contents>の魅力を伝えたいです。そのためのLPの構成となる見出しリストを作成してください。

<item>
貯金箱「コツコツくん」
</item>

<contents>
- 解決したい課題
- 課題の解決力
- 利用シーン    
</contents>

<target>
貯金がなかなかできない人
</target>
""",height=500)

    # 処理を開始するボタン
    if st.button("HTMLを生成する"):
        # 処理中はローディング状態を表示
        with st.spinner('HTMLを生成中です...'):
            # Amazon Bedrock でHTML生成を実行する
            # prompt の入力
            prompt = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.0,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt_1
                    }
                ]
            })

            # 1回目の LLM からの回答文
            assistant_return_1 = bedrock_api.invoke_model(prompt,modelId=MODEL_ID)
            st.subheader("LP の見出しリスト")
            st.markdown(assistant_return_1)
        with st.spinner('HTMLを生成中です...'):
            # 2回目のユーザの入力文
            user_prompt_2 = "LPのセクションの内容を作成するにあたって、追加で必要となる情報を質問してください。"
            prompt = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.0,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt_1
                    },
                    {
                        "role": "assistant",
                        "content": assistant_return_1
                    },
                    {
                        "role": "user",
                        "content": user_prompt_2
                    }
                ]
            })
            # 2回目の LLM からの回答文
            assistant_return_2 = bedrock_api.invoke_model(prompt,modelId=MODEL_ID)
            # 3回目のユーザの入力文
            st.subheader("見出しリストへの肉付け")
            st.markdown(assistant_return_2)
        with st.spinner('HTMLを生成中です...'):
            user_prompt_3 = "実際に各セクションに、見出しと本文にダミー情報を入れてください。"
            prompt = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.0,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt_1
                    },
                    {
                        "role": "assistant",
                        "content": assistant_return_1
                    },
                    {
                        "role": "user",
                        "content": user_prompt_2
                    },
                    {
                        "role": "assistant",
                        "content": assistant_return_2
                    },
                    {
                        "role": "user",
                        "content": user_prompt_3
                    }

                ]
            })
            # 3回目の LLM からの返却文
            assistant_return_3 = bedrock_api.invoke_model(prompt,modelId=MODEL_ID)
            st.subheader("サンプルとしてダミーの情報を入れる")
            st.markdown(assistant_return_3)
        with st.spinner('HTMLを生成中です...'):

            # 画像を生成しない場合の プロンプト
            image_contain_prompt = " - 画像のタグは生成しないでください。"
            if image_num != 0:
                # 画像名をランダム生成
                img_name_dict=[]
                for i in range(image_num):
                    img_name_dict.append(generate_random_hash())
                print(img_name_dict)

                # 画像を生成するためのプロンプト
                prompt = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": MAX_OUTPUT_TOKENS,
                    "temperature": 0.0,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""
<content></content>を元に、各セクションに画像の説明をする文章を<rule></rule>に従って英語で作成してください。
出力は<output></output>のJSON形式で出力してください。画像名は<name></name>で与えられたモノを順に利用してください。
JSON 以外は出力しないでください。
<content>{assistant_return_3}</content>
<rule>
- HTMLのタグで表現できる内容は画像にしないでください。
- 画像の説明は{image_num}枚分作成してください。
- 暴力的な表現や誇大広告は避けてください。
- 生成する文章は AWS の責任ある AI ポリシーに従ってください。ポリシーのurl はhttps://aws.amazon.com/jp/machine-learning/responsible-ai/policy/ です。
</rule>
<name>
{img_name_dict}
</name>
<output>
{{
    'image_9e3d82f':'ここに画像の説明をする文章を英語で入力します。画像生成 AI のプロンプトに沿った形式で入力してください。'
}}
</output>
    """
                            }
                        ]
                    })
                # 画像生成のための dict 生成
                image_dict = bedrock_api.invoke_model(prompt,modelId=sonnetId)
                image_dict = image_dict.strip('<output>')
                image_dict = image_dict.rstrip('</output>')
                image_dict = dict(json.loads(image_dict))
                print(image_dict)
            for i,v in enumerate(image_dict.values()):
                st.subheader(f"生成する画像の説明: {i+1}")
                st.markdown(v)
        with st.spinner('HTMLを生成中です...'):
            if image_num != 0:
                asyncio.run(titan_image_generator(image_dict,seed_value))
                # 生成した画像を
                image_contain_prompt = f'''- 画像のタグは<img src="./app/static/image_7e0ceb1.png"> のように作成してください。
- <images></images>の画像から選択し、同じ画像は使わないようにしてください。
- 画像のタグは {len(image_dict)} つ作成してください。'''
            content = []
            # 画像を参考にしてデザインを作成する場合のプロンプト (参考にしない場合)
            add_image_prompt = ""
            if uploaded_file is not None:
                # 画像をプロンプトの先頭に配置する
                content.append(
                    {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": uploaded_file.type,
                        "data": image_base64,
                    },
                })
                # 画像を参考にしてデザインを作成する場合のプロンプト (参考にする場合)
                add_image_prompt = "デザインは添付の画像を参考にして作成してください。"
            # HTML を作成するためのプロンプト
            prompt = f"""
<content></content>を元に、LP を作成してください。
{add_image_prompt}
作成には<rule></rule>に従ってください。HTML と Style のみを出力してください。それ以外は出力しないでください。
<rule>
- 出力はHTMLと、それを修飾するためのStyleのみを出力してください。
{image_contain_prompt}
</rule>
<images>
{image_dict}
</images>
<content>{assistant_return_3}</content>
                        """
            content.append(
                    {
                        "type": "text",
                        "text": prompt
                    }
            )    
            prompt = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.0,
                "messages": [{"role": "user","content":content}] if uploaded_file is not None else [{
                    "role": "user",
                    "content": prompt
                }]
            })
            # 生成した HTML

            html = bedrock_api.invoke_model(prompt,modelId=sonnetId)
            html = html.strip('```html')
            html = html.rstrip('```')
            with open("static/bedrock_lp_generator.html","w", encoding="utf-8") as f:
                f.write(html)
            shutil.make_archive('static', format='zip', root_dir='static')
            st.subheader("作成した LP")
            with st.container(border=True):
                # HTML の出力
                components.html(html,height=1000,scrolling=True)
                with open("static.zip", "rb") as file:
                    st.download_button(
                        label="HTMLをダウンロード",
                        data=file,
                        # file_name=f"bedrock_lp_generator.html",
                        file_name="static.zip",
                        # mime="text/html"
                        mime="application/zip"
                    )
     
# if __name__ == "__main__":
main()

