import numpy as np
import os
import streamlit as st
import pandas as pd
import glob
import faiss
from api import common
from PIL import Image
import json

def exists_dir(save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

def load_images(dir_path):
    files = os.listdir(dir_path)
    ret = []
    for file in [f for f in files if f.endswith(".jpg") or f.endswith(".png") or f.endswith(".bmp")]:
        file_path = os.path.join(dir_path, file)
        ret.append(Image.open(file_path))
    return ret

def load_item_list_files(dir_path):
    files = os.listdir(dir_path)
    ret = []
    for file in [f for f in files if f.endswith(".csv") or f.endswith(".txt")]:
        file_path = os.path.join(dir_path, file)
        ret.append(read_item_list_csv(file_path))
    return ret
    
def read_item_list_csv(file_path):
    return pd.read_csv(
        file_path,
        names = ['image_name','item_name','item_desc'],
        header = 0,
        sep = ',',
        skipinitialspace = True,
        quotechar = '"',
        quoting = 0
    )

def delete_files_in_directory(directory):
    try:
        # ディレクトリ内のすべてのファイルのパスを取得
        file_paths = glob.glob(os.path.join(directory, '*'))
        
        # 各ファイルを削除
        for file_path in file_paths:
            os.remove(file_path)
        print(f"All files in {directory} have been deleted.")
    except Exception as e:
        print(f"Error deleting files: {e}")
        
def add_text_vectorDB(vectorDB, ref, text, name):
    bedrock_api = common.BedrockAPI()
    vector = bedrock_api.get_vector_titan_multi_modal(
        None, 
        text
    )
    vectorDB.add(np.array([vector]))
    ref[vectorDB.ntotal-1] = name

def add_image_vectorDB(vectorDB, ref, image, name):
    bedrock_api = common.BedrockAPI()
    vector = bedrock_api.get_vector_titan_multi_modal(
        image, 
        None,
    )
    vectorDB.add(np.array([vector]))
    ref[vectorDB.ntotal-1] = name
    
def add_item_list(df_item_list):
    st.session_state["pdframe_item_list"] = pd.concat(
        [st.session_state["pdframe_item_list"], 
        df_item_list]
    )

    
def init_vectorDB():
    # IndexFlatIP : コサイン類似度
    st.session_state["vectorDB_img"] = faiss.IndexFlatIP(1024)
    st.session_state["vectorDB_text"] = faiss.IndexFlatIP(1024)
    st.session_state["ref_idx_img"] = {}
    st.session_state["ref_idx_text"] = {}
    
def init_item_list():
    st.session_state["pdframe_item_list"] = pd.DataFrame()
    
def need_initialize():
    return "vectorDB_img" not in st.session_state or "vectorDB_text" not in st.session_state

def display_items(images, display_size = 5):
    rows = st.columns(display_size)

    for i, image in enumerate(images):
        row_idx = i // display_size
        col_idx = i % display_size
    
        # 対応するグリッドセルにコンテナを作成し、画像を表示
        with rows[col_idx]:
            with st.container():
                st.image(image, use_column_width=True)
            # 最後の行の場合は空白を追加
            if row_idx == 2:
                st.write("")

def int_keys(obj):
    return {int(k) if k.isdigit() else k: v for k, v in obj.items()}

def main():
    st.title("商品登録")
    st.markdown("""ベクターDB（FAISS）に商品を登録します。ここではすでにEmbedding済みのデータを用意しており、Vector DBにロードできます。  
以下のストアを選択して、`商品インデックスのロード` をクリックしてください。  
- store: アパレル商品  
- store_food: 料理、食品  
- store_living: 家具
""")
    
    if need_initialize():
        init_vectorDB()
        init_item_list()
    
    # ストア名
    if "store_name" not in st.session_state:
        st.session_state["store_name"] = 'store'

    # st.session_state["store_name"] = st.text_input("ストア名", value=st.session_state.store_name)
    st.session_state["store_name"] = st.selectbox(
        'ストア名',
        ('store', 'store_food', 'store_living')
    )
    save_dir = "store_source/" + st.session_state["store_name"]
    
    # 入力されたストア名を保存
    exists_dir(save_dir)

    # uploaded_images = st.file_uploader(
    #     "商品画像(複数可)をアップロードしてください", 
    #     type=["png", "jpg", "jpeg"], 
    #     accept_multiple_files=True
    # )

    # uploaded_item_lists = st.file_uploader(
    #     "商品リストをアップロードしてください", 
    #     accept_multiple_files=True,
    #     type=["csv", "txt"]
    # )

    # if st.button("全削除"):
    #     delete_files_in_directory(save_dir)
    #     init_vectorDB()
    #     init_item_list()
    #     st.success("Store files are deleted successfully.")
        
    # if uploaded_images is not None and uploaded_item_lists is not None:
    #     if st.button("追加登録"):
    #         if uploaded_images is not None:
    #             for image in uploaded_images:
    #                 save_path = os.path.join(save_dir, image.name)
    #                 with open(save_path, "wb") as f:
    #                     f.write(image.getbuffer())
    #                 add_image_vectorDB(
    #                     st.session_state["vectorDB_img"], 
    #                     st.session_state["ref_idx_img"],
    #                     Image.open(io.BytesIO(image.getvalue())), 
    #                     image.name
    #                 )
    #         if uploaded_item_lists is not None:
    #             for uploaded_item_list in uploaded_item_lists:
    #                 df = read_item_list_csv(uploaded_item_list)
    #                 add_item_list(df)
    #                 save_path = os.path.join(save_dir, uploaded_item_list.name)
    #                 with open(save_path, "wb") as f:
    #                     f.write(uploaded_item_list.getvalue())
                        
    #                 for data in df.itertuples():
    #                     #logging(data.image_name)
    #                     #logging(data.item_desc)

    #                     try:
    #                         add_text_vectorDB(
    #                             st.session_state["vectorDB_text"], 
    #                             st.session_state["ref_idx_text"],
    #                             data.item_desc,
    #                             data.image_name
    #                         )
    #                     except:
    #                         st.write(data.image_name)
    #                         st.write(data.item_desc)
    #         st.success("登録に成功しました。")

    txt_index_name = "index/" + st.session_state["store_name"] + "_txt.index"
    img_index_name = "index/" + st.session_state["store_name"] + "_img.index"
    ref_idx_txt_json = "index/" + st.session_state["store_name"] + "_txt.json"
    ref_idx_img_json = "index/" + st.session_state["store_name"] + "_img.json"

    
    if os.path.exists(txt_index_name) and os.path.exists(img_index_name):
        st.info(
            f"""
            インデックスパス：{txt_index_name} サイズ：{os.path.getsize(txt_index_name)} byte  
            インデックスパス：{img_index_name} サイズ：{os.path.getsize(img_index_name)} byte  
            jsonパス：{ref_idx_txt_json} サイズ：{os.path.getsize(ref_idx_txt_json)} byte  
            jsonパス：{ref_idx_img_json} サイズ：{os.path.getsize(ref_idx_img_json)} byte""")
        if st.button("商品インデックスのロード"):
            # Index Load
            st.session_state["vectorDB_text"] = faiss.read_index(txt_index_name)
            st.session_state["vectorDB_img"] = faiss.read_index(img_index_name)
            # 画面表示
            st.text(f"vectorDB_text: {st.session_state['vectorDB_text'].ntotal}")
            st.text(f"vectorDB_img: {st.session_state['vectorDB_img'].ntotal}")
            # Dict Load
            with open(ref_idx_txt_json, 'r', encoding="utf-8") as f:
                print("text json load")
                print(ref_idx_txt_json)
                st.session_state["ref_idx_text"] = json.load(f, object_hook=int_keys)
                print (st.session_state["ref_idx_text"])
            with open(ref_idx_img_json, 'r', encoding="utf-8") as f:
                print("img json load")
                print(ref_idx_img_json)
                st.session_state["ref_idx_img"] = json.load(f, object_hook=int_keys)
                print (st.session_state["ref_idx_img"]) 
            for item_list in load_item_list_files(save_dir):
                st.text(item_list)
                init_item_list()
                add_item_list(item_list)
                st.text(st.session_state["pdframe_item_list"])
    else:
        st.warning("インデックスが存在しません。初期化操作を行ってください。")

    st.markdown("""商品データからベクトルを作成するには、以下の `初期化操作` を利用してください。
                """)  

    if st.toggle("初期化操作"):
        st.markdown("""
- 初期化 - 商品データ登録 : 商品データの画像とテキストをベクトル化し、FAISSに登録します
- 商品インデックスの保存 : 一度 FAISS に登録したデータを `.index` ファイルとしてローカル保存します
                    """)
        if st.button("初期化 - 商品データ登録"):
            with st.spinner('Titan Multimodal Embeddings G1で商品データの画像とテキストをベクトル化し、FAISSに登録中です...'):
                init_vectorDB()
                for image in load_images(save_dir):
                    add_image_vectorDB(
                        st.session_state["vectorDB_img"], 
                        st.session_state["ref_idx_img"],
                        image, 
                        os.path.basename(image.filename)
                    )
                init_item_list()
                for item_list in load_item_list_files(save_dir):
                    add_item_list(item_list)
                    for data in item_list.itertuples():
                        st.write(data.image_name)
                        add_text_vectorDB(
                            st.session_state["vectorDB_text"], 
                            st.session_state["ref_idx_text"],
                            data.item_desc,
                            data.image_name
                        )
            
            st.success("商品データ登録に成功しました。")

        if st.button("商品インデックスの保存"):
            # Indexの保存
            exists_dir("index/")
            faiss.write_index(st.session_state["vectorDB_text"],txt_index_name)
            faiss.write_index(st.session_state["vectorDB_img"],img_index_name)
            # Dictの保存
            with open(ref_idx_txt_json, 'w', encoding="utf-8") as f:
                json.dump(st.session_state["ref_idx_text"], f)
            with open(ref_idx_img_json, 'w', encoding="utf-8") as f:
                json.dump(st.session_state["ref_idx_img"], f)
            st.success("インデックスの保存に成功しました。")
            

    st.markdown("""
        ---
        ## 登録結果
    """)

    if "ref_idx_img" in st.session_state and "pdframe_item_list" in st.session_state:
        image_names = st.session_state["ref_idx_img"].values()
        st.write(f"画像登録数: {len(image_names)}")
        try:
            display_items([Image.open(os.path.join(save_dir, image_name)) for image_name in image_names])
            item_list = st.session_state["pdframe_item_list"]
            st.write(item_list)
            st.write(st.session_state["ref_idx_img"])
            st.write(st.session_state["ref_idx_text"])
        except FileNotFoundError:
            st.write("該当なし")


# if __name__ == "__main__":
main()

