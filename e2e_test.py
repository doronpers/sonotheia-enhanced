
import numpy as np
import scipy.io.wavfile as wav
import requests
import time
import sys

# Generate dummy audio
fs = 16000
duration = 2.0  # seconds
t = np.linspace(0, duration, int(fs * duration))
y = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
# Add some noise
y += 0.01 * np.random.normal(size=len(t))
y = (y * 32767).astype(np.int16)

wav_path = "test_audio.wav"
wav.write(wav_path, fs, y)
print(f"Created {wav_path}")

# Wait for server to be up
url = "http://localhost:8000/api/detect"
health_url = "http://localhost:8000/api/v1/health"

print("Waiting for server...")
for i in range(10):
    try:
        resp = requests.get(health_url)
        if resp.status_code == 200:
            print("Server is up!")
            break
    except requests.exceptions.ConnectionError:
        time.sleep(1)
else:
    print("Server failed to start")
    sys.exit(1)

# Send request
print(f"Sending request to {url}...")
with open(wav_path, 'rb') as f:
    files = {'file': (wav_path, f, 'audio/wav')}
    data = {'quick_mode': 'true'} # Run quick mode for speed
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            print("Test PASSED")
        else:
            print("Test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"Request failed: {e}")
        sys.exit(1)
