import json
import boto3
from boto3.dynamodb.conditions import Key

# Initialize the DynamoDB connection
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SmartFarm_Data')        #Name of my DynamoDB Table 

def lambda_handler(event, context):
    try:
        # Query the table for our specific device
        response = table.query(                 #Quick path finding method...
            KeyConditionExpression=Key('device_id').eq('SmartFarm_Pi_01'),      #(Partittion key) & (Thing in IoT Core)
            Limit=5,          # Just get the last 5 readings
            ScanIndexForward=False # Get newest readings first
        )
        
        items = response.get('Items', [])

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # Important for Web Front-ends!
            },
            'body': json.dumps(items, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
    

    #boto3: This is the standard Python library for talking to AWS services.
    #table.query: This is much faster and cheaper than "scanning" the whole table. It goes straight to the SmartFarm_Pi_01 "folder."
    #ScanIndexForward=False: Since we used timestamp as our Sort Key, setting this to False tells AWS to give us the latest data first.
    #Access-Control-Allow-Origin: This is a "CORS" header. Without this, your future website will be blocked by the browser for security reasons.
    