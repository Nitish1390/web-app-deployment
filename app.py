import boto3
import time

# Initialize clients
s3_client = boto3.client('s3')
ec2_client = boto3.client('ec2')
elbv2_client = boto3.client('elbv2')
autoscaling_client = boto3.client('autoscaling')
sns_client = boto3.client('sns')

# Step 1: Web Application Deployment

# 1.1 Create S3 Bucket
bucket_name = 'your-unique-bucket-name'
s3_client.create_bucket(Bucket=bucket_name)
print(f"S3 Bucket '{bucket_name}' created successfully.")

# 1.2 Launch EC2 Instance and Configure as a Web Server
instance_params = {
    'ImageId': 'nitish-web-app-deployment',
    'InstanceType': 't2.micro',
    'KeyName': 'Nitish13',
    # Add other parameters as needed
}

response = ec2_client.run_instances(**instance_params)
instance_id = response['Instances'][0]['InstanceId']
print(f"EC2 Instance '{instance_id}' launched successfully.")

# Wait for the instance to be running
ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])
print(f"EC2 Instance '{instance_id}' is now running.")

# Step 2: Load Balancing with ELB

# 2.1 Deploy Application Load Balancer (ALB)
alb_params = {
    'Name': 'nitish-alb',
    'Subnets': ['subnet-005ec39a066648bdc'],  # Specify your subnets
    'SecurityGroups': ['sg-03a0a98fe163a64bb'],
    'Scheme': 'internet-facing',
}

alb_response = elbv2_client.create_load_balancer(**alb_params)
alb_arn = alb_response['LoadBalancers'][0]['LoadBalancerArn']
print(f"ALB {alb_arn} created successfully.")

# 2.2 Register EC2 Instance(s) with ALB
target_group_params = {
    'Name': 'nitish-web-lb',
    'Protocol': 'HTTP',
    'Port': 80,
    'VpcId': 'your-vpc-id',
}

target_group_response = elbv2_client.create_target_group(**target_group_params)
target_group_arn = target_group_response['TargetGroups'][0]['TargetGroupArn']

elbv2_client.register_targets(TargetGroupArn=target_group_arn, Targets=[{'Id': instance_id}])
elbv2_client.create_listener(
    DefaultActions=[{'Type': 'fixed-response', 'FixedResponseConfig': {'ContentType': 'text/plain', 'StatusCode': '200'}}],
    LoadBalancerArn=alb_arn,
    Port=80,
    Protocol='HTTP'
)

print(f"EC2 Instance {instance_id} registered with ALB {alb_arn}.")

# Step 3: Auto Scaling Group Configuration

# 3.1 Create Auto Scaling Group
launch_config_params = {
    'LaunchConfigurationName': 'nitish-web-app-deployment',
    'ImageId': 'ami-02a2af70a66af6dfb',
    'InstanceType': 't2.micro',
    'KeyName': 'Nitish13',
    # Add other parameters as needed
}

autoscaling_client.create_launch_configuration(**launch_config_params)

asg_params = {
    'AutoScalingGroupName': 'nitish-asg',
    'LaunchConfigurationName': 'nitish-web-app-deployment',
    'MinSize': 1,
    'MaxSize': 3,
    'DesiredCapacity': 1,
    'VPCZoneIdentifier': 'subnet-005ec39a066648bdc',  # Specify your subnets
    'Tags': [{'Nitish13': 'Name', 'Value': 'nitish-asg', 'PropagateAtLaunch': True}],
}

autoscaling_client.create_auto_scaling_group(**asg_params)
print(f"ASG {asg_params['AutoScalingGroupName']} created successfully.")

# 3.2 Configure Scaling Policies
scaling_policy_params = {
    'AutoScalingGroupName': 'nitish-asg',
    'PolicyName': 'nitish-asg-policy',
    'PolicyType': 'TargetTrackingScaling',
    'EstimatedInstanceWarmup': 300,
    'TargetTrackingConfiguration': {
        'PredefinedMetricSpecification': {'PredefinedMetricType': 'ASGAverageCPUUtilization'},
        'TargetValue': 70,
    },
}

autoscaling_client.put_scaling_policy(**scaling_policy_params)
print(f"Scaling policy {scaling_policy_params['PolicyName']} configured.")

# Step 4: Lambda-based Health Checks & Management
# Assume you have a Lambda function code for health checks

# Step 5: S3 Logging & Monitoring

# 5.1 Configure ALB Logging to S3
# Assume you have an S3 bucket created for storing logs

# 5.2 Create a Lambda Function for Log Analysis
# Assume you have a Lambda function code for log analysis

# Step 6: SNS Notifications

# 6.1 Set Up SNS Topics
health_issues_topic = sns_client.create_topic(Name='HealthIssuesTopic')
scaling_events_topic = sns_client.create_topic(Name='ScalingEventsTopic')
high_traffic_topic = sns_client.create_topic(Name='HighTrafficTopic')
print("SNS topics created successfully.")

import boto3

# Initialize SNS client
sns_client = boto3.client('sns')

# Step 6.2: Integrate SNS with Lambda

# Assume you have Lambda function ARNs or names for health issues, scaling events, and high traffic

# Lambda function for health issues
health_lambda_arn = 'your-health-lambda-function-arn'
sns_health_topic_arn = sns_client.create_topic(Name='HealthIssuesTopic')['TopicArn']

# Lambda function for scaling events
scaling_lambda_arn = 'your-scaling-lambda-function-arn'
sns_scaling_topic_arn = sns_client.create_topic(Name='ScalingEventsTopic')['TopicArn']

# Lambda function for high traffic
high_traffic_lambda_arn = 'your-high-traffic-lambda-function-arn'
sns_high_traffic_topic_arn = sns_client.create_topic(Name='HighTrafficTopic')['TopicArn']

# Subscribe Lambda functions to SNS topics
sns_client.subscribe(
    TopicArn=sns_health_topic_arn,
    Protocol='lambda',
    Endpoint=health_lambda_arn
)

sns_client.subscribe(
    TopicArn=sns_scaling_topic_arn,
    Protocol='lambda',
    Endpoint=scaling_lambda_arn
)

sns_client.subscribe(
    TopicArn=sns_high_traffic_topic_arn,
    Protocol='lambda',
    Endpoint=high_traffic_lambda_arn
)

print("Lambda functions subscribed to SNS topics successfully.")

