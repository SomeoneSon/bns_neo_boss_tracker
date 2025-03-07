import sys
from PyQt5.QtWidgets import QApplication
from ui import SpawnTracker

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpawnTracker()
    window.show()
    sys.exit(app.exec_())