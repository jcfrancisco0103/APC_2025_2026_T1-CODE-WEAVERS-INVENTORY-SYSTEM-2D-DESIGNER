"""
Refund utilities for processing refunds for PayPal and GCash payments
"""
import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class RefundProcessor:
    """
    Handles refund processing for different payment methods
    """
    
    def __init__(self):
        self.paypal_client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
        self.paypal_secret_key = getattr(settings, 'PAYPAL_SECRET_KEY', '')
        self.paypal_base_url = 'https://api.sandbox.paypal.com'  # Use sandbox for testing
        
    def get_paypal_access_token(self) -> Optional[str]:
        """
        Get PayPal access token for API calls
        """
        try:
            url = f"{self.paypal_base_url}/v1/oauth2/token"
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            data = 'grant_type=client_credentials'
            
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(self.paypal_client_id, self.paypal_secret_key)
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Failed to get PayPal access token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {str(e)}")
            return None
    
    def process_paypal_refund(self, transaction_id: str, amount: Decimal, currency: str = 'PHP') -> Tuple[bool, str, Dict]:
        """
        Process PayPal refund
        
        Args:
            transaction_id: PayPal transaction ID
            amount: Refund amount
            currency: Currency code (default: PHP)
            
        Returns:
            Tuple of (success, message, refund_data)
        """
        try:
            access_token = self.get_paypal_access_token()
            if not access_token:
                return False, "Failed to authenticate with PayPal", {}
            
            url = f"{self.paypal_base_url}/v2/payments/captures/{transaction_id}/refund"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            refund_data = {
                'amount': {
                    'value': str(amount),
                    'currency_code': currency
                },
                'note_to_payer': 'Refund for cancelled order'
            }
            
            response = requests.post(url, headers=headers, json=refund_data)
            
            if response.status_code in [200, 201]:
                refund_response = response.json()
                return True, "PayPal refund processed successfully", refund_response
            else:
                error_msg = f"PayPal refund failed: {response.text}"
                logger.error(error_msg)
                return False, error_msg, {}
                
        except Exception as e:
            error_msg = f"Error processing PayPal refund: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def process_gcash_refund(self, transaction_id: str, amount: Decimal) -> Tuple[bool, str, Dict]:
        """
        Process GCash refund
        
        Note: This is a placeholder implementation as GCash API integration
        would require specific API credentials and endpoints from GCash.
        
        Args:
            transaction_id: GCash transaction ID
            amount: Refund amount
            
        Returns:
            Tuple of (success, message, refund_data)
        """
        try:
            # Placeholder implementation
            # In a real implementation, you would:
            # 1. Get GCash API credentials from settings
            # 2. Make API call to GCash refund endpoint
            # 3. Handle the response
            
            logger.info(f"Processing GCash refund for transaction {transaction_id}, amount: {amount}")
            
            # For now, we'll simulate a successful refund
            # In production, replace this with actual GCash API integration
            refund_data = {
                'transaction_id': transaction_id,
                'refund_amount': str(amount),
                'status': 'pending',
                'refund_id': f"gcash_refund_{transaction_id}",
                'message': 'GCash refund initiated - will be processed within 3-5 business days'
            }
            
            return True, "GCash refund initiated successfully", refund_data
            
        except Exception as e:
            error_msg = f"Error processing GCash refund: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def process_refund(self, payment_method: str, transaction_id: str, amount: Decimal) -> Tuple[bool, str, Dict]:
        """
        Process refund based on payment method
        
        Args:
            payment_method: Payment method ('paypal' or 'gcash')
            transaction_id: Transaction ID
            amount: Refund amount
            
        Returns:
            Tuple of (success, message, refund_data)
        """
        if payment_method.lower() == 'paypal':
            return self.process_paypal_refund(transaction_id, amount)
        elif payment_method.lower() == 'gcash':
            return self.process_gcash_refund(transaction_id, amount)
        else:
            return False, f"Unsupported payment method: {payment_method}", {}


def process_order_refund(order, admin_user=None) -> Tuple[bool, str]:
    """
    Process refund for an order
    
    Args:
        order: Orders model instance
        admin_user: Admin user processing the refund
        
    Returns:
        Tuple of (success, message)
    """
    try:
        if not order.is_paid_order():
            return True, "No refund needed for COD orders"
        
        if order.refund_processed:
            return False, "Refund has already been processed for this order"
        
        if not order.transaction_id:
            return False, "No transaction ID found for this order"
        
        refund_processor = RefundProcessor()
        amount = order.get_total_amount()
        
        success, message, refund_data = refund_processor.process_refund(
            order.payment_method,
            order.transaction_id,
            amount
        )
        
        if success:
            # Mark refund as processed
            order.refund_processed = True
            order.refund_amount = amount
            order.refund_processed_at = timezone.now()
            if admin_user:
                order.refund_processed_by = admin_user
            order.save()
            
            logger.info(f"Refund processed for order {order.id}: {message}")
            return True, message
        else:
            logger.error(f"Refund failed for order {order.id}: {message}")
            return False, message
            
    except Exception as e:
        error_msg = f"Error processing refund for order {order.id}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg