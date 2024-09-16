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

def main():
    st.title("商品画像背景修正 事例")
    st.markdown("""#### Amazon""")
    image2 = Image.open("img/case-study/Amazon_img_gen.png")
    st.image(image2, caption="", use_column_width=True)
    st.markdown("https://www.youtube.com/watch?v=89OubJGcUx0")

    st.markdown("""#### 画像関連事例、物体検出　- RoomClip""")
    image = Image.open("img/case-study/Roomclip.png")
    st.image(image, caption="", use_column_width=True)



main()
