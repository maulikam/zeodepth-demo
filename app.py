import os
import numpy as np
from PIL import Image
import torch 
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

# Load the ZoeDepth model
zoe = torch.hub.load("isl-org/ZoeDepth", "ZoeD_N", pretrained=True)

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

    try:
        image = Image.open(file).convert("RGB")  # Convert image to RGB
        logging.debug(f"Image opened successfully: {image}")
    except Exception as e:
        logging.error(f"Error opening image: {e}")
        return jsonify({'error': 'Invalid image file'}), 400

    try:
        # Perform depth estimation
        predicted_depth = zoe.infer_pil(image, pad_input=False)  # Better 'metric' accuracy
        logging.debug(f"Depth estimation completed: {predicted_depth}")

        # Convert the depth map to a numpy array and normalize it
        depth_np = np.array(predicted_depth)
        depth_np_normalized = (depth_np - np.min(depth_np)) / (np.max(depth_np) - np.min(depth_np))
        depth_image = Image.fromarray((depth_np_normalized * 255).astype(np.uint8))
        
        # Convert the depth image to base64
        buffered = io.BytesIO()
        depth_image.save(buffered, format="PNG")
        depth_image_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return jsonify({'depth_image': depth_image_str})
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return jsonify({'error': f'Error processing image: {e}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
