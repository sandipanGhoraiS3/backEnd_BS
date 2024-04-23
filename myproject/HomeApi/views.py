from django.shortcuts import render
import json
import boto3
from dotenv import load_dotenv
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.decorators import api_view
import tempfile
from django.db import connection
from rest_framework import status
import requests

# Create your views here.
@csrf_exempt
def add_media(request, format=None):
    if request.method == 'POST':
        if 'media' not in request.FILES:
            return JsonResponse({'error': 'File not found in the request'}, status=400)

        file_url = request.FILES['media'].name
        print(file_url)

        try:
            metadata = json.loads(request.POST.get('metadata', '{}'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON metadata'}, status=400)
        
        media_type = metadata.get('media_type')
        media_category = metadata.get('media_category')
        media_name = metadata.get('media_name')
        media_desc = metadata.get('media_desc')
        created_by = metadata.get('created_by')

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT _id FROM media_type WHERE type = %s ", [media_type])
                media_type_id = cursor.fetchone()[0]

            with connection.cursor() as cursor:
                cursor.execute("SELECT _id FROM media_category_type WHERE type = %s ", [media_category])
                media_category_type_id = cursor.fetchone()[0]

            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM bs_users WHERE _id = %s AND is_active = true ", [created_by])
                count_user_id = cursor.fetchone()[0]

                print(count_user_id)

            if media_type_id and media_category_type_id and count_user_id > 0:
                
                upload_url = 'http://127.0.0.1:8000/test/upload_file/'
                files = {'media': request.FILES['media']}
                data = {
                    'type': media_type,
                }
                print("all good")
                response = requests.post(upload_url, files=files, data=data)

                if response.status_code == 200:
                    response_payload = response.json()

                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO bs_media 
                                (media_type_id, media_category_id, 
                                storage_link, media_name, media_desc, 
                                media_size, created_by) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, [media_type_id, media_category_type_id, response_payload['path'], media_name, media_desc, response_payload['file_size'], created_by])

                        return JsonResponse({'massage': f'{media_type} added successfuly'}, status=200)
                    except Exception as e:
                        return JsonResponse({'error': 'Failed to add media', 'details': str(e)}, status=500)
            else:
                return JsonResponse({'error': 'Media type not found'}, status=404)
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=500)


    
