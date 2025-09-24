from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from shapely.wkt import loads
from shapely.geometry import mapping
from pyproj import Transformer, CRS

app = Flask(__name__)
CORS(app)

# Define the source and target coordinate systems
# The ULDK API returns coordinates in EPSG:2180
# Leaflet uses WGS 84 (EPSG:4326)
crs_2180 = CRS("EPSG:2180")
crs_4326 = CRS("EPSG:4326")
transformer_to_wgs84 = Transformer.from_crs(crs_2180, crs_4326, always_xy=True)
transformer_to_2180 = Transformer.from_crs(crs_4326, crs_2180, always_xy=True)

def get_parcel_id_by_coords(lat, lon):
    """Fetches parcel ID from the ULDK API using geographic coordinates."""
    x, y = transformer_to_2180.transform(lon, lat)
    url = f"https://uldk.gugik.gov.pl/?request=GetParcelByXY&xy={x},{y}&result=id"
    try:
        response = requests.get(url)
        response.raise_for_status()
        status_code, parcel_id = response.text.strip().split('\n', 1)
        if status_code != '0' or not parcel_id.strip():
            return None, "No parcel found at this location."
        return parcel_id.strip(), None
    except requests.exceptions.RequestException as e:
        return None, f"Failed to connect to ULDK API: {e}"
    except (ValueError, IndexError) as e:
        return None, f"Failed to parse ULDK API response: {e}"

def get_parcel_geometry(parcel_id):
    """Fetches parcel geometry from the ULDK API and converts it to GeoJSON."""
    url = f"https://uldk.gugik.gov.pl/?request=GetParcelById&id={parcel_id}&result=geom_wkt"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        # The response is a single line of text. The first part is a status code.
        # '0' means success.
        status_code, wkt_data = response.text.strip().split('\n', 1)
        if status_code != '0':
            return None, f"ULDK API returned an error: {wkt_data}"

        # The geometry is in WKT (Well-Known Text) format, but includes an SRID
        # which we need to strip for Shapely to parse it correctly.
        if 'SRID' in wkt_data:
            wkt_data = wkt_data.split(';', 1)[1]

        polygon_2180 = loads(wkt_data)

        # Transform all points in the polygon to the new coordinate system
        transformed_coords = [transformer_to_wgs84.transform(x, y) for x, y in polygon_2180.exterior.coords]

        # Create a new polygon with the transformed coordinates
        from shapely.geometry import Polygon
        polygon_4326 = Polygon(transformed_coords)

        # Convert the Shapely geometry object to a GeoJSON-like dictionary
        return mapping(polygon_4326), None

    except requests.exceptions.RequestException as e:
        return None, f"Failed to connect to ULDK API: {e}"
    except (ValueError, IndexError) as e:
        return None, f"Failed to parse ULDK API response: {e}"

@app.route('/api/parcel', methods=['GET'])
def get_parcel():
    parcel_id = request.args.get('id')
    if not parcel_id:
        return jsonify({"error": "Parcel ID is required"}), 400

    geometry, error = get_parcel_geometry(parcel_id)

    if error:
        return jsonify({"error": error}), 500

    return jsonify({
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "parcel_id": parcel_id
        }
    })

@app.route('/api/parcel_by_coords', methods=['GET'])
def get_parcel_by_coords():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    parcel_id, error = get_parcel_id_by_coords(float(lat), float(lon))
    if error:
        return jsonify({"error": error}), 500

    geometry, error = get_parcel_geometry(parcel_id)
    if error:
        return jsonify({"error": error}), 500

    return jsonify({
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "parcel_id": parcel_id
        }
    })

# Overpass API URL
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

def get_nearby_features(polygon_wgs84):
    """Queries the Overpass API for features within a certain distance of the parcel."""

    # Get the bounding box of the parcel to narrow down the search area
    bounds = polygon_wgs84.bounds
    bbox_str = f"{bounds[1]},{bounds[0]},{bounds[3]},{bounds[2]}" # (S,W,N,E)

    # Define the query to find various features around the parcel
    # We look for highways, buildings, and specific amenities.
    # The `around` filter is used to find features within a certain radius (in meters).
    # We use a large radius (1100m) to cover the 1km rule for ecological apiaries.
    query = f"""
    [out:json][timeout:25];
    (
      // Roads
      way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|service)$"](around:1100, {polygon_wgs84.centroid.y}, {polygon_wgs84.centroid.x});

      // Buildings
      way["building"](around:1100, {polygon_wgs84.centroid.y}, {polygon_wgs84.centroid.x});
      node["building"](around:1100, {polygon_wgs84.centroid.y}, {polygon_wgs84.centroid.x});

      // Public facilities
      node["amenity"~"^(school|clinic|hospital|kindergarten|nursing_home)$"](around:1100, {polygon_wgs84.centroid.y}, {polygon_wgs84.centroid.x});
      way["amenity"~"^(school|clinic|hospital|kindergarten|nursing_home)$"](around:1100, {polygon_wgs84.centroid.y}, {polygon_wgs84.centroid.x});

      // Landfills and industrial
      node["landuse"~"^(landfill|industrial)$"](around:1100, {polygon_wgs84.centroid.y}, {polygon_wgs84.centroid.x});
      way["landuse"~"^(landfill|industrial)$"](around:1100, {polygon_wgs84.centroid.y}, {polygon_wgs84.centroid.x});
    );
    out geom;
    """

    try:
        response = requests.post(OVERPASS_API_URL, data=query)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"Failed to connect to Overpass API: {e}"

@app.route('/api/analyze', methods=['POST'])
def analyze_location():
    data = request.get_json()
    if not data or 'geometry' not in data:
        return jsonify({"error": "Missing geometry in request"}), 400

    from shapely.geometry import shape
    parcel_polygon = shape(data['geometry'])

    features_data, error = get_nearby_features(parcel_polygon)
    if error:
        return jsonify({"error": error}), 500

    from pyproj import Geod

    results = []
    geod = Geod(ellps="WGS84")

    for element in features_data.get('elements', []):
        elem_type = element.get('type')
        tags = element.get('tags', {})

        if elem_type == 'node':
            geom = loads(f"POINT({element['lon']} {element['lat']})")
        elif elem_type == 'way' and 'geometry' in element and len(element['geometry']) >= 2:
            coords = ", ".join([f"{p['lon']} {p['lat']}" for p in element['geometry']])
            geom = loads(f"LINESTRING({coords})")
        else:
            continue

        # Calculate the shortest distance from the parcel to the feature
        # This returns the forward and back azimuths, and the distance in meters.
        _, _, distance_meters = geod.inv(
            parcel_polygon.centroid.x, parcel_polygon.centroid.y,
            geom.centroid.x, geom.centroid.y
        )


        # Check rules
        if tags.get('highway') in ['motorway', 'trunk'] and distance_meters < 50:
            results.append(f"Too close to a highway/expressway ({tags.get('name', 'N/A')}) - {distance_meters:.2f}m")
        elif tags.get('amenity') in ['school', 'clinic', 'hospital', 'kindergarten', 'nursing_home'] and distance_meters < 150:
            results.append(f"Too close to a public facility ({tags.get('name', 'N/A')}) - {distance_meters:.2f}m")
        elif tags.get('landuse') in ['landfill', 'industrial'] and distance_meters < 1000:
             results.append(f"Too close to a landfill/industrial area ({tags.get('name', 'N/A')}) - {distance_meters:.2f}m")
        elif (tags.get('building') or tags.get('highway')) and distance_meters < 10:
            results.append(f"Too close to a building/road ({tags.get('name', 'N/A')}) - {distance_meters:.2f}m")

    if not results:
        return jsonify({"message": "All checks passed!"})

    return jsonify({"violations": results})

if __name__ == '__main__':
    app.run(debug=True, port=5001)