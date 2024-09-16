import streamlit as st
# from st_pages import add_indentation

# add_indentation()
def main():
    st.title("ユーザ情報")
    if "user_info" not in st.session_state:
        st.session_state["user_info"] = {}

    st.session_state["user_info"]["名前"] = st.text_input("名前", key="user_name", value="Amazon太郎")
    st.session_state["user_info"]["性別"] = st.text_input("性別", key="user_sex", value="男")
    st.session_state["user_info"]["年齢"] = st.number_input("年齢", key="user_age", value=37)
    st.session_state["user_info"]["趣味"] = st.text_input("趣味", key="user_hobby", value="テニス")


# if __name__ == "__main__":
main()