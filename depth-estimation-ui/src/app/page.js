'use client';

import { useState } from 'react';

export default function Home() {
  const [depthOutput, setDepthOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [depthData, setDepthData] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [depthWidth, setDepthWidth] = useState(0);
  const [depthHeight, setDepthHeight] = useState(0);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setErrorMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
        headers: {
          Accept: 'image/png',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to process image');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      displayDepthImage(url);
    } catch (error) {
      setErrorMessage('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const displayDepthImage = (url) => {
    const img = new Image();
    img.src = url;
    img.onload = () => {
      setDepthWidth(img.width);
      setDepthHeight(img.height);
      const canvas = document.getElementById('depth-output');
      const ctx = canvas.getContext('2d');
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0, img.width, img.height);
      const depthImgData = ctx.getImageData(0, 0, img.width, img.height).data;
      setDepthData(depthImgData);
      setImageData(ctx.getImageData(0, 0, img.width, img.height));
      canvas.style.display = 'block';
      canvas.addEventListener('mousemove', showDepthValue);
    };
  };

  const showDepthValue = (event) => {
    const canvas = document.getElementById('depth-output');
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const index = (y * depthWidth + x) * 4;
    const depthValue = depthData[index]; // Assuming depth value is stored in the red channel

    const ctx = canvas.getContext('2d');
    ctx.putImageData(imageData, 0, 0); // Restore the original image

    // Draw the crosshair lines
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 1;

    // Vertical line
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, depthHeight);
    ctx.stroke();

    // Horizontal line
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(depthWidth, y);
    ctx.stroke();

    // Update and show depth information
    const depthInfo = document.getElementById('depth-info');
    depthInfo.style.left = `${event.clientX + 10}px`;
    depthInfo.style.top = `${event.clientY + 10}px`;
    depthInfo.textContent = `Depth: ${depthValue}`;
    depthInfo.style.display = 'block';
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
        <div className="text-center mt-4">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p>Processing image, please wait...</p>
        </div>
      )}

      {errorMessage && (
        <div className="alert alert-danger mt-4 text-red-500">{errorMessage}</div>
      )}

      <div className="image-container mt-4 relative">
        <canvas id="depth-output" className="w-full h-auto" style={{ display: 'none' }}></canvas>
        <div
          id="depth-info"
          className="absolute bg-black text-white p-1 rounded pointer-events-none"
          style={{ display: 'none' }}
        ></div>
      </div>
    </div>
  );
}
