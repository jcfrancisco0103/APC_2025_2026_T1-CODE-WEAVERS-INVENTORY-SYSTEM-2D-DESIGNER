from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import colorsys
import random
import math

@csrf_exempt
@require_http_methods(["POST"])
def ai_color_harmony_recommend(request):
    """
    AI-powered color harmony recommendation for jersey designs
    Based on color theory and sports team aesthetics
    """
    try:
        data = json.loads(request.body)
        base_color = data.get('baseColor', '#3B82F6')
        harmony_type = data.get('harmonyType', 'complementary')
        sport_type = data.get('sportType', 'football')
        team_style = data.get('teamStyle', 'modern')
        
        # Convert hex to HSV for color calculations
        def hex_to_hsv(hex_color):
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        
        def hsv_to_hex(h, s, v):
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        # Get base color HSV
        h, s, v = hex_to_hsv(base_color)
        
        # Generate color harmonies based on type
        colors = [base_color]  # Always include base color
        
        if harmony_type == 'complementary':
            # Complementary color (180 degrees opposite)
            comp_h = (h + 0.5) % 1.0
            colors.append(hsv_to_hex(comp_h, s, v))
            
        elif harmony_type == 'triadic':
            # Triadic colors (120 degrees apart)
            colors.append(hsv_to_hex((h + 0.333) % 1.0, s, v))
            colors.append(hsv_to_hex((h + 0.667) % 1.0, s, v))
            
        elif harmony_type == 'analogous':
            # Analogous colors (30 degrees apart)
            colors.append(hsv_to_hex((h + 0.083) % 1.0, s, v))
            colors.append(hsv_to_hex((h - 0.083) % 1.0, s, v))
            
        elif harmony_type == 'split_complementary':
            # Split complementary (150 and 210 degrees)
            colors.append(hsv_to_hex((h + 0.417) % 1.0, s, v))
            colors.append(hsv_to_hex((h + 0.583) % 1.0, s, v))
            
        elif harmony_type == 'tetradic':
            # Tetradic/Square (90 degrees apart)
            colors.append(hsv_to_hex((h + 0.25) % 1.0, s, v))
            colors.append(hsv_to_hex((h + 0.5) % 1.0, s, v))
            colors.append(hsv_to_hex((h + 0.75) % 1.0, s, v))
        
        # Sport-specific color adjustments
        sport_adjustments = {
            'football': {'saturation_boost': 0.1, 'brightness_boost': 0.05},
            'basketball': {'saturation_boost': 0.15, 'brightness_boost': 0.1},
            'soccer': {'saturation_boost': 0.05, 'brightness_boost': 0.0},
            'baseball': {'saturation_boost': 0.0, 'brightness_boost': -0.05},
            'volleyball': {'saturation_boost': 0.08, 'brightness_boost': 0.08},
            'cycling': {'saturation_boost': 0.2, 'brightness_boost': 0.15},
            'esports': {'saturation_boost': 0.25, 'brightness_boost': 0.2}
        }
        
        # Apply sport-specific adjustments
        if sport_type in sport_adjustments:
            adj = sport_adjustments[sport_type]
            adjusted_colors = []
            for color in colors:
                h_adj, s_adj, v_adj = hex_to_hsv(color)
                s_adj = min(1.0, s_adj + adj['saturation_boost'])
                v_adj = max(0.0, min(1.0, v_adj + adj['brightness_boost']))
                adjusted_colors.append(hsv_to_hex(h_adj, s_adj, v_adj))
            colors = adjusted_colors
        
        # Generate team style variations
        style_variations = []
        
        if team_style == 'modern':
            # Modern: High contrast, bold colors
            for i, color in enumerate(colors[:3]):  # Limit to 3 colors
                h_var, s_var, v_var = hex_to_hsv(color)
                # Create high contrast version
                if v_var > 0.5:
                    v_var = min(1.0, v_var + 0.2)
                else:
                    v_var = max(0.0, v_var - 0.2)
                s_var = min(1.0, s_var + 0.1)
                style_variations.append(hsv_to_hex(h_var, s_var, v_var))
                
        elif team_style == 'classic':
            # Classic: Muted, traditional colors
            for color in colors[:3]:
                h_var, s_var, v_var = hex_to_hsv(color)
                s_var = max(0.3, s_var - 0.2)  # Reduce saturation
                v_var = max(0.2, min(0.8, v_var))  # Keep moderate brightness
                style_variations.append(hsv_to_hex(h_var, s_var, v_var))
                
        elif team_style == 'vibrant':
            # Vibrant: High saturation, bright colors
            for color in colors[:3]:
                h_var, s_var, v_var = hex_to_hsv(color)
                s_var = min(1.0, s_var + 0.3)
                v_var = min(1.0, v_var + 0.2)
                style_variations.append(hsv_to_hex(h_var, s_var, v_var))
        
        # Generate gradient color schemes
        def generate_gradient_colors(color1, color2, steps=5):
            """Generate intermediate colors for smooth gradients"""
            h1, s1, v1 = hex_to_hsv(color1)
            h2, s2, v2 = hex_to_hsv(color2)
            
            gradient_colors = []
            for i in range(steps):
                ratio = i / (steps - 1)
                # Interpolate HSV values
                h_interp = h1 + (h2 - h1) * ratio
                s_interp = s1 + (s2 - s1) * ratio
                v_interp = v1 + (v2 - v1) * ratio
                gradient_colors.append(hsv_to_hex(h_interp, s_interp, v_interp))
            return gradient_colors
        
        # Generate accent colors (lighter/darker variations)
        accent_colors = []
        for color in colors[:2]:  # Use first 2 main colors
            h_acc, s_acc, v_acc = hex_to_hsv(color)
            # Lighter version
            accent_colors.append(hsv_to_hex(h_acc, max(0.1, s_acc - 0.3), min(1.0, v_acc + 0.3)))
            # Darker version
            accent_colors.append(hsv_to_hex(h_acc, min(1.0, s_acc + 0.1), max(0.1, v_acc - 0.3)))
        
        # Generate gradient schemes for each recommendation
        gradient_schemes = []
        if len(colors) >= 2:
            # Primary to Secondary gradient
            gradient_schemes.append({
                'type': 'linear',
                'direction': '45deg',
                'colors': generate_gradient_colors(colors[0], colors[1], 3),
                'name': 'Primary-Secondary Blend'
            })
            
            # Multi-color gradient if we have 3+ colors
            if len(colors) >= 3:
                gradient_schemes.append({
                    'type': 'linear',
                    'direction': '90deg',
                    'colors': [colors[0], colors[1], colors[2]],
                    'name': 'Triple Color Flow'
                })
            
            # Radial gradient for dynamic effect
            gradient_schemes.append({
                'type': 'radial',
                'direction': 'circle at center',
                'colors': generate_gradient_colors(colors[0], accent_colors[0] if accent_colors else colors[1], 4),
                'name': 'Radial Burst'
            })
        
        # Create design recommendations
        recommendations = [
            {
                'id': 1,
                'name': f'{harmony_type.title()} Harmony',
                'description': f'Professional {sport_type} jersey with {harmony_type} color harmony',
                'primaryColor': colors[0],
                'secondaryColor': colors[1] if len(colors) > 1 else colors[0],
                'accentColor': accent_colors[0] if accent_colors else colors[0],
                'textColor': '#FFFFFF' if hex_to_hsv(colors[0])[2] < 0.5 else '#000000',
                'gradient': gradient_schemes[0] if gradient_schemes else None,
                'confidence': 0.95,
                'tags': [harmony_type, sport_type, team_style]
            },
            {
                'id': 2,
                'name': f'{team_style.title()} Style',
                'description': f'{team_style.title()} design perfect for {sport_type} teams',
                'primaryColor': style_variations[0] if style_variations else colors[0],
                'secondaryColor': style_variations[1] if len(style_variations) > 1 else (colors[1] if len(colors) > 1 else colors[0]),
                'accentColor': accent_colors[1] if len(accent_colors) > 1 else (accent_colors[0] if accent_colors else colors[0]),
                'textColor': '#FFFFFF' if hex_to_hsv(style_variations[0] if style_variations else colors[0])[2] < 0.5 else '#000000',
                'gradient': gradient_schemes[1] if len(gradient_schemes) > 1 else (gradient_schemes[0] if gradient_schemes else None),
                'confidence': 0.88,
                'tags': [team_style, sport_type, 'professional']
            }
        ]
        
        # Add a third recommendation if we have enough colors
        if len(colors) >= 3:
            recommendations.append({
                'id': 3,
                'name': 'Dynamic Contrast',
                'description': f'High-impact design with dynamic color contrast for {sport_type}',
                'primaryColor': colors[2],
                'secondaryColor': colors[0],
                'accentColor': accent_colors[2] if len(accent_colors) > 2 else (accent_colors[0] if accent_colors else colors[1]),
                'textColor': '#FFFFFF' if hex_to_hsv(colors[2])[2] < 0.5 else '#000000',
                'gradient': gradient_schemes[2] if len(gradient_schemes) > 2 else (gradient_schemes[0] if gradient_schemes else None),
                'confidence': 0.82,
                'tags': ['dynamic', 'contrast', sport_type]
            })
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations,
            'harmonyType': harmony_type,
            'sportType': sport_type,
            'teamStyle': team_style,
            'baseColor': base_color,
            'generatedColors': colors,
            'accentColors': accent_colors,
            'gradientSchemes': gradient_schemes
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def ai_jersey_pattern_suggest(request):
    """
    AI-powered pattern suggestions for jersey designs
    """
    try:
        data = json.loads(request.body)
        sport_type = data.get('sportType', 'football')
        team_style = data.get('teamStyle', 'modern')
        primary_color = data.get('primaryColor', '#3B82F6')
        
        # Pattern suggestions based on sport and style
        pattern_library = {
            'football': {
                'modern': ['stripes_vertical', 'gradient_diagonal', 'geometric_hexagon'],
                'classic': ['stripes_horizontal', 'solid', 'stripes_sleeve'],
                'vibrant': ['chevron', 'diamond_pattern', 'wave_pattern']
            },
            'basketball': {
                'modern': ['gradient_radial', 'geometric_triangle', 'mesh_pattern'],
                'classic': ['solid', 'side_panels', 'number_focus'],
                'vibrant': ['lightning', 'flame_pattern', 'abstract_flow']
            },
            'soccer': {
                'modern': ['stripes_diagonal', 'gradient_vertical', 'pixel_pattern'],
                'classic': ['stripes_vertical', 'solid', 'collar_accent'],
                'vibrant': ['zigzag', 'tribal_pattern', 'burst_pattern']
            },
            'cycling': {
                'modern': ['aerodynamic_lines', 'gradient_flow', 'tech_pattern'],
                'classic': ['racing_stripes', 'solid_panels', 'team_bands'],
                'vibrant': ['speed_lines', 'energy_burst', 'neon_accents']
            },
            'esports': {
                'modern': ['digital_camo', 'circuit_pattern', 'glitch_effect'],
                'classic': ['logo_focus', 'solid_base', 'minimal_accent'],
                'vibrant': ['neon_grid', 'cyber_pattern', 'holographic']
            }
        }
        
        # Get patterns for the specified sport and style
        patterns = pattern_library.get(sport_type, pattern_library['football']).get(team_style, ['solid', 'stripes_vertical'])
        
        # Generate pattern recommendations
        recommendations = []
        for i, pattern in enumerate(patterns[:3]):  # Limit to 3 recommendations
            recommendations.append({
                'id': i + 1,
                'patternType': pattern,
                'name': pattern.replace('_', ' ').title(),
                'description': f'{pattern.replace("_", " ").title()} pattern optimized for {sport_type} jerseys',
                'complexity': random.uniform(0.3, 0.8),
                'sportOptimized': True,
                'confidence': random.uniform(0.75, 0.95)
            })
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations,
            'sportType': sport_type,
            'teamStyle': team_style
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)