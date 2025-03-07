def apply_dark_theme(widget):
    widget.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #2D2D30;
            color: #CCCCCC;
        }
        QFrame {
            background-color: #252526;
            border: 1px solid #3F3F46;
            border-radius: 4px;
        }
        QLabel {
            color: #CCCCCC;
        }
        QPushButton {
            background-color: #3C3C3C;
            color: #CCCCCC;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
            min-height: 25px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #5C5C5C;
        }
        QScrollArea {
            border: 1px solid #3F3F46;
            background-color: #252526;
        }
        QScrollBar:vertical {
            background-color: #2D2D30;
            width: 10px;
            margin: 15px 0 15px 0;
        }
        QScrollBar::handle:vertical {
            background-color: #3F3F46;
            min-height: 20px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #555555;
        }
    """)