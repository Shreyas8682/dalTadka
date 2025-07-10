# dalTadka/face_engine/matcher.py

import numpy as np
import pickle
from db.database import get_all_encodings

def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def find_matches(selfie_embedding, threshold=0.4):
    results = []
    data = get_all_encodings()

    for row in data:
        try:
            raw_encoding = row["encoding"]

            # Detect and decode if pickled bytes
            if isinstance(raw_encoding, bytes):
                db_vec = pickle.loads(raw_encoding)  # ✅ properly decode
            elif isinstance(raw_encoding, str):
                db_vec = np.array(list(map(float, raw_encoding.split(","))))  # fallback
            else:
                continue

            if len(db_vec) != len(selfie_embedding):
                continue  # avoid comparing mismatched vector sizes

            similarity = cosine_similarity(selfie_embedding, db_vec)

            if similarity > threshold:
                results.append({
                    "url": row["cloudinary_url"],
                    "score": round(similarity, 3)
                })

        except Exception as e:
            
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
