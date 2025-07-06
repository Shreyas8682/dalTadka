# dalTadka/face_engine/matcher.py

import numpy as np
from db.database import get_all_encodings

def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def find_matches(selfie_embedding, threshold=0.5):
    results = []
    data = get_all_encodings()

    for row in data:
        try:
            db_vec = np.array(list(map(float, row["encoding"].split(","))))
            similarity = cosine_similarity(selfie_embedding, db_vec)

            if similarity > threshold:
                results.append({
                    "url": row["cloudinary_url"],  # ✅ Use Cloudinary URL now
                    "score": round(similarity, 3)
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
