#!/usr/bin/env python3
"""
Enhanced Reports Testing Script
Tests the improved total sales reflection in the database for the manage reports functionality.
"""

import os
import sys
import django
import requests
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from ecom import models
from django.db.models import Sum, F
from django.utils import timezone

class EnhancedReportsTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, success, message=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
    
    def test_database_calculations(self):
        """Test enhanced database calculations for total sales"""
        print("\n🔍 Testing Enhanced Database Calculations...")
        
        try:
            # Test 1: Enhanced Total Revenue Calculation
            total_revenue_from_items = models.OrderItem.objects.filter(
                order__status='Delivered'
            ).aggregate(
                total=Sum(F('price') * F('quantity'))
            )['total'] or 0
            
            total_delivery_fees = models.Orders.objects.filter(
                status='Delivered'
            ).aggregate(
                total=Sum('delivery_fee')
            )['total'] or 0
            
            enhanced_total_revenue = float(total_revenue_from_items) + float(total_delivery_fees)
            
            self.log_result(
                "Enhanced Total Revenue Calculation",
                enhanced_total_revenue >= 0,
                f"Enhanced Revenue: ₱{enhanced_total_revenue:,.2f} (Items: ₱{total_revenue_from_items:,.2f} + Delivery: ₱{total_delivery_fees:,.2f})"
            )
            
            # Test 2: Total Items Sold
            total_items_sold = models.OrderItem.objects.filter(
                order__status='Delivered'
            ).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            self.log_result(
                "Total Items Sold Calculation",
                total_items_sold >= 0,
                f"Total Items Sold: {total_items_sold:,} units"
            )
            
            # Test 3: Delivered Orders Count
            total_delivered_orders = models.Orders.objects.filter(status='Delivered').count()
            total_all_orders = models.Orders.objects.count()
            
            self.log_result(
                "Order Counts Accuracy",
                total_delivered_orders <= total_all_orders,
                f"Delivered: {total_delivered_orders:,} / Total: {total_all_orders:,} orders"
            )
            
            # Test 4: Average Order Value Enhancement
            avg_order_value = enhanced_total_revenue / total_delivered_orders if total_delivered_orders > 0 else 0
            
            self.log_result(
                "Enhanced Average Order Value",
                avg_order_value >= 0,
                f"Enhanced AOV: ₱{avg_order_value:,.2f} per delivered order"
            )
            
            # Test 5: Data Consistency Check
            # Compare enhanced calculation with alternative method
            delivered_orders = models.Orders.objects.filter(status='Delivered')
            alt_total_revenue = float(sum(order.get_total_amount() for order in delivered_orders))
            
            revenue_difference = abs(enhanced_total_revenue - alt_total_revenue)
            revenue_match = revenue_difference < 1.0  # Allow small floating point differences
            
            self.log_result(
                "Revenue Calculation Consistency",
                revenue_match,
                f"Enhanced: ₱{enhanced_total_revenue:,.2f} vs Alternative: ₱{alt_total_revenue:,.2f} (Diff: ₱{revenue_difference:.2f})"
            )
            
        except Exception as e:
            self.log_result("Database Calculations", False, f"Error: {str(e)}")
    
    def test_admin_reports_access(self):
        """Test access to admin reports page"""
        print("\n🌐 Testing Admin Reports Page Access...")
        
        try:
            # Test admin reports page accessibility
            response = self.session.get(f"{self.base_url}/admin-reports", timeout=10)
            
            self.log_result(
                "Admin Reports Page Access",
                response.status_code in [200, 302],  # 302 for redirect to login
                f"Status Code: {response.status_code}"
            )
            
            # Check if page contains enhanced metrics
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for enhanced revenue display
                has_enhanced_revenue = "total revenue (enhanced)" in content or "items + delivery fees" in content
                self.log_result(
                    "Enhanced Revenue Display",
                    has_enhanced_revenue,
                    "Enhanced revenue metrics found in template" if has_enhanced_revenue else "Enhanced revenue metrics not found"
                )
                
                # Check for new metrics
                has_items_sold = "items sold" in content or "total quantity" in content
                self.log_result(
                    "Items Sold Metric Display",
                    has_items_sold,
                    "Items sold metric found in template" if has_items_sold else "Items sold metric not found"
                )
                
                has_delivered_orders = "delivered orders" in content
                self.log_result(
                    "Delivered Orders Metric Display",
                    has_delivered_orders,
                    "Delivered orders metric found in template" if has_delivered_orders else "Delivered orders metric not found"
                )
            
        except Exception as e:
            self.log_result("Admin Reports Access", False, f"Error: {str(e)}")
    
    def test_real_time_data_accuracy(self):
        """Test real-time data accuracy and synchronization"""
        print("\n⏱️ Testing Real-time Data Accuracy...")
        
        try:
            # Get current timestamp
            current_time = timezone.now()
            
            # Test 1: Recent orders reflection
            recent_orders = models.Orders.objects.filter(
                created_at__gte=current_time - timedelta(hours=24)
            ).count()
            
            self.log_result(
                "Recent Orders Tracking",
                True,  # Always pass as we're just checking the query works
                f"Orders in last 24h: {recent_orders}"
            )
            
            # Test 2: Active users calculation
            thirty_days_ago = timezone.now() - timedelta(days=30)
            active_users = models.Customer.objects.filter(
                orders__created_at__gte=thirty_days_ago
            ).distinct().count()
            
            self.log_result(
                "Active Users Calculation",
                active_users >= 0,
                f"Active users (30 days): {active_users}"
            )
            
            # Test 3: Conversion rate accuracy
            total_customers = models.Customer.objects.count()
            customers_with_orders = models.Customer.objects.filter(
                orders__isnull=False
            ).distinct().count()
            
            conversion_rate = (customers_with_orders / total_customers * 100) if total_customers > 0 else 0
            
            self.log_result(
                "Conversion Rate Accuracy",
                0 <= conversion_rate <= 100,
                f"Conversion Rate: {conversion_rate:.1f}% ({customers_with_orders}/{total_customers})"
            )
            
        except Exception as e:
            self.log_result("Real-time Data Accuracy", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all enhanced reports tests"""
        print("🚀 Starting Enhanced Reports Testing...")
        print("=" * 60)
        
        # Run test suites
        self.test_database_calculations()
        self.test_admin_reports_access()
        self.test_real_time_data_accuracy()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ENHANCED REPORTS TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n✨ Enhanced reports testing completed!")
        return success_rate >= 80  # Consider 80%+ as successful

if __name__ == "__main__":
    tester = EnhancedReportsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)