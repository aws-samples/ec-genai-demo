import json
import boto3
import os
import base64
import io
from PIL import Image

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

class BedrockAPI:
    def __init__(self):
        self.client = boto3.client(service_name="bedrock-runtime", region_name=os.environ['region'])

    def proofread_desc_message(
        self, 
        generated_desc, 
        review_text,
        system_prompt = "商品画像と商品説明文と入力されたテキストを比較して誤りがあれば指摘してください。商品画像や商品説明文とは異なる説明がされている可能性があります。",
        max_tokens = 1000,
        top_p = 0.5,
        top_k = 10,
        stop_sequences = [],
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        content = []

        if generated_desc is not None and len(generated_desc) != 0:
            content.append(
                {
                    "type": "text",
                    "text": f"生成されたお客様メッセージは以下の通りです。<お客様メッセージ>{generated_desc}</お客様メッセージ>" 
                }
            )

        if review_text is not None and len(review_text) != 0:
            content.append(
                {
                    "type": "text",
                    "text": f"上記お客様メッセージのレビュー結果は以下の通りです。<レビュー結果>{review_text}</レビュー結果>" 
                }
            )

        messages = [
            {
                "role": "user",
                "content": content
            }, {
                "role": "assistant", 
                "content": [{
                    "type": "text",
                    "text": "<"
                }]
            }
        ]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "top_p": top_p,
            "top_k": top_k,
            "stop_sequences": stop_sequences,
            "messages": messages
        }
        
        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId=modelId,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return "<" + response_body["content"][0]["text"]

    def review_user_message(
        self, 
        item_image, 
        item_desc, 
        generated_desc,
        system_prompt = "商品画像と商品説明文と入力されたテキストを比較して誤りがあれば指摘してください。商品画像や商品説明文とは異なる説明がされている可能性があります。",
        max_tokens = 1000,
        top_p = 0.5,
        top_k = 10,
        stop_sequences = [],
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        content = []

        if item_image is not None:
            content.append(
                {
                    "type": "text",
                    "text": f"商品画像は以下の通りです。" 
                }
            )
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": ImageProcessor.convert_image_to_base64(item_image)
                    }
                }
            )
        if item_desc is not None and len(item_desc) != 0:
            content.append(
                {
                    "type": "text",
                    "text": f"商品説明文は以下の通りです。<商品説明文>{item_desc}</商品説明文>" 
                }
            )
        if generated_desc is not None and len(generated_desc) != 0:
            content.append(
                {
                    "type": "text",
                    "text": f"生成されたお客様メッセージは以下の通りです。<お客様メッセージ>{generated_desc}</お客様メッセージ>" 
                }
            )

        messages = [
            {
                "role": "user",
                "content": content
            }
        ]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "top_p": top_p,
            "top_k": top_k,
            "stop_sequences": stop_sequences,
            "messages": messages
        }
        
        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId=modelId,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]

    def get_item_desc_message(
        self, 
        item_image, 
        item_desc, 
        system_prompt = "あなたは商品説明のプロです。お客様の年齢や趣味、性別に合わせて商品の良さを説明してください。",
        max_tokens = 1000,
        top_p = 0.5,
        top_k = 10,
        stop_sequences = [],
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        content = []

        if item_image is not None:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": ImageProcessor.convert_image_to_base64(item_image)
                    }
                }
            )
        if item_desc is not None and len(item_desc) != 0:
            content.append(
                {
                    "type": "text",
                    "text": item_desc
                }
            )

        messages = [
            {
                "role": "user",
                "content": content
            }
        ]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "top_p": top_p,
            "top_k": top_k,
            "stop_sequences": stop_sequences,
            "messages": messages
        }
        
        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId=modelId,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]

        
    def get_compare_message(
        self, 
        left_image, 
        left_text, 
        right_image, 
        right_text, 
        system_prompt = "あなたは商品を推薦する目利きの担当者です。2 つの商品が提示されるので、共通点と相違点をまとめてください。日本語語で回答してください。",
        max_tokens = 1000,
        top_p = 0.5,
        top_k = 10,
        stop_sequences = [],
        modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        content = []
        if left_image is not None:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": ImageProcessor.convert_image_to_base64(left_image)
                    }
                }
            )
        if left_text is not None and len(left_text) != 0:
            content.append(
                {
                    "type": "text",
                    "text": left_text
                }
            )
        
        if right_image is not None:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": ImageProcessor.convert_image_to_base64(right_image)
                    }
                }
            )
            
        if right_text is not None and len(right_text) != 0:
            content.append(
                {
                    "type": "text",
                    "text": right_text
                }
            )

        messages = [
            {
                "role": "user",
                "content": content
            }
        ]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "top_p": top_p,
            "top_k": top_k,
            "stop_sequences": stop_sequences,
            "messages": messages
        }
        
        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId=modelId,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]

    def get_vector_titan_multi_modal(self, image, text):
        # MAX image size supported is 2048 * 2048 pixels
        if image is None and text is None:
            return []
        if not image and not text:
            return []
            
        # You can specify either text or image or both
        body = {
            "embeddingConfig": {
                "outputEmbeddingLength": 1024
            }
        }
        
        if text: 
            body["inputText"] = text
        if image:
            body["inputImage"] = ImageProcessor.convert_image_to_base64(image)

        response = self.client.invoke_model(
            body=json.dumps(body),
            modelId="amazon.titan-embed-image-v1",
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        return embedding
    