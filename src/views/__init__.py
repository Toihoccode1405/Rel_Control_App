"""
kRel - Views Package
UI Views and Dialogs
"""
from src.views.login_dialog import LoginDialog
from src.views.register_dialog import RegisterDialog
from src.views.main_window import MainWindow
from src.views.input_tab import InputTab
from src.views.edit_tab import EditTab
from src.views.report_tab import ReportTab
from src.views.settings_tab import SettingsTab

__all__ = [
    "LoginDialog",
    "RegisterDialog",
    "MainWindow",
    "InputTab",
    "EditTab",
    "ReportTab",
    "SettingsTab",
]