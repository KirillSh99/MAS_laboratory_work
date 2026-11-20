import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from functools import lru_cache
import logging
from logsetup import logcfg

from thespian.actors import ActorSystem

from agents.scene_agent import SceneAgent
from agents.dispatcher_agent import AgentsDispatcher
from agents.messages import Message, MessageType


class RedactorForm(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        logcfg["handlers"]["h1"]["level"] = logging.INFO
        logcfg["handlers"]["h2"]["level"] = logging.INFO
        logcfg["loggers"][""]["level"] = logging.INFO

        self.actor_system = ActorSystem(systemBase="simpleSystemBase", logDefs=logcfg)
        self.scene = self.actor_system.createActor(SceneAgent)
        self.dispatcher = self.actor_system.createActor(AgentsDispatcher)
        init_dispatcher_data = {"scene_agent_address": self.scene}
        self.actor_system.tell(
            self.dispatcher, Message(MessageType.INIT_DISPATCHER, init_dispatcher_data)
        )

        self.main_layout.addWidget(QtWidgets.QLabel("Введите промт:"))
        self.name_line = QtWidgets.QLineEdit()
        self.main_layout.addWidget(self.name_line)

        self.textEdit = QtWidgets.QTextEdit()
        self.textEdit.setMinimumHeight(200)
        self.main_layout.addWidget(self.textEdit)

        self.resultLabel = QtWidgets.QLabel("Ожидание расчета...")
        self.main_layout.addWidget(self.resultLabel)

        self.calculateButton = QtWidgets.QPushButton("Дать оценку состояния")
        self.main_layout.addWidget(self.calculateButton)

        self.calculateButton.clicked.connect(self.predict_state)

    @QtCore.pyqtSlot()
    def predict_state(self):
        text = self.name_line.text().strip()

        if len(text) < 6:
            print("Слишком короткий запрос!")
            return

        request_dispatcher_data = {"request_user": text}
        self.actor_system.tell(
            self.dispatcher, Message(MessageType.REQUEST_USER, request_dispatcher_data)
        )

        with open("result_data/text.txt", "r", encoding="utf-8") as f:
            finish_text = f.read()

        with open("result_data/mark.txt", "r", encoding="utf-8") as f:
            mark = f.read()

        self.textEdit.setPlainText(f"{finish_text}")
        self.resultLabel.setText(f"Оценка эксперта: {mark}")

    @lru_cache(maxsize=None)
    def maps(self):
        desktop = QtWidgets.QApplication.desktop()
        x = (desktop.width() - self.width()) // 2
        y = (desktop.height() - self.height()) // 2
        self.move(x, y)


if __name__ == '__main__':
    app = QtWidgets. QApplication(sys. argv)
    window = RedactorForm()

    window.resize(700, 500)
    window. setWindowTitle('Redactor System')
    window.maps()

    window. show()
    sys. exit(app. exec_())