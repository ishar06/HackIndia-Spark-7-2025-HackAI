from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import fitz  # PyMuPDF
import ollama  # Using Ollama Python package
from django.core.files.storage import FileSystemStorage
import os
import pytesseract
import numpy as np
import json
from .models import Resume, PDFSummary, UserProfile
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.html import escape
from .forms import EditProfileForm, ExtendedUserCreationForm, UserProfileForm

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/landing.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'core/login.html')
            
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            
    return render(request, 'core/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after registration
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome {user.first_name}! Your account has been created successfully.')
                return redirect('home')
        else:
            # Collect all error messages
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{error}")
            messages.error(request, ' '.join(error_messages))
    else:
        form = ExtendedUserCreationForm()

    return render(request, 'core/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('landing')

@login_required
def home(request):
    return render(request, 'core/home.html')

@login_required
def profile(request):
    # Get or create UserProfile for the current user
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'additional':
            # Handle additional information form
            profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Additional information updated successfully!')
                return redirect('profile')
        else:
            # Handle main profile form
            user_form = EditProfileForm(request.POST, instance=request.user)
            profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile,
                                        fields=['phone_number', 'address', 'gender', 'age'])
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        user_form = EditProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    return render(request, 'core/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def pdf_summary(request):
    summary = None
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        try:
            pdf_file = request.FILES['pdf_file']
            
            # Validate file type
            if not pdf_file.name.endswith('.pdf'):
                messages.error(request, 'Please upload a valid PDF file.')
                return render(request, 'core/pdf_summary.html')
            
            # Save uploaded file temporarily
            fs = FileSystemStorage()
            filename = fs.save(pdf_file.name, pdf_file)
            file_path = fs.path(filename)

            # Extract text from PDF
            doc = fitz.open(file_path)
            text = ""
            
            for page_num, page in enumerate(doc, 1):
                try:
                    # Try regular text extraction first
                    regular_text = page.get_text()
                    
                    # If no text is found or text is very short, try OCR
                    if not regular_text or len(regular_text.strip()) < 50:
                        # Convert PDF page to image with higher DPI for better OCR
                        zoom = 2  # zoom factor
                        mat = fitz.Matrix(zoom, zoom)
                        pix = page.get_pixmap(matrix=mat)
                        
                        # Get the image data as bytes
                        img_bytes = pix.samples
                        
                        # Convert to numpy array and reshape
                        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
                        img_array = img_array.reshape(pix.height, pix.width, pix.n)
                        
                        # Perform OCR directly on the image array
                        ocr_text = pytesseract.image_to_string(img_array)
                        text += ocr_text if ocr_text else ""
                    else:
                        text += regular_text
                except Exception as e:
                    messages.warning(request, f'Warning: Could not process page {page_num} properly. Using partial text.')
                    text += regular_text
                   
            doc.close()
            
            # Clean up the temporary file
            try:
                os.remove(file_path)
            except OSError:
                pass

            if not text.strip():
                messages.error(request, 'Could not extract any text from the PDF. Please make sure the file contains readable text.')
                return render(request, 'core/pdf_summary.html')

            # Call Ollama for summarization with title extraction
            try:
                title_prompt = (
                    "Do not add any prefixes or suffixes like '(Note: I've kept it concise while still capturing the main topic and purpose of the document)' or 'Here is a well-formatted summary of the text using HTML markup:' Based on the following text, generate a concise but descriptive title "
                    "that summarizes the main topic or purpose of the document (maximum 5-7 words):\n\n"
                    f"{text[:1000]}"  # Use first 1000 characters for title generation
                )
                
                title_response = ollama.chat(
                    model='llama3',
                    messages=[{"role": "user", "content": title_prompt}]
                )
                generated_title = title_response['message']['content'].strip()
                
                # Clean up the title
                if generated_title.startswith('"') and generated_title.endswith('"'):
                    generated_title = generated_title[1:-1]
                generated_title = generated_title.strip()

                # Now generate the summary
                summary_prompt = (
                    "Create a well-formatted summary of the following text using HTML markup. Follow these rules:\n"
                    "1. Use h2 tags for main sections\n"
                    "2. Use h3 tags for subsections\n"
                    "3. Use p tags for paragraphs\n"
                    "4. Use ul/li tags for lists where appropriate\n"
                    "5. Use div class='highlight' for important points\n"
                    "6. Make it easy to read and understand\n"
                    "7. Group related information under appropriate sections\n"
                    "Text to summarize:\n\n"
                    f"{text}"
                )
                
                summary_response = ollama.chat(
                    model='llama3',
                    messages=[{"role": "user", "content": summary_prompt}]
                )
                summary = summary_response['message']['content'].strip()
                
                # Clean up the formatting if needed
                if not summary.startswith('<'):
                    formatted_lines = []
                    for line in summary.split('\n'):
                        line = line.strip()
                        if line:
                            if line.startswith('•') or line.startswith('-'):
                                if not formatted_lines or not formatted_lines[-1].startswith('<ul>'):
                                    formatted_lines.append('<ul>')
                                formatted_lines.append(f'<li>{line.lstrip("•- ")}</li>')
                            else:
                                if formatted_lines and formatted_lines[-1].startswith('<ul>'):
                                    formatted_lines.append('</ul>')
                                formatted_lines.append(f'<p>{line}</p>')
                    summary = '\n'.join(formatted_lines)
                
                # Save the summary to database with the generated title
                PDFSummary.objects.create(
                    user=request.user,
                    file_name=pdf_file.name,
                    title=generated_title,
                    summary=summary
                )
                
                messages.success(request, 'Summary generated successfully!')
            except Exception as e:
                messages.error(request, 'An error occurred while generating the summary. Please try again.')
                return render(request, 'core/pdf_summary.html')

        except Exception as e:
            messages.error(request, f'An error occurred while processing your PDF: {str(e)}')
            return render(request, 'core/pdf_summary.html')

    return render(request, 'core/pdf_summary.html', {'summary': summary})

@login_required
def download_resume_pdf(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    template = get_template('core/resume_pdf.html')
    html = template.render({'resume_content': resume.generated_content})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{resume.full_name}_resume.pdf"'
    
    # Convert HTML to PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response

@login_required
def resume_builder(request):
    form_type = request.GET.get('type')
    auto_fill = {}
    
    if form_type == 'auto':
        # Get user profile data
        userprofile = request.user.userprofile
        user = request.user
        
        # Format the skills from comma-separated string to list
        skills_list = [s.strip() for s in userprofile.skills.split(',')] if userprofile.skills else []
        
        # Prepare auto-fill data
        auto_fill = {
            'full_name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'phone': userprofile.phone_number,
            'location': userprofile.address,
            'summary': userprofile.bio or '',
            'education': {
                'degree': userprofile.highest_education,
                'institution': userprofile.institution,
                'graduation_year': userprofile.graduation_year
            } if userprofile.highest_education else None,
            'skills': [{'category': 'Skills', 'skills': skills_list}] if skills_list else []
        }

    if request.method == 'POST':
        try:
            # Extract form data
            data = {
                'full_name': escape(request.POST['full_name']),
                'email': escape(request.POST['email']),
                'phone': escape(request.POST['phone']),
                'location': escape(request.POST['location']),
                'summary': escape(request.POST['summary']),
                'education': [],
                'experience': [],
                'skills': []
            }
            
            # Process education entries
            education_count = 0
            while f'education[{education_count}][degree]' in request.POST:
                education = {
                    'degree': escape(request.POST[f'education[{education_count}][degree]']),
                    'institution': escape(request.POST[f'education[{education_count}][institution]']),
                    'start_date': escape(request.POST[f'education[{education_count}][start_date]']),
                    'end_date': escape(request.POST.get(f'education[{education_count}][end_date]', 'Present'))
                }
                data['education'].append(education)
                education_count += 1
            
            # Process experience entries
            experience_count = 0
            while f'experience[{experience_count}][title]' in request.POST:
                experience = {
                    'title': escape(request.POST[f'experience[{experience_count}][title]']),
                    'company': escape(request.POST[f'experience[{experience_count}][company]']),
                    'start_date': escape(request.POST[f'experience[{experience_count}][start_date]']),
                    'end_date': escape(request.POST.get(f'experience[{experience_count}][end_date]', 'Present')),
                    'description': escape(request.POST[f'experience[{experience_count}][description]'])
                }
                data['experience'].append(experience)
                experience_count += 1
            
            # Process skills entries
            skills_count = 0
            while f'skills[{skills_count}][category]' in request.POST:
                skills = {
                    'category': escape(request.POST[f'skills[{skills_count}][category]']),
                    'skills': [escape(s.strip()) for s in request.POST[f'skills[{skills_count}][skills]'].split(',')]
                }
                data['skills'].append(skills)
                skills_count += 1
            
            # Generate resume content using Ollama
            prompt = """Create a professional resume using HTML markup with the following information. Do not write any prefix, do only what you are told, no prefix or suffix. i don't want anything like 'Here is the professional resume in HTML markup:' in the beginning. Follow the HTML structure exactly:

<h1>{full_name}</h1>
<div class="contact-info">
<p>Email: <a href="mailto:{email}">{email}</a><br>
Phone: {phone}<br>
Location: {location}</p>
</div>

<div class="section">
<h2 class="section-title">Professional Summary</h2>
<p>{summary}</p>
</div>

<div class="section">
<h2 class="section-title">Education</h2>
""".format(**data)

            # Add education entries
            for edu in data['education']:
                prompt += f"""
<div class="entry">
<div class="entry-title">{edu['degree']}</div>
<div class="entry-subtitle">{edu['institution']}</div>
<div class="entry-date">{edu['start_date']} - {edu['end_date']}</div>
</div>"""

            prompt += """
</div>

<div class="section">
<h2 class="section-title">Experience</h2>
"""

            # Add experience entries
            for exp in data['experience']:
                prompt += f"""
<div class="entry">
<div class="entry-title">{exp['title']}</div>
<div class="entry-subtitle">{exp['company']}</div>
<div class="entry-date">{exp['start_date']} - {exp['end_date']}</div>
<p>{exp['description']}</p>
</div>"""

            prompt += """
</div>

<div class="section">
<h2 class="section-title">Skills</h2>
"""

            # Add skills entries
            for skill in data['skills']:
                prompt += f"""
<div class="skills-category">
<h3>{skill['category']}</h3>
<ul class="skills-list">
"""
                for s in skill['skills']:
                    prompt += f"<li>{s}</li>"
                prompt += """
</ul>
</div>"""

            prompt += """
</div>"""

            response = ollama.chat(
                model='llama3',
                messages=[{"role": "user", "content": prompt}]
            )
            
            generated_content = response['message']['content']
            
            # Clean up the generated HTML by removing any AI prefixes and code block markers
            unwanted_prefixes = [
                "Here is the HTML code for the professional resume:",
                "```html",
                "```",
                "Here's the formatted resume:",
                "Here's your professional resume:"
            ]
            for prefix in unwanted_prefixes:
                generated_content = generated_content.replace(prefix, "")
            generated_content = generated_content.strip()
            
            # Save to database
            resume = Resume(
                user=request.user,
                full_name=data['full_name'],
                email=data['email'],
                phone=data['phone'],
                location=data['location'],
                summary=data['summary'],
                education=data['education'],
                experience=data['experience'],
                skills=data['skills'],
                generated_content=generated_content
            )
            resume.save()
            
            messages.success(request, 'Resume generated successfully!')
            return render(request, 'core/resume_builder.html', {
                'resume_content': generated_content,
                'resume_id': resume.id,
                'form_type': form_type,
                'auto_fill': auto_fill
            })
            
        except Exception as e:
            messages.error(request, f'An error occurred while generating your resume: {str(e)}')
            return render(request, 'core/resume_builder.html', {
                'form_type': form_type,
                'auto_fill': auto_fill
            })
    
    return render(request, 'core/resume_builder.html', {
        'form_type': form_type,
        'auto_fill': auto_fill
    })

@login_required
def resumes_view_all(request):
    resumes = Resume.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/resumes_list.html', {'resumes': resumes})

@login_required
def pdf_summaries_view_all(request):
    query = request.GET.get('q', '')
    if query:
        pdf_summaries = PDFSummary.search(request.user, query)
    else:
        pdf_summaries = PDFSummary.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/pdf_summaries_list.html', {
        'pdf_summaries': pdf_summaries,
        'query': query
    })