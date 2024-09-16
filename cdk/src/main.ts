import * as cdk from 'aws-cdk-lib';
import {
  App,
  Stack,
  StackProps,
  aws_iam as iam,
  aws_ec2 as ec2,
} from 'aws-cdk-lib';
import { PolicyStatement, Effect } from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { AlbEcs } from './constructs/alb-ecs';
import { cf } from './constructs/cloudfront';

export class EcGenaiDemo extends Stack {
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);

    // vpc with private subnet
    const vpc = new ec2.Vpc(this, 'EcGenaiDemoVpc', {
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
      natGateways: 1,
      maxAzs: 2,
    });
    const privateSubnets = vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    });

    //// VPC Endpoint for private ECS
    // vpc.addInterfaceEndpoint('ecr-endpoint', {
    //   service: ec2.InterfaceVpcEndpointAwsService.ECR,
    // });
    // vpc.addInterfaceEndpoint('ecr-dkr-endpoint', {
    //   service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
    // });
    // vpc.addInterfaceEndpoint('logs-endpoint', {
    //   service: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
    // });
    // vpc.addGatewayEndpoint('s3-endpoint', {
    //   service: ec2.GatewayVpcEndpointAwsService.S3,
    //   subnets: [privateSubnets],
    // });
    // vpc.addInterfaceEndpoint('bedrock-endpoint', {
    //   service: ec2.InterfaceVpcEndpointAwsService.BEDROCK,
    // });
    // vpc.addInterfaceEndpoint('bedrock-runtime-endpoint', {
    //   service: ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
    // });

    // IAM Role which has Bedrock policy
    const bedrockAccessPolicy = new PolicyStatement({
      effect: Effect.ALLOW,
      // See: https://docs.aws.amazon.com/ja_jp/service-authorization/latest/reference/list_amazonbedrock.html
      actions: ['bedrock:InvokeModel'],
      resources: ['*'],
    });

    // create IAM Role
    const role = new iam.Role(this, 'EcGenaiDemoRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });
    role.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('TranslateFullAccess'),
    );
    role.addToPolicy(bedrockAccessPolicy);

    const albEcs = new AlbEcs(this, 'ecs-service', {
      vpc: vpc,
      role: role,
      selectedSubnets: privateSubnets,
    });

    const cloudFront = new cf(this, 'CloudFront', {
      loadBalancer: albEcs.loadBalancer,
    });

    new cdk.CfnOutput(this, 'ECxGenAI Demo URL', {
      value: 'https://'+cloudFront.domainName,
    });
  }
}

// for development, use account/region from cdk cli
const prodEnv = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
};

const app = new App();

// new EcGenaiDemo(app, 'cdk-dev', { env: devEnv });
// new EcGenaiDemo(app, 'cdk-prod', { env: prodEnv });
new EcGenaiDemo(app, 'ec-genai-demo', { env: prodEnv });

app.synth();
