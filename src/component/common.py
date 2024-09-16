import streamlit as st

def signle_compare_panel(side):
    uploaded_image = st.file_uploader(
        "比較したい商品画像を 1 枚アップロード", 
        type=["png", "jpg", "jpeg"], 
        key = side + "file_uploader"
    )
    text = st.text_input("商品説明を入力", key=side + "text_input")
    
    return uploaded_image, text
