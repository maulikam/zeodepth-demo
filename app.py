import os
import numpy as np
from PIL import Image
import torch
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import io
import base64
import logging
import matplotlib
import matplotlib.pyplot as plt

# Use the 'Agg' backend for headless rendering (no GUI)
matplotlib.use('Agg')

# Set up Flask app
app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load the ZoeDepth model
zoe = torch.hub.load("isl-org/ZoeDepth", "ZoeD_N", pretrained=True)

# Set the model to evaluation mode explicitly
zoe.eval()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.debug("Upload endpoint called")

    try:
        # Read raw image data from the request
        image_data = request.data
        image = Image.open(io.BytesIO(image_data)).convert("RGB")  # Convert image to RGB
        logging.debug(f"Image opened successfully: {image}")
    except Exception as e:
        logging.error(f"Error opening image: {e}")
        return jsonify({'error': 'Invalid image file'}), 400

    try:
        # Perform depth estimation
        predicted_depth = zoe.infer_pil(image, pad_input=False)  # Better 'metric' accuracy
        logging.debug(f"Depth estimation completed: {predicted_depth}")

        # Convert the depth map to a numpy array
        depth_np = np.array(predicted_depth)

        # Plot and save the depth map with Matplotlib
        fig, ax = plt.subplots()
        cax = ax.imshow(depth_np, cmap='gray')
        fig.colorbar(cax, ax=ax, label='Depth value')
        
        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)  # Close the figure to free up memory

        return send_file(buf, mimetype='image/png', as_attachment=True, download_name='depth_map.png')

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return jsonify({'error': f'Error processing image: {e}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
