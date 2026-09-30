"""
Django Forms for Smart Waste Management System.
Handles user registration, login, complaint submission, pickup requests,
and administrative status updates with clean server-side validation.
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Complaint, PickupRequest, UserProfile


class CitizenRegistrationForm(forms.Form):
    """
    Form for registering a new citizen in the platform.
    Collects full name, email, phone number, and password.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'autocomplete': 'name',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'autocomplete': 'email',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. +1 555-0199 or 9876543210',
            'autocomplete': 'tel',
        })
    )
    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Society / Apartment / Colony address (optional)',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a secure password (min 6 characters)',
        }),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your password',
        }),
        min_length=6
    )

    def clean_email(self):
        """Ensure email is unique across all registered users."""
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        """Validate that both password fields match."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match. Please verify.")
        return cleaned_data

    def save(self):
        """
        Creates and saves the User and linked UserProfile objects in SQLite.
        """
        email = self.cleaned_data['email']
        full_name = self.cleaned_data['full_name']
        phone = self.cleaned_data['phone']
        address = self.cleaned_data.get('address', '')
        password = self.cleaned_data['password']

        # Split full name into first and last name for Django User model
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Create standard Django user (email is also used as username)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create accompanying UserProfile
        UserProfile.objects.create(
            user=user,
            phone=phone,
            address=address
        )
        return user


class CitizenLoginForm(forms.Form):
    """
    Login form allowing citizens and staff to log in using either their email or username.
    """
    username_or_email = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email or username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )


class ComplaintForm(forms.ModelForm):
    """
    Form for citizens to report waste-related issues in their area.
    Includes smart priority calculation fallback.
    """
    auto_priority = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'auto_priority_toggle'}),
        help_text="Let Smart Waste system calculate urgency automatically"
    )
    priority = forms.ChoiceField(
        choices=Complaint.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'manual_priority_select'})
    )

    class Meta:
        model = Complaint
        fields = ['issue_type', 'description', 'location', 'landmark', 'priority', 'image', 'latitude', 'longitude']
        widgets = {
            'issue_type': forms.Select(attrs={'class': 'form-select', 'id': 'issue_type_select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the waste issue in detail (e.g. bin overflowing since 2 days, foul smell, stray animals gathering)...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_location',
                'placeholder': 'e.g. Sector 4 Market, Near Central Library, Block B Road',
            }),
            'landmark': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Opposite Water Tank, Behind Metro Pillar 42',
            }),
            'priority': forms.Select(attrs={'class': 'form-select', 'id': 'manual_priority_select'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_latitude', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_longitude', 'step': 'any'}),
        }

    def clean_image(self):
        """Validate uploaded file size (maximum 5MB) and file extension."""
        image = self.cleaned_data.get('image')
        if image:
            # Check maximum file size (5 MB = 5 * 1024 * 1024 bytes)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file is too large. Maximum size is 5MB.")
            # Validate allowed file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError("Unsupported format. Please upload JPG, PNG, or WebP images.")
        return image


class PickupRequestForm(forms.ModelForm):
    """
    Form for citizens to schedule doorstep waste collection.
    """
    TIME_SLOT_CHOICES = [
        ('Morning (08:00 AM - 11:00 AM)', 'Morning (08:00 AM - 11:00 AM)'),
        ('Midday (11:00 AM - 02:00 PM)', 'Midday (11:00 AM - 02:00 PM)'),
        ('Afternoon (02:00 PM - 05:00 PM)', 'Afternoon (02:00 PM - 05:00 PM)'),
        ('Evening (05:00 PM - 07:00 PM)', 'Evening (05:00 PM - 07:00 PM)'),
    ]

    preferred_time = forms.ChoiceField(
        choices=TIME_SLOT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = PickupRequest
        fields = ['waste_category', 'quantity', 'pickup_address', 'preferred_date', 'preferred_time', 'notes', 'latitude', 'longitude']
        widgets = {
            'waste_category': forms.Select(attrs={'class': 'form-select', 'id': 'pickup_category_select'}),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2 medium garbage bags, 1 cardboard box, ~15 kg',
            }),
            'pickup_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'House / Flat number, building name, society / street name',
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special notes, gate access instructions, or handling precautions',
            }),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_latitude', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_longitude', 'step': 'any'}),
        }


class AdminComplaintUpdateForm(forms.ModelForm):
    """
    Form used by administrators to update complaint status, assign crew, and add notes.
    """
    class Meta:
        model = Complaint
        fields = ['status', 'priority', 'assigned_crew', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_crew': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Crew Unit #3, Truck 104'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal progress notes or resolution report'}),
        }


class AdminPickupUpdateForm(forms.ModelForm):
    """
    Form used by administrators to update pickup status and dispatch vehicles.
    """
    class Meta:
        model = PickupRequest
        fields = ['status', 'assigned_vehicle', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_vehicle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Electric Waste Van #2, Driver Rajesh'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Pickup coordination details or confirmation'}),
        }
