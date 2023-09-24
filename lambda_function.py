import json
import boto3
import botocore

s3 = boto3.resource('s3')
client = boto3.client('s3')
ses = boto3.client('ses')  

def lambda_handler(event, context):
    offending = []
    for bucket in s3.buckets.all():
        try:
            bucket_policy = client.get_bucket_policy(Bucket=bucket.name)
            bucket_policy_j = json.loads(bucket_policy["Policy"])
            for statement in bucket_policy_j["Statement"]:
                if (statement["Effect"] == "Allow" and
                    statement["Principal"] == "*" ):
                        pretty_statement = json.dumps(statement, indent=4, sort_keys=True)
                        offending.append("%s: %s" % (bucket.name, pretty_statement))
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                pass
            else:
                print("Unexpected error on %s: %s" % (bucket.name, e))

    if offending:
        msg = '\n\n'.join(offending)
    else:
        msg = "Could not find any buckets granting public access"

    send_email_notification(msg)

def send_email_notification(message):
    # Replace with your SES configuration
    sender_email = 'aws@xyz.com'
    recipient_email = 'audit@xyz.com'
    subject = 'S3 Public Access Granted'

    try:
        email_body = f"Public access has been detected in your S3 buckets:\n\n{message}"
        
        response = ses.send_email(
            Source=sender_email,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': email_body}}
            }
        )

        print(f"Email sent successfully. Message ID: {response['MessageId']}")

    except Exception as e:
        print(f"Error sending email: {str(e)}")

