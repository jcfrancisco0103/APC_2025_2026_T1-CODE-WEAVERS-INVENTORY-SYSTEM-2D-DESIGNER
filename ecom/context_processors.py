"""
Context processors for ecom app
"""

def superadmin_context(request):
    """
    Context processor to provide SuperAdmin check to templates
    """
    is_superadmin = False
    
    if request.user.is_authenticated:
        try:
            is_superadmin = hasattr(request.user, 'superadmin') and request.user.superadmin.is_active
        except:
            is_superadmin = False
    
    return {
        'is_superadmin': is_superadmin,
    }