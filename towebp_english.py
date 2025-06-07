import os
import glob
import apng
from PIL import Image
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QMessageBox, QFrame, QRadioButton, QButtonGroup,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices

def create_webp(output_file, input_folder="input", delay=42, quality=80, lossless=False):
    """
    Create an animated WebP image
    :param output_file: Output file name (e.g., "output.webp")
    :param input_folder: Input folder path (default is "input")
    :param delay: Delay time per frame (in milliseconds), default 42 ms corresponding to 24 FPS
    :param quality: Compression quality (0-100), default 80, only effective in non-lossless mode
    :param lossless: Whether to enable lossless mode, default is False
    """
    print(f"Starting to create WebP: Output file={output_file}, Input folder={input_folder}")
    # Get all PNG files in the input folder
    png_files = sorted(glob.glob(os.path.join(input_folder, "*.png")))

    if not png_files:
        raise FileNotFoundError(f"No PNG files found, please check the {input_folder} folder.")

    # Open the first image and load other frames
    images = []
    for i, png_file in enumerate(png_files):
        img = Image.open(png_file).convert("RGBA")  # Ensure the image is in RGBA format to support transparency
        if i > 0:
            img.info["duration"] = delay
        images.append(img)

    # Prepare save parameters
    save_params = {
        "format": "WEBP",
        "save_all": True,
        "append_images": images[1:],
        "duration": delay,
        "loop": 0,  # 0 means infinite loop
        "lossless": lossless,  # Whether to enable lossless mode
    }

    # Set the quality parameter only in non-lossless mode
    if not lossless:
        save_params["quality"] = quality

    # Save as a WebP animation
    images[0].save(output_file, **save_params)


def create_apng(output_file, input_folder="input", delay=42):
    """
    Create an APNG file
    :param output_file: Output file name (e.g., "output.png")
    :param input_folder: Input folder path (default is "input")
    :param delay: Delay time per frame (in milliseconds), default 42 ms corresponding to 24 FPS
    """
    # Create an APNG object
    apng_obj = apng.APNG()

    # Get all PNG files in the input folder
    png_files = sorted(glob.glob(os.path.join(input_folder, "*.png")))

    if not png_files:
        raise FileNotFoundError(f"No PNG files found, please check the {input_folder} folder.")

    # Add frames
    for png_file in png_files:
        apng_obj.append_file(png_file, delay=int(delay / 10))  # The apng library uses centiseconds
        print(f"Frame added: {png_file}")

    # Save as an APNG file
    apng_obj.save(output_file)
    print(f"APNG file saved as {output_file}")


# Utility function: Show a toast message
def show_toast(parent, message, duration=3000, toast_type="info"):
    if hasattr(parent, 'toast') and parent.toast:
        parent.toast.hide()
    parent.toast = ToastMessage(parent, message, duration, toast_type)
    parent.toast.show()

class ConversionThread(QThread):
    conversion_finished = Signal(bool, str)

    def __init__(self, output_file, input_folder, format_type, delay, quality, lossless):
        super().__init__()
        self.output_file = output_file
        self.input_folder = input_folder
        self.format_type = format_type
        self.delay = delay
        self.quality = quality
        self.lossless = lossless

    def run(self):
        try:
            if self.format_type == "webp":
                create_webp(self.output_file, self.input_folder,
                            delay=self.delay, quality=self.quality, lossless=self.lossless)
            elif self.format_type == "apng":
                create_apng(self.output_file, self.input_folder, delay=self.delay)
            self.conversion_finished.emit(True, "")
        except Exception as e:
            self.conversion_finished.emit(False, str(e))

class ToastMessage(QLabel):
    def __init__(self, parent, message, duration=3000, toast_type="info"):
        super().__init__(message, parent)
        if toast_type == "error":
            # Error toast style
            self.setStyleSheet("""
                background-color: #FF4747;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                height: 40px;
            """)
        elif toast_type == "progress":
            # Progress toast style
            self.setStyleSheet("""
                background-color: #00CB7D;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                height: 40px;
            """)
        elif toast_type == "success":
            # Success toast style
            self.setStyleSheet("""
                background-color: #0069D9;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                height: 40px;
            """)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.adjustSize()
        # Move toast to the top
        self.move((parent.width() - self.width()) // 2, 20)
        self.show()
        QTimer.singleShot(duration, self.hide)

class WebPConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.input_folder = None
        self.toast = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Animated Image Maker")
        self.setGeometry(100, 100, 620, 650)
        # Set the window background color to white
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)

        self.setup_title(main_layout)
        self.setup_file_selection(main_layout)
        self.setup_preview_info(main_layout)
        self.setup_settings(main_layout)
        self.setup_convert_button(main_layout)
        self.setup_copyright_info(main_layout)

        self.setLayout(main_layout)
        self.setAcceptDrops(True)
        self.toggle_format()

    def setup_title(self, layout):
        """Setup the title section"""
        title_layout = QHBoxLayout()
        
        title = QLabel("Animated Image Maker")
        title.setStyleSheet("""font-size: 24px; 
                            font-weight: bold; 
                            color: #000000;
                             background-color: white;
                             margin: 20px 20px 20px 0px;
                            """)
        title_layout.addWidget(title)
        
        # Add donate button
        self.donate_button = QPushButton("Donate")
        self.donate_button.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: white;
                font-size: 14px;
                height: 30px;
                border-radius: 15px;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #202020;
            }
        """)
        self.donate_button.clicked.connect(self.open_donate_url)
        title_layout.addWidget(self.donate_button, alignment=Qt.AlignRight)
        
        layout.addLayout(title_layout)
        
    def open_donate_url(self):
        """Open the PayPal donation URL in the browser"""
        QDesktopServices.openUrl(QUrl("https://paypal.me/xffdgs"))

    def setup_file_selection(self, layout):
        """Setup the file selection area"""
        select_frame = QFrame()
        select_frame.setStyleSheet("background-color: white; margin-left: 0px;")
        select_layout = QHBoxLayout()
        select_layout.setContentsMargins(0, 0, 0, 0)

        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        self.folder_path.setStyleSheet("background-color: #F5F5F5; border: none; height: 60px; border-radius: 12px; padding: 0 20px;")
        select_layout.addWidget(self.folder_path, stretch=3)

        select_button = QPushButton("Select Folder")
        BUTTON_STYLE = """
            QPushButton {
                background-color: #F5F5F5;
                border: none;
                color: #000000;
                height: 60px;
                border-radius: 12px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #DEDEDE;
                border: none;
                color: #000000;
                height: 60px;
                border-radius: 12px;
                padding: 0 20px;
            }
        """
        select_button.setStyleSheet(BUTTON_STYLE)
        select_button.clicked.connect(self.select_folder)

        clear_button = QPushButton("Clear Folder")
        clear_button.setStyleSheet(BUTTON_STYLE)
        clear_button.clicked.connect(self.clear_folder)

        select_layout.addWidget(select_button, stretch=1)
        select_layout.addWidget(clear_button, stretch=1)

        select_frame.setLayout(select_layout)
        layout.addWidget(select_frame)

    def setup_preview_info(self, layout):
        """Setup the preview information section"""
        preview_frame = QFrame()
        preview_frame.setStyleSheet("background-color: white;")
        preview_layout = QHBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # Image preview area
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(120, 120)
        self.image_preview.setStyleSheet("background-color: #F5F5F5; border-radius: 8px;")
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.hide()
        preview_layout.addWidget(self.image_preview)
        
        # Text information area
        text_frame = QFrame()
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_label = QLabel("Drag a folder here")
        self.preview_label.setStyleSheet("""
            background-color: white;
            font-size: 18px;
            color: #000000;
        """)
        text_layout.addWidget(self.preview_label)
        text_frame.setLayout(text_layout)
        preview_layout.addWidget(text_frame)
        
        preview_frame.setLayout(preview_layout)
        layout.addWidget(preview_frame)

    def setup_settings(self, layout):
        """Setup the settings area"""
        settings_frame = QFrame()
        settings_frame.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)

        self.setup_format_and_compression(settings_layout)
        self.setup_output_filename(settings_layout)
        self.setup_quality_and_delay(settings_layout)

        settings_frame.setLayout(settings_layout)
        layout.addWidget(settings_frame)

    def setup_format_and_compression(self, layout):
        """Setup the output format and compression mode selection area"""
        format_and_compression_frame = QFrame()
        self.format_and_compression_layout = QHBoxLayout()
        self.format_and_compression_layout.setContentsMargins(0, 0, 0, 0)
        self.format_and_compression_layout.setSpacing(20)

        # Format selection section
        format_section = QFrame()
        format_section.setStyleSheet("background-color: white;")
        format_section_layout = QVBoxLayout()
        format_section_layout.setContentsMargins(0, 0, 0, 8)

        format_label = QLabel("Output Format")
        format_label.setStyleSheet("background-color: transparent;")
        format_section_layout.addWidget(format_label)

        format_option_frame = QFrame()
        format_option_frame.setStyleSheet("""
            background-color: #F5F5F5;
            height: 60px;
            border-radius: 12px;
            padding: 4px;
        """)
        format_option_layout = QHBoxLayout()
        format_option_layout.setContentsMargins(0, 0, 0, 0)

        self.format_button_group = QButtonGroup()
        radio_button_style = """
            QRadioButton {
                font-size: 16px;
                padding: 0 10px;
                border-radius: 10px;
                margin: 0 2px;
            }
            QRadioButton::indicator {
                width: 0px;
                height: 0px;
                border: none;
            }
            QRadioButton:checked {
                background-color: white;
                color: black;
                font-weight: bold;
            }
            QRadioButton:!checked {
                background-color: transparent;
                color: #555555;
            }
        """
        webp_radio = QRadioButton("WebP")
        webp_radio.setStyleSheet(radio_button_style)
        apng_radio = QRadioButton("APNG")
        apng_radio.setStyleSheet(radio_button_style)
        self.format_button_group.addButton(webp_radio)
        self.format_button_group.addButton(apng_radio)
        webp_radio.setChecked(True)
        format_option_layout.addWidget(webp_radio)
        format_option_layout.addWidget(apng_radio)
        format_option_frame.setLayout(format_option_layout)
        format_section_layout.addWidget(format_option_frame)
        format_section.setLayout(format_section_layout)

        # Compression mode selection section
        self.compression_section = QFrame()
        self.compression_section.setStyleSheet("background-color: white;")
        compression_section_layout = QVBoxLayout()
        compression_section_layout.setContentsMargins(0, 0, 0, 8)

        compression_label = QLabel("Compression")
        compression_label.setStyleSheet("background-color: transparent;")
        compression_section_layout.addWidget(compression_label)

        compression_option_frame = QFrame()
        compression_option_frame.setStyleSheet("""
            background-color: #F5F5F5;
            height: 60px;
            border-radius: 12px;
            padding: 4px;
        """)
        compression_option_layout = QHBoxLayout()
        compression_option_layout.setContentsMargins(0, 0, 0, 0)

        self.compression_button_group = QButtonGroup()
        lossy_radio = QRadioButton("Lossy Mode")
        lossy_radio.setStyleSheet(radio_button_style)
        lossless_radio = QRadioButton("Lossless Mode")
        lossless_radio.setStyleSheet(radio_button_style)
        self.compression_button_group.addButton(lossy_radio)
        self.compression_button_group.addButton(lossless_radio)
        lossy_radio.setChecked(True)
        compression_option_layout.addWidget(lossy_radio)
        compression_option_layout.addWidget(lossless_radio)
        compression_option_frame.setLayout(compression_option_layout)
        compression_section_layout.addWidget(compression_option_frame)
        self.compression_section.setLayout(compression_section_layout)

        # Add format selection and compression mode to the horizontal layout
        self.format_and_compression_layout.addWidget(format_section)
        self.format_and_compression_layout.addWidget(self.compression_section)
        format_and_compression_frame.setLayout(self.format_and_compression_layout)
        layout.addWidget(format_and_compression_frame)

    def setup_output_filename(self, layout):
        """Setup the output filename section"""
        output_label = QLabel("Output Filename")
        output_label.setStyleSheet("background-color: white;")
        layout.addWidget(output_label)
        self.output_entry = QLineEdit("output.webp")
        input_box_style = (
        "background-color: #F5F5F5;"
        "border: none;"
        "height: 60px;"
        "border-radius: 12px;"
        "padding: 0 20px;"
        "margin-bottom: 8px;"
        )
        self.output_entry.setStyleSheet(input_box_style)
        layout.addWidget(self.output_entry)

    def setup_quality_and_delay(self, layout):
        """Setup the quality and delay time section"""

        input_box_style = (
        "background-color: #F5F5F5;"
        "border: none;"
        "height: 60px;"
        "border-radius: 12px;"
        "padding: 0 20px;"
        "margin-bottom: 8px;"
        )
        quality_and_delay_frame = QFrame()
        quality_and_delay_frame.setStyleSheet("background-color: white; padding: 0 0;")
        self.quality_and_delay_layout = QHBoxLayout()
        self.quality_and_delay_layout.setContentsMargins(0, 0, 0, 0)
        self.quality_and_delay_layout.setSpacing(20)

        # Quality settings area
        self.quality_frame = QFrame()
        self.quality_frame.setStyleSheet("background-color: white;")
        quality_layout = QVBoxLayout()
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_label = QLabel("Image Quality")
        quality_label.setStyleSheet("background-color: white;")
        quality_layout.addWidget(quality_label)

        self.quality_entry = QLineEdit()
        self.quality_entry.setStyleSheet(input_box_style)
        self.quality_entry.setText("90")  # Set initial value
        quality_layout.addWidget(self.quality_entry)
        self.quality_frame.setLayout(quality_layout)
        
        self.quality_and_delay_layout.addWidget(self.quality_frame)

        # Delay time settings
        delay_label = QLabel("Frame Delay")
        delay_label.setStyleSheet("background-color: white;")
        self.delay_entry = QLineEdit("24")
        self.delay_entry.setStyleSheet(input_box_style)

        delay_layout = QVBoxLayout()
        delay_layout.setContentsMargins(0, 0, 0, 0)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_entry)
        self.delay_frame = QFrame()
        
        self.delay_frame.setStyleSheet("background-color: white;")
        
        self.delay_frame.setLayout(delay_layout)
        self.quality_and_delay_layout.addWidget(self.delay_frame)

        quality_and_delay_frame.setLayout(self.quality_and_delay_layout)
        layout.addWidget(quality_and_delay_frame)

    def setup_convert_button(self, layout):
        """Setup the convert button section"""
        convert_button = QPushButton("Convert")
        convert_button.setStyleSheet("""
        QPushButton {
            background-color: #000000;
            color: white;
            font-size: 16px;
            font-weight: bold;
            height: 60px;
            border-radius: 12px;
            width: 100%;
        }
        QPushButton:hover {
            background-color: #202020;
            color: white;
            font-size: 16px;
            font-weight: bold;
            height: 60px;
            border-radius: 12px;
            width: 100%;
        }
    """)
        convert_button.clicked.connect(self.convert_images)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.addWidget(convert_button)
        layout.addLayout(button_layout)

    def setup_copyright_info(self, layout):
        """Setup the copyright information section"""
        copyright_label = QLabel("Copyright © 2024 Your Name. All rights reserved.")
        copyright_label.setStyleSheet("font-size: 9px; color: #95a5a6; background-color: white;")
        layout.addWidget(copyright_label, alignment=Qt.AlignBottom | Qt.AlignHCenter)
        # Add event handling
        webp_radio = self.format_button_group.buttons()[0]
        apng_radio = self.format_button_group.buttons()[1]
        lossy_radio = self.compression_button_group.buttons()[0]
        lossless_radio = self.compression_button_group.buttons()[1]
        webp_radio.toggled.connect(self.toggle_format)
        apng_radio.toggled.connect(self.toggle_format)
        lossy_radio.toggled.connect(self.toggle_compression)
        lossless_radio.toggled.connect(self.toggle_compression)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.input_folder = path
                self.folder_path.setText(path)
                png_files = sorted(glob.glob(os.path.join(path, "*.png")))
                png_count = len(png_files)
                self.preview_label.setText(f"Folder: {os.path.basename(path)}\n"                                           f"Found {png_count} PNG files")
                
                if png_files:
                    # Load the first image
                    pixmap = QPixmap(png_files[0])
                    pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_preview.setPixmap(pixmap)
                    self.image_preview.show()
                else:
                    self.image_preview.hide()
            else:
                QMessageBox.critical(self, "Error", "Please drag and drop a folder, not a file")
            break

    def select_folder(self):
        folder_selected = QFileDialog.getExistingDirectory(self, "Select folder containing PNG files")
        if folder_selected:
            self.input_folder = folder_selected
            self.folder_path.setText(folder_selected)
            png_files = sorted(glob.glob(os.path.join(folder_selected, "*.png")))
            png_count = len(png_files)
            self.preview_label.setText(f"Folder: {os.path.basename(folder_selected)}\n"                                       f"Found {png_count} PNG files")
            
            if png_files:
                # Load the first image
                pixmap = QPixmap(png_files[0])
                pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_preview.setPixmap(pixmap)
                self.image_preview.show()
            else:
                self.image_preview.hide()

    def clear_folder(self):
        self.input_folder = None
        self.folder_path.setText("")
        self.preview_label.setText("No folder selected")
        self.image_preview.clear()  # Clear the image preview
        self.image_preview.hide()  # Hide the image preview area

    def toggle_compression(self):
        if self.compression_button_group.checkedButton().text() == "Lossy Mode":
            self.quality_frame.show()
            # Restore the size policy of the frame rate area
            self.delay_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            self.quality_frame.hide()
            # When the quality area is hidden, let the frame rate area fill the row
            self.delay_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Adjust the layout
        self.layout().update()

    def toggle_format(self):
        if self.format_button_group.checkedButton().text() == "WebP":
            self.quality_frame.show()
            self.compression_section.show()
            # Set the ratio of the format and compression areas to 2:1
            self.format_and_compression_layout.setStretch(0, 1)  # Format section
            self.format_and_compression_layout.setStretch(1, 1)  # Compression section
            # Set the ratio of the quality and delay areas to 1:1
            self.quality_and_delay_layout.setStretch(0, 1)  # Quality section
            self.quality_and_delay_layout.setStretch(1, 1)  # Delay section
            
            self.output_entry.setText("output.webp")
        else:
            self.quality_frame.hide()
            self.compression_section.hide()
            # When the compression module is hidden, let the frame rate area fill the row
            self.delay_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.output_entry.setText("output.png")
        self.layout().update()

    def convert_images(self):
        if not self.input_folder:
            show_toast(self, "Please select a folder containing PNG files first", toast_type="error")
            return

        output_file = self.output_entry.text().strip()
        format_type = "webp" if self.format_button_group.checkedButton().text() == "WebP" else "apng"

        try:
            fps = int(self.delay_entry.text())  # Get the input frame rate
            if fps <= 0:
                raise ValueError
            delay = int(1000 / fps)  # Convert frame rate to frame delay time (milliseconds)
        except ValueError:
            show_toast(self, "Frame rate must be a positive integer", toast_type="error")
            return

        if format_type == "webp" and not output_file.endswith(".webp"):
            show_toast(self, "Output file name must end with .webp", toast_type="error")
            return
        elif format_type == "apng" and not output_file.endswith(".png"):
            show_toast(self, "Output file name must end with .png", toast_type="error")
            return

        lossless = self.compression_button_group.checkedButton().text() == "Lossless Mode"

        if not lossless:
            try:
                quality = int(self.quality_entry.text())  # Get the quality value from the input box
                if quality < 0 or quality > 100:
                    raise ValueError
            except ValueError:
                show_toast(self, "Image quality must be an integer between 0 and 100", toast_type="error")
                return
        else:
            quality = 100  # Set quality to 100 in lossless mode

        # Show a toast indicating conversion in progress
        show_toast(self, "Converting...", duration=0, toast_type="progress")

        # Create a ConversionThread instance
        self.thread = ConversionThread(output_file, self.input_folder, format_type, delay, quality, lossless)

        self.thread.conversion_finished.connect(lambda success, error: self.conversion_finished(success, error))
        self.thread.start()

    def conversion_finished(self, success, error):
        if success:
            output_file = self.output_entry.text().strip()
            format_type = "webp" if self.format_button_group.checkedButton().text() == "WebP" else "apng"
            show_toast(self, f"{format_type.upper()} animation saved as {output_file}", toast_type="success")
        else:
            show_toast(self, f"Conversion failed: {error}", toast_type="error")

if __name__ == "__main__":
    app = QApplication([])
    window = WebPConverterApp()
    window.show()
    app.exec()    