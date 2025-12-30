import json
import os
import logging
from typing import Dict, Any
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'openai.gpt-oss-120b-1:0')
BEDROCK_REGION = os.environ.get('BEDROCK_REGION', 'us-east-1')

bedrock_runtime = boto3.client('bedrock-runtime', region_name=BEDROCK_REGION)

SYSTEM_PROMPT = """You are Pocket Counsel, an expert personal finance advisor AI assistant. Provide practical, actionable financial guidance to help users make better money decisions.

Keep responses concise (2-4 paragraphs). Be friendly, supportive, and non-judgmental. Focus on budgeting, debt management, savings, investment basics, and credit improvement."""


def invoke_bedrock(user_message: str, user_name: str = "there") -> str:
    request_body = {
        "max_tokens": 512,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"User {user_name} asks: {user_message}"
            }
        ]
    }
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Check for OpenAI-style response format (choices[0].message.content)
        if 'choices' in response_body and len(response_body['choices']) > 0:
            content = response_body['choices'][0]['message']['content']
            
            # Remove <reasoning> blocks if present
            if '<reasoning>' in content and '</reasoning>' in content:
                import re
                content = re.sub(r'<reasoning>.*?</reasoning>', '', content, flags=re.DOTALL).strip()
            
            return content
        # Fallback to standard Bedrock format
        elif 'content' in response_body and len(response_body['content']) > 0:
            return response_body['content'][0]['text']
        else:
            logger.error(f"Unexpected Bedrock response format: {response_body}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
            
    except Exception as e:
        logger.error(f"Bedrock invocation error: {e}")
        return "I'm experiencing technical difficulties. Please try again in a moment."


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        body = json.loads(event.get('body', '{}'))
        logger.info(f"Parsed body: {json.dumps(body)}")
        
        telegram_message = body.get('message', {})
        user_message = telegram_message.get('text', '')
        
        from_user = telegram_message.get('from', {})
        user_name = from_user.get('first_name', 'User')
        
        if not user_message:
            logger.warning("No text found in Telegram message")
            return {
                'statusCode': 200,
                'body': json.dumps({'ok': True})
            }
        
        logger.info(f"Processing message from {user_name}: {user_message}")
        
        response_text = invoke_bedrock(user_message, user_name)
        
        logger.info(f"Bedrock response: {response_text}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'ok': True,
                'message': user_message,
                'response': response_text,
                'user': user_name
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return {
            'statusCode': 200,
            'body': json.dumps({'ok': True})
        }
