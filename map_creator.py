import gpxpy
import folium
from folium.plugins import MarkerCluster
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pillow_heif
pillow_heif.register_heif_opener()
import base64
import io
from geopy.distance import geodesic
import math

def compute_bearing(point1, point2):
    lat1, lon1 = map(math.radians, point1)
    lat2, lon2 = map(math.radians, point2)

    delta_lon = lon2 - lon1
    x = math.sin(delta_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - \
        math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)

    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    return (bearing + 360) % 360

def extract_gps_data(image_path):
    import piexif

    def to_degrees(values):
        d = values[0][0] / values[0][1]
        m = values[1][0] / values[1][1]
        s = values[2][0] / values[2][1]
        return d + m / 60 + s / 3600

    try:
        img = Image.open(image_path)
        exif_bytes = img.info.get("exif", b"")
        if not exif_bytes:
            return None
        exif_dict = piexif.load(exif_bytes)
        gps_data = exif_dict.get("GPS", {})
        if not gps_data:
            return None

        lat = gps_data.get(piexif.GPSIFD.GPSLatitude)
        lat_ref = gps_data.get(piexif.GPSIFD.GPSLatitudeRef)
        lon = gps_data.get(piexif.GPSIFD.GPSLongitude)
        lon_ref = gps_data.get(piexif.GPSIFD.GPSLongitudeRef)

        if lat and lon and lat_ref and lon_ref:
            lat_deg = to_degrees(lat)
            lon_deg = to_degrees(lon)
            if lat_ref == b'S':
                lat_deg = -lat_deg
            if lon_ref == b'W':
                lon_deg = -lon_deg
            return lat_deg, lon_deg
        return None
    except Exception as e:
        print(f"Error reading EXIF from {image_path}: {e}")
        return None

def gpx_to_coords(gpx_path):
    with open(gpx_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        coords = []
        for track in gpx.tracks:
            for segment in track.segments:
                coords.extend([(point.latitude, point.longitude, point.time) for point in segment.points])
        return coords

def encode_image_to_base64(image_path):
    with Image.open(image_path) as img:
        img = img.convert("RGB")  # Convert to RGB to ensure JPEG compatibility
        img.thumbnail((400, 400))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode()

def generate_map(gpx_file, photos_dir, output_html="map_output.html"):
    coords = gpx_to_coords(gpx_file)
    if coords:
        avg_lat = sum(lat for lat, lon, _ in coords) / len(coords)
        avg_lon = sum(lon for lat, lon, _ in coords) / len(coords)
        start_coord = (avg_lat, avg_lon)
    else:
        start_coord = (0, 0)

    m = folium.Map(location=start_coord, zoom_start=13, zoom_control=False, dragging=True, scrollWheelZoom=True, doubleClickZoom=False)
    # Draw the route in blue with an arrow marker at the end to indicate direction
    from folium import PolyLine, features
    if coords:
        # Draw the route as a blue, thicker polyline
        folium.PolyLine([(lat, lon) for lat, lon, _ in coords], color="blue", weight=5).add_to(m)
        # Add arrows every N points to indicate direction
        N = max(1, len(coords)//10)
        for i in range(0, len(coords) - 1, N):
            lat1, lon1, _ = coords[i]
            lat2, lon2, _ = coords[i + 1]
            angle = compute_bearing((lat1, lon1), (lat2, lon2))
            folium.RegularPolygonMarker(
                location=(lat1, lon1),
                number_of_sides=3,
                radius=8,
                rotation=(angle - 90) % 360,
                color='white',
                weight=2,
                fill_color='white',
                fill_opacity=1
            ).add_to(m)
        # Add a larger arrow at the end for visual consistency
        angle = compute_bearing(coords[-2][:2], coords[-1][:2])
        arrow_head = features.RegularPolygonMarker(
            location=(coords[-1][0], coords[-1][1]),
            number_of_sides=3,
            radius=8,
            rotation=(angle - 90) % 360,
            color='white',
            weight=2,
            fill_color='white',
            fill_opacity=1
        )
        arrow_head.add_to(m)

        # Add START marker with folium.Icon
        folium.Marker(
            location=(coords[0][0], coords[0][1]),
            icon=folium.Icon(color="green", icon="play", prefix="fa")
        ).add_to(m)

        # Add END marker with folium.Icon
        folium.Marker(
            location=(coords[-1][0], coords[-1][1]),
            icon=folium.Icon(color="red", icon="stop", prefix="fa")
        ).add_to(m)


    def group_by_proximity(photo_coords, max_distance_meters=500):
        groups = []
        for coord, path in photo_coords:
            added = False
            for group in groups:
                if any(geodesic(coord, g_coord).meters < max_distance_meters for g_coord, _ in group):
                    group.append((coord, path))
                    added = True
                    break
            if not added:
                groups.append([(coord, path)])
        return groups

    photo_coords = []
    from datetime import datetime
    img_paths_with_time = []
    for img_path in Path(photos_dir).glob("*"):
        if img_path.suffix.lower() not in [".jpg", ".jpeg", ".heic"]:
            continue
        gps = extract_gps_data(img_path)
        if gps:
            try:
                timestamp = img_path.stat().st_mtime
                img_paths_with_time.append((timestamp, gps, img_path))
            except Exception as e:
                print(f"Could not read timestamp for {img_path}: {e}")

    # Sort photos by time before grouping
    img_paths_with_time.sort(key=lambda x: x[0])
    photo_coords = [(gps, path) for _, gps, path in img_paths_with_time]

    grouped_photos = group_by_proximity(photo_coords, max_distance_meters=500)

    import string
    letter_labels = iter(string.ascii_uppercase)
    first_marker = None
    first_marker_time = float('inf')

    for group in grouped_photos:
        location = group[0][0]
        img_paths = [p for _, p in group]
        slide_html = f"""
<style>
/* Injected into header for full popup control */
.leaflet-popup-content-wrapper, .leaflet-popup-tip {{
    background: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
}}
.leaflet-popup-content {{
    margin: 7px !important;
    padding: 0 !important;
    width: auto !important;
    max-width: unset !important;
}}
.swiper {{
    border-radius: 0 !important;
    background: none !important;
}}
.swiper-slide img {{
    width: 100% !important;
    height: 100% !important;
    object-fit: cover;
    border-radius: 0 !important;
}}
</style>
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css"
/>\n<script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>

<style>
  .swiper {{
    width: 240px;
    height: 240px;
    border-radius: 0;
    overflow: hidden;
    background-color: transparent;
  }}
  .swiper-slide {{
    display: flex;
    justify-content: center;
    align-items: center;
    width: 240px;
    height: 240px;
  }}
  .swiper-slide img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 0;
    display: block;
  }}
  .swiper-button-next,
  .swiper-button-prev {{
    color: white !important;
  }}
  .swiper-pagination-bullet-active {{
    background: white !important;
  }}
  .swiper-pagination-bullet {{
    background: rgba(255, 255, 255, 0.4) !important;
  }}
</style>

<div class="swiper">
  <div class="swiper-wrapper">
    {''.join([f'<div class="swiper-slide"><img src="data:image/jpeg;base64,{encode_image_to_base64(p)}"></div>' for p in img_paths])}
  </div>
  <div class="swiper-pagination"></div>
  <div class="swiper-button-next"></div>
  <div class="swiper-button-prev"></div>
</div>

<script>
  setTimeout(() => {{
    new Swiper('.swiper', {{
      loop: true,
      navigation: {{
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
      }},
      pagination: {{
        el: '.swiper-pagination',
        clickable: true,
      }},
    }});
  }}, 100);
</script>
"""
        slide_html_wrapped = f'<div class="custom-popup">{slide_html}</div>'
        iframe = folium.IFrame(html=slide_html_wrapped, width=260, height=260)
        popup = folium.Popup(iframe, max_width=260, show=(first_marker is None))
        label = next(letter_labels, "?")
        icon = folium.DivIcon(html=f'''
  <div style="
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: white;
      border: 2px solid #007aff;
      border-radius: 50%;
      width: 32px;
      height: 32px;
      font-size: 18px;
      font-weight: bold;
      color: #007aff;
      box-shadow: 0 2px 6px rgba(0,0,0,0.15);
      text-align: center;
  ">
      {label}
  </div>
  ''')
        marker = folium.Marker(location=location, icon=icon, popup=popup)
        marker.add_to(m)
        marker.add_child(popup)
        if first_marker is None or img_paths[0].stat().st_mtime < first_marker_time:
            first_marker = marker
            first_marker_time = img_paths[0].stat().st_mtime

    m.save(output_html)
    print(f"✅ Map saved to {output_html}")

# Example usage:
generate_map("/Users/KevinLim/Downloads/Zepp20250517102135.gpx", "/Users/KevinLim/Downloads/untitled folder/")
