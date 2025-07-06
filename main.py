import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QComboBox, QLineEdit, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processor")
        self.setGeometry(100, 100, 800, 600)
        
        # Основные переменные
        self.image = None
        self.current_display = None
        
        # Создание интерфейса
        self.setup_ui()
        
    def setup_ui(self):
        # Виджет для отображения изображения
        self.image_label = QLabel("Image will appear here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        self.image_label.setMinimumSize(600, 400)
        
        # Кнопки загрузки
        self.btn_load = QPushButton("Load Image")
        self.btn_camera = QPushButton("Take Photo")
        
        # Выбор цветового канала
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Red", "Green", "Blue"])
        
        # Функции по варианту
        self.threshold_input = QLineEdit()
        self.threshold_input.setPlaceholderText("Red threshold (0-255)")
        self.btn_red_mask = QPushButton("Apply Red Mask")
        
        self.btn_sharpen = QPushButton("Sharpen Image")
        
        # Исправлено: placeholderText вместо placeholder_text
        self.rect_inputs = [
            QLineEdit(placeholderText="X1"),
            QLineEdit(placeholderText="Y1"),
            QLineEdit(placeholderText="X2"),
            QLineEdit(placeholderText="Y2")
        ]
        self.btn_draw_rect = QPushButton("Draw Rectangle")
        
        # Расположение элементов
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        
        # Панель загрузки
        load_layout = QHBoxLayout()
        load_layout.addWidget(self.btn_load)
        load_layout.addWidget(self.btn_camera)
        load_layout.addWidget(QLabel("Channel:"))
        load_layout.addWidget(self.channel_combo)
        main_layout.addLayout(load_layout)
        
        # Функция 1: Красная маска
        mask_layout = QHBoxLayout()
        mask_layout.addWidget(self.threshold_input)
        mask_layout.addWidget(self.btn_red_mask)
        main_layout.addLayout(mask_layout)
        
        # Функция 2: Резкость
        main_layout.addWidget(self.btn_sharpen)
        
        # Функция 3: Прямоугольник
        rect_layout = QHBoxLayout()
        rect_layout.addWidget(QLabel("Coordinates:"))
        for inp in self.rect_inputs:
            rect_layout.addWidget(inp)
        rect_layout.addWidget(self.btn_draw_rect)
        main_layout.addLayout(rect_layout)
        
        # Контейнер
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Подключение событий
        self.btn_load.clicked.connect(self.load_image)
        self.btn_camera.clicked.connect(self.capture_image)
        self.channel_combo.currentIndexChanged.connect(self.select_channel)
        self.btn_red_mask.clicked.connect(self.apply_red_mask)
        self.btn_sharpen.clicked.connect(self.sharpen_image)
        self.btn_draw_rect.clicked.connect(self.draw_rectangle)

    def load_image(self):
        """Загрузка изображения из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image = cv2.imread(file_path)
            if self.image is None:
                QMessageBox.critical(self, "Error", "Failed to load image!")
                return
            self.display_image(self.image)

    def capture_image(self):
        """Захват изображения с камеры"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            QMessageBox.critical(self, "Camera Error", 
                                "Camera not available!\nPossible solutions:\n"
                                "1. Check camera connection\n"
                                "2. Grant application permissions\n"
                                "3. Restart device")
            return
        
        ret, frame = cap.read()
        cap.release()
        if ret:
            self.image = frame
            self.display_image(self.image)
        else:
            QMessageBox.critical(self, "Error", "Failed to capture image!")

    def display_image(self, img):
        """Отображение изображения в интерфейсе"""
        # Конвертация формата OpenCV в Qt
        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_BGR888)
        
        # Сохранение и отображение
        self.current_display = img.copy()
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(), 
            self.image_label.height(),
            Qt.KeepAspectRatio
        ))

    def select_channel(self):
        """Выбор цветового канала"""
        if self.image is None:
            QMessageBox.warning(self, "Error", "Load an image first!")
            return
            
        channel_index = self.channel_combo.currentIndex()
        img_copy = self.image.copy()
        
        # Оставляем только выбранный канал
        if channel_index == 0:    # Красный
            img_copy[:, :, 0] = 0  # Убираем синий
            img_copy[:, :, 1] = 0  # Убираем зеленый
        elif channel_index == 1:  # Зеленый
            img_copy[:, :, 0] = 0  # Синий
            img_copy[:, :, 2] = 0  # Красный
        else:                     # Синий
            img_copy[:, :, 1] = 0  # Зеленый
            img_copy[:, :, 2] = 0  # Красный
            
        self.display_image(img_copy)

    def apply_red_mask(self):
        """Создание маски по красному каналу"""
        if self.image is None:
            QMessageBox.warning(self, "Error", "Load an image first!")
            return
            
        try:
            threshold = int(self.threshold_input.text())
            if not 0 <= threshold <= 255:
                raise ValueError
        except:
            QMessageBox.warning(self, "Input Error", "Enter a number (0-255)!")
            return
            
        # Извлекаем красный канал
        red_channel = self.image[:, :, 2]
        # Создаем бинарную маску
        mask = np.where(red_channel > threshold, 255, 0).astype(np.uint8)
        # Конвертируем в 3-канальное изображение
        mask_bgr = cv2.merge([mask, mask, mask])
        self.display_image(mask_bgr)

    def sharpen_image(self):
        """Увеличение резкости изображения"""
        if self.image is None:
            QMessageBox.warning(self, "Error", "Load an image first!")
            return
            
        # Ядро для увеличения резкости
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])
        sharpened = cv2.filter2D(self.image, -1, kernel)
        self.display_image(sharpened)

    def draw_rectangle(self):
        """Рисование прямоугольника"""
        if self.image is None:
            QMessageBox.warning(self, "Error", "Load an image first!")
            return
            
        try:
            coords = [int(inp.text()) for inp in self.rect_inputs]
            if len(coords) != 4:
                raise ValueError
            x1, y1, x2, y2 = coords
        except:
            QMessageBox.warning(self, "Input Error", "Enter 4 coordinates (x1 y1 x2 y2)")
            return
            
        img_copy = self.image.copy()
        # Рисуем синий прямоугольник (BGR: 255,0,0)
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), (255, 0, 0), 2)
        self.display_image(img_copy)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorApp()
    window.show()
    sys.exit(app.exec_())
