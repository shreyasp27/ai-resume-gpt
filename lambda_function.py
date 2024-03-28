import json
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent


def lambda_handler(event: APIGatewayProxyEvent, context):
           
    answer = "lambda is working"

    response = {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json"
    },
    "body": json.dumps({"answer": answer})
    }

    return response