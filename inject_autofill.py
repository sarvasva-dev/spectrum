import re

files = [
    r"c:\Users\Admin\OneDrive\Desktop\spectrum\frontend\pages\report_waste.html",
    r"c:\Users\Admin\OneDrive\Desktop\spectrum\frontend\pages\pickup_request.html"
]

autofill_func = """
            // Reverse Geocoding helper
            async function reverseGeocodeAndUpdate(lat, lng) {
                const locInput = document.getElementById('id_location');
                if (!locInput) return;
                
                try {
                    const originalPlaceholder = locInput.placeholder;
                    locInput.placeholder = "Auto-filling location...";
                    
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
                    const data = await response.json();
                    
                    if (data && data.display_name) {
                        let parts = [];
                        if (data.address) {
                            if (data.address.road) parts.push(data.address.road);
                            if (data.address.suburb) parts.push(data.address.suburb);
                            if (data.address.city_district) parts.push(data.address.city_district);
                            if (data.address.city || data.address.town || data.address.village) parts.push(data.address.city || data.address.town || data.address.village);
                        }
                        const conciseAddress = parts.length > 0 ? parts.join(', ') : data.display_name.split(',').slice(0, 3).join(', ');
                        
                        // Only set if user hasn't already typed a lot of details
                        if (!locInput.value || locInput.value.length < 5 || locInput.value === "28.613900") {
                            locInput.value = conciseAddress;
                        } else if (locInput.value.length > 0) {
                            // If they already clicked the map and generated an address, just overwrite it
                            locInput.value = conciseAddress;
                        }
                    }
                    locInput.placeholder = originalPlaceholder;
                } catch (e) {
                    console.error("Reverse geocoding failed", e);
                }
            }
"""

click_target = """                    if (latInput && lngInput) {
                        latInput.value = lat.toFixed(6);
                        lngInput.value = lng.toFixed(6);
                    }"""
click_replace = """                    if (latInput && lngInput) {
                        latInput.value = lat.toFixed(6);
                        lngInput.value = lng.toFixed(6);
                    }
                    reverseGeocodeAndUpdate(lat, lng);"""

geo_target = """                                if (latInput && lngInput) {
                                    latInput.value = lat.toFixed(6);
                                    lngInput.value = lng.toFixed(6);
                                }"""
geo_replace = """                                if (latInput && lngInput) {
                                    latInput.value = lat.toFixed(6);
                                    lngInput.value = lng.toFixed(6);
                                }
                                reverseGeocodeAndUpdate(lat, lng);"""

for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "reverseGeocodeAndUpdate" in content:
        print(f"Already injected in {fpath}")
        continue
        
    content = content.replace("iframe.onload = function() {", "iframe.onload = function() {\n" + autofill_func)
    content = content.replace(click_target, click_replace)
    content = content.replace(geo_target, geo_replace)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Injected into {fpath}")
