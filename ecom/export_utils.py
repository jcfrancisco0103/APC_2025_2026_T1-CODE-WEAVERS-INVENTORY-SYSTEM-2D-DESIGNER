import csv
import io
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
import json


class ReportExporter:
    """Utility class for exporting reports in various formats"""
    
    @staticmethod
    def export_to_csv(data, filename, headers=None):
        """Export data to CSV format"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        writer = csv.writer(response)
        
        # Write headers if provided
        if headers:
            writer.writerow(headers)
        
        # Write data rows
        for row in data:
            if isinstance(row, dict):
                writer.writerow(row.values())
            else:
                writer.writerow(row)
        
        return response
    
    @staticmethod
    def export_to_excel(data, filename, headers=None):
        """Export data to Excel format (CSV with Excel MIME type)"""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        # For now, we'll use CSV format with Excel MIME type
        # In a production environment, you might want to use openpyxl or xlsxwriter
        output = io.StringIO()
        writer = csv.writer(output)
        
        if headers:
            writer.writerow(headers)
        
        for row in data:
            if isinstance(row, dict):
                writer.writerow(row.values())
            else:
                writer.writerow(row)
        
        response.write(output.getvalue().encode('utf-8'))
        return response
    
    @staticmethod
    def export_to_pdf(template_name, context, filename):
        """Export data to PDF format using xhtml2pdf"""
        # Render the template with context
        html_string = render_to_string(template_name, context)
        
        # Create HTTP response with PDF content type
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        
        # Generate PDF
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        
        return response


class SalesReportExporter:
    """Specialized exporter for sales reports"""
    
    @staticmethod
    def get_sales_csv_data(orders, daily_sales=None):
        """Prepare sales data for CSV export"""
        data = []
        
        # Add summary data
        if daily_sales:
            data.append(['Date', 'Orders', 'Revenue', 'Items Sold'])
            for sale in daily_sales:
                data.append([
                    sale['date'].strftime('%Y-%m-%d'),
                    sale['orders'],
                    f"${sale['revenue']:.2f}",
                    sale['items']
                ])
            data.append([])  # Empty row separator
        
        # Add order details
        data.append(['Order ID', 'Customer', 'Date', 'Status', 'Total Amount', 'Items'])
        for order in orders:
            data.append([
                order.id,
                order.customer.get_name() if order.customer else 'N/A',
                order.order_date.strftime('%Y-%m-%d %H:%M'),
                order.status,
                f"${order.total:.2f}",
                order.orderitem_set.count()
            ])
        
        return data
    
    @staticmethod
    def get_sales_pdf_context(orders, daily_sales, date_range):
        """Prepare context for sales PDF export"""
        total_orders = orders.count()
        total_revenue = sum(order.total for order in orders)
        total_items = sum(order.orderitem_set.count() for order in orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            'report_title': 'Sales Report',
            'date_range': date_range,
            'generated_at': datetime.now(),
            'summary': {
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'total_items': total_items,
                'avg_order_value': avg_order_value,
            },
            'daily_sales': daily_sales,
            'orders': orders[:50],  # Limit for PDF
        }


class CustomerReportExporter:
    """Specialized exporter for customer reports"""
    
    @staticmethod
    def get_customer_csv_data(customers, registration_data=None):
        """Prepare customer data for CSV export"""
        data = []
        
        # Add registration summary if available
        if registration_data:
            data.append(['Date', 'New Registrations'])
            for reg in registration_data:
                data.append([
                    reg['date'].strftime('%Y-%m-%d'),
                    reg['count']
                ])
            data.append([])  # Empty row separator
        
        # Add customer details
        data.append(['Customer ID', 'Name', 'Email', 'Registration Date', 'Total Orders', 'Total Spent'])
        for customer in customers:
            total_orders = customer.orders.count()
            total_spent = sum(order.total for order in customer.orders.all())
            data.append([
                customer.id,
                customer.get_name(),
                customer.email,
                customer.date_joined.strftime('%Y-%m-%d'),
                total_orders,
                f"${total_spent:.2f}"
            ])
        
        return data


class InventoryReportExporter:
    """Specialized exporter for inventory reports"""
    
    @staticmethod
    def get_inventory_csv_data(products, low_stock_threshold=10):
        """Prepare inventory data for CSV export"""
        data = []
        
        # Add inventory summary
        data.append(['Product ID', 'Name', 'Category', 'Stock', 'Price', 'Stock Value', 'Status'])
        
        for product in products:
            stock_status = 'Out of Stock' if product.stock == 0 else (
                'Low Stock' if product.stock <= low_stock_threshold else 'In Stock'
            )
            stock_value = product.stock * product.price
            
            data.append([
                product.id,
                product.product_name,
                product.category.category_name if product.category else 'N/A',
                product.stock,
                f"${product.price:.2f}",
                f"${stock_value:.2f}",
                stock_status
            ])
        
        return data


class ProductReportExporter:
    """Specialized exporter for product reports"""
    
    @staticmethod
    def get_product_csv_data(products, sales_data=None):
        """Prepare product data for CSV export"""
        data = []
        
        # Add product performance data
        data.append(['Product ID', 'Name', 'Category', 'Price', 'Stock', 'Total Sold', 'Revenue', 'Avg Rating'])
        
        for product in products:
            # Calculate sales metrics
            total_sold = sum(item.quantity for item in product.orderitem_set.all())
            revenue = sum(item.quantity * item.price for item in product.orderitem_set.all())
            
            # Calculate average rating
            reviews = product.productreview_set.all()
            avg_rating = sum(review.rating for review in reviews) / len(reviews) if reviews else 0
            
            data.append([
                product.id,
                product.product_name,
                product.category.category_name if product.category else 'N/A',
                f"${product.price:.2f}",
                product.stock,
                total_sold,
                f"${revenue:.2f}",
                f"{avg_rating:.1f}"
            ])
        
        return data