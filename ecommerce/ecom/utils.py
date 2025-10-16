import requests
import json
import os
from django.core.cache import cache
from django.conf import settings

def load_local_psgc_data():
    """Load local PSGC data as fallback"""
    try:
        static_dir = getattr(settings, 'STATIC_ROOT', None) or os.path.join(settings.BASE_DIR, 'staticfiles')
        
        # Load regions
        regions_file = os.path.join(static_dir, 'ecom', 'refregion.json')
        if os.path.exists(regions_file):
            with open(regions_file, 'r', encoding='utf-8') as f:
                regions_data = json.load(f)
        else:
            regions_data = []
            
        # Load provinces
        provinces_file = os.path.join(static_dir, 'ecom', 'refprovince.json')
        if os.path.exists(provinces_file):
            with open(provinces_file, 'r', encoding='utf-8') as f:
                provinces_data = json.load(f)
        else:
            provinces_data = []
            
        # Load cities/municipalities
        citymun_file = os.path.join(static_dir, 'ecom', 'refcitymun.json')
        if os.path.exists(citymun_file):
            with open(citymun_file, 'r', encoding='utf-8') as f:
                citymun_data = json.load(f)
        else:
            citymun_data = []
            
        # Load barangays
        barangay_file = os.path.join(static_dir, 'ecom', 'refbrgy.json')
        if os.path.exists(barangay_file):
            with open(barangay_file, 'r', encoding='utf-8') as f:
                barangay_data = json.load(f)
        else:
            barangay_data = []
            
        return {
            'regions': regions_data,
            'provinces': provinces_data,
            'citymun': citymun_data,
            'barangays': barangay_data
        }
    except Exception as e:
        print(f"Error loading local PSGC data: {e}")
        return {
            'regions': [],
            'provinces': [],
            'citymun': [],
            'barangays': []
        }

def get_region_name(region_code):
    """Get region name from PSGC API or local data"""
    if not region_code:
        return "Unknown Region"
        
    # Check cache first
    cache_key = f"region_{region_code}"
            cache.set(cache_key, name, 3600)  # Cache for 1 hour
            return name
    except Exception as e:
        print(f"API error for region {region_code}: {e}")
    
    # Fallback to local data
    try:
        local_data = load_local_psgc_data()
        for region in local_data['regions']:
            if str(region.get('regCode')) == str(region_code):
                name = region.get('regDesc', f"Region {region_code}")
                cache.set(cache_key, name, 3600)
                return name
    except Exception as e:
        print(f"Local data error for region {region_code}: {e}")
    
    return f"Region {region_code}"

def get_province_name(province_code):
    """Get province name from PSGC API or local data"""
    if not province_code:
        return "Unknown Province"
        
    # Check cache first
    cache_key = f"province_{province_code}"
    cached_name = cache.get(cache_key)
    if cached_name:
        return cached_name
    
    try:
        # Try API first
        base_url = getattr(settings, 'PSGC_API_BASE_URL', 'https://psgc.gitlab.io/api')
        url = f"{base_url}/provinces/{province_code}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        name = None
        if isinstance(data, dict) and 'name' in data:
            name = data['name']
        elif isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
            name = data[0]['name']
            
        if name:
            cache.set(cache_key, name, 3600)
            return name
    except Exception as e:
        print(f"API error for province {province_code}: {e}")
    
    # Fallback to local data
    try:
        local_data = load_local_psgc_data()
        for province in local_data['provinces']:
            if str(province.get('provCode')) == str(province_code):
                name = province.get('provDesc', f"Province {province_code}")
                cache.set(cache_key, name, 3600)
                return name
    except Exception as e:
        print(f"Local data error for province {province_code}: {e}")
    
    return f"Province {province_code}"

def get_citymun_name(citymun_code):
    """Get city/municipality name from PSGC API or local data"""
    if not citymun_code:
        return "Unknown City/Municipality"
        
    # Check cache first
    cache_key = f"citymun_{citymun_code}"
    cached_name = cache.get(cache_key)
    if cached_name:
        return cached_name
    
    try:
        # Try API first
        base_url = getattr(settings, 'PSGC_API_BASE_URL', 'https://psgc.gitlab.io/api')
        url = f"{base_url}/cities-municipalities/{citymun_code}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        name = None
        if isinstance(data, dict) and 'name' in data:
            name = data['name']
        elif isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
            name = data[0]['name']
            
        if name:
            cache.set(cache_key, name, 3600)
            return name
    except Exception as e:
        print(f"API error for citymun {citymun_code}: {e}")
    
    # Fallback to local data
    try:
        local_data = load_local_psgc_data()
        for citymun in local_data['citymun']:
            if str(citymun.get('citymunCode')) == str(citymun_code):
                name = citymun.get('citymunDesc', f"City/Municipality {citymun_code}")
                cache.set(cache_key, name, 3600)
                return name
    except Exception as e:
        print(f"Local data error for citymun {citymun_code}: {e}")
    
    return f"City/Municipality {citymun_code}"

def get_barangay_name(barangay_code):
    """Get barangay name from PSGC API or local data"""
    if not barangay_code:
        return "Unknown Barangay"
        
    # Check cache first
    cache_key = f"barangay_{barangay_code}"
    cached_name = cache.get(cache_key)
    if cached_name:
        return cached_name
    
    try:
        # Try API first
        base_url = getattr(settings, 'PSGC_API_BASE_URL', 'https://psgc.gitlab.io/api')
        url = f"{base_url}/barangays/{barangay_code}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        name = None
        if isinstance(data, dict) and 'name' in data:
            name = data['name']
        elif isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
            name = data[0]['name']
            
        if name:
            cache.set(cache_key, name, 3600)
            return name
    except Exception as e:
        print(f"API error for barangay {barangay_code}: {e}")
    
    # Fallback to local data
    try:
        local_data = load_local_psgc_data()
        for barangay in local_data['barangays']:
            if str(barangay.get('brgyCode')) == str(barangay_code):
                name = barangay.get('brgyDesc', f"Barangay {barangay_code}")
                cache.set(cache_key, name, 3600)
                return name
    except Exception as e:
        print(f"Local data error for barangay {barangay_code}: {e}")
    
    return f"Barangay {barangay_code}"
