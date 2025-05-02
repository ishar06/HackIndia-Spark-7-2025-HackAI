from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import UserProfile

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class UserProfileForm(forms.ModelForm):
    current_year = timezone.now().year
    graduation_year = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1950', 'max': current_year}),
        min_value=1950,
        max_value=current_year,
        required=False
    )
    age = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '16', 'max': '100'}),
        min_value=16,
        max_value=100,
        required=False
    )
    skills = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter skills separated by commas'
        }),
        required=False
    )

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'gender', 'age', 'profile_photo',
                'highest_education', 'institution', 'graduation_year', 
                'field_of_study', 'skills', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gender': forms.RadioSelect(attrs={'class': 'btn-check'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'highest_education': forms.TextInput(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class ExtendedUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'Email'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Username'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username