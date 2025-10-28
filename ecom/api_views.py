import requests
import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect

PSGC_BASE_URL = "https://psgc.gitlab.io/api"

@require_GET
def get_regions(request):
    try:
        response = requests.get(f"{PSGC_BASE_URL}/regions/")
        response.raise_for_status()
        data = response.json()
        return JsonResponse(data, safe=False)
    except requests.RequestException:
        return JsonResponse({"error": "Failed to fetch regions"}, status=500)

@require_GET
def get_provinces(request):
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse({"error": "region_id parameter is required"}, status=400)
    try:
        response = requests.get(f"{PSGC_BASE_URL}/regions/{region_id}/provinces/")
        response.raise_for_status()
        data = response.json()
        return JsonResponse(data, safe=False)
    except requests.RequestException:
        return JsonResponse({"error": "Failed to fetch provinces"}, status=500)

@require_GET
def get_cities(request):
    province_id = request.GET.get('province_id')
    region_id = request.GET.get('region_id')
    try:
        if province_id:
            response = requests.get(f"{PSGC_BASE_URL}/provinces/{province_id}/cities-municipalities/")
            response.raise_for_status()
            data = response.json()
            return JsonResponse(data, safe=False)
        elif region_id:
            # For NCR and similar regions without provinces
            response = requests.get(f"{PSGC_BASE_URL}/regions/{region_id}/cities-municipalities/")
            response.raise_for_status()
            data = response.json()
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({"error": "province_id or region_id parameter is required"}, status=400)
    except requests.RequestException:
        return JsonResponse({"error": "Failed to fetch cities"}, status=500)

@require_GET
def get_barangays(request):
    city_id = request.GET.get('city_id')
    if not city_id:
        return JsonResponse({"error": "city_id parameter is required"}, status=400)
    try:
        response = requests.get(f"{PSGC_BASE_URL}/cities-municipalities/{city_id}/barangays/")
        response.raise_for_status()
        data = response.json()
        return JsonResponse(data, safe=False)
    except requests.RequestException:
        return JsonResponse({"error": "Failed to fetch barangays"}, status=500)

def get_barangay_name(barangay_id):
    """Helper function to get barangay name by ID"""
    try:
        # This is a simplified version - in production you might want to cache this
        # or use a different approach depending on your needs
        response = requests.get(f"{PSGC_BASE_URL}/barangays/{barangay_id}")
        response.raise_for_status()
        barangay = response.json()
        return barangay.get('name', barangay_id)
    except Exception:
        return barangay_id

def get_color_usage_suggestions(colors):
    """Get suggestions for how to use colors in design"""
    return [
        f'Use {colors[0]} as primary background color',
        f'Apply {colors[1]} for main text and important elements',
        f'Use {colors[2]} for accents and call-to-action buttons',
        'Maintain 60-30-10 color distribution rule'
    ]