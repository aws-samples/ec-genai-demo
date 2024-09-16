import {
  aws_cloudfront as cloudfront,
  aws_cloudfront_origins as origins,
} from 'aws-cdk-lib';
import { ApplicationLoadBalancer } from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { Construct } from 'constructs';


export interface cfProps {
  loadBalancer: ApplicationLoadBalancer;
}

export class cf extends Construct {
  public domainName: string;

  constructor(scope: Construct, id: string, props: cfProps) {
    super(scope, id);
    const { loadBalancer } = props;

    // CloudFront
    const EcGenaiDemoCF = new cloudfront.Distribution(this, 'EcGenaiDemoCF', {
      defaultBehavior: {
        origin: new origins.LoadBalancerV2Origin(loadBalancer, {
          protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
      },
      comment: 'EC x GenAI',
    });

    this.domainName = EcGenaiDemoCF.domainName;

  }
}