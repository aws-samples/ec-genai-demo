import { Stack } from 'aws-cdk-lib';
import { NagSuppressions } from 'cdk-nag';

export function applySuppressions(stack: Stack): void {
  NagSuppressions.addStackSuppressions(stack, [
    {
      id: 'AwsSolutions-CFR1',
      reason: 'Geo restrictions is not required',
    },
    {
      id: 'AwsSolutions-CFR2',
      reason: 'WAF is not required because this solution does not have database',
    },
    {
      id: 'AwsSolutions-VPC7',
      reason: 'VPC Flow log is not required',
    },
    {
      id: 'AwsSolutions-IAM4',
      reason: 'TranslateFullAccess is ok to use as managed policy',
      appliesTo: ['Policy::arn:<AWS::Partition>:iam::aws:policy/TranslateFullAccess'],
    },
    {
      id: 'AwsSolutions-IAM5',
      appliesTo: ['Action::bedrock:InvokeModel', 'Resource::*'],
      reason: 'Necessary to grant invokemodel access to all models in the bedrock',
    },
    {
      id: 'AwsSolutions-ECS4',
      reason: 'ContainerInsights is no required for current use case',
    },
    {
      id: 'AwsSolutions-ECS2',
      reason: 'env is only used for region',
    },
    {
      id: 'AwsSolutions-ELB2',
      reason: 'Access log is not required for current use case',
    },
    {
      id: 'AwsSolutions-CFR3',
      reason: 'Access log is not required for current use case',
    },
    {
      id: 'AwsSolutions-CFR4',
      reason: 'custom certification is required for this issue workaround',
    },
    {
      id: 'AwsSolutions-CFR5',
      reason: 'custom certification is required for this issue workaround',
    },
  ]);
}