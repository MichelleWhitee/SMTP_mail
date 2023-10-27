from socket import *

import ssl
import base64

import re
import sys

from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QLineEdit, QMessageBox

uiMainWindow, QMainWindow = uic.loadUiType("ui/mainWindow.ui")
regex = r'\b[A-Za-z0-9]+@[A-Za-z0-9]+\.[A-Z|a-z]{2,7}\b'

class MainWindow(QMainWindow, uiMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setFixedSize(603, 399)
        self.passwd_lineEdit.setEchoMode(QLineEdit.Password)
        self.setWindowIcon(QtGui.QIcon('YoumuAava.ico'))

        #Сокет
        self.socket = None
        self.context = None
        self.sslSocket = None

        #Кнопки
        self.sendButton.clicked.connect(self.send_clicked)
        self.connectButton.clicked.connect(self.connect_clicked)

    def closeEvent(self, event):
        close = QMessageBox(self)
        close.setWindowTitle("Выход")
        close.setIcon(QMessageBox.Warning)
        close.setText("Выйти ?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()

        if close == QMessageBox.Yes:
            event.accept()

            print("Quit")
            self.quit()

        else:
            event.ignore()

    def initSocket(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.settimeout(5)

        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

    def connect_clicked(self):
        self.statusLabel.setText("N/A")
        self.statusLabel.setStyleSheet('color: black')

        self.initSocket()

        smtpSrv = self.smtp_combo.currentText()
        print(smtpSrv)

        try:
            self.sslSocket = self.context.wrap_socket(self.socket, server_hostname=smtpSrv)
            self.sslSocket.connect((smtpSrv, 465))

            self.ehlo()
            self.login(self.login_lineEdit.text(), self.passwd_lineEdit.text())
            response = self.sendMsg(f"MAIL FROM:<{self.login_lineEdit.text()}>")

            if response.startswith("535"):
                raise Exception("Auth not accepted")

            self.statusLabel.setText("OK")
            self.statusLabel.setStyleSheet('color: green')

            self.from_lineEdit.setText(self.login_lineEdit.text())

            messageBox = QMessageBox(self)
            messageBox.setWindowTitle("Успех")
            messageBox.setIcon(QMessageBox.Information)
            messageBox.setText("Соединение установлено!")
            messageBox.setDefaultButton(QMessageBox.Ok)
            messageBox.exec_()

        except BaseException:
            self.statusLabel.setText("ERR")
            self.statusLabel.setStyleSheet('color: red')

            messageBox = QMessageBox(self)
            messageBox.setWindowTitle("Неудача")
            messageBox.setIcon(QMessageBox.Warning)
            messageBox.setText("Не удалось установить соединение")
            messageBox.setDefaultButton(QMessageBox.Ok)
            messageBox.exec_()

    def checkEmail(self, email):
        if re.fullmatch(regex, email):
            return True
        else:
            return False

    def send_clicked(self):
        if self.statusLabel.text() == "OK":
            if self.to_lineEdit.text() == '':
                messageBox = QMessageBox(self)
                messageBox.setWindowTitle("Неудача")
                messageBox.setIcon(QMessageBox.Warning)
                messageBox.setText('Поле "Кому" пустое')
                messageBox.setDefaultButton(QMessageBox.Ok)
                messageBox.exec_()

            else:
                valid = self.checkEmail(self.to_lineEdit.text())
                print(valid)
                if not valid:
                    messageBox = QMessageBox(self)
                    messageBox.setWindowTitle("Неудача")
                    messageBox.setIcon(QMessageBox.Warning)
                    messageBox.setText('Email получателя имеет неправильный формат')
                    messageBox.setDefaultButton(QMessageBox.Ok)
                    messageBox.exec_()

                else:
                    self.sendMail(self.from_lineEdit.text(), self.to_lineEdit.text(), self.subject_lineEdit.text(), self.textEdit.toPlainText())
                    print("OK")

                    messageBox = QMessageBox(self)
                    messageBox.setWindowTitle("Успех")
                    messageBox.setIcon(QMessageBox.Information)
                    messageBox.setText("Сообщение отправлено!")
                    messageBox.setDefaultButton(QMessageBox.Ok)
                    messageBox.exec_()

        else:
            print("ERR")

            messageBox = QMessageBox(self)
            messageBox.setWindowTitle("Неудача")
            messageBox.setIcon(QMessageBox.Warning)
            messageBox.setText("Не удалось отправить сообщение")
            messageBox.setDefaultButton(QMessageBox.Ok)
            messageBox.exec_()

    def createAuthMsg(self, user, passwd):
        str = "\x00" + user + "\x00" + passwd
        base64_str = base64.b64encode(str.encode())

        return "AUTH PLAIN " + base64_str.decode()

    def recvMsg(self):
        try:
            return self.sslSocket.recv(2048).decode()

        except timeout:
            print("Message recv timed out")

    def sendMsg(self, message, returnMsg=True):
        if message == ".":
            self.sslSocket.send(f"\r\n{message}\r\n".encode())
        else:
            self.sslSocket.send(f"{message}\r\n".encode())

        if returnMsg:
            recv = self.recvMsg()
            print(recv)

            return recv

    def ehlo(self):
        return self.sendMsg(f"EHLO {self.smtp_combo.currentText()}")

    def login(self, user, passwd):
        authMsg = self.createAuthMsg(user, passwd)
        self.sendMsg(authMsg)

    def quit(self):
        if self.socket:
            self.sendMsg("QUIT")
            self.sslSocket.close()
        else:
            pass

    def sendMail(self, sender, receiver, subject, msg):
        self.sendMsg(f"MAIL FROM:<{sender}>")
        self.sendMsg(f"RCPT TO:<{receiver}>")
        self.sendMsg(f"DATA")
        self.sendMsg(f"SUBJECT: {subject}\n")
        self.sendMsg(msg, returnMsg=False)
        self.sendMsg(".")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())