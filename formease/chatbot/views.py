import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ChatMessage
import json

def get_ollama_response(message):
    try:
        # Define available features and their descriptions
        features = {
            "resume": {
                "url": "/resume-builder/",
                "description": "Create professional resumes with AI assistance"
            },
            "pdf": {
                "url": "/pdf-summary/",
                "description": "Generate AI-powered summaries of PDF documents"
            },
            "resumes": {
                "url": "/resumes/",
                "description": "View all your created resumes"
            },
            "summaries": {
                "url": "/pdf-summaries/",
                "description": "View all your PDF summaries"
            }
        }

        # Add feature information to the prompt
        feature_context = """
        Available features:
        - Resume Builder (/resume-builder/): Create professional resumes with AI assistance
        - PDF Summarizer (/pdf-summary/): Generate AI-powered summaries of PDF documents
        - My Resumes (/resumes/): View all your created resumes
        - PDF Summaries (/pdf-summaries/): View all your PDF summaries
        """

        response = requests.post('http://localhost:11434/api/generate',
            json={
                'model': 'llama3',
                'prompt': f"""You are FormEase assistant. Here are the available features:
                {feature_context}
                
                When referring to features, include their paths.
                Response to: {message}""",
                'stream': False
            })
        if response.status_code == 200:
            return response.json()['response']
        return "I apologize, but I'm having trouble processing your request at the moment."
    except Exception as e:
        return f"I apologize, but I'm having trouble processing your request at the moment. Error: {str(e)}"

def get_chatbot_response(message):
    return get_ollama_response(message)

@login_required
def chat_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            response = get_chatbot_response(user_message)
            
            # Save the chat message and response
            chat = ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=response
            )
            
            return JsonResponse({
                'response': response,
                'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)