import boto3
from io import BytesIO

def get_s3_folders_from_result(result):
    """
    Gets the folders from a s3 list_objects result.
    """

    if 'CommonPrefixes' in result:
        folders = result['CommonPrefixes']
    else:
        folders = []

    return [x['Prefix'] for x in folders]

def get_s3_files_from_result(result):
    """
    Gets the files from a s3 list_objects result.
    """
    if 'Contents' in result:
        files = result['Contents']
    else:
        files = []

    return [x['Key'] for x in files]

def read_s3_bucket_folder(bucket_name, folder):
    """
    Reads the contents of an s3 folder in a bucket.
    """
    client = boto3.client('s3')

    kwargs = {'Bucket': bucket_name, 'Delimiter':'/'}

    if(folder != '/'):
        kwargs['Prefix'] = folder

    result = client.list_objects(**kwargs)

    folders = get_s3_folders_from_result(result)
    files = get_s3_files_from_result(result)

    return folders, files

def read_s3_file(bucket_name, key, binary=False):
    """
    Reads the contents of an S3 text file.
    """
    client = boto3.client('s3')

    result = client.get_object(Bucket=bucket_name, Key=key)

    if result['ResponseMetadata']['HTTPStatusCode'] != 200:
        pass

    if binary:
        return result['Body'].read()
    else:
        return result['Body'].read().decode('utf-8')

def write_s3_file(bucket_name, key, content):
    """
    Writes text to an S3 text file.
    """
    client = boto3.client('s3')
    file_like_content = BytesIO(content)
    result = client.put_object(Bucket=bucket_name, Key=key, Body=file_like_content)

    # TODO: Some kind of error handling.

def read_s3_stream(bucket_name, key):
    """
    Returns a stream for an S3 file.
    """
    client = boto3.client('s3')

    result = client.get_object(Bucket=bucket_name, Key=key)

    if result['ResponseMetadata']['HTTPStatusCode'] != 200:
        pass

    return result['Body']

def write_s3_stream(bucket_name, key, stream):
    """
    Writes a stream to S3.
    """
    pass

def delete_s3_file(bucket_name, key):
    """Delete file from S3."""
    client = boto3.client('s3')
    client.delete_object(Bucket=bucket_name,
                         Key=key)
