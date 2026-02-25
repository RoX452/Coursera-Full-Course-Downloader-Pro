__version__ = "3.1.0"

import sys
import logging
from threading import Thread
from os import path

# PyQt5 Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QRadioButton,
    QComboBox, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QAction, QGroupBox, QTextEdit, QDialog, QListWidget, QListWidgetItem, 
    QDialogButtonBox, QProgressBar, QSizePolicy, QMenu, QLayout
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QThread

# Imports locales (asumiendo que tienes estos archivos/librerías)
try:
    from utils import process_notification_html
    import general
    from coursera_dl import main_f
    from localdb import SimpleDB
except ImportError:
    # Fallback para pruebas si faltan archivos
    class MockGeneral:
        LANG_NAME_TO_CODE_MAPPING = {'English': 'en', 'Spanish': 'es'}
        ALLOWED_BROWSERS = ['chrome', 'firefox', 'edge']
        def loadcauth(self, a, b): return "cookie"
        def urltoclassname(self, url): return "python-course"
        def move_to_first(self, d, k): return d
    general = MockGeneral()
    
    class MockDB:
        def __init__(self, f): self.d = {'argdict': {'classname': '', 'path': '', 'video_resolution': '720p', 'sl': 'en'}, 'language': 'en', 'browser': 'chrome'}
        def get_full_db(self): return self.d
        def read(self, k): 
            if k == 'argdict': return self.d['argdict']
            return self.d.get(k, '')
        def update(self, k, v): pass
    SimpleDB = MockDB
    main_f = lambda x: print("Simulando descarga...")


# --- DICCIONARIO DE TRADUCCIONES ---
TRANSLATIONS = {
    "en": {
        "menu": "Menu", "about": "About", "help": "Help", "language": "Language",
        "login_msg": "<b>You must be logged in on coursera.org in your browser.</b>",
        "auth_source": "Authentication Source", "select_browser": "Select browser:",
        "course_details": "Course Details", "url_slug": "Course URL / Slug:",
        "save_to": "Save to:", "browse": "Browse...", "resolution": "Resolution:",
        "subtitles": "Subtitles:", "select_langs": "Select Languages...",
        "resume": "Resume Download", "start": "Start Download", "downloading": "Downloading...",
        "show_logs": "Show Details / Logs ▼", "hide_logs": "Hide Details / Logs ▲",
        "ready": "Ready to download", "finished": "Download process finished.",
        "error_auth_title": "Authentication Error",
        "error_auth_body": "Could not load cookies from {browser}.\n\n1. Make sure you are logged in on coursera.org.\n2. Try running this app as Administrator.\n3. Try a different browser (Firefox/Chrome usually work best).",
        "error_path": "Please select a download folder first.", "error_url": "Invalid Course URL or Name.",
        "status_finished_title": "Status", "status_finished_body": "Download process finished.\nCheck the logs for details.",
        "about_title": "About", "about_body": "<h3>Coursera Downloader Pro</h3><p>Created by <b>Rockii</b></p><p>This is an Open Source project.</p><p>Clean, fast, and secure.</p>",
        "help_title": "Help", "help_body": "<h3>How to use:</h3><ol><li>Login to Coursera in your browser.</li><li>Select the browser you used in the app.</li><li>Paste the Course URL.</li><li>Select download folder.</li><li>Click Start Download.</li></ol>",
        "lang_select_title": "Select Subtitle Languages", "lang_select_info": "Select one or more languages:"
    },
    "es": {
        "menu": "Menú", "about": "Acerca de", "help": "Ayuda", "language": "Idioma",
        "login_msg": "<b>Debes haber iniciado sesión en coursera.org en tu navegador.</b>",
        "auth_source": "Fuente de Autenticación", "select_browser": "Seleccionar navegador:",
        "course_details": "Detalles del Curso", "url_slug": "URL del Curso / Slug:",
        "save_to": "Guardar en:", "browse": "Explorar...", "resolution": "Resolución:",
        "subtitles": "Subtítulos:", "select_langs": "Seleccionar Idiomas...",
        "resume": "Reanudar Descarga", "start": "Iniciar Descarga", "downloading": "Descargando...",
        "show_logs": "Mostrar Detalles / Logs ▼", "hide_logs": "Ocultar Detalles / Logs ▲",
        "ready": "Listo para descargar", "finished": "Proceso de descarga finalizado.",
        "error_auth_title": "Error de Autenticación",
        "error_auth_body": "No se pudieron cargar las cookies de {browser}.\n\n1. Asegúrate de haber iniciado sesión en coursera.org.\n2. Intenta ejecutar esta aplicación como Administrador.\n3. Prueba con otro navegador (Firefox/Chrome suelen funcionar mejor).",
        "error_path": "Por favor selecciona una carpeta de descarga primero.", "error_url": "URL o Nombre del curso inválido.",
        "status_finished_title": "Estado", "status_finished_body": "Proceso de descarga finalizado.\nRevisa los logs para más detalles.",
        "about_title": "Acerca de", "about_body": "<h3>Coursera Downloader Pro</h3><p>Creado por <b>Rockii</b></p><p>Este es un proyecto de Código Abierto.</p><p>Limpio, rápido y seguro.</p>",
        "help_title": "Ayuda", "help_body": "<h3>Cómo usar:</h3><ol><li>Inicia sesión en Coursera en tu navegador.</li><li>Selecciona el navegador que usaste en la app.</li><li>Pega la URL del curso.</li><li>Selecciona la carpeta de descarga.</li><li>Haz clic en Iniciar Descarga.</li></ol>",
        "lang_select_title": "Seleccionar Idiomas de Subtítulos", "lang_select_info": "Selecciona uno o más idiomas:"
    }
}

# --- ESTILO MODO CLARO PROFESIONAL ---
LIGHT_THEME = """
    QMainWindow, QWidget { 
        background-color: #ffffff; 
        color: #000000; 
        font-family: "Segoe UI", sans-serif;
        font-size: 10pt;
    }
    QMenuBar { background-color: #f5f5f5; color: #000000; border-bottom: 1px solid #dcdcdc; }
    QMenuBar::item { background-color: transparent; padding: 8px 12px; color: #000000; }
    QMenuBar::item:selected { background-color: #e0e0e0; }
    QMenu { background-color: #ffffff; border: 1px solid #dcdcdc; }
    QMenu::item { padding: 6px 24px; color: #000000; }
    QMenu::item:selected { background-color: #0078d7; color: #ffffff; }
    QGroupBox { font-weight: bold; border: 1px solid #dcdcdc; border-radius: 6px; margin-top: 20px; padding-top: 15px; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; color: #0078d7; }
    QLineEdit, QComboBox { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; padding: 6px; border-radius: 4px; }
    QLineEdit:focus, QComboBox:focus { border: 1px solid #0078d7; }
    QPushButton { background-color: #0078d7; color: #ffffff; border: none; padding: 8px 16px; font-weight: bold; border-radius: 4px; }
    QPushButton:hover { background-color: #0063b1; }
    QPushButton:pressed { background-color: #004f8b; }
    QPushButton:disabled { background-color: #cccccc; color: #666666; }
    QTextEdit { background-color: #f9f9f9; color: #000000; font-family: Consolas, Monospace; border: 1px solid #dcdcdc; }
    QProgressBar { border: 1px solid #dcdcdc; border-radius: 4px; text-align: center; background-color: #f0f0f0; }
    QProgressBar::chunk { background-color: #0078d7; width: 10px; }
    QMessageBox { background-color: #ffffff; }
    QMessageBox QLabel { color: #000000; }
"""

# --- DIÁLOGO SELECCIÓN IDIOMAS ---
class LanguageSelector(QDialog):
    def __init__(self, languages, current_selection, title_text, info_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title_text)
        self.resize(300, 400)
        layout = QVBoxLayout(self)
        
        info = QLabel(info_text)
        layout.addWidget(info)

        self.list_widget = QListWidget()
        self.languages = languages 
        selected_codes = [c.strip() for c in current_selection.split(',')]

        for name in sorted(self.languages.keys()):
            code = self.languages[name]
            if code == '': continue 
            item = QListWidgetItem(f"{name} ({code})")
            item.setData(Qt.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if code in selected_codes or (code == 'en' and not selected_codes):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)
            
        layout.addWidget(self.list_widget)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
    def get_selected_codes(self):
        codes = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                codes.append(item.data(Qt.UserRole))
        return ",".join(codes)

# --- CLASES AUXILIARES PARA LOGS Y HILOS ---
class LogHandler(logging.Handler):
    def __init__(self, log_signal, progress_signal):
        super().__init__()
        self.log_signal = log_signal
        self.progress_signal = progress_signal

    def emit(self, record):
        msg = self.format(record)
        if "PROGRESS_BAR:" in msg:
            try:
                percent = int(msg.split("PROGRESS_BAR:")[1].strip())
                self.progress_signal.emit(percent)
            except: pass
        else:
            self.log_signal.emit(msg)

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        handler = LogHandler(self.log_signal, self.progress_signal)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        
        try:
            main_f(self.cmd)
        except SystemExit: pass
        except Exception as e:
            self.log_signal.emit(f"CRITICAL ERROR: {str(e)}")
        finally:
            root_logger.removeHandler(handler)
            self.finished_signal.emit()

# --- CLASE PRINCIPAL ---
class MainWindow(QMainWindow):
    append_log_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coursera Downloader Pro")
        
        # --- CORRECCIÓN IMPORTANTE AQUÍ ---
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)        
        # ANTES: self.setFixedWidth(650)  <-- ESTO ERA EL PROBLEMA
        # AHORA: Lo eliminamos para que la ventana pueda ser más angosta.
        
        if path.exists('course.png'):
            icon_path = path.abspath(path.join(path.dirname(__file__), 'course.png'))
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(LIGHT_THEME)

        self.shouldResume = False
        self.sllangschoices = general.LANG_NAME_TO_CODE_MAPPING
        self.allowed_browsers = general.ALLOWED_BROWSERS

        self.localdb  = SimpleDB('data.bin')
        self.argdict = self.localdb.get_full_db()['argdict']
        
        self.current_lang = self.localdb.read('language')
        if not self.current_lang or self.current_lang not in TRANSLATIONS:
            self.current_lang = 'en'

        self.initUI()
        self.retranslateUi()

        self.append_log_signal.connect(self.append_log_text)
        self.update_progress_signal.connect(self.update_progress_bar)

    def t(self, key):
        return TRANSLATIONS[self.current_lang].get(key, key)

    def initUI(self):
        # --- MENU ---
        menubar = self.menuBar()
        self.menu_main = menubar.addMenu("Menu")
        self.menu_lang = self.menu_main.addMenu("Language")
        
        action_en = QAction("English", self)
        action_en.triggered.connect(lambda checked: self.change_language('en'))
        self.menu_lang.addAction(action_en)
        
        action_es = QAction("Español", self)
        action_es.triggered.connect(lambda checked: self.change_language('es'))
        self.menu_lang.addAction(action_es)

        self.action_about = QAction("About", self)
        self.action_about.triggered.connect(self.show_about)
        self.menu_main.addAction(self.action_about)
        
        self.action_help = QAction("Help", self)
        self.action_help.triggered.connect(self.show_help)
        self.menu_main.addAction(self.action_help)

        # --- WIDGET CENTRAL ---
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout()
        # Esta línea asegura que la ventana se ajuste EXACTAMENTE al contenido (alto y ancho)
        layout.setSizeConstraint(QLayout.SetFixedSize) 
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        central.setLayout(layout)

        # Info Login
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(self.info_label)

        # Browser
        self.browser_group = QGroupBox()
        self.browser_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        browser_layout = QHBoxLayout()
        self.browser_group.setLayout(browser_layout)
        self.browser_label = QLabel()
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(self.allowed_browsers)
        default_browser = self.localdb.read('browser')
        if default_browser in self.allowed_browsers:
            self.browser_combo.setCurrentText(default_browser)
        browser_layout.addWidget(self.browser_label)
        browser_layout.addWidget(self.browser_combo)
        layout.addWidget(self.browser_group)

        # Course Details Group
        self.grid_group = QGroupBox()
        self.grid_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        grid_layout = QVBoxLayout()
        self.grid_group.setLayout(grid_layout)
        
        # --- GRID LAYOUT ---
        grid = QGridLayout()
        grid.setSpacing(10)
        # ANTES: grid.setColumnStretch(1, 1) <-- ELIMINADO
        # AHORA: Sin stretch, porque queremos que la ventana se encoja.
        grid_layout.addLayout(grid)

        # Fila 0: URL
        self.label_url = QLabel()
        grid.addWidget(self.label_url, 0, 0)
        self.classname_edit = QLineEdit(self.localdb.read('argdict')['classname'])
        self.classname_edit.setPlaceholderText("e.g., https://www.coursera.org/learn/python")
        grid.addWidget(self.classname_edit, 0, 1)

        # Fila 1: Path
        self.label_path = QLabel()
        grid.addWidget(self.label_path, 1, 0)
        path_layout = QHBoxLayout()
        self.path_label = QLineEdit(self.localdb.read('argdict')['path'])
        self.path_label.setReadOnly(True)
        self.path_btn = QPushButton()
        self.path_btn.setFixedWidth(100)
        self.path_btn.clicked.connect(self.getPath)
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_btn)
        grid.addLayout(path_layout, 1, 1)

        # Fila 2: Resolution
        self.label_res = QLabel()
        grid.addWidget(self.label_res, 2, 0)
        res_layout = QHBoxLayout()
        self.res_720 = QRadioButton("720p (HD)")
        self.res_540 = QRadioButton("540p")
        self.res_360 = QRadioButton("360p")
        res_layout.addWidget(self.res_720)
        res_layout.addWidget(self.res_540)
        res_layout.addWidget(self.res_360)
        grid.addLayout(res_layout, 2, 1)
        
        saved_res = self.localdb.read('argdict')['video_resolution']
        if saved_res == '540p': self.res_540.setChecked(True)
        elif saved_res == '360p': self.res_360.setChecked(True)
        else: self.res_720.setChecked(True)

        # Fila 3: Subtitles
        self.label_sub = QLabel()
        grid.addWidget(self.label_sub, 3, 0)
        sub_layout = QHBoxLayout()
        saved_sl = self.localdb.read('argdict')['sl']
        if not saved_sl: saved_sl = "en"
        self.sl_display = QLineEdit(saved_sl)
        self.sl_display.setReadOnly(True)
        self.sl_display.setPlaceholderText("en")
        self.sl_btn = QPushButton()
        self.sl_btn.clicked.connect(self.open_language_selector)
        sub_layout.addWidget(self.sl_display)
        sub_layout.addWidget(self.sl_btn)
        grid.addLayout(sub_layout, 3, 1)
        
        layout.addWidget(self.grid_group)

        # --- SECCIÓN DE PROGRESO Y LOGS ---
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        self.progress_label.setAlignment(Qt.AlignCenter)
        
        # "Ignored" le dice a la ventana: "No cambies mi tamaño aunque el texto sea kilométrico".
        self.progress_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed) 
        layout.addWidget(self.progress_label)

        self.progressBar = QProgressBar()            
        self.progressBar.setRange(0, 100)           
        self.progressBar.setValue(0)             
        self.progressBar.setVisible(False)           
        layout.addWidget(self.progressBar)           
        # ---------------------------------------------------------
        self.toggle_log_btn = QPushButton()
        self.toggle_log_btn.setCheckable(True)

        self.toggle_log_btn.setStyleSheet("background-color: #e0e0e0; color: black; text-align: left;")
        self.toggle_log_btn.clicked.connect(self.toggle_logs)
        layout.addWidget(self.toggle_log_btn)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setVisible(False) 
        self.log_viewer.setMinimumHeight(200)
        layout.addWidget(self.log_viewer)

        # Botones de acción
        btn_layout = QHBoxLayout()
        self.resume_btn = QPushButton()
        self.resume_btn.clicked.connect(self.resumeBtnHandler)
        btn_layout.addWidget(self.resume_btn)

        self.download_btn = QPushButton()
        self.download_btn.clicked.connect(self.downloadBtnHandler)
        self.download_btn.setStyleSheet("background-color: #2E7D32; color: white; font-size: 11pt; padding: 10px;") 
        btn_layout.addWidget(self.download_btn)
        layout.addLayout(btn_layout)

    def change_language(self, lang):
        self.current_lang = lang
        self.localdb.update('language', lang)
        self.retranslateUi()

    def retranslateUi(self):
        self.menu_main.setTitle(self.t("menu"))
        self.menu_lang.setTitle(self.t("language"))
        self.action_about.setText(self.t("about"))
        self.action_help.setText(self.t("help"))
        
        self.info_label.setText(self.t("login_msg"))
        self.browser_group.setTitle(self.t("auth_source"))
        self.browser_label.setText(self.t("select_browser"))
        self.grid_group.setTitle(self.t("course_details"))
        self.label_url.setText(self.t("url_slug"))
        self.label_path.setText(self.t("save_to"))
        self.path_btn.setText(self.t("browse"))
        self.label_res.setText(self.t("resolution"))
        self.label_sub.setText(self.t("subtitles"))
        self.sl_btn.setText(self.t("select_langs"))
        self.resume_btn.setText(self.t("resume"))
        self.download_btn.setText(self.t("start"))
        
        if self.toggle_log_btn.isChecked():
            self.toggle_log_btn.setText(self.t("hide_logs"))
        else:
            self.toggle_log_btn.setText(self.t("show_logs"))
            
        if not self.progressBar.isVisible():
            self.progress_label.setText(self.t("ready"))

    def toggle_logs(self):
        if self.toggle_log_btn.isChecked():
            self.log_viewer.setVisible(True)
            self.toggle_log_btn.setText(self.t("hide_logs"))
        else:
            self.log_viewer.setVisible(False)
            self.toggle_log_btn.setText(self.t("show_logs"))
        
        QApplication.processEvents()
        self.adjustSize()

    def open_language_selector(self):
        current_selection = self.sl_display.text()
        dialog = LanguageSelector(
            self.sllangschoices, 
            current_selection, 
            self.t("lang_select_title"),
            self.t("lang_select_info"),
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            new_selection = dialog.get_selected_codes()
            if not new_selection: new_selection = "en"
            self.sl_display.setText(new_selection)

    def append_log_text(self, text):
            # Fíjate que esto está alineado normal, con 4 espacios o 1 tab
            self.log_viewer.append(text)
            sb = self.log_viewer.verticalScrollBar()
            sb.setValue(sb.maximum())
            
            # Lógica mejorada para detectar qué se está descargando
            if "DOWNLOADING_FILE:" in text:
                # Limpiamos el texto para mostrar solo el nombre limpio
                filename = text.split("DOWNLOADING_FILE:")[1].strip()
                # Usamos QFontMetrics para acortar el texto visualmente
                metrics = self.progress_label.fontMetrics()
                elided_text = metrics.elidedText(f"Descargando: {filename}", Qt.ElideMiddle, self.progress_label.width() - 20)
                self.progress_label.setText(elided_text)
                
            elif "Downloading" in text and "->" in text:
                # Fallback por si acaso
                self.progress_label.setText("Iniciando descarga...")

    def update_progress_bar(self, percent):
        self.progressBar.setValue(percent)

    def downloadBtnHandler(self):
        self.progress_label.setVisible(True)
        self.progressBar.setVisible(True)
        self.progress_label.setText(self.t("downloading"))
        
        browser = self.browser_combo.currentText()
        try:
            cauth = general.loadcauth('coursera.org', browser)
        except Exception:
            cauth = ""
            
        if cauth == "":
            msg = self.t("error_auth_body").format(browser=browser)
            self.log_viewer.append(f"ERROR: {msg}")
            QMessageBox.warning(self, self.t("error_auth_title"), msg)
            return
        
        self.localdb.update('argdict.ca', cauth)
        self.localdb.update('browser', browser)
        self.localdb.update('argdict.classname', self.classname_edit.text())
        self.localdb.update('argdict.path', self.path_label.text())
        
        if self.res_720.isChecked(): res = '720p'
        elif self.res_540.isChecked(): res = '540p'
        else: res = '360p'
        self.localdb.update('argdict.video_resolution', res)
        self.localdb.update('argdict.sl', self.sl_display.text())

        if self.localdb.read('argdict')['path'] == '':
            QMessageBox.warning(self, "Error", self.t("error_path"))
            return

        self.argdict = {}
        full_db = self.localdb.get_full_db()['argdict']
        
        courseurl = full_db['classname']
        cname = general.urltoclassname(courseurl)
        if cname == "":
            QMessageBox.warning(self, "Error", self.t("error_url"))
            return
        
        for key, value in full_db.items():
            if key == 'classname':
                self.argdict[key] = cname
            else:
                self.argdict[key] = value

        self.localdb.update('argdict', self.argdict)

        cmd = []
        self.argdict = general.move_to_first(self.argdict, 'ca')
        
        for item in self.argdict.items():
            flag = '--' + item[0] if item[0] in ['video_resolution', 'path'] else '-' + item[0]
            flag = flag.replace('_', '-')
            if 'classname' not in flag:
                cmd.append(flag)
            cmd.append(item[1])

        cmd.extend([
            '--download-quizzes', '--download-notebooks', '--disable-url-skipping', 
            '--unrestricted-filenames', '--combined-section-lectures-nums', '--jobs', '1'
        ])

        if self.shouldResume:
            cmd.extend(["--resume", "--cache-syllabus"])

        self.log_viewer.clear()
        self.progressBar.setValue(0)
        self.log_viewer.append(f">>> STARTING DOWNLOAD FOR: {cname}")
        self.log_viewer.append(">>> PLEASE WAIT, PARSING SYLLABUS CAN TAKE A MINUTE...")
        self.log_viewer.append("-" * 50)

        self.download_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.download_btn.setText(self.t("downloading"))
        
        if not self.toggle_log_btn.isChecked():
            self.log_viewer.setVisible(False)
            self.adjustSize()

        self.worker = DownloadWorker(cmd)
        self.worker.log_signal.connect(self.append_log_signal)
        self.worker.progress_signal.connect(self.update_progress_signal)
        self.worker.finished_signal.connect(self.on_download_finished)
        self.worker.start()

    def on_download_finished(self):
        self.download_btn.setEnabled(True)
        self.resume_btn.setEnabled(True)
        self.download_btn.setText(self.t("start"))
        self.progress_label.setText(self.t("finished"))
        self.progressBar.setValue(100)
        self.log_viewer.append("-" * 50)
        self.log_viewer.append(">>> PROCESS FINISHED.")
        QMessageBox.information(self, self.t("status_finished_title"), self.t("status_finished_body"))

    def resumeBtnHandler(self):
        self.shouldResume = True
        self.downloadBtnHandler()
        self.shouldResume = False

    def getPath(self):
        dir = QFileDialog.getExistingDirectory(self, "Select Download Folder", "")
        if dir:
            self.path_label.setText(dir)

    def show_about(self):
        QMessageBox.about(self, self.t("about_title"), self.t("about_body"))

    def show_help(self):
        QMessageBox.about(self, self.t("help_title"), self.t("help_body"))

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())