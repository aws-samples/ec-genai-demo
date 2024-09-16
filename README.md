# ec-genai-demo: E コマースにおける生成AI 4大ユースケースデモ 

本デモでは、以下の E コマースにおける代表的な生成AIの 4 つのユースケースについて、 Amazon Bedrock とその上で利用可能なモデルを利用した実装をお試しいただけます。  

細かな解説は以下のブログもご参照ください。  
紹介ブログ：[生成 AI で加速する e コマースの変革 その 2 – AWS Summit Japan 2024 で展示した Amazon Bedrock デモの解説 | Amazon Web Services ブログ](https://aws.amazon.com/jp/blogs/news/aws-summit-2024-retail-cpg-ec-genai-bedrock-demo-architecture/)

![alt text](./img/streamlit-image.png)


## 機能紹介
次の 4 つのユースケースについての Amazon Bedrock によるデモ実装が含まれます。  

![alt text](img/usecase.png)

### デモ
こちらのデモについて 2024/7/24 の AWS Expert Online  for JAWS-UG #34 にて、動画付きで紹介しました。  
[!['デモ動画'](https://img.youtube.com/vi/6Ud6GgnrU6o/0.jpg)](https://youtu.be/6Ud6GgnrU6o?t=840)


## アーキテクチャ
アーキテクチャは非常にシンプルで、Amazon ECS 上に Steamlit で実装された簡易的な Web アプリケーションがデプロイされており、CloudFront -> Application Load Balancer 経由 で HTTPS にてアクセスが可能です。

Steamlit 上の Python スクリプトにより、Amazon Bedrock の API を呼び出し、各種生成 AI のプロンプト実行と結果の取得を行います。
モデルは、画像生成には Amazon Titan Image Generator G1、テキスト処理の LLM には Anthropic Claude 3/3.5 Sonnet/Haiku、検索時のベクトル化（Embedding）には、 Amazon Titan Multimodal Embeddings G1 を Amazon Bedrock の API から利用しています。

![picture 1](./img/Architecture.png)  


## デプロイ
> [!IMPORTANT]  
> このリポジトリでは、Amazon Bedrock のモデルとしてオレゴンリージョン (us-west-2) の以下モデルを利用する設定になっています。  
> - Amazon
>   - Titan Image Generator G1
>   - Titan Multimodal Embeddings G1
> - Anthropic 
>   - Claude 3.5 Sonnet
>   - Claude 3 Sonnet
>   - Claude 3 Haiku  
> 
> 事前に本サンプルをデプロイするアカウントにて、[Model access 画面 (us-west-2)](https://us-west-2.console.aws.amazon.com/bedrock/home?region=us-west-2#/modelaccess)を開き、モデルアクセスにチェックして Save changes してください。


デプロイには [AWS Cloud Development Kit](https://aws.amazon.com/jp/cdk/)（以降 CDK）と [Projen](https://github.com/projen/projen) を利用します。  

> [!IMPORTANT]  
> Projen と CDK については以下 AWS ブログも参考にしてください。  
> https://aws.amazon.com/jp/blogs/news/getting-started-with-projen-and-aws-cdk/  

CDK を利用したことがない場合、初回のみ [Bootstrap](https://docs.aws.amazon.com/ja_jp/cdk/v2/guide/bootstrapping.html) 作業が必要です。  
※すでに Bootstrap された環境では以下のコマンドは不要です。

```bash
npx cdk bootstrap
```

続いて、以下のコマンドで`cdk`ディレクトリに移動し、セットアップします。  

```bash
cd cdk

npx projen install
```

以下コマンドで、AWS リソースをデプロイします。デプロイが完了するまで、お待ちください。  
※大体15分ほどかかります。  
```bash
npx projen build
npx projen deploy
```

## 開発
ローカル環境にて、コンテナか poetry にて環境構築が可能です。  
ローカル環境からは、Amazon Bedrock や Amazon Translate を呼び出せる権限を持っている必要があります  

### ローカルのコンテナで動かす場合

環境変数でアクセスキーを設定

```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
```

Docker composeにて起動
```bash
cd src
docker compose up
```

### ローカルの poetry で動かす場合

> [!IMPORTANT]  
> pythonバージョンは poetry の `pyproject.toml` にあるように、 `">=3.12,<3.13"` を前提としています。  
> poetry の仮想環境機能を利用するため、既存の Python とは衝突しません。 

以下のように poetry で環境構築が可能です。  
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

## Requests & Issues
ご要望や問題があれば [Issue](https://github.com/aws-samples/ec-genai-demo/issues) に起票をお願いします。  

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

