from ultralytics import YOLO
import serial
import serial.tools.list_ports
import time


# ---------------------------------------------------------
# Select COM port for Arduino
# ---------------------------------------------------------
ports = serial.tools.list_ports.comports()
portsList = []

for one in ports:
    portsList.append(str(one))
    print(str(one))

com = input("Select COM Port for Arduino #: ")

# Find the selected COM port
for i in range(len(portsList)):
    if portsList[i].startswith("COM" + str(com)):
        use = "COM" + str(com)
        print("Using:", use)

# Open serial connection to Arduino
arduino = serial.Serial(use, 9600)
time.sleep(2)   # allow Arduino to reset


# ---------------------------------------------------------
# Load YOLO model
# ---------------------------------------------------------
model = YOLO("C:\\Users\\khade\\Graduation-project\\best2_2.pt")


# ---------------------------------------------------------
# Python sends 0–180, Arduino constrains if needed
# ---------------------------------------------------------
X_MIN, X_MAX = 0, 180
Y_MIN, Y_MAX = 0, 180

# ---------------------------------------------------------
# Object lock memory
# last_center_x / last_center_y store previous object location
# Used to keep tracking the same object even if YOLO loses it
# ---------------------------------------------------------
last_center_x = None
last_center_y = None

# Lock radius grows when object is lost
lock_radius = 150
max_lock_radius = 2000
radius_growth_per_second = 80
last_time = time.time()


# ---------------------------------------------------------
# YOLO detection + tracking loop
# ---------------------------------------------------------
for result in model.predict(
    source=0,          # webcam
    show=True,         # show video window
    conf=0.70,         # confidence threshold
    vid_stride=1,
    stream=True,       # continuous frames
    verbose=False,
    imgsz=1500,        # high resolution
):
    boxes = result.boxes

    # -----------------------------------------------------
    # If YOLO sees NO objects → expand search radius
    # This helps re-find the same object later
    # -----------------------------------------------------
    if len(boxes) == 0:
        current_time = time.time()
        if current_time - last_time >= 1:
            lock_radius = min(lock_radius + radius_growth_per_second, max_lock_radius)
            last_time = current_time
            print(f"No detections — expanding radius to {lock_radius}")
        continue


    # -----------------------------------------------------
    # Select which object to track
    # -----------------------------------------------------
    selected_box = None

    # If no object was previously locked → pick the first one
    if last_center_x is None:
        selected_box = boxes[0]
        lock_radius = 100
        last_time = time.time()

    else:
        # Try to find the object near the last known location
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Distance from previous center
            dist = ((cx - last_center_x)**2 + (cy - last_center_y)**2)**0.5

            # If inside lock radius → this is the same object
            if dist < lock_radius:
                selected_box = box
                lock_radius = 100
                last_time = time.time()
                break

        # If no object found near last position → expand radius
        if selected_box is None:
            current_time = time.time()
            if current_time - last_time >= 1:
                lock_radius = min(lock_radius + radius_growth_per_second, max_lock_radius)
                last_time = current_time
                print(f"Object not found near last position — expanding radius to {lock_radius}")
            continue


    # -----------------------------------------------------
    # Extract bounding box center
    # -----------------------------------------------------
    x1, y1, x2, y2 = selected_box.xyxy[0]
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)

    # Save for next frame
    last_center_x = center_x
    last_center_y = center_y

    frame_w = result.orig_shape[1]
    frame_h = result.orig_shape[0]

    print("Tracking locked object at:", center_x, center_y)


    # -----------------------------------------------------
    # Horizontal movement (X axis)
    # Pixel difference → servo angle
    # Inverted so servo moves correctly
    # -----------------------------------------------------
    center_horizontal = frame_w // 2
    pixel_diff_x = center_x - center_horizontal

    # Strong centering movement
    angle_x = 90 - (pixel_diff_x / 6)
    angle_x = int(max(X_MIN, min(X_MAX, angle_x)))


    # -----------------------------------------------------
    # Vertical movement (Y axis)
    # Pixel difference → servo angle
    # -----------------------------------------------------
    center_vertical = frame_h // 2
    pixel_diff_y = center_y - center_vertical

    angle_y = 90 - (pixel_diff_y / 9)
    angle_y = int(max(Y_MIN, min(Y_MAX, angle_y)))


    # -----------------------------------------------------
    # Send servo commands to Arduino
    # -----------------------------------------------------
    cmd_x = f"X{angle_x}\n"
    cmd_y = f"Y{angle_y}\n"

    arduino.write(cmd_x.encode())
    arduino.write(cmd_y.encode())

    print("Sent:", cmd_x.strip(), cmd_y.strip())
