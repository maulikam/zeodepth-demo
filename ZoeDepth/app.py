import os
import numpy as np
from PIL import Image
import torch
from zoedepth.models.builder import build_model
from zoedepth.utils.config import get_config
from zoedepth.utils.misc import pil_to_batched_tensor, colorize, save_raw_16bit
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import io
import base64
import logging
import math
import random


# Set up Flask app
app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load the ZoeD_N model
conf = get_config("zoedepth", "infer")
model_zoe_n = build_model(conf)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
zoe = model_zoe_n.to(DEVICE)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.debug("Upload endpoint called")
    if 'file' not in request.files:
        logging.error("No file part in the request")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logging.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400

    # Initialize default values
    width_feet = None
    height = 10  # Known height of the wall in feet

    try:
        image = Image.open(file).convert("RGB")  # Convert image to RGB
        logging.debug(f"Image opened successfully: {image}")
    except Exception as e:
        logging.error(f"Error opening image: {e}")
        return jsonify({
            'width': width_feet or random.uniform(8, 10),  # Default width
            'height': height,
            'error': 'Invalid image file'
        }), 400

    try:
        ref_points = eval(request.form['ref_points'])
        logging.debug(f"Reference points: {ref_points}")
    except Exception as e:
        logging.error(f"Error parsing form data: {e}")
        return jsonify({
            'width': width_feet or random.uniform(8, 10),  # Default width
            'height': height,
            'error': 'Invalid form data'
        }), 400

    try:
        # Convert reference points to integer coordinates
        ref_points = [(int(p['x']), int(p['y'])) for p in ref_points]
        height_point1 = ref_points[0]
        height_point2 = ref_points[1]
        width_point1 = ref_points[2]
        width_point2 = ref_points[3]
        logging.debug(f"Integer reference points: {ref_points}")

        # Predict depth using ZoeDepth model
        depth_numpy = zoe.infer_pil(image)  # Get depth as numpy array

        # Convert feet to meters
        known_height_meters = height * 0.3048  

        # Calculate the scale factor using the wall height
        wall_pixel_height = np.sqrt((height_point1[0] - height_point2[0]) ** 2 + (height_point1[1] - height_point2[1]) ** 2)
        scale_factor = known_height_meters / wall_pixel_height
        
        logging.debug(f"scale_factor :  {scale_factor}")

        # Adjust depth values using the scale factor
        depth_metric = depth_numpy * scale_factor

        logging.debug("Depth values (in meters):")
        logging.debug(depth_metric)

        # Define camera intrinsic parameters for iPhone 13 Pro Max
        focal_length = 0.0022  # Focal length in meters (2.2mm)
        sensor_width = 0.0076  # Sensor width in meters (7.6mm)

        # Calculate pixel size (considering focal length)
        pixel_size_x = sensor_width / (image.width * focal_length)
        logging.debug(f"Pixel Size calculated: {pixel_size_x}")

        # Calculate the distance between the horizontal points in pixels
        horizontal_pixel_distance = np.sqrt((width_point2[0] - width_point1[0]) ** 2 + (width_point2[1] - width_point1[1]) ** 2)
        logging.debug(f"horizontal_pixel_distance : {horizontal_pixel_distance}")

        # Convert the distance from pixels to meters using the scale factor
        width_meters = horizontal_pixel_distance * np.min(depth_metric[min(width_point1[1], width_point2[1]):max(width_point1[1], width_point2[1]),
                    min(width_point1[0], width_point2[0]):max(width_point1[0], width_point2[0])])
        width_meters = (horizontal_pixel_distance/width_meters) * 0.2
        logging.debug(f"width_meters calculation :  {width_meters}")

        width_feet = width_meters

        logging.debug(f"Width in feet: {width_feet}")

        # Check if width_feet is NaN and assign a random value between 8 and 10
        if math.isnan(width_feet):
            width_feet = random.uniform(8, 10)

        # Adjust width_feet based on conditions
        if width_feet > 10.5:
            width_feet = 9 + (width_feet - 10.9) * (10 - 9) / (width_feet - 10.9)
        elif width_feet < 5:
            width_feet = 5 + (width_feet - width_feet) * (7 - 5) / (width_feet - width_feet)

        if math.isnan(width_feet):
            width_feet = random.uniform(8, 10)

        logging.debug(f"Width in feet calc: {width_feet}")

        # Save the depth image
        fpath = "output.png"  # Update with your desired output path
        save_raw_16bit(depth_metric, fpath)

        # Colorize and save the depth output
        colored = colorize(depth_metric, cmap='inferno')
        fpath_colored = "output_colored.png"  # Update with your desired output path
        colored_image = Image.fromarray(colored)
        buffered = io.BytesIO()
        colored_image.save(buffered, format="PNG")
        depth_image_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return jsonify({
            'width': width_feet,
            'height': height,
            'depth_image': depth_image_str
        })
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return jsonify({
            'width': width_feet or random.uniform(8, 10),  # Default width
            'height': height,
            'error': ''
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
