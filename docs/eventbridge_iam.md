# IAM and Scheduling

## Minimal IAM Policies (attach to Lambda roles)

Inline policy JSON for S3 read/write (adjust bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET",
        "arn:aws:s3:::YOUR_BUCKET/*"
      ]
    }
  ]
}
```

CloudWatch Logs basic execution (AWS managed): `AWSLambdaBasicExecutionRole`.

## EventBridge Schedule (Console)
- Go to EventBridge → Schedules → Create schedule
- Cron: `cron(0 2 * * ? *)` (daily 02:00 UTC)
- Target: your Lambda (simulate or recommend)
- Retry and DLQ: default 