import time
import threading
from PyQt5.QtWidgets import QApplication
import pytesseract
from PIL import Image, ImageEnhance

class ChannelLogic:
    def __init__(self):
        self.channels = {}  # Каналы теперь хранят только активные каналы с их временем
        self.history = []
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def scan_channel(self, screenshot_path):
        img = Image.open(screenshot_path)
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        new_size = (img.width * 2, img.height * 2)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        text = pytesseract.image_to_string(img, config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
        try:
            channel = int(text.strip())
            if 1 <= channel <= 25:
                if channel not in self.channels:
                    self.channels[channel] = 0  # Новый канал сразу активен, время 0 = "неизвестно"
                return channel
        except ValueError:
            pass
        return None

    def get_channel_data(self):
        return sorted(
            [(ch, max(0, self.channels[ch] - time.time()) if self.channels[ch] > 0 else 0,
              "timer" if self.channels[ch] > time.time() else "alive" if self.channels[ch] > 0 else "unknown")
             for ch in self.channels],
            key=lambda x: (0 if x[2] == "timer" else 1 if x[2] == "alive" else 2, x[1])
        )

    def start_timer(self, channel, duration, boss_type):
        self.history.append((channel, self.channels[channel]))
        self.channels[channel] = time.time() + duration
        threading.Thread(target=self._timer_thread, args=(channel, duration), daemon=True).start()

    def _timer_thread(self, channel, duration):
        time.sleep(max(0, self.channels[channel] - time.time()))
        if self.channels[channel] == time.time() + duration:
            QApplication.beep()

    def undo_action(self):
        if self.history:
            channel, prev_time = self.history.pop()
            self.channels[channel] = prev_time

    def delete_channel(self, channel):
        if channel in self.channels:
            del self.channels[channel]
            # Удаляем из истории записи о канале
            self.history = [entry for entry in self.history if entry[0] != channel]