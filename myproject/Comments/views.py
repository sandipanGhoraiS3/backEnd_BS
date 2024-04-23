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
                cursor.execute("SELECT count(*) FROM bs_users WHERE _id = %s AND is_active = true ", [commenter])
                commenter_idValid = cursor.fetchone()[0]

            if commenter_idValid > 0:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO bs_comments 
                            (media_id, commenter, comment_text) VALUES (%s, %s, %s)""", [media_id, commenter, comment_text]) 

                    return JsonResponse({'message': 'Comment added successfully'}, status=201)
                
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
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM bs_media WHERE _id = %s ", [like_on_id])
                likeOnValid = cursor.fetchone()[0]

            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM bs_users WHERE _id = %s AND is_active = true ", [liked_by])
                likedByValid = cursor.fetchone()[0]

            if likeOnValid and likedByValid:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM bs_likes WHERE like_on_id = %s and liked_by = %s ", [like_on_id, liked_by])
                    likedForUser = cursor.fetchone()[0]

                if likedForUser > 0: 
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT is_active FROM bs_likes WHERE like_on_id = %s AND liked_by = %s", [like_on_id, liked_by])
                        row = cursor.fetchone()

                    if row:
                        is_active = row[0]
                        if is_active: 
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE bs_likes 
                                    SET is_active = false, updated_at = Now()
                                    WHERE like_on_id = %s AND liked_by = %s""", [like_on_id, liked_by])
                            
                            return JsonResponse({'message': 'Like updated successfully'}, status=200)
                        else:
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE bs_likes 
                                    SET is_active = true, updated_at = Now()
                                    WHERE like_on_id = %s AND liked_by = %s""", [like_on_id, liked_by])
                            return JsonResponse({'message': 'Like added successfully'}, status=200)
                    
                    else:
                        return JsonResponse({'error': 'Invalid like_by id or media id'}, status=400)
                    
                else:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO bs_likes 
                            (like_on_id, liked_by) VALUES (%s, %s)""", [like_on_id, liked_by])
                    
                    return JsonResponse({'message': 'Like added successfully'}, status=200)
                
            else:
                return JsonResponse({'error': 'Invalid liked_by id or media id'}, status=400)

        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def add_comment_like(request, format=None):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            like_on_id = data.get('like_on_id')
            liked_by = data.get('liked_by')
            media_on = data.get('media_on')

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM bs_comments WHERE _id = %s ", [like_on_id])
                likeOnValid = cursor.fetchone()[0]

            with connection.cursor() as cursor:
                cursor.execute("""SELECT count(*) FROM bs_users 
                    WHERE _id = %s AND is_superuser = true AND is_active = true """, [liked_by])
                likedByValid = cursor.fetchone()[0]

            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM bs_media WHERE _id = %s ", [media_on])
                mediaValid = cursor.fetchone()[0]

            if likeOnValid and likedByValid and mediaValid:
                with connection.cursor() as cursor:
                    cursor.execute("""SELECT count(*) FROM likes_on_comments 
                        WHERE like_on_id = %s and liked_by = %s and media_on = %s """, [like_on_id, liked_by, media_on])
                    
                    hasData = cursor.fetchone()[0]

                if hasData > 0:
                    with connection.cursor() as cursor:
                        cursor.execute("""SELECT is_active FROM likes_on_comments 
                            WHERE like_on_id = %s AND liked_by = %s AND media_on = %s """, [like_on_id, liked_by, media_on])
                    row = cursor.fetchone()

                    if row:
                        is_active = row[0]
                        if is_active: 
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE likes_on_comments 
                                    SET is_active = false, updated_at = Now()
                                    WHERE like_on_id = %s AND liked_by = %s AND media_on = %s""", 
                                    [like_on_id, liked_by, media_on])
                                
                            with connection.cursor() as cursor: 
                                cursor.execute("""
                                    UPDATE bs_comments 
                                    SET is_react = false, react_updated_at = Now() 
                                    WHERE _id = %s""", [like_on_id])
                            
                            return JsonResponse({'message': 'Like updated successfully'}, status=200)
                        else:
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE likes_on_comments 
                                    SET is_active = true, updated_at = Now()
                                    WHERE like_on_id = %s AND liked_by = %s AND media_on = %s """, 
                                    [like_on_id, liked_by, media_on])

                            with connection.cursor() as cursor: 
                                cursor.execute("""
                                    UPDATE bs_comments 
                                    SET is_react = true, react_updated_at = Now() 
                                    WHERE _id = %s""", [like_on_id])
                                
                            return JsonResponse({'message': 'Like updated successfully'}, status=200)
                    
                    else:
                        return JsonResponse({'error': 'Invalid like_by id or media id, comment id'}, status=400)
                    
                else:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO likes_on_comments 
                            (like_on_id, liked_by, media_on) VALUES (%s, %s, %s)""", [like_on_id, liked_by, media_on])
                        
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                UPDATE bs_comments 
                                SET is_react = true, react_at = Now() 
                                WHERE _id = %s""", [like_on_id])
                    
                    return JsonResponse({'message': 'Like added successfully'}, status=200)
                
            else:
                return JsonResponse({'error': 'ids are not valid'}, status=405)
                
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)





    

