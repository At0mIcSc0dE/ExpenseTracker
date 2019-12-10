"""
This programm will allow you to enter your monthly budget. Every expense will be stored and removed from it.
You will be able to show a graph showing if your expenses increased or decreased (30 days, 12 months).
The GUI will have a list of all of your expenses on the left, to which you can add using a text box right next to it.
You will also be able to enter monthly expenses that are always the same so these will be automatically subtracted from
your budget.
All of this will be stored in a databasein the chosen directory, which you will be able to select
when you first open the program. I will also add a way to change the path and move all files from the previous one
to the newer one.
"""


from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from os import execl, mkdir
from os.path import exists
from shutil import move
from time import time
from datetime import datetime
from sqlite3 import connect
from matplotlib.pyplot import plot, legend, title, xlabel, ylabel, show
from concurrent.futures import ThreadPoolExecutor
from string import ascii_lowercase, ascii_uppercase

global path, expenseDtbPath
DEFAULTFONT = 'MS Shell Dlg 2'
DEFAULTPLAINTEXT = 'Write more info about your expense here...'
DELCMD = 'focus1'


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, mainWindowTitle: str = 'MainWindow',
                 application: QtWidgets.QApplication = None, minsizeX: int = 0, minsizeY: int = 0,
                 maxsizeX: int = 1920, maxsizeY: int = 1080, *args, **kwargs) -> None:
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = application
        self.setObjectName(mainWindowTitle)
        self.setWindowTitle(mainWindowTitle)
        self.resize(1200, 600)
        self.setMinimumSize(QtCore.QSize(minsizeX, minsizeY))
        self.setMaximumSize(QtCore.QSize(maxsizeX, maxsizeY))

    def closeEvent(self, event):
        self.app.closeAllWindows()


class Editor(QtWidgets.QMessageBox):
    """The editor to edit the selected entry"""

    def __init__(self) -> None:
        super().__init__()
        self.editWin = QtWidgets.QDialog()
        self.editWin.resize(800, 400)
        self.editWin.setWindowTitle('Editor')

        self.editWin.setObjectName("Editor")
        self.expNameTxtEdit = TextBox(self.editWin, x=60, y=110, width=220, height=40, fontsize=16)
        self.expNameTxtEdit.setGeometry(QtCore.QRect(60, 110, 220, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.expNameTxtEdit.setFont(font)
        self.expNameTxtEdit.setObjectName("expNameTxtEdit")
        self.expPriceTxtEdit = TextBox(self.editWin, x=300, y=110, width=220, height=40, fontsize=16)
        self.expPriceTxtEdit.setGeometry(QtCore.QRect(300, 110, 220, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.expPriceTxtEdit.setFont(font)
        self.expPriceTxtEdit.setObjectName("expPriceTxtEdit")
        self.expInfoEdit = PlainText(self.editWin, x=60, y=160, width=460, height=180, fontsize=11)
        self.expInfoEdit.setGeometry(QtCore.QRect(60, 160, 460, 180))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.expInfoEdit.setFont(font)
        self.expInfoEdit.setObjectName("expInfoEdit")
        self.lblDateEdit = Label(self.editWin, x=60, y=10, width=550, height=40, fontsize=18)
        self.lblDateEdit.setGeometry(QtCore.QRect(60, 10, 550, 40))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.lblDateEdit.setFont(font)
        self.lblDateEdit.setObjectName("lblDateEdit")
        self.btnOkEdit = Button(self.editWin, text='Ok', x=590, y=320, width=90, height=35, key='Return',
                                command=self.apply)
        self.btnOkEdit.setGeometry(QtCore.QRect(590, 320, 90, 35))
        self.btnOkEdit.setObjectName("btnOkEdit")
        self.btnCancelEdit = Button(self.editWin, text='Cancel', x=700, y=320, width=90, height=35, command=self.close)
        self.btnCancelEdit.setGeometry(QtCore.QRect(700, 320, 90, 35))
        self.btnCancelEdit.setObjectName("btnCancelEdit")

        self.retranslateUi(self.editWin)
        QtCore.QMetaObject.connectSlotsByName(self.editWin)

    def retranslateUi(self, Editor) -> None:
        _translate = QtCore.QCoreApplication.translate
        Editor.setWindowTitle(_translate("Editor", "Editor"))
        self.lblDateEdit.setText(_translate("Editor", "TextLabel"))
        self.btnOkEdit.setText(_translate("Editor", "Ok"))
        self.btnCancelEdit.setText(_translate("Editor", "Cancel"))

    def apply(self) -> None:
        """takes your selection, and the textbox elements!"""

        global editWin, currselectOnceEdit, currselectMonthEdit
        name = editWin.expNameTxtEdit.getText()
        price = editWin.expPriceTxtEdit.getText()
        info = editWin.expInfoEdit.getText()

        try:
            price = float(price)
        except ValueError:
            msgbox = QtWidgets.QMessageBox.critical(None, 'Invalid Input', 'Invalid Input, try again',
                                                    QtWidgets.QMessageBox.Ok)
            if msgbox == QtWidgets.QMessageBox.Ok:
                return
        except TypeError:
            pass

        if DELCMD == 'focus1' and currselectOnceEdit != -1:
            lstbox.update(currselectOnceEdit, name, price)
            dtbOnce.update(currselectOnceEdit, name, price, info)
            updateLbls(1)
            self.editWin.destroy()
        elif DELCMD == 'focus2' and currselectMonthEdit != -1:
            lstboxMonth.update(currselectMonthEdit, name, price)
            dtbMonth.update(currselectMonthEdit, name, price, info)
            updateLbls(1)
            self.editWin.destroy()

    def close(self) -> None:

        """Closes the editwindow"""

        self.editWin.destroy()

    def show(self) -> None:
        self.editWin.show()


class DataBase:
    """Database class, no inheritance"""

    def __init__(self, databasePath: str, table: str) -> None:
        """Will create table if it does not exist.
        Args: your databasePath and the name of your table"""

        self.table = table
        self.conn = connect(databasePath)
        self.cursor = self.conn.cursor()

        self.cursor.execute('CREATE TABLE IF NOT EXISTS ' + self.table + '''(
                            ID INTEGER,
                            Expense TEXT,
                            Price INTEGER,
                            MoreInfo TEXT,
                            Day INTEGER,
                            Month INTEGER,
                            Year INTEGER,
                            PRIMARY KEY(ID)
                            )''')

    def getRowValuesById(self, rowid: int, *elemIndex: int):
        """Enter the ID by which the record is stored and the function will return you a list if you want multiple elements
        of one record or it will return the entire row if no elemIndex given."""

        self.cursor.execute('SELECT ID FROM ' + self.table)
        rws = self.cursor.fetchall()
        rws = rws[::-1]
        r = rws[rowid][0]
        self.cursor.execute('SELECT * FROM ' + self.table + ' WHERE ID = ?', (r,))
        row = self.cursor.fetchall()
        returns = []
        for arg in elemIndex:
            returns.append(row[0][arg])
        return returns if returns != [] else row[0]

    def getAllRecords(self) -> list:
        """Returns a list of tuples containing all the elements of a dtb"""

        self.cursor.execute('SELECT * FROM ' + self.table)
        return self.cursor.fetchall()

    def dataEntry(self, price: float, exp: str, moreInfo: str = None):
        """Enters data into a database"""

        day, month, year = str(datetime.fromtimestamp(time()).strftime('%d-%m-%Y')).split('-')
        self.cursor.execute(
                'INSERT INTO ' + self.table + ' (Expense, Price, MoreInfo, Day, Month, Year) VALUES (?, ?, ?, ?, ?, ?)',
                (exp, price, moreInfo.rstrip('\n').strip(DEFAULTPLAINTEXT), day, month, year))
        self.conn.commit()

    def clearDtb(self) -> None:
        """Clears the database of all records. Also updates labels"""

        self.cursor.execute('DELETE FROM ' + self.table)
        self.conn.commit()

    def removeFromDtb(self, currselect: int) -> None:
        """Removes item with the reversed rowid from listbox"""

        self.cursor.execute('SELECT ID FROM ' + self.table)
        rws = self.cursor.fetchall()
        rws = rws[::-1]
        rw = rws[currselect]
        self.cursor.execute('DELETE FROM ' + self.table + ' WHERE ID = ?', (str(rw[0]),))
        self.conn.commit()
        self.updateId()

    def updateId(self) -> None:
        """Updates IDs because if you delete ID=1 then ID=2 will then be the first element in the dtb"""

        self.cursor.execute('SELECT * FROM ' + self.table)
        rows = self.cursor.fetchall()

        r = []
        for row in range(len(rows)):
            r.append(row + 1)
        with ThreadPoolExecutor() as executor:
            executor.map(self._update, r, rows)

    def _update(self, index: list, row: list) -> None:
        self.cursor.execute('UPDATE ' + self.table + ' SET ID = ? WHERE ID = ?', (index[0], row[0]))
        self.conn.commit()

    def cal(self) -> float:
        """Calculation of totalExpenses"""

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Critical)
        msgbox.setWindowTitle('Invalid Input')
        msgbox.setText('Invalid Input, try again!')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        self.cursor.execute('SELECT Price FROM ' + self.table)
        expenses = self.cursor.fetchall()
        totalExpense = 0
        for expense in expenses:
            while True:
                try:
                    expense = str(expense[0])
                    for L, l in zip(ascii_uppercase, ascii_lowercase):
                        expense = expense.strip(L)
                        expense = expense.strip(l)
                    totalExpense += float(expense)
                    break
                except ValueError:
                    msgbox.show()
        return totalExpense

    def readFromDtb(self) -> list:
        """Reads Expense, Price, MoreInfo from Database"""

        self.cursor.execute('SELECT Expense, Price, MoreInfo FROM ' + self.table)
        return self.cursor.fetchall()

    def update(self, rowid: int, name: str, price: float, moreInfo: str) -> None:
        """Updates one record with the rowid and replaces the name, price and moreInfo with the passed parameters"""

        self.cursor.execute('SELECT ID FROM ' + self.table)
        ids = self.cursor.fetchall()
        ids = ids[::-1]
        ids = ids[rowid][0]
        self.cursor.execute('UPDATE ' + self.table + ' SET Expense = ?, Price = ?, MoreInfo = ? WHERE ID = ?',
                            (name, price, moreInfo, ids))
        self.conn.commit()


class Button(QtWidgets.QPushButton):
    """Simplyfied button class for PyQt5.QtWindgets.QPushButton"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: str = None, x: int = 0, y: int = 0, width: int = 75,
                 height: int = 23, font: str = 'MS Shell Dlg 2', fontsize: int = 8,
                 command: callable = None, key: str = '') -> None:
        super().__init__()

        self._text = text
        self.command = command
        self.button = QtWidgets.QPushButton(win)
        self.button.setGeometry(QtCore.QRect(x, y, width, height))
        self.button.setText(self.text)
        if self.command:
            self.button.clicked.connect(self.command)
        self.font = QtGui.QFont()
        self.font.setPointSize(fontsize)
        self.font.setFamily(font)
        self.button.setFont(self.font)
        self.dialogs = []

        if key != '':
            self.button.setShortcut(key)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value) -> None:
        self._text = value
        self.button.setText(self._text)


class TextBox(QtWidgets.QLineEdit):
    """Simplified class of PyQt5.QtWidgets.QLineEdit TextBox"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: str = '', x: int = 0, y: int = 0, width: int = 75,
                 height: int = 23,
                 font: str = DEFAULTFONT, fontsize: int = 8) -> None:
        super().__init__()
        self._text = text
        self.textbox = QtWidgets.QLineEdit(win)
        self.textbox.setGeometry(QtCore.QRect(x, y, width, height))
        self.textbox.setText(self.text)
        self.font = QtGui.QFont()
        self.font.setFamily(font)
        self.font.setPointSize(fontsize)
        self.textbox.setFont(self.font)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.textbox.setText(value)

    def getText(self) -> str:
        """:returns the current text of a QLineEdit"""

        return str(self.textbox.text())


class ListBox(QtWidgets.QListWidget, QtWidgets.QWidget):
    """Simplified class for PyQt5.QtWidgets.QListWidget ListBox"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), x: int = 0, y: int = 0, width: int = 75, height: int = 23,
                 font: str = DEFAULTFONT, fontsize: int = 8) -> None:

        QtWidgets.QListWidget.__init__(self)
        self.listbox = QtWidgets.QListWidget(win)
        self.listbox.setGeometry(QtCore.QRect(x, y, width, height))
        self.font = QtGui.QFont()
        self.font.setFamily(font)
        self.font.setPointSize(fontsize)
        self.listbox.setFont(self.font)
        self.listbox.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        global DELCMD
        if event.type() == QtCore.QEvent.FocusIn:
            if obj == lstbox.listbox:
                lstboxTakingsMonth.clearFocus()
                lstboxTakingsMonth.clearSelection()
                lstboxMonth.listbox.clearFocus()
                lstboxMonth.listbox.clearSelection()
                lstboxTakings.listbox.clearFocus()
                lstboxTakings.listbox.clearSelection()
                print('focus1')
                DELCMD = 'focus1'
                return True
            elif obj == lstboxMonth.listbox:
                lstboxTakingsMonth.clearFocus()
                lstboxTakingsMonth.clearSelection()
                lstbox.listbox.clearFocus()
                lstbox.listbox.clearSelection()
                lstboxTakings.listbox.clearFocus()
                lstboxTakings.listbox.clearSelection()
                print('focus2')
                DELCMD = 'focus2'
                return True
            elif obj == lstboxTakings.listbox:
                lstboxTakingsMonth.clearFocus()
                lstboxTakingsMonth.clearSelection()
                lstbox.listbox.clearFocus()
                lstbox.listbox.clearSelection()
                lstboxMonth.listbox.clearFocus()
                lstboxMonth.listbox.clearSelection()
                print('focus3')
                DELCMD = 'focus3'
                return True
            elif obj == lstboxTakingsMonth.listbox:
                lstboxTakings.clearFocus()
                lstboxTakings.clearSelection()
                lstbox.listbox.clearFocus()
                lstbox.listbox.clearSelection()
                lstboxMonth.listbox.clearFocus()
                lstboxMonth.listbox.clearSelection()
                print('focus4')
                DELCMD = 'focus4'
                return True
        return False

    def add(self, expenseTime: (str, tuple), txt: str = None, currselect: tuple = None, index: int = 0) -> bool:

        """Adds items into listbox.
        Valid expenseTime: ('dup', 'once'), ('dup', 'month'), 'once', 'month', 'taking'"""

        if isinstance(expenseTime, tuple):
            self.listbox.insert(index, txt)
            name = txt.split(',')[0]
            currency = comboBoxCur.getText().split(' ')[1]
            price = txt.split(' ')[1].split(currency)[0]
            expTime = expenseTime[1]
            moreInfo = ''
            if expenseTime == ('dup', 'once'):
                moreInfo = dtbOnce.getRowValuesById(currselect[0], 3)
            elif expenseTime == ('dup', 'month'):
                moreInfo = dtbMonth.getRowValuesById(currselect[0], 3)
            addListToDtb(float(price), name, expTime, moreInfo)
            return True

        name = expNameTxt.getText()
        price = expPriceTxt.getText()
        moreInfo = expInfo.getText()
        currency = comboBoxCur.getText().split(' ')[1]
        multiplier = expMultiTxt.getText()

        # Check if valid price and multiplier input
        msgbox = QtWidgets.QMessageBox(mainWin)
        msgbox.setWindowTitle('Error')
        msgbox.setIcon(QtWidgets.QMessageBox.Critical)
        msgbox.setGeometry(500, 200, 300, 500)
        try:
            price = float(price)
            multiplier = int(multiplier)
        except:
            msgbox.information(msgbox, 'Invalid Input', 'Invalid Input, try again!')
            return False

        if name and price != '':
            # text = f'{name}, {price}{currency}'
            for i in range(multiplier):
                self.insertItems(0, '{1}, {0:.2f}{2}'.format(price, name, currency))
                addListToDtb(price, name, expenseTime, moreInfo)
                expMultiTxt.text = 1
            return True
        else:
            msgbox.information(msgbox, 'Invalid Input', 'Invalid Input, try again!')
            return False

    def insertItems(self, row: int, *args: str) -> None:
        """Inserts all Items specified as args"""

        for arg in args:
            self.listbox.insertItem(row, arg)

    def curselection(self) -> int:
        """:returns: the current selection of listbox as a rowID"""

        return self.listbox.currentIndex().row()

    def delete(self, rowID: int) -> None:
        """Deletes item with index rowID"""

        self.listbox.takeItem(rowID)

    def update(self, selection: int, name: str, price: float) -> None:
        """Updates listboxselection. Works by deleting the previos entry and replacing it with a new one"""

        self.delete(selection)
        self.insertItems(selection, '{1}, {0:.2f}{2}'.format(float(price), name, comboBoxCur.getText().split(" ")[1]))
        self.listbox.setCurrentRow(selection)


class CheckBox(QtWidgets.QCheckBox, QtWidgets.QAbstractButton):
    """Simplified class for PyQt5.QtWidgets.QCheckBox CheckBox"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: str, command: callable = None, checked: bool = False,
                 x: int = 0, y: int = 0, width:
                 int = 75, height: int = 23, font: str = DEFAULTFONT, fontsize: int = 8) -> None:
        super().__init__()

        self._text = text
        self._command = command
        self.checkbox = QtWidgets.QCheckBox(win)
        self.checkbox.setGeometry(QtCore.QRect(x, y, width, height))
        self.checkbox.setText(self._text)

        self.font = QtGui.QFont()
        self.font.setPointSize(fontsize)
        self.font.setFamily(font)
        self.checkbox.setFont(self.font)
        self.setChecked(checked)
        if self.command:
            self.checkbox.clicked.connect(self.command)

    @property
    def command(self) -> callable:
        return self._command

    @command.setter
    def command(self, func: callable) -> None:
        self._command = func

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text
        self.checkbox.setText(self._text)

    def unckeckAny(self, checked: bool, *chbs: QtWidgets.QCheckBox) -> None:
        """checked: bool should equal True if the checkbox was checked before the click"""

        for chb in chbs:
            if checked:
                self.checkbox.setChecked(False)
                chb.setChecked(True)
            elif not checked:
                self.checkbox.setChecked(True)
                chb.setChecked(False)

    def setChecked(self, value: bool) -> None:
        """Set checked value"""

        self.checkbox.setChecked(value)

    def check(self) -> None:
        """Checkes checkbox"""

        self.setChecked(True)


class ComboBox(QtWidgets.QComboBox):
    """Simplified class of PyQt5.QtWidgets.QComboBox ComboBox"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), x: int = 0, y: int = 0, width: int = 75, height: int = 23,
                 font: str = DEFAULTFONT, fontsize: int = 8) -> None:
        super().__init__()
        self.combobox = QtWidgets.QComboBox(win)
        self.combobox.setGeometry(QtCore.QRect(x, y, width, height))
        self.font = QtGui.QFont()
        self.font.setFamily(font)
        self.font.setPointSize(fontsize)
        self.combobox.setFont(self.font)
        self.combobox.currentTextChanged.connect(self.currentTextChanged)

    def addItems(self, *drops: str) -> None:
        """Adds items with param drops"""

        self.combobox.addItems(drops)

    def getText(self) -> str:
        """:returns the current text of the combobox"""

        return self.combobox.currentText()

    def currentTextChanged(self, p_str: str) -> None:
        """Change event for different selection in combobox"""

        global german, english
        if p_str == 'English':
            changeLanguageEnglish(english)
            german = False
            english = True
        elif p_str == 'Deutsch':
            changeLanguageGerman(german)
            german = True
            english = False


class PlainText(QtWidgets.QPlainTextEdit):
    """Simplified class of PyQt5.QtWidgets.QPlainTextEdit PlainText"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: str = '', x: int = 0, y: int = 0, width: int = 75,
                 height: int = 23,
                 font: str = DEFAULTFONT, fontsize: int = 8) -> None:
        super().__init__()
        self._text = text
        self.plain = QtWidgets.QPlainTextEdit(win)
        self.plain.setGeometry(QtCore.QRect(x, y, width, height))
        self.plain.insertPlainText(self.text)
        self.font = QtGui.QFont()
        self.font.setPointSize(fontsize)
        self.font.setFamily(font)
        self.plain.setFont(self.font)
        self.plain.installEventFilter(self)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.plain.setPlainText(value)

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QtCore.QEvent.FocusIn:
            if self.text == DEFAULTPLAINTEXT:
                self.text = ''
                return True
        return False

    def getText(self) -> str:
        """:returns the current text of the plain"""

        return self.plain.toPlainText()


class Label(QtWidgets.QLabel):
    """Simplified class for PyQt5.QtWidgets.QLabel Label"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: str = None, x: int = 0, y: int = 0, width: int = 75,
                 height: int = 23, font: str = 'MS Shell Dlg 2', fontsize: int = 8) -> None:
        super().__init__()

        self._text = text
        self.label = QtWidgets.QLabel(win)
        self.label.setText(self._text)
        self.label.setGeometry(QtCore.QRect(x, y, width, height))
        self.font = QtGui.QFont()
        self.font.setPointSize(fontsize)
        self.font.setFamily(font)
        self.label.setFont(self.font)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.label.setText(value)


class SpinBox(QtWidgets.QSpinBox):
    """Simplified class of PyQt5.QtWidgets.QSpinBox SpinBox"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: int = 0, x: int = 0, y: int = 0, width: int = 75, height: int = 23,
                 font: str = DEFAULTFONT, fontsize: int = 8, mincount: int = 0, maxcount: int = 999) -> None:
        super().__init__()
        self._text = text
        self.spinbox = QtWidgets.QSpinBox(win)
        self.spinbox.setGeometry(QtCore.QRect(x, y, width, height))
        self.spinbox.setMinimum(mincount)
        self.spinbox.setMaximum(maxcount)
        self.spinbox.setValue(text)
        self.font = QtGui.QFont()
        self.font.setFamily(font)
        self.font.setPointSize(fontsize)
        self.spinbox.setFont(self.font)

    @property
    def text(self) -> str:
        return self._value

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        self.spinbox.setValue(value)

    def getText(self) -> str:
        """:returns the text(value) of the spinbox"""

        return self.spinbox.value()


def updateLbls(focus: int=None):
    if focus == 1:
        lblNetto.text = f'Your remaining budget: {str(calculateResult())}{comboBoxCur.getText().split(" ")[1]}'
        lblNettoBank.text = 'Your remaining bank balance: {0:.2f}{1}'.format(calculateBank(), comboBoxCur.getText().split(' ')[1])
    else:
        lblNetto.text = f'Your remaining budget: {str(calculateResult())}{comboBoxCur.getText().split(" ")[1]}'
        lblBrutto.text = f'Your monthly brutto budget: {str(calculateIncome())}{comboBoxCur.getText().split(" ")[1]}'
        lblNettoBank.text = 'Your remaining bank balance: {0:.2f}{1}'.format(calculateBank(), comboBoxCur.getText().split(' ')[1])


def delSelectedItem() -> None:
    """Main handler for deleting the selected item. Gets the focus and deletes the item in it"""

    currselectOnce = lstbox.curselection()
    currselectMonth = lstboxMonth.curselection()
    currselectTakings = lstboxTakings.curselection()
    currselectTakingsMonth = lstboxTakingsMonth.curselection()
    if DELCMD == 'focus1' and currselectOnce != -1:
        try:
            dtbOnce.removeFromDtb(currselectOnce)
            lstbox.delete(currselectOnce)
            updateLbls(1)
        except IndexError:
            return
    elif DELCMD == 'focus2' and currselectMonth != -1:
        try:
            dtbMonth.removeFromDtb(currselectMonth)
            lstboxMonth.delete(currselectMonth)
            updateLbls(1)
        except IndexError:
            return
    elif DELCMD == 'focus3' and currselectTakings != -1:
        try:
            dtbTakings.removeFromDtb(currselectTakings)
            lstboxTakings.delete(currselectTakings)
            updateLbls()
        except IndexError:
            return
    elif DELCMD == 'focus4' and currselectTakingsMonth != -1:
        try:
            dtbTakingsMonth.removeFromDtb(currselectTakingsMonth)
            lstboxTakingsMonth.delete(currselectTakingsMonth)
            updateLbls()
        except IndexError:
            return


def addItem() -> None:
    """Main handler for adding items to listbox"""

    if chbOneTime.checkbox.isChecked():
        if lstbox.add('once'):
            expNameTxt.text = ''
            expPriceTxt.text = ''
            if expInfo.getText() != DEFAULTPLAINTEXT:
                expInfo.text = ''
            else:
                expInfo.text = DEFAULTPLAINTEXT
            updateLbls(1)
    elif chbMonthly.checkbox.isChecked():
        if lstboxMonth.add('month'):
            expNameTxt.text = ''
            expPriceTxt.text = ''
            expInfo.text = '' if expInfo.text != DEFAULTPLAINTEXT else DEFAULTPLAINTEXT
            updateLbls(1)
    elif chbTakings.checkbox.isChecked():
        if lstboxTakings.add('taking'):
            expNameTxt.text = ''
            expPriceTxt.text = ''
            expInfo.text = '' if expInfo.text != DEFAULTPLAINTEXT else DEFAULTPLAINTEXT
            updateLbls()
    elif chbTakingsMonth.checkbox.isChecked():
        if lstboxTakingsMonth.add('takingMonth'):
            expNameTxt.text = ''
            expPriceTxt.text = ''
            expInfo.text = '' if expInfo.text != DEFAULTPLAINTEXT else DEFAULTPLAINTEXT
            updateLbls()


def dupSelectedItem() -> None:
    """Duplication of the current selection and adding it to the list at index 0"""

    currselectOnce = lstbox.curselection()
    currselectMonth = lstboxMonth.curselection()
    currselectTakings = lstboxTakings.curselection()
    currselectTakingsMonth = lstboxTakingsMonth.curselection()
    if DELCMD == 'focus1' and currselectOnce != -1:
        text = dtbOnce.getRowValuesById(currselectOnce, 1, 2, 3)
        lstbox.insertItems(
            currselectOnce + 1, lstbox.listbox.currentItem().text())
        dtbOnce.dataEntry(text[1], text[0], text[2])
        updateLbls(1)
    elif DELCMD == 'focus2' and currselectMonth != -1:
        text = dtbMonth.getRowValuesById(currselectMonth, 1, 2, 3)
        lstboxMonth.insertItems(currselectMonth + 1, lstboxMonth.listbox.currentItem().text())
        dtbMonth.dataEntry(text[1], text[0], text[2])
        updateLbls(1)
    elif DELCMD == 'focus3' and currselectTakings != -1:
        text = dtbTakings.getRowValuesById(currselectTakings, 1, 2, 3)
        lstboxTakings.insertItems(currselectTakings + 1, lstboxTakings.listbox.currentItem().text())
        dtbTakings.dataEntry(text[1], text[0], text[2])
        updateLbls()
    elif DELCMD == 'focus4' and currselectTakingsMonth != -1:
        text = dtbTakingsMonth.getRowValuesById(currselectTakingsMonth, 1, 2, 3)
        lstboxTakingsMonth.insertItems(currselectTakingsMonth + 1, lstboxTakingsMonth.listbox.currentItem().text())
        dtbTakingsMonth.dataEntry(text[1], text[0], text[2])
        updateLbls()


def selectDirMoveFiles() -> None:
    """Used when the 'select directory' button is pressed. closes all database connections and moves the files."""

    global path
    newPath = ''
    filedialog = QtWidgets.QFileDialog(mainWin, 'Select Directory')
    filedialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
    if filedialog.exec_() == QtWidgets.QDialog.Accepted:
        newPath = filedialog.selectedFiles()[0]
    if newPath is not path:
        dtbOnce.cursor.close()
        dtbOnce.conn.close()
        dtbMonth.cursor.close()
        dtbMonth.conn.close()
        dtbOldOnce.cursor.close()
        dtbOldOnce.conn.close()
        dtbTakings.cursor.close()
        dtbTakings.conn.close()
        try:
            move(path, newPath)
        except:
            restart()
        path = newPath
        writeToTxtFile(dirfile, path + '/ExpenseTracker/')
        restart()


def addListToDtb(price: float, exp: str, t: str, moreInfo: str = None) -> None:
    """Adds parameters to database"""

    if t == 'once':
        dtbOnce.dataEntry(float(price), exp, moreInfo)
    elif t == 'month':
        dtbMonth.dataEntry(float(price), exp, moreInfo)
    elif t == 'taking':
        dtbTakings.dataEntry(float(price), exp, moreInfo)
    elif t == 'takingMonth':
        dtbTakingsMonth.dataEntry(float(price), exp, moreInfo)
    else:
        raise ValueError


def isFirstTime() -> bool:
    """Checks if this is the first time the user openes the program"""

    if exists(path + 'FirstTime.txt'):
        if readFromTxtFile(path + 'FirstTime.txt', 'str') == 'False':
            return False
        else:
            writeToTxtFile(path + 'FirstTime.txt', 'False')
            return True
    else:
        return True


def restart() -> None:
    execl(sys.executable, sys.executable, *sys.argv)


def showExpenseInfo() -> None:
    """Displays the info in a messagebox"""

    curselectOnce = lstbox.curselection()
    curselectMonth = lstboxMonth.curselection()
    curselectTakings = lstboxTakings.curselection()
    curselectTakingsMonth = lstboxTakingsMonth.curselection()
    if DELCMD == 'focus1' and curselectOnce != -1:
        infoOnce = dtbOnce.getRowValuesById(curselectOnce, 3)
        if infoOnce != [None]: QtWidgets.QMessageBox.information(None, 'Product info', ''.join(infoOnce),
                                                                 QtWidgets.QMessageBox.Ok)
    elif DELCMD == 'focus2' and curselectMonth != -1:
        infoMonth = dtbMonth.getRowValuesById(curselectMonth, 3)
        if infoMonth != [None]: QtWidgets.QMessageBox.information(None, 'Product info', ''.join(infoMonth),
                                                                  QtWidgets.QMessageBox.Ok)
    elif DELCMD == 'focus3' and curselectTakings != -1:
        infoMonth = dtbTakings.getRowValuesById(curselectMonth, 3)
        if infoMonth != [None]: QtWidgets.QMessageBox.information(None, 'Product info', ''.join(infoMonth),
                                                                  QtWidgets.QMessageBox.Ok)
    elif DELCMD == 'focus4' and curselectTakingsMonth != -1:
        infoMonth = dtbTakings.getRowValuesById(curselectMonth, 3)
        if infoMonth != [None]: QtWidgets.QMessageBox.information(None, 'Product info', ''.join(infoMonth),
                                                                  QtWidgets.QMessageBox.Ok)


def readFromTxtFile(pa: str, typ: str):
    """Reads from text file. Valid typ params: 'str', 'float'"""

    try:
        with open(pa, 'r') as f:
            if typ == 'float':
                return float(f.readline())
            elif typ == 'str':
                r = f.readline()
                return r
            else:
                raise ValueError('Invalid type!')
    except FileNotFoundError:
        f = open(pa, 'w+')
        f.close()


def writeToTxtFile(pa: str, text: str) -> None:
    """Writes to text file in write mode"""

    with open(pa, 'w') as f:
        f.write(str(text))


def calculateResult() -> float:
    """Returns the end result of the expense calculation"""

    return round(calculateIncome() - (dtbOnce.cal() + dtbMonth.cal()), 2)


def calculateIncome() -> float:
    """Returns the sum of all the monthly income sources"""

    return round(dtbTakingsMonth.cal() + dtbTakings.cal(), 2)


def calculateBank() -> float:
    """Returns the money left from your bank ballance"""
    try:
        return round(bankBalance + calculateIncome() - dtbOnce.cal() - dtbMonth.cal(), 2)
    except TypeError:
        setBankBalance()


def setBankBalance() -> float:
    if english:
        inpt, okpressed = QtWidgets.QInputDialog.getDouble(None, 'Get Bank Deposit', 'Please enter your current bank balance',
                                                           min=0, decimals=2)
    elif german:
        inpt, okpressed = QtWidgets.QInputDialog.getDouble(None, 'Bankguthaben', 'Bitte gib dein Bankguthaben ein',
                                                           min=0, decimals=2)
    if okpressed:
        writeToTxtFile(path + 'Bank.txt', str(inpt))
        return inpt
    else:
        exit()


def setBankBalanceBtn():
    setBankBalance()
    restart()


def clearD() -> None:
    """Clears database depending on the checked checkbox"""

    if DELCMD == 'focus1':
        dtbOnce.clearDtb()
        lstbox.listbox.clear()
        updateLbls(1)
    elif DELCMD == 'focus2':
        dtbMonth.clearDtb()
        lstboxMonth.listbox.clear()
        updateLbls(1)
    elif DELCMD == 'focus3':
        dtbTakings.clearDtb()
        lstboxTakings.listbox.clear()
        updateLbls()
    elif DELCMD == 'focus4':
        dtbTakingsMonth.clearDtb()
        lstboxTakingsMonth.listbox.clear()
        updateLbls()


def changeLanguageEnglish(eng: bool) -> None:
    """Changes language to english"""

    if not eng:
        addBtn.text = 'Add'
        delBtn.text = 'Delete'
        clearBtn.text = 'Clear'
        dirBtn.text = 'Select\nDirec-\ntory'
        dupBtn.text = 'Duplicate'
        editBtn.text = 'Edit'
        chbOneTime.text = 'One-Time-Expenses'
        chbMonthly.text = 'Monthly-Expenses'
        chbTakings.text = 'One-Time-Takings'
        chbTakingsMonth.text = 'Monthly Income Sources'
        showExpGraph_30.text = '30-Day-Graph'
        showExpGraph_365.text = '1-Year-Graph'
        tl1 = lblBrutto.text.split(':')[1].strip()
        tl2 = lblNetto.text.split(':')[1].strip()
        lblBrutto.text = 'Your monthly brutto budget: ' + tl1
        lblNetto.text = 'Your remaining budget:          ' + tl2
        lblinfoPrice.text = 'Price'
        lblinfoMulti.text = 'Multiplier'
        lbloneTime.text = 'One-Time-Expenses'
        lblmonthly.text = 'Monthly-Expenses'
        lblTakings.text = 'One-Time Takings'
        lblMonthlyTakings.text = 'Monthly Income Sources'
        lblNettoBank.text = 'Your remaining bank balance: ' + str(calculateBank())
        setBankBtn.text = 'Set Balance'



def changeLanguageGerman(ger: bool) -> None:
    """Changes language to german"""

    if not ger:
        addBtn.text = 'Hinzufügen'
        delBtn.text = 'Löschen'
        clearBtn.text = 'Alles löschen'
        dirBtn.text = 'Verzeich-\nnis än-\ndern'
        dupBtn.text = 'Duplizieren'
        editBtn.text = 'Editieren'
        showExpGraph_30.text = '30 Tage Graph'
        showExpGraph_365.text = '1 Jahr Graph'
        chbOneTime.text = 'Einmalige Ausgaben'
        chbMonthly.text = 'Monatliche Ausgaben'
        chbTakings.text = 'Einnahmen'
        chbTakingsMonth.text = 'Monatliche Einnahmen'
        lblBrutto.text = 'Ihr brutto Einkommen: ' + lblBrutto.text.split(':')[1].strip()
        lblNetto.text = 'Ihr überbleibendes Geld:               ' + lblNetto.text.split(':')[1].strip()
        lblinfoPrice.text = 'Preis'
        lblinfoMulti.text = 'Multiplikator'
        lbloneTime.text = 'Einmalige Ausgaben'
        lblmonthly.text = 'Monatliche Ausgaben'
        lblTakings.text = 'Einnahmen'
        lblMonthlyTakings.text = 'Monatliche Einnahmen'
        lblNettoBank.text = 'Ihr überbleibendes Bankguthaben: ' + str(calculateBank())
        setBankBtn.text = 'Guthaben'


def isMonthEnd() -> bool:
    """Returns True if the month has ended, else False"""

    lastDate = readFromTxtFile(path + 'LastOpened.txt', 'str')
    today = datetime.today()
    try:
        lastMonth, lastYear = lastDate.split(';')
    except ValueError:
        return True
    lastMonth = int(lastMonth)
    lastYear = int(lastYear)
    if today.month > lastMonth and today.year == lastYear:
        writeToTxtFile(path + 'LastOpened.txt', f'{str(today.month)};{str(today.year)}')
        return True
    elif today.year > lastYear:
        writeToTxtFile(path + 'LastOpened.txt', f'{str(today.month)};{str(today.year)}')
        return True
    return False


def monthEnd() -> bool:
    """The events that have to happen if the month has ended. Line moving all old One-Time expenses to the oldDtb and writing date to text file"""

    if isMonthEnd():
        msgbox = QtWidgets.QMessageBox(mainWin)
        msgbox.setIcon(QtWidgets.QMessageBox.Information)
        msgbox.setWindowTitle('New month!')
        writeToTxtFile(path + 'Bank.txt', str(calculateBank()))
        for data in dtbOnce.getAllRecords():
            dtbOldOnce.dataEntry(data[2], data[1], data[3])
            dtbOnce.clearDtb()
            lstbox.listbox.clear()
            dtbTakings.clearDtb()
            lstboxTakings.listbox.clear()
            msgbox.information(msgbox, 'New Month',
                               'A new month has begun, all One-Time-Expenses and Takings were deleted!')
        return True
    return False


def initPlot(l1: list, l2: list, label: str, tile: str, xlabl: str, ylabl: str, linestyle: str = None) -> None:
    """Plots the plot used to show expense graph"""

    plot(l1, l2, marker='o', linestyle=linestyle, label=label, color='k')
    legend()
    title(tile)
    xlabel(xlabl)
    ylabel(ylabl)
    show()


def showGraph(t: str, tile: str, xaxis: str, yaxis: str) -> None:
    """Gets items from dtb and calls initPlot method"""

    now = datetime.now()
    if t == 'month':
        dtbOnce.cursor.execute('SELECT Day, Price FROM OneTimeExpenseTable WHERE Month = ?', (now.month,))
    elif t == 'year':
        dtbOnce.cursor.execute('SELECT Month, Price FROM OneTimeExpenseTable WHERE Year = ?', (now.year,))
    else:
        raise ValueError('Please Enter "month" or "year"')

    days = []
    prices = []
    for val in dtbOnce.cursor.fetchall():
        days.append(val[0])
        prices.append(val[1])

    dic = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0,
           17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 30: 0, 31: 0}

    valueLst = [elem for elem in zip(days, prices)]

    for value in valueLst:
        dic[value[0]] += value[1]

    if english:
        initPlot(list(dic.keys()), list(dic.values()), 'One-Time-Expenses', tile, xaxis, yaxis, linestyle='--')
    elif german:
        initPlot(list(dic.keys()), list(dic.values()), 'Einmalige Ausgabel', tile, xaxis, yaxis, linestyle='--')


def showYearGraph() -> None:
    if english:
        showGraph('year', 'Expenses of the last year', 'month', 'price')
    elif german:
        showGraph('year', 'Ausgaben des letzten Jahres', 'Monat', 'Preis')


def showMonthGraph() -> None:
    if english:
        showGraph('month', 'Expenses of the last month', 'days', 'price')
    elif german:
        showGraph('month', 'Ausgaben des letzten Monats', 'Tag', 'Preis')


def createFiles() -> None:
    """Creates the files when the program is first opened."""

    try:
        mkdir('C:/tmp/')
    except:
        pass
    try:
        mkdir(path)
    except:
        pass
    open(dirfile, 'w+')
    open(path + 'Bank.txt', 'w+')
    open(expenseDtbPath, 'w+')
    open(path + 'FirstTime.txt', 'w+')
    open(path + 'LastOpened.txt', 'w+')
    f = open(path + 'OldExpenses.db', 'w+')
    f.close()


def chb1CommandHandler() -> None:
    chbOneTime.unckeckAny(False, chbMonthly, chbTakings, chbTakingsMonth)


def chb2CommandHandler() -> None:
    chbMonthly.unckeckAny(False, chbOneTime, chbTakings, chbTakingsMonth)


def chb3CommandHandler() -> None:
    chbTakings.unckeckAny(False, chbMonthly, chbOneTime, chbTakingsMonth)

def chb4CommandHandler() -> None:
    chbTakingsMonth.unckeckAny(False, chbMonthly, chbOneTime, chbTakings)


def edit() -> None:
    """Function to handle the edit window"""

    global editWin, currselectMonthEdit, currselectOnceEdit
    editWin = Editor()
    currselectOnceEdit = lstbox.curselection()
    currselectMonthEdit = lstboxMonth.curselection()

    if currselectOnceEdit != -1 or currselectMonthEdit != -1:

        # insert all texts
        if DELCMD == 'focus1' and currselectOnceEdit != -1:
            values = dtbOnce.getRowValuesById(currselectOnceEdit, 1, 2, 3, 4, 5, 6)
            editWin.lblDateEdit.text = f'This expense was added on {values[3]}-{values[4]}-{values[5]}'
            editWin.expNameTxtEdit.text = str(values[0])
            editWin.expPriceTxtEdit.text = '{0:.2f}'.format((float(values[1])))
            editWin.expInfoEdit.text = str(values[2])
        elif DELCMD == 'focus2' and currselectMonthEdit != -1:
            values = dtbMonth.getRowValuesById(currselectMonthEdit, 1, 2, 3, 4, 5, 6)
            editWin.lblDateEdit.text = f'This expense was added on {values[3]}-{values[4]}-{values[5]}'
            editWin.expNameTxtEdit.text = str(values[0])
            editWin.expPriceTxtEdit.text = '{0:.2f}'.format((float(values[1])))
            editWin.expInfoEdit.text = str(values[2])
        editWin.show()


if __name__ == '__main__':
    # Initialize main app
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow(application=app, mainWindowTitle='ExpenseTracker', minsizeX=1200, minsizeY=600, maxsizeX=1200, maxsizeY=600)
    mainWin.resize(1200, 600)
    lstbox = ListBox(mainWin, x=20, y=50, width=180, height=300, fontsize=13)
    lstboxMonth = ListBox(mainWin, x=20, y=380, width=180, height=210, fontsize=13)
    lstboxTakings = ListBox(mainWin, x=930, y=50, width=180, height=300, fontsize=13)
    lstboxTakingsMonth = ListBox(mainWin, x=930, y=380, width=180, height=210, fontsize=13)
    expenseDtbPath = 'C:/tmp/ExpenseTracker/Expenses.db'
    dirfile = 'C:/tmp/dir.txt'
    german = False
    english = True

    # Try to read from dirfile and set path = standart if it catches error
    try:
        _path = readFromTxtFile(dirfile, 'str')
        if _path is not None:
            path = _path
        else:
            path = 'C:/tmp/ExpenseTracker/'
    except:
        path = 'C:/tmp/ExpenseTracker/'

    # All the first Time things like creating files and entering config data
    if isFirstTime():
        createFiles()
        today = datetime.today()
        writeToTxtFile(path + 'LastOpened.txt', f'{str(today.month)};{str(today.year)}')
        writeToTxtFile(path + 'FirstTime.txt', 'False')
        writeToTxtFile(dirfile, path)
        bankBalance = setBankBalance()
        writeToTxtFile(path + 'Bank.txt', str(bankBalance))
    else:
        expenseDtbPath = path + 'Expenses.db'
        bankBalance = readFromTxtFile(path + 'Bank.txt', 'float')

    # Drop down menu for currency
    comboBoxCur = ComboBox(mainWin, x=800, y=100, height=40, width=80, fontsize=11)
    comboBoxCur.addItems('Euro €', 'Dollar $', 'Pound £')
    comboBoxLang = ComboBox(mainWin, x=1120, y=0, width=80, height=40, fontsize=11)
    comboBoxLang.addItems('English', 'Deutsch')

    # Database
    dtbOnce = DataBase(expenseDtbPath, 'OneTimeExpenseTable')
    dtbMonth = DataBase(expenseDtbPath, 'MonthlyExpenseTable')
    dtbOldOnce = DataBase(path + 'OldExpenses.db', 'OneTimeExpenseTable')
    dtbTakings = DataBase(expenseDtbPath, 'OneTimeTakingsTable')
    dtbTakingsMonth = DataBase(expenseDtbPath, 'MonthlyTakingsTable')

    # Check wether the month has ended
    if monthEnd():
        bankBalance = readFromTxtFile(path + 'Bank.txt', 'float')

    for data in dtbOnce.readFromDtb():
        lstbox.insertItems(0, '{1}, {0:.2f}{2}'.format(data[1], data[0], comboBoxCur.getText().split(" ")[1]))
    for data in dtbMonth.readFromDtb():
        lstboxMonth.insertItems(0, '{1}, {0:.2f}{2}'.format(float(data[1]), data[0], comboBoxCur.getText().split(" ")[1]))
    for data in dtbTakings.readFromDtb():
        lstboxTakings.insertItems(0, '{1}, {0:.2f}{2}'.format(float(data[1]), data[0], comboBoxCur.getText().split(" ")[1]))
    for data in dtbTakingsMonth.readFromDtb():
        lstboxTakingsMonth.insertItems(0, '{1}, {0:.2f}{2}'.format(float(data[1]), data[0], comboBoxCur.getText().split(" ")[1]))

    # Textboxes
    expNameTxt = TextBox(mainWin, x=350, y=100, width=220, height=40, fontsize=16)
    expPriceTxt = TextBox(mainWin, x=590, y=100, width=210, height=40, fontsize=16)

    # SpinBox for Multiplier
    expMultiTxt = SpinBox(mainWin, text=1, x=350, y=190, width=70, height=30, mincount=1)

    # Extra Info Text
    expInfo = PlainText(mainWin, text=DEFAULTPLAINTEXT, x=350, y=250, width=510, height=200, fontsize=11)

    # Labels
    totalIncome = calculateIncome()
    totalexp = calculateResult()
    totalBank = calculateBank()
    lblBrutto = Label(mainWin, x=400, y=10, height=50, width=500, fontsize=17,
                      text='Your monthly brutto budget: {0:.2f}{1}'.format(totalIncome, comboBoxCur.getText().split(" ")[1]))
    lblNetto = Label(mainWin, y=480, height=50, width=500, fontsize=17,
                     text='Your remaining budget: {0:.2f}{1}'.format(totalexp, comboBoxCur.getText().split(' ')[1]),
                     x=400)
    lbloneTime = Label(mainWin, 'One-Time-Expenses', 20, 30, 170, 20, fontsize=14)
    lblmonthly = Label(mainWin, 'Monthly-Expenses', 20, 360, 170, 20, fontsize=14)
    lblTakings = Label(mainWin, 'One-Time Takings', 930, 20, 170, 20, fontsize=14)
    lblMonthlyTakings = Label(mainWin, 'Monthly Income Sources', 930, 360, 220, 20, fontsize=14)
    lblinfoExp = Label(mainWin, 'Name', 350, 75, 160, 20, fontsize=13)
    lblinfoPrice = Label(mainWin, 'Price', 590, 75, 160, 20, fontsize=13)
    lblinfoMulti = Label(mainWin, 'Multiplier', 350, 170, 100, 20, fontsize=13)
    lblNettoBank = Label(mainWin, x=400, y=530, height=50, width=500, fontsize=17,
                         text='Your remaining bank balance: {0:.2f}{1}'.format(totalBank, comboBoxCur.getText().split(' ')[1]))


    # Checkboxes
    chbOneTime = CheckBox(mainWin, text='One-Time-Expense', command=chb1CommandHandler, x=620, y=160, width=250,
                          height=20)
    chbMonthly = CheckBox(mainWin, text='Monthly-Expense', command=chb2CommandHandler, x=620, y=190, width=250,
                          height=20)
    chbTakings = CheckBox(mainWin, text='One-Time-Takings', command=chb3CommandHandler, x=780, y=160, width=110, height=20)
    chbTakingsMonth = CheckBox(mainWin, text='Monthly Income Sources', command=chb4CommandHandler, x=780, y=190, width=140, height=20)
    chbOneTime.check()

    # Buttons
    addBtn = Button(mainWin, text='Add', command=addItem, x=230, y=100, height=35, width=90, key='Return')
    delBtn = Button(mainWin, text='Delete', command=delSelectedItem, x=230, y=140, height=35, width=90,
                    key='Delete')
    dupBtn = Button(mainWin, text='Duplicate', command=dupSelectedItem, x=230, y=180, height=35, width=90,
                    key='Ctrl+D')
    editBtn = Button(mainWin, text='Edit', command=edit, x=230, y=240, height=35, width=90, key='Ctrl+E')
    dirBtn = Button(mainWin, text='Select\nDirec-\ntory', command=selectDirMoveFiles, x=1150, y=530, height=70,
                    width=50)
    clearBtn = Button(mainWin, text='Clear List', command=clearD, x=230, y=280, height=35, width=90, key='Ctrl+C')
    moreInfoBtn = Button(mainWin, text='More Info', command=showExpenseInfo, x=230, y=340, height=35, width=90,
                         key='Ctrl+F')
    showExpGraph_30 = Button(mainWin, text='30-Day-Graph', command=showMonthGraph, x=230, y=400, height=35,
                             width=90)
    showExpGraph_365 = Button(mainWin, text='1-Year-Graph', command=showYearGraph, x=230, y=440, height=35,
                              width=90)
    setBankBtn = Button(mainWin, text='Set Balance', command=setBankBalanceBtn, x=230, y=500, height=35,
                        width=90)

    # start the app
    mainWin.show()
    sys.exit(app.exec_())