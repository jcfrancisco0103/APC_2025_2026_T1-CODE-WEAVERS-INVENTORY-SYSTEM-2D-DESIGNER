from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
import uuid
# Create your models here.
class Customer(models.Model):
    REGION_CHOICES = [
        ('NCR', 'National Capital Region'),
        ('CAR', 'Cordillera Administrative Region'),
        ('R1', 'Ilocos Region'),
        ('R2', 'Cagayan Valley'),
        ('R3', 'Central Luzon'),
        ('R4A', 'CALABARZON'),
        ('R4B', 'MIMAROPA'),
        ('R5', 'Bicol Region'),
        ('R6', 'Western Visayas'),
        ('R7', 'Central Visayas'),
        ('R8', 'Eastern Visayas'),
        ('R9', 'Zamboanga Peninsula'),
        ('R10', 'Northern Mindanao'),
        ('R11', 'Davao Region'),
        ('R12', 'SOCCSKSARGEN'),
        ('R13', 'Caraga'),
        ('BARMM', 'Bangsamoro Autonomous Region in Muslim Mindanao'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/CustomerProfilePic/', null=True, blank=True)
    region = models.CharField(max_length=100, choices=REGION_CHOICES)
    province = models.CharField(max_length=100, blank=True, null=True)
    citymun = models.CharField(max_length=100, blank=True, null=True)
    barangay = models.CharField(max_length=100, blank=True, null=True)
    street_address = models.CharField(max_length=100)
    postal_code = models.PositiveIntegerField()
    mobile = models.CharField(max_length=13, help_text="Enter 10 digits, e.g. '956 837 0169'")

    @property
    def get_full_address(self):
        # Return formatted address with actual names
        from .utils import get_region_name, get_province_name, get_citymun_name, get_barangay_name
        
        region_name = get_region_name(self.region) if self.region else self.region
        province_name = get_province_name(self.province) if self.province else self.province
        citymun_name = get_citymun_name(self.citymun) if self.citymun else self.citymun
        barangay_name = get_barangay_name(self.barangay) if self.barangay else self.barangay
        
        return f"{self.street_address}, {barangay_name}, {citymun_name}, {province_name}, {region_name}, {self.postal_code}"

    @property
    def region_name(self):
        """Get the readable region name"""
        from .utils import get_region_name
        return get_region_name(self.region) if self.region else self.region

    @property
    def province_name(self):
        """Get the readable province name"""
        from .utils import get_province_name
        return get_province_name(self.province) if self.province else self.province

    @property
    def citymun_name(self):
        """Get the readable city/municipality name"""
        from .utils import get_citymun_name
        return get_citymun_name(self.citymun) if self.citymun else self.citymun

    @property
    def barangay_name(self):
        """Get the readable barangay name"""
        from .utils import get_barangay_name
        return get_barangay_name(self.barangay) if self.barangay else self.barangay

    def __str__(self):
        return self.user.first_name

    @property
    def customer_code(self):
        # Format user id with prefix and zero padding, e.g. CUST000123
        return f"CUST{self.user.id:06d}"

    @property
    def status(self):
        return "Active" if self.user.is_active else "Inactive"


class InventoryItem(models.Model):
    name = models.CharField(max_length=50)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=40)
    product_image = models.ImageField(upload_to='product_image/', null=True, blank=True)
    price = models.PositiveIntegerField()
    description = models.CharField(max_length=40)
    quantity = models.PositiveIntegerField(default=0)
    SIZE_CHOICES = (
        ('S', 'Small'),
        ('XS', 'Extra Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
    )
    size = models.CharField(max_length=2, choices=SIZE_CHOICES, default='M')
    
    def __str__(self):
        return self.name

    def get_size_stock(self):
        stock = {size: 0 for size, _ in self.SIZE_CHOICES}
        for size, _ in self.SIZE_CHOICES:
            item = InventoryItem.objects.filter(name=f"{self.name} - {size}").first()
            if item:
                stock[size] = item.quantity
            elif self.size == size:
                stock[size] = self.quantity
        return stock

    def get_size_stock_json(self):
        import json
        return json.dumps(self.get_size_stock())

class CartItem(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=Product.SIZE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('customer', 'product', 'size')
    
    def __str__(self):
        return f"{self.customer.user.username} - {self.product.name} ({self.size})"



class Orders(models.Model):
    STATUS = (
        ('Pending', 'Pending - Awaiting Payment'),
        ('Processing', 'Processing - Payment Confirmed'),
        ('Order Confirmed', 'Order Confirmed - In Production'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancellation Requested', 'Waiting for approval of Cancellation'),
        ('Cancelled', 'Cancelled')
    )
    PAYMENT_METHODS = (
        ('cod', 'Cash on Delivery'),
        ('paypal', 'PayPal'),
        ('gcash', 'GCash')
    )
    
    CANCELLATION_STATUS = (
        ('none', 'No Cancellation Request'),
        ('requested', 'Cancellation Requested'),
        ('approved', 'Cancellation Approved'),
        ('rejected', 'Cancellation Rejected')
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text='When the order was created')
    updated_at = models.DateTimeField(auto_now=True, help_text='When the order was last updated')
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=True)
    email = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=500, null=True)
    mobile = models.CharField(max_length=20, null=True)
    order_date = models.DateField(auto_now_add=True, null=True, help_text='Date when order was placed')
    status = models.CharField(max_length=50, null=True, choices=STATUS, default='Pending', help_text='Current status of the order')
    status_updated_at = models.DateTimeField(null=True, blank=True, help_text='When the status was last changed')
    estimated_delivery_date = models.DateField(null=True, blank=True, help_text='Estimated delivery date')
    notes = models.TextField(blank=True, null=True, help_text='Additional notes about the order')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cod', help_text='Payment method for the order')
    transaction_id = models.CharField(max_length=100, null=True, blank=True, help_text='PayPal or GCash transaction ID for paid orders')
    order_ref = models.CharField(max_length=12, unique=True, null=True, blank=True, help_text='Unique short order reference ID')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Delivery fee for this order')
    delivery_proof_photo = models.ImageField(upload_to='delivery_proof/', null=True, blank=True, help_text='Customer uploaded proof of delivery photo')
    customer_received_at = models.DateTimeField(null=True, blank=True, help_text='When customer confirmed receipt with photo proof')
    
    # Cancellation approval fields
    cancellation_status = models.CharField(max_length=20, choices=CANCELLATION_STATUS, default='none', help_text='Status of cancellation request')
    cancellation_reason = models.TextField(blank=True, null=True, help_text='Reason provided by customer for cancellation')
    cancellation_requested_at = models.DateTimeField(null=True, blank=True, help_text='When cancellation was requested')
    cancellation_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_cancellations', help_text='Super Admin who approved/rejected the cancellation')
    cancellation_approved_at = models.DateTimeField(null=True, blank=True, help_text='When cancellation was approved/rejected')
    cancellation_admin_notes = models.TextField(blank=True, null=True, help_text='Admin notes regarding the cancellation decision')
    refund_processed = models.BooleanField(default=False, help_text='Whether refund has been processed for paid orders')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Amount refunded to customer')
    refund_processed_at = models.DateTimeField(null=True, blank=True, help_text='When refund was processed')
    refund_processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds', help_text='Admin who processed the refund')
    
    def __str__(self):
        return f"Order {self.order_ref or self.id} - {self.customer.user.username if self.customer else 'No Customer'}"
    
    def get_total_amount(self):
        """Calculate total amount from all order items including delivery fee"""
        items_total = sum(item.price * item.quantity for item in self.orderitem_set.all())
        return items_total + self.delivery_fee
    
    def can_request_cancellation(self):
        """Check if order can be cancelled by customer"""
        return (self.status in ['Pending', 'Processing', 'Order Confirmed'] and 
                self.cancellation_status == 'none')
    
    def is_paid_order(self):
        """Check if this is a paid order (PayPal or GCash)"""
        return self.payment_method in ['paypal', 'gcash']
    
    def request_cancellation(self, reason, customer_user):
        """Request cancellation of the order"""
        if self.can_request_cancellation():
            self.cancellation_status = 'requested'
            self.cancellation_reason = reason
            self.cancellation_requested_at = timezone.now()
            # Keep the original status instead of changing to 'Cancellation Requested'
            # self.status = 'Cancellation Requested'
            # self.status_updated_at = timezone.now()
            self.save()
            return True
        return False
    
    def approve_cancellation(self, admin_user, admin_notes=""):
        """Approve the cancellation request"""
        if self.cancellation_status == 'requested':
            self.cancellation_status = 'approved'
            self.cancellation_approved_by = admin_user
            self.cancellation_approved_at = timezone.now()
            self.cancellation_admin_notes = admin_notes
            self.status = 'Cancelled'
            self.status_updated_at = timezone.now()
            
            # Restore stock for each item in the order
            order_items = self.orderitem_set.all()
            for item in order_items:
                product = item.product
                product.quantity += item.quantity
                product.save()
            
            self.save()
            return True
        return False
    
    def reject_cancellation(self, admin_user, admin_notes=""):
        """Reject the cancellation request"""
        if self.cancellation_status == 'requested':
            self.cancellation_status = 'rejected'
            self.cancellation_approved_by = admin_user
            self.cancellation_approved_at = timezone.now()
            self.cancellation_admin_notes = admin_notes
            # Revert status back to original
            if self.status == 'Cancellation Requested':
                self.status = 'Pending'  # or determine appropriate status
                self.status_updated_at = timezone.now()
            self.save()
            return True
        return False

class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=5, choices=Product.SIZE_CHOICES, null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.name} ({self.size}) x{self.quantity} - Order {self.order.order_ref or self.order.id}"
    
    def get_total_price(self):
        """Calculate total price for this order item"""
        return self.price * self.quantity


class Feedback(models.Model):
    name=models.CharField(max_length=40)
    feedback=models.CharField(max_length=500)
    date= models.DateField(auto_now_add=True,null=True)

    def __str__(self):
        return self.name


# Address model for admin system
class Address(models.Model):
    region = models.CharField(max_length=100, help_text="Region name, e.g. 'Ilocos Region'")
    province = models.CharField(max_length=100, help_text="Province name, e.g. 'Ilocos Norte'")
    city_municipality = models.CharField(max_length=100, help_text="City/Municipality name, e.g. 'Laoag City'")
    barangay = models.CharField(max_length=100, help_text="Barangay name, e.g. 'Barangay 1'")
    street = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.street}, {self.barangay}, {self.city_municipality}, {self.province}, {self.region}, {self.postal_code}"

class ShippingFee(models.Model):
    courier = models.CharField(max_length=50)
    origin_region = models.CharField(max_length=50)
    destination_region = models.CharField(max_length=50)
    weight_kg = models.DecimalField(max_digits=4, decimal_places=2)
    price_php = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.courier}: {self.origin_region} to {self.destination_region} ({self.weight_kg}kg) - ₱{self.price_php}"



class SavedAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='saved_addresses')
    region = models.CharField(max_length=100, choices=Customer.REGION_CHOICES)
    province = models.CharField(max_length=100)
    citymun = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100)
    street_address = models.CharField(max_length=100)
    postal_code = models.PositiveIntegerField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-updated_at']

    def __str__(self):
        return f"{self.street_address}, {self.barangay}, {self.citymun}, {self.province}, {self.region}, {self.postal_code}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this customer to non-default
            SavedAddress.objects.filter(customer=self.customer).update(is_default=False)
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'product')

    def __str__(self):
        return f"{self.customer.user.username} - {self.product.name}"

class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('customer', 'product')

    def __str__(self):
        return f"{self.customer.user.username} - {self.product.name} ({self.rating} stars)"

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ChatSession(models.Model):
    HANDOVER_STATUS_CHOICES = (
        ('bot', 'Bot Handling'),
        ('requested', 'Admin Help Requested'),
        ('admin', 'Admin Handling'),
        ('resolved', 'Resolved'),
    )
    
    session_id = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    handover_status = models.CharField(max_length=20, choices=HANDOVER_STATUS_CHOICES, default='bot')
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_chats')
    handover_requested_at = models.DateTimeField(null=True, blank=True)
    admin_joined_at = models.DateTimeField(null=True, blank=True)
    handover_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Chat Session {self.session_id} ({self.handover_status})"


class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        ('user', 'User Message'),
        ('bot', 'Bot Response'),
        ('admin', 'Admin Response'),
        ('system', 'System Message'),
    )
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_helpful = models.BooleanField(null=True, blank=True)  # User feedback on bot responses
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_messages')

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class ChatbotKnowledge(models.Model):
    CATEGORY_CHOICES = (
        ('general', 'General Help'),
        ('ordering', 'Ordering Process'),
        ('products', 'Products & Inventory'),
        ('account', 'Account Management'),
        ('shipping', 'Shipping & Delivery'),
        ('payment', 'Payment Methods'),
        ('customization', 'Product Customization'),
        ('returns', 'Returns & Refunds'),
    )
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    keywords = models.TextField(help_text="Comma-separated keywords that trigger this response")
    question = models.CharField(max_length=200)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category}: {self.question}"

    def get_keywords_list(self):
        return [keyword.strip().lower() for keyword in self.keywords.split(',')]


# Automated Delivery System Models
class DeliveryMagicLink(models.Model):
    """Model to store magic links for external delivery status updates"""
    order = models.OneToOneField(Orders, on_delete=models.CASCADE, related_name='magic_link')
    token = models.CharField(max_length=64, unique=True, help_text="Unique token for the magic link")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this magic link expires")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Magic Link for Order {self.order.order_ref}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def get_status_url(self):
        """Get the URL for viewing delivery status"""
        return f"/delivery/status/{self.token}/"
    
    def get_update_url(self, action):
        """Get the URL for updating delivery status"""
        return f"/delivery/update/{self.token}/{action}/"


class DeliveryStatusLog(models.Model):
    """Model to track delivery status changes and updates"""
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='status_logs')
    previous_status = models.CharField(max_length=50, null=True, blank=True)
    new_status = models.CharField(max_length=50)
    updated_by = models.CharField(max_length=100, help_text="Who updated the status (admin, system, external)")
    update_method = models.CharField(max_length=50, help_text="How the status was updated (dashboard, magic_link, api)")
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Order {self.order.order_ref}: {self.previous_status} → {self.new_status}"


class BulkOrderOperation(models.Model):
    """Model to track bulk operations on orders"""
    OPERATION_TYPES = (
        ('status_update', 'Status Update'),
        ('bulk_progress', 'Bulk Progress'),
        ('export', 'Export Orders'),
    )
    
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    orders_affected = models.ManyToManyField(Orders, related_name='bulk_operations')
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    parameters = models.JSONField(help_text="Operation parameters (status, filters, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.get_operation_type_display()} by {self.performed_by.username} at {self.created_at}"


class CustomJerseyDesign(models.Model):
    """
    Store custom jersey design configurations for orders
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    jersey_type = models.CharField(max_length=50, default='jersey')  # Changed default to jersey
    collar_type = models.CharField(max_length=50, default='crew_neck')  # Changed default to crew_neck
    sleeve_type = models.CharField(max_length=50, default='short_sleeve')  # Added to fix NOT NULL constraint
    design_scale = models.FloatField(default=1.0)  # Added to fix NOT NULL constraint
    fabric_type = models.CharField(max_length=50, default='polyester')  # Added to fix NOT NULL constraint
    is_3d_design = models.BooleanField(default=False)  # Added to fix NOT NULL constraint
    logo_position_3d = models.JSONField(default=dict, help_text="3D logo position coordinates")  # Added to fix NOT NULL constraint
    text_position_3d = models.JSONField(default=dict, help_text="3D text position coordinates")  # Added to fix NOT NULL constraint
    primary_color = models.CharField(max_length=7, default='#000000')  # Hex color
    secondary_color = models.CharField(max_length=7, default='#ffffff')  # Hex color
    pattern = models.CharField(max_length=50, default='solid')
    front_number = models.CharField(max_length=10, blank=True, null=True)
    back_name = models.CharField(max_length=50, blank=True, null=True)
    back_number = models.CharField(max_length=10, blank=True, null=True)
    text_color = models.CharField(max_length=7, default='#000000')  # Hex color
    logo_placement = models.CharField(max_length=50, default='none')
    design_data = models.JSONField(help_text="Complete design configuration as JSON")
    design_image = models.ImageField(upload_to='custom_designs/', blank=True, null=True, help_text="Generated image of the custom jersey design")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Custom Jersey Design by {self.customer.user.username} - {self.created_at.strftime('%Y-%m-%d')}"


class CustomOrderItem(models.Model):
    """
    Extended order item for custom jersey designs
    """
    PRE_ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    custom_design = models.ForeignKey(CustomJerseyDesign, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=5, choices=Product.SIZE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    additional_info = models.TextField(blank=True, null=True)
    is_pre_order = models.BooleanField(default=False)
    pre_order_status = models.CharField(max_length=20, choices=PRE_ORDER_STATUS_CHOICES, default='pending', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Custom Jersey ({self.size}) x{self.quantity} - Order {self.order.order_ref or self.order.id}"
    
    def get_total_price(self):
        """Calculate total price for this custom order item"""
        return self.price * self.quantity


class EmailVerification(models.Model):
    """Model to handle email verification for user registration"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
    
    def __str__(self):
        return f"Email verification for {self.user.username} - {'Verified' if self.is_verified else 'Pending'}"
    
    def is_token_expired(self):
        """Check if verification token has expired (24 hours)"""
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() > expiry_time
    
    def verify_email(self):
        """Mark email as verified and activate user account"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.user.is_active = True
        self.save()
        self.user.save()




