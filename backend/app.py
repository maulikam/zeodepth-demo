import os
import numpy as np
from PIL import Image
import torch
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import base64
import logging
import matplotlib
import matplotlib.pyplot as plt

# Use the 'Agg' backend for headless rendering (no GUI)
matplotlib.use('Agg')

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
async def upload_file(file: UploadFile = File(...)):
    logging.debug("Upload endpoint called")

    try:
        # Read raw image data from the uploaded file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")  # Convert image to RGB
        logging.debug(f"Image opened successfully: {image}")
    except Exception as e:
        logging.error(f"Error opening image: {e}")
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        # Perform depth estimation
        predicted_depth = zoe.infer_pil(image, pad_input=False)  # Better 'metric' accuracy
        logging.debug(f"Depth estimation completed: {predicted_depth}")

        # Convert the depth map to a numpy array
        depth_np = np.array(predicted_depth)

        # Convert from meters to feet
        depth_np_feet = depth_np * 3.28084

        # Plot and save the depth map with Matplotlib
        fig, ax = plt.subplots()
        cax = ax.imshow(depth_np_feet, cmap='gray')
        fig.colorbar(cax, ax=ax, label='Depth value (feet)')

        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)  # Close the figure to free up memory

        return StreamingResponse(buf, media_type="image/png", headers={"Content-Disposition": "attachment; filename=depth_map.png"})

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
