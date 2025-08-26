import cv2
import mediapipe as mp
import numpy as np
from tkinter import *
from PIL import Image, ImageTk
import time

# ----------- Initialize the main Tkinter window ----------------
root = Tk()
root.title("Gesture Game!")
root.geometry("800x600")
root.configure(bg='lightblue')

# Create a frame for the welcome message and button
frame = Frame(root, bg='lightblue')
frame.place(relx=0.5, rely=0.5, anchor='center')

# Header label
header = Label(frame, text="Welcome to the Gesture Game!", font=("Arial", 30), bg='lightblue')
header.pack(pady=(10, 10))

# Instruction label
instruction = Label(frame, text="Do the gesture to score points", font=("Arial", 18), bg='lightblue')
instruction.pack(pady=(10, 10))

# Start game button
start_button = Button(frame, text='-->> Start Game <<--', width=15, font=("Arial", 14), command=lambda: start_game(), fg='white', bg='navy')
start_button.pack(pady=(10, 10))
# ---------------------------------------------------------------

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# ################ Gesture detection functions ##################

# to check if the gesture is_thumbs_up
def is_thumbs_up(landmarks):
    thumb_tip = landmarks[4]  
    index_base = landmarks[6]  
    middle_base = landmarks[10]  
    ring_base = landmarks[14]  
    pinky_base = landmarks[18]  

    # Ensure thumb is up
    thumb_up = thumb_tip.y < index_base.y

    # Ensure other fingers are down 
    fingers_down = (
        landmarks[8].y > landmarks[6].y and  # Index finger
        landmarks[12].y > landmarks[10].y and  # Middle finger
        landmarks[16].y > landmarks[14].y and  # Ring finger
        landmarks[20].y > landmarks[18].y  # Pinky finger
    )

    if thumb_up and fingers_down:
        return True
    return False

# to check if the gesture is_peace_sign
def is_peace_sign(landmarks):
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    # Checking the relative positions of the fingers for the peace sign
    if (index_tip.y < ring_tip.y and middle_tip.y < pinky_tip.y and 
        ring_tip.y > landmarks[13].y and pinky_tip.y > landmarks[17].y):
        return True
    return False

# to check if the gesture is_ok_sign
def is_ok_sign(landmarks, frame):
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]

    # Normalize the coordinates using the frame's width and height
    thumb_tip = (thumb_tip.x * frame.shape[1], thumb_tip.y * frame.shape[0])
    index_tip = (index_tip.x * frame.shape[1], index_tip.y * frame.shape[0])

    # Check if the thumb and index fingers are close enough in the horizontal direction (x-axis)
    # and also have a reasonable vertical alignment (y-axis).
    if abs(thumb_tip[0] - index_tip[0]) < 50 and abs(thumb_tip[1] - index_tip[1]) < 50:
        return True
    return False

# to check if the gesture is_rock_and_roll
def is_rock_and_roll(landmarks):
    index_tip = landmarks[8]
    pinky_tip = landmarks[20]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]

    # The Rock & Roll gesture has index and pinky fingers extended
    if index_tip.y < middle_tip.y and pinky_tip.y < ring_tip.y:
        return True
    return False

# to check if the gesture is_high_five
def is_high_five(landmarks):
    for i in [4, 8, 12, 16, 20]:  # Thumb tip, index tip, middle tip, ring tip, pinky tip
        tip = landmarks[i]
        base = landmarks[i - 2]  # The base joint of each finger is 2 joints before the tip (index 2, 6, 10, 14, 18)
       
        if tip.y > base.y + 0.1:  # Check if the tip is below the base joint (allowing a small tolerance)
            return False
    return True

# to check if the gesture is_thumb_down
def is_thumb_down(landmarks):
    thumb_tip = landmarks[4]  # Thumb tip
    thumb_base = landmarks[2]  # Base joint of thumb
   
    # The thumb down gesture has the thumb tip below the thumb base (y-coordinate comparison)
    if thumb_tip.y > thumb_base.y + 0.1:
        return True
    return False

# ################################################################

# --------------- Game Start Logic -------------------

def start_game():
    global score, current_gesture_index, gesture_sequence

    score = 0  
    current_gesture_index = 0
    gesture_sequence = ["thumbs up", "peace sign", "ok sign", "rock and roll", "high five", "thumb down"]

    # ----- Initialize the second Tkinter window --------------------

    root.withdraw()  # Hide the main Tkinter window
    game_window = Toplevel()  # Create a new window for the game
    game_window.title("Gesture Recognition Game")
    game_window.geometry("900x700")
    game_window.configure(bg='navy')

    # Create a frame for the game window
    game_frame = Frame(game_window, bg='lightblue')
    game_frame.place(relx=0.5, rely=0.5, anchor='center')

    score_label = Label(game_frame, text=f"Score: {score}", font=("Arial", 20), bg='lightblue')
    score_label.pack(pady=(10, 10))

    target_label = Label(game_frame, text=f"Gesture to do:  {gesture_sequence[current_gesture_index]}", font=("Arial", 20), bg='lightblue')
    target_label.pack()

    timer_label = Label(game_window, text="Time left: ", font=("Arial", 16), fg='red')
    timer_label.pack(pady=(10, 10))

    # Canvas to display the webcam feed
    camera_label = Label(game_frame, bg='black')
    camera_label.pack(pady=(10, 10))

    # ----------------------------------------------------------------

    # Initialize the webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def capture_frames():
        global score, current_gesture_index, gesture_sequence
        time_limit = 10

        while current_gesture_index < len(gesture_sequence):
            gesture = gesture_sequence[current_gesture_index]
            target_label.config(text=f"Gesture to do: {gesture}")
            gesture_done = False
            start_time = time.time()

            # Loop until the time runs out
            while not gesture_done:
                elapsed_time = time.time() - start_time
                remaining_time = max(0, time_limit - int(elapsed_time))
                timer_label.config(text=f"Time left: {remaining_time}")

                if remaining_time == 0:
                    target_label.config(text=f"Time's up for {gesture}!")
                    break


                if cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        print("Failed to capture frame. Exiting...")
                        exit 

                # Flip the image horizontally for a selfie-view display
                frame = cv2.flip(frame, 1)

                # Convert the BGR image to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Process the image to detect hands
                result = hands.process(frame_rgb)

                if result.multi_hand_landmarks:
                    for hand_landmarks in result.multi_hand_landmarks:
                        # Draw hand landmarks
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
                        landmarks = hand_landmarks.landmark

                        # Check if the current gesture is performed
                        if gesture == "thumbs up" and is_thumbs_up(landmarks):
                            cv2.putText(frame, f'Correct! {gesture}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            score += 1
                            score_label.config(text=f"Score: {score}")
                            gesture_done = True
                        elif gesture == "peace sign" and is_peace_sign(landmarks):
                            cv2.putText(frame, f'Correct! {gesture}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            score += 1
                            score_label.config(text=f"Score: {score}")
                            gesture_done = True
                        elif gesture == "ok sign" and is_ok_sign(landmarks, frame):
                            cv2.putText(frame, f'Correct! {gesture}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            score += 1
                            score_label.config(text=f"Score: {score}")
                            gesture_done = True
                        elif gesture == "rock and roll" and is_rock_and_roll(landmarks):
                            cv2.putText(frame, f'Correct! {gesture}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            score += 1
                            score_label.config(text=f"Score: {score}")
                            gesture_done = True
                        elif gesture == "high five" and is_high_five(landmarks):
                            cv2.putText(frame, f'Correct! {gesture}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            score += 1
                            score_label.config(text=f"Score: {score}")
                            gesture_done = True
                        elif gesture == "thumb down" and is_thumb_down(landmarks):
                            cv2.putText(frame, f'Correct! {gesture}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            score += 1
                            score_label.config(text=f"Score: {score}")
                            gesture_done = True

                # Convert the frame for Tkinter display
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)

                # Update the camera feed in the Tkinter window
                camera_label.imgtk = imgtk
                camera_label.configure(image=imgtk)

                # Update the GUI
                game_window.update_idletasks()
                game_window.update()

            current_gesture_index += 1

        # Update the UI after all gestures are completed
        target_label.config(text="Game Over! Well Done!")
        timer_label.config(text="")

        # Release resources after a short delay to show the final message
        game_window.after(2000, on_closing)

    # Function to handle window closing
    def on_closing():
        cap.release()
        root.quit()

    capture_frames()

# ---------------------------------------------------------------------

root.mainloop()