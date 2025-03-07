import json
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QScrollArea, QFrame, QSlider, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPixmap, QImage
from logic import ChannelLogic
from styles import apply_dark_theme
import pyautogui
import win32gui
import win32con

class SpawnTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BNS Spawn Tracker")
        self.setMinimumSize(700, 500)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.logic = ChannelLogic()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        apply_dark_theme(self)
        
        self.setWindowOpacity(0.9)
        self.is_alt_pressed = False
        self.old_pos = None
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.header = QWidget()
        self.header.setFixedHeight(20)
        self.header.setStyleSheet("background-color: #252526; border-bottom: 1px solid #3F3F46;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.header)
        
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # Панель каналов
        channel_frame = QFrame()
        channel_frame.setFrameShape(QFrame.StyledPanel)
        channel_layout = QVBoxLayout(channel_frame)
        
        title = QLabel("Каналы")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        channel_layout.addWidget(title)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.channels_layout = QVBoxLayout(scroll_widget)
        self.scroll_area.setWidget(scroll_widget)
        channel_layout.addWidget(self.scroll_area)
        
        # Панель управления
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_frame.setMaximumWidth(250)
        control_layout = QVBoxLayout(control_frame)
        
        control_title = QLabel("Управление")
        control_title.setFont(QFont("Arial", 12, QFont.Bold))
        control_layout.addWidget(control_title)
        
        self.undo_button = QPushButton("↩ Отменить последнее")
        self.undo_button.clicked.connect(self.logic.undo_action)
        control_layout.addWidget(self.undo_button)
        
        # Прозрачность
        opacity_layout = QVBoxLayout()
        opacity_label = QLabel("Прозрачность")
        opacity_label.setFont(QFont("Arial", 10, QFont.Bold))
        opacity_layout.addWidget(opacity_label)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(90)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        opacity_layout.addWidget(self.opacity_slider)
        control_layout.addLayout(opacity_layout)
        
        self.always_on_top_checkbox = QCheckBox("Поверх всех окон")
        self.always_on_top_checkbox.stateChanged.connect(self.toggle_always_on_top)
        control_layout.addWidget(self.always_on_top_checkbox)
        
        # OCR управление
        ocr_layout = QVBoxLayout()
        ocr_title = QLabel("OCR Захват")
        ocr_title.setFont(QFont("Arial", 10, QFont.Bold))
        ocr_layout.addWidget(ocr_title)
        
        self.load_capture_settings()
        self.screenshot_label = QLabel()
        self.screenshot_label.setFixedSize(60, 40)
        self.screenshot_label.setStyleSheet("border: 1px solid #555555;")
        ocr_layout.addWidget(self.screenshot_label)
        
        arrow_layout = QHBoxLayout()
        self.up_btn = QPushButton("↑")
        self.up_btn.clicked.connect(lambda: self.move_capture_area(0, -10))
        self.down_btn = QPushButton("↓")
        self.down_btn.clicked.connect(lambda: self.move_capture_area(0, 10))
        self.left_btn = QPushButton("←")
        self.left_btn.clicked.connect(lambda: self.move_capture_area(-10, 0))
        self.right_btn = QPushButton("→")
        self.right_btn.clicked.connect(lambda: self.move_capture_area(10, 0))
        
        for btn in (self.up_btn, self.down_btn, self.left_btn, self.right_btn):
            btn.setMaximumWidth(30)
            arrow_layout.addWidget(btn)
        ocr_layout.addLayout(arrow_layout)
        
        size_layout = QHBoxLayout()
        self.w_plus_btn = QPushButton("W+")
        self.w_plus_btn.clicked.connect(lambda: self.resize_capture_area(10, 0))
        self.w_minus_btn = QPushButton("W-")
        self.w_minus_btn.clicked.connect(lambda: self.resize_capture_area(-10, 0))
        self.h_plus_btn = QPushButton("H+")
        self.h_plus_btn.clicked.connect(lambda: self.resize_capture_area(0, 10))
        self.h_minus_btn = QPushButton("H-")
        self.h_minus_btn.clicked.connect(lambda: self.resize_capture_area(0, -10))
        
        for btn in (self.w_plus_btn, self.w_minus_btn, self.h_plus_btn, self.h_minus_btn):
            btn.setMaximumWidth(30)
            size_layout.addWidget(btn)
        ocr_layout.addLayout(size_layout)
        
        self.scan_btn = QPushButton("Сканировать")
        self.scan_btn.clicked.connect(self.scan_area)
        ocr_layout.addWidget(self.scan_btn)
        
        control_layout.addLayout(ocr_layout)
        
        self.active_count = QLabel("Активные каналы: 0")
        self.timer_count = QLabel("Таймеры: 0 | Живые: 0")
        control_layout.addWidget(self.active_count)
        control_layout.addWidget(self.timer_count)
        control_layout.addStretch()
        
        content_layout.addWidget(channel_frame, 3)
        content_layout.addWidget(control_frame, 1)
        main_layout.addWidget(content_widget)
        
        self.apply_click_through(True)
        
        QTimer(self, timeout=self.update_channel_list, interval=1000).start()
        QTimer(self, timeout=self.auto_update_screenshot, interval=2000).start()

    def update_opacity(self):
        opacity = self.opacity_slider.value() / 100.0
        self.setWindowOpacity(opacity)

    def toggle_always_on_top(self, state):
        if state == Qt.Checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def apply_click_through(self, enable):
        hwnd = int(self.winId())
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if enable:
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_TRANSPARENT)
        else:
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style & ~win32con.WS_EX_TRANSPARENT)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.is_alt_pressed = True
            self.apply_click_through(False)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.is_alt_pressed = False
            self.apply_click_through(True)

    def mousePressEvent(self, event):
        if self.is_alt_pressed and event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.is_alt_pressed and self.old_pos is not None:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    def load_capture_settings(self):
        if os.path.exists("capture_settings.json"):
            with open("capture_settings.json", "r") as f:
                self.capture_area = json.load(f)
        else:
            self.capture_area = {'x': 100, 'y': 100, 'width': 30, 'height': 20}

    def save_capture_settings(self):
        with open("capture_settings.json", "w") as f:
            json.dump(self.capture_area, f)

    def move_capture_area(self, dx, dy):
        self.capture_area['x'] += dx
        self.capture_area['y'] += dy
        self.save_capture_settings()
        self.scan_area()

    def resize_capture_area(self, dw, dh):
        new_width = max(10, self.capture_area['width'] + dw)
        new_height = max(10, self.capture_area['height'] + dh)
        self.capture_area['width'] = new_width
        self.capture_area['height'] = new_height
        self.save_capture_settings()
        self.scan_area()

    def auto_update_screenshot(self):
        screenshot = pyautogui.screenshot(region=(
            self.capture_area['x'], 
            self.capture_area['y'], 
            self.capture_area['width'], 
            self.capture_area['height']
        ))
        screenshot.save("last_scan.png")
        pixmap = QPixmap("last_scan.png").scaled(60, 40, Qt.KeepAspectRatio)
        self.screenshot_label.setPixmap(pixmap)
        channel = self.logic.scan_channel("last_scan.png")
        if channel:
            self.update_channel_list()

    def scan_area(self):
        self.auto_update_screenshot()

    def update_channel_list(self):
        while self.channels_layout.count():
            self.channels_layout.takeAt(0).widget().deleteLater()
        
        channel_data = self.logic.get_channel_data()
        timers, alive = 0, 0
        
        for channel, time_left, status in channel_data:
            frame = QFrame()
            frame.setMaximumHeight(40)
            layout = QHBoxLayout(frame)
            layout.setContentsMargins(5, 2, 5, 2)
            
            label = QLabel(f"Канал {channel}")
            label.setMinimumWidth(70)
            layout.addWidget(label)
            
            # Кнопки "Обычный" и "Мутант" для активных каналов
            btn_normal = QPushButton("⚔️ Обычный")
            btn_normal.clicked.connect(lambda _, ch=channel: self.logic.start_timer(ch, 300, "обычный"))
            layout.addWidget(btn_normal)
            
            btn_mutant = QPushButton("☠️ Мутант")
            btn_mutant.clicked.connect(lambda _, ch=channel: self.logic.start_timer(ch, 480, "мутант"))
            layout.addWidget(btn_mutant)
            
            # Кнопка удаления
            btn_delete = QPushButton("✖")
            btn_delete.setMaximumWidth(25)
            btn_delete.setStyleSheet("background-color: #e74c3c; color: white;")
            btn_delete.clicked.connect(lambda _, ch=channel: self.delete_channel(ch))
            layout.addWidget(btn_delete)
            
            # Отображение статуса
            if status == "timer":
                timers += 1
                timer_label = QLabel(f"⏱️ {int(time_left)//60:02d}:{int(time_left)%60:02d}")
                timer_label.setStyleSheet("color: #e67e22; font-weight: bold;")
                layout.addWidget(timer_label)
            elif status == "alive":
                alive += 1
                alive_label = QLabel("🔴 ЖИВ!")
                alive_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                layout.addWidget(alive_label)
            elif status == "unknown":
                unknown_label = QLabel("❓ Неизвестно")
                unknown_label.setStyleSheet("color: #3498db; font-weight: bold;")
                layout.addWidget(unknown_label)
            
            layout.addStretch()
            self.channels_layout.addWidget(frame)
        
        self.active_count.setText(f"Активные каналы: {len(self.logic.channels)}")
        self.timer_count.setText(f"Таймеры: {timers} | Живые: {alive}")

    def delete_channel(self, channel):
        self.logic.delete_channel(channel)
        self.update_channel_list()