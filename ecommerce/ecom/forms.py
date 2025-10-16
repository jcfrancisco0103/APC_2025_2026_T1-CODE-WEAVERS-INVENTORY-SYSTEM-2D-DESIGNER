from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from . import models
from .models import Product, InventoryItem
import re
from django.core.exceptions import ValidationError

# User registration form
class CustomerUserForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Unable to use this username. Please choose another.")
        return username

def validate_password_strength(value):
    """
    Validates password strength with the following rules:
    - At least 8 characters long
    - Include at least one uppercase letter
    - Include at least one number
    - Include at least one symbol (e.g. !, @, #, $, %)
    """
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', value):
        raise ValidationError("Password must include at least one uppercase letter.")
    if not re.search(r'[0-9]', value):
        raise ValidationError("Password must include at least one number.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError("Password must include at least one symbol (e.g. !, @, #, $, %).")


    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        # Password strength validation
        if password:
            validate_password_strength(password)


# Customer personal details form
class CustomerForm(forms.ModelForm):
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        import re
        # Accepts format: 956 837 0169 (10 digits, 2 spaces)
        pattern = r'^\d{3} \d{3} \d{4}$'
        if not re.match(pattern, mobile):
            raise forms.ValidationError("Enter number as '912 345 6789' (10 digits, spaces required).")
        return mobile
    region = forms.CharField(max_length=100)
    province = forms.CharField(max_length=100, required=False)
    citymun = forms.CharField(max_length=100, required=False)
    barangay = forms.CharField(max_length=100, required=False)

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
            self.fields[field].required = True

    class Meta:
        model = models.Customer
        fields = ['street_address', 'citymun', 'province', 'barangay', 'postal_code', 'mobile', 'profile_pic', 'region']
        widgets = {
            'citymun': forms.Select(choices=[]),
            'province': forms.Select(choices=[]),
            'barangay': forms.Select(choices=[]),
        }


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