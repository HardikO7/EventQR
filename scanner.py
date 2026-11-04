"""
EventPass - Real-Time Gate Entry Scanner & Validation Engine
Validates single-entry digital QR tokens and records timestamped entry logs.
"""

import cv2
import sys
import time
import argparse
from pathlib import Path
import numpy as np

# Import database module
import database

# Try pyzbar import
try:
    from pyzbar import pyzbar
    HAS_PYZBAR = True
except Exception:
    HAS_PYZBAR = False

def process_token(token, gate="Main Gate 1", scanner_name="Staff Bot"):
    """
    Validate decoded QR token against database:
    1. Check if token exists in registrations table
    2. Check if already checked in (entry_logs)
    3. If valid & unused, insert entry log
    """
    reg = database.get_registration_by_token(token)
    if not reg:
        return {
            "status": "INVALID",
            "message": "INVALID TICKET (Token Not Found)",
            "guest": None
        }

    if reg.get("status") != "confirmed":
        return {
            "status": "INVALID",
            "message": f"ENTRY REJECTED: Registration is '{reg.get('status')}'",
            "guest": reg
        }

    # Check if already scanned
    success, log_entry = database.record_gate_entry(reg["id"], gate_number=gate, scanned_by=scanner_name)
    if not success:
        return {
            "status": "ALREADY_USED",
            "message": f"ALREADY SCANNED ({log_entry.get('scan_time', 'Earlier')})",
            "guest": reg
        }

    return {
        "status": "GRANTED",
        "message": f"ACCESS GRANTED: {reg['student_name']} ({reg['student_roll']})",
        "guest": reg
    }

def decode_frame(frame, qr_detector=None):
    """Decode QR code from a cv2 frame using pyzbar or OpenCV QRCodeDetector"""
    results = []
    
    # Method 1: pyzbar
    if HAS_PYZBAR:
        decoded_objs = pyzbar.decode(frame)
        for obj in decoded_objs:
            token = obj.data.decode("utf-8").strip()
            pts = [(point.x, point.y) for point in obj.polygon]
            if len(pts) == 0:
                rect = obj.rect
                pts = [
                    (rect.left, rect.top),
                    (rect.left + rect.width, rect.top),
                    (rect.left + rect.width, rect.top + rect.height),
                    (rect.left, rect.top + rect.height)
                ]
            results.append((token, pts))
        if results:
            return results

    # Method 2: OpenCV QRCodeDetector fallback
    if qr_detector is not None:
        retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
        if retval and points is not None:
            for info, pt in zip(decoded_info, points):
                if info:
                    pts = [(int(p[0]), int(p[1])) for p in pt]
                    results.append((info.strip(), pts))

    return results

def run_webcam_scanner(camera_idx=0, gate="Gate 1"):
    """Run real-time webcam scanning loop"""
    print("=" * 65)
    print(" EventPass Gate Entry Scanner - OpenCV Live Feed")
    print(" Single-Entry QR Verification")
    print("=" * 65)
    print(f"Connecting to camera index {camera_idx}... Press 'q' to exit.")

    cap = cv2.VideoCapture(camera_idx)
    if not cap.isOpened():
        print(f"[ERROR] Could not open webcam at index {camera_idx}.")
        print("Tip: Test with an image file using: python scanner.py --image <path-to-qr.png>")
        return

    qr_detector = cv2.QRCodeDetector()
    last_scanned_token = None
    last_scan_time = 0
    display_message = "Scan guest QR code ticket at camera"
    display_color = (255, 255, 255) # White
    display_sub = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame from camera.")
            break

        current_time = time.time()
        
        # Reset display banner after 4 seconds
        if current_time - last_scan_time > 4.0:
            display_message = "Point QR code ticket to camera"
            display_color = (200, 200, 200)
            display_sub = "EventQR Gate Entry Validation System"

        # Detect QR codes in frame
        detections = decode_frame(frame, qr_detector)

        for token, pts in detections:
            # Draw polygon around detected QR code
            pts_array = np.array(pts, np.int32)
            pts_array = pts_array.reshape((-1, 1, 2))

            # Process token if debounce passed (1.5 seconds)
            if token != last_scanned_token or (current_time - last_scan_time > 2.0):
                last_scanned_token = token
                last_scan_time = current_time

                res = process_token(token, gate=gate)
                guest_name = res['guest'].get('student_name', res['guest'].get('name', 'Attendee')) if res.get('guest') else 'Unknown'
                guest_roll = res['guest'].get('student_roll', res['guest'].get('roll_no', '')) if res.get('guest') else ''
                guest_dept = res['guest'].get('student_dept', res['guest'].get('department', '')) if res.get('guest') else ''

                if res["status"] == "GRANTED":
                    display_color = (0, 200, 0) # Green
                    display_message = f"VALID: {guest_name} ({guest_roll})"
                    display_sub = f"Dept: {guest_dept} | Status: CHECKED IN"
                    print(f"[OK] {display_message}")
                elif res["status"] == "ALREADY_USED":
                    display_color = (0, 0, 220) # Red
                    display_message = f"REJECTED: ALREADY SCANNED!"
                    display_sub = f"Guest: {guest_name} | Already Checked In"
                    print(f"[ALERT] {display_message} - {guest_name}")
                else:
                    display_color = (0, 140, 255) # Orange
                    display_message = "REJECTED: UNRECOGNIZED QR CODE"
                    display_sub = "Token not found in Event database"
                    print(f"[ERROR] {display_message}")

            # Highlight bounding box with status color
            cv2.polylines(frame, [pts_array], isClosed=True, color=display_color, thickness=3)

        # Draw Header & Footer HUD Overlay
        h, w = frame.shape[:2]
        # Top banner
        cv2.rectangle(frame, (0, 0), (w, 65), (20, 24, 33), -1)
        cv2.putText(frame, display_message, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.68, display_color, 2)
        if display_sub:
            cv2.putText(frame, display_sub, (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        # Bottom info bar
        cv2.rectangle(frame, (0, h - 30), (w, h), (15, 23, 42), -1)
        info_str = "EventQR System • Pondicherry University • Press 'Q' to Exit"
        cv2.putText(frame, info_str, (15, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 174, 192), 1)

        cv2.imshow("EventQR Live Gate Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def scan_single_image(image_path, gate="Gate 1"):
    """Test QR code scanning on a static image file"""
    print(f"\n[SCANNER] Reading image: {image_path}")
    frame = cv2.imread(str(image_path))
    if frame is None:
        print(f"[ERROR] Could not load image from {image_path}")
        return

    qr_detector = cv2.QRCodeDetector()
    detections = decode_frame(frame, qr_detector)
    if not detections:
        print("[RESULT] No QR code detected in the image.")
        return

    for token, pts in detections:
        print(f"[RESULT] Decoded Token: {token}")
        res = process_token(token, gate=gate)
        print(f"[STATUS] {res['status']}: {res['message']}")
        if res.get("guest"):
            g = res["guest"]
            print(f"         Name: {g.get('student_name', g.get('name'))}")
            print(f"         Roll: {g.get('student_roll', g.get('roll_no'))}")
            print(f"         Dept: {g.get('student_dept', g.get('department'))}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EventQR Gate Entry Scanner")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--image", type=str, default="", help="Path to QR image file to scan")
    parser.add_argument("--gate", type=str, default="Main Gate 1", help="Gate identifier")
    args = parser.parse_args()

    if args.image:
        scan_single_image(args.image, gate=args.gate)
    else:
        run_webcam_scanner(camera_idx=args.camera, gate=args.gate)
