## デプロイ
>> [!IMPORTANT]  
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