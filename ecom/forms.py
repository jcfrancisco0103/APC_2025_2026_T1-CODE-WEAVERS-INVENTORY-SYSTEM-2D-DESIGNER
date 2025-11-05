import re
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from . import models
from .models import Product, InventoryItem


# User registration form
class CustomerUserForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), 
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={'autocomplete': 'new-password'})
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Unable to use this username. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password):
                raise forms.ValidationError("Password must include at least one uppercase letter.")
            if not re.search(r'\d', password):
                raise forms.ValidationError("Password must include at least one number.")
            if not re.search(r'[!@#$%*]', password):
                raise forms.ValidationError("Password must include at least one symbol (e.g., !, @, #, $, %, *).")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")


# User edit form (no password fields)
class CustomerUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            qs = User.objects.filter(username=username)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Unable to use this username. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = User.objects.filter(email=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("An account with this email already exists.")
        return email


# Customer personal details form
class CustomerForm(forms.ModelForm):
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        import re
        # Accepts format: 956 837 0169 (10 digits, 2 spaces)
        pattern = r'^\d{3} \d{3} \d{4}$'
        if not re.match(pattern, mobile):
            raise forms.ValidationError("Enter number as '956 837 0169' (10 digits, spaces required).")
        return mobile
    region = forms.CharField(max_length=100)
    province = forms.CharField(max_length=100, required=False)
    citymun = forms.CharField(max_length=100, required=False)
    barangay = forms.CharField(max_length=100, required=False)

    # PSGC to Django region code mapping
    PSGC_TO_DJANGO_REGION = {
        '010000000': 'R1',   # Ilocos Region
        '020000000': 'R2',   # Cagayan Valley
        '030000000': 'R3',   # Central Luzon
        '040000000': 'R4A',  # CALABARZON
        '170000000': 'R4B',  # MIMAROPA
        '050000000': 'R5',   # Bicol Region
        '060000000': 'R6',   # Western Visayas
        '070000000': 'R7',   # Central Visayas
        '080000000': 'R8',   # Eastern Visayas
        '090000000': 'R9',   # Zamboanga Peninsula
        '100000000': 'R10',  # Northern Mindanao
        '110000000': 'R11',  # Davao Region
        '120000000': 'R12',  # SOCCSKSARGEN
        '130000000': 'NCR',  # National Capital Region
        '140000000': 'CAR',  # Cordillera Administrative Region
        '160000000': 'R13',  # Caraga
        '150000000': 'BARMM' # Bangsamoro Autonomous Region in Muslim Mindanao
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].choices = models.Customer.REGION_CHOICES
        self.fields['region'].widget = forms.Select()
        self.fields['region'].required = True
        # Remove city and barangay logic, use citymun, province, barangay
        for field in ['citymun', 'province', 'barangay']:
            value = self.data.get(field, None) or self.initial.get(field, None)
            if value:
                self.fields[field].choices = [(value, value)]
            else:
                self.fields[field].choices = []
            self.fields[field].widget = forms.Select()
            # Province is not required for NCR
            if field == 'province':
                region_value = self.data.get('region', None) or self.initial.get('region', None)
                # Convert PSGC code to Django code if needed
                if region_value in self.PSGC_TO_DJANGO_REGION:
                    region_value = self.PSGC_TO_DJANGO_REGION[region_value]
                if region_value == 'NCR':
                    self.fields[field].required = False
                else:
                    self.fields[field].required = True
            else:
                self.fields[field].required = True

    def clean_region(self):
        region = self.cleaned_data.get('region')
        if region:
            # Convert PSGC code to Django region code if it's a PSGC code
            if region in self.PSGC_TO_DJANGO_REGION:
                return self.PSGC_TO_DJANGO_REGION[region]
            # If it's already a Django code, validate it's in choices
            valid_codes = [choice[0] for choice in models.Customer.REGION_CHOICES]
            if region in valid_codes:
                return region
            # If neither, raise validation error
            raise forms.ValidationError(f"Invalid region code: {region}")
        return region

    class Meta:
        model = models.Customer
        fields = ['street_address', 'citymun', 'province', 'barangay', 'postal_code', 'mobile', 'profile_pic', 'region']
        widgets = {
            'citymun': forms.Select(choices=[]),
            'province': forms.Select(choices=[]),
            'barangay': forms.Select(choices=[]),
        }

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        province = cleaned_data.get('province')
        
        # For NCR, set province to 'NCR' if not provided
        if region == 'NCR':
            if not province:
                cleaned_data['province'] = 'NCR'
        elif not province:
            # For non-NCR regions, province is required
            self.add_error('province', 'Province is required for this region.')
        
        return cleaned_data


# Edit Profile form without address fields
class CustomerNonAddressForm(forms.ModelForm):
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        # Accepts format: 956 837 0169 (10 digits, 2 spaces)
        pattern = r'^\d{3} \d{3} \d{4}$'
        if not re.match(pattern, mobile):
            raise forms.ValidationError("Enter number as '956 837 0169' (10 digits, spaces required).")
        return mobile

    class Meta:
        model = models.Customer
        fields = ['mobile', 'profile_pic']


# Extended signup form with privacy agreement
class CustomerSignupForm(CustomerForm):
    def clean_mobile(self):
        return super().clean_mobile()
    privacy_policy = forms.BooleanField(
        required=True,
        label='I agree to the Privacy Policy',
        error_messages={'required': 'You must accept the privacy policy to create an account'}
    )

    class Meta(CustomerForm.Meta):
        fields = CustomerForm.Meta.fields + ['region']


# Multi-step signup forms
class PersonalInformationForm(forms.ModelForm):
    """Step 1: Personal Information"""
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        import re
        # Accepts format: 956 837 0169 (10 digits, 2 spaces)
        pattern = r'^\d{3} \d{3} \d{4}$'
        if not re.match(pattern, mobile):
            raise forms.ValidationError("Enter number as '956 837 0169' (10 digits, spaces required).")
        return mobile

    class Meta:
        model = models.Customer
        fields = ['mobile']

    # Add User fields
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)


class AccountSecurityForm(forms.ModelForm):
    """Step 2: Account Security"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), 
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), 
        label="Confirm Password"
    )
    privacy_policy = forms.BooleanField(
        required=True,
        label='I agree to the Privacy Policy',
        error_messages={'required': 'You must accept the privacy policy to create an account'}
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Unable to use this username. Please choose another.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password):
                raise forms.ValidationError("Password must include at least one uppercase letter.")
            if not re.search(r'\d', password):
                raise forms.ValidationError("Password must include at least one number.")
            if not re.search(r'[!@#$%*]', password):
                raise forms.ValidationError("Password must include at least one symbol (e.g., !, @, #, $, %, *).")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")


class ShippingAddressForm(forms.ModelForm):
    """Step 3: Shipping Address"""
    region = forms.CharField(max_length=100)
    province = forms.CharField(max_length=100, required=False)
    citymun = forms.CharField(max_length=100, required=False)
    barangay = forms.CharField(max_length=100, required=False)

    # PSGC to Django region code mapping
    PSGC_TO_DJANGO_REGION = {
        '010000000': 'R1',   # Ilocos Region
        '020000000': 'R2',   # Cagayan Valley
        '030000000': 'R3',   # Central Luzon
        '040000000': 'R4A',  # CALABARZON
        '170000000': 'R4B',  # MIMAROPA
        '050000000': 'R5',   # Bicol Region
        '060000000': 'R6',   # Western Visayas
        '070000000': 'R7',   # Central Visayas
        '080000000': 'R8',   # Eastern Visayas
        '090000000': 'R9',   # Zamboanga Peninsula
        '100000000': 'R10',  # Northern Mindanao
        '110000000': 'R11',  # Davao Region
        '120000000': 'R12',  # SOCCSKSARGEN
        '130000000': 'NCR',  # National Capital Region
        '140000000': 'CAR',  # Cordillera Administrative Region
        '160000000': 'R13',  # Caraga
        '150000000': 'BARMM' # Bangsamoro Autonomous Region in Muslim Mindanao
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].choices = models.Customer.REGION_CHOICES
        self.fields['region'].widget = forms.Select()
        self.fields['region'].required = True
        # Remove city and barangay logic, use citymun, province, barangay
        for field in ['citymun', 'province', 'barangay']:
            value = self.data.get(field, None) or self.initial.get(field, None)
            if value:
                self.fields[field].choices = [(value, value)]
            else:
                self.fields[field].choices = []
            self.fields[field].widget = forms.Select()
            # Province is not required for NCR
            if field == 'province':
                region_value = self.data.get('region', None) or self.initial.get('region', None)
                # Convert PSGC code to Django code if needed
                if region_value in self.PSGC_TO_DJANGO_REGION:
                    region_value = self.PSGC_TO_DJANGO_REGION[region_value]
                if region_value == 'NCR':
                    self.fields[field].required = False
                else:
                    self.fields[field].required = True
            else:
                self.fields[field].required = True

    def clean_region(self):
        region = self.cleaned_data.get('region')
        if region:
            # Convert PSGC code to Django region code if it's a PSGC code
            if region in self.PSGC_TO_DJANGO_REGION:
                return self.PSGC_TO_DJANGO_REGION[region]
            # If it's already a Django code, validate it's in choices
            valid_codes = [choice[0] for choice in models.Customer.REGION_CHOICES]
            if region in valid_codes:
                return region
            # If neither, raise validation error
            raise forms.ValidationError(f"Invalid region code: {region}")
        return region

    class Meta:
        model = models.Customer
        fields = ['street_address', 'citymun', 'province', 'barangay', 'postal_code', 'region']
        widgets = {
            'citymun': forms.Select(choices=[]),
            'province': forms.Select(choices=[]),
            'barangay': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        province = cleaned_data.get('province')
        
        # For NCR, set province to 'NCR' if not provided
        if region == 'NCR' and not province:
            cleaned_data['province'] = 'NCR'
        
        return cleaned_data


# Product creation and update form
class ProductForm(forms.ModelForm):
    size = forms.ChoiceField(choices=[
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    ], required=True)
    quantity = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = models.Product
        fields = ['name', 'price', 'description', 'product_image', 'quantity', 'size']


# Address form during checkout or delivery
class AddressForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput())
    mobile = forms.CharField(max_length=15, widget=forms.TextInput())

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        import re
        digits = re.sub(r'\D', '', mobile)
        if digits.startswith('63'):
            digits = '0' + digits[2:]
        if len(digits) != 11 or not digits.startswith('09'):
            raise forms.ValidationError('Enter a valid Philippine mobile number (e.g., 09568370169).')
        return digits
    address = forms.CharField(max_length=500, widget=forms.Textarea(attrs={'rows': 3}))


# Feedback form from customers
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = models.Feedback
        fields = ['name', 'feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 3})
        }


# For updating order status and delivery details
class OrderForm(forms.ModelForm):
    class Meta:
        model = models.Orders
        fields = ['status', 'estimated_delivery_date', 'notes']
        widgets = {
            'estimated_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.instance.pk:  # Updating an existing order
            original = models.Orders.objects.get(pk=self.instance.pk)
            if instance.status != original.status:
                instance.status_updated_at = timezone.now()
        else:  # New order
            instance.status_updated_at = timezone.now()
        if commit:
            instance.save()
        return instance


# Contact us page form
class ContactusForm(forms.Form):
    name = forms.CharField(max_length=30, widget=forms.TextInput())
    email = forms.EmailField(widget=forms.EmailInput())
    message = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 30})
    )


# Inventory management form for staff
class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'quantity', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


# Login form for customers
class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username', max_length=100, widget=forms.TextInput())
    password = forms.CharField(label='Password', widget=forms.PasswordInput())
