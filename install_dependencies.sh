#!/bin/bash

# Install system dependencies for TTS (Kokoro library)
echo "Installing system dependencies for Text-to-Speech..."

# Update package list
sudo apt-get update

# Install espeak-ng for Kokoro TTS
echo "Installing espeak-ng..."
sudo apt-get install -y espeak-ng

# Install other audio dependencies if needed
echo "Installing additional audio libraries..."
sudo apt-get install -y libsndfile1 ffmpeg

echo "System dependencies installation completed!"
echo "Now you can install Python dependencies with: pip install -r requirements.txt" 