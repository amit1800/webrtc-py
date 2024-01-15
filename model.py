import cv2
from from_root import from_root
from ultralytics import YOLO
import os

classes = ["bag", "human", "fire", "smoke", "number-plate"]
ROOT = os.path.dirname(__file__)


def get_infer_data(output):
    infer_data = []
    for box in output[0].boxes:
        box_data = {
            "class": int(box.cls.numpy().data.tolist()[0]),
            "conf": box.conf.numpy().data.tolist()[0],
            "box": [int(p) for p in box.xyxy.numpy().data.tolist()[0]],
        }
        infer_data.append(box_data)
    return infer_data


def overlay_prediction(img, infer_data, with_p=False):
    probability = round(infer_data["conf"], 2)
    class_name = classes[infer_data["class"]]
    class_name_with_p = f"{class_name} {probability:.2f}"
    text = class_name_with_p if with_p else class_name
    start_point = infer_data["box"][0], infer_data["box"][1]
    org = start_point[0], start_point[1] - 15
    font_scale = 1
    end_point = infer_data["box"][2], infer_data["box"][3]
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (255, 0, 0)
    thickness = 2
    line_type = cv2.LINE_AA
    rect_drawn = cv2.rectangle(img, start_point, end_point, color, thickness)
    class_drawn = cv2.putText(
        rect_drawn, text, org, font, font_scale, color, thickness, line_type
    )
    return class_drawn


def process_frame(frame):
    model = YOLO(os.path.join(ROOT, "models/best.pt"))
    results = model(frame)
    # annotated_frame = results[0].plot()
    annot_data = get_infer_data(results)
    annotated_frame = overlay_prediction(frame, annot_data[0])
    return annotated_frame


input_image_path = "img.png"
img = cv2.imread(input_image_path)

# Check if the image is loaded successfully
if img is None:
    print(f"Error: Could not read image from {input_image_path}")
else:
    # Detect faces in the image
    output_img = process_frame(img.copy())

    # Display the original and the output image
    cv2.imshow("Original Image", img)
    cv2.imshow("Output Image with Faces Detected", output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
