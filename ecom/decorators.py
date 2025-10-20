from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from . import models

def report_permission_required(report_type, permission_type='view'):
    """
    Decorator that checks if user has specific report permissions.
    
    Args:
        report_type: Type of report ('sales', 'customer', 'inventory', 'product')
        permission_type: Type of permission ('view', 'export', 'generate')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated and admin
            if not request.user.is_authenticated or not request.user.is_staff:
                messages.error(request, 'Access denied. Admin privileges required.')
                return redirect('adminlogin')
            
            # Superusers have access to all reports
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check specific report permissions
            try:
                report_access = models.ReportAccess.objects.get(
                    user=request.user,
                    report_type=report_type
                )
                
                # Check permission type
                if permission_type == 'view' and not report_access.can_view:
                    raise PermissionDenied("You don't have permission to view this report.")
                elif permission_type == 'export' and not report_access.can_export:
                    raise PermissionDenied("You don't have permission to export this report.")
                elif permission_type == 'generate' and not report_access.can_generate:
                    raise PermissionDenied("You don't have permission to generate this report.")
                
            except models.ReportAccess.DoesNotExist:
                # If no specific permission exists, deny access
                messages.error(request, f'Access denied. You do not have permission to access {report_type} reports.')
                return redirect('reports-dashboard')
            except PermissionDenied as e:
                messages.error(request, str(e))
                return redirect('reports-dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def any_report_permission_required(permission_type='view'):
    """
    Decorator that checks if user has any report permissions.
    Used for general report dashboard access.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated and admin
            if not request.user.is_authenticated or not request.user.is_staff:
                messages.error(request, 'Access denied. Admin privileges required.')
                return redirect('adminlogin')
            
            # Superusers have access to all reports
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has any report permissions
            has_permission = models.ReportAccess.objects.filter(
                user=request.user
            ).exists()
            
            if not has_permission:
                messages.error(request, 'Access denied. You do not have permission to access reports.')
                return redirect('admin-dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def export_permission_required(view_func):
    """
    Decorator specifically for export functionality.
    Checks if user has export permissions for the requested report type.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated and admin
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('adminlogin')
        
        # Superusers have access to all exports
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Get report type from URL parameters or request
        report_type = kwargs.get('report_type') or request.GET.get('report_type')
        
        if not report_type:
            messages.error(request, 'Invalid report type specified.')
            return redirect('reports-dashboard')
        
        # Check export permission for specific report type
        try:
            report_access = models.ReportAccess.objects.get(
                user=request.user,
                report_type=report_type
            )
            
            if not report_access.can_export:
                messages.error(request, f'You do not have permission to export {report_type} reports.')
                return redirect('reports-dashboard')
                
        except models.ReportAccess.DoesNotExist:
            messages.error(request, f'Access denied. You do not have permission to access {report_type} reports.')
            return redirect('reports-dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper