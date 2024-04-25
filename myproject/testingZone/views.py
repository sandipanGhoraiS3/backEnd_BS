from django.shortcuts import render
import boto3
from dotenv import load_dotenv
import os, io
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.decorators import api_view
import json
import tempfile
import botocore
from django.db import connection

# Create your views here.
load_dotenv()


def format_file_size(size_in_bytes):
    for unit in ['bytes', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0


@csrf_exempt
@api_view(['POST',])
def upload_file(request, format=None):
    # try:
    #     data = json.loads(request.body)
    # except json.JSONDecodeError:
    #     return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    if 'media' not in request.FILES:
        return JsonResponse({'error': 'File not found in the request'}, status=400)
    
    file_url = request.FILES['media']
    print(request.FILES['media'].name)
    # file_type = json.loads(request.POST.get('data', '{}'))
    file_type = request.POST.get('type', '')
    print(file_type)
    # typeoffile = file_type.get('type')
    # print(typeoffile)
    file_size = format_file_size(file_url.size)
    print(file_size)

    upload_path = file_type+"s"
    # upload_path = typeoffile

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

    s3 = boto3.client('s3',
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION_NAME)

    # s3_file_url = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file_url.chunks():
                temp_file.write(chunk)

        file_key = f"{upload_path}/{file_url.name}"
        print(f"FILE KEY: {file_key}")
        s3.upload_file(temp_file.name, S3_BUCKET_NAME, file_key)

        s3_file_url = f"s3://{S3_BUCKET_NAME}/{file_key}"
        print(f"File uploaded to S3: {s3_file_url}")

        os.unlink(temp_file.name)
    except Exception as e:
        return JsonResponse({
            'error': f"Error uploading file from S3: {e}"
        }, status=400)

    return JsonResponse({
        'message': 'file uploaded succesfuly',
        'path': s3_file_url,
        'file_size': file_size
        }, status=200) 

@csrf_exempt
@api_view(['POST',])
def download_file(request, format=None):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    
    download_from = data.get('download_from')
    print(download_from)
    
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")

    bucket_name, key = download_from.split('/')[2], '/'.join(download_from.split('/')[3:])
    folder_path, file_name = os.path.split(key)

    print(f"BUCKET NAME: {bucket_name}")
    print(f"KEY: {key}")
    print(f"FOLER PATH: {folder_path}")
    print(f"FILE NAME: {file_name}")

    file_path = 'C:/Users/Sandipan Ghorai/Downloads/' + file_name

    print(file_name)

    s3 = boto3.client('s3',
                      aws_access_key_id=AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                      region_name=AWS_REGION_NAME)

    try:
        s3.download_file(bucket_name, key, file_path)
        print(f"File downloaded from S3: s3://{bucket_name}/{key}")

        with connection.cursor() as cursor:
            cursor.execute("SELECT _id FROM bs_media WHERE storage_link = %s ", [download_from])
            media_id = cursor.fetchone()[0]

            print(f"MEDIA ID: {media_id}")

            believer_id = 6 # Now hardcoded

            cursor.execute("""
                INSERT INTO bs_downloads (believer_id, media_id) VALUES (%s, %s)""", [believer_id, media_id])

        return JsonResponse({
            'message': 'File downloaded successfully'
        }, status=200)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return JsonResponse({'error': 'File not found'}, status=404)
        else:
            return JsonResponse({'error': 'Error downloading file from S3'}, status=500)


