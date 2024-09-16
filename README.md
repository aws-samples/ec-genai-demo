# Eコマースにおける生成AI 4大ユースケースデモ

本デモでは、以下の  コマースにおいて代表的な生成AIの 4 つのユースケースについて、 Amazon Bedrock とその上で利用可能なモデルを利用した実装をお試しいただけます。

紹介ブログ：https://aws.amazon.com/jp/blogs/news/aws-summit-2024-retail-cpg-ec-genai-bedrock-demo-architecture/

![alt text](./img/streamlit-image.png)


## 機能紹介
次の 4 つのユースケースについての Amazon Bedrock によるデモ実装が含まれます。  
![alt text](img/usecase.png)

機能の細かい解説はブログを参照ください。  
紹介ブログ：https://aws.amazon.com/jp/blogs/news/aws-summit-2024-retail-cpg-ec-genai-bedrock-demo-architecture/

## アーキテクチャ
アーキテクチャは非常にシンプルで、Amazon ECS 上に Steamlit で実装された簡易的な Web アプリケーションがデプロイされており、HTTP/S にてアクセスが可能です。

Steamlit 上の Python スクリプトにより、Amazon Bedrock の API を呼び出し、各種生成 AI のプロンプト実行と結果の取得を行います。
モデルは、画像生成には Amazon Titan Image Generator G1、テキスト処理の LLM には Anthropic Claude 3 Haiku、検索時のベクトル化（Embedding）には、 Amazon Titan Multimodal Embeddings G1 を Amazon Bedrock の API から利用しています。

![picture 1](./img/Architecture.png)  

## デプロイ
> [!IMPORTANT]  
> このリポジトリでは、デフォルトのモデルとしてオレゴンリージョン (us-west-2) の以下モデルを利用する設定になっています。  
> - Amazon
>   - Titan Image Generator G1
>   - Titan Multimodal Embeddings G1
> - Anthropic 
>   - Claude 3.5 Sonnet
>   - Claude 3 Sonnet
>   - Claude 3 Haiku  
> 
> [Model access 画面 (us-east-1)](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/modelaccess)を開き、モデルアクセスにチェックして Save changes してください。


デプロイには [AWS Cloud Development Kit](https://aws.amazon.com/jp/cdk/)（以降 CDK）と[Projen](https://github.com/projen/projen)をを利用します。  

> [!IMPORTANT]  
> Projen と CDK については以下 AWS ブログも参考にしてください。  
> https://aws.amazon.com/jp/blogs/news/getting-started-with-projen-and-aws-cdk/  

CDK を利用したことがない場合、初回のみ [Bootstrap](https://docs.aws.amazon.com/ja_jp/cdk/v2/guide/bootstrapping.html) 作業が必要です。すでに Bootstrap された環境では以下のコマンドは不要です。

```bash
npx cdk bootstrap
```

続いて、以下のコマンドで`cdk`ディレクトリに移動し、セットアップします。  

```bash
cd cdk

npx projen install
```

AWS リソースをデプロイします。デプロイが完了するまで、お待ちください。  

```bash
npx projen build
npx projen deploy
```

## 開発

### ローカルのコンテナで動かす場合

環境変数でアクセスキー, region を設定

```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_SESSION_TOKEN=xxx
```

Docker composeにて起動
```bash
cd src
docker compose up
```

### ローカルで動かす場合

> [!IMPORTANT]  
>pythonバージョンは `">=3.11,<3.12"` である必要があります  
>Amazon Bedrock や Amazon Translate を呼び出せる権限を持っている必要があります  

poetry で環境構築が可能です。  
```
poetry config virtualenvs.in-project true
poetry install

# .venvで仮想環境が利用可能です。
source .venv/bin/activate
```

`.env.example` ファイルを `.env` にリネームし、AWS の認証情報を設定します。
```
# EC2 や Cloud9 の IAM ロールを利用する場合は .env の設定は不要です
cp .env.example .env
```

環境構築後、以下のコマンドで Streamlit を起動します。

```
source .venv/bin/activate
region=us-west-2 poetry run streamlit run app.py
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

