import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QGridLayout,
    QDoubleSpinBox, QPushButton, QTimeEdit, QLineEdit, QSizePolicy, QMessageBox, QFileDialog, QTabWidget, QTextEdit,
    QScrollArea, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtGui import QColor, QPixmap, QIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
import os
import mplcursors
import rigidez_backend
from openpyxl.utils import get_column_letter

# Estilo personalizado para a caixa de diálogo de configuração do matplotlib
MATPLOTLIB_DIALOG_STYLE = """
QDialog {
    background-color: #000000;
    color: #FFFFFF;
}
QLabel {
    color: #FFFFFF;
    font-family: 'Porsche', 'Montserrat', sans-serif;
    font-size: 12px;
    padding: 4px;
}
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: rgba(255, 255, 255, 0.1);
    color: #FFFFFF;
    border: 1px solid #D40000;
    border-radius: 4px;
    padding: 4px;
    min-width: 60px;
    min-height: 24px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #D40000;
    background-color: rgba(212, 0, 0, 0.1);
}
QPushButton {
    background-color: #D40000;
    color: #FFFFFF;
    border-radius: 4px;
    padding: 8px 16px;
    font-family: 'Porsche', 'Montserrat', sans-serif;
    font-weight: bold;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #FF4C4C;
    border: 1px solid #FFFFFF;
}
QPushButton:pressed {
    background-color: #A80000;
}
QGroupBox {
    border: 2px solid #D40000;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    background-color: rgba(0, 0, 0, 0.85);
}
QGroupBox::title {
    color: #FFFFFF;
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
}
"""

class CustomNavigationToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent)
        self.setStyleSheet("""
            QToolBar {
                background: transparent;
                spacing: 6px;
                padding: 4px;
            }
            QToolButton {
                background: transparent;
                border: none;
                padding: 4px;
                color: #FFFFFF;
            }
            QToolButton:hover {
                border: 1px solid #D40000;
                border-radius: 4px;
            }
            QToolButton:pressed {
                background: rgba(212, 0, 0, 0.1);
            }
            QSpinBox {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
                border: 1px solid #D40000;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        # Personalizar ícones
        for action in self.actions():
            if action.icon():
                if action.text() == "Save":
                    # Substituir o ícone de salvar por um emoji
                    save_btn = QPushButton("💾")
                    save_btn.setToolTip("Save the figure")
                    save_btn.setStyleSheet("""
                        QPushButton {
                            background: transparent;
                            color: #D40000;
                            border: none;
                            padding: 4px;
                            font-size: 18px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 30px;
                            max-height: 30px;
                        }
                        QPushButton:hover { 
                            border: 1px solid #D40000;
                            border-radius: 4px;
                        }
                        QPushButton:pressed {
                            background: rgba(212, 0, 0, 0.1);
                        }
                    """)
                    save_btn.clicked.connect(action.trigger)
                    action.setVisible(False)
                    self.addWidget(save_btn)
                else:
                    # Mudar a cor dos outros ícones para vermelho
                    icon = action.icon()
                    pixmap = icon.pixmap(24, 24)
                    mask = pixmap.createMaskFromColor(QColor('black'), Qt.MaskMode.MaskOutColor)
                    pixmap.fill(QColor('#D40000'))
                    pixmap.setMask(mask)
                    action.setIcon(QIcon(pixmap))
        
    def _init_toolbar(self):
        super()._init_toolbar()
        for action in self.actions():
            if action.text() == "Customize":
                action.triggered.disconnect()
                action.triggered.connect(self.customize_dialog)
    
    def customize_dialog(self):
        # Chama o diálogo de configuração original
        result = super().edit_parameters()
        if result:
            # Se o diálogo foi aceito, aplica o estilo personalizado
            for widget in self.findChildren(QDialog):
                widget.setStyleSheet(MATPLOTLIB_DIALOG_STYLE)
        return result

class TirePressureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tire Management System")
        self.setMinimumSize(1366, 768)
        self.sessions_data = []
        self.base_font_size = 14
        self.base_groupbox_font_size = 16
        self.base_spacing = 12

        # Inicialização do gráfico principal
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        # Estilos
        self.setStyleSheet("""
            QMainWindow, QWidget {
                font-family: 'Porsche', 'Montserrat', sans-serif;
                color: #FFFFFF;
                background-color: transparent;
                font-weight: bold;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.2);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #D40000;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: rgba(0, 0, 0, 0.2);
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #D40000;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QGroupBox {
                color: #FFFFFF;
                font: bold 16px 'Porsche';
                border: 2px solid #D40000;
                border-radius: 8px;
                margin: 10px;
                padding: 18px 12px;
                background: rgba(0, 0, 0, 0.85);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                background: #D40000;
                padding: 4px 12px;
                margin-top: 12px;
                font: bold 16px 'Porsche';
                color: #FFFFFF;
                border-radius: 4px;
            }
            QLabel {
                font: bold 14px 'Porsche';
                color: #FFFFFF;
            }
            QDoubleSpinBox, QLineEdit, QTimeEdit {
                background: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
                border: 1px solid #D40000;
                border-radius: 4px;
                padding: 6px;
                font: bold 14px 'Porsche';
                min-width: 60px;
            }
            QDoubleSpinBox:focus, QLineEdit:focus, QTimeEdit:focus {
                border: 2px solid #D40000;
                background: rgba(212, 0, 0, 0.1);
            }
            QPushButton {
                background: #D40000;
                color: #FFFFFF;
                border-radius: 4px;
                padding: 12px 24px;
                font: bold 14px 'Porsche';
                text-transform: uppercase;
                min-width: 120px;
            }
            QPushButton:hover { 
                background: #FF4C4C;
                border: 1px solid #FFFFFF;
            }
            QPushButton:pressed {
                background: #A80000;
            }
            QTabWidget::pane {
                border: 2px solid #D40000;
                background: transparent;
            }
            QTabBar::tab {
                background: #1A1A1A;
                color: #FFFFFF;
                padding: 8px 16px;
                border: 1px solid #D40000;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #D40000;
                color: #FFFFFF;
            }
            QTabBar::tab:hover:!selected {
                background: #2A2A2A;
            }
        """)

        # Fundo com imagem
        bg_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'background ff.png')
        self.bg_label = None
        if os.path.exists(bg_path):
            self.bg_label = QLabel(self)
            pixmap = QPixmap(bg_path)
            self.bg_label.setPixmap(pixmap)
            self.bg_label.setScaledContents(True)
            self.bg_label.lower()
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
            self.bg_label.setStyleSheet("opacity: 0.5;")
            self.bg_label.show()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(12, 12, 12, 12)
        self.central_layout.setSpacing(12)
        
        # Configuração das tabs com scroll
        self.tabs = QTabWidget()
        self.central_layout.addWidget(self.tabs)
        
        # Tab Data Entry com scroll
        self.tab_data = QWidget()
        self.tab_data_scroll = QScrollArea()
        self.tab_data_scroll.setWidget(self.tab_data)
        self.tab_data_scroll.setWidgetResizable(True)
        self.tab_data_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_data_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabs.addTab(self.tab_data_scroll, "DATA ENTRY")
        self.build_data_tab(self.tab_data)
        
        # Nova aba Rigidez Backend
        self.tab_rigidez = QWidget()
        self.tab_rigidez_scroll = QScrollArea()
        self.tab_rigidez_scroll.setWidget(self.tab_rigidez)
        self.tab_rigidez_scroll.setWidgetResizable(True)
        self.tab_rigidez_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_rigidez_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabs.addTab(self.tab_rigidez_scroll, "ARB SETUP")
        self.build_rigidez_tab(self.tab_rigidez)
        
        self.resizeEvent = self._resize_bg_and_fonts

    def _resize_bg_and_fonts(self, event):
        # Ajusta imagem de fundo
        if self.bg_label:
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        # Ajuste dinâmico de fonte e espaçamento
        w = self.width()
        h = self.height()
        # Fator de escala baseado na largura (pode ajustar para ser mais ou menos sensível)
        scale = min(max(w / 1920, 0.7), 1.0)
        font_size = int(self.base_font_size * scale)
        groupbox_font_size = int(self.base_groupbox_font_size * scale)
        spacing = int(self.base_spacing * scale)
        # Ajusta fonte global
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                font-family: 'Porsche', 'Montserrat', sans-serif;
                color: #FFFFFF;
                background-color: transparent;
                font-weight: bold;
                font-size: {font_size}px;
            }}
            QGroupBox {{
                color: #FFFFFF;
                font: bold {groupbox_font_size}px 'Porsche';
                border: 2px solid #D40000;
                border-radius: 8px;
                margin: 10px;
                padding: 18px 12px;
                background: rgba(0, 0, 0, 0.85);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                background: #D40000;
                padding: 4px 12px;
                margin-top: 12px;
                font: bold {groupbox_font_size}px 'Porsche';
                color: #FFFFFF;
                border-radius: 4px;
            }}
            QLabel {{
                font: bold {font_size}px 'Porsche';
                color: #FFFFFF;
            }}
            QDoubleSpinBox, QLineEdit, QTimeEdit {{
                background: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
                border: 1px solid #D40000;
                border-radius: 4px;
                padding: 6px;
                font: bold {font_size}px 'Porsche';
                min-width: 60px;
            }}
            QDoubleSpinBox:focus, QLineEdit:focus, QTimeEdit:focus {{
                border: 2px solid #D40000;
                background: rgba(212, 0, 0, 0.1);
            }}
            QPushButton {{
                background: #D40000;
                color: #FFFFFF;
                border-radius: 4px;
                padding: 12px 24px;
                font: bold {font_size}px 'Porsche';
                text-transform: uppercase;
                min-width: 100px;
            }}
            QPushButton:hover {{ 
                background: #FF4C4C;
                border: 1px solid #FFFFFF;
            }}
            QPushButton:pressed {{
                background: #A80000;
            }}
            QTabWidget::pane {{
                border: 2px solid #D40000;
                background: transparent;
            }}
            QTabBar::tab {{
                background: #1A1A1A;
                color: #FFFFFF;
                padding: 8px 16px;
                border: 1px solid #D40000;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                font-size: {font_size}px;
            }}
            QTabBar::tab:selected {{
                background: #D40000;
                color: #FFFFFF;
            }}
            QTabBar::tab:hover:!selected {{
                background: #2A2A2A;
            }}
        """)
        # Ajusta espaçamento dos layouts principais
        for layout in [self.central_layout]:
            layout.setSpacing(spacing)
        QWidget.resizeEvent(self, event)

    def build_data_tab(self, parent):
        root = QHBoxLayout(parent)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        # --- LADO ESQUERDO (INPUTS) ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(0, 0, 0, 0)
        # Session Info
        session = self._make_session_info()
        session.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(session)
        # 2x2x1 GRID
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        # Pressures
        self.spinboxes = {}
        grp1, spins1 = self._make_pressure_group("Target Pressures (psi)", "Pressão alvo recomendada para o pneu")
        grp2, spins2 = self._make_pressure_group("Cold Pressures (psi)", "Pressão fria medida para o pneu")
        grp3, spins3 = self._make_pressure_group("Hot Pressures (psi)", "Pressão quente medida para o pneu")
        temp_box = QGroupBox("Temperatures (°C)")
        temp_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        g = QGridLayout(temp_box)
        g.setAlignment(Qt.AlignCenter)
        g.setSpacing(2)
        temps = [("Air Before", 'air1'), ("Track Before", 'track1'), ("Air After", 'air2'), ("Track After", 'track2')]
        for idx, (lbl, attr) in enumerate(temps):
            r, c = divmod(idx,2)
            g.addWidget(QLabel(lbl), r, c*2)
            spin = QDoubleSpinBox(); spin.setDecimals(1); spin.setMinimumWidth(60); spin.setMinimumHeight(24)
            spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            spin.setToolTip(f"Temperatura {lbl.lower()}")
            setattr(self, attr, spin)
            g.addWidget(spin, r, c*2+1)
        self.spinboxes["Target Pressures (psi)"] = spins1
        self.spinboxes["Cold Pressures (psi)"] = spins2
        self.spinboxes["Hot Pressures (psi)"] = spins3
        # Adiciona ao grid 2x2
        grid.addWidget(grp1, 0, 0)
        grid.addWidget(grp2, 0, 1)
        grid.addWidget(grp3, 1, 0)
        grid.addWidget(temp_box, 1, 1)
        # Car Setup com imagens
        setup_container = QWidget()
        setup_layout = QHBoxLayout(setup_container)
        setup_layout.setContentsMargins(0, 0, 0, 0)
        setup_layout.setSpacing(10)
        
        # Imagem do carro
        car_image_label = QLabel()
        car_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'SP21L31IX0002_low-1.png')
        if os.path.exists(car_path):
            car_pixmap = QPixmap(car_path)
            # Reduzindo para 120 pixels de largura mantendo proporção
            car_pixmap = car_pixmap.scaledToWidth(240, Qt.SmoothTransformation)
            car_image_label.setPixmap(car_pixmap)
        car_image_label.setStyleSheet("background: transparent;")
        setup_layout.addWidget(car_image_label)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'Felipe_Forte_Motorsports-removebg-preview.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_pixmap = logo_pixmap.scaledToHeight(150, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        logo_label.setStyleSheet("background: transparent;")
        setup_layout.addWidget(logo_label)
        
        # Car Setup Box
        setup_box = QGroupBox("Car Setup")
        setup_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        setup_box.setMinimumWidth(200)
        g3 = QGridLayout(setup_box)
        g3.setAlignment(Qt.AlignCenter)
        g3.setSpacing(2)
        
        # ARB Controls
        arb_labels = ['Arb FL', 'Arb FR', 'Arb RL', 'Arb RR']
        self.arb_spins = {}
        for idx, lbl in enumerate(arb_labels):
            r, c = divmod(idx, 2)
            g3.addWidget(QLabel(lbl), r, c*2)
            spin = QDoubleSpinBox()
            spin.setDecimals(1)
            spin.setRange(1.0, 7.0)
            spin.setMinimumWidth(60)
            spin.setMinimumHeight(24)
            spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            spin.setToolTip(f"Barra anti-rolagem {lbl}")
            self.arb_spins[lbl] = spin
            g3.addWidget(spin, r, c*2+1)
        
        # Wing centralizado
        wing_container = QWidget()
        wing_layout = QHBoxLayout(wing_container)
        wing_layout.setContentsMargins(0, 0, 0, 0)
        wing_layout.addStretch()
        wing_layout.addWidget(QLabel("Wing"))
        self.wing_spin = QDoubleSpinBox()
        self.wing_spin.setDecimals(1)
        self.wing_spin.setRange(0.0, 10.0)
        self.wing_spin.setMinimumWidth(60)
        self.wing_spin.setMinimumHeight(24)
        self.wing_spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.wing_spin.setToolTip("Ajuste do aerofólio")
        wing_layout.addWidget(self.wing_spin)
        wing_layout.addStretch()
        g3.addWidget(wing_container, 2, 0, 1, 4, Qt.AlignCenter)
        
        setup_layout.addWidget(setup_box)
        setup_layout.addStretch()
        
        grid.addWidget(setup_container, 2, 0, 1, 2, Qt.AlignCenter)
        left_layout.addLayout(grid)
        # Observações
        obs_box = QGroupBox("SESSION OBSERVATIONS")
        obs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        obs_layout = QVBoxLayout(obs_box)
        self.obs_text = QTextEdit()
        self.obs_text.setPlaceholderText("Anote aqui observações rápidas, condições da pista, pneus, etc.")
        self.obs_text.setMinimumHeight(40)
        self.obs_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        obs_layout.addWidget(self.obs_text)
        left_layout.addWidget(obs_box)
        left_layout.addStretch(1)
        # --- LADO DIREITO (RESULTADOS E BOTÕES) ---
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(0, 0, 0, 0)
        # Buttons
        btn_calc = QPushButton("CALCULATE\nCORRECTIONS")
        btn_calc.setStyleSheet("""
            QPushButton {
                text-align: center;
                line-height: 120%;
                padding: 8px 12px;
            }
        """)
        btn_calc.clicked.connect(self.calculate)
        btn_new = QPushButton("NEW SESSION")
        btn_new.clicked.connect(self.new_session)
        btn_export = QPushButton("GENERATE REPORT")
        btn_export.clicked.connect(self.export_report)
        btnc = QWidget()
        hb2 = QHBoxLayout(btnc)
        hb2.setContentsMargins(0, 0, 0, 0)
        hb2.setSpacing(6)
        for btn in [btn_calc, btn_new, btn_export]:
            btn.setMinimumWidth(100)
            btn.setMinimumHeight(50)  # Aumentando a altura mínima para acomodar duas linhas
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            hb2.addWidget(btn)
        right_layout.addWidget(btnc)
        # Results
        self.results = {}
        for title in ["Corrected Cold Pressure", "Cold pr. corrected by air temp", "Cold pr. corrected by Track Temp"]:
            box = QGroupBox(title)
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            g3 = QGridLayout(box)
            g3.setAlignment(Qt.AlignCenter)
            g3.setSpacing(2)
            outs = {}
            for i, lbl in enumerate(['FL','FR','RL','RR']):
                r, c = (0 if i<2 else 1), (0 if lbl in ['FL','RL'] else 2)
                g3.addWidget(QLabel(lbl), r, c)
                out = QLineEdit(); out.setReadOnly(True); out.setMinimumWidth(60); out.setMinimumHeight(24)
                out.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                g3.addWidget(out, r, c+1)
                outs[lbl] = out
            right_layout.addWidget(box)
            self.results[title] = outs
        # Mini gráfico interativo ocupando todo espaço restante
        mini_chart_box = QGroupBox("Session Chart")
        mini_chart_layout = QVBoxLayout(mini_chart_box)
        
        # Criar o canvas primeiro
        self.mini_figure = Figure()
        self.mini_canvas = FigureCanvas(self.mini_figure)
        self.mini_ax = self.mini_figure.add_subplot(111)
        
        # Toolbar e botão fullscreen em layout horizontal
        toolbar_layout = QHBoxLayout()
        self.mini_toolbar = NavigationToolbar2QT(self.mini_canvas, right)
        
        # Estilizar os botões da toolbar
        self.mini_toolbar.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QToolButton:hover {
                border: 1px solid #D40000;
                border-radius: 4px;
            }
            QToolButton:pressed {
                background: rgba(212, 0, 0, 0.1);
            }
        """)
        
        # Mudar a cor dos ícones para vermelho e substituir o ícone de salvar
        for action in self.mini_toolbar.actions():
            if action.icon():
                if action.text() == "Save":
                    # Criar botão personalizado para salvar
                    save_btn = QPushButton("💾")  # Ícone Unicode de disquete
                    save_btn.setToolTip("Save the figure")
                    save_btn.setStyleSheet("""
                        QPushButton {
                            background: transparent;
                            color: #D40000;
                            border: none;
                            padding: 4px;
                            font-size: 18px;
                            min-width: 30px;
                            max-width: 30px;
                            min-height: 30px;
                            max-height: 30px;
                        }
                        QPushButton:hover { 
                            border: 1px solid #D40000;
                            border-radius: 4px;
                        }
                        QPushButton:pressed {
                            background: rgba(212, 0, 0, 0.1);
                        }
                    """)
                    save_btn.clicked.connect(action.trigger)
                    action.setVisible(False)  # Esconde o botão original
                    toolbar_layout.addWidget(save_btn)
                else:
                    # Outros ícones em vermelho
                    icon = action.icon()
                    pixmap = icon.pixmap(24, 24)
                    mask = pixmap.createMaskFromColor(QColor('black'), Qt.MaskMode.MaskOutColor)
                    pixmap.fill(QColor('#D40000'))
                    pixmap.setMask(mask)
                    action.setIcon(QIcon(pixmap))
        
        toolbar_layout.addWidget(self.mini_toolbar)
        
        fullscreen_btn = QPushButton("⛶")  # Ícone Unicode para tela cheia
        fullscreen_btn.setToolTip("View in fullscreen")
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #D40000;
                border: none;
                padding: 4px;
                font-size: 18px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
            }
            QPushButton:hover { 
                border: 1px solid #D40000;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background: rgba(212, 0, 0, 0.1);
            }
        """)
        fullscreen_btn.clicked.connect(self.show_mini_fullscreen_chart)
        toolbar_layout.addWidget(fullscreen_btn)
        toolbar_layout.addStretch()
        
        mini_chart_layout.addLayout(toolbar_layout)
        mini_chart_layout.addWidget(self.mini_canvas, stretch=10)
        
        right_layout.addWidget(mini_chart_box, stretch=10)
        root.addWidget(left, stretch=2)
        root.addWidget(right, stretch=1)

    def _make_session_info(self):
        session = QGroupBox("Session Info")
        session.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hb = QHBoxLayout(session)
        hb.setAlignment(Qt.AlignCenter)
        hb.setSpacing(6)
        name_l, start_l, end_l = QLabel("Name:"), QLabel("Start:"), QLabel("End:")
        self.session_name = QLineEdit(); self.session_name.setMinimumWidth(80)
        self.session_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.session_name.setToolTip("Nome da sessão ou piloto")
        self.start_time = QTimeEdit(QTime.currentTime()); self.start_time.setDisplayFormat("HH:mm"); self.start_time.setMinimumWidth(60)
        self.start_time.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_time.setToolTip("Horário de início da sessão")
        self.end_time = QTimeEdit(QTime.currentTime()); self.end_time.setDisplayFormat("HH:mm"); self.end_time.setMinimumWidth(60)
        self.end_time.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.end_time.setToolTip("Horário de término da sessão")
        for w in [self.session_name, self.start_time, self.end_time]:
            w.setMinimumHeight(26)
        hb.addWidget(name_l); hb.addWidget(self.session_name)
        hb.addWidget(start_l); hb.addWidget(self.start_time)
        hb.addWidget(end_l); hb.addWidget(self.end_time)
        return session

    def _make_pressure_group(self, title, tip=None):
        box = QGroupBox(title)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        g = QGridLayout(box)
        g.setAlignment(Qt.AlignCenter)
        g.setSpacing(2)
        spins = {}
        for i, lbl in enumerate(['FL','FR','RL','RR']):
            r, c = (0 if i<2 else 1), (0 if lbl in ['FL','RL'] else 2)
            g.addWidget(QLabel(lbl), r, c)
            spin = QDoubleSpinBox(); spin.setDecimals(1); spin.setMinimumWidth(60); spin.setMinimumHeight(24)
            spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if tip:
                spin.setToolTip(f"{tip} {lbl}")
            g.addWidget(spin, r, c+1)
            spins[lbl] = spin
        return box, spins

    def calculate(self):
        phases = ["Target Pressures (psi)", "Cold Pressures (psi)", "Hot Pressures (psi)"]
        tires = ['FL','FR','RL','RR']
        vals = {ph: {t: self.spinboxes[ph][t].value() for t in tires} for ph in phases}
        air1K = self.air1.value() + 273.15; air2K = self.air2.value() + 273.15
        track1K = self.track1.value() + 273.15; track2K = self.track2.value() + 273.15
        for t in tires:
            tgt, cold, hot = vals['Target Pressures (psi)'][t], vals['Cold Pressures (psi)'][t], vals['Hot Pressures (psi)'][t]
            new_cold = cold * tgt / hot if hot else 0
            corr_air = new_cold * air2K / air1K if air1K else 0
            new_cold_b = new_cold / 14.504
            corr_track = (((new_cold_b+1)*air2K)/((air2K*(new_cold_b+1)/(new_cold_b+1))+(track2K-track1K))-1)*14.504 if track1K else 0
            self.results['Corrected Cold Pressure'][t].setText(f"{new_cold:.2f}")
            self.results['Cold pr. corrected by air temp'][t].setText(f"{corr_air:.2f}")
            self.results['Cold pr. corrected by Track Temp'][t].setText(f"{corr_track:.2f}")

    def new_session(self):
        data = {
            'session_name': self.session_name.text(),
            'start_time': self.start_time.time().toString('HH:mm'),
            'end_time': self.end_time.time().toString('HH:mm')
        }
        for ph, spins in self.spinboxes.items():
            for tire, spin in spins.items():
                data[f"{ph}_{tire}"] = spin.value()
        for attr in ['air1','air2','track1','track2']:
            data[attr] = getattr(self, attr).value()
        # Adiciona dados de setup
        for lbl, spin in self.arb_spins.items():
            data[lbl.lower().replace(' ', '_')] = spin.value()
        data['wing'] = self.wing_spin.value()
        # Adiciona observações
        data['observacoes'] = self.obs_text.toPlainText()
        for grp, outs in self.results.items():
            for tire, out in outs.items():
                data[f"{grp}_{tire}"] = float(out.text() or 0)
        self.sessions_data.append(data)
        QMessageBox.information(self, "New Session", f"Session '{data['session_name']}' saved successfully.")
        self.reset_fields(); self.update_chart()

    def export_report(self):
        if not self.sessions_data:
            QMessageBox.warning(self, "No Data", "No sessions to export.")
            return
        
        # Reorganizar as colunas em uma ordem mais lógica
        column_order = [
            'session_name', 'start_time', 'end_time',
            # Pressões alvo
            'Target Pressures (psi)_FL', 'Target Pressures (psi)_FR',
            'Target Pressures (psi)_RL', 'Target Pressures (psi)_RR',
            # Pressões frias
            'Cold Pressures (psi)_FL', 'Cold Pressures (psi)_FR',
            'Cold Pressures (psi)_RL', 'Cold Pressures (psi)_RR',
            # Pressões quentes
            'Hot Pressures (psi)_FL', 'Hot Pressures (psi)_FR',
            'Hot Pressures (psi)_RL', 'Hot Pressures (psi)_RR',
            # Temperaturas
            'air1', 'air2', 'track1', 'track2',
            # Car Setup
            'arb_fl', 'arb_fr', 'arb_rl', 'arb_rr', 'wing',
            # Resultados calculados
            'Corrected Cold Pressure_FL', 'Corrected Cold Pressure_FR',
            'Corrected Cold Pressure_RL', 'Corrected Cold Pressure_RR',
            'Cold pr. corrected by air temp_FL', 'Cold pr. corrected by air temp_FR',
            'Cold pr. corrected by air temp_RL', 'Cold pr. corrected by air temp_RR',
            'Cold pr. corrected by Track Temp_FL', 'Cold pr. corrected by Track Temp_FR',
            'Cold pr. corrected by Track Temp_RL', 'Cold pr. corrected by Track Temp_RR',
            # Observações
            'observacoes'
        ]
        
        df = pd.DataFrame(self.sessions_data)
        
        # Reordenar as colunas, mantendo apenas as que existem no DataFrame
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "sessions_report.xlsx", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if path:
            try:
                if path.endswith('.xlsx'):
                    # Configurar o writer do Excel para formatar as células
                    with pd.ExcelWriter(path, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Tire Data')
                        # Ajustar largura das colunas
                        worksheet = writer.sheets['Tire Data']
                        for idx, col in enumerate(df.columns):
                            # Encontrar o comprimento máximo na coluna
                            max_length = max(
                                df[col].astype(str).apply(len).max(),
                                len(str(col))
                            )
                            # Adicionar um pouco de espaço extra
                            worksheet.column_dimensions[get_column_letter(idx + 1)].width = max_length + 2
                    QMessageBox.information(self, "Export Complete", f"Report saved to {path}")
                else:
                    # Salvar como CSV usando ponto e vírgula como separador
                    df.to_csv(path, index=False, sep=';', decimal=',', encoding='utf-8-sig')
                    QMessageBox.information(self, "Export Complete", f"Report saved to {path}")
            except Exception as e:
                # Tentar salvar como CSV se falhar o Excel
                try:
                    csv_path = path.rsplit('.', 1)[0] + '.csv'
                    df.to_csv(csv_path, index=False, sep=';', decimal=',', encoding='utf-8-sig')
                    QMessageBox.warning(self, "Fallback to CSV", 
                        f"Could not save as Excel (error: {str(e)}). Saved as CSV: {csv_path}")
                except Exception as e2:
                    QMessageBox.critical(self, "Export Failed", 
                        f"Failed to export data: {str(e2)}")

    def reset_fields(self):
        from PySide6.QtCore import QTime
        # Limpar Session Info
        self.session_name.clear()
        self.start_time.setTime(QTime.currentTime())
        self.end_time.setTime(QTime.currentTime())
        # Limpar pressões
        for spins in self.spinboxes.values():
            for spin in spins.values():
                spin.setValue(0.0)
        # Limpar temperaturas
        for attr in ['air1','air2','track1','track2']:
            getattr(self, attr).setValue(0.0)
        # Limpar setup
        for spin in self.arb_spins.values():
            spin.setValue(1.0)  # Valor inicial para as barras
        self.wing_spin.setValue(0.0)
        # Limpar resultados
        for outs in self.results.values():
            for out in outs.values():
                out.clear()
        # Limpar observações
        self.obs_text.clear()

    def update_chart(self):
        self.ax.clear()
        self.mini_ax.clear()
        if not self.sessions_data:
            self.ax.text(0.5,0.5,'No data', ha='center', va='center')
            self.mini_ax.text(0.5,0.5,'No data', ha='center', va='center')
        else:
            df = pd.DataFrame(self.sessions_data)
            x = range(len(df))
            x_labels = df['session_name'].tolist()
            
            # Criar legenda separada abaixo do gráfico
            box = self.ax.get_position()
            self.ax.set_position([box.x0, box.y0 + box.height * 0.1,
                                box.width, box.height * 0.9])
            
            box_mini = self.mini_ax.get_position()
            self.mini_ax.set_position([box_mini.x0, box_mini.y0 + box_mini.height * 0.1,
                                     box_mini.width, box_mini.height * 0.9])

            lines = []
            labels = []
            
            phases = ["Target Pressures (psi)", "Cold Pressures (psi)", "Hot Pressures (psi)"]
            for ph in phases:
                for t in ['FL','FR','RL','RR']:
                    col = f"{ph}_{t}"
                    if col in df:
                        line, = self.ax.plot(x, df[col], label=col)
                        self.mini_ax.plot(x, df[col], label=col)
                        lines.append(line)
                        labels.append(col)
            
            for attr in ['air1','air2','track1','track2']:
                if attr in df:
                    line, = self.ax.plot(x, df[attr], label=attr)
                    self.mini_ax.plot(x, df[attr], label=attr)
                    lines.append(line)
                    labels.append(attr)
            
            # Configurar eixo x com os nomes das sessões
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(x_labels, rotation=45, ha='right')
            self.mini_ax.set_xticks(x)
            self.mini_ax.set_xticklabels(x_labels, rotation=45, ha='right')
            
            self.ax.set_xlabel('Session Name')
            self.ax.set_ylabel('Value')
            self.mini_ax.set_xlabel('Session Name')
            self.mini_ax.set_ylabel('Value')
            
            # Adicionar legenda abaixo do gráfico em múltiplas linhas
            self.ax.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15),
                         ncol=4, fontsize='small')
            self.mini_ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                              ncol=4, fontsize=6)
            
            # Adicionar grid
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.mini_ax.grid(True, linestyle='--', alpha=0.7)
            
            # Configurar interatividade
            self.cursor = mplcursors.cursor(lines, hover=True)
            @self.cursor.connect("add")
            def on_add(sel):
                x_val = int(sel.target[0])
                y_val = sel.target[1]
                session_name = x_labels[x_val]
                sel.annotation.set_text(f'Session: {session_name}\nValue: {y_val:.2f}')
                sel.annotation.get_bbox_patch().set(fc="black", alpha=0.8)
                sel.annotation.set_color('white')
            
            # Ajustar layout
            self.figure.tight_layout()
            self.mini_figure.tight_layout()
        
        self.canvas.draw()
        self.mini_canvas.draw()

    def show_mini_fullscreen_chart(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Session Chart Fullscreen View")
        dialog.setWindowState(Qt.WindowMaximized)
        dialog.setStyleSheet(MATPLOTLIB_DIALOG_STYLE)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        
        toolbar_container = QHBoxLayout()
        
        figure = Figure(figsize=(16, 9), dpi=100)
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        # Criar legenda separada abaixo do gráfico
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                        box.width, box.height * 0.9])
        
        # Usar a toolbar personalizada
        toolbar = CustomNavigationToolbar(canvas, dialog)
        toolbar_container.addWidget(toolbar)
        toolbar_container.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setToolTip("Close fullscreen")
        close_btn.clicked.connect(dialog.close)
        toolbar_container.addWidget(close_btn)
        
        layout.addLayout(toolbar_container)
        layout.addWidget(canvas)
        
        if self.sessions_data:
            df = pd.DataFrame(self.sessions_data)
            x = range(len(df))
            x_labels = df['session_name'].tolist()
            
            lines = []
            labels = []
            
            phases = ["Target Pressures (psi)", "Cold Pressures (psi)", "Hot Pressures (psi)"]
            for ph in phases:
                for t in ['FL','FR','RL','RR']:
                    col = f"{ph}_{t}"
                    if col in df:
                        line, = ax.plot(x, df[col], label=col, linewidth=2)
                        lines.append(line)
                        labels.append(col)
            
            for attr in ['air1','air2','track1','track2']:
                if attr in df:
                    line, = ax.plot(x, df[attr], label=attr, linewidth=2)
                    lines.append(line)
                    labels.append(attr)
            
            # Configurar eixo x com os nomes das sessões
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            
            ax.set_xlabel('Session Name', fontsize=12)
            ax.set_ylabel('Value', fontsize=12)
            
            # Adicionar legenda abaixo do gráfico em múltiplas linhas
            ax.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15),
                     ncol=4, fontsize=10)
            
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Configurar interatividade
            cursor = mplcursors.cursor(lines, hover=True)
            @cursor.connect("add")
            def on_add(sel):
                x_val = int(sel.target[0])
                y_val = sel.target[1]
                session_name = x_labels[x_val]
                sel.annotation.set_text(f'Session: {session_name}\nValue: {y_val:.2f}')
                sel.annotation.get_bbox_patch().set(fc="black", alpha=0.8)
                sel.annotation.set_color('white')
            
            # Ajustar layout
            figure.tight_layout(pad=2.0)
        else:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=14)
        
        canvas.draw()
        dialog.exec()

    def build_rigidez_tab(self, parent):
        # Criar um widget de conteúdo e layout principal
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(12,12,12,12)
        layout.setSpacing(14)

        # Grupo de inputs
        input_box = QGroupBox("ARBs STIFFNESS DISTRIBUTION CALCULATION")
        input_box.setStyleSheet("""
            QGroupBox {
                border: 2px solid #D40000;
                border-radius: 8px;
                margin-top: 12px;
                background: rgba(0,0,0,0.85);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                background: #D40000;
                color: #fff;
                font: bold 15px 'Porsche';
                border-radius: 4px;
                padding: 4px 16px;
                margin-top: 4px;
            }
        """)
        input_layout = QGridLayout(input_box)
        input_layout.setSpacing(8)
        input_layout.setContentsMargins(10,10,10,10)

        # Dianteira
        input_layout.addWidget(QLabel("ARB (FL)"), 0, 0)
        self.rig_fl = QDoubleSpinBox(); self.rig_fl.setRange(1.0, 7.0); self.rig_fl.setSingleStep(0.5); self.rig_fl.setValue(2.0)
        self.rig_fl.setStyleSheet("font-size: 13px; min-width: 60px; min-height: 24px;")
        input_layout.addWidget(self.rig_fl, 0, 1)
        input_layout.addWidget(QLabel("ARB (FR)"), 0, 2)
        self.rig_fr = QDoubleSpinBox(); self.rig_fr.setRange(1.0, 7.0); self.rig_fr.setSingleStep(0.5); self.rig_fr.setValue(2.0)
        self.rig_fr.setStyleSheet("font-size: 13px; min-width: 60px; min-height: 24px;")
        input_layout.addWidget(self.rig_fr, 0, 3)
        # Traseira
        input_layout.addWidget(QLabel("ARB (RL)"), 1, 0)
        self.rig_rl = QDoubleSpinBox(); self.rig_rl.setRange(1.0, 7.0); self.rig_rl.setSingleStep(0.5); self.rig_rl.setValue(6.0)
        self.rig_rl.setStyleSheet("font-size: 13px; min-width: 60px; min-height: 24px;")
        input_layout.addWidget(self.rig_rl, 1, 1)
        input_layout.addWidget(QLabel("ARB (RR)"), 1, 2)
        self.rig_rr = QDoubleSpinBox(); self.rig_rr.setRange(1.0, 7.0); self.rig_rr.setSingleStep(0.5); self.rig_rr.setValue(6.0)
        self.rig_rr.setStyleSheet("font-size: 13px; min-width: 60px; min-height: 24px;")
        input_layout.addWidget(self.rig_rr, 1, 3)

        # Botão calcular
        btn_calc = QPushButton("CALCULATE STIFFNESS DISTRIBUTION")
        btn_calc.setStyleSheet("""
            QPushButton {
                background: #D40000;
                color: #fff;
                font: bold 15px 'Porsche';
                border-radius: 4px;
                padding: 8px 0;
                min-height: 28px;
                margin-top: 6px;
            }
            QPushButton:hover {
                background: #FF4C4C;
                border: 1px solid #fff;
            }
        """)
        input_layout.addWidget(btn_calc, 2, 0, 1, 4)
        btn_calc.clicked.connect(self.calcular_rigidez_backend)

        # Resultados destacados
        self.result_highlight = QLabel()
        self.result_highlight.setAlignment(Qt.AlignCenter)
        self.result_highlight.setStyleSheet("""
            QLabel {
                background: #D40000;
                color: #fff;
                font: bold 16px 'Porsche';
                border-radius: 6px;
                padding: 10px 0 6px 0;
                margin-top: 10px;
            }
        """)
        input_layout.addWidget(self.result_highlight, 3, 0, 1, 4)

        layout.addWidget(input_box)

        # Grupo de busca de setups
        search_box = QGroupBox("LOCATE SETUPS NEAR DISTRIBUTION TARGET")
        search_box.setStyleSheet("""
            QGroupBox {
                border: 2px solid #D40000;
                border-radius: 8px;
                margin-top: 12px;
                background: rgba(0,0,0,0.85);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                background: #D40000;
                color: #fff;
                font: bold 15px 'Porsche';
                border-radius: 4px;
                padding: 4px 16px;
                margin-top: 4px;
            }
        """)
        search_layout = QGridLayout(search_box)
        search_layout.setSpacing(8)
        search_layout.setContentsMargins(10,10,10,10)
        search_layout.addWidget(QLabel("TARGET DISTRIBUTION (%)"), 0, 0)
        self.target_pct = QDoubleSpinBox(); self.target_pct.setRange(00, 100); self.target_pct.setValue(21); self.target_pct.setSingleStep(0.1)
        self.target_pct.setStyleSheet("font-size: 13px; min-width: 60px; min-height: 24px;")
        search_layout.addWidget(self.target_pct, 0, 1)
        search_layout.addWidget(QLabel("TOLERANCE (%)"), 0, 2)
        self.tol_pct = QDoubleSpinBox(); self.tol_pct.setRange(0.1, 10.0); self.tol_pct.setValue(1.0); self.tol_pct.setSingleStep(0.1)
        self.tol_pct.setStyleSheet("font-size: 13px; min-width: 60px; min-height: 24px;")
        search_layout.addWidget(self.tol_pct, 0, 3)
        btn_search = QPushButton("FIND COMBINATIONS")
        btn_search.setStyleSheet("""
            QPushButton {
                background: #D40000;
                color: #fff;
                font: bold 15px 'Porsche';
                border-radius: 4px;
                padding: 8px 0;
                min-height: 28px;
                margin-top: 6px;
            }
            QPushButton:hover {
                background: #FF4C4C;
                border: 1px solid #fff;
            }
        """)
        search_layout.addWidget(btn_search, 1, 0, 1, 4)
        btn_search.clicked.connect(self.buscar_combinacoes_backend)
        layout.addWidget(search_box)

        # Tabela de resultados
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ARB FRONT", "ARB REAR", "DIST %"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background: #111;
                color: #fff;
                font-size: 12px;
                border: 1.5px solid #D40000;
                border-radius: 6px;
                selection-background-color: #D40000;
                selection-color: #fff;
            }
            QHeaderView::section {
                background: #D40000;
                color: #fff;
                font: bold 12px 'Porsche';
                border: none;
                height: 28px;
            }
        """)
        self.table.verticalHeader().setVisible(True)
        self.table.setMinimumHeight(6 * 28 + 32)  # 6 linhas + header
        self.table.setMaximumHeight(12 * 28 + 32) # até 12 linhas sem rolagem
        layout.addWidget(self.table)

        # Adiciona o heatmap e imagens ao final da aba
        self.add_heatmap_and_images(layout)

        # Adiciona o layout de conteúdo ao scroll area
        scroll = QScrollArea(parent)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)
        parent_layout = QVBoxLayout(parent)
        parent_layout.setContentsMargins(0,0,0,0)
        parent_layout.addWidget(scroll)

    def calcular_rigidez_backend(self):
        try:
            front = [self.rig_fl.value(), self.rig_fr.value()]
            rear = [self.rig_rl.value(), self.rig_rr.value()]
            rig_f, rig_r = rigidez_backend.get_rigidez(front, rear)
            dist = rigidez_backend.get_distribution(front, rear)
            self.result_highlight.setText(f"<span style='font-size:22px;'>STIFFNESS AT FRONT ARB: <b>{rig_f:.2f}</b> N/mm &nbsp;&nbsp;|&nbsp;&nbsp; STIFFNESS AT REAR ARB: <b>{rig_r:.2f}</b> N/mm<br>ARBs STIFFNESS DISTRIBUTION: <b>{dist:.2f}%</b></span>")
        except Exception as e:
            self.result_highlight.setText(f"<span style='color:#fff;font-size:20px;'>Erro: {str(e)}</span>")

    def buscar_combinacoes_backend(self):
        target = self.target_pct.value()
        tol = self.tol_pct.value()
        resultados = rigidez_backend.find_setups(target, tol)
        self.table.setRowCount(len(resultados))
        for i, (pf, pr, pct) in enumerate(resultados):
            item_pf = QTableWidgetItem(f"{pf:.1f}")
            item_pr = QTableWidgetItem(f"{pr:.1f}")
            item_pct = QTableWidgetItem(f"{pct:.2f}%")
            for item in [item_pf, item_pr, item_pct]:
                item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, item_pf)
            self.table.setItem(i, 1, item_pr)
            self.table.setItem(i, 2, item_pct)

    def add_heatmap_and_images(self, parent_layout):
        from PySide6.QtGui import QColor, QPixmap
        from PySide6.QtWidgets import QTableWidgetItem, QLabel, QHBoxLayout, QWidget, QVBoxLayout
        import os
        # Heatmap
        posicoes = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
        table = QTableWidget(len(posicoes), len(posicoes))
        table.setHorizontalHeaderLabels([str(p) for p in posicoes])
        table.setVerticalHeaderLabels([str(p) for p in posicoes])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setStyleSheet("""
            QTableWidget {
                background: #111;
                color: #fff;
                font-size: 12px;
                border: 1.5px solid #D40000;
                border-radius: 6px;
                selection-background-color: #D40000;
                selection-color: #fff;
            }
            QHeaderView::section {
                background: #D40000;
                color: #fff;
                font: bold 12px 'Porsche';
                border: none;
                height: 28px;
            }
        """)
        table.verticalHeader().setVisible(True)
        table.setMinimumHeight(32 + len(posicoes) * 28)
        table.setMaximumHeight(32 + len(posicoes) * 28)

        # Calcular todos os valores e encontrar min/max para normalizar as cores
        values = []
        for i, traseira in enumerate(posicoes):
            for j, dianteira in enumerate(posicoes):
                try:
                    pct = rigidez_backend.get_distribution([dianteira, dianteira], [traseira, traseira])
                except Exception:
                    pct = None
                values.append(pct if pct is not None else 0)
        vmin, vmax = min(values), max(values)
        # Preencher a tabela
        for i, traseira in enumerate(posicoes):
            for j, dianteira in enumerate(posicoes):
                try:
                    pct = rigidez_backend.get_distribution([dianteira, dianteira], [traseira, traseira])
                except Exception:
                    pct = None
                item = QTableWidgetItem(f'{pct:.2f}' if pct is not None else '')
                item.setTextAlignment(Qt.AlignCenter)
                # Colorir: vermelho (baixo) a azul (alto)
                if pct is not None:
                    ratio = (pct - vmin) / (vmax - vmin) if vmax > vmin else 0
                    r = int(255 * (1 - ratio))
                    g = int(255 * (1 - abs(0.5 - ratio) * 2))
                    b = int(255 * ratio)
                    item.setBackground(QColor(r, g, b))
                table.setItem(i, j, item)

        # Imagens
        images_widget = QWidget()
        images_layout = QVBoxLayout(images_widget)
        images_layout.setContentsMargins(0,0,0,0)
        images_layout.setSpacing(0)
        # Caminhos das imagens
        base_dir = os.path.dirname(__file__)
        car_path = os.path.join(base_dir, 'assets', 'images', 'SP21L31IX0002_low-1.png')
        logo_path = os.path.join(base_dir, 'assets', 'images', 'Felipe_Forte_Motorsports-removebg-preview.png')
        # Carro
        car_label = QLabel()
        if os.path.exists(car_path):
            car_pixmap = QPixmap(car_path)
            car_pixmap = car_pixmap.scaledToWidth(400, Qt.SmoothTransformation)
            car_label.setPixmap(car_pixmap)
            car_label.setAlignment(Qt.AlignCenter)
        car_label.setStyleSheet("background: transparent;")
        images_layout.addWidget(car_label)
        # Logo
        logo_label = QLabel()
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_pixmap = logo_pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        images_layout.addWidget(logo_label)
        images_layout.addStretch()

        # Layout horizontal para heatmap + imagens
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        hbox.setSpacing(24)
        # Heatmap ocupa o máximo possível, imagens ficam à direita
        heatmap_container = QWidget()
        heatmap_layout = QVBoxLayout(heatmap_container)
        heatmap_layout.setContentsMargins(0,0,0,0)
        heatmap_layout.setSpacing(0)
        heatmap_layout.addWidget(QLabel("DISTRIBUTION MAP (%)"))
        heatmap_layout.addWidget(table)

        # Adicionar tabela de posições da asa
        wing_table = QTableWidget()
        wing_table.setColumnCount(2)
        wing_table.setHorizontalHeaderLabels(["WING POSITION", "AERO BALANCE IN FRONT AXLE"])
        wing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        wing_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        wing_table.setStyleSheet("""
            QTableWidget {
                background: #111;
                color: #fff;
                font-size: 12px;
                border: 1.5px solid #D40000;
                border-radius: 6px;
                selection-background-color: #D40000;
                selection-color: #fff;
            }
            QHeaderView::section {
                background: #D40000;
                color: #fff;
                font: bold 12px 'Porsche';
                border: none;
                height: 28px;
            }
        """)
        wing_table.verticalHeader().setVisible(False)
        
        # Dados da tabela
        wing_data = [
            ("P14", "-6,0%"),
            ("P13", "-5,3%"),
            ("P12", "-4,6%"),
            ("P11", "-3,9%"),
            ("P10", "-3,2%"),
            ("P9", "-2,4%"),
            ("P8", "-1,6%"),
            ("P7", "-0,8%"),
            ("P6", "0,0%"),
            ("P5", "1,1%"),
            ("P4", "2,3%")
        ]
        
        wing_table.setRowCount(len(wing_data))
        for i, (pos, balance) in enumerate(wing_data):
            item_pos = QTableWidgetItem(pos)
            item_balance = QTableWidgetItem(balance)
            for item in [item_pos, item_balance]:
                item.setTextAlignment(Qt.AlignCenter)
            # Colorir baseado no valor do balance
            balance_value = float(balance.replace('%', '').replace(',', '.'))
            ratio = (balance_value + 6) / 8.3  # Normalizar entre 0 e 1
            r = int(255 * (1 - ratio))
            g = int(255 * (1 - abs(0.5 - ratio) * 2))
            b = int(255 * ratio)
            item_balance.setBackground(QColor(r, g, b))
            wing_table.setItem(i, 0, item_pos)
            wing_table.setItem(i, 1, item_balance)
        
        wing_table.setMinimumHeight(32 + len(wing_data) * 28)
        wing_table.setMaximumHeight(32 + len(wing_data) * 28)

        # Container para a tabela da asa
        wing_container = QWidget()
        wing_layout = QVBoxLayout(wing_container)
        wing_layout.setContentsMargins(0,0,0,0)
        wing_layout.setSpacing(0)
        wing_layout.addWidget(QLabel("WING POSITION MAP"))
        wing_layout.addWidget(wing_table)

        hbox.addWidget(heatmap_container, stretch=3)
        hbox.addWidget(wing_container, stretch=1)
        hbox.addWidget(images_widget, stretch=1)
        parent_layout.addLayout(hbox)

if __name__=='__main__':
    app = QApplication(sys.argv)
    win = TirePressureApp()
    win.show()
    sys.exit(app.exec())
