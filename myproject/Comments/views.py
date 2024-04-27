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
from . import utils



@csrf_exempt
def add_comment(request, format=None):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        media_id = data.get('media_id')
        commenter = data.get('commenter')
        comment_text = data.get('comment_text')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT count(*) FROM bs_users 
                WHERE _id = %s AND is_active = true AND is_superuser <> true """, [commenter])
                commenter_idValid = cursor.fetchone()[0]

            if commenter_idValid > 0:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO bs_comments 
                            (media_id, commenter, comment_text) VALUES (%s, %s, %s)""", [media_id, commenter, comment_text])

                    with connection.cursor() as cursor:
                        cursor.execute("""
                        SELECT _id FROM bs_comments 
                        WHERE media_id = %s AND commenter = %s AND comment_text = %s 
                        ORDER BY created_at DESC LIMIT 1 """, [media_id, commenter, comment_text]) 
                        comment_id = cursor.fetchone()[0]
                    
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO bs_notification_admin  
                            (comment_id, notification_type) VALUES (%s, %s)""", [comment_id, 'added comment']) 

                    return JsonResponse({
                        'message': 'Comment added successfully',
                        'comment_id': comment_id,
                        }, status=201)
                
                except Exception as e:
                    error_message = str(e)
                    return JsonResponse({'error': error_message}, status=500)

        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def add_like(request, format=None):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            like_on_id = data.get('like_on_id')
            liked_by = data.get('liked_by')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        print(like_on_id)
        print(liked_by)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM bs_media WHERE _id = %s ", [like_on_id])
                likeOnValid = cursor.fetchone()[0]

            print(f"likeOnValid: {likeOnValid}")

            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM bs_users WHERE _id = %s AND is_active = true ", [liked_by])
                likedByValid = cursor.fetchone()[0]

            print(f"likedByValid: {likedByValid}")

            if likeOnValid and likedByValid:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM bs_likes WHERE like_on_id = %s and liked_by = %s ", [like_on_id, liked_by])
                    likedForUser = cursor.fetchone()[0]

                print(f"likedForUser: {likedForUser}")

                if likedForUser > 0: 
                    with connection.cursor() as cursor:
                        cursor.execute("""
                        SELECT _id, is_active FROM bs_likes 
                        WHERE like_on_id = %s AND liked_by = %s """, [like_on_id, liked_by]) 
                        result = cursor.fetchone()
                        if result:
                            like_id, is_active = result
                        else:
                            return JsonResponse({'message': 'not find any record'}, status=405)

                    print(f"like_id: {like_id}")
                    print(f"is_active: {is_active}")

                    if is_active: 
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                UPDATE bs_likes 
                                SET is_active = false, updated_at = Now()
                                WHERE like_on_id = %s AND liked_by = %s""", [like_on_id, liked_by])
                            
                    else:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                UPDATE bs_likes 
                                SET is_active = true, updated_at = Now()
                                WHERE like_on_id = %s AND liked_by = %s""", [like_on_id, liked_by])

                    with connection.cursor() as cursor:
                        cursor.execute("""
                        INSERT INTO bs_notification_admin  
                        (like_id, notification_type) VALUES (%s, %s)""", [like_id, 'update like'])

                    with connection.cursor() as cursor:
                        cursor.execute("""
                        SELECT _id FROM bs_notification_admin  
                        WHERE like_id = %s AND notification_type = %s ORDER BY created_at DESC LIMIT 1 """, 
                        [like_id, 'update like'])
                        notification_id = cursor.fetchone()[0]

                    return JsonResponse({
                        'message': 'like updated successfully',
                        'like_id': like_id,
                        'notification_id': notification_id,
                        }, status=200)

                else:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                        INSERT INTO bs_likes  
                        (like_on_id, liked_by) VALUES (%s, %s)""", [like_on_id, liked_by])

                    with connection.cursor() as cursor:
                        cursor.execute("""
                        SELECT _id FROM bs_likes 
                        WHERE like_on_id = %s AND liked_by = %s """, [like_on_id, liked_by]) 
                        like_id = cursor.fetchone()[0]

                    print(f"like_id: {like_id}")

                    with connection.cursor() as cursor:
                        cursor.execute("""
                        INSERT INTO bs_notification_admin  
                        (like_id, notification_type) VALUES (%s, %s)""", [like_id, 'added like'])

                    print('all good')

                    with connection.cursor() as cursor:
                        cursor.execute("""
                        SELECT _id FROM bs_notification_admin  
                        WHERE like_id = %s AND notification_type = %s ORDER BY created_at DESC LIMIT 1 """, 
                        [like_id, 'added like'])
                        notification_id = cursor.fetchone()[0]
                    
                    return JsonResponse({
                        'message': 'Like inserted successfully',
                        'like_id': like_id,
                        'notification_id': notification_id,
                        }, status=200)
            else:
                return JsonResponse({'error': 'Invalid liked_by id or media id'}, status=400)

        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    

@csrf_exempt
def list_comments(request, media_id, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bs_media WHERE _id = %s AND is_active = true ", [media_id])
            valid_media_count = cursor.fetchone()[0]

        print(valid_media_count)

        if valid_media_count:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT _id, commenter, comment_text, type_of_comment, 
                    media_id, created_at, is_react, react_at FROM bs_comments 
                    WHERE media_id = %s AND is_active = true """, [media_id])
                comment_info = cursor.fetchall()
            
            if comment_info:
                comment_list = []
                for comment in comment_info:
                    comments = {
                        '_id': comment[0],
                        'commenter': comment[1],
                        'comment_text': comment[2],
                        'type_of_comment': comment[3],
                        'media_id': comment[4],
                        'created_at': utils.format_time_since(comment[7]),
                        'admin_react': comment[6],
                    }
                    comment_list.append(comments)

                return JsonResponse(comment_list, safe=False)
            else:
                return JsonResponse({'error': 'No comments found for this media'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid media ID'}, status=404)
    except Exception as e:
        return HttpResponseServerError(str(e))

@csrf_exempt
def list_likes(request, media_id, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM bs_media WHERE _id = %s AND is_active = true ", [media_id])
            valid_media_count = cursor.fetchone()[0]

        if valid_media_count:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT bl."_id" AS like_id, bu."_id" AS user_id, bu.username
                    FROM bs_likes bl, bs_users bu
                    WHERE bl.liked_by = bu."_id"
                    AND bl.like_on_id = %s
                    AND bl.is_active = true """, [media_id])
                like_info = cursor.fetchall()
            
            like_list = []  # Define like_list outside the if block

            if like_info:
                for like in like_info:
                    likes = {
                        'like_id': like[0],
                        'user_id': like[1],
                        'username': like[2],
                    }
                    like_list.append(likes)

            return JsonResponse(like_list, safe=False)
        else:
            return JsonResponse({'error': 'Invalid media ID'}, status=404)
    except Exception as e:
        return HttpResponseServerError(str(e))


@csrf_exempt
def add_admin_like(request, format=None):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            comment_id = data.get('comment_id')
            react_by = data.get('react_by')

            if not comment_id or not react_by:
                return JsonResponse({'error': 'Missing comment_id or react_by'}, status=400)
        
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM bs_comments WHERE _id = %s AND is_active = true", [comment_id])
                validComment_id = cursor.fetchone()[0]

            print(f"validComment_id: {validComment_id}")

            with connection.cursor() as cursor:
                cursor.execute("""SELECT COUNT(*) FROM bs_users 
                WHERE _id = %s AND is_active = true AND is_superuser = true""", [react_by])
                validAdmin_id = cursor.fetchone()[0]

            with connection.cursor() as cursor:
                cursor.execute("""SELECT commenter FROM bs_comments 
                WHERE _id = %s AND is_active = true""", [comment_id])
                commenter_id = cursor.fetchone()[0]

            print(f"validAdmin_id: {validAdmin_id}")

            if validComment_id and validAdmin_id:
                print("all present")

                with connection.cursor() as cursor:
                    cursor.execute("""SELECT EXISTS (SELECT 1 FROM bs_comments 
                    WHERE _id = %s AND is_active = true AND react_at IS NOT NULL
                    ) AS exists_react_at""", [comment_id])
                    is_react_at = cursor.fetchone()[0]

                print(is_react_at)

                if is_react_at:

                    print("react_at present")

                    with connection.cursor() as cursor:
                        cursor.execute("""SELECT is_react FROM bs_comments 
                        WHERE _id = %s AND is_active = true""", [comment_id])
                        is_react = cursor.fetchone()[0]

                    if is_react:
                        with connection.cursor() as cursor:
                            cursor.execute(""" UPDATE bs_comments SET is_react = false, react_by = %s, react_updated_at = Now()
                            WHERE _id = %s """, [react_by, comment_id])
                    else:
                        with connection.cursor() as cursor:
                            cursor.execute(""" UPDATE bs_comments SET is_react = true, react_by = %s, react_updated_at = Now()
                            WHERE _id = %s """, [react_by, comment_id])


                    with connection.cursor() as cursor:
                        cursor.execute("""INSERT INTO bs_notifications 
                        (activator_id, comment_id, type_of_notification, notification_text) VALUES (%s, %s, %s, %s)""", [react_by, comment_id, 'update react by admin', 'react updated by admin'])

                    with connection.cursor() as cursor:
                        cursor.execute("""SELECT _id FROM bs_notifications 
                        WHERE activator_id = %s AND comment_id = %s AND type_of_notification = %s 
                        AND notification_text = %s ORDER BY created_at DESC LIMIT 1 """, [react_by, comment_id, 'update react by admin', 'react updated by admin'])
                        notification_id = cursor.fetchone()[0]

                    with connection.cursor() as cursor:
                        cursor.execute("""INSERT INTO bs_notification_users 
                        (notification_id, notifier) VALUES (%s, %s)""", [notification_id, commenter_id])

                    return JsonResponse({
                        'message': 'like updated',
                        'notification_id': notification_id,
                        'commenter': comment_id,
                    }, status=200)
                    
                else:
                    print("react_at not present")

                    with connection.cursor() as cursor:
                        cursor.execute(""" UPDATE bs_comments SET is_react = true, react_by = %s, react_at = Now()
                        WHERE _id = %s """, [react_by, comment_id]) 
                    
                    with connection.cursor() as cursor:
                        cursor.execute("""INSERT INTO bs_notifications 
                        (activator_id, comment_id, type_of_notification, notification_text) VALUES (%s, %s, %s, %s)""", [react_by, comment_id, 'new admin react', 'New react added from admin'])

                    with connection.cursor() as cursor:
                        cursor.execute("""SELECT _id FROM bs_notifications 
                        WHERE activator_id = %s AND comment_id = %s AND type_of_notification = %s 
                        AND notification_text = %s ORDER BY created_at DESC LIMIT 1 """, [react_by, comment_id, 'new admin react', 'New react added from admin'])
                        notification_id = cursor.fetchone()[0]

                    with connection.cursor() as cursor:
                        cursor.execute("""INSERT INTO bs_notification_users 
                        (notification_id, notifier) VALUES (%s, %s)""", [notification_id, commenter_id])

                    return JsonResponse({
                        'message': 'new like added',
                        'notification_id': notification_id,
                        'commenter': commenter_id,
                    }, status=200)
            else:
                return JsonResponse({'error': 'Invalid comment ID or react by ID'}, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return HttpResponseNotAllowed(['PUT'])

@csrf_exempt
def list_notification_users(request, user_id, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) 
                FROM bs_users  
                WHERE _id = %s AND is_active = true
            """, [user_id])
            is_user = cursor.fetchone()[0]

        if is_user:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT notification_id, notifier, created_at, updated_at, is_new 
                    FROM bs_notification_users  
                    WHERE notifier = %s AND is_active = true ORDER BY created_at DESC
                """, [user_id])
                notifications = cursor.fetchall()

                notification_list = []
                for notification in notifications:
                    notify = {
                        'notification_id': notification[0],
                        'notifier': notification[1],
                        'created_at': utils.format_time_since(notification[2]),
                        'updated_at': notification[3],
                        'is_new': notification[4]
                    }
                    notification_list.append(notify)

            return JsonResponse(notification_list, safe=False, status=200)
        
        else:
            return JsonResponse({'error': 'user not found'}, status=500)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def list_notification_admin(request, admin_id, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) FROM bs_users WHERE _id = %s AND is_active = true AND is_superuser = true 
            """, [admin_id])
            is_admin = cursor.fetchone()[0]

            if is_admin:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        select * from bs_notification_admin bna 
                        where bna.activator_id = %s and is_active = true order by created_at desc
                    """, [admin_id])
                    notifications = cursor.fetchall()
                
                notification_list = []
                for notification in notifications:
                    notify = {
                        '_id': notification[0],
                        'comment_id': notification[1],
                        'like_id': notification[2],
                        'created_at': utils.format_time_since(notification[3]),
                        'updated_at': notification[4],
                        'is_new': notification[5],
                        'is_active': notification[6],
                        'notification_type': notification[7],
                        'activator_id': notification[8]
                    }
                    notification_list.append(notify)

                return JsonResponse(notification_list, safe=False, status=200)
            else:
                return JsonResponse({'error': 'admin not found'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def admin_notification_info(request, notification_id, format=None):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) FROM bs_notification_admin WHERE _id = %s AND is_active = true 
            """, [notification_id])
            is_notification = cursor.fetchone()[0]

        if is_notification:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        EXISTS (SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'bs_notification_admin' AND column_name = 'comment_id') AS comment_id_exists,
                        EXISTS (SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'bs_notification_admin' AND column_name = 'like_id') AS like_id_exists;
                """)
                row = cursor.fetchone()
                comment_id_exists = row[0]
                like_id_exists = row[1]

            notification_details = {}
            
            with connection.cursor() as cursor:
                    cursor.execute("""
                        select * from bs_notification_admin bna 
                        where _id = %s and is_active = true 
                    """, [notification_id])
                    notification = cursor.fetchall()

            if comment_id_exists:

                comment_id = notification[1],

                notify = {
                '_id': notification[0],
                'comment_id': notification[1],
                'created_at': utils.format_time_since(notification[3]),
                'updated_at': notification[4],
                'is_new': notification[5],
                'is_active': notification[6],
                'notification_type': notification[7],
                'activator_id': notification[8]
                }
                notification_details['notification_info'] = notify

                with connection.cursor() as cursor:
                    cursor.execute("""
                    select commenter , comment_text , type_of_comment , media_id , 
                    created_at , updated_at , is_react , react_by , react_at , 
                    react_updated_at , react_by from bs_comments bc 
                    where _id = 3 and is_active = true
                    """, [comment_id])
                    comment = cursor.fetchall()

                commenter = comment[0]
                media_id = comment[3]

                comment_info = {
                    'commenter': comment[0],
                    'comment_text': comment[1],
                    'type_of_comment': comment[2],
                    'media_id' : comment[3],
                    'created_at': comment[4],
                    'updated_at': comment[5],
                    'is_react': comment[6],
                    'react_by': comment[7],
                    'react_at' : comment[8],
                    'react_updated_at': comment[9],
                    'react_by': comment[10],
                }

                notification_details['comment_info'] = comment_info

                ## find media details and add to notification detils
                with connection.cursor() as cursor:
                    cursor.execute("""
                    select commenter , comment_text , type_of_comment , media_id , 
                    created_at , updated_at , is_react , react_by , react_at , 
                    react_updated_at , react_by from bs_comments bc 
                    where _id = 3 and is_active = true
                    """, [comment_id])
                    comment = cursor.fetchall()

                ## also add commentor info details


                


        else:
            return JsonResponse({'error': 'notification not found'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
