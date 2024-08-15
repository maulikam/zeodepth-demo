import os
import numpy as np
from PIL import Image
import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import logging
import base64
import matplotlib.pyplot as plt

# Set up FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load the ZoeDepth model
zoe = torch.hub.load("isl-org/ZoeDepth", "ZoeD_N", pretrained=True)

# Set the model to evaluation mode explicitly
zoe.eval()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the ZoeDepth API"}

@app.post("/upload")
async def upload_file(request: Request):
    logging.debug("Upload endpoint called")

    try:
        # Read raw image data from the request body
        image_data = await request.body()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")  # Convert image to RGB
        logging.debug(f"Image opened successfully: {image}")
    except Exception as e:
        logging.error(f"Error opening image: {e}")
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        # Perform depth estimation
        predicted_depth = zoe.infer_pil(image, pad_input=False)  # Better 'metric' accuracy
        logging.debug(f"Depth estimation completed")

        # Convert the depth map to a numpy array
        depth_np = np.array(predicted_depth)

        # Convert from meters to feet
        depth_np_feet = depth_np * 3.28084

        # Normalize the depth values to the range 0-255 and convert to uint8
        depth_min, depth_max = depth_np_feet.min(), depth_np_feet.max()
        depth_np_normalized = ((depth_np_feet - depth_min) / (depth_max - depth_min) * 255).astype(np.uint8)
        logging.debug(f"Normalized Depth Value: {depth_np_normalized[:10]}")

        # Encode to base64
        depth_base64 = base64.b64encode(depth_np_normalized).decode('utf-8')

        logging.debug(f"Base64 encoded depth size: {len(depth_base64) / (1024 * 1024):.2f} MB")

        # Convert depth_min and depth_max to standard Python floats
        depth_min = float(depth_min)
        depth_max = float(depth_max)

        # Return the base64-encoded depth data as JSON
        return JSONResponse(content={
            "depth_values": depth_base64,
            "width": depth_np_normalized.shape[1],
            "height": depth_np_normalized.shape[0],
            "depth_min": depth_min,
            "depth_max": depth_max
        })

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
