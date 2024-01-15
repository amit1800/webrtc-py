import cv2

# Load the pre-trained face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def detect_faces(img):
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces in the image
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    # Draw rectangles around the faces
    for x, y, w, h in faces:
        img2 = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
    return img2


# Read the input image
input_image_path = "img.png"
img = cv2.imread(input_image_path)

# Check if the image is loaded successfully
if img is None:
    print(f"Error: Could not read image from {input_image_path}")
else:
    # Detect faces in the image
    output_img = detect_faces(img.copy())

    # Display the original and the output image
    cv2.imshow("Original Image", img)
    cv2.imshow("Output Image with Faces Detected", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
