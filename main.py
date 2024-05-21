# TODO:
# 1. доделать работу колонок -
# 2. сделать создание проектов
# 3. все фичи проекта(удаление, добавление новых людей, удаление людей)
# 4. гранты в дашборде

import sys
import os
import datetime
import hashlib
import requests
import base64
import locale

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QApplication

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from PyQt5.QtCore import QMimeData
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QDrag
from PyQt5.QtGui import QRegion, QPixmap
from PyQt5.QtGui import QPixmap

from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtGui


# app dir pat in windows
app_dir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/') + '/'
url = "https://justontime-backend.onrender.com/"
# url = "http://localhost:8080/"

class Login(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(app_dir + 'ui/login.ui', self)
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

        data = {'login': self.login, 'password': self.password}
        
        response = requests.post(url+"auth/login", json=data)
        
        if response.status_code == 200:
            user_data = response.json()['user']
            self.id = user_data['id']
            self.role = user_data['role']
            self.code = user_data['code']
            self.projects_ids = user_data['projects_ids']
            self.name = user_data['name']
            self.avatar = user_data['avatar']
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
    def __init__(self, column=None):
        super().__init__()
        uic.loadUi(app_dir + 'ui/new_task.ui', self)
        self.new_task_button.setStyleSheet("background-color: rgb(7, 71, 166);\n"
        "color: white; border: none; border-radius: 3px;")
        self.new_task_name.hide()
        self.column = column
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
        self.task_id = task_id
        self.task_id = str(self.task_id)

        # Загрузите шаблон из файла .ui
        uic.loadUi(app_dir + 'ui/card.ui', self)

        self.card.setObjectName("Card")
        self.setStyleSheet("#Card { background-color: rgb(255, 255, 255); border-radius: 3px; border: 1px solid rgb(217, 217, 217);}")

        self.label.setText(name)
        self.label_2.setText(status)
        # self.task_id.setText('task-'+str(task_id))
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
        mimedata.setText(str(self.task_id))

        # Create a pixmap of the card
        pixmap = self.grab()

        # Set the pixmap for the drag object
        drag.setPixmap(pixmap)

        # Set the hot spot to the center of the pixmap
        drag.setHotSpot(pixmap.rect().center())

        drag.setMimeData(mimedata)
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('text/plain'):
            event.acceptProposedAction()

    def dropEvent(self, event):
        task_id = event.mimeData().text()
        self.card_moved_signal.moved.emit(task_id, self)

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
        if event.mimeData().hasFormat('text/plain'):
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

        uic.loadUi(app_dir + 'ui/profile.ui', self)
        self.setStyleSheet("QWidget { border-radius: 3px; }")
        self.profileCloseButton.setText('✖')
        self.show()

class ProfileDashboard(QWidget):
    def __init__(self):
        super().__init__()

        uic.loadUi(app_dir + 'ui/profile_dash.ui', self)

class TaskDashboard(QWidget):
    def __init__(self, name, status, card):
        super().__init__()

        uic.loadUi(app_dir + 'ui/task_dash.ui', self)
        self.task_name_dash.setText(name)
        self.task_status_dash.setText(status)


class NewColumn(QWidget):
    def __init__(self):
        super().__init__()

        uic.loadUi(app_dir + 'ui/new_column.ui', self)

        self.create_column_button.setStyleSheet("background-color: rgb(217, 217, 217); color: rgb(7, 71, 166); border: none; border-radius: 3px;")


class MainWin(QtWidgets.QMainWindow):
    def __init__(self, role, id, code, projects_ids, user_name, avatar):
        super().__init__()

        uic.loadUi(app_dir + 'ui/main_window.ui', self)
        self.setWindowIcon(QtGui.QIcon(app_dir + 'resources/winicon.png'))
        # self.homepage_button.setStyleSheet(f"image: url({app_dir}/resources/homepage.svg);")
        # self.stats_button.setStyleSheet(f"image: url({app_dir}/resources/stats.svg);")
        # self.refresh_button.setStyleSheet(f"image: url({app_dir}/resources/refresh.svg);")
        # self.profile_button.setStyleSheet(f"image: url({app_dir}/resources/profile.svg);")
        self.setWindowTitle('Just on time')

        self.role = role
        self.id = id
        self.code = code
        self.projects_ids = projects_ids
        self.avatar = avatar
        self.projects = []

        self.profile_name.setText(user_name)

        self.avatar = base64.b64decode(self.avatar)
        self.avatar = base64.b64decode(self.avatar)
        byte_array = QByteArray(self.avatar)
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.ReadOnly)

        user_avatar = QPixmap()

        if not user_avatar.loadFromData(buffer.readAll()):
            print("Failed to load the image.")
        else:
            self.profile_button.setIcon(QtGui.QIcon(user_avatar))
            self.profile_button.setIconSize(QtCore.QSize(40, 40))
            mask = QRegion(self.profile_button.rect(), QRegion.Ellipse)
            self.profile_button.setMask(mask)

        # self.loading_movie = QtGui.QMovie(app_dir + 'resources/22.gif')
        # self.loading_movie_2 = QtGui.QMovie(app_dir + 'resources/22.gif')
        # self.loading_label.setMovie(self.loading_movie)
        # self.loading_label_2.setMovie(self.loading_movie_2)

        self.projectname_combo_box.hide()

        # if self.role != 'admin':
        #     self.new_project_button.hide()
            
        self.widget_5.hide()

        if self.projects_ids:
            self.projects_ids = ','.join(map(str, projects_ids))
            response = requests.get(url + "projects/?ids=" + self.projects_ids)
            if response.status_code == 200:
                data = response.json()
            else:
                print(f'Request failed with status code {response.status_code}')

            for id, name in data['projects'].items():
                self.projectname_combo_box.addItem(name)

            self.projects = list(data['projects'].keys())
            self.project_name = self.projectname_combo_box.currentText()
            self.project_id = self.projects[0]

        self.open_dashboard()

        self.widgets_stylesheet_setter()
        self.cards_area_setter()

        self.refresh_lists()

        self.pushButton.clicked.connect(lambda: self.close_card_info())
        self.profile_button.clicked.connect(lambda: self.open_profile(self.id))
        self.projectname_combo_box.currentTextChanged.connect(self.refresh_lists)
        self.dashboard_button.clicked.connect(lambda: self.open_dashboard())
        self.kanban_button.clicked.connect(lambda: self.open_kanban())
        self.search_button.clicked.connect(lambda: self.open_search())

        self.darkening_widget = QWidget(self)
        self.darkening_widget.hide()
        self.darkening_widget.setGeometry(0, 0, self.width(), self.height())
        self.darkening_widget.setStyleSheet("background-color: rgba(0, 0, 0, 127);")
        self.profile_window = Profile()
        self.profile_window.hide()

    def open_search(self):
        self.projectname_combo_box.hide()
        self.search_button.setStyleSheet("color: rgb(7, 71, 166); background-color: rgba(255, 255, 255, 0);")
        self.kanban_button.setStyleSheet("color: rgb(0, 0, 0); background-color: rgba(255, 255, 255, 0);")
        self.dashboard_button.setStyleSheet("color: rgb(0, 0, 0); background-color: rgba(255, 255, 255, 0);")
        self.widget.move(self.widget.x(), 171)
        self.stackedWidget.setCurrentIndex(2)

    def open_kanban(self):
        self.widget.move(self.widget.x(), 125)
        self.kanban_button.setStyleSheet("color: rgb(7, 71, 166); background-color: rgba(255, 255, 255, 0);")
        self.search_button.setStyleSheet("color: rgb(0, 0, 0); background-color: rgba(255, 255, 255, 0);")
        self.dashboard_button.setStyleSheet("color: rgb(0, 0, 0); background-color: rgba(255, 255, 255, 0);")
        self.projectname_combo_box.show()
        self.stackedWidget.setCurrentIndex(1)

    def open_dashboard(self):
        self.widget.move(self.widget.x(), 75)
        self.dashboard_button.setStyleSheet("color: rgb(7, 71, 166); background-color: rgba(255, 255, 255, 0);")
        self.search_button.setStyleSheet("color: rgb(0, 0, 0); background-color: rgba(255, 255, 255, 0);")
        self.kanban_button.setStyleSheet("color: rgb(0, 0, 0); background-color: rgba(255, 255, 255, 0);")
        self.projectname_combo_box.hide()

        # Дата в "Месяц, год" формате на русском языке
        self.label_date.setText(datetime.datetime.now().strftime("%B, %Y"))

        # Получаем текущую дату
        today = datetime.date.today()
        # Определяем день недели текущей даты (0 - понедельник, 6 - воскресенье)
        weekday = today.weekday()

        # Вычисляем дату последнего понедельника (начало текущей недели)
        start_of_week = today - datetime.timedelta(days=weekday)

        # Цикл для установки дат в лейблы
        for i in range(7):
            # Вычисляем дату для каждого дня недели
            day = start_of_week + datetime.timedelta(days=i)
            # Получаем число месяца для дня недели
            day_number = day.day

            if day_number == today.day:
                getattr(self, f'label_date_{i+1}').setStyleSheet("background-color: rgb(7, 71, 166); color: rgb(255, 255, 255); border-radius: 9px;")
            else:
                getattr(self, f'label_date_{i+1}').setStyleSheet("color: rgb(0, 0, 0);")

            getattr(self, f'label_date_{i+1}').setAlignment(Qt.AlignCenter)
            
            # Установка числа в соответствующий лейбл
            getattr(self, f'label_date_{i+1}').setText(str(day_number))

        self.stackedWidget.setCurrentIndex(0)

    def cards_area_setter(self):
        self.columns_layout.setAlignment(Qt.AlignLeft)
        self.columns_layout.setSpacing(0)
        self.columns_scrollarea_contents.setLayout(self.columns_layout)
        self.scrollArea_columns.setWidgetResizable(True)

        self.widget_5_on_screen = False

        self.dashboard_tasks_scrollArea.setWidget(self.scrollArea_tasks_dash)
        self.scrollArea_tasks_dash.setLayout(self.tasks_Layout)
        self.dashboard_tasks_scrollArea.setFrameShape(QFrame.NoFrame)
        self.dashboard_tasks_scrollArea.setWidgetResizable(True)


    def widgets_stylesheet_setter(self):
        ...
        # self.left_menu.setStyleSheet("background-color: rgba(235, 235, 235, 255);")
        # self.widget_4.setStyleSheet("")
        # self.widget_4.setObjectName("widget_4")
        # # self.widget_4.setStyleSheet("#widget_4 { background-image: \
        #             # url(" + app_dir + "resources/main_background.jpg);\
        #             # background-repeat: no-repeat; background-size: cover; }")

        # self.widget_6.setStyleSheet("background-color: rgba(235, 235, 235, 220);")
        # self.widget_7.setStyleSheet("background-color: rgba(235, 235, 235, 220);")
        # self.widget_8.setStyleSheet("background-color: rgba(235, 235, 235, 220);")
        # self.widget_5.setStyleSheet("background-color: rgba(235, 235, 235, 220);")

        # self.scrollArea.setStyleSheet("background-color: rgba(235, 235, 235, 0);")
        # self.scrollArea_2.setStyleSheet("background-color: rgba(235, 235, 235, 0);")
        # self.scrollArea_3.setStyleSheet("background-color: rgba(235, 235, 235, 0);")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def update_task_status(self, task_id, status):
        data = {'status': status}
        response = requests.post(f"{url}tasks/{task_id}/updateStatus", json=data)
        if response.status_code == 200:
            # self.refresh_lists()
            ...
        else:
            print(f'Request failed with status code {response.status_code}')

    def card_moved(self, task_id, dropped_in_column):
        print(f'Card {task_id} was dropped in column {dropped_in_column}')
        print(self.drop_areas)

        status = None
        for key, value in self.drop_areas.items():
            if value == dropped_in_column:
                status = key
                break

        print(f'moved card {task_id} to {status} column')

        self.update_task_status(task_id, status)
        self.refresh_lists()

    def close_card_info(self):
        self.group = QtCore.QParallelAnimationGroup()
        self.animation = QtCore.QPropertyAnimation(self.widget_5, b"geometry")
        self.animation.setDuration(150)
        self.animation.setStartValue(QtCore.QRect(990, 0, self.widget_5.width(), self.widget_5.height()))
        self.widget_5.show()
        self.widget_5_on_screen = True
        self.animation.setEndValue(QtCore.QRect(1350, 0, self.widget_5.width(), self.widget_5.height()))
        self.delete_task_button.disconnect()
        self.widget_5_on_screen = False

        self.group.addAnimation(self.animation)
        self.group.start()

    def show_card_info(self, card = None, task_id = None, page = None):
        if page == "dashboard":
            self.open_kanban()

        try:
            self.delete_task_button.disconnect()
        except TypeError:
            pass
        
        empl_id = None

        try:
            self.delete_task_button.disconnect()
        except TypeError:
            pass

        self.delete_task_button.clicked.connect(lambda: self.delete_task(task_id))

        try:
            self.User_task_worker.clicked.disconnect()
        except TypeError:
            pass
        
        if card is not None:
            task_id = card.task_id

        self.project_name_task_id.setText(self.projectname_combo_box.currentText() \
                                          + ' / task-' + task_id)

        response = requests.get(url + "tasks/" + task_id)

        if response.status_code == 200:
            data = response.json()
            data = data['task']
            # self.project_name.setText(self.projectname_combo_box.currentText() + ' / task-' + data['id'])
            self.task_name.setText(data['name'])
            self.descr_2.setPlainText(data['descr'])
            self.task_status.setText(data['status'])
            date = data['date'].split('T')
            self.task_date.setText(date[0] + " " + date[1][:-1])
            empl_id = data['empl_id']
        else:
            print(f'Request failed with status code {response.status_code}')

        self.left_button.clicked.connect(lambda: self.move_task_button(task_id, self.task_status.text(), 'left'))
        self.right_button.clicked.connect(lambda: self.move_task_button(task_id, self.task_status.text(), 'right'))

        if empl_id != '':
            response = requests.get(url + "profile/" + str(empl_id))

            if response.status_code == 200:
                data = response.json()
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
            self.animation.setStartValue(QtCore.QRect(1350, 0, self.widget_5.width(), self.widget_5.height()))
            self.widget_5.show()
            self.widget_5_on_screen = True
            self.animation.setEndValue(QtCore.QRect(990, 0, self.widget_5.width(), self.widget_5.height()))

            self.group = QtCore.QParallelAnimationGroup()
            self.group.addAnimation(self.animation)
            self.group.start()

    def move_task_button(self, task_id, status, direction):
        status_map = {i+1: column for i, column in enumerate(self.columns.keys())}

        print(status_map)
        if direction == 'left':
            ...

        data = {'status': status}
        response = requests.post(f"{url}tasks/{task_id}/updateStatus", json=data)
        if response.status_code == 200:
            print(response.json())
            self.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

    def delete_task(self, task_id):
        response = requests.delete(url + "tasks/" + task_id)

        if response.status_code == 200:
            print(response.json())
            self.close_card_info()
            self.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

    def assign_to_task(self, id, task_id):
        response = requests.post(url + "tasks/" + task_id + "/assign/" + "?empl_id=" + str(id))

        if response.status_code == 200:
            print(response.json())
            self.show_card_info(task_id=task_id)
            self.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

    def open_profile(self, id):
        self.profile_window.show()
        self.darkening_widget.show()

        response = requests.get(url + "profile/" + str(id))

        if response.status_code == 200:
            data = response.json()
            data = data['user']
            self.profile_window.profileName.setText(data['name'])
            self.profile_window.profileJobTitle.setText(data['role']) 
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
        print('REFRESHING LISTS')
        # query for tasks of project
        if self.projectname_combo_box.currentIndex() != -1:
            self.project_name = self.projectname_combo_box.currentText()
            self.project_id = self.projects[self.projectname_combo_box.currentIndex()]
            response = requests.get(url+ "projects/" + self.project_id + "/tasks")

            data = {}

            self.columns = {}
            self.drop_areas = {}

            for column in self.columns_layout.children():
                Column.clear(column)
            self.delete_columns()

            self.scrollArea_columns.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scrollArea_columns.horizontalScrollBar().setFocusPolicy(Qt.StrongFocus)

            if response.status_code == 200:
                data = response.json()
                if data['columns'] != None:
                    columns_string = data['columns'][0]
                    columns_list = columns_string[1:-1].split(',')
                    columns_list = [column.strip()[1:-1] if column.strip().startswith('"') else column.strip() for column in columns_list]

                for column in columns_list:
                    self.columns[column] = Column(column, self.project_id, self)
                    self.columns[column].add_task_adder()
                    self.columns_layout.addWidget(self.columns[column])
                    self.columns_layout.update()
                    self.columns_scrollarea_contents.updateGeometry()
                    self.columns_scrollarea_contents.adjustSize()
                    self.scrollArea_columns.update()
                    self.drop_areas[column] = self.columns[column].scroll_content


                if data['tasks'] != None:
                    for data in data['tasks']:
                        column = data['status']
                        self.columns[column].add_card(data['name'], data['status'], data['id'], data['avatar'], self)
                        self.tasks_Layout.update()
                        self.scrollArea_tasks_dash.adjustSize()
                        self.scrollArea_tasks_dash.update()

            else:
                print(f'Request failed with status code {response.status_code}')

            # for column in self.columns.values():
            #     self.columns_layout.addWidget(column)
            #     self.columns_layout.update()
            #     self.columns_scrollarea_contents.updateGeometry()
            #     self.columns_scrollarea_contents.adjustSize()
            #     self.scrollArea_columns.update()
            #     self.scrollArea_columns.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            #     self.scrollArea_columns.horizontalScrollBar().setFocusPolicy(Qt.StrongFocus)
            #     self.scrollArea_columns.horizontalScrollBar().setValue(self.scrollArea_columns.horizontalScrollBar().maximum())
            #     self.drop_areas[column.name] = column.scroll_content

            for column in self.columns.values():
                column.add_spacer()

            new_column = NewColumn()
            self.columns_layout.addWidget(new_column)
            new_column.create_column_button.clicked.connect(lambda: self.create_column(self.project_id))
        self.tasks_Layout.update()

    def delete_columns(self):
        for i in reversed(range(self.columns_layout.count())):
            item = self.columns_layout.itemAt(i)

            self.columns_layout.removeItem(item)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                widget.setParent(None)
                self.drop_areas = {}
                self.columns = {}

    def create_column(self, project_id):
        data = {
            'name': 'New column'
        }

        response = requests.post(f"{url}projects/{project_id}/column", json=data)

        if response.status_code == 200:
            print('Creating new column')
            self.delete_columns()
            self.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

class Column(QWidget):
    def __init__(self, name, project_id, MainWin = None):
        super().__init__()

        uic.loadUi(app_dir + 'ui/column.ui', self)

        self.name = name
        self.project_id = project_id
        self._window = MainWin

        self.column_name.setText(name)

        self.cards = []

        self.scroll_content = DropArea()
        # self.drop_areas.append(self.scroll_content)
        self.scroll_content.card_moved_signal.moved.connect(self.card_moved)
        self.cards_layout = QGridLayout()
        self.scroll_content.setLayout(self.cards_layout)
        self.scrollArea.setWidget(self.scroll_content)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scroll_content.setAcceptDrops(True)

        self.del_column_button.clicked.connect(lambda: self.delete_column(self.project_id, self.name))
        self.column_name.returnPressed.connect(lambda: self.rename_column(self.project_id, self.name, self.column_name.text()))

    def rename_column(self, project_id, column_name, new_name):
        if column_name == new_name:
            return
        
        data = {
            'old_name': column_name,
            'new_name': new_name
        }

        response = requests.post(f"{url}projects/{project_id}/column/update", json=data)
        if response.status_code == 200:
            print(f'Renaming column {column_name} to {new_name}')
            self.name = new_name
            self._window.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

    def delete_column(self, project_id, column_name):
        data = {
            'name': column_name,
        }

        response = requests.delete(f"{url}projects/{project_id}/column", json=data)

        if response.status_code == 200:
            self._window.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

    def add_card(self, name, status, task_id, avatar = None, MainWin = None):
        self._window = MainWin
        card = Card(name, status, task_id, avatar)
        self.cards.append(card)
        self.cards_layout.addWidget(card, self.cards_layout.rowCount(), 0)
        card.show()
        self.scroll_content.updateGeometry()
        self.scroll_content.adjustSize()
        self.cards_layout.update()
        self.scrollArea.update()

        card_dashboard = TaskDashboard(name, status, card)
        MainWin.tasks_Layout.addWidget(card_dashboard)
        MainWin.tasks_Layout.update()
        MainWin.scrollArea_tasks_dash.adjustSize()
        MainWin.scrollArea_tasks_dash.update()

        card_dashboard.task_open_dash.clicked.connect(lambda: MainWin.show_card_info(card = card, task_id=task_id, page = "dashboard"))
        card.clicked.connect(lambda: MainWin.show_card_info(card = card, task_id=task_id, page = "kanban"))

    def card_moved(self, task_id, dropped_in_column):
        self._window.card_moved(task_id, dropped_in_column)

    def add_task_adder(self):
        task_adder = NewTask()
        self.cards_layout.addWidget(task_adder, self.cards_layout.rowCount(), 0)
        task_adder.lower()
        task_adder.new_task_button.clicked.connect(lambda: self.new_task(task_adder))

    def new_task(self, task_adder):
        task_adder.new_task_button.hide()
        task_adder.new_task_name.show()

        try:
            task_adder.new_task_name.returnPressed.disconnect()
        except TypeError:
            pass

        task_adder.new_task_name.returnPressed.connect(lambda: self.add_new_task(task_adder.new_task_name.text(), self.name))

    def add_new_task(self, name, column):
        data = {
            'name': name,
            'status': column,
            'projectId': int(self.project_id),
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        response = requests.post(url+ "tasks/new", json=data)

        if response.status_code == 200:
            self._window.delete_columns()
            self._window.refresh_lists()
        else:
            print(f'Request failed with status code {response.status_code}')

    def add_spacer(self):
        self.cards_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def clear(self):
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)

            self.cards_layout.removeItem(item)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                widget.setParent(None)
        
class SignIn(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(app_dir + 'ui/sign_in.ui', self)
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
        response = requests.get(url + "auth/register/check/" + login)
        if response.status_code == 200:
            data = response.json()
            print(data)
            self.password = self.pass_input_2.text()
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
                data = {'name': self.name_input.text(),
                        'login': self.login_input.text(), 
                        'password': self.password, 
                        'role': 'employee', 
                        'code': self.empl_code_input.text()}
                response = requests.post(url + "auth/register", json=data)
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

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    locale.setlocale(locale.LC_TIME, 'Russian_Russia')
    app.setStyleSheet("""
    QScrollBar:vertical {
        background: rgba(128, 128, 128, 0);
        width: 8px;
    }

    QScrollBar::handle:vertical {
        background: rgba(7, 71, 166, 255);
        border-radius: 4px;
        min-height: 20px;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
    }

    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        width: 0px; height: 0px;
        background: none;
    }
                      
    QScrollBar:horizontal {
        background: rgba(128, 128, 128, 0);
        height: 8px;
    }
                      
    QScrollBar::handle:horizontal {
        background: rgba(7, 71, 166, 255);
        border-radius: 4px;
        min-width: 20px;
    }
                      
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        background: none;
    }
                      
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        width: 0px; height: 0px;
        background: none;
    }
    """)
    fontId = QtGui.QFontDatabase.addApplicationFont(app_dir + "resources/Rubik-Regular.ttf")
    if fontId != -1:
        fontFamilies = QtGui.QFontDatabase.applicationFontFamilies(fontId)
        if fontFamilies:
            font = QtGui.QFont(fontFamilies[0], 10)
            app.setFont(font)
    else:
        print("Failed to load font")

    window = Login()
    window.show()
    sys.exit(app.exec_())