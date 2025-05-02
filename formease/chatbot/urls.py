from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('message/', views.chat_message, name='chat_message'),
]