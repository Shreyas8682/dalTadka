import os
import insightface
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import requests

class FaceEngine:
    def __init__(self):
        self.model = insightface.app.FaceAnalysis(name='buffalo_l')
        self.model.prepare(ctx_id=0)
        print("✅ FaceEngine initialized.")

    def get_face_embeddings(self, image_input):
        try:
            # Load image from URL or path
            if isinstance(image_input, str):
                if image_input.startswith("http"):
                    print(f"📥 Downloading image from URL (timeout=10): {image_input}")
                    response = requests.get(image_input, timeout=10, stream=True)
                    response.raise_for_status()

                    # Limit image size to 20MB
                    image_data = b''
                    for chunk in response.iter_content(1024):
                        image_data += chunk
                        if len(image_data) > 20 * 1024 * 1024:
                            raise ValueError("❌ Image exceeds size limit (20MB)")

                    image_bytes = BytesIO(image_data)
                    img = np.array(Image.open(image_bytes).convert("RGB"))
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                else:
                    img = cv2.imread(image_input)
                    if img is None:
                        raise RuntimeError(f"❌ Failed to read local image: {image_input}")
            elif isinstance(image_input, BytesIO):
                img = np.array(Image.open(image_input).convert("RGB"))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            else:
                raise ValueError("Unsupported input type")

            # Get face embeddings
            faces = self.model.get(img)
            if not faces:
                return []

            return [face.embedding for face in faces]

        except requests.exceptions.Timeout:
            raise RuntimeError("❌ get_face_embeddings failed: Read timed out.")
        except Exception as e:
            raise RuntimeError(f"❌ get_face_embeddings failed: {e}")
