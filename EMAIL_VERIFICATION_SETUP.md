# Email Verification Setup Guide

This guide explains how to set up real-time email verification using Gmail SMTP for your Django e-commerce application.

## Overview

The email verification system includes:
- **EmailVerification Model**: Tracks verification status and tokens
- **Automated Email Sending**: Sends verification emails upon registration
- **Real-time Status Checking**: AJAX-based verification status updates
- **Secure Token System**: UUID-based verification tokens with expiration
- **User-friendly Templates**: Professional email and web templates

## Gmail SMTP Configuration

### 1. Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Enable 2-Step Verification if not already enabled

### 2. Generate App Password
1. Go to Google Account → Security → App passwords
2. Select "Mail" as the app
3. Select "Other" as the device and name it (e.g., "Django App")
4. Copy the generated 16-character password

### 3. Environment Variables Setup

Create or update your `.env` file with the following variables:

```env
# Email Configuration
EMAIL_HOST_USER=your-gmail-address@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
EMAIL_RECEIVING_USER=admin@yourdomain.com

# Optional: For development
DEBUG=True
```

**Important Notes:**
- Use your Gmail address for `EMAIL_HOST_USER`
- Use the 16-character App Password (not your regular Gmail password) for `EMAIL_HOST_PASSWORD`
- Never commit these credentials to version control

## Features Implemented

### 1. User Registration Flow
- User registers with email address
- Account is created but set to inactive (`is_active=False`)
- Verification email is automatically sent
- User is redirected to verification required page

### 2. Email Verification Process
- Professional HTML email template with verification link
- Secure UUID token system
- Token expiration (24 hours by default)
- One-click verification via email link

### 3. Real-time Status Updates
- AJAX polling every 5 seconds on verification page
- Automatic redirect upon successful verification
- No page refresh required

### 4. User Experience Features
- Resend verification email functionality
- Clear status messages and feedback
- Mobile-responsive email templates
- Professional styling and branding

## URL Endpoints

The following endpoints have been added:

```python
# Email Verification URLs
path('verify-email/<uuid:token>/', views.verify_email_view, name='verify_email'),
path('resend-verification/', views.resend_verification_view, name='resend_verification'),
path('verification-required/', views.verification_required_view, name='verification_required'),
path('api/check-verification-status/', views.check_verification_status, name='check_verification_status'),
```

## Database Schema

### EmailVerification Model
```python
class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
```

## Testing the Implementation

### 1. Registration Test
1. Navigate to `/customersignup`
2. Fill out the registration form with a valid email
3. Submit the form
4. Check that you're redirected to verification required page
5. Check your email for the verification message

### 2. Email Verification Test
1. Open the verification email
2. Click the verification link
3. Verify you're redirected to login with success message
4. Try logging in with the verified account

### 3. Real-time Updates Test
1. Register a new account
2. Stay on the verification required page
3. Open email in another tab/device
4. Click verification link
5. Watch the page automatically redirect

## Troubleshooting

### Common Issues

**1. SMTPAuthenticationError**
- Ensure 2-Factor Authentication is enabled
- Use App Password, not regular Gmail password
- Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env

**2. Email Not Sending**
- Verify Gmail SMTP settings in settings.py
- Check if DEBUG mode affects email backend
- Ensure DEFAULT_FROM_EMAIL is set correctly

**3. Verification Link Not Working**
- Check URL patterns are correctly configured
- Verify token format in email template
- Ensure EmailVerification table exists in database

**4. Real-time Updates Not Working**
- Check JavaScript console for errors
- Verify AJAX endpoint is accessible
- Ensure user is authenticated for status checks

### Development vs Production

**Development Mode (DEBUG=True):**
- Emails are printed to console
- Use `console.EmailBackend` for testing
- No actual emails sent

**Production Mode (DEBUG=False):**
- Emails sent via Gmail SMTP
- Requires valid Gmail credentials
- Uses `smtp.EmailBackend`

## Security Considerations

1. **Token Security**: UUID tokens are cryptographically secure
2. **Token Expiration**: Tokens expire after 24 hours
3. **One-time Use**: Tokens are invalidated after successful verification
4. **HTTPS Required**: Use HTTPS in production for secure token transmission
5. **Rate Limiting**: Consider implementing rate limiting for resend functionality

## Customization Options

### Email Template Customization
- Edit `templates/ecom/email/verification_email.html`
- Customize branding, colors, and messaging
- Add company logo and contact information

### Verification Page Customization
- Edit `templates/ecom/verification_required.html`
- Modify polling interval (currently 5 seconds)
- Add additional user guidance or support links

### Token Expiration
- Modify `is_token_expired()` method in EmailVerification model
- Default: 24 hours, can be customized as needed

## Support

For issues or questions:
1. Check Django logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test email configuration in Django shell
4. Review Gmail security settings and App Password setup

The email verification system is now fully implemented and ready for use!