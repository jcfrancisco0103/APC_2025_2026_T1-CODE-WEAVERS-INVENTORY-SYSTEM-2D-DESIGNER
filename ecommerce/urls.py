from django.contrib import admin
from django.urls import path, include
from ecom import views
from ecom import wishlist_views
from django.contrib.auth.views import LoginView,LogoutView
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from ecom.views import manage_inventory, update_stock 
from ecom.views import delete_inventory, edit_inventory, bulk_update_orders
from django.conf import settings
from django.conf.urls.static import static
from ecom.views import admin_manage_inventory_view
from ecom import api_views
from ecom import chatbot_views




urlpatterns = [
    path('admin/', admin.site.urls),
    # Include Django auth URLs to provide password reset and related named routes
    path('', include('django.contrib.auth.urls')),
    path('accounts/login/', RedirectView.as_view(url=reverse_lazy('customerlogin')), name='accounts-login-redirect'),
    path('manage-inventory', manage_inventory, name='manage-inventory'),
    path('update-stock/<int:item_id>/', update_stock, name='update-stock'),
    path('',views.home_view,name=''),
    path('afterlogin', views.afterlogin_view,name='afterlogin'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('customerlogin')), name='logout'),
    path('about', views.aboutus_view, name='about'),
    path('contactus', views.contactus_view,name='contactus'),
    path('search', views.search_view,name='search'),
    path('send-feedback', views.send_feedback_view,name='send-feedback'),
    path('view-feedback', views.view_feedback_view,name='view-feedback'),
    path('user-profile/<int:user_id>/', views.user_profile_page, name='user_profile_page'),

    path('adminclick', views.adminclick_view),
    path('adminlogin', LoginView.as_view(template_name='ecom/adminlogin.html'),name='adminlogin'),
    path('admin-dashboard', views.admin_dashboard_view,name='admin-dashboard'),

    path('view-customer', views.admin_view_users,name='view-customer'),

    # Added URL pattern for update-user to fix NoReverseMatch
    path('update-user/<int:pk>/', views.update_customer_view, name='update-user'),

    # Added URL pattern for bulk-update-users to fix NoReverseMatch
    path('bulk-update-users/', views.bulk_update_users, name='bulk-update-users'),

    # Added URL pattern for create-user to fix NoReverseMatch
    # Removed the create-user URL pattern as create_user_view does not exist
    path('delete-customer/<int:pk>', views.delete_customer_view,name='delete-customer'),
    path('update-customer/<int:pk>', views.update_customer_view,name='update-customer'),

    # New URL for admin_view_users.html
    path('admin-view-users', views.admin_view_users, name='admin-view-users'),

    path('admin-products', views.admin_products_view,name='admin-products'),
    path('admin-add-product', views.admin_add_product_view,name='admin-add-product'),
    path('bulk-update-orders/', bulk_update_orders, name='bulk-update-orders'),
    
    # Automated Delivery System URLs
    path('quick-progress-order/<int:order_id>/', views.quick_progress_order, name='quick-progress-order'),
    path('bulk-progress-orders/', views.bulk_progress_orders, name='bulk-progress-orders'),
    path('generate-magic-link/<int:order_id>/', views.generate_magic_link, name='generate-magic-link'),
    path('delivery/update/<str:token>/<str:action>/', views.magic_link_update, name='magic-link-update'),
    path('delivery/status/<str:token>/', views.delivery_status_page, name='delivery-status-page'),
    
    # Admin Automated Delivery API URLs
    path('api/admin/initiate-delivery/<int:order_id>/', views.initiate_automated_delivery, name='api-initiate-delivery'),
    path('api/admin/track-delivery/<int:order_id>/', views.track_delivery_status, name='api-track-delivery'),
    path('api/admin/mark-delivered/<int:order_id>/', views.mark_order_delivered, name='api-mark-delivered'),
    
    path('delete-product/<int:pk>', views.delete_product_view,name='delete-product'),
    path('update-product/<int:pk>', views.update_product_view,name='update-product'),

    path('admin-view-booking', views.admin_view_booking_view, name='admin-view-booking'),
    path('admin-view-processing-orders', views.admin_view_processing_orders, name='admin-view-processing-orders'),
    path('admin-view-confirmed-orders', views.admin_view_confirmed_orders, name='admin-view-confirmed-orders'),
    path('admin-view-shipping-orders', views.admin_view_shipping_orders, name='admin-view-shipping-orders'),
    path('admin-view-delivered-orders', views.admin_view_delivered_orders, name='admin-view-delivered-orders'),
    path('admin-view-cancelled-orders', views.admin_view_cancelled_orders, name='admin-view-cancelled-orders'),
    path('admin-view-pre-orders', views.admin_view_pre_orders, name='admin-view-pre-orders'),
    path('admin/orders/<int:order_id>/detail/', views.admin_order_detail_ajax, name='admin-order-detail-ajax'),
    path('delete-order/<int:pk>', views.delete_order_view,name='delete-order'),
    path('update-order/<int:pk>', views.update_order_view,name='update-order'),




    # Named route for signup to fix NoReverseMatch in templates
    path('customersignup', views.customer_signup_view, name='signup'),
    path('customerlogin', LoginView.as_view(template_name='ecom/customerlogin.html'),name='customerlogin'),
    path('customer-home', views.customer_home_view,name='customer-home'),
    path('orders/pending/', views.pending_orders_view, name='pending-orders'),
    path('orders/to-ship/', views.to_ship_orders_view, name='to-ship-orders'),
    path('orders/to-receive/', views.to_receive_orders_view, name='to-receive-orders'),
    path('orders/delivered/', views.delivered_orders_view, name='delivered-orders'),
    path('orders/cancelled/', views.cancelled_orders_view, name='cancelled-orders'),
    path('my-order', views.my_order_view, name='my-order'),
    path('my-order/<int:pk>', views.my_order_view_pk, name='my-order-pk'),
    path('my-profile', views.my_profile_view,name='my-profile'),
    path('edit-profile', views.edit_profile_view,name='edit-profile'),
    path('download-invoice/<int:order_id>/', views.download_invoice_view, name='download-invoice'),
    path('customer/confirm-received/<int:order_id>/', views.customer_confirm_received, name='customer-confirm-received'),
    path('add-to-cart/<int:pk>/', views.add_to_cart_view,name='add-to-cart'),
    path('cart', views.cart_view,name='cart'),
    path('remove-from-cart/<int:pk>', views.remove_from_cart_view,name='remove-from-cart'),
    path('remove-custom-item/<int:pk>/', views.remove_custom_item_view, name='remove-custom-item'),
    path('customer-address', views.customer_address_view,name='customer-address'),
    path('payment-success/', views.payment_success_view,name='payment-success'),
    path('customizer/', views.jersey_customizer, name='customizer'),
    path('jersey-customizer/advanced/', views.jersey_customizer_advanced_view, name='jersey-customizer-advanced'),

    path('home', views.home,name='home'),
    # Removed the view_customer URL pattern as view_customer_view no longer exists
    # path('view_customer', views.view_customer_view, name='view_customer'),
    path('update-order/<int:pk>', views.update_order_view,name='update-order'),
    path('delete-order/<int:pk>', views.delete_order_view,name='delete-order'),
    path('facebook/', RedirectView.as_view(url='https://www.facebook.com/worksteamwear'), name='facebook'),
    path('instagram/', RedirectView.as_view(url='https://www.instagram.com/worksteamwear/'), name='instagram'),
    path('create/', views.create, name='create'),
    path('jersey-customizer/3d/', views.jersey_customizer_3d_view, name='jersey_customizer_3d'),
    path('jersey-customizer/advanced/', views.jersey_customizer_advanced_view, name='jersey_customizer_advanced'),
    path('jersey-customizer/', views.jersey_customizer, name='jersey_customizer'),
    path('jersey-template/', views.jersey_template, name='jersey_template'),
    path('interactive-jersey/', views.interactive_jersey, name='interactive_jersey'),
    path('delete-inventory/<int:item_id>/', delete_inventory, name='delete_inventory'),
    path('edit-inventory/<int:item_id>/', edit_inventory, name='edit_inventory'), 
    path('place-order/', views.place_order, name='place_order'),
    path('cancel-order/<int:order_id>', views.cancel_order_view, name='cancel-order'),
    path('add-custom-jersey-to-cart/', views.add_custom_jersey_to_cart, name='add-custom-jersey-to-cart'),
    path('pay-with-gcash/', views.create_gcash_payment, name='pay_with_gcash'),
    path('payment-success/', views.payment_success_view, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('update-address/', views.update_address, name='update-address'),
    path('admin-manage-inventory/', admin_manage_inventory_view, name='admin-manage-inventory'),

    # PSGC address APIs for cascade
    path('api/regions/', api_views.get_regions, name='api-regions'),
    path('api/provinces/', api_views.get_provinces, name='api-provinces'),
    path('api/cities/', api_views.get_cities, name='api-cities'),
    path('api/barangays/', api_views.get_barangays, name='api-barangays'),

    # PSGC API proxy endpoints
    path('api/regions/', api_views.get_regions, name='api-regions'),
    path('api/provinces/', api_views.get_provinces, name='api-provinces'),
    path('api/cities/', api_views.get_cities, name='api-cities'),
    path('api/barangays/', api_views.get_barangays, name='api-barangays'),
    
    # AI Design Generation API
    path('api/generate-ai-design/', api_views.generate_ai_design, name='api-generate-ai-design'),
    path('save-address/', views.save_new_address, name='save-address'),
    path('get-saved-addresses/', views.get_saved_addresses, name='get-saved-addresses'),
    path('set-default-address/<int:address_id>/', views.set_default_address, name='set-default-address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete-address'),
    
    # Wishlist functionality
    path('add-to-wishlist/<int:product_id>/', wishlist_views.add_to_wishlist, name='add-to-wishlist'),
    path('remove-from-wishlist/<int:product_id>/', wishlist_views.remove_from_wishlist, name='remove-from-wishlist'),
    path('wishlist/', wishlist_views.wishlist_view, name='wishlist'),
    
    # Product reviews
    path('add-review/<int:product_id>/', wishlist_views.add_review, name='add-review'),
    path('product/<int:product_id>/', wishlist_views.product_detail_view, name='product-detail'),
    
    # Newsletter
    path('newsletter-signup/', wishlist_views.newsletter_signup, name='newsletter-signup'),
    
    # Enhanced search API
    path('api/search/', wishlist_views.search_products_api, name='search-api'),
    
    # Chatbot URLs
    path('chatbot/', chatbot_views.chatbot_widget, name='chatbot-widget'),
    path('api/chatbot/send-message/', chatbot_views.chat_message, name='chatbot-send-message'),
    path('api/chatbot/history/', chatbot_views.chat_history, name='chatbot-history'),
    path('api/chatbot/feedback/', chatbot_views.chat_feedback, name='chatbot-feedback'),
    
    # Chatbot Admin Handover URLs
    path('api/admin/pending-handovers/', chatbot_views.admin_pending_handovers, name='admin-pending-handovers'),
    path('api/admin/take-handover/', chatbot_views.admin_take_handover, name='admin-take-handover'),
    path('api/admin/send-message/', chatbot_views.admin_send_message, name='admin-send-message'),
    path('api/admin/resolve-handover/', chatbot_views.admin_resolve_handover, name='admin-resolve-handover'),
    path('api/admin/clear-all-chats/', chatbot_views.admin_clear_all_chats, name='admin-clear-all-chats'),
    
    # Customer Support Chat URLs
    path('api/support/start-session/', chatbot_views.support_start_session, name='support-start-session'),
    path('api/support/send-message/', chatbot_views.support_send_message, name='support-send-message'),
    path('api/support/chat-history/', chatbot_views.support_chat_history, name='support-chat-history'),
    path('api/support/new-messages/', chatbot_views.support_new_messages, name='support-new-messages'),
    path('api/support/request-new-agent/', chatbot_views.support_request_new_agent, name='support-request-new-agent'),
    
    # AI Designer
    path('ai-designer/', views.ai_designer_view, name='ai-designer'),

    # Admin Transactions
    path('admin-transactions/', views.admin_transactions_view, name='admin-transactions'),

    # Report Management URLs
    path('reports/', views.reports_dashboard_view, name='reports-dashboard'),
    path('reports/sales/', views.sales_report_view, name='sales-report'),
    path('reports/customer/', views.customer_report_view, name='customer-report'),
    path('reports/inventory/', views.inventory_report_view, name='inventory-report'),
    path('reports/product/', views.product_report_view, name='product-report'),
    path('reports/export/', views.export_report_view, name='export-report'),
    path('reports/generate/', views.generate_report_view, name='generate-report'),

    # Custom Jersey Order API
    path('api/add-custom-order/', views.add_custom_order, name='api-add-custom-order'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
