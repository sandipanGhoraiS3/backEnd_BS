from django.shortcuts import render
import json
import boto3
from dotenv import load_dotenv
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseServerError, HttpResponseNotAllowed
from rest_framework.decorators import api_view
import tempfile
from django.db import connection
from rest_framework import status
import requests
from django.utils.timesince import timesince
from datetime import datetime

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

                    # storage_link = response_payload["path"]

                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO bs_media 
                                (media_type_id, media_category_id, 
                                storage_link, media_name, media_desc, 
                                media_size, created_by) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, [media_type_id, media_category_type_id, response_payload['path'], media_name, media_desc, response_payload['file_size'], created_by])

                        with connection.cursor() as cursor:
                            cursor.execute("""
                            SELECT _id FROM bs_media WHERE media_type_id = %s AND media_category_id = %s 
                            AND storage_link = %s AND media_name = %s AND media_desc = %s AND media_size = %s AND created_by = %s ORDER BY created_at DESC LIMIT 1
                            """, [media_type_id, media_category_type_id, response_payload['path'], media_name, media_desc, response_payload['file_size'], created_by])
                            media_id = cursor.fetchone()[0]

                        print(f"media _id : {media_id}")
                        
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT type FROM media_category_type WHERE _id = %s ", [media_category_type_id])
                            media_category_type = cursor.fetchone()[0]

                        print(f"media_category_type : {media_category_type}")

                        notification_text = f'New {media_category_type} added from admin'

                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO bs_notifications 
                                (activator_id, media_id, type_of_notification, notification_text) 
                                VALUES (%s, %s, %s, %s)""", [created_by, media_id, 'admin post', notification_text])

                        with connection.cursor() as cursor:
                            cursor.execute("""
                            SELECT _id FROM bs_notifications WHERE activator_id = %s AND
                            media_id = %s AND type_of_notification = %s AND notification_text = %s 
                            ORDER BY created_at DESC LIMIT 1 """, 
                            [created_by, media_id, 'admin post', notification_text])
                            notification_id = cursor.fetchone()[0]

                        print(f"notification_id : {notification_id}")

                        with connection.cursor() as cursor:
                            cursor.execute("""
                            SELECT _id FROM bs_users WHERE is_superuser <> true """)
                            users = cursor.fetchall()

                        print(users)

                        if users:
                            for user in users:
                                with connection.cursor() as cursor:
                                    cursor.execute("""
                                    INSERT INTO bs_notification_users 
                                    (notification_id, notifier) VALUES (%s, %s)""", [notification_id, user])

                        return JsonResponse({
                            'massage': f'{media_type} added successfuly',
                            'media_id': media_id,
                            'notification_id': notification_id,
                            }, status=200)
                    
                    except Exception as e:
                        return JsonResponse({'error': 'Failed to add media', 'details': str(e)}, status=500)
            else:
                return JsonResponse({'error': 'Media type not found'}, status=404)
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=500)



def format_time_since(timestamp):
    now = datetime.now()
    delta = now - timestamp
    if delta.days > 0:
        return f"{delta.days} days ago"
    elif delta.seconds < 60:
        return f"{delta.seconds} seconds ago"
    elif delta.seconds < 3600:
        return f"{delta.seconds // 60} minutes ago"
    else:
        return f"{delta.seconds // 3600} hours ago"


@csrf_exempt
def list_devotions(request, user_id, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bs_users WHERE _id = %s AND is_active = true ", [user_id])
            valid_user_count = cursor.fetchone()[0]

        if valid_user_count:
            with connection.cursor() as cursor:
                cursor.execute("SELECT _id FROM media_category_type WHERE type = 'devotion'")
                media_category_type_id = cursor.fetchone()[0]

            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM bs_media WHERE media_category_id = %s AND is_active = true ", [media_category_type_id])
                media_info = cursor.fetchall()

            if media_info:
                response_data = []
                for media_row in media_info:
                    media_info_dict = {
                        '_id': media_row[0],
                        'media_type_id': media_row[1],
                        'media_category_id': media_row[2],
                        'storage_link': media_row[3],
                        'media_name': media_row[4],
                        'media_desc': media_row[5],
                        'created_by': media_row[6],
                        'created_at': format_time_since(media_row[7]),
                        'updated_at': media_row[8],
                        'is_active': media_row[9],
                        'media_size': media_row[10]
                    }

                    with connection.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM bs_comments WHERE media_id = %s AND is_active = true", [media_row[0]])
                        total_comments = cursor.fetchone()[0]

                    with connection.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM bs_likes WHERE like_on_id = %s AND is_active = true", [media_row[0]])
                        total_likes = cursor.fetchone()[0]

                    response_data.append({
                        'media_info': media_info_dict,
                        'total_comments': total_comments,
                        'total_likes': total_likes
                    })

                return JsonResponse(response_data, safe=False)
            else:
                return JsonResponse({'error': 'No media found for this user'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid user ID'}, status=404)
            
    except Exception as e:
        return HttpResponseServerError(str(e))

def get_greeting():
    now = datetime.now()
    current_hour = now.hour

    if current_hour < 12:
        return "Good morning"
    elif current_hour < 18:
        return "Good afternoon"
    elif current_hour < 22:
        return "Good evening"
    else:
        return "Good night"

@csrf_exempt
def find_user_info(request, user_id, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bs_users WHERE _id = %s AND is_active = true ", [user_id])
            valid_user_count = cursor.fetchone()[0]

        if valid_user_count:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT username, first_name, last_name, phone_number
                     FROM bs_users WHERE _id = %s AND is_active = true """, [user_id])
                user_info = cursor.fetchone()
            
            if user_info:
                media_info_dict = {
                    'username': user_info[0],
                    'first_name': user_info[1],
                    'last_name': user_info[2],
                    'phone_number': user_info[3],
                    'greeting': get_greeting(),
                }

                return JsonResponse(media_info_dict, safe=False)
            else:
                return JsonResponse({'error': 'No media found for this user'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid user ID'}, status=404)
    except Exception as e:
        return HttpResponseServerError(str(e))

@csrf_exempt
def find_user_info_list(request, username_prefix, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT _id, username, first_name, last_name, phone_number,
                is_superuser, last_login_at FROM bs_users WHERE username LIKE %s AND 
                is_active = true """, [username_prefix + '%'])
            users_info = cursor.fetchall()
            
        if users_info:
            users_list = []
            for user_info in users_info:
                user = {
                    '_id': user_info[0],
                    'username': user_info[1],
                    'first_name': user_info[2],
                    'last_name': user_info[3],
                    'phone_number': user_info[4],
                    'is_superuser': user_info[5],
                    'last_login_at': user_info[6],
                }
                users_list.append(user)

            return JsonResponse(users_list, safe=False)
        else:
            return JsonResponse({'error': 'No users found for this prefix'}, status=404)
    except Exception as e:
        return HttpResponseServerError(str(e))

