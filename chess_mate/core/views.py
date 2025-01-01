from django.shortcuts import render
import requests
from django.http import HttpResponse, JsonResponse

def index(request):
    return HttpResponse("Welcome to ChessMate!")


