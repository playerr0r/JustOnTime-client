import sys
import os
import datetime
import hashlib
import requests
import base64

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QGraphicsBlurEffect
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from PyQt5.QtCore import QMimeData
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt, QRect

from PyQt5.QtGui import QColor
from PyQt5.QtGui import QDrag
from PyQt5.QtGui import QRegion, QPixmap
from PyQt5.QtGui import QPixmap

from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtGui

from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from sympy import N

from login import Ui_Login
from main_window import Ui_MainWindow
from sign_in import Ui_SignIn
from stats import Ui_Stats
from reports_backlog import Ui_ReportsWindow
from new_task import Ui_NewTask
from task import Ui_TaskWindow
from new_project import Ui_NewProject


# app dir pat in windows
app_dir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/') + '/'

class Login(QtWidgets.QDialog, Ui_Login):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.widget_3.setObjectName("widget_3")
        self.widget_3.setStyleSheet("#widget_3 { background-image: url(" + app_dir + "resources/login_background.jpg); background-repeat: no-repeat; background-position: center; background-size: cover; }")

        self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
        self.setWindowTitle('Just on time')
        self.login_button.clicked.connect(self.open_main_win)
        self.create_acc_button.clicked.connect(self.open_sign_in)

    def open_main_win(self):
        self.login = self.login_input.text()
        self.password = self.pass_input.text()

        self.password = hashlib.sha256(self.password.encode()).hexdigest()

        print(self.password)
        print(len(self.password))

        url = 'http://localhost:8080/auth/login'
        data = {'login': self.login, 'password': self.password}
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            user_data = response.json()['user']
            self.id = user_data['id']
            self.role = user_data['role']
            self.code = user_data['code']
            self.projects_ids = user_data['projects_ids']
            self.name = user_data['name']
            self.avatar = user_data['avatar']
            print(self.avatar)
            print('Login successful')
            self.main_win = MainWin(self.role, self.id, self.code, self.projects_ids, self.name, self.avatar)
            self.main_win.show()
            self.close()
        else:
            print('Login failed:', response.json())
            self.login_input.setStyleSheet("border: 1px;\n"
            "border-color: rgb(255, 0, 0);\n"
            "border-style: outset;\n"
            "border-radius: 3px;")
            self.pass_input.setStyleSheet("border: 1px;\n"
            "border-color: rgb(255, 0, 0);\n"
            "border-style: outset;\n"
            "border-radius: 3px;")
            print('error')

    def open_sign_in(self):
        self.sign_in = SignIn()
        self.sign_in.show()
        self.close()

class NewTask(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(app_dir + 'new_task.ui', self)
        self.new_task_button.setStyleSheet("background-color: rgb(7, 71, 166);\n"
        "color: white; border: none; border-radius: 3px;")
        self.new_task_name.hide()
        # self.show()

    def dragEnterEvent(self, event):
        event.ignore()

    def dragMoveEvent(self, event):
        event.ignore()

    def dropEvent(self, event):
        event.ignore()

class Card(QWidget):
    clicked = pyqtSignal()

    def __init__(self, name=None, status=None, task_id=None, avatar=None, show = False):
        super().__init__()

        self.drag_start_position = None

        print(avatar)

        # Загрузите шаблон из файла .ui
        uic.loadUi(app_dir + 'card.ui', self)

        self.label.setText(name)
        self.label_2.setText(status)
        self.task_id.setText('task-'+str(task_id))
        # Если предоставлены имя и описание, установите их и покажите карточку
        if avatar is not None:
            avatar = base64.b64decode(avatar)
            byte_array = QByteArray(avatar)
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.ReadOnly)

            user_avatar = QPixmap()
            if not user_avatar.loadFromData(buffer.readAll()):
                print("Failed to load the image.")
            else:
                self.label_3.setPixmap(user_avatar)
                self.label_3.setScaledContents(True)
                mask = QRegion(self.label_3.rect(), QRegion.Ellipse)
                self.label_3.setMask(mask)
        else:
            # Иначе, скройте карточку
            self.label_3.hide()
        if show:
            self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if self.drag_start_position is not None and (event.pos() \
                - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimedata = QMimeData()

        # Set the data for the drag operation
        mimedata.setText(self.task_id.text())

        # Create a pixmap of the card
        pixmap = self.grab()

        # Set the pixmap for the drag object
        drag.setPixmap(pixmap)

        # Set the hot spot to the center of the pixmap
        drag.setHotSpot(pixmap.rect().center())

        drag.setMimeData(mimedata)
        QTimer.singleShot(100, lambda: drag.exec_(Qt.MoveAction))

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('text/plain'):
            event.acceptProposedAction()

    def dropEvent(self, event):
        # Здесь вы можете обработать событие drop, например, переместить карточку
        event.acceptProposedAction()

    def mouseDoubleClickEvent(self, event):
        self.clicked.emit()

    def clone(self, name, status, task_id):
        # Создайте новый экземпляр Card с новым именем и описанием
        return Card(name, status, task_id)
    
class CardMovedSignal(QtCore.QObject):
    moved = pyqtSignal(str, QWidget)
    
class DropArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.card_moved_signal = CardMovedSignal()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            self.card_moved_signal.moved.emit(event.mimeData().text(), self)
            event.acceptProposedAction()
    
class Profile(QWidget):
    def __init__(self):
        super().__init__()

        uic.loadUi(app_dir + 'profile.ui', self)
        self.setStyleSheet("QWidget { border-radius: 3px; }")
        self.profileCloseButton.setText('✖')
        self.show()

class MainWin(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, role, id, code, projects_ids, user_name, avatar):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
        self.setWindowTitle('Just on time')

        self.role = role
        self.id = id
        self.code = code
        self.projects_ids = projects_ids
        self.avatar = avatar

        self.avatar = base64.b64decode(self.avatar)
        self.avatar = base64.b64decode(self.avatar)
        byte_array = QByteArray(self.avatar)
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.ReadOnly)

        user_avatar = QPixmap()

        if not user_avatar.loadFromData(buffer.readAll()):
            print("Failed to load the image.")
        else:
            self.setupUi(self)
            self.profile_button.setIcon(QtGui.QIcon(user_avatar))
            self.profile_button.setIconSize(QtCore.QSize(40, 40))
            mask = QRegion(self.profile_button.rect(), QRegion.Ellipse)
            self.profile_button.setMask(mask)

        if self.role != 'admin':
            self.new_project_button.hide()


        # TODO: добавить функционал для кнопок
        self.reports_button.hide()
        self.search_button.hide()
            
        self.widget_5.hide()

        self.projects_ids = ','.join(map(str, projects_ids))

        response = requests.get(f'http://localhost:8080/projects/?ids={self.projects_ids}')
        if response.status_code == 200:
            data = response.json()
            print(data)
        else:
            print(f'Request failed with status code {response.status_code}')

        for id, name in data['projects'].items():
            self.projectname_combo_box.addItem(name)

        self.projects = list(data['projects'].keys())
        self.project_name = self.projectname_combo_box.currentText()
        self.project_id = self.projects[0]

        self.widgets_stylesheet_setter()
        self.cards_area_setter()

        self.refresh_lists()

        self.pushButton.clicked.connect(lambda: self.close_card_info())
        self.profile_button.clicked.connect(lambda: self.open_profile(self.id))
        self.projectname_combo_box.currentTextChanged.connect(self.refresh_lists)

        self.darkening_widget = QWidget(self)
        self.darkening_widget.hide()
        self.profile_window = Profile()
        self.profile_window.hide()

    def cards_area_setter(self):
        # Создайте новый виджет для содержимого прокрутки
        self.scroll_content = DropArea()
        self.scroll_content2 = DropArea()
        self.scroll_content3 = DropArea()

        self.scroll_content.card_moved_signal.moved.connect(self.card_moved)
        self.scroll_content2.card_moved_signal.moved.connect(self.card_moved)
        self.scroll_content3.card_moved_signal.moved.connect(self.card_moved)

        # Создайте макет для карточек
        self.cards_layout = QGridLayout()
        self.cards_layout2 = QGridLayout()
        self.cards_layout3 = QGridLayout()

        self.scroll_content.setLayout(self.cards_layout)
        self.scroll_content2.setLayout(self.cards_layout2)
        self.scroll_content3.setLayout(self.cards_layout3)

        # Установите scroll_content в качестве виджета прокрутки для scrollArea
        self.scrollArea.setWidget(self.scroll_content)
        # self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.scrollArea_2.setWidget(self.scroll_content2)
        # self.scrollArea_2.setFrameShape(QFrame.NoFrame)
        self.scrollArea_2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.scrollArea_3.setWidget(self.scroll_content3)
        # self.scrollArea_3.setFrameShape(QFrame.NoFrame)
        self.scrollArea_3.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_3.setWidgetResizable(True)

        self.scroll_content.setAcceptDrops(True)
        self.scroll_content2.setAcceptDrops(True)
        self.scroll_content3.setAcceptDrops(True)

        self.cards_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.cards_layout2.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.cards_layout3.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.widget_5_on_screen = False

    def widgets_stylesheet_setter(self):
        self.left_menu.setStyleSheet("background-color: rgba(235, 235, 235, 255);")
        self.widget_4.setStyleSheet("")
        self.widget_4.setObjectName("widget_4")
        self.widget_4.setStyleSheet("#widget_4 { background-image: \
                    url(" + app_dir + "resources/main_background.jpg);\
                    background-repeat: no-repeat; background-size: cover; }")

        self.widget_6.setStyleSheet("background-color: rgba(235, 235, 235, 220);")
        self.widget_7.setStyleSheet("background-color: rgba(235, 235, 235, 220);")
        self.widget_8.setStyleSheet("background-color: rgba(235, 235, 235, 220);")
        self.widget_5.setStyleSheet("background-color: rgba(235, 235, 235, 220);")

        self.scrollArea.setStyleSheet("background-color: rgba(235, 235, 235, 0);")
        self.scrollArea_2.setStyleSheet("background-color: rgba(235, 235, 235, 0);")
        self.scrollArea_3.setStyleSheet("background-color: rgba(235, 235, 235, 0);")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def card_moved(self, task_id, dropped_in_column):
        if dropped_in_column is not None:
            url = 'http://localhost:8080/tasks/' + task_id.split('-')[1] + '/updateStatus'
            # Найдите карточку и переместите ее в новый столбец
            for layout in [self.cards_layout, self.cards_layout2, self.cards_layout3]:
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    widget = item.widget()
                    if widget is not None and isinstance(widget, Card) and widget.task_id.text() == task_id:
                        layout.takeAt(i)
                        if self.widget_5_on_screen == True and \
                            self.project_name_task_id.text().split(' / ')[1].split('-')[1] \
                                == task_id.split('-')[1]:
                            QTimer.singleShot(100, lambda: \
                                              self.show_card_info(task_id=task_id.split('-')[1]))
                    
                        widget.setParent(None)
                        if dropped_in_column == self.scroll_content:
                            data = {'status': 'todo'}
                            response = requests.post(url, json=data)

                            if response.status_code == 200:
                                print(response.json())
                                self.refresh_lists()
                            else:
                                print(f'Request failed with status code {response.status_code}')

                        elif dropped_in_column == self.scroll_content2:
                            data = {'status': 'in progress'}
                            response = requests.post(url, json=data)

                            if response.status_code == 200:
                                print(response.json())
                                self.refresh_lists()
                            else:
                                print(f'Request failed with status code {response.status_code}')

                        elif dropped_in_column == self.scroll_content3:
                            data = {'status': 'done'}
                            response = requests.post(url, json=data)

                            if response.status_code == 200:
                                print(response.json())
                                self.refresh_lists()
                            else:
                                print(f'Request failed with status code {response.status_code}')
                        break

                QApplication.processEvents()

    def close_card_info(self):
        self.group = QtCore.QParallelAnimationGroup()
        self.animation = QtCore.QPropertyAnimation(self.widget_5, b"geometry")
        self.animation.setDuration(150)
        self.animation.setStartValue(QtCore.QRect(1255, -3, 301, 916))
        self.animation.setEndValue(QtCore.QRect(1557, -3, 301, 916))
        self.widget_5_on_screen = False

        self.animation2 = QtCore.QPropertyAnimation(self.widget_6, b"geometry")
        self.animation2.setDuration(150)
        self.animation2.setStartValue(QtCore.QRect(250, 30, 301, 868))
        self.animation2.setEndValue(QtCore.QRect(340, 30, 301, 868))

        self.animation3 = QtCore.QPropertyAnimation(self.widget_7, b"geometry")
        self.animation3.setDuration(150)
        self.animation3.setStartValue(QtCore.QRect(580, 30, 301, 868))
        self.animation3.setEndValue(QtCore.QRect(727, 30, 301, 868))
    
        self.animation4 = QtCore.QPropertyAnimation(self.widget_8, b"geometry")
        self.animation4.setDuration(150)
        self.animation4.setStartValue(QtCore.QRect(910, 30, 301, 868))
        self.animation4.setEndValue(QtCore.QRect(1102, 30, 301, 868))

        self.group.addAnimation(self.animation)
        self.group.addAnimation(self.animation2)
        self.group.addAnimation(self.animation3)
        self.group.addAnimation(self.animation4)
        self.group.start()

    def add_card(self, name, status, task_id, avatar = None):
        # Создайте новую карточку
        card = Card(name, status, task_id, avatar, show=False)
        QApplication.processEvents()
        card.clicked.connect(lambda: self.show_card_info(card = card))
        # Добавьте карточку в макет

        if status == 'todo':
            row = self.cards_layout.rowCount()
            self.cards_layout.addWidget(card, row, 0)
            card.show()
            self.scroll_content.updateGeometry()
            self.scroll_content.adjustSize()
            self.cards_layout.update()
            self.scrollArea.update()
            self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        elif status == 'in progress':
            row = self.cards_layout2.rowCount()
            self.cards_layout2.addWidget(card, row, 0)
            card.show()
            self.scroll_content2.updateGeometry()
            self.scroll_content2.adjustSize()
            self.cards_layout2.update()
            self.scrollArea_2.update()
            self.scrollArea_2.verticalScrollBar().setValue(self.scrollArea_2.verticalScrollBar().maximum())
        elif status == 'done':
            row = self.cards_layout3.rowCount()
            self.cards_layout3.addWidget(card, row, 0)
            card.show()
            self.scroll_content3.updateGeometry()
            self.scroll_content3.adjustSize()
            self.cards_layout3.update()
            self.scrollArea_3.update()
            self.scrollArea_3.verticalScrollBar().setValue(self.scrollArea_3.verticalScrollBar().maximum())

    def show_card_info(self, card = None, task_id = None):
        self.widget_6.setGeometry(250, 30, 301, 868)
        self.widget_7.setGeometry(580, 30, 301, 868)
        self.widget_8.setGeometry(910, 30, 301, 868)

        empl_id = None

        try:
            self.User_task_worker.clicked.disconnect()
        except TypeError:
            pass
        
        if card is not None:
            task_id = card.task_id.text().split('-')[1]

        self.project_name_task_id.setText(self.projectname_combo_box.currentText() \
                                          + ' / task-' + task_id)

        url = 'http://localhost:8080/tasks/' + task_id

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            print(data)
            data = data['task']
            # self.project_name.setText(self.projectname_combo_box.currentText() + ' / task-' + data['id'])
            self.task_name.setText(data['name'])
            # descr_2 is QPlainTextEdit
            self.descr_2.setPlainText(data['descr'])
            self.task_status.setText(data['status'])
            date = data['date'].split('T')[0]
            self.task_date.setText(date)
            empl_id = data['empl_id']
        else:
            print(f'Request failed with status code {response.status_code}')

        if empl_id != '':
            url = 'http://localhost:8080/profile/' + str(empl_id)

            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                print(data)
                data = data['user']
                self.User_task_worker.setStyleSheet("text-align: left; \
                                                    border: none; color: rgb(7, 71, 166); \
                                                    text-decoration: underline;")
                self.User_task_worker.setText(data['name'])
                self.User_task_worker.clicked.connect(lambda: self.open_profile(empl_id))
                avatar = data['avatar']
                avatar = base64.b64decode(avatar)
                byte_array = QByteArray(avatar)
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.ReadOnly)

                user_avatar = QPixmap()
                if not user_avatar.loadFromData(buffer.readAll()):
                    print("Failed to load the image.")
                else:
                    self.User_task_worker_pic.setPixmap(user_avatar)
                    self.User_task_worker_pic.setScaledContents(True)
                    mask = QRegion(self.User_task_worker_pic.rect(), QRegion.Ellipse)
                    self.User_task_worker_pic.setMask(mask)
        else:
            self.User_task_worker.setText('Назначить себя')
            self.User_task_worker_pic.setText('')
            self.User_task_worker.setStyleSheet("text-align: center; border: none;\
                                                 color: rgb(7, 71, 166); text-decoration: underline;\
                                                 background-color: rgba(255, 255, 255, 0);")
            self.User_task_worker_pic.clear()
            self.User_task_worker_pic.setStyleSheet("background-color: rgba(255, 255, 255, 0);\
                                                     color: rgb(0, 0, 0, 0);")
            self.User_task_worker.clicked.connect(lambda: self.assign_to_task(self.id, task_id))

        if self.widget_5_on_screen == False:
            self.animation = QtCore.QPropertyAnimation(self.widget_5, b"geometry")
            self.animation.setDuration(150)
            self.animation.setStartValue(QtCore.QRect(1557, -3, 301, 916))
            self.widget_5.show()
            self.widget_5_on_screen = True
            self.animation.setEndValue(QtCore.QRect(1255, -3, 301, 916))

            self.animation2 = QtCore.QPropertyAnimation(self.widget_6, b"geometry")
            self.animation2.setDuration(150)
            self.animation2.setStartValue(QtCore.QRect(340, 30, 301, 868))
            self.animation2.setEndValue(QtCore.QRect(250, 30, 301, 868))

            self.animation3 = QtCore.QPropertyAnimation(self.widget_7, b"geometry")
            self.animation3.setDuration(150)
            self.animation3.setStartValue(QtCore.QRect(727, 30, 301, 868))
            self.animation3.setEndValue(QtCore.QRect(580, 30, 301, 868))

            self.animation4 = QtCore.QPropertyAnimation(self.widget_8, b"geometry")
            self.animation4.setDuration(150)
            self.animation4.setStartValue(QtCore.QRect(1102, 30, 301, 868))
            self.animation4.setEndValue(QtCore.QRect(910, 30, 301, 868))

            self.group = QtCore.QParallelAnimationGroup()
            self.group.addAnimation(self.animation)
            self.group.addAnimation(self.animation2)
            self.group.addAnimation(self.animation3)
            self.group.addAnimation(self.animation4)
            self.group.start()

    def assign_to_task(self, id, task_id):
        url = 'http://localhost:8080/tasks/' + task_id + '/assign/' + '?empl_id=' + str(id)
        response = requests.post(url)

        if response.status_code == 200:
            print(response.json())
            self.show_card_info(task_id=task_id)
            self.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

    def clear_column(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)

            layout.removeItem(item)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                widget.setParent(None)

    def open_profile(self, id):
        self.profile_window.show()
        self.darkening_widget.show()

        url = 'http://localhost:8080/profile/' + str(id)

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            print(data)
            data = data['user']
            self.profile_window.profileName.setText(data['name'])
            self.profile_window.profileJobTitle.setText(data['role']) 
            # profile_window.role.setText(data['role'])
            avatar = data['avatar']
            avatar = base64.b64decode(avatar)
            byte_array = QByteArray(avatar)
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.ReadOnly)

            user_avatar = QPixmap()
            if not user_avatar.loadFromData(buffer.readAll()):
                print("Failed to load the image.")
            else:
                self.profile_window.profileAvatar.setPixmap(user_avatar)
                self.profile_window.profileAvatar.setScaledContents(True)
                mask = QRegion(self.profile_window.profileAvatar.rect(), QRegion.Ellipse)
                self.profile_window.profileAvatar.setMask(mask)

        try:
            self.profile_window.profileCloseButton.clicked.disconnect()
        except TypeError:
            pass

        self.profile_window.profileCloseButton.clicked.connect(lambda: \
                    self.close_profile(self.profile_window, self.darkening_widget))

        # Создание виджета для затемнения

        self.darkening_widget.setGeometry(0, 0, self.width(), self.height())
        self.darkening_widget.setStyleSheet("background-color: rgba(0, 0, 0, 127);")

        self.profile_window.setGeometry(
            self.width() // 2 - self.profile_window.width() // 2,
            self.height() // 2 - self.profile_window.height() // 2,
            self.profile_window.width(),
            self.profile_window.height()
        )

        self.profile_window.setParent(self)

        self.darkening_widget.show()
        self.profile_window.show()

    def close_profile(self, profile_window, darkening_widget):
        profile_window.hide()
        darkening_widget.hide()

    def refresh_lists(self):
        # self.widget_5.hide()
        print('REFRESHING LISTS')
        self.scroll_content.hide()
        self.scroll_content2.hide()
        self.scroll_content3.hide()
        self.clear_column(self.cards_layout)
        self.clear_column(self.cards_layout2)   
        self.clear_column(self.cards_layout3)

        # query for tasks of project
        self.project_name = self.projectname_combo_box.currentText()
        self.project_id = self.projects[self.projectname_combo_box.currentIndex()]
        response = requests.get(f'http://localhost:8080/projects/{self.project_id}/tasks')

        data = {}

        if response.status_code == 200:
            data = response.json()
            print(data)
            if data['tasks'] != None:
                for data in data['tasks']:
                    self.add_card(data['name'], data['status'], data['id'], data['avatar'])
        else:
            print(f'Request failed with status code {response.status_code}')

        adder_task = NewTask()
        self.cards_layout.addWidget(adder_task, self.cards_layout.rowCount(), 0)
        adder_task.show()
        adder_task.lower()
        self.scroll_content.updateGeometry()
        self.scroll_content.adjustSize()
        self.cards_layout.update()
        self.scrollArea.update()
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        adder_task.new_task_button.clicked.connect(lambda:\
                    self.new_task(adder_task, self.project_id, 'todo'))

        adder_task2 = NewTask()
        self.cards_layout2.addWidget(adder_task2, self.cards_layout2.rowCount(), 0)
        adder_task2.show()
        adder_task2.lower()
        self.scroll_content2.updateGeometry()
        self.scroll_content2.adjustSize()
        self.cards_layout2.update()
        self.scrollArea_2.update()
        self.scrollArea_2.verticalScrollBar().setValue(self.scrollArea_2.verticalScrollBar().maximum())
        adder_task2.new_task_button.clicked.connect(lambda:\
                     self.new_task(adder_task2, self.project_id, 'in progress'))

        adder_task3 = NewTask()
        self.cards_layout3.addWidget(adder_task3, self.cards_layout3.rowCount(), 0)
        adder_task3.show()
        adder_task3.lower()
        self.scroll_content3.updateGeometry()
        self.scroll_content3.adjustSize()
        self.cards_layout3.update()
        self.scrollArea_3.update()
        self.scrollArea_3.verticalScrollBar().setValue(self.scrollArea_3.verticalScrollBar().maximum())
        adder_task3.new_task_button.clicked.connect(lambda:\
                     self.new_task(adder_task3, self.project_id, 'done'))

        self.cards_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.cards_layout2.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.cards_layout3.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.scroll_content.show()
        self.scroll_content2.show()
        self.scroll_content3.show()

    def new_task(self, adder_task, project_id, status):
        adder_task.new_task_button.hide()
        adder_task.new_task_name.show()

        try:
            adder_task.new_task_name.returnPressed.disconnect()
        except TypeError:
            pass

        adder_task.new_task_name.returnPressed.connect(lambda:\
                     self.add_new_task(adder_task.new_task_name.text(), adder_task, project_id, status))

    def add_new_task(self, name, adder_task, project_id, status):
        print(name)
        
        data = {
            'name': name,
            'status': status,
            'project_id': project_id,
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        print(data['date'])

        response = requests.post('http://localhost:8080/tasks/new', json=data)

        if response.status_code == 200:
            adder_task.new_task_name.setText('')
            adder_task.new_task_name.hide()
            adder_task.new_task_button.show()
            print(response.json())
            self.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')
        
# class reports_backlog(QtWidgets.QDialog, Ui_ReportsWindow):
#     def __init__(self, mode, id_project):
#         super().__init__()
#         self.setupUi(self)
#         self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
#         self.setWindowTitle('Just on time')
#         self.id_project = id_project
#         self.mode = mode
#         # clear table widget
#         self.tableWidget.clear()

#         if self.id_project == None:
#             self.tableWidget.setColumnCount(1)
#             self.tableWidget.setHorizontalHeaderLabels(['No project selected'])
#             self.tableWidget.setColumnWidth(0, 800)
#             self.tableWidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
#             self.tableWidget.setRowCount(1)
#             self.tableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem('No project selected'))
#         elif self.mode == 'reports':
#             self.tableWidget.setColumnCount(6)
#             self.tableWidget.setHorizontalHeaderLabels(['id', 'report', 'date', 'task_id', 'empl_code', 'project_id'])
#             self.tableWidget.setColumnWidth(0, 50)
#             self.tableWidget.setColumnWidth(1, 550)
#             self.tableWidget.setColumnWidth(2, 150)
#             self.tableWidget.setColumnWidth(3, 90)
#             self.tableWidget.setColumnWidth(4, 90)
#             self.tableWidget.setColumnWidth(5, 90)
#             self.tableWidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
#             cur.execute("SELECT * from reports WHERE project_id = '%s'", (self.id_project,))
#             self.reports = cur.fetchall()
#             self.tableWidget.setRowCount(len(self.reports))
#             for report in self.reports:
#                 self.report_date = report[2].strftime("%d/%m/%Y")
#                 self.report_date = self.report_date.split('/')
#                 self.report_date = self.report_date[2] + '.' + self.report_date[1] + '.' + self.report_date[0]
#                 self.report_date = self.report_date.replace(' ', '')
#             print(self.reports)
#             for rows in range(len(self.reports)):
#                     for row in range(6):
#                         self.tableWidget.setItem(rows, row, QtWidgets.QTableWidgetItem(str(self.reports[rows][row])))
    
#         elif self.mode == 'backlog':
#             self.tableWidget.setColumnCount(4)
#             self.tableWidget.setHorizontalHeaderLabels(['id', 'date', 'date_act', 'empl_code'])
#             self.tableWidget.setColumnWidth(0, 50)
#             self.tableWidget.setColumnWidth(1, 150)
#             self.tableWidget.setColumnWidth(2, 150)
#             self.tableWidget.setColumnWidth(3, 150)
#             self.tableWidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
#             cur.execute("SELECT id, date, date_act, empl_code from tasks WHERE status = 'done' and project_id = '%s'", (self.id_project,))
#             self.backlog = cur.fetchall()
#             print(self.backlog)
#             self.tableWidget.setRowCount(len(self.backlog))
#             for log in self.backlog:
#                 self.log_date = log[1].strftime("%d/%m/%Y")
#                 self.log_date_act = log[2].strftime("%d/%m/%Y")
#                 self.log_date = self.log_date.split('/')
#                 self.log_date = self.log_date[2] + '.' + self.log_date[1] + '.' + self.log_date[0]
#                 self.log_date = self.log_date.replace(' ', '')
#                 self.log_date_act = self.log_date_act.split('/')
#                 self.log_date_act = self.log_date_act[2] + '.' + self.log_date_act[1] + '.' + self.log_date_act[0]
#                 self.log_date_act = self.log_date_act.replace(' ', '')
#             for rows in range(len(self.backlog)):
#                     for row in range(4):
#                         self.tableWidget.setItem(rows, row, QtWidgets.QTableWidgetItem(str(self.backlog[rows][row])))

# class new_task(QtWidgets.QDialog, Ui_NewTask):
#     def __init__(self, id_of_project, code):
#         super().__init__()
#         self.setupUi(self)
#         self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
#         self.setWindowTitle('Just on time')
#         self.code = code
#         self.id_of_project = id_of_project
#         print(self.id_of_project)
#         self.buttonBox.accepted.connect(self.create_task)
#         self.buttonBox.rejected.connect(self.close)
#         # get list of users codes from project where user is in project and project is selected
#         cur.execute("SELECT codes_users FROM projects WHERE codes_users LIKE %s AND id = %s", ('%' + str(self.code) + '%', self.id_of_project))
#         self.codes = cur.fetchall()
#         # self.codes to list of integers
#         self.codes = self.codes[0][0].split(', ')
#         # clear empty
#         self.codes = [i for i in self.codes if i]
#         # to int
#         self.codes = [int(i) for i in self.codes]
#         print(self.codes)
#         # get all employees names and codes of project
#         cur.execute("SELECT name, id FROM users WHERE code = ANY(%s) and role = 'employee'", (self.codes,))
#         self.employees = cur.fetchall()
#         print(self.employees)
#         # employee name to listwidget
#         list_of_employee = []
#         for employee in self.employees:
#             if employee not in list_of_employee:
#                 list_of_employee.append(employee)
#         for employee in list_of_employee:
#             self.list_of_employee.addItem(employee[0])

#     def create_task(self):
#         self.task_status = 'todo'
#         self.task_name = self.task_name_input.text()
#         self.task_desc = self.task_description_input.text()
#         self.task_date = self.dateEdit.text()
#         # postgre date format from string
#         self.task_date = self.task_date.split('.')
#         self.task_date = self.task_date[2] + '-' + self.task_date[1] + '-' + self.task_date[0]
#         self.task_date = self.task_date.replace(' ', '')

#         self.task_empl_name = self.list_of_employee.currentItem().text()
#         for employee in self.employees:
#             if employee[0] == self.task_empl_name:
#                 self.task_empl_code = employee[1]
        
#         cur.execute("SELECT max(id) FROM tasks")
#         self.max_id = cur.fetchall()
#         # self.task_empl_code to int
#         self.task_empl_code = int(self.task_empl_code)
#         if self.max_id[0][0] == None:
#             self.id_of_task = 1
#         else:
#             self.id_of_task = self.max_id[0][0] + 1
#         cur.execute("INSERT INTO tasks (id, name, descr, status, date, empl_code, project_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.id_of_task, self.task_name, self.task_desc, self.task_status, self.task_date, self.task_empl_code, self.id_of_project))
#         con.commit()
#         self.close()

# class task(QtWidgets.QDialog, Ui_TaskWindow):
#     def __init__(self, id_of_task, project_name, id_project, code):
#         super().__init__()
#         self.setupUi(self)
#         self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
#         self.setWindowTitle('Just on time')
#         self.id_of_task = id_of_task
#         self.project_name = project_name
#         self.id_project = id_project
#         self.code = code
#         cur.execute("SELECT name, descr, status, date, date_act FROM tasks WHERE id = %s", (self.id_of_task,))
#         task_info = cur.fetchall()
#         self.task_name = task_info[0][0]
#         self.task_desc = task_info[0][1]
#         self.task_status = task_info[0][2]
#         self.task_date = task_info[0][3]
#         self.task_num2.setText(self.id_of_task)
#         self.task_name2.setText(self.task_name)
#         self.task_desc2.setText(self.task_desc)
#         self.task_date = self.task_date.strftime("%d/%m/%Y")
#         self.date_to_complete2.setText(self.task_date)
#         self.status2.setText(self.task_status)

#         if self.task_status == 'todo':
#             self.complete_button_2.hide()
#             self.complete_button.setText('Take task')
#         self.report_button.clicked.connect(self.send_report)
#         self.complete_button.clicked.connect(self.complete_task)
#         self.ok_button.clicked.connect(self.close)
#         self.complete_button_2.clicked.connect(self.decrease_task)

#     def send_report(self):
#         self.date = datetime.datetime.now()
#         # postgre date format from string
#         self.date = self.date.strftime("%d/%m/%Y")
#         self.date = self.date.split('/')
#         self.date = self.date[2] + '-' + self.date[1] + '-' + self.date[0]
#         self.date = self.date.replace(' ', '')

#         self.report = self.new_report_input.text()
#         cur.execute("SELECT max(id) FROM reports")
#         self.max_id = cur.fetchall()
#         if self.max_id[0][0] == None:
#             self.id_of_report = 1
#         else:
#             self.id_of_report = self.max_id[0][0] + 1
#         cur.execute("INSERT INTO reports (id, report, task_id, date, empl_code, project_id) VALUES (%s, %s, %s, %s, %s, %s)", (self.id_of_report, self.report, self.id_of_task, self.date, self.code, self.id_project))
#         con.commit()
#         self.new_report_input.setText('')

#     def complete_task(self):
#         if self.task_status == 'todo':
#             cur.execute("UPDATE tasks SET status = 'in progress' WHERE id = %s", (self.id_of_task,)) 
#             con.commit()
#         else:
#             date = datetime.datetime.now()
#             # postgre date format from string
#             date = date.strftime("%d/%m/%Y")
#             date = date.split('/')
#             date = date[2] + '-' + date[1] + '-' + date[0]
#             date = date.replace(' ', '')

#             cur.execute("UPDATE tasks SET status = 'done', date_act = %s WHERE id = %s", (date, self.id_of_task))
#             con.commit()
#         self.close()
    
#     def decrease_task(self):
#         if self.task_status == 'done':
#             cur.execute("UPDATE tasks SET status = 'in progress' WHERE id = %s", (self.id_of_task,))
#             con.commit()
#         else:
#             cur.execute("UPDATE tasks SET status = 'todo' WHERE id = %s", (self.id_of_task,))
#             con.commit()
#         self.close()

# class new_project(QtWidgets.QDialog, Ui_NewProject):
#     def __init__(self):
#         super().__init__()
#         self.setupUi(self)
#         self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
#         self.setWindowTitle('Just on time')
#         self.selected_members.setText('')
#         self.codes_selected_members = ''
#         self.listWidget.clear()
#         # list of all employees and code in listwidget
#         cur.execute("SELECT name, code FROM users WHERE role = 'employee'")
#         self.employees = cur.fetchall()
#         print(self.employees)
#         for employee in self.employees:
#             self.listWidget.addItem(employee[0])
#         self.listWidget.itemDoubleClicked.connect(lambda: self.add_member(self.listWidget.currentItem().text(), self.employees))
#         self.buttonBox.accepted.connect(self.create_project)
#         self.buttonBox.rejected.connect(self.close)

#     def add_member(self, member, employees):
#         self.employees = employees
#         for employee in self.employees:
#             if employee[0] == member:
#                 self.code = employee[1]
#         if member not in self.selected_members.text():
#             self.selected_members.setText(self.selected_members.text() + member + '\n')
#             self.codes_selected_members = self.codes_selected_members + str(self.code) + ', '
#         else:
#             self.selected_members.setText(self.selected_members.text().replace(member + '\n', ''))
#             self.codes_selected_members = self.codes_selected_members.replace(str(self.code) + ', ', '')

#         # print all codes of selected members
#         print(self.codes_selected_members)

#     def create_project(self):
#         cur.execute("SELECT max(id) FROM projects")
#         self.max_id = cur.fetchall()
#         print(self.max_id[0][0])
#         if self.max_id[0][0] is None:
#             self.id_of_project = 1
#         else:
#             self.id_of_project = self.max_id[0][0] + 1
#         self.project_name = self.project_name_input.text()
#         # add codes of admins to codes of selected members
#         cur.execute("SELECT code FROM users WHERE role = 'admin'")
#         self.admins = cur.fetchall()
#         for admin in self.admins:
#             self.codes_selected_members = self.codes_selected_members + str(admin[0]) + ', '
#         cur.execute("INSERT INTO projects (id, name, codes_users) VALUES (%s, %s, %s)", (self.id_of_project, self.project_name, self.codes_selected_members))
#         con.commit()
#         self.close()
        
class SignIn(QtWidgets.QDialog, Ui_SignIn):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.widget.setObjectName("widget")
        self.widget.setStyleSheet("#widget { background-image:\
                 url(" + app_dir + "resources/sign_in_background.png);\
                 background-repeat: no-repeat; background-position: center;\
                 background-size: cover; }")
        self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
        self.setWindowTitle('Just on time')
        self.signin_button.clicked.connect(self.input_checker)
        self.back_button.clicked.connect(self.open_login)


    def input_checker(self):
        login = self.login_input.text()
        url = 'http://localhost:8080/auth/register/check/' + login
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(data)
            self.password = self.pass_input.text()
            self.password = hashlib.sha256(self.password.encode()).hexdigest()
            if data['message'] == 'Login exists' or self.login_input.text() == '':
                self.login_input.setStyleSheet("border: 1px;\n"
                "border-color: rgb(255, 0, 0);\n"
                "border-style: outset;\n"
                "border-radius: 3px;")
                self.login_input.setText('')
            elif self.pass_input_2.text() == '':
                self.pass_input_2.setStyleSheet("border: 1px;\n"
                "border-color: rgb(255, 0, 0);\n"
                "border-style: outset;\n"
                "border-radius: 3px;")
            elif self.empl_code_input.text() == '':
                self.empl_code_input.setStyleSheet("border: 1px;\n"
                "border-color: rgb(255, 0, 0);\n"
                "border-style: outset;\n"
                "border-radius: 3px;")
            elif self.name_input.text() == '':
                self.name_input.setStyleSheet("border: 1px;\n"
                "border-color: rgb(255, 0, 0);\n"
                "border-style: outset;\n"
                "border-radius: 3px;")
            else:
                url = 'http://localhost:8080/auth/register'
                data = {'name': self.name_input.text(),
                        'login': self.login_input.text(), 
                        'password': self.password, 
                        'role': 'employee', 
                        'code': self.empl_code_input.text()}
                response = requests.post(url, json=data)
                if response.status_code == 200:
                    print(response.json())
                    self.open_login()
                else:
                    print(f'Request failed with status code {response.status_code}')
        else:
            print(f'Request failed with status code {response.status_code}')

    def open_login(self):
        self.login = Login()
        self.login.show()
        self.close()

# class stats(QtWidgets.QDialog, Ui_Stats):
#     def __init__(self, id, role, project_id, code):
#         super().__init__()
#         self.setupUi(self)
#         self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
#         self.setWindowTitle('Just on time')
#         self.id = id
#         self.code = code
#         self.role = role
#         self.project_id = project_id
#         self.active_sprints_button.clicked.connect(self.export)
#         self.homepage_button.clicked.connect(self.open_main_win)
#         self.refresh_button.clicked.connect(self.refresh)

#         self.figure = Figure()
#         self.canvas = FigureCanvas(self.figure)
#         self.ax = self.figure.add_subplot(111)
#         # line diagram in widget7 of tasks done by employees in last 7 days if role is admin
#         if self.role == 'admin':
#             cur.execute("SELECT name, code FROM users")
#             self.employees = cur.fetchall()
#             self.employees_tasks = []
#             for employee in self.employees:
#                 cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act >= current_date - interval '7 days'", (employee[1],))
#                 self.employees_tasks.append(cur.fetchall()[0][0])
#             self.ax.plot([1, 2, 3, 4, 5, 6, 7], self.employees_tasks)
#             self.ax.set_title('Tasks done by employees in last 7 days')
#             self.ax.set_xlabel('days')
#             self.ax.set_ylabel('tasks done')
#             self.figure.set_facecolor('none')
#             self.figure.tight_layout()
#             self.figure.set_alpha(0)
#             # set size of canvas
#             self.canvas.resize(750, 340)
#             # set margins of canvas to make space for label of x axis
#             self.figure.subplots_adjust(bottom=0.15)
#             # set x axis to 1-7
#             self.ax.set_xlim(1, 7)
#             # draw lines of grid
#             self.ax.grid(True)
#             self.canvas.draw()
#             self.layout = QtWidgets.QVBoxLayout(self.widget_7)
#             self.layout.addWidget(self.canvas)
#         # line diagram in widget7 of tasks done by employee in last 7 days if role is employee
#         else:
#             # line diagram in widget7 of tasks done by employee in last 7 days
#             # list of tasks done by employee in last 7 days day by day with 0 if no tasks done
#             self.employees_tasks = []
#             cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act = current_date - interval '6 days'", (self.id,))
#             self.employees_tasks.append(cur.fetchall()[0][0])
#             cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act = current_date - interval '5 days'", (self.id,))
#             self.employees_tasks.append(cur.fetchall()[0][0])
#             cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act = current_date - interval '4 days'", (self.id,))
#             self.employees_tasks.append(cur.fetchall()[0][0])
#             cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act = current_date - interval '3 days'", (self.id,))
#             self.employees_tasks.append(cur.fetchall()[0][0])
#             cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act = current_date - interval '2 days'", (self.id,))
#             self.employees_tasks.append(cur.fetchall()[0][0])
#             cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act = current_date - interval '1 days'", (self.id,))
#             self.employees_tasks.append(cur.fetchall()[0][0])
#             cur.execute("SELECT count(id) FROM tasks WHERE empl_code = %s AND status = 'done' AND date_act = current_date", (self.id,))
#             self.employees_tasks.append(cur.fetchall()[0][0])
#             print(self.employees_tasks)
#             self.ax.plot([1, 2, 3, 4, 5, 6, 7], self.employees_tasks)
#             self.ax.set_title('Tasks done by you in last 7 days')
#             self.ax.set_xlabel('days')
#             self.ax.set_ylabel('tasks done')
#             self.figure.set_facecolor('none')
#             self.figure.tight_layout()
#             self.figure.set_alpha(0)
#             # set size of canvas
#             self.canvas.resize(750, 340)
#             # set margins of canvas to make space for label of x axis
#             self.figure.subplots_adjust(bottom=0.15)
#             # set x axis to 1-7
#             self.ax.set_xlim(1, 7)
#             # draw lines of grid
#             self.ax.grid(True)
#             self.canvas.draw()
#             self.layout = QtWidgets.QVBoxLayout(self.widget_7)
#             self.layout.addWidget(self.canvas)

#         # pie diagram in widget8 of tasks status if role is admin on project

#         self.figure = Figure()
#         self.canvas = FigureCanvas(self.figure)
#         self.ax = self.figure.add_subplot(111)
#         # set background color of diagram to transparent
#         self.figure.set_facecolor('none')
#         if self.role == 'admin':
#             cur.execute("SELECT count(id) FROM tasks WHERE status = 'todo' AND project_id = %s", (self.project_id))
#             self.to_do = cur.fetchall()[0][0]
#             cur.execute("SELECT count(id) FROM tasks WHERE status = 'in progress' AND project_id = %s", (self.project_id))
#             self.in_progress = cur.fetchall()[0][0]
#             cur.execute("SELECT count(id) FROM tasks WHERE status = 'done' AND project_id = %s", (self.project_id))
#             self.done_ = cur.fetchall()[0][0]
#             self.ax.pie([self.to_do, self.in_progress, self.done_], labels=['todo', 'in progress', 'done'])
#             self.ax.set_title('Tasks status')
#             self.figure.set_facecolor('none')
#             self.figure.set_alpha(0)
#             self.canvas.draw()
#             self.layout = QtWidgets.QVBoxLayout(self.widget_8)
#             self.layout.addWidget(self.canvas)
#         # pie diagram in widget8 of tasks status if role is employee on project
#         else:
#             cur.execute("SELECT count(id) FROM tasks WHERE status = 'todo' AND project_id = %s AND empl_code = %s", (self.project_id, self.id))
#             self.to_do = cur.fetchall()[0][0]
#             cur.execute("SELECT count(id) FROM tasks WHERE status = 'in progress' AND project_id = %s AND empl_code = %s", (self.project_id, self.id))
#             self.in_progress = cur.fetchall()[0][0]
#             cur.execute("SELECT count(id) FROM tasks WHERE status = 'done' AND project_id = %s AND empl_code = %s", (self.project_id, self.id))
#             self.done_ = cur.fetchall()[0][0]
#             print(self.to_do, self.in_progress, self.done_)
#             if self.to_do == 0 and self.in_progress == 0 and self.done_ == 0:
#                 self.ax.pie([1], labels=['no tasks'])
#             else:
#                 self.ax.pie([self.to_do, self.in_progress, self.done_], labels=['todo', 'in progress', 'done'])
#                 self.ax.set_title('Tasks status')
#                 self.figure.set_facecolor('none')
#                 self.figure.set_alpha(0)
#             self.canvas.draw()
#             self.layout = QtWidgets.QVBoxLayout(self.widget_8)
#             self.layout.addWidget(self.canvas)

    # def open_main_win(self):
    #     try:
    #         self.main_win = main_win(code = self.code, role=self.role, id=self.id)
    #         self.main_win.show()
    #         self.close()
    #     except:
    #         # error message
    #         print('error')

    # def refresh(self):
    #     self.stats = stats(id=self.id, role=self.role, project_id=self.project_id, code = self.code)
    #     self.stats.show()
    #     self.close()
        
# unit tests of qt app
# import unittest
# class TestApp(unittest.TestCase):
#     def test_main_win(self):
#         self.app = QtWidgets.QApplication([])
#         self.assertEqual(main_win(role='admin', id='1').role, 'admin')
#         self.assertEqual(main_win(role='admin', id='1').code, '1')
#         self.assertEqual(main_win(role='admin', id='1').project_id, None)
#         self.assertEqual(main_win(role='employee', id='1').role, 'employee')

#     def test_stats(self):
#         self.app = QtWidgets.QApplication([])
#         self.assertEqual(stats(role='admin', code='1', project_id='1').role, 'admin')
#         self.assertEqual(stats(role='admin', code='1', project_id='1').employees_tasks, [])

# TestApp().test_main_win()
# TestApp().test_stats()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app.setStyleSheet("""
    QScrollBar:vertical {
        background: rgba(128, 128, 128, 255); /* Полупрозрачный серый фон */
        width: 8px; /* Ширина скроллбара */
    }

    QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 210); /* Полупрозрачная белая ручка */
        border-radius: 4px; /* Скругление углов */
        min-height: 20px; /* Минимальная высота ручки */
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none; /* Убираем кнопки вверху и внизу скроллбара */
    }

    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        width: 0px; height: 0px; /* Убираем стрелки и неиспользуемые элементы */
        background: none;
    }
    """)
    fontId = QtGui.QFontDatabase.addApplicationFont(app_dir + "resources/Rubik-Regular.ttf")
    if fontId != -1:
        # Шрифт успешно загружен, получаем его семейство
        fontFamilies = QtGui.QFontDatabase.applicationFontFamilies(fontId)
        if fontFamilies:
            font = QtGui.QFont(fontFamilies[0], 10)
            app.setFont(font)
    else:
        print("Failed to load font")

    window = Login()
    window.show()
    sys.exit(app.exec_())