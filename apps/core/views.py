import json

import jwt
import io
from datetime import datetime, timedelta
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser
# from PIL import Image
# from model.main import prediction
from .models import User
from .serializers import UserSerializer

# from chatterbot import ChatBot
# from chatterbot.trainers import ChatterBotCorpusTrainer
import os
import google.generativeai as genai
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

load_dotenv()  # loads .env if you're storing the key there
genai.configure(api_key="AIzaSyBxadVk3AvVFgkE1oA8tMfTpbrql25T7Rg") # Better practice than hardcoding
model = genai.GenerativeModel("gemini")  # or "gemini-pro-vision" for multimodal

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv()

# Configure Gemini API key from environment variable
genai.configure(api_key="AIzaSyBxadVk3AvVFgkE1oA8tMfTpbrql25T7Rg")

# Initialize the Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")

# Full context about Milk and Honey smart farm system
SYSTEM_CONTEXT = """
You are an expert assistant knowledgeable about 'Milk and Honey', a smart farm management system powered by AgroSense.

### Problem Solved:
Milk and Honey solves the critical issue of "Lack of Timely and Accurate Farm Insights" faced by smallholder farmers. Without real-time and precise data, farmers rely on guesswork or delayed advice, causing overwatering or underwatering, soil degradation, crop loss, wasted inputs, and low yields.

### Services Provided:
- Real-time monitoring of farm conditions
- Data logging and analysis for actionable insights
- Automated actions such as irrigation control and alerting
- AI-powered plant disease detection through image analysis
- Crop growth tracking to predict yields and optimize care

### Sensors Available:
- Soil pH sensors to monitor soil acidity or alkalinity
- Soil moisture sensors to track water levels in the soil

Milk and Honey empowers farmers with accurate, timely data and AI-driven insights to make informed decisions and improve crop productivity.
"""

@csrf_exempt
@api_view(["POST"])
def chatbot(request):
    try:
        user_input = request.data.get("message")
        if not user_input:
            return Response({"error": "No message provided"}, status=400)

        # Combine the system context with user input for the prompt
        full_prompt = f"{SYSTEM_CONTEXT}\n\nUser: {user_input}\nAssistant:"

        # Get response from Gemini
        response = model.generate_content(full_prompt)

        return Response({'message': response.text})

    except Exception as e:
        return Response({'error': f"Error: {str(e)}"}, status=500)


def convert_keys(obj):
    """Convert keys with hyphens to underscores in nested dictionaries."""
    if isinstance(obj, dict):
        new_dict = {}
        for key, value in obj.items():
            new_key = key.replace('-', '_') if isinstance(key, str) else key
            new_dict[new_key] = convert_keys(value)
        return new_dict
    elif isinstance(obj, list):
        return [convert_keys(item) for item in obj]
    else:
        return obj

@api_view(["GET"])
def weather(request):
    location = request.GET.get('location', 'nairobi')
    data = {}
    try:
        response = requests.get(
            f"https://api.weatherapi.com/v1/current.json?key={os.getenv('API_KEY')}&q={location}&aqi=yes")
        if response.status_code == 200:
            data = convert_keys(response.json())
    except:
            data = {}

    return Response(data, status=200)


@api_view(["POST"])
@parser_classes([MultiPartParser])
def detection(request):
    return Response({"result": f"Plant is affected by Black Sport"}, status=status.HTTP_200_OK)
    # image = request.FILES.get('image')
    #
    # if not image:
    #     return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
    #
    # image = Image.open(io.BytesIO(image.read()))
    # result = prediction(image)
    # return Response({"result": f"Plant is affected by {result[0]}"}, status=status.HTTP_200_OK)


@api_view(["GET"])
def tomato(request):
    return render(request, "tomato.html", {})

@api_view(["GET"])
def data_logging(request):
    return render(request, "datalogging.html", {})

@api_view(["GET"])
def automated_actions(request):
    return render(request, "automatedactions.html", {})

@api_view(["GET"])
def sensors(request):
    return render(request, "sensors.html", {})

@api_view(["GET"])
def enquiry(request):
    return render(request, "enquiry.html", {})

@api_view(["GET"])
def logout_view(request):
    logout(request)

    response = redirect('/login')
    if 'auth_token' in request.COOKIES:
        response.delete_cookie('auth_token')

    return response

@api_view(["GET"])
def dashboard(request):
    token = request.COOKIES.get('auth_token')

    if not token and 'HTTP_AUTHORIZATION' in request.META:
        auth_header = request.META['HTTP_AUTHORIZATION']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

    if not token:
        return Response({"redirect": "/login"}, status=302, headers={"Location": "/login"})

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload['id']
        user = User.objects.get(id=user_id)
        user_data = UserSerializer(user).data

        return render(request, "dashboard/dashboard.html", {
            "user": user_data,
        })
    except jwt.ExpiredSignatureError:
        return Response({"redirect": "/login"}, status=302, headers={"Location": "/login"})
    except jwt.InvalidTokenError:
        return Response({"redirect": "/login"}, status=302, headers={"Location": "/login"})

# def dashboard(request):
#     return render(request, "dashboard/dashboard.html", {})

# @api_view(["GET"])
# def dashboard(request):
#     return render(request, "dashboard/dashboard.html", {})

@api_view(["GET"])
def index(request):
    return render(request, "index.html", {})

@api_view(["GET"])
def sign_up(request):
    return render(request, "auth/registration.html", {})

@api_view(["POST", "GET"])
def sign_in(request):
    if request.method == "POST":
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = get_object_or_404(User, email=email)
        except:
            raise NotFound("Email does not exist")

        if not check_password(password, user.password):
            raise ValidationError({"detail": "Incorrect password"})

        token = jwt.encode(
            {"id": str(user.id), "exp": datetime.utcnow() + timedelta(days=1)},
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        # return Response({
        #     "token": token,
        # }, status=200)

        response = Response({
            "token": token,
        }, status=200)

        response.set_cookie(
            key='auth_token',
            value=token,
            httponly=True,
            samesite='Lax',  # Prevents CSRF
            max_age=86400  # 1 day in seconds
        )

        return response

    else:
        return render(request, "auth/login.html", {})

class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        if request.data["password"] != request.data["confirm_password"]:
            raise ValidationError({'detail': "Passwords do not match."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # headers = self.get_success_headers(serializer.data)
        # return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return redirect("/login")
