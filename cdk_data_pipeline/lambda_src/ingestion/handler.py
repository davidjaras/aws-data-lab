import io
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime

import boto3
import pandas as pd

S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX")
API_RESULTS_COUNT = int(os.getenv("API_RESULTS_COUNT", "100"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

API_URL = f"https://randomuser.me/api/?results={API_RESULTS_COUNT}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
}

s3 = boto3.client("s3")


def get_nested_value(data, path, default=None):
    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def flatten_user(user):
    return {
        "gender": get_nested_value(user, "gender"),
        "title": get_nested_value(user, "name.title"),
        "first_name": get_nested_value(user, "name.first"),
        "last_name": get_nested_value(user, "name.last"),
        "street_number": get_nested_value(user, "location.street.number"),
        "street_name": get_nested_value(user, "location.street.name"),
        "city": get_nested_value(user, "location.city"),
        "state": get_nested_value(user, "location.state"),
        "country": get_nested_value(user, "location.country"),
        "postcode": str(get_nested_value(user, "location.postcode")),
        "latitude": get_nested_value(user, "location.coordinates.latitude"),
        "longitude": get_nested_value(user, "location.coordinates.longitude"),
        "timezone_offset": get_nested_value(user, "location.timezone.offset"),
        "timezone_description": get_nested_value(user, "location.timezone.description"),
        "email": get_nested_value(user, "email"),
        "phone": get_nested_value(user, "phone"),
        "cell": get_nested_value(user, "cell"),
        "uuid": get_nested_value(user, "login.uuid"),
        "username": get_nested_value(user, "login.username"),
        "dob_date": get_nested_value(user, "dob.date"),
        "age": get_nested_value(user, "dob.age"),
        "registered_date": get_nested_value(user, "registered.date"),
        "id_name": get_nested_value(user, "id.name"),
        "id_value": get_nested_value(user, "id.value"),
        "picture_large": get_nested_value(user, "picture.large"),
        "picture_medium": get_nested_value(user, "picture.medium"),
        "picture_thumbnail": get_nested_value(user, "picture.thumbnail"),
        "nationality": get_nested_value(user, "nat"),
        "processed_at": datetime.now().isoformat(),
    }


def fetch_api_data(url, timeout=API_TIMEOUT):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.getcode() != 200:
                raise urllib.error.HTTPError(
                    url, response.getcode(), f"HTTP {response.getcode()}", None, None
                )

            data = response.read()
            return json.loads(data.decode("utf-8"))

    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        raise Exception(f"API request failed: {str(e)}")


def generate_s3_key(execution_key):
    now = datetime.now()
    request_id = uuid.uuid4().hex

    return (
        f"{S3_PREFIX}/execution_key={execution_key}/"
        f"year={now.year}/month={now.month:02d}/day={now.day:02d}/"
        f"request_id={request_id}.parquet"
    )


def upload_to_s3(bucket, key, data):
    try:
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)

        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/vnd.apache.parquet",
        )

        return f"s3://{bucket}/{key}"

    except Exception as e:
        raise Exception(f"S3 upload failed: {str(e)}")


def lambda_handler(event, context):
    if not S3_BUCKET:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing S3_BUCKET environment variable"}),
        }

    try:
        execution_key = (event or {}).get("execution_key") or "lambda"

        api_response = fetch_api_data(API_URL)
        users = api_response.get("results", [])

        if not users:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No users found", "users_processed": 0}),
            }

        flattened_users = [flatten_user(user) for user in users]

        s3_key = generate_s3_key(execution_key)
        s3_location = upload_to_s3(S3_BUCKET, s3_key, flattened_users)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Success",
                    "users_processed": len(users),
                    "s3_location": s3_location,
                    "key": s3_key,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Processing failed", "details": str(e)}),
        }
