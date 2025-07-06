# dalTadka/face_engine/face_model.py

import insightface
import cv2
import numpy as np

class FaceEngine:
    def __init__(self):
        # Load the InsightFace model
        self.model = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.model.prepare(ctx_id=0)

    def get_face_embeddings(self, image_path):
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Image not found or unreadable")

        faces = self.model.get(img)
        embeddings = []

        for face in faces:
            embeddings.append(face.embedding)

        return embeddings

    def compute_cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
