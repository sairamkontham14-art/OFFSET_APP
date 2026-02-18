from PyQt5.QtCore import Qt, QPropertyAnimation, QRectF, QSize, pyqtProperty
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QLinearGradient, QFont, QPen
from PyQt5.QtWidgets import QWidget, QPushButton, QStyleOption, QStyle
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt

# Modern color schemes
DARK_THEME = {
    # Base colors
    'bg_primary': '#1E1E1E',
    'bg_secondary': '#252525',
    'bg_tertiary': '#2D2D2D',
    'bg_hover': '#3D3D3D',

    # New UI specific colors
    'sidebar_bg': '#252525',
    'content_bg': '#1E1E1E',  # Added missing key
    'menu_hover': '#333333',
    'menu_active': '#0078D4',
    'border_color': '#333333',
    'card_bg': '#2D2D2D',

    # Text colors
    'text_primary': '#FFFFFF',
    'text_secondary': '#B3B3B3',
    'text_disabled': '#666666',

    # Accent colors
    'accent_primary': '#0078D4',
    'accent_secondary': '#2B88D8',
    'accent_success': '#28A745',
    'accent_warning': '#FFC107',
    'accent_danger': '#DC3545',

    # Border colors
    'border_light': '#404040',
    'border_dark': '#1A1A1A',

    # Matplotlib specific colors
    'plot_bg': '#1E1E1E',
    'plot_fg': '#FFFFFF',
    'plot_grid': '#404040',
    'plot_face': '#252525',

    # Figure specific
    'figure_bg': '#252525',
    'figure_border': '#404040',
}

LIGHT_THEME = {
    # Base colors
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F8F9FA',
    'bg_tertiary': '#E9ECEF',
    'bg_hover': '#DEE2E6',

    # New UI specific colors
    'sidebar_bg': '#F8F9FA',
    'content_bg': '#FFFFFF',  # Added missing key
    'menu_hover': '#E9ECEF',
    'menu_active': '#0078D4',
    'border_color': '#DEE2E6',
    'card_bg': '#FFFFFF',

    # Text colors
    'text_primary': '#000000',
    'text_secondary': '#6C757D',
    'text_disabled': '#ADB5BD',

    # Accent colors
    'accent_primary': '#0078D4',
    'accent_secondary': '#2B88D8',
    'accent_success': '#28A745',
    'accent_warning': '#FFC107',
    'accent_danger': '#DC3545',

    # Border colors
    'border_light': '#DEE2E6',
    'border_dark': '#ADB5BD',

    # Matplotlib specific colors
    'plot_bg': '#FFFFFF',
    'plot_fg': '#000000',
    'plot_grid': '#DEE2E6',
    'plot_face': '#F8F9FA',

    # Figure specific
    'figure_bg': '#F8F9FA',
    'figure_border': '#DEE2E6',
}


def get_stylesheet(theme):
    return f"""
    /* Global styles */
    QWidget {{
        background-color: {theme['bg_primary']};
        color: {theme['text_primary']};
        font-family: 'Segoe UI', sans-serif;
    }}

    /* Main window */
    QMainWindow {{
        background-color: {theme['content_bg']};
    }}

    /* Sidebar */
    #sidebar {{
        background-color: {theme['sidebar_bg']};
        border-right: 1px solid {theme['border_color']};
        min-width: 250px;
        padding: 0;
    }}

    #sidebarTitle {{
        color: {theme['text_primary']};
        font-size: 18px;
        font-weight: bold;
        padding: 20px;
    }}

    /* Menu buttons */
    #menuButton {{
        text-align: left;
        padding: 12px 20px;
        border: none;
        border-radius: 8px;
        margin: 4px 12px;
        font-size: 14px;
        background-color: transparent;
        color: {theme['text_primary']};
    }}

    #menuButton:hover {{
        background-color: {theme['menu_hover']};
    }}

    #menuButton[selected="true"] {{
        background-color: {theme['menu_active']};
        color: white;
    }}

    /* Settings button */
    #settingsButton {{
        text-align: left;
        padding: 12px 20px;
        border: none;
        border-radius: 8px;
        margin: 12px;
        font-size: 14px;
        background-color: transparent;
        border-top: 1px solid {theme['border_color']};
    }}

    /* Content area */
    #contentArea {{
        background-color: {theme['content_bg']};
        padding: 20px;
    }}

    /* Toolbar */
    #toolbar {{
        background-color: {theme['bg_secondary']};
        border-bottom: 1px solid {theme['border_color']};
        padding: 10px 20px;
        min-height: 60px;
    }}

    /* Search input */
    #searchInput {{
        background-color: {theme['bg_tertiary']};
        border: 1px solid {theme['border_color']};
        border-radius: 6px;
        padding: 8px 12px;
        color: {theme['text_primary']};
    }}

    /* Cards */
    #fileCard {{
        background-color: {theme['card_bg']};
        border-radius: 8px;
        padding: 12px;
        margin: 8px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {theme['accent_primary']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
    }}

    QPushButton:hover {{
        background-color: {theme['accent_secondary']};
    }}

    QPushButton:pressed {{
        background-color: {theme['bg_hover']};
    }}

    /* Input fields */
    QLineEdit {{
        background-color: {theme['bg_tertiary']};
        border: 1px solid {theme['border_color']};
        border-radius: 6px;
        padding: 8px 12px;
        color: {theme['text_primary']};
    }}

    QLineEdit:focus {{
        border-color: {theme['accent_primary']};
    }}

    /* Canvas/Figure */
    FigureCanvas {{
        background-color: {theme['figure_bg']};
        border: 1px solid {theme['border_color']};
        border-radius: 8px;
        padding: 12px;
    }}

    /* Navigation Toolbar */
    QToolBar {{
        background-color: {theme['bg_secondary']};
        border: none;
        spacing: 8px;
        padding: 4px;
    }}
    """


class ModernThemeButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)
        self._is_dark = True
        self.setToolTip("Toggle Theme")
        self.setObjectName("themeButton")

        # Set initial icon and size
        self.setIconSize(QSize(24, 24))
        self.update_icon()

    def update_icon(self):
        icon_path = "icons/moon.png" if self._is_dark else "icons/sun.png"
        self.setIcon(QIcon(icon_path))

    def toggle_theme(self):
        self._is_dark = not self._is_dark
        self.update_icon()
        return DARK_THEME if self._is_dark else LIGHT_THEME