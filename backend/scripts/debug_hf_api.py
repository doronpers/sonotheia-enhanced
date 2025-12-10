
import os
import io
import scipy.io.wavfile
import numpy as np
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

def test_router():
    token = os.getenv("HUGGINGFACE_TOKEN")
    print(f"DEBUG: Token present? {'Yes' if token else 'No'}")
    
    if not token:
        print("ERROR: No token found. Cannot test API.")
        return
        
    # Create simple audio
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    audio = np.sin(2 * np.pi * 440 * t) * 0.5
    
    # Bytes
    byte_io = io.BytesIO()
    scipy.io.wavfile.write(byte_io, sr, (audio * 32767).astype(np.int16))
    audio_bytes = byte_io.getvalue()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    models_to_test = [
        "MelodyMachine/Deepfake-audio-detection-V2",
        "mo-thecreator/Deepfake-audio-detection",
        "facebook/wav2vec2-base-960h"
    ]
    
    for model_id in models_to_test:
        print(f"\nTesting model (ROUTER ROOT): {model_id}")
        api_url = f"https://router.huggingface.co/models/{model_id}"
        
        try:
            response = requests.post(api_url, headers=headers, data=audio_bytes)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"SUCCESS: {model_id} worked")
                try:
                    print(f"Response: {response.json()[:2]}")
                except:
                    print(f"Response (text): {response.text[:100]}")
            else:
                print(f"FAILED: {model_id} - Response: {response.text[:200]}...")
        except Exception as e:
            print(f"FAILED: {model_id} - {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_router()
