import sys
import os
import json
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QLineEdit, QAction, QPushButton, QVBoxLayout, QWidget, QDialog, QCheckBox, QLabel, QComboBox, QLineEdit as QLE)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

SETTINGS_FILE = "settings.json"

# --- Ad Blocker ---
class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        try:
            with open("blocklist.txt", "r") as file:
                self.blocked_domains = set(line.strip() for line in file if line.strip())
        except FileNotFoundError:
            self.blocked_domains = set()

    def interceptRequest(self, info):
        if not self.settings.get("ad_block_enabled", True):
            return
        url = info.requestUrl().toString()
        if any(domain in url for domain in self.blocked_domains):
            info.block(True)

# --- Settings Dialog ---
class SettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        self.adblock_checkbox = QCheckBox("Enable Ad Blocker")
        self.adblock_checkbox.setChecked(self.settings.get("ad_block_enabled", True))
        layout.addWidget(self.adblock_checkbox)

        self.darkmode_checkbox = QCheckBox("Enable Dark Mode")
        self.darkmode_checkbox.setChecked(self.settings.get("dark_mode", False))
        layout.addWidget(self.darkmode_checkbox)

        layout.addWidget(QLabel("Default Search Engine:"))
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.addItems(["DuckDuckGo", "Google", "Startpage", "Brave"])
        self.search_engine_combo.setCurrentText(self.settings.get("search_engine", "DuckDuckGo"))
        layout.addWidget(self.search_engine_combo)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings_and_close)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_settings_and_close(self):
        self.settings["ad_block_enabled"] = self.adblock_checkbox.isChecked()
        self.settings["dark_mode"] = self.darkmode_checkbox.isChecked()
        self.settings["search_engine"] = self.search_engine_combo.currentText()
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)
        self.accept()

# --- Main Browser ---
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OneTabBrowser")
        self.settings = self.load_settings()

        # Web view
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        # Apply dark mode
        if self.settings.get("dark_mode", False):
            self.setStyleSheet("""
                QMainWindow { background-color: #121212; }
                QLineEdit, QPushButton { background-color: #1e1e1e; color: #ffffff; border: 1px solid #333; }
                QLabel { color: #ffffff; }
            """)

        # Ad blocker
        self.adblocker = AdBlocker(self.settings)
        from PyQt5.QtWebEngineWidgets import QWebEngineProfile
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.adblocker)

        # Toolbar
        navtb = QToolBar()
        self.addToolBar(navtb)

        back_btn = QAction("Back", self)
        back_btn.triggered.connect(self.browser.back)
        navtb.addAction(back_btn)

        forward_btn = QAction("Forward", self)
        forward_btn.triggered.connect(self.browser.forward)
        navtb.addAction(forward_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.triggered.connect(self.browser.reload)
        navtb.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setFixedWidth(1120)
        navtb.addWidget(self.url_bar)

        settings_btn = QAction("Settings", self)
        settings_btn.triggered.connect(self.open_settings)
        navtb.addAction(settings_btn)

        # Load homepage
        self.navigate_home()
        self.browser.urlChanged.connect(self.update_url_bar)

        self.show()
        self.showMaximized()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        return {
            "ad_block_enabled": True,
            "dark_mode": False,
            "search_engine": "DuckDuckGo"
        }

    def open_settings(self):
        dlg = SettingsDialog(self.settings)
        if dlg.exec_():
            self.close()
            os.execl(sys.executable, sys.executable, *sys.argv)

    def navigate_home(self):
        self.browser.setUrl(QUrl(self.get_search_url("")))

    def navigate_to_url(self):
        q = self.url_bar.text()
        if q.startswith("http"):
            self.browser.setUrl(QUrl(q))
        else:
            self.browser.setUrl(QUrl(self.get_search_url(q)))

    def update_url_bar(self, q):
        self.url_bar.setText(q.toString())

    def get_search_url(self, query):
        engine = self.settings.get("search_engine", "DuckDuckGo")
        encoded = query.replace(" ", "+")
        if engine == "DuckDuckGo":
            return f"https://duckduckgo.com/?q={encoded}"
        elif engine == "Google":
            return f"https://www.google.com/search?q={encoded}"
        elif engine == "Startpage":
            return f"https://www.startpage.com/do/search?query={encoded}"
        elif engine == "Brave":
            return f"https://search.brave.com/search?q={encoded}"
        else:
            return f"https://duckduckgo.com/?q={encoded}"

    def closeEvent(self, event):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)
        event.accept()

# --- Run the App ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Browser()
    sys.exit(app.exec_())
