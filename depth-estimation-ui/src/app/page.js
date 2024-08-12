'use client';

import { useState, useEffect } from 'react';
import * as THREE from 'three';
import pako from 'pako';
import config from '@/config';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadedImageUrl, setUploadedImageUrl] = useState(null);
  const [depthData, setDepthData] = useState(null);
  const [depthWidth, setDepthWidth] = useState(0);
  const [depthHeight, setDepthHeight] = useState(0);

  useEffect(() => {
    if (depthData) {
      console.log('Depth Data:', depthData);  // Log depth data to console
      renderDepthMap();
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

      // Decode base64 and decompress the depth data
      const compressedDepth = Uint8Array.from(atob(compressedDepthBase64), c => c.charCodeAt(0));
      const decompressedDepth = pako.inflate(compressedDepth);

      // Convert decompressed data back to a Float32Array
      const depthArray = new Float32Array(decompressedDepth.buffer);

      console.log('Decompressed Depth Data:', depthArray);  // Log decompressed depth data

      setDepthData(depthArray);
      setDepthWidth(width);
      setDepthHeight(height);
    } catch (error) {
      console.error('Error:', error.message);  // Log error to console
      setErrorMessage('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const renderDepthMap = () => {
    console.log('Rendering depth map with dimensions:', depthWidth, depthHeight);  // Log rendering process

    // Create a Three.js scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, depthWidth / depthHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer();
    renderer.setSize(depthWidth, depthHeight);
    document.getElementById('depth-render').appendChild(renderer.domElement);

    // Create a plane and apply depth data as height map
    const geometry = new THREE.PlaneGeometry(depthWidth, depthHeight, depthWidth - 1, depthHeight - 1);
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true });

    const plane = new THREE.Mesh(geometry, material);
    scene.add(plane);

    // Map depth data to geometry vertices
    for (let y = 0; y < depthHeight; y++) {
      for (let x = 0; x < depthWidth; x++) {
        const index = y * depthWidth + x;
        geometry.attributes.position.setZ(index, depthData[index]);
      }
    }

    camera.position.z = 100;
    camera.position.y = 100;
    camera.rotation.x = -Math.PI / 4;

    const animate = function () {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();
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
        </div>
      )}

      <div id="depth-render" className="w-full h-auto mt-6"></div>
    </div>
  );
}
