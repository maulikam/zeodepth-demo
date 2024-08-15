'use client';

import { useState, useEffect } from 'react';
import config from '@/config';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadedImageUrl, setUploadedImageUrl] = useState(null);
  const [depthData, setDepthData] = useState(null);
  const [depthWidth, setDepthWidth] = useState(0);
  const [depthHeight, setDepthHeight] = useState(0);
  const [depthMin, setDepthMin] = useState(0);
  const [depthMax, setDepthMax] = useState(255);  // Default max if not provided
  const [depthValue, setDepthValue] = useState(null);
  const [crosshairPosition, setCrosshairPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const imageElement = document.getElementById('uploaded-image');
    if (imageElement && depthData) {
      imageElement.addEventListener('mousemove', handleMouseMove);
      return () => {
        imageElement.removeEventListener('mousemove', handleMouseMove);
      };
    }
  }, [depthData]);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setErrorMessage('');
    setDepthData(null);
    setUploadedImageUrl(URL.createObjectURL(file));

    try {
      const response = await fetch(`${config.backendUrl}/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/octet-stream',
        },
        body: await file.arrayBuffer(),
      });

      if (!response.ok) {
        throw new Error('Failed to process image');
      }

      const responseData = await response.json();
      const compressedDepthBase64 = responseData.depth_values;
      const width = responseData.width;
      const height = responseData.height;
      const depthMin = responseData.depth_min;
      const depthMax = responseData.depth_max;

      // Decode base64
      const binaryString = atob(compressedDepthBase64);
      const depthArray = new Uint8Array(binaryString.length);

      for (let i = 0; i < binaryString.length; i++) {
        depthArray[i] = binaryString.charCodeAt(i);
      }

      // Debugging information
      console.log('Response Metadata:', responseData);
      console.log('Image Dimensions:', `Width: ${width}, Height: ${height}`);
      console.log('Depth Array Length:', depthArray.length);
      console.log('First 100 Depth Values:', depthArray.slice(0, 100)); // Print the first 100 depth values for inspection

      setDepthData(depthArray);
      setDepthWidth(width);
      setDepthHeight(height);
      setDepthMin(depthMin);
      setDepthMax(depthMax);
    } catch (error) {
      console.error('Error:', error.message);
      setErrorMessage('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMouseMove = (event) => {
    const rect = event.target.getBoundingClientRect();
    const x = Math.floor(((event.clientX - rect.left) / rect.width) * depthWidth);
    const y = Math.floor(((event.clientY - rect.top) / rect.height) * depthHeight);

    setCrosshairPosition({ x: event.clientX - rect.left, y: event.clientY - rect.top });

    if (depthData && x >= 0 && y >= 0 && x < depthWidth && y < depthHeight) {
      const index = y * depthWidth + x;
      const normalizedDepthValue = depthData[index]; // Normalized depth value (0-255)

      // Reverse normalization to get the actual depth value in feet
      const depthValue = (normalizedDepthValue / 255) * (depthMax - depthMin) + depthMin;

      setDepthValue(depthValue);
    } else {
      setDepthValue(null);
    }
  };

  return (
    <div className="container mx-auto px-4">
      <h1 className="text-3xl font-bold text-center mt-10">Interactive Depth Estimation</h1>

      <div className="flex justify-center mt-6">
        <label className="btn bg-green-500 text-white py-2 px-4 rounded cursor-pointer">
          Upload or Capture Image
          <input
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={handleImageUpload}
          />
        </label>
      </div>

      {loading && (
        <div className="flex justify-center mt-4">
          <div className="flex flex-col items-center">
            <div className="loader ease-linear rounded-full border-8 border-t-8 border-gray-200 h-32 w-32 mb-4"></div>
            <p className="text-lg font-semibold">Processing image, please wait...</p>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="alert alert-danger mt-4 text-red-500">{errorMessage}</div>
      )}

      {uploadedImageUrl && (
        <div className="image-container mt-4 relative">
          <img id="uploaded-image" src={uploadedImageUrl} alt="Uploaded" className="w-full h-auto" />
          <div
            className="crosshair"
            style={{
              position: 'absolute',
              top: `${crosshairPosition.y}px`,
              left: `${crosshairPosition.x}px`,
              width: '1px',
              height: '1px',
              backgroundColor: 'red',
            }}
          />
          {depthValue !== null && (
            <div
              className="depth-info"
              style={{
                position: 'absolute',
                top: `${crosshairPosition.y + 10}px`,
                left: `${crosshairPosition.x + 10}px`,
                backgroundColor: 'white',
                padding: '5px',
                borderRadius: '5px',
                border: '1px solid black',
              }}
            >
              Depth: {depthValue.toFixed(2)} ft
            </div>
          )}
        </div>
      )}
    </div>
  );
}
