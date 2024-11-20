import base64
import os
import re
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox

from util.Constants import UI
from util.SettingsManager import SettingsManager


class Utility:

    @staticmethod
    def get_icon_path(folder: str, icon: str):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = Path(os.path.dirname(__file__))
            base_path = base_path.parents[0]  # root path

        icon_path = os.path.join(base_path, folder, icon)
        icon_path = icon_path.replace(os.sep, '/')

        if not os.path.exists(icon_path):
            print(f"{UI.ICON_FILE_ERROR} {icon_path} {UI.ICON_FILE_NOT_EXIST}")
            return None
        return icon_path

    @staticmethod
    def get_settings_value(section: str, prop: str, default: str, save: bool) -> str:
        settings = SettingsManager.get_settings()
        settings.beginGroup(section)

        value = settings.value(prop, None)

        if value is None:
            if save:
                settings.setValue(prop, default)
                settings.sync()
            value = default

        settings.endGroup()
        return value

    @staticmethod
    def get_system_value(section: str, prefix: str, default: str, length: int) -> dict:
        settings = SettingsManager.get_settings()

        if section not in settings.childGroups():
            settings.beginGroup(section)
            for i in range(1, length + 1):
                settings.setValue(f"{prefix}{i}", default)
            settings.endGroup()

        settings.beginGroup(section)
        values = {f"{prefix}{i}": settings.value(f"{prefix}{i}", default) for i in range(1, length + 1)}
        settings.endGroup()

        return values

    @staticmethod
    def add_tavily_model_list(domain_list, domain_type):
        settings = SettingsManager.get_settings()
        settings.beginGroup(f"Tavily_{domain_type}_Domain_List")

        if domain_list and domain_type == 'Include':
            for domain in domain_list:
                settings.setValue(domain, True)

        if domain_list and domain_type == 'Exclude':
            for domain in domain_list:
                settings.setValue(domain, True)

        settings.endGroup()

    @staticmethod
    def remove_tavily_model_list(domain, domain_type):
        settings = SettingsManager.get_settings()
        settings.beginGroup(f"Tavily_{domain_type}_Domain_List")

        if settings.contains(domain):
            settings.remove(domain)

        settings.endGroup()

    @staticmethod
    def extract_number_from_end(name):
        match = re.search(r'\d+$', name)
        if match:
            return int(match.group())
        return None

    @staticmethod
    def confirm_dialog(title: str, message: str) -> bool:
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setLayout(QVBoxLayout())

        message_label = QLabel(message)
        dialog.layout().addWidget(message_label)

        dialog_buttonbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
        dialog.layout().addWidget(dialog_buttonbox)

        no_button = dialog_buttonbox.button(QDialogButtonBox.StandardButton.No)
        no_button.setDefault(True)
        no_button.setFocus()

        def on_click(button):
            dialog.done(dialog_buttonbox.standardButton(button) == QDialogButtonBox.StandardButton.Yes)

        dialog_buttonbox.clicked.connect(on_click)

        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted

    @staticmethod
    def base64_encode_file(path):
        with open(path, UI.FILE_READ_IN_BINARY_MODE) as file:
            return base64.b64encode(file.read()).decode(UI.UTF_8)

    @staticmethod
    def base64_encode_bytes(image_bytes):
        return base64.b64encode(image_bytes).decode('utf-8')

    @staticmethod
    def create_temp_file(content, extension_name, apply_decode):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + extension_name) as temp_file:
            if apply_decode:
                temp_file.write(base64.b64decode(content))
            else:
                temp_file.write(content)
            temp_file.flush()
            temp_file_name = temp_file.name
        return temp_file_name
