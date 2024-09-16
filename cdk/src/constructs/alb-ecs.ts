import * as cdk from 'aws-cdk-lib';
import {
  aws_iam as iam,
  aws_ec2 as ec2,
  aws_ecs as ecs,
  aws_ecs_patterns as ecsPattens,
} from 'aws-cdk-lib';
import { Peer, Port } from 'aws-cdk-lib/aws-ec2';
import { ApplicationLoadBalancer } from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';


export interface AlbEcsProps {
  vpc: ec2.Vpc;
  role: iam.Role;
  selectedSubnets: ec2.SelectedSubnets;
}

export class AlbEcs extends Construct {
  public loadBalancer: ApplicationLoadBalancer;
  constructor(scope: Construct, id: string, props: AlbEcsProps) {
    super(scope, id);
    const { vpc, role, selectedSubnets } = props;

    // create ECS cluster
    const cluster = new ecs.Cluster(this, 'EcGenaiDemoCluster', {
      vpc,
    });

    // ECS Task Definition
    const taskDef = new ecs.FargateTaskDefinition(this, 'EcGenaiDemoTaskDef', {
      cpu: 8192,
      memoryLimitMiB: 16384,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
      },
      taskRole: role,
    });

    taskDef.addContainer('EcGenaiDemoContainer', {
      image: ecs.ContainerImage.fromAsset('../src/', {
        platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64,
      }),
      portMappings: [{ containerPort: 8501 }],
      logging: ecs.LogDriver.awsLogs({ streamPrefix: 'ecs' }),
      environment: {
        region: this.node.tryGetContext('region'),
      },
    });


    // ALB + ECS Service
    const albEcs = new ecsPattens.ApplicationLoadBalancedFargateService(
    // new ecsPattens.ApplicationLoadBalancedFargateService(
      this,
      'EcGenaiDemoService',
      {
        cluster,
        cpu: 1024,
        memoryLimitMiB: 4096,
        desiredCount: 2, // 2以上にするにはSticky sessionが必要
        taskDefinition: taskDef,
        taskSubnets: {
          subnets: selectedSubnets.subnets,
        },
        loadBalancerName: 'EcGenaiDemoALB',
        openListener: false,
      },
    );
    // SecurityGroup for ALB which can be only accessed by CloudFront managed prefix list
    const sg = new ec2.SecurityGroup(this, 'SecurityGroup', {
      vpc: vpc,
    });
    // sg.connections.allowFrom(Peer.prefixList('pl-58a04531'), Port.HTTP); // Allow from Tokyo Region CloudFront IP prefix
    sg.connections.allowFrom(Peer.ipv4('0.0.0.0/0'), Port.HTTP); // Allow from all ip with HTTP
    albEcs.loadBalancer.addSecurityGroup(sg);
    NagSuppressions.addResourceSuppressions(sg, [
      {
        id: 'AwsSolutions-EC23',
        reason: 'ALB is open for all ip with HTTP',
      },
    ]);

    albEcs.targetGroup.enableCookieStickiness(cdk.Duration.minutes(1440)); // Sticky Session

    albEcs.targetGroup.configureHealthCheck({
      path: '/',
      port: '8501',
      timeout: cdk.Duration.seconds(30),
      interval: cdk.Duration.seconds(45),
    });
    albEcs.targetGroup.setAttribute('deregistration_delay.timeout_seconds', '10'); // for faster deployment
    this.loadBalancer = albEcs.loadBalancer;
  }
}