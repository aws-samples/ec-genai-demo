import io
import numpy as np
import os
from PIL import Image
import streamlit as st
from api import common
from numpy import dot
from numpy.linalg import norm
import time

class RateLimiter:
    def __init__(self, calls_per_second):
        self.calls_per_second = calls_per_second
        self.last_call = 0

    def wait(self):
        now = time.time()
        time_since_last_call = now - self.last_call
        if time_since_last_call < 1 / self.calls_per_second:
            time.sleep((1 / self.calls_per_second) - time_since_last_call)
        self.last_call = time.time()

rate_limiter = RateLimiter(2)  # 1秒あたり2回のリクエストを許可



def calc_similarity(left_text, left_image, right_text, right_image):
    left_vector = get_vector(left_text, left_image)
    right_vector = get_vector(right_text, right_image)
    # コサイン類似度を求める計算式
    return dot(left_vector, right_vector) / (norm(left_vector) * norm(right_vector)) 

def get_vector(text, image):
    if text is None and image is None:
        return []

    bedrock_api = common.BedrockAPI()
    vector = bedrock_api.get_vector_titan_multi_modal(
        image if image is not None else None, 
        text if text is not None else None,
    )
    
    return vector

def signle_compare_panel(side):
    text = st.text_input("商品説明を入力", key=side + "text_input")
    
    return text
    
def search(k, vectorDB, text, image):
    bedrock_api = common.BedrockAPI()
    vector = bedrock_api.get_vector_titan_multi_modal(
        image, 
        text
    )
    return vectorDB.search(np.array([vector]), k)
    
def get_item_desc(image_name):
    df = st.session_state["pdframe_item_list"]
    return df[df["image_name"] == image_name][:1]["item_desc"].values[0]

def get_item_name(image_name):
    df = st.session_state["pdframe_item_list"]
    # print(df[df["image_name"]==image_name][:1]["item_name"].values[0])
    return df[df["image_name"] == image_name][:1]["item_name"].values[0]

def main():
    st.session_state["left_item_idx"] = 0
    st.session_state["right_item_idx"] = 0
    st.session_state["search_result_name_list"] = []

    st.title("商品検索")

    # ストア名
    # item_registerで事前に登録したか
    if "store_name" not in st.session_state:
        st.session_state["store_name"] = 'store'
        st.error('ストア名が登録されていません')
    try:
        if len(st.session_state["ref_idx_img"].values()) == 0:
            st.error('商品が登録されていません')
    except KeyError:
        pass

    save_dir = "store_source/" + st.session_state.store_name
    st.text('ストア名')
    st.text(st.session_state.store_name)
    
    if not os.path.exists(save_dir):
        st.warning(save_dir)

    uploaded_file = st.file_uploader("検索画像をアップロード", type=["png", "jpg", "jpeg"])

    text = st.text_input("検索テキストを入力 E.g. \"黒の服\", \"緑の長袖\",\"健康でヘルシーなご飯\",\"和食が食べたい\",\"画像＋これの長袖。\"")

    if uploaded_file is not None:
        # アップロードされた画像を読み込む
        bytes_data = uploaded_file.getvalue()
        image = Image.open(io.BytesIO(bytes_data))
        st.image(image, caption="アップロードされた画像")
        
    on_text = st.toggle(label="テキストモードON (ON:商品説明文に対してクエリー、off: 商品画像に対してクエリー)", value=True)

    # 処理を開始するボタン
    num_results = st.number_input("検索件数を指定してください", min_value=1, max_value=10, value=3)
    if st.button("検索する"):
        st.session_state["search_results"] = None
        if "vectorDB_img" not in st.session_state or st.session_state["vectorDB_img"].ntotal == 0:
            st.info("商品登録がありません。")
        elif "vectorDB_text" not in st.session_state or st.session_state["vectorDB_text"].ntotal == 0:
            st.info("商品登録がありません。")
        else:
            if on_text:
                st.session_state["search_results"] = search(
                    num_results,
                    st.session_state["vectorDB_text"], 
                    text, 
                    image if "image" in locals() else None
                )
            else:
                st.session_state["search_results"] = search(
                    num_results,
                    st.session_state["vectorDB_img"], 
                    text, 
                    image if "image" in locals() else None
                )
            st.markdown("""
            ----
            #### 商品検索結果
            """)
            if "search_results" in st.session_state and st.session_state["search_results"]:
                ds, ids = st.session_state["search_results"]
                        
                display_size = 3
                rows = st.columns(display_size)
                item_list = []
                
                item_desc_system_prompt = "あなたは商品を説明するプロです。お客様の性別、年齢、趣味に合う商品の良さを説明してください。"
                
                if "user_info" in  st.session_state:
                    for attr in st.session_state["user_info"]:
                        value = st.session_state["user_info"][attr]
                        item_desc_system_prompt = item_desc_system_prompt + f"お客様の {attr} は {value} です。"
                if text:
                    item_desc_system_prompt = item_desc_system_prompt + f"お客様からは「{text}」とのご要望をいただいています。回答時にご要望に対する補足説明を含めてください。 "
        
            
                for i, idx in enumerate(ids[0]):
                    idx = int(idx)
                    if idx != -1:
                        image_name = None
                        if on_text:
                            image_name = st.session_state["ref_idx_text"][idx]
                        else:
                            image_name = st.session_state["ref_idx_img"][idx]
                        item_list.append(image_name)
                        file_path = os.path.join(save_dir, image_name)
                        image = Image.open(file_path)
                        similarity = ds[0][i]
                        row_idx = i // display_size
                        col_idx = i % display_size
            
                        with rows[col_idx]:
                            with st.container(height=600):
                                st.image(image, caption=image_name, width=80)
                                st.write(f"類似度: {similarity:.2f}")
                                rate_limiter.wait()
                                bedrock_api = common.BedrockAPI()
                                #st.write(image_name)

                                #get_item_name(image_name)
                                st.write(get_item_name(image_name))


                                generated_desc = bedrock_api.get_item_desc_message(
                                    image, 
                                    get_item_desc(image_name), 
                                    system_prompt = item_desc_system_prompt,
                                    modelId = "anthropic.claude-3-haiku-20240307-v1:0"
                                )
                                st.write(generated_desc)
    
                                # 最後の行の場合は空白を追加
                                if row_idx == 2:
                                    st.write("")
                st.session_state["search_result_name_list"] = item_list
            
            st.markdown("""
            ----
            #### 商品比較結果
            """)
        
            if "search_results" in st.session_state and st.session_state["search_results"]:
                ds, ids = st.session_state["search_results"]
                item_compare_system_prompt = """
あなたは商品を推薦する目利きの担当者です。
2 つの商品が提示されるので、共通点と相違点をまとめてください。
日本語で回答してください。
商品画像や商品説明文と異なるメッセージはしないでください。
"""
                if "user_info" in  st.session_state:
                    for attr in st.session_state["user_info"]:
                        value = st.session_state["user_info"][attr]
                        item_compare_system_prompt = item_compare_system_prompt + f"お客様の {attr} は {value} です。"
                if text:
                    item_compare_system_prompt = item_compare_system_prompt + f"お客様からは「{text}」とのご要望をいただいています。回答時にご要望に対する補足説明を含めてください。 "
    
                
                first_item_idx = int(ids[0][0])
                first_image_name = None
                if on_text:
                    first_image_name = st.session_state["ref_idx_text"][first_item_idx]
                else:
                    first_image_name = st.session_state["ref_idx_img"][first_item_idx]
                first_image = Image.open(os.path.join(save_dir, first_image_name))
                first_desc = get_item_desc(first_image_name)        
                
                for i, idx in enumerate(ids[0]):
                    if idx == -1 or i == 0:
                        continue
                    comp_item_idx = int(ids[0][i])
                    comp_image_name = None
                    if on_text:
                        comp_image_name = st.session_state["ref_idx_text"][comp_item_idx]
                    else:
                        comp_image_name = st.session_state["ref_idx_img"][comp_item_idx]
                    comp_image = Image.open(os.path.join(save_dir, comp_image_name))
                    comp_desc = get_item_desc(comp_image_name)        
        
                    similarity = calc_similarity(
                        first_desc, 
                        first_image, 
                        comp_desc, 
                        comp_image,
                    )
                    rate_limiter.wait()
                    api = common.BedrockAPI()
                    compare_text = api.get_compare_message(
                        first_image, 
                        first_desc, 
                        comp_image,
                        comp_desc, 
                        system_prompt=item_compare_system_prompt,
                        modelId = "anthropic.claude-3-haiku-20240307-v1:0"
                    )
                    first_item_col, comp_item_col = st.columns(2)
                    with first_item_col:
                        st.image(first_image, caption = first_image_name)
                    with comp_item_col:
                        st.image(comp_image, caption = comp_image_name)
                    st.write(f"商品類似度: {similarity}")
                    st.write(compare_text)
                    st.markdown("---")

# if __name__ == "__main__":
main()

