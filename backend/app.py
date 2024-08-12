import os
import numpy as np
from PIL import Image
import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import logging
import gzip
import base64

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
        depth_np_feet = np.round(depth_np * 3.28084, 4)
        logging.debug(f"Rounded Depth Value: {depth_np_feet[:10]}")

        # Compress the NumPy array directly
        # compressed_depth = gzip.compress(depth_np_feet.tobytes())
        #
        # # Encode to base64 to safely transfer over HTTP
        compressed_depth_base64 = base64.b64encode(depth_np_feet).decode('utf-8')
        logging.debug(f"Rounded Depth Value: {compressed_depth_base64[:10]}")
        #
        # logging.debug(f"compressed depth size: {len(compressed_depth) / (1024 * 1024):.2f} MB")
        logging.debug(f"compressed depth base 64 size: {len(compressed_depth_base64) / (1024 * 1024):.2f} MB")

        # Return the compressed depth data as base64-encoded JSON
        return JSONResponse(content={"depth_values": depth_np_feet, "width": depth_np_feet.shape[1], "height": depth_np_feet.shape[0]})

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
