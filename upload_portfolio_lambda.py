from io import BytesIO
import zipfile
import boto3
import mimetypes


def lambda_handler(event, context):

    sns = boto3.resource('sns')
    topic= sns.Topic('arn:aws:sns:us-east-1:384247156835:portfolio-deploy-topic')

    location = {
        "bucketName": "portfolio.build.sudiptobasak",
        "objectKey": "portfoliobuild.zip"
    }

    try:

        job = event.get("CodePipeline.job")
        #print("Codepipeline JobId: {}".format(job["id"]))
        #print(str(job))

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "BuildArtifact":
                    location = artifact["location"]["s3Location"]
                    print(str(location))

        print("Building portfolio from: {}".format(str(location)))

        s3 = boto3.resource('s3')

        build_bucket = s3.Bucket(location["bucketName"])
        portfolio_bucket = s3.Bucket('portfolio.sudiptobasak')

        portfolio_zip = BytesIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for name in myzip.namelist():
                obj = myzip.open(name)
                portfolio_bucket.upload_fileobj(obj, name, ExtraArgs={'ContentType': mimetypes.guess_type(name)[0]})
                portfolio_bucket.Object(name).Acl().put(ACL='public-read')

        print('done')
        topic.publish(Subject='Deployment Notifictaion', Message='Deployment done succesfully!')

        if job:
            codepipeline = boto3.client("codepipeline")
            codepipeline.put_job_success_result(jobId=job["id"])

    except:
        topic.publish(Subject='Deployment Failure', Message='Deployment failed!')
        raise

    return "Done"
