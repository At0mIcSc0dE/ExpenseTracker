# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\userEditor2.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_main(object):
    def setupUi(self, main):
        main.setObjectName("main")
        main.resize(730, 140)
        self.lblUsername = QtWidgets.QLabel(main)
        self.lblUsername.setGeometry(QtCore.QRect(40, 20, 200, 20))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.lblUsername.setFont(font)
        self.lblUsername.setObjectName("lblUsername")
        self.lblPassword = QtWidgets.QLabel(main)
        self.lblPassword.setGeometry(QtCore.QRect(290, 20, 200, 20))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.lblPassword.setFont(font)
        self.lblPassword.setObjectName("lblPassword")
        self.lblBalance = QtWidgets.QLabel(main)
        self.lblBalance.setGeometry(QtCore.QRect(540, 20, 200, 20))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.lblBalance.setFont(font)
        self.lblBalance.setObjectName("lblBalance")
        self.usernameTxt = QtWidgets.QLineEdit(main)
        self.usernameTxt.setGeometry(QtCore.QRect(40, 50, 170, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.usernameTxt.setFont(font)
        self.usernameTxt.setObjectName("usernameTxt")
        self.pwTxt = QtWidgets.QLineEdit(main)
        self.pwTxt.setGeometry(QtCore.QRect(290, 50, 170, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.pwTxt.setFont(font)
        self.pwTxt.setObjectName("pwTxt")
        self.balanceTxt = QtWidgets.QLineEdit(main)
        self.balanceTxt.setGeometry(QtCore.QRect(540, 50, 170, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.balanceTxt.setFont(font)
        self.balanceTxt.setObjectName("balanceTxt")
        self.updateBtn = QtWidgets.QPushButton(main)
        self.updateBtn.setGeometry(QtCore.QRect(637, 110, 75, 23))
        self.updateBtn.setObjectName("updateBtn")
        self.cancelBtn = QtWidgets.QPushButton(main)
        self.cancelBtn.setGeometry(QtCore.QRect(540, 110, 75, 23))
        self.cancelBtn.setObjectName("cancelBtn")

        self.retranslateUi(main)
        QtCore.QMetaObject.connectSlotsByName(main)

    def retranslateUi(self, main):
        _translate = QtCore.QCoreApplication.translate
        main.setWindowTitle(_translate("main", "Dialog"))
        self.lblUsername.setText(_translate("main", "Username"))
        self.lblPassword.setText(_translate("main", "Password"))
        self.lblBalance.setText(_translate("main", "Bank Balance"))
        self.usernameTxt.setPlaceholderText(_translate("main", "Username"))
        self.pwTxt.setPlaceholderText(_translate("main", "Pasword"))
        self.balanceTxt.setPlaceholderText(_translate("main", "Balance"))
        self.updateBtn.setText(_translate("main", "Update"))
        self.cancelBtn.setText(_translate("main", "Cancel"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    main = QtWidgets.QDialog()
    ui = Ui_main()
    ui.setupUi(main)
    main.show()
    sys.exit(app.exec_())
