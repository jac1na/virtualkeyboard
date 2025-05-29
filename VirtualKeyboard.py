import cv2
import numpy as np
import cvzone
from cvzone.HandTrackingModule import HandDetector
from pynput.keyboard import Controller
from time import time

# Webcam Setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetector(detectionCon=1)
keyboard = Controller()

# Key Layouts
keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]]

extra_keys = [("Space", 400), ("Backspace", 170), ("Enter", 120)]

lines = [""]
cursor_visible = True
last_cursor_toggle = time()
cursor_interval = 0.5

lastPressedTime = 0
debounceTime = 0.4

pressedKey = None
keyFlashDuration = 0.2
pressedKeyTime = 0

class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text
        self.lastPressTime = 0  # <-- New per-button cooldown


# Create Buttons
buttonList = []
for i, row in enumerate(keys):
    for j, key in enumerate(row):
        x = 100 * j + 50
        y = 100 * i + 50
        buttonList.append(Button([x, y], key))

# Extra Buttons Row
x_offset = 50
y_extra = 100 * len(keys) + 50
for key, width in extra_keys:
    buttonList.append(Button([x_offset, y_extra], key, [width, 85]))
    x_offset += width + 20

# Draw Buttons
def drawAll(img, buttonList):
    imgNew = np.zeros_like(img, np.uint8)
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        color = (0, 255, 0) if button.text == pressedKey else (64, 64, 64)
        cvzone.cornerRect(imgNew, (x, y, w, h), 20, rt=0)
        cv2.rectangle(imgNew, (x, y), (x + w, y + h), color, cv2.FILLED)
        font_scale = 2 if len(button.text) > 1 else 4
        offset_x = 10 if len(button.text) > 6 else 20
        cv2.putText(imgNew, button.text, (x + offset_x, y + 60),
                    cv2.FONT_HERSHEY_PLAIN, font_scale, (255, 255, 255), 3)

    alpha = 0.5
    mask = imgNew.astype(bool)
    img[mask] = cv2.addWeighted(img, alpha, imgNew, 1 - alpha, 0)[mask]
    return img

# Draw Typing Box
def drawTypingArea(img, lines, cursor_visible):
    overlay = img.copy()
    top = 600
    bottom = 720
    cv2.rectangle(overlay, (50, top), (1200, bottom), (0, 0, 0), cv2.FILLED)
    img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)

    font = cv2.FONT_HERSHEY_SIMPLEX
    y_line = top + 30

    for i, line in enumerate(lines[-5:]):
        line_disp = line
        if i == len(lines[-5:]) - 1 and cursor_visible:
            line_disp += "|"
        cv2.putText(img, line_disp, (60, y_line + i * 22), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    return img

# Update Text Logic
def addCharacter(char):
    global lines
    if char == "\n":
        lines.append("")
    elif char == "\b":
        if lines[-1]:
            lines[-1] = lines[-1][:-1]
        elif len(lines) > 1:
            lines = lines[:-1]
    else:
        if len(lines[-1]) >= 50:
            lines.append(char)
        else:
            lines[-1] += char

# Main Loop
while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList, _ = detector.findPosition(img)
    currentTime = time()

    # Draw keys
    img = drawAll(img, buttonList)

    # Blinking Cursor
    if currentTime - last_cursor_toggle > cursor_interval:
        cursor_visible = not cursor_visible
        last_cursor_toggle = currentTime

    # Reset flash
    if pressedKey and currentTime - pressedKeyTime > keyFlashDuration:
        pressedKey = None

    # Process Press
    if lmList:
        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            if x < lmList[8][0] < x + w and y < lmList[8][1] < y + h:
                l, _, _ = detector.findDistance(8, 12, img, draw=False)
                if l < 30 and currentTime - button.lastPressTime > debounceTime:
                    key = button.text
                    key_char = {
                        "Space": " ",
                        "Backspace": "\b",
                        "Enter": "\n"
                    }.get(key, key)
                    addCharacter(key_char)
                    keyboard.press(key_char)
                    pressedKey = key
                    pressedKeyTime = currentTime
                    button.lastPressTime = currentTime

    # Draw typing area
    img = drawTypingArea(img, lines, cursor_visible)

    cv2.imshow("Virtual Keyboard", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
