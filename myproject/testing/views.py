from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from twilio.rest import Client
import os
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

# load_dotenv()


class UserRegistrationAPIView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

User = get_user_model()

class ForgotPasswordAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        phone_number = request.data.get('phone_number')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not phone_number or not new_password or not confirm_password:
            return Response({'error': 'Phone number and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({'error': 'User with this phone number does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Update user's password
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)

import random


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def send_otp_forgot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        phone_number = data.get('phone_number')

        if not phone_number:
            return JsonResponse({'error': 'Phone number is required in the request'}, status=400)
        
        # account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        # account_auth_token = os.getenv('TWILIO_AUTH_TOKEN')

        # print(f"account_sid: {account_sid}")
        # print(f"account_auth_token: {account_auth_token}")

        # if not account_sid or not account_auth_token:
        #     return JsonResponse({'error': 'Twilio account credentials are not configured correctly'}, status=500)

        # client = Client(account_sid, account_auth_token)

        print(f"phone number {phone_number} and type {type(phone_number)}")

        try:
            phone_number_code = "+91"+phone_number
            otp = random.randint(1000, 9999)
            print(f"OTP:- {otp}")

            # message = client.messages.create(
            #     body=f"This is a testing message from Sandipan. Your OTP is - {otp}",
            #     from_="+13344234986", 
            #     to=phone_number_code
            # )

            with connection.cursor() as cursor:
                cursor.execute("SELECT otp FROM otp_table WHERE phone_number = %s", [phone_number])
                otp_data = cursor.fetchone()

            if otp_data:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE otp_table SET otp = %s WHERE phone_number = %s", [otp, phone_number])
            else:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO otp_table (phone_number, otp) VALUES (%s, %s)", [phone_number, otp])

            # print(message)
            return JsonResponse({'message': 'Your SMS has been sent'}, status=200)
        except Exception as e:
            return JsonResponse({'error': f'Failed to send SMS: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def send_otp_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

        phone_number = data.get('phone_number')

        if not phone_number:
            return JsonResponse({'error': 'Phone number is required in the request'}, status=400)
        
        # account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        # account_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        

        # print(f"account_sid: {account_sid}")
        # print(f"account_auth_token: {account_auth_token}")

        # if not account_sid or not account_auth_token:
        #     return JsonResponse({'error': 'Twilio account credentials are not configured correctly'}, status=500)

        # client = Client(account_sid, account_auth_token)

        print(f"phone number {phone_number} and type {type(phone_number)}")

        try:
            phone_number_code = "+91"+phone_number
            otp = random.randint(1000, 9999)
            print(f"OTP:- {otp}")

            # message = client.messages.create(
            #     body=f"This is a testing message from Sandipan. Your OTP is - {otp}",
            #     from_="+13344234986", 
            #     to=phone_number_code
            # )

            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO temp_otp_table (phone_number, otp) VALUES (%s, %s)", [phone_number, otp])

            # print(message)
            return JsonResponse({'message': 'Your SMS has been sent'}, status=200)
        except Exception as e:
            return JsonResponse({'error': f'Failed to send SMS: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)




class LogoutAPIView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to logout: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

      
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_username(request, username, format=None):
    if request.method == 'GET':
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT EXISTS(SELECT 1 FROM testing_customuser WHERE username = %s)", [username])
                username_exists = cursor.fetchone()[0]

                print(cursor.fetchone())

            data = {'is_unique': not username_exists}
            return JsonResponse(data)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_phone_number(request, phone, format=None):
    if request.method == 'GET':
        if len(phone) != 10 or len(phone) < 10:
            return JsonResponse({'message': 'phone number must be 10 digits'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT EXISTS(SELECT 1 FROM testing_customuser WHERE phone_number = %s)", [phone])
                username_exists = cursor.fetchone()[0]

                print(cursor.fetchone())

            data = {'is_unique': not username_exists}
            return JsonResponse(data, status=status.HTTP_200_OK)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def verify_otp_forgot(request, phone, otp, format=None):
    if request.method == 'GET':
        if len(phone) != 10 or len(phone) < 10:
            return JsonResponse({'message': 'phone number must be 10 digits'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # phone_number = "+91"+phone
            phone_number = phone
            with connection.cursor() as cursor:
                cursor.execute("SELECT otp FROM otp_table WHERE phone_number = %s ", [phone_number])
                username_exists = cursor.fetchone()[0]
                print(username_exists)

            if username_exists == otp:
                return JsonResponse({'data': True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'data': False}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def verify_otp_login(request, phone, otp, format=None):
    if request.method == 'GET':
        if len(phone) != 10 or len(phone) < 10:
            return JsonResponse({'message': 'phone number must be 10 digits'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # phone_number = "+91"+phone
            phone_number = phone
            with connection.cursor() as cursor:
                cursor.execute("SELECT otp FROM temp_otp_table  WHERE phone_number = %s ", [phone_number])
                username_exists = cursor.fetchone()[0]
                print(username_exists)

            if username_exists == otp:
                return JsonResponse({'data': True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'data': False}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def check_passcode(request, code,  format=None):
    if request.method == 'GET':
        print(len(code))

        if len(code) != 4:
            return JsonResponse({'message': 'secret code must be 4 digits'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT secret_code FROM secret_code_table")
                otp_exists = cursor.fetchone()[0]
                print(otp_exists)

            if otp_exists == code:
                return JsonResponse({'data': True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'data': False}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

