from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import uuid
from .models import EmailVerification


def send_verification_email(user, request):
    """Send verification email to user"""
    try:
        # Get or create email verification record
        email_verification, created = EmailVerification.objects.get_or_create(
            user=user,
            defaults={'verification_token': uuid.uuid4()}
        )
        
        # If not created and not verified, generate new token
        if not created and not email_verification.is_verified:
            email_verification.verification_token = uuid.uuid4()
            email_verification.save()
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            reverse('verify_email', kwargs={'token': email_verification.verification_token})
        )
        
        # Prepare email content
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'WorksTeamWear'
        }
        
        html_message = render_to_string('ecom/email/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject='Verify Your Email Address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ Verification email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_email_view(request, token):
    """Verify email using token"""
    try:
        email_verification = get_object_or_404(EmailVerification, verification_token=token)
        
        if email_verification.is_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('customerlogin')
        
        if email_verification.is_token_expired():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('resend_verification')
        
        # Verify the email
        email_verification.verify_email()
        messages.success(request, 'Your email has been successfully verified! You can now log in.')
        return redirect('customerlogin')
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('customerlogin')


def resend_verification_view(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Please provide your email address.')
            return render(request, 'ecom/resend_verification.html')
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
            email_verification = EmailVerification.objects.get(user=user)
            
            if email_verification.is_verified:
                messages.info(request, 'This email is already verified. You can log in now.')
                return redirect('customerlogin')
            
            # Send new verification email
            if send_verification_email(user, request):
                messages.success(request, 'Verification email sent successfully! Please check your inbox.')
            else:
                messages.error(request, 'Failed to send verification email. Please try again.')
                
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
        except EmailVerification.DoesNotExist:
            messages.error(request, 'No verification record found for this email.')
            
        return render(request, 'ecom/resend_verification.html')
    
    return render(request, 'ecom/resend_verification.html')


@csrf_exempt
def check_verification_status(request):
    """AJAX endpoint to check email verification status"""
    if request.method == 'GET' and request.user.is_authenticated:
        try:
            email_verification = EmailVerification.objects.get(user=request.user)
            return JsonResponse({
                'is_verified': email_verification.is_verified,
                'verified_at': email_verification.verified_at.isoformat() if email_verification.verified_at else None
            })
        except EmailVerification.DoesNotExist:
            return JsonResponse({'is_verified': False, 'verified_at': None})
    
    return JsonResponse({'error': 'Unauthorized'}, status=401)


def verification_required_view(request):
    """View to show when email verification is required"""
    if request.user.is_authenticated:
        try:
            email_verification = EmailVerification.objects.get(user=request.user)
            if email_verification.is_verified:
                return redirect('home')
        except EmailVerification.DoesNotExist:
            pass
    
    return render(request, 'ecom/verification_required.html')