import base64
import io
import os
from PIL import Image
import logging
from dotenv import load_dotenv
import streamlit as st


# from st_pages import add_indentation
# add_indentation()

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
    st.title("テキスト＆画像によるマルチモーダル商品検索")
    st.markdown("""
### Overview
* この Demo では特に生成 AI のマルチモーダルな機能を使って、今後 EC にどのような実装ができそうかを表現したいと思います
### 画面説明
#### user info
* EC 利用者情報登録画面
* 表示することで情報が読み込まれる（リロードで消えるため、必要に応じて表示する）
#### item register
* 商品情報登録画面
* item search で検索する元になる情報を設定する
* ストア名を指定することで、複数の商品セットを切り替えできる
* 商品リストは画像, 商品名, 説明文 3 列を持つ
* Amazon Titan Multimodal Embeddings G1 モデルにより Faiss に Vector が登録される
#### item search
* 商品検索画面
* 画像検索、テキスト検索、マルチモーダル検索ができる
* Amazon Titan Multimodal Embeddings G1 モデルにより Vector が計算され、Cosine 類似度降順に商品一覧を表示する
* 商品一覧が表示される際には、検索窓に入力されたテキストと usr info の情報を考慮して Amazon Bedrock Claude 3 Sonnet がユーザへのメッセージを生成、表示する
* 検索窓に入力されたテキストと usr info の情報を考慮して Amazon Bedrock Claude 3 Sonnet が商品一覧トップの商品と他の商品との比較説明を生成、表示する
### アーキテクチャ
                
* 利用モデル
  * anthropic.claude-3-haiku-20240307-v1:0
  * amazon.titan-embed-image-v1
""")
    architecture_image = Image.open("img/search_architecture.png")
    st.image(architecture_image, caption="", use_column_width=True)
    

# if __name__ == "__main__":
main()

