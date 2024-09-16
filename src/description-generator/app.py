import os
import base64
import json
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder, 
)
from langchain_community.chat_models import BedrockChat
from langchain.memory import ConversationBufferMemory
from langchain.schema import (
    messages_from_dict, 
    messages_to_dict,
    HumanMessage,
)

import time
import io

# Load environment variables
load_dotenv()

# Function to load prompt from S3 bucket
def load_prompt():
    with open("./description-generator/prompt.txt", "r", encoding="utf-8") as file:
        prompt = file.read()
    return prompt

# Function to save conversation memory to local file system
def save_memory(memory, session_id):
    file_path = f'./{session_id}.json'
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(messages_to_dict(memory.chat_memory.messages)))

# Function to load conversation memory from local file system
def load_memory(session_id):
    file_path = f'./{session_id}.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            memory = ConversationBufferMemory(return_messages=False, human_prefix="H", assistant_prefix="A")
            memory.chat_memory.messages = messages_from_dict(json_data)
    except FileNotFoundError:
        memory = ConversationBufferMemory(return_messages=False, human_prefix="H", assistant_prefix="A")
    return memory

# Function to handle chat with model
def chat(message, session_id, model_id):
    start = time.perf_counter()
    system_prompt = load_prompt()
    # memory = load_memory(session_id)
    # messages = memory.chat_memory.messages
    messages = {"human_input":message}

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        # MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="human_input")
    ])
    
    LLM = BedrockChat(
        # model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_id=model_id,
        region_name=os.environ['region']
    )

    chain = prompt | LLM

    human_input = [HumanMessage(content=message)]
    resp = chain.invoke(
        {
            # "history": messages,
            "human_input": human_input,
        }
    )

    response = resp.content

    # if isinstance(message, str):
    #     memory.chat_memory.messages.append(human_input[0])
    # else:
    #     text = next(item for item in message if item['type'] == 'text')['text']
    #     memory.chat_memory.messages.append(HumanMessage(content=text))
        
    # memory.chat_memory.messages.append(AIMessage(content=response))
    # save_memory(memory, session_id)
    end = time.perf_counter()
    duration = end - start

    return response, duration

def load_default_image(default_image_path="./store_source/store/02.png"):
    """デフォルト画像を読み込む関数"""
    if os.path.exists(default_image_path):
        with open(default_image_path, "rb") as file:
            default_bytes_data = file.read()
        # return Image.open(io.BytesIO(default_bytes_data))
        
        return io.BytesIO(default_bytes_data)
    else:
        st.error(f"デフォルト画像が見つかりません。")
        return None

def upload_image(default_image):
    """ユーザーに画像のアップロードを促し、アップロードされた画像またはデフォルト画像を返す関数"""
    uploaded_file = st.file_uploader("画像をアップロードしてください（任意）", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return uploaded_file
    return default_image

def main():
    st.title("Claude3による商品説明文生成")
    st.markdown("""
- 利用モデル
  - anthropic.claude-3-haiku-20240307-v1:0
  - anthropic.claude-3-sonnet-20240229-v1:0
- 仕組み
  - 商品分析
    - 商品画像、商品名、商品の特徴をインプットに、Amazon BedrockのClaude3を利用して、商品について分析
      - プロンプトや商品の特徴を変更して出力結果の違いを見てみてください
      - HaikuとSonnetを切り替えて、精度の違いや速度の違いを感じてください
  - 商品説明文生成
    - 商品分析した結果を使って、「説明文に含めたいトピック」に基づいて、商品説明文やインスタグラムの投稿パターンをClaude3にて提案します。
---
""")

    session_id = st.session_state.get("session_id", "default")
    model_id = st.selectbox(
        'モデル選択',
        (
            'anthropic.claude-3-haiku-20240307-v1:0', 
            'anthropic.claude-3-sonnet-20240229-v1:0',
            'anthropic.claude-3-5-sonnet-20240620-v1:0'
        )
    )
    # temp_messageとfollow_up_messageをsession_stateで管理
    if 'messages_1' not in st.session_state:
        st.session_state.messages_1 = []
    if 'messages_2' not in st.session_state:
        st.session_state.messages_2 = []
    if 'messages_3' not in st.session_state:
        st.session_state.messages_3 = []


    st.markdown("#### 商品情報のインプット")

    # uploading image
    default_image = load_default_image()
    uploaded_file = upload_image(default_image)

    if uploaded_file:   # Display the uploaded image with specified size
        st.image(uploaded_file, caption='Uploaded Image.', width=300)

    focus_item = st.text_input("商品名", "半袖シャツ")

    feature = st.text_area(label="商品の特徴", height=150, value="""- 素材：ポリエステル
- 伸縮性：あり
- 季節：通年
- 厚さ：薄手"""
    )

    st.markdown("---")
    st.markdown("#### 商品説明文の生成")
    topic = st.text_area(label="説明文に含めたいトピック", height=150, value="""- 【概要】
- 【詳細】
- 【素材】
- 【利用用途】
- 【デザイン】"""
    )


    prompt_analyze = st.text_area(label="商品説明文生成用のPrompt",height=400,
value=f"""
<your role>あなたは、Eコマースにおける売場づくりのプロフェッショナルです。</your role>
<instruction>
新商品 {focus_item}の販売促進のために、Eコマースサイトでユーザーが思わず購入したくなるような魅力的な商品説明を考えてください。
あなたが読み込んだ画像は{focus_item}の写真です。
{focus_item}の色や種類を分析し、この商品を具体的に説明してください。商品の特徴が feature に記載されます。
説明文の提案は step に則って作成してください。
</instruction>
<step>
ステップ1: 商品の基本情報を確認する
ステップ2: ターゲット層を設定する
ステップ3: ターゲット層に合わせた言葉遣いやトーンを決める
ステップ4: 概要を書く
ステップ5: 埋めるべき各項目を書く
ステップ6: 全体を通して推敲する
</step>
<feature>
{feature}
</feature>
<topic>
{topic}
</topic>
<constraint>
アウトプットは topic に記載された項目に沿って記載してください。
最後に推奨ターゲット層とそれに合わせた販売チャネルについて提案してください。
なお、XMLタグは出力しないでください。
</constraint>
"""
    )
    if st.button("商品説明文の生成"):
        with st.spinner('処理中...'):
            if uploaded_file is not None:
                # To read file as bytes:
                bytes_data = uploaded_file.getvalue()
                encoded_string = base64.b64encode(bytes_data).decode("utf-8")

                response, duration = chat([
                    {"type": "image_url", "image_url": { "url": "data:image/jpeg;base64,"+encoded_string } },
                    {
                        "type": "text",
                        "text": prompt_analyze
                    },
                ], session_id, model_id)
                st.session_state.messages_1.append({'title': "商品説明文の生成結果", 'duration': "処理時間：{:.2f}秒".format(duration), 'message': response, 'count': len(st.session_state.messages_1)+1})
        
    
    # for dict in st.session_state.messages_1:
    if len(st.session_state.messages_1) > 0:
        dict = st.session_state.messages_1[-1]
        # st.markdown(f"##### {dict['title']} - 試行 {dict['count']} 回目 \n\n{dict['duration']}")
        st.markdown(f"##### {dict['title']} \n\n{dict['duration']}")
        st.text_area(label="結果", value=dict['message'], height=600)

    st.markdown("---")
    st.markdown("#### インスタグラム案の作成")

    prompt_desc_gen = st.text_area(label="インスタグラム用のPrompt", height=500, 
value=f"""
<your role>あなたは、インスタグラムで商品の紹介をするのが得意なマーケティングのプロフェッショナルです。</your role>
<instruction>
description は商品説明文です。description を踏まえて、インスタグラムへの商品紹介投稿の原稿案を作成してください。
加えてインスタグラムに投稿につけるハッシュタグを10個生成してください。
</instruction>
<description>
{st.session_state.messages_1[-1]['message'] if len(st.session_state.messages_1) > 0 else "※ここに上記の分析結果が入ります。" }
</description>
<constraint>
XMLタグは出力しないでください。
</constraint>
""")

    if st.button("インスタグラム案の作成"):
        response, duration = chat([
            {
                "type": "text",
                "text": prompt_desc_gen
            }
        ], session_id, model_id)
        st.session_state.messages_2.append({'title': "商品説明文、カテゴリ、インスタグラム案", 'duration': "処理時間：{:.2f}秒".format(duration), 'message': response, 'count': len(st.session_state.messages_2)+1})

    if len(st.session_state.messages_2) > 0:
        dict = st.session_state.messages_2[-1]
        # st.markdown(f"##### {dict['title']} - 試行 {dict['count']} 回目 \n\n{dict['duration']}")
        st.markdown(f"##### {dict['title']} \n\n{dict['duration']}")
        st.text_area(label="結果", value=dict['message'], height=600)


    st.markdown("---")
    st.markdown("#### カテゴリ作成")

    prompt_desc_gen = st.text_area(label="カテゴリ生成用のPrompt", height=500, 
value=f"""
<your role>あなたは、Eコマースにおける売場づくりのプロフェッショナルです。</your role>
<instruction>
description は商品説明文です。description を踏まえて、カテゴリを生成してください。
大カテゴリは category を参照し、サブカテゴリは2段階までで自由に生成してください。
5個のカテゴリ案を階層構造で ">" で接続して記載してください。
</instruction>
<description>
{st.session_state.messages_1[-1]['message'] if len(st.session_state.messages_1) > 0 else "※ここに上記の分析結果が入ります。" }
</description>
<constraint>
XMLタグは出力しないでください。
</constraint>
<category>
本
洋書
ミュージック
クラシック
DVD
TVゲーム
PCソフト
パソコン・周辺機器
家電&カメラ
文房具・オフィス用品
ホーム&キッチン
ペット用品
ドラッグストア
ビューティー
食品・飲料・お酒
ベビー&マタニティ
ファッション - レディース
ファッション - メンズ
ファッション - キッズ&ベビー
おもちゃ
ホビー
楽器
スポーツ&アウトドア
車&バイク
DIY・工具・ガーデン
大型家電
クレジットカード
ギフトカード
産業・研究開発用品
</category>
""")

    if st.button("カテゴリ作成"):
        response, duration = chat([
            {
                "type": "text",
                "text": prompt_desc_gen
            }
        ], session_id, model_id)
        st.session_state.messages_3.append({'title': "カテゴリ結果", 'duration': "処理時間：{:.2f}秒".format(duration), 'message': response, 'count': len(st.session_state.messages_3)+1})

    if len(st.session_state.messages_3) > 0:
        dict = st.session_state.messages_3[-1]
        # st.markdown(f"##### {dict['title']} - 試行 {dict['count']} 回目 \n\n{dict['duration']}")
        st.markdown(f"##### {dict['title']} \n\n{dict['duration']}")
        st.text_area(label="結果", value=dict['message'], height=600)


# if __name__ == "__main__":
main()