import base64
import io
import os
from PIL import Image
import logging
from dotenv import load_dotenv
import streamlit as st



# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# dotenv で環境変数を読み込む
def load_env_if_exists():
    """カレントディレクトリに .env ファイルが存在する場合に限り、環境変数を読み込む。"""
    env_path = '.env'
    if os.path.isfile(env_path):
        load_dotenv(env_path)
        print(".env から環境変数を読み込みました。")
    else:
        print(".env ファイルが見つかりません。IAMロールまたは他の認証方法を使用します。")

load_env_if_exists()

class ImageProcessor:
    @staticmethod
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
        
st.title("生成 AI が切り開く新たな小売/消費財の体験")

st.markdown("""
グローバルトレンドとして小売/消費財業界での具体的な生成 AI の活用が始まっており、日本でも多くの企業が取り組み始めています。  
本デモでは、以下の4つのユースケースについて、Amazon Bedrockとその上で利用可能なモデルを利用した実装をお試しいただけます。  

また、日本のAWSのお客様やAmazonで既に取り組まれている事例をユースケースに合わせてご確認いただけます。  
""")

image = Image.open("img/image.png")
st.image(image, caption="", use_column_width=True)

st.markdown("#### アーキテクチャ")
st.markdown("""
アーキテクチャは非常にシンプルで、StreamlitベースのデモアプリがECSで起動し、適宜Amazon Bedrockのモデルにプロンプトを送信し、結果を描画します。  
マルチモーダル検索では、ベクトルDBとしてFAISSをECS上で動かしています。  
""")
architecture_image = Image.open("img/Architecture.png")
st.image(architecture_image, caption="", use_column_width=True)