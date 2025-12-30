# Pocket Counsel - Personal Finance AI Advisor

AWS CDK project that deploys a personal finance AI advisor powered by AWS Bedrock.

## Phase 1: Minimal Core Stack (Current)

This phase deploys the minimal infrastructure for testing:
- Lambda function with Bedrock integration
- IAM permissions for Bedrock API
- CloudWatch Logs

**Note:** Telegram integration removed temporarily for testing. Lambda accepts simple JSON events.

## Prerequisites

- AWS Account with Bedrock access in us-east-1
- Python 3.12+
- AWS CLI configured

## Setup

1. **Create virtual environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Bootstrap CDK** (first time only):
```bash
cdk bootstrap
```

## Deployment

```bash
cdk deploy
```

**Outputs:**
- `CoreLambdaArn`: Lambda function ARN
- `CoreLambdaName`: Lambda function name

## Testing

### Option 1: AWS Console
1. Go to AWS Lambda Console
2. Find your function (name from outputs)
3. Go to "Test" tab
4. Create test event with:
```json
{
  "message": "How should I start budgeting?",
  "user_name": "David"
}
```
5. Click "Test"

### Option 2: AWS CLI
```bash
aws lambda invoke \
  --function-name <FUNCTION_NAME> \
  --payload '{"message":"How should I start budgeting?","user_name":"David"}' \
  response.json

cat response.json
```

### Option 3: Use test-event.json
```bash
aws lambda invoke \
  --function-name <FUNCTION_NAME> \
  --payload file://test-event.json \
  response.json
```

### Expected Response
```json
{
  "statusCode": 200,
  "body": "{\"message\":\"How should I start budgeting?\",\"response\":\"<AI response here>\",\"user\":\"David\"}"
}
```

## Important: Enable Bedrock Model Access

Before testing, enable meta.llama4-maverick-17b-instruct-v1:0 in AWS Console:
1. Go to AWS Bedrock Console
2. Click "Model access" in left menu
3. Click "Enable specific models"
4. Enable "meta.llama4-maverick-17b-instruct-v1:0"
5. Wait for approval (usually instant)

## View Logs

```bash
aws logs tail /aws/lambda/<FUNCTION_NAME> --follow
```

## Next Steps

- Phase 2: Add Telegram integration
- Phase 3: Add API Gateway for webhook endpoint
- Phase 4: Add S3 bucket for knowledge base
- Phase 5: Enhanced prompts and features

## Cleanup

```bash
cdk destroy
```
