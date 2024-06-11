# -*- coding: utf-8 -*-
"""app.py

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nWj_oHEYLttzqO8LQmtoDEiQ5jttmFr5
"""

# app.py

from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image, ImageDraw
import io
from fastapi import FastAPI, File, UploadFile

# Initialize MTCNN for face detection
mtcnn = MTCNN()

# Load pre-trained Inception Resnet model
resnet = InceptionResnetV1(pretrained='casia-webface').eval()

app = FastAPI()

def detect_and_draw_faces(img, faces, color='green'):
    draw = ImageDraw.Draw(img)
    for box in faces:
        draw.rectangle(box.tolist(), outline=color, width=3)
    return img

def compare_faces(person_image: Image.Image, verification_image: Image.Image) -> str:
    # Detect faces
    faces_person, _ = mtcnn.detect(person_image)
    faces_verification, _ = mtcnn.detect(verification_image)

    if faces_person is not None and faces_verification is not None:
        # Align faces
        aligned_person = mtcnn(person_image).unsqueeze(0)
        aligned_verification = mtcnn(verification_image).unsqueeze(0)

        # Extract embeddings
        embeddings_person = resnet(aligned_person).detach()
        embeddings_verification = resnet(aligned_verification).detach()

        # Calculate the Euclidean distance between embeddings
        distance = (embeddings_person - embeddings_verification).norm().item()

        # Determine if the faces match
        result = "Same person" if distance < 1.0 else "Different persons"

        # If the distance is below a threshold, consider them a match
        if distance < 1.0:
            person_image_with_box = detect_and_draw_faces(person_image, faces_person, color='green')
            verification_image_with_box = detect_and_draw_faces(verification_image, faces_verification, color='green')

        return f'Distance: {distance:.2f} - {result}'
    else:
        return "Faces not detected in one or both images."


@app.get("/")
async def home():
    return{"message":"Hello from matching Ai server "}

@app.post("/compare_faces/")
async def compare_faces_endpoint(person_image: UploadFile = File(...), verification_image: UploadFile = File(...)):
    person_image_bytes = await person_image.read()
    verification_image_bytes = await verification_image.read()

    person_image_pil = Image.open(io.BytesIO(person_image_bytes))
    verification_image_pil = Image.open(io.BytesIO(verification_image_bytes))

    result = compare_faces(person_image_pil, verification_image_pil)

    return {"result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)