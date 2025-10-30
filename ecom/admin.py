from django.contrib import admin
from .models import Customer, Product, Orders, Feedback, OrderItem, Address, ChatSession, ChatMessage, ChatbotKnowledge
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['region', 'province', 'city_municipality', 'barangay', 'street', 'postal_code']
    search_fields = ['region', 'province', 'city_municipality', 'barangay', 'street', 'postal_code']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'mobile', 'region_name', 'province_name', 'citymun_name', 'barangay_name']
    list_filter = ['region', 'province', 'citymun', 'barangay']
    search_fields = ['user__first_name', 'user__last_name', 'region', 'province', 'citymun', 'barangay', 'street_address']

    def region_name(self, obj):
        from ecom.utils import get_region_name
        return get_region_name(obj.region) if obj.region else ''
    region_name.short_description = 'Region'

    def province_name(self, obj):
        from ecom.utils import get_province_name
        return get_province_name(obj.province) if obj.province else ''
    province_name.short_description = 'Province'

    def citymun_name(self, obj):
        from ecom.utils import get_citymun_name
        return get_citymun_name(obj.citymun) if obj.citymun else ''
    citymun_name.short_description = 'City/Municipality'

    def barangay_name(self, obj):
        from ecom.utils import get_barangay_name
        return get_barangay_name(obj.barangay) if obj.barangay else ''
    barangay_name.short_description = 'Barangay'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'size']
    list_filter = ['size']
    search_fields = ['name', 'description']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'quantity', 'price')
    extra = 0  # Don't show extra empty forms
    can_delete = False  # Prevent deletion of order items

class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_ref', 'customer', 'status', 'payment_method', 'address', 
        'mobile', 'email', 'order_date', 'created_at', 'estimated_delivery_date'
    )
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('order_ref', 'customer__user__first_name', 'customer__user__last_name', 'mobile', 'email', 'address')
    inlines = [OrderItemInline]
    
    # Make customer order details read-only to protect order integrity
    readonly_fields = (
        'created_at', 'updated_at', 'customer', 'email', 'address', 'mobile', 
        'order_date', 'payment_method', 'transaction_id', 'order_ref', 
        'delivery_fee', 'delivery_proof_photo', 'customer_received_at',
        'cancellation_reason', 'cancellation_requested_at', 'cancellation_approved_by',
        'cancellation_approved_at', 'refund_processed', 'refund_amount', 
        'refund_processed_at', 'refund_processed_by'
    )
    
    # Fields that can be edited by admin (operational fields only)
    fields = (
        # Read-only customer and order information
        ('order_ref', 'customer', 'order_date'),
        ('email', 'mobile'),
        ('address',),
        ('payment_method', 'transaction_id'),
        ('delivery_fee',),
        
        # Editable operational fields
        ('status', 'estimated_delivery_date'),
        ('notes',),
        
        # Cancellation information (read-only)
        ('cancellation_status', 'cancellation_reason'),
        ('cancellation_requested_at', 'cancellation_approved_by', 'cancellation_approved_at'),
        ('cancellation_admin_notes',),
        
        # Delivery tracking (read-only customer proof, editable admin fields)
        ('delivery_proof_photo', 'customer_received_at'),
        
        # Refund information (read-only)
        ('refund_processed', 'refund_amount', 'refund_processed_at', 'refund_processed_by'),
        
        # Timestamps (read-only)
        ('created_at', 'updated_at'),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of orders to maintain data integrity"""
        return False

admin.site.register(Orders, OrderAdmin)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']
    search_fields = ['name', 'feedback']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'customer', 'handover_status', 'created_at', 'is_active']
    list_filter = ['handover_status', 'is_active', 'created_at']
    search_fields = ['session_id', 'customer__first_name', 'customer__last_name']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'admin_user')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['content', 'session__session_id']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'admin_user')


@admin.register(ChatbotKnowledge)
class ChatbotKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['category', 'question', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer', 'keywords']
    readonly_fields = ['created_at', 'updated_at']

# Customize Django Admin Site
admin.site.site_header = "WorksTeamWear Administration"
admin.site.site_title = "WorksTeamWear Admin Portal"
admin.site.index_title = "Welcome to WorksTeamWear Administration"