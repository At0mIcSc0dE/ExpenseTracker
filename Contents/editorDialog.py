# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\dialogEditor.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Editor(object):
    def setupUi(self, Editor):
        Editor.setObjectName("Editor")
        Editor.resize(800, 400)
        self.expNameTxtEdit = QtWidgets.QTextEdit(Editor)
        self.expNameTxtEdit.setGeometry(QtCore.QRect(60, 110, 220, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.expNameTxtEdit.setFont(font)
        self.expNameTxtEdit.setObjectName("expNameTxtEdit")
        self.expPriceTxtEdit = QtWidgets.QTextEdit(Editor)
        self.expPriceTxtEdit.setGeometry(QtCore.QRect(300, 110, 220, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.expPriceTxtEdit.setFont(font)
        self.expPriceTxtEdit.setObjectName("expPriceTxtEdit")
        self.expInfoEdit = QtWidgets.QPlainTextEdit(Editor)
        self.expInfoEdit.setGeometry(QtCore.QRect(60, 160, 460, 180))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.expInfoEdit.setFont(font)
        self.expInfoEdit.setObjectName("expInfoEdit")
        self.lblDateEdit = QtWidgets.QLabel(Editor)
        self.lblDateEdit.setGeometry(QtCore.QRect(60, 10, 550, 40))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.lblDateEdit.setFont(font)
        self.lblDateEdit.setObjectName("lblDateEdit")
        self.btnOkEdit = QtWidgets.QPushButton(Editor)
        self.btnOkEdit.setGeometry(QtCore.QRect(590, 320, 90, 35))
        self.btnOkEdit.setObjectName("btnOkEdit")
        self.btnCancelEdit = QtWidgets.QPushButton(Editor)
        self.btnCancelEdit.setGeometry(QtCore.QRect(700, 320, 90, 35))
        self.btnCancelEdit.setObjectName("btnCancelEdit")

        self.retranslateUi(Editor)
        QtCore.QMetaObject.connectSlotsByName(Editor)

    def retranslateUi(self, Editor):
        _translate = QtCore.QCoreApplication.translate
        Editor.setWindowTitle(_translate("Editor", "Editor"))
        self.lblDateEdit.setText(_translate("Editor", "TextLabel"))
        self.btnOkEdit.setText(_translate("Editor", "Ok"))
        self.btnCancelEdit.setText(_translate("Editor", "Cancel"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Editor = QtWidgets.QDialog()
    ui = Ui_Editor()
    ui.setupUi(Editor)
    Editor.show()
    sys.exit(app.exec_())
