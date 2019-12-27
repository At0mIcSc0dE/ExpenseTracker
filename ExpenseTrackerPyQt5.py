"""
This programm will allow you to enter your monthly budget. Every expense will be stored and removed from it.
You will be able to show a graph showing if your expenses increased or decreased (30 days, 12 months).
The GUI will have a list of all of your expenses on the left, to which you can add using a text box right next to it.
You will also be able to enter monthly expenses that are always the same so these will be automatically subtracted from
your budget.
All of this will be stored in a database in the chosen directory, which you will be able to select
when you first open the program. I will also add a way to change the path and move all files from the previous one
to the newer one. One-Time-Expenses categorize all expenses like (butter -> Food) (car repair -> Car), Add another TxtBox, 
which you can type your Category in it, which will be added to another column in the database and will be able to be sorted 
with a drop down menu in the lstbox. I will also add a way to view old expenses and change the date at which they were added.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from os import execl, mkdir
from os.path import exists
from shutil import move
from sqlite3 import connect
from time import time
from matplotlib.pyplot import legend, plot, show, title, xlabel, ylabel
# from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5 import QtCore, QtGui, QtWidgets

global path, expenseDtbPath
DEFAULTFONT = 'MS Shell Dlg 2'
DELCMD = 'focus1'


class MainWindow(QtWidgets.QMainWindow):
    """Main WIndow"""

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
        """closes all windows"""

        dtbOnce.cursor.close()
        dtbOnce.conn.close()
        dtbMonth.cursor.close()
        dtbMonth.conn.close()
        dtbTakings.cursor.close()
        dtbTakings.conn.close()
        dtbTakingsMonth.cursor.close()
        dtbTakingsMonth.conn.close()
        dtbOldOnce.cursor.close()
        dtbOldOnce.conn.close()

        self.app.closeAllWindows()


class Editor(QtWidgets.QDialog):
    """The editor to edit the selected entry"""

    def __init__(self) -> None:
        super().__init__()
        self.editWin = QtWidgets.QDialog()
        self.editWin.resize(800, 400)
        self.editWin.setWindowTitle('Editor')

        self.editWin.setObjectName("Editor")
        self.expNameTxtEdit = TextBox(self.editWin, x=60, y=110, width=220, height=40, fontsize=16, placeHolder='Name')
        self.expPriceTxtEdit = TextBox(self.editWin, x=300, y=110, width=220, height=40, fontsize=16, placeHolder='Price')
        self.expInfoEdit = PlainText(self.editWin, x=60, y=160, width=460, height=180, fontsize=11, placeHolder='Write more info about your expense here...')
        self.lblDateEdit = Label(self.editWin, x=60, y=10, width=550, height=40, fontsize=18)
        self.btnOkEdit = Button(self.editWin, text='Ok', x=590, y=320, width=90, height=35, key='Return', command=self.apply)
        self.btnCancelEdit = Button(self.editWin, text='Cancel', x=700, y=320, width=90, height=35, command=self.close)

    def apply(self) -> None:
        """takes your selection, and the textbox elements!"""

        global editWin, currselectOnceEdit, currselectMonthEdit, currselectTakingsEdit, currselectTakingsMonthEdit
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
        if currselectOnceEdit != -1 or currselectTakingsEdit != -1 or currselectMonthEdit != -1 or currselectTakingsMonthEdit != -1:
            if DELCMD == 'focus1' and currselectOnceEdit != -1:
                lstbox.update(currselectOnceEdit, name, price)
                dtbOnce.update(currselectOnceEdit, name, price, info)
            elif DELCMD == 'focus2' and currselectMonthEdit != -1:
                lstboxMonth.update(currselectMonthEdit, name, price)
                dtbMonth.update(currselectMonthEdit, name, price, info)
            elif DELCMD == 'focus3' and currselectTakingsEdit != -1:
                lstboxTakings.update(currselectTakingsEdit, name, price)
                dtbTakings.update(currselectTakingsEdit, name, price, info)
            elif DELCMD == 'focus4' and currselectTakingsMonthEdit != -1:
                lstboxTakingsMonth.update(currselectTakingsMonthEdit, name, price)
                dtbTakingsMonth.update(currselectTakingsMonthEdit, name, price, info)
            updateLbls(1)
            self.editWin.destroy()

    def close(self) -> None:
        """Closes the editwindow"""

        self.editWin.destroy()

    def show(self) -> None:
        """shows the editwin"""

        self.editWin.show()


class UserEditor(QtWidgets.QDialog):
    """Class to design the User editor."""

    def __init__(self) -> None:
        super().__init__()
        self.editWin = QtWidgets.QDialog()
        self.editWin.resize(900, 450)
        self.editWin.setWindowTitle('User Editor')

        self.editWin.setMinimumSize(QtCore.QSize(900, 450))
        self.editWin.setMaximumSize(QtCore.QSize(900, 450))
        self.addBtnEdit = Button(self.editWin, text='Add', x=220, y=30, width=90, height=35, command=addUser)
        self.editBtnEdit = Button(self.editWin, text='Edit', x=220, y=70, width=90, height=35, command=editUser)
        self.lstboxUsers = ListBox(self.editWin, x=10, y=30, width=180, height=160, fontsize=13)
        self.lstboxUserGroup = ListBox(self.editWin, x=10, y=220, width=180, height=150, fontsize=13)
        self.lblUser = Label(self.editWin, text='User', x=10, y=10, width=90, height=20, fontsize=13)
        self.lblGroup = Label(self.editWin, text='User Groups', x=10, y=196, width=160, height=20, fontsize=13)
        self.lstboxUsersInGroup = ListBox(self.editWin, x=240, y=220, width=180, height=150, fontsize=13)
        self.userInfoBtnEdit = Button(self.editWin, text='Show User Info', x=220, y=110, width=90, height=35, command=showUserInfo)
        self.deleteBtnEdit = Button(self.editWin, text='Delete', x=220, y=150, width=90, height=35, command=deleteUser)
        self.lblUserGroup = Label(self.editWin, text='Users in Group', x=240, y=196, width=160, height=20, fontsize=13)
        self.UsernameTxt = TextBox(self.editWin, x=330, y=30, width=170, height=40, fontsize=16, placeHolder='Username')
        self.PasswordTxt = TextBox(self.editWin, x=520, y=30, width=170, height=40, fontsize=16, placeHolder='Password')
        self.BalanceTxt = TextBox(self.editWin, x=710, y=30, width=170, height=40, fontsize=16, placeHolder='Balance')
        self.lblinfoUsername = Label(self.editWin, text='Username', x=330, y=10, width=200, height=20, fontsize=13)
        self.lblinfoPassword = Label(self.editWin, text='Password', x=560, y=10, width=200, height=20, fontsize=13)
        self.chbAddUser = CheckBox(self.editWin, text='User', x=330, y=80, width=240, height=20, command=chb5CommandHandler)
        self.chbAddUserGroup = CheckBox(self.editWin, text='User Group', x=330, y=110, width=240, height=20, command=chb6CommandHandler)
        self.chbAddUserToGroup = CheckBox(self.editWin, text='User in User Group', x=330, y=140, width=240, height=20, command=chb7CommandHandler)
        self.lblinfoBalance = Label(self.editWin, text='Bank Balance', x=710, y=10, width=210, height=20, fontsize=13)

    def close(self) -> None:
        """Closes the editwindow"""

        self.editWin.destroy()

    def show(self) -> None:
        """Shows the editwin"""

        self.editWin.show()


class UserInfo(QtWidgets.QDialog):
    """Class to display user info"""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.infoWin = QtWidgets.QDialog()
        self.infoWin.setWindowTitle(title)
        self.infoWin.resize(700, 300)

        self.OkBtnInfo = Button(self.infoWin, text='Ok', x=580, y=250, width=93, height=28, command=self.close)
        self.lstbox = ListBox(self.infoWin, x=10, y=10, width=210, height=280, fontsize=13)
        self.lblUsername = Label(self.infoWin, text='', x=230, y=100, width=230, height=30, fontsize=13)
        self.lblInfo = Label(self.infoWin, text='', x=230, y=0, width=460, height=40, fontsize=13)

    def close(self) -> None:
        """Closes the editwindow"""

        self.infoWin.destroy()

    def show(self) -> None:
        """Shows the editwin"""

        self.infoWin.show()


class UserInfoEditor:
    """Class to display the three messageboxes(dialogs) for changing username, password, balance"""

    def __init__(self, usgr: str) -> None:
        super().__init__()
        self.usage = usgr
        self.userEditWin = QtWidgets.QDialog()
        self.userEditWin.resize(730, 140)
        self.userEditWin.setMaximumSize(730, 140)
        self.userEditWin.setMinimumSize(730, 140)
        self.userEditWin.setWindowTitle('Edit User/Group')
        self.lblPassword = Label(self.userEditWin, 'Password', 290, 20, 200, 20, fontsize=13)

        if usgr == 'user':
            self.lblBalance = Label(self.userEditWin, 'Bank Balance', 540, 20, 200, 20, fontsize=13)
            self.balanceTxt = TextBox(self.userEditWin, x=540, y=50, width=170, height=40, placeHolder='Balance', fontsize=16)
            self.lblUsername = Label(self.userEditWin, text='Username', x=40, y=20, width=200, height=20, fontsize=13)
            self.usernameTxt = TextBox(self.userEditWin, x=40, y=50, width=170, height=40, placeHolder='Username', fontsize=16)
        elif usgr == 'group':
            self.lblUsername = Label(self.userEditWin, text='Group name', x=40, y=20, width=200, height=20, fontsize=13)
            self.usernameTxt = TextBox(self.userEditWin, x=40, y=50, width=170, height=40, placeHolder='Group name', fontsize=16)

        self.pwTxt = TextBox(self.userEditWin, x=290, y=50, width=170, height=40, placeHolder='Password', fontsize=16)
        self.updateBtn = Button(self.userEditWin, 'Update', 637, 110, command=self.update)
        self.cancelBtn = Button(self.userEditWin, 'Cancel', 540, 110, command=self.cancel)

    def show(self):
        """shows the window"""

        self.userEditWin.show()

    def cancel(self):
        """closes the editor"""

        self.userEditWin.close()

    def update(self):
        """Updaates the daatabase/json file, the labels"""

        global userWin
        if self.usage == 'user':
            name = self.usernameTxt.getText()
            pw = self.pwTxt.getText()
            balance = self.balanceTxt.getText()
            oldName = userWin.lstboxUsers.listbox.currentItem().text().split(',')[0].strip('"')

            dtbUser.updateUser(name, pw, balance, oldName, typ='typ3')

            data = readFromJson()
            for group in groups:
                for user in data['groups'][group]:
                    if user == oldName:
                        data['groups'][group].append(name)
                        data['groups'][group].remove(oldName)
            with open('C:/tmp/groups.json', 'w') as file:
                json.dump(data, file, indent=4)

            dtbOnce.cursor.execute('UPDATE OneTimeExpenseTable SET Username = ? WHERE Username = ?', (name, oldName))
            dtbMonthrsor.execute('UPDATE MonthlyExpenseTable SET Username = ? WHERE Username = ?', (name, oldName))
            dtbTakings.cursor.execute('UPDATE OneTimeTakingsTable SET Username = ? WHERE Username = ?', (name, oldName))
            dtbTakingsMonth.cursor.execute('UPDATE MonthlyTakingsTable SET Username = ? WHERE Username = ?', (name, oldName))
            dtbOnce.conn.commit()
            dtbMOnth.conn.commit()
            dtbTakings.conn.commit()
            dtbTakingsMonth.conn.commit()

            userWin.lstboxUsers.update(userWin.lstboxUsers.curselection(), name, pw, balance, 'editUser')
            updateLbls()
        elif self.usage == 'group':
            name = self.usernameTxt.getText() # globall
            pw = self.pwTxt.getText()   # ""
            oldName = userWin.lstboxUserGroup.listbox.currentItem().text().split(',')[0].strip('"') # global

            data = readFromJson()
            s = data['groups']
            for group in data['groups']:
                if oldName == group:
                    data['groups'][name] = data['groups'][oldName]
                    del data['groups'][oldName]
                    data['passwords'][name] = pw
                    del data['passwords'][oldName]
                    break

            with open('C:/tmp/groups.json', 'w') as file:
                json.dump(data, file, indent=4)
            dtbUser.updateUser(username=name, password=pw, oldUsername=oldName)
        self.cancel()
        userWin.close()


class User:
    """User class, You will be able to register with username and pw, data of user will be accesed by username str in database
    as a new column"""

    def __init__(self, username: str, password: str, balance: str = 0) -> None:
        self._username = username
        self._password = password
        self._balance = balance

        if self.username in groups:
            usersInGroup = readFromJson()['groups'][self.username]
            balances = []

            # assignes balance for the group
            for user in usersInGroup:
                if user not in groups:
                    data = dtbUser.readUserDtb(username=user)
                    try:
                        balances.append(dtbUser.readUserDtb(username=user)[0][2])
                    except IndexError:
                        pass
            
            for bal in balances:
                self.balance += float(bal)

        if not self.userExists():
            if self.username in groups:
                self.registerUser(group=True)
            else:
                self.registerUser()
    
    def registerUser(self, group: bool=False):
        """registers the user, adds them to dtb and json file(global group)"""
        if group:
            with open('C:/tmp/groups.json') as file:
                data = json.load(file)
            
            self.password = data['passwords'][self.username]

            dtbUser.dataEntryUser(self.username, self.password, self.balance)
        else:
            dtbUser.dataEntryUser(self.username, self.password, self.balance)
            group = Group('global')
            group.addUserToGroup(self.username)
            group.addGroupPW('')

    @property
    def balance(self):
        """@property balance"""

        return self._balance

    @balance.setter
    def balance(self, value):
        """balance setter"""

        self._balance = value

    @property
    def username(self) -> str:
        """@property username"""

        return self._username

    @username.setter
    def username(self, value) -> None:
        """username setter"""

        self._username = value

    @property
    def password(self) -> str:
        """@property password"""

        return self._password

    @password.setter
    def password(self, value) -> None:
        """password setter"""

        self._password = value

    def userExists(self) -> bool:
        """Returns true if the user already exists"""

        users = dtbUser.readUserDtb(arg='noBank')
        curUser = (self.username, self.password)
        # return True if curUser in users else False
        for user in users:
            if curUser[0] == user[0]:
                if curUser[1] != user[1]:
                    reply = QtWidgets.QMessageBox.critical(None, 'Invalid', 'Invalid password or username, try again?', QtWidgets.QMessageBox.Ok|QtWidgets.QMessageBox.Cancel)
                    restart() if reply == QtWidgets.QMessageBox.Ok else exit()
                else:
                    return True


class Group:
    """Class group, can read, write to json, manages global group and users of group"""

    def __init__(self, groupName: str):
        self.groupName = groupName

    def getUsersFromGroup(self, pa: str='C:/tmp/groups.json') -> list:
        """Returns a list of all the users in the group"""

        with open(pa) as file:
            data = json.load(file)
        
        return data['groups'][self.groupName]

    def addUserToGroup(self, username: str, path: str='C:/tmp/groups.json'):
        """Adds user to group, stored in json file"""
        with open(path) as file:
            data = json.load(file)

            data['groups'][self.groupName] == data['groups'][self.groupName].append(username)

        with open(path, 'w') as file:
            json.dump(data, file, indent=4)

    def addGroupPW(self, groupPW: str, path: str='C:/tmp/groups.json') -> None:
        """Adds groupPW to json file"""

        with open(path) as file:
            data = json.load(file)

            data['passwords'].update({self.groupName: groupPW})

        with open(path, 'w') as file:
            json.dump(data, file, indent=4)


class Category:
    """Categorizes Expenses. All expenses will automatically be added to the category "all"."""

    def __init__(self, name: str, exp: bool=True):
        self._name = name
        self.exp = exp
        if self.name not in expCategories and exp:
            self.addCategroy()
        elif self.name not in takCategories and not exp:
            self.addCategroy()
        else:
            print('Exists')

    def addCategroy(self):
        if self.exp:
            dtbExpCategory.dataEntryCategory(self.name)
            expCategories.append(self.name)
        else:
            dtbTakCategory.dataEntryCategory(self.name)
            takCategories.append(self.name)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value


class DataBase:
    """Database class, no inheritance"""

    def __init__(self, databasePath: str, table: str, enc: str='expense') -> None:
        """Will create table if it does not exist.
        Args: your databasePath and the name of your table"""

        self.table = table
        self.conn = connect(databasePath)
        self.cursor = self.conn.cursor()

        if enc == 'expense':
            self.cursor.execute('CREATE TABLE IF NOT EXISTS ' + self.table + '''(
                                ID INTEGER,
                                Expense TEXT,
                                Price INTEGER,
                                MoreInfo TEXT,
                                Day INTEGER,
                                Month INTEGER,
                                Year INTEGER,
                                Username TEXT,
                                Category TEXT,
                                PRIMARY KEY(ID)
                                )''')
        elif enc == 'user':
            self.cursor.execute('CREATE TABLE IF NOT EXISTS ' + self.table + '''(
                                ID INTEGER,
                                Username TEXT,
                                Password TEXT,
                                BankBalance INTEGER,
                                PRIMARY KEY(ID)
                                )''')
        elif enc == 'category':
            self.cursor.execute('CREATE TABLE IF NOT EXISTS ' + self.table + '''(
                                 ID INTEGER,
                                 Name TEXT,
                                 PRIMARY KEY(ID)
                                 )''')

    def dataEntryCategory(self, name: str) -> None:
        """Enters the category with the name into the dtb"""

        self.cursor.execute('INSERT INTO ' + self.table + ' (Name) VALUES(?)', (name, ))
        self.conn.commit()

    def updateUser(self, username: str=None, password: str=None, balance: (int, str)=None, oldUsername: str=None, typ: str='main') -> None:
        """Updates all balances and writes them to DTB:"""

        if password and oldUsername is None and typ == 'main':
            if username not in groups:
                self.cursor.execute('UPDATE ' + self.table + ' Set BankBalance = ? WHERE Username = ?', (balance, username))
                self.conn.commit()
        elif password and oldUsername is not None and typ == 'typ2':
            self.cursor.execute('UPDATE ' + self.table + ' Set Username = ?, Password = ? WHERE Username = ?', (username, password, oldUsername))
            self.conn.commit()
        elif username is not None and password is not None and balance is not None and oldUsername is not None and typ == 'typ3':
            self.cursor.execute('UPDATE ' + self.table + ' SET Username = ?, Password = ?, BankBalance = ? WHERE Username = ?', (username, password, balance, oldUsername))
            self.conn.commit()
        else:
            raise ValueError('Please input either only balance or all of the arguments')

    def getUsers(self):
        """returns list of all usernames"""

        self.cursor.execute('SELECT Username FROM ' + self.table)
        return self.cursor.fetchall()

    def getUserBalance(self, username: str) -> list:
        """returns the balance of the user"""

        self.cursor.execute('SELECT BankBalance FROM ' + self.table + ' WHERE Username = ?', (username, ))
        return self.cursor.fetchall()

    def readFromCategoryDtb(self, name: str=None) -> list:
        """returns a list of all the names of all categories"""

        if name:
            self.cursor.execute('SELECT Name FROM ' + self.table + ' WHERE Name = ?', (name, ))
        else:
            self.cursor.execute('SELECT Name FROM ' + self.table)
        retval = []
        for element in self.cursor.fetchall():
            retval.append(element[0])
        return retval

    def getRowValuesById(self, rowid: int, *elemIndex: int):
        """Enter the ID by which the record is stored and the function will return you a list if you want multiple elements
        of one record or it will return the entire row if no elemIndex given."""

        self.cursor.execute('SELECT ID FROM ' + self.table)
        rws = self.cursor.fetchall()
        rws = rws[::-1]
        try:
            r = rws[rowid][0]
        except IndexError as e:
            print(e)
            return []
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

    def dataEntry(self, price: float, exp: str, username: str = '', moreInfo: str = None, category: str='All'):
        """Enters data into a database"""

        day, month, year = str(datetime.fromtimestamp(time()).strftime('%d-%m-%Y')).split('-')
        self.cursor.execute('INSERT INTO ' + self.table + ' (Expense, Price, MoreInfo, Day, Month, Year, Username, Category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                            (exp, price, moreInfo.rstrip('\n'), day, month, year, username, category))
        self.conn.commit()

    def dataEntryUser(self, username: str, password: str, balance: str) -> None:
        """Enters into user database, takes username, password and userid"""

        self.cursor.execute('INSERT INTO ' + self.table + ' (Username, Password, BankBalance) VALUES (?, ?, ?)', (username, password, balance))
        self.conn.commit()

    def clearDtb(self) -> None:
        """Clears the database of all records. Also updates labels"""

        self.cursor.execute('DELETE FROM ' + self.table)
        self.conn.commit()

    def removeFromDtb(self, currselect: int=None, username: str=None) -> None:
        """Removes item with the reversed rowid from listbox"""
        if currselect is not None:
            self.cursor.execute('SELECT ID FROM ' + self.table)
            rws = self.cursor.fetchall()
            rws = rws[::-1]
            rw = rws[currselect]
            self.cursor.execute('DELETE FROM ' + self.table + ' WHERE ID = ?', (str(rw[0]),))
            self.conn.commit()
            self.updateId()
        elif username is not None:
            self.cursor.execute('DELETE FROM ' + self.table + ' WHERE Username = ?', (username, ))
            self.conn.commit()
            self.updateId()
        else:
            raise ValueError('Please either input currselect or username')

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

    def cal(self, userName: str='NONE') -> float:
        """Calculation of totalExpenses"""

        if userName not in groups:
            
            self.cursor.execute('SELECT Price FROM ' + self.table + ' WHERE Username = ?', (userName, ))
            expenses = self.cursor.fetchall()

            totalExpense = 0
            for expense in expenses:
                totalExpense += float(expense[0])
        else:
            group = Group(userName)
            for user in group.getUsersFromGroup():
                self.cursor.execute('SELECT Price FROM ' + self.table + ' WHERE Username = ?', (user, ))
                expenses = self.cursor.fetchall()

                totalExpense = 0
                for expense in expenses:
                    totalExpense += float(expense[0])

        return totalExpense

    def readFromDtb(self) -> list:
        """Reads Expense, Price, MoreInfo from Database"""

        self.cursor.execute('SELECT Expense, Price, MoreInfo, Username FROM ' + self.table)
        return self.cursor.fetchall()

    def readUserDtb(self, username: str=None, arg: str=None) -> list:
        """Reads Username, Password and Balance"""
        if arg == 'noBank':
            self.cursor.execute('SELECT Username, Password FROM ' + self.table)
            return self.cursor.fetchall()
        elif username is not None:
            self.cursor.execute('SELECT Username, Password, BankBalance FROM ' + self.table + ' WHERE Username = ?', (username, ))
            return self.cursor.fetchall()
        self.cursor.execute('SELECT Username, Password, BankBalance FROM ' + self.table)
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

    def destroy(self):
        """Closes instance off class"""

        self.cursor.close()
        self.conn.close()
        del self


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
        """@property text"""

        return self._text

    @text.setter
    def text(self, value) -> None:
        """text.setter"""

        self._text = value
        self.button.setText(self._text)


class TextBox(QtWidgets.QLineEdit):
    """Simplified class of PyQt5.QtWidgets.QLineEdit TextBox"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: str = '', x: int = 0, y: int = 0, width: int = 75,
                 height: int = 23, placeHolder: str='',
                 font: str = DEFAULTFONT, fontsize: int = 8) -> None:
        super().__init__()
        self._text = text
        self._placeHolder = placeHolder
        self.textbox = QtWidgets.QLineEdit(win)
        self.textbox.setPlaceholderText(placeHolder)
        self.textbox.setGeometry(QtCore.QRect(x, y, width, height))
        self.textbox.setText(self.text)
        self.font = QtGui.QFont()
        self.font.setFamily(font)
        self.font.setPointSize(fontsize)
        self.textbox.setFont(self.font)
    
    @property
    def placeHolder(self) -> str:
        """@property placeHolder"""

        return self._placeHolder

    @placeHolder.setter
    def placeHolder(self, value: str) -> None:
        """@placeHolder.setter for placeHolder"""

        self._placeHolder = value
        self.textbox.setPlaceholderText(value)

    @property
    def text(self) -> str:
        """@property balance"""

        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """text.setter"""

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

        # please install event signals like the one below before event filters!
        self.listbox.currentItemChanged.connect(self.itemChanged)
        self.listbox.installEventFilter(self)

    def itemChanged(self, current: QtWidgets.QListWidgetItem, previous: QtWidgets.QListWidgetItem):
        """Event handler for item changed signal, updates userWin.lstboxUsersInGroup"""

        global userWin
        try:
            if self == userWin.lstboxUserGroup:
                group = Group(current.text().split(',')[0].strip('"'))
                users = group.getUsersFromGroup()
                userWin.lstboxUsersInGroup.listbox.clear()
                for user in users:
                    userWin.lstboxUsersInGroup.insertItems(0, user)
        except NameError:
            pass
    
    @staticmethod
    def lstboxCleaner(*listboxes):
        """clears lstbox focus and selection"""

        for lst in listboxes:
            lst.clearFocus()
            lst.clearSelection()

    def eventFilter(self, obj, event) -> bool:
        """event filter for lstbox, responsible for focus1, focus2..."""

        global DELCMD, userWin
        if event.type() == QtCore.QEvent.FocusIn:
            if obj == lstbox.listbox:
                self.lstboxCleaner(lstboxTakingsMonth, lstboxMonth, lstboxTakings)
                print('focus1')
                DELCMD = 'focus1'
                return True
            elif obj == lstboxMonth.listbox:
                self.lstboxCleaner(lstboxTakingsMonth, lstbox, lstboxTakings)
                print('focus2')
                DELCMD = 'focus2'
                return True
            elif obj == lstboxTakings.listbox:
                self.lstboxCleaner(lstboxTakingsMonth, lstboxMonth, lstbox)
                print('focus3')
                DELCMD = 'focus3'
                return True
            elif obj == lstboxTakingsMonth.listbox:
                self.lstboxCleaner(lstbox, lstboxMonth, lstboxTakings)
                print('focus4')
                DELCMD = 'focus4'
                return True
        return False

    def add(self, expenseTime: (str, tuple), txt: str = None, currselect: tuple = None, index: int = 0, window=None) -> bool:
        """Adds items into listbox.
        Valid expenseTime: ('dup', 'once'), ('dup', 'month'), 'once', 'month', 'taking', 'user', 'user group', 'user to group'"""

        global userWin
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
        if expenseTime in ('user', 'user group'):
            name = userWin.UsernameTxt.getText()
            password = userWin.PasswordTxt.getText()
            if expenseTime == 'user':
                balance = userWin.BalanceTxt.getText()
        else:
            expname = expNameTxt.getText()
            expprice = expPriceTxt.getText()
            expmoreInfo = expInfo.getText()
            expcurrency = comboBoxCur.getText().split(' ')[1]
            expmultiplier = expMultiTxt.getText()

        # Check if valid price and multiplier input
        msgbox = QtWidgets.QMessageBox(mainWin)
        msgbox.setWindowTitle('Error')
        msgbox.setIcon(QtWidgets.QMessageBox.Critical)
        msgbox.setGeometry(500, 200, 300, 500)
        try:
            if expenseTime == 'user':
                if balance != '':
                    balance = float(balance)
                else:
                    balance = float(0)
            elif expenseTime == 'user group':
                pass
            elif expenseTime == 'user to group':
                curselectUser = window.lstboxUsers.curselection()
                curselectUserInGroup = window.lstboxUsersInGroup.curselection()
            else:
                expprice = float(expprice)
                multiplier = int(expmultiplier)
        except:
            msgbox.information(msgbox, 'Invalid Input', 'Invalid Input, try again!')
            return False
            
        if expenseTime == 'user':
            self.insertItems(0, '"{1}", "{2}", "{0:.2f}"'.format(balance, name, password))
            addListToDtb(price=password, exp=name, t=expenseTime, moreInfo=balance)
            return True
        elif expenseTime == 'user group':
            self.insertItems(0, f'"{name}", "{password}"')
            addListToJson(name=name, password=password)
            return True
        elif expenseTime == 'user to group':
            name = window.lstboxUsers.listbox.currentItem().text().split(',')[0].strip('"')
            groupName = window.lstboxUserGroup.listbox.currentItem().text().split(',')[0].strip('"')
            self.insertItems(0, name)
            group = Group(groupName)
            group.addUserToGroup(name)
            return True
        elif expname and expprice != '':
            for _ in range(multiplier):
                self.insertItems(0, '{1}, {0:.2f}{2}'.format(expprice, expname, expcurrency))
                addListToDtb(expprice, expname, expenseTime, expmoreInfo)
                expMultiTxt.text = 1
            return True
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

    def update(self, selection: int, name: str, price: float, balance: (str, float)=0, usage: str='main') -> None:
        """Updates listboxselection. Works by deleting the previos entry and replacing it with a new one,
           :param usage = main, editUser or editUserGroup"""

        self.delete(selection)
        if usage == 'main':
            self.insertItems(selection, '{1}, {0:.2f}{2}'.format(float(price), name, comboBoxCur.getText().split(" ")[1]))
        elif usage == 'editUser':
            self.insertItems(selection, f'"{name}", "{price}", "{balance}"')
        elif usage == 'editUserGroup':
            self.insertItems(selection, f'"{name}", "{price}"')
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
        """@property command"""

        return self._command

    @command.setter
    def command(self, func: callable) -> None:
        """command.setter"""

        self._command = func

    @property
    def text(self) -> str:
        """@property text"""

        return self._text

    @text.setter
    def text(self, text: str) -> None:
        """text.setter"""

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
                 font: str = DEFAULTFONT, fontsize: int = 8, isEditable: bool=False) -> None:
        super().__init__()
        self.combobox = QtWidgets.QComboBox(win)
        self.combobox.setGeometry(QtCore.QRect(x, y, width, height))
        self.combobox.setEditable(isEditable)
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

    def clear(self):
        """Clears text and items in self"""

        self.combobox.clear()


class PlainText(QtWidgets.QPlainTextEdit):
    """Simplified class of PyQt5.QtWidgets.QPlainTextEdit PlainText"""

    def __init__(self, win: (QtWidgets.QMainWindow, QtWidgets.QDialog), text: str = '', x: int = 0, y: int = 0, width: int = 75,
                 height: int = 23, placeHolder: str='',
                 font: str = DEFAULTFONT, fontsize: int = 8) -> None:
        super().__init__()
        self._text = text
        self.plain = QtWidgets.QPlainTextEdit(win)
        self.plain.setPlaceholderText(placeHolder)
        self.plain.setGeometry(QtCore.QRect(x, y, width, height))
        self.plain.insertPlainText(self.text)
        self.font = QtGui.QFont()
        self.font.setPointSize(fontsize)
        self.font.setFamily(font)
        self.plain.setFont(self.font)
        # self.plain.installEventFilter(self)

    @property
    def text(self) -> str:
        """@property text"""

        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """text.setter"""

        self._text = value
        self.plain.setPlainText(value)

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
        """@property text"""

        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """text.setter"""

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
        """@property text"""

        return self._value

    @text.setter
    def text(self, value: str) -> None:
        """text.setter"""

        self._text = value
        self.spinbox.setValue(value)

    def getText(self) -> str:
        """:returns the text(value) of the spinbox"""

        return self.spinbox.value()


def updateLbls(focus: int=None):
    """Updates lbls"""

    if focus == 1:
        lblNetto.text = 'Your remaining budget: {0:.2f}{1}'.format(calculateResult(), comboBoxCur.getText().split(" ")[1])
        lblNettoBank.text = 'Your remaining bank balance: {0:.2f}{1}'.format(calculateBank(), comboBoxCur.getText().split(' ')[1])
    else:
        lblNetto.text = 'Your remaining budget: {0:.2f}{1}'.format(calculateResult(), comboBoxCur.getText().split(" ")[1])
        lblBrutto.text = 'Your monthly brutto budget: {0:.2f}{1}'.format(calculateIncome(), comboBoxCur.getText().split(" ")[1])
        lblNettoBank.text = 'Your remaining bank balance: {0:.2f}{1}'.format(calculateBank(), comboBoxCur.getText().split(' ')[1])


def delSelectedItem() -> None:
    """Main handler for deleting the selected item. Gets the focus and deletes the item in it"""

    currselectOnce = lstbox.curselection()
    currselectMonth = lstboxMonth.curselection()
    currselectTakings = lstboxTakings.curselection()
    currselectTakingsMonth = lstboxTakingsMonth.curselection()
    if DELCMD == 'focus1' and currselectOnce != -1:
        try:
            dtbOnce.removeFromDtb(currselect=currselectOnce)
            lstbox.delete(currselectOnce)
            updateLbls(1)
        except IndexError:
            return
    elif DELCMD == 'focus2' and currselectMonth != -1:
        try:
            dtbMonth.removeFromDtb(currselect=currselectMonth)
            lstboxMonth.delete(currselectMonth)
            updateLbls(1)
        except IndexError:
            return
    elif DELCMD == 'focus3' and currselectTakings != -1:
        try:
            dtbTakings.removeFromDtb(currselect=currselectTakings)
            lstboxTakings.delete(currselectTakings)
            updateLbls()
        except IndexError:
            return
    elif DELCMD == 'focus4' and currselectTakingsMonth != -1:
        try:
            dtbTakingsMonth.removeFromDtb(currselect=currselectTakingsMonth)
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
            expInfo.text = ''
            updateLbls(1)
    elif chbMonthly.checkbox.isChecked():
        if lstboxMonth.add('month'):
            expNameTxt.text = ''
            expPriceTxt.text = ''
            expInfo.text = ''
            updateLbls(1)
    elif chbTakings.checkbox.isChecked():
        if lstboxTakings.add('taking'):
            expNameTxt.text = ''
            expPriceTxt.text = ''
            expInfo.text = ''
            updateLbls()
    elif chbTakingsMonth.checkbox.isChecked():
        if lstboxTakingsMonth.add('takingMonth'):
            expNameTxt.text = ''
            expPriceTxt.text = ''
            expInfo.text = ''
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
        dtbOnce.dataEntry(text[1], text[0], user.username, text[2])
        updateLbls(1)
    elif DELCMD == 'focus2' and currselectMonth != -1:
        text = dtbMonth.getRowValuesById(currselectMonth, 1, 2, 3)
        lstboxMonth.insertItems(currselectMonth + 1, lstboxMonth.listbox.currentItem().text())
        dtbMonth.dataEntry(text[1], text[0], user.username, text[2])
        updateLbls(1)
    elif DELCMD == 'focus3' and currselectTakings != -1:
        text = dtbTakings.getRowValuesById(currselectTakings, 1, 2, 3)
        lstboxTakings.insertItems(currselectTakings + 1, lstboxTakings.listbox.currentItem().text())
        dtbTakings.dataEntry(text[1], text[0], user.username, text[2])
        updateLbls()
    elif DELCMD == 'focus4' and currselectTakingsMonth != -1:
        text = dtbTakingsMonth.getRowValuesById(currselectTakingsMonth, 1, 2, 3)
        lstboxTakingsMonth.insertItems(currselectTakingsMonth + 1, lstboxTakingsMonth.listbox.currentItem().text())
        dtbTakingsMonth.dataEntry(text[1], text[0], user.username, text[2])
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
        dtbOnce.destroy()
        dtbMonth.destroy()
        dtbOldOnce.destroy()
        dtbTakings.destroy()
        dtbTakingsMonth.destroy()
        move(path, newPath)
        path = newPath
        writeToTxtFile(dirfile, path + '/ExpenseTracker/')
        restart()


def addListToDtb(price: float, exp: str, t: str, moreInfo: str = None) -> None:
    """Adds parameters to database"""

    global user
    if t == 'once':
        dtbOnce.dataEntry(float(price), exp, user.username, moreInfo)
    elif t == 'month':
        dtbMonth.dataEntry(float(price), exp, user.username, moreInfo)
    elif t == 'taking':
        dtbTakings.dataEntry(float(price), exp, user.username, moreInfo)
    elif t == 'takingMonth':
        dtbTakingsMonth.dataEntry(float(price), exp, user.username, moreInfo)
    elif t == 'user':
        user = User(exp, price, moreInfo)
    else:
        raise ValueError


def addListToJson(name: str, password: str) -> None:
    """Adds name and password to groups.json"""

    with open('C:/tmp/groups.json') as file:
        data = json.load(file)

    data['groups'][name] = []
    data['passwords'][name] = password

    with open('C:/tmp/groups.json', 'w') as file:
        json.dump(data, file, indent=4)


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
    """restarts application"""

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

def showUserToExpense():
    """Shows a messagebox displaying which user added this item"""
    
    curselectOnce = lstbox.curselection()
    curselectMonth = lstboxMonth.curselection()
    curselectTakings = lstboxTakings.curselection()
    curselectTakingsMonth = lstboxTakingsMonth.curselection()
    if curselectOnce or curselectMonth or curselectTakings or curselectTakingsMonth != -1:
        if curselectOnce != -1 and DELCMD == 'focus1':
            expenses = dtbOnce.readFromDtb()[::-1][curselectOnce]
        elif curselectMonth != -1 and DELCMD == 'focus2':
            expenses = dtbMonth.readFromDtb()[::-1][curselectMonth]
        elif curselectTakings != -1 and DELCMD == 'focus3':
            expenses = dtbTakings.readFromDtb()[::-1][curselectTakings]
        elif curselectTakingsMonth != -1 and DELCMD == 'focus4':
            expenses = dtbTakingsMonth.readFromDtb()[::-1][curselectTakingsMonth]
        if english:
            if expenses[3] != globalUser:
                QtWidgets.QMessageBox.information(mainWin,
                                                  'User', f'The user "{expenses[3]}" added expense/taking "{expenses[0]}" for {expenses[1]}{comboBoxCur.getText().split(" ")[1]}.')
            else:
                QtWidgets.QMessageBox.information(mainWin,
                                                  'User', f'The global user added expense/taking "{expenses[0]}" for {expenses[1]}{comboBoxCur.getText().split(" ")[1]}.')
        elif german:
            if expenses[3] != globalUser:
                QtWidgets.QMessageBox.information(mainWin,
                                                  'User', f'Der Benutzer "{expenses[3]}" hat die Ausgabe/Einnahme "{expenses[0]}" für {expenses[1]}{comboBoxCur.getText().split(" ")[1]} hinzugefügt.')
            else:
                QtWidgets.QMessageBox.information(mainWin,
                                                  'User', f'Der algemeine Benutzer hat die Ausgabe/Einnahme "{expenses[0]}" für {expenses[1]}{comboBoxCur.getText().split(" ")[1]} hinzugefügt.')
    

def readFromTxtFile(pa: str, typ: str):
    """Reads from text file. Valid typ params: 'str', 'float'"""

    try:
        with open(pa, 'r') as f:
            if typ == 'float':
                return float(f.readline())
            elif typ == 'str':
                r = f.readline()
                return r
            raise ValueError('Invalid type!')
    except FileNotFoundError:
        f = open(pa, 'w+')
        f.close()


def writeToTxtFile(pa: str, text: str) -> None:
    """Writes to text file in write mode"""

    with open(pa, 'w') as f:
        f.write(str(text))


def calculateResult(userName: str='NONE') -> float:
    """Returns the end result of the expense calculation"""

    if userName == 'NONE':
        userName = user.username

    result = 0
    for usr in dtbUser.getUsers():
        if usr[0] == userName:
            if usr[0] in groups:

                with open('C:/tmp/groups.json') as file:
                    data = json.load(file)

                for us in data['groups'][usr[0]]:
                    if us not in groups:
                        result += calculateIncome(us) - (dtbOnce.cal(us) + dtbMonth.cal(us))
                break
            result += calculateIncome(userName) - (dtbOnce.cal(userName) + dtbMonth.cal(userName))
            break
    return round(result, 2)


def calculateIncome(userName: str='NONE') -> float:
    """Returns the sum of all the monthly income sources"""
    
    if userName == 'NONE':
        userName = user.username

    income = 0
    for usr in dtbUser.getUsers():
        if usr[0] == userName:
            if usr[0] in groups:

                with open('C:/tmp/groups.json') as file:
                    data = json.load(file)

                for us in data['groups'][usr[0]]:
                    if us not in groups:
                        income += dtbTakings.cal(us) + dtbTakingsMonth.cal(us)
                break
            income += dtbTakings.cal(userName) + dtbTakingsMonth.cal(userName)
            break
    return round(income, 2)


def calculateBank(userName: str='NONE') -> float:
    """Returns the money left from your bank ballance"""

    try:
        if userName == 'NONE':
            userName = user.username

        balance = 0
        for usr in dtbUser.getUsers():
            if usr[0] == userName:
                if usr[0] in groups:

                    with open('C:/tmp/groups.json') as file:
                        data = json.load(file)

                    for us in data['groups'][usr[0]]:
                        if us not in groups:
                            try:
                                balance += dtbUser.getUserBalance(us)[0][0] + calculateIncome(us) - dtbOnce.cal(us) - dtbMonth.cal(us)
                            except IndexError:
                                pass
                    break
                balance += dtbUser.getUserBalance(usr[0])[0][0] + calculateIncome(userName) - dtbOnce.cal(userName) - dtbMonth.cal(userName)
                break
        return round(balance, 2)
    except TypeError:
        return setBankBalance()


def setBankBalance() -> float:
    """sets bankBalance, also sets user.balance"""

    if english:
        inpt, okpressed = QtWidgets.QInputDialog.getDouble(None, 'Get Bank Deposit', 'Please enter your current bank balance',
                                                           min=0, decimals=2)
    elif german:
        inpt, okpressed = QtWidgets.QInputDialog.getDouble(None, 'Bankguthaben', 'Bitte gib dein Bankguthaben ein',
                                                           min=0, decimals=2)
    if okpressed:
        user.balance = str(inpt)
        dtbUser.cursor.execute('Update User SET BankBalance = ? WHERE Username = ?', (user.balance, user.username))
        dtbUser.conn.commit()
        return float(user.balance)
    exit()


def setBankBalanceBtn():
    """btn handler to set balance"""

    setBankBalance()
    updateLbls()
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


def changeLanguageEnglish(win=None) -> None:
    """Changes language to english"""

    try:
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
        moreInfoBtn.text = 'More Info'
        userOriginBtn.text = 'See user'
        if user.username == globalUser:
            editUserBtn.text = 'Edit Users'
        if win:
            win.addBtnEdit.text = 'Add'
            win.editBtnEdit.text = 'Edit'
            win.lblGroup.text = 'User Groups'
            win.lblUser.text = 'User'
            win.userInfoBtnEdit.text = 'Show User info'
            win.deleteBtnEdit.text = 'Delete'
            win.lblinfoUsername.text = 'Username'
            win.lblinfoPassword.text = 'Password'
            win.chbAddUser.text = 'User'
            win.chbAddUserGroup.text = 'User Group'
            win.chbAddUserToGroup.text = 'User in User Group'
            win.lblinfoBalance.text = 'Bank Balance'
            win.lblUserGroup.text = 'Users in Group'
    except NameError:
        pass


def changeLanguageGerman(win=None) -> None:
    """Changes language to german"""

    addBtn.text = 'Hinzufügen'
    delBtn.text = 'Löschen'
    moreInfoBtn.text = 'Mehr Infos'
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
    userOriginBtn.text = 'Benutzer anzeigen'
    if user.username == globalUser:
        editUserBtn.text = 'Benutzer verwalten'
    if win:
        win.addBtnEdit.text = 'Hinzufügen'
        win.editBtnEdit.text = 'Editieren'
        win.lblGroup.text = 'Benutzer Gruppen'
        win.lblUser.text = 'Benutzer'
        win.userInfoBtnEdit.text = 'Zeig Benutzer Info'
        win.deleteBtnEdit.text = 'Löschen'
        win.lblinfoUsername.text = 'Benutzername'
        win.lblinfoPassword.text = 'Passwort'
        win.chbAddUser.text = 'Benutzer'
        win.chbAddUserGroup.text = 'Benutzergruppe'
        win.chbAddUserToGroup.text = 'Benutzer in Gruppe'
        win.lblinfoBalance.text = 'Bankguthaben'
        win.lblUserGroup.text = 'Benutzer in Gruppe'


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

        for user in dtbUser.getUsers():
            dtbUser.updateUser(balance=calculateBank(user[0]), username=user[0])

        for data in dtbOnce.getAllRecords():
            dtbOldOnce.dataEntry(data[2], data[1], moreInfo=data[3])
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
    """btn handler for showing yearly graph"""

    if english:
        showGraph('year', 'Expenses of the last year', 'month', 'price')
    elif german:
        showGraph('year', 'Ausgaben des letzten Jahres', 'Monat', 'Preis')


def showMonthGraph() -> None:
    """btn handler for showing monthly graph"""

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
    f = open('C:/tmp/groups.json', 'w')
    data = {'groups': {'global': []}, 'passwords': {}}
    json.dump(data, f, indent=4)
    open(dirfile, 'w+')
    open(expenseDtbPath, 'w+')
    open(path + 'FirstTime.txt', 'w+')
    open(path + 'LastOpened.txt', 'w+')
    f.close()

def chb1CommandHandler() -> None:
    """chbCommandHandler, unchecks any other chbs"""
    
    global categoryType
    if categoryType != 'Expense':
        catInptTxt.clear()
        for catg in expCategories:
            catInptTxt.addItems(catg)
            categoryType = 'Expense'
    chbOneTime.unckeckAny(False, chbMonthly, chbTakings, chbTakingsMonth)


def chb2CommandHandler() -> None:
    """chbCommandHandler, unchecks any other chbs"""

    global categoryType
    if categoryType != 'Expense':
        catInptTxt.clear()
        for catg in expCategories:
            catInptTxt.addItems(catg)
            categoryType = 'Expense'
    chbMonthly.unckeckAny(False, chbOneTime, chbTakings, chbTakingsMonth)


def chb3CommandHandler() -> None:
    """chbCommandHandler, unchecks any other chbs"""

    global categoryType
    if categoryType != 'Taking':
        catInptTxt.clear()
        for catg in takCategories:
            catInptTxt.addItems(catg)
            categoryType = 'Taking'
    chbTakings.unckeckAny(False, chbMonthly, chbOneTime, chbTakingsMonth)

def chb4CommandHandler() -> None:
    """chbCommandHandler, unchecks any other chbs"""

    global categoryType
    if categoryType != 'Taking':
        catInptTxt.clear()
        for catg in takCategories:
            catInptTxt.addItems(catg)
            categoryType = 'Taking'
    chbTakingsMonth.unckeckAny(False, chbMonthly, chbOneTime, chbTakings)

def chb5CommandHandler() -> None:
    """chbCommandHandler, unchecks any other chbs"""

    global userWin
    userWin.UsernameTxt.textbox.show()
    userWin.PasswordTxt.textbox.show()
    userWin.BalanceTxt.textbox.show()
    userWin.lblinfoUsername.label.show()
    userWin.lblinfoPassword.label.show()
    userWin.lblinfoBalance.label.show()
    userWin.lblinfoUsername.text = 'Username'
    userWin.chbAddUser.unckeckAny(False, userWin.chbAddUserGroup, userWin.chbAddUserToGroup)

def chb6CommandHandler() -> None:
    """chbCommandHandler, unchecks any other chbs"""

    global userWin
    userWin.UsernameTxt.textbox.show()
    userWin.PasswordTxt.textbox.show()
    userWin.BalanceTxt.textbox.hide()
    userWin.lblinfoUsername.label.show()
    userWin.lblinfoPassword.label.show()
    userWin.lblinfoBalance.label.hide()
    userWin.lblinfoUsername.text = 'Group name'
    userWin.chbAddUserGroup.unckeckAny(False, userWin.chbAddUser, userWin.chbAddUserToGroup)

def chb7CommandHandler() -> None:
    """chbCommandHandler, unchecks any other chbs"""

    global userWin
    userWin.chbAddUserToGroup.unckeckAny(False, userWin.chbAddUserGroup, userWin.chbAddUser)

    userWin.lstboxUsersInGroup.listbox.clear()
    userWin.UsernameTxt.textbox.hide()
    userWin.PasswordTxt.textbox.hide()
    userWin.BalanceTxt.textbox.hide()
    userWin.lblinfoUsername.label.hide()
    userWin.lblinfoPassword.label.hide()
    userWin.lblinfoBalance.label.hide()

    curselectUser = userWin.lstboxUsers.curselection()
    curselectUserGroup = userWin.lstboxUserGroup.curselection()
    try:
        selection = userWin.lstboxUserGroup.listbox.currentItem().text().split(',')[0].strip('"')
    except AttributeError:
        # QtWidgets.QMessageBox.information(userWin, 'No selection', 'Please select a user and a user group to display')
        return
    jsonData = readFromJson()['groups'][selection]
    for data in jsonData:
        userWin.lstboxUsersInGroup.insertItems(0, data)


def edit() -> None:
    """Function to handle the edit window"""

    global editWin, currselectMonthEdit, currselectOnceEdit, currselectTakingsEdit, currselectTakingsMonthEdit
    editWin = Editor()
    currselectOnceEdit = lstbox.curselection()
    currselectMonthEdit = lstboxMonth.curselection()
    currselectTakingsEdit = lstboxTakings.curselection()
    currselectTakingsMonthEdit = lstboxTakingsMonth.curselection()
    if user.username not in groups:
        if currselectOnceEdit != -1 or currselectMonthEdit != -1 or currselectTakingsEdit != -1 or currselectTakingsMonthEdit != -1:

            # insert all texts
            if DELCMD == 'focus1' and currselectOnceEdit != -1:
                values = dtbOnce.getRowValuesById(currselectOnceEdit, 1, 2, 3, 4, 5, 6)
            elif DELCMD == 'focus2' and currselectMonthEdit != -1:
                values = dtbMonth.getRowValuesById(currselectMonthEdit, 1, 2, 3, 4, 5, 6)
            elif DELCMD == 'focus3' and currselectTakingsEdit != -1:
                values = dtbTakings.getRowValuesById(currselectTakingsEdit, 1, 2, 3, 4, 5, 6)
            elif DELCMD == 'focus4' and currselectTakingsMonthEdit != -1:
                values = dtbTakingsMonth.getRowValuesById(currselectTakingsMonthEdit, 1, 2, 3, 4, 5, 6)
            
            editWin.lblDateEdit.text = f'This expense was added on {values[3]}-{values[4]}-{values[5]}'
            editWin.expNameTxtEdit.text = str(values[0])
            editWin.expPriceTxtEdit.text = '{0:.2f}'.format((float(values[1])))
            editWin.expInfoEdit.text = str(values[2])

            editWin.show()
    else:
        QtWidgets.QMessageBox.critical(None, 'Failed', "Can't edit when logged into a group")


def readFromJson(pa: str='C:/tmp/groups.json'):
    """Reads json and returns it"""

    with open(pa) as file:
        return json.load(file)


def userEdit():
    """Function used to handle the editor for the users"""

    # I had to use the global statement for the window so it doesnt get destroyed immediately when I try to open it
    global userWin
    userWin = UserEditor()
    userWin.chbAddUser.check()

    for data in dtbUser.readUserDtb():
        userWin.lstboxUsers.insertItems(0, '"{1}", "{2}", "{0:.2f}"'.format(data[2], data[0], data[1]))

    with open('C:/tmp/groups.json') as file:
        data = json.load(file)

    for group in data['groups']:
        pw = readFromJson()['passwords'][group]
        userWin.lstboxUserGroup.insertItems(0, f'"{group}", "{pw}"')

    userWin.show()


def addUser():
    """chb1.checked: Adds user to lstbox, dtbase
       chh2.checked: Adds user group
       chb3.checked: Adds selected user to user group"""

    global userWin
    if userWin.chbAddUser.checkbox.isChecked():
        if userWin.lstboxUsers.add('user'):
            User(userWin.UsernameTxt.getText(), userWin.PasswordTxt.getText(), userWin.BalanceTxt.getText())
            userWin.UsernameTxt.text = ''
            userWin.PasswordTxt.text = ''
            userWin.BalanceTxt.text = ''
    elif userWin.chbAddUserGroup.checkbox.isChecked():
        if userWin.lstboxUserGroup.add('user group'):
            userWin.UsernameTxt.text = ''
            userWin.PasswordTxt.text = ''
    elif userWin.chbAddUserToGroup.checkbox.isChecked():
        userWin.lstboxUsersInGroup.add('user to group', window=userWin)


def editUser():
    """In User lstbox focus: Messabebox: Username, Password, Balance with next, ok, cancel btns"""
    
    global userEditWin, userWin

    curselectUser = userWin.lstboxUsers.curselection()
    curselectGroup = userWin.lstboxUserGroup.curselection()

    values = []
    if curselectUser != -1 and userWin.chbAddUser.checkbox.isChecked():
        userEditWin = UserInfoEditor('user')
        values = dtbUser.getRowValuesById(curselectUser, 1, 2, 3)
        userEditWin.usernameTxt.text = values[0]
        userEditWin.pwTxt.text = values[1]
        userEditWin.balanceTxt.text = str(values[2])
        userEditWin.show()
    elif curselectGroup != -1 and userWin.chbAddUserGroup.checkbox.isChecked():
        userEditWin = UserInfoEditor('group')
        text = userWin.lstboxUserGroup.listbox.currentItem().text().split(',')
        values.append(text[0].strip('"'))
        values.append(text[1].strip('"').strip().strip('"'))
        userEditWin.usernameTxt.text = values[0]
        userEditWin.pwTxt.text = values[1]
        userEditWin.show()

def deleteUser():
    """In user lstbox focus: removes User and all instances of him in groups
       In userGroup focus: removes group
       In usersInGroup focus: delete user from group"""

    global userWin
    currselectUser = userWin.lstboxUsers.curselection()
    currselectGroup = userWin.lstboxUserGroup.curselection()
    currselectUserInGroup = userWin.lstboxUsersInGroup.curselection()

    if userWin.chbAddUser.checkbox.isChecked() and currselectUser != -1:
        with open('C:/tmp/groups.json') as file:
            data = json.load(file)

        text = userWin.lstboxUsers.listbox.currentItem().text().split(',')[0].strip('"')
        if text != globalUser:
            for group in data['groups']:
                try:
                    data['groups'][group].remove(text)
                except ValueError:
                    pass
            
            with open('C:/tmp/groups.json', 'w') as file:
                json.dump(data, file, indent=4)
            userWin.lstboxUsers.delete(currselectUser)
            dtbUser.removeFromDtb(currselect=currselectUser)
            dtbOnce.removeFromDtb(username=text)
            dtbMonth.removeFromDtb(username=text)
            dtbTakings.removeFromDtb(username=text)
            dtbTakingsMonth.removeFromDtb(username=text)
        else:
            QtWidgets.QMessageBox.critical(None, 'Failed', "You can't delete the global user")

    elif userWin.chbAddUserGroup.checkbox.isChecked() and currselectGroup != -1:
        with open('C:/tmp/groups.json') as file:
            data = json.load(file)

        text = userWin.lstboxUserGroup.listbox.currentItem().text().split(',')[0].strip('"')

        if text != globalUser:
            data['groups'].pop(text)
            data['passwords'].pop(text)
            
            for group in data['groups']:
                data['groups'][group].remove(text)

            with open('C:/tmp/groups.json', 'w') as file:
                json.dump(data, file, indent=4)
            userWin.lstboxUserGroup.delete(currselectGroup)
            dtbUser.removeFromDtb(username=text)
            dtbOnce.removeFromDtb(username=text)
            dtbMonth.removeFromDtb(username=text)
            dtbTakings.removeFromDtb(username=text)
            dtbTakingsMonth.removeFromDtb(username=text)
        else:
            QtWidgets.QMessageBox.critical(None, 'Failed', "You can't delete the global group")

    elif userWin.chbAddUserToGroup.checkbox.isChecked()and currselectUserInGroup != -1:
        with open('C:/tmp/groups.json') as file:
            data = json.load(file)

        text = userWin.lstboxUsersInGroup.listbox.currentItem().text().split(',')[0].strip('"')
        if userWin.lstboxUserGroup.listbox.currentItem().text().split(',')[0].strip('"') != globalUser:
            data['groups'][userWin.lstboxUserGroup.listbox.currentItem().text().split(',')[0].strip('"')].remove(text)

            with open('C:/tmp/groups.json', 'w') as file:
                json.dump(data, file, indent=4)
            userWin.lstboxUsersInGroup.delete(currselectUserInGroup)
        else:
            QtWidgets.QMessageBox.critical(None, 'Failed', "You can't remove users from global group!")


def showUserInfo() -> None:
    """messagebox showing all her/his items(edited, added), name and balance, the same for group but not for useringroup"""

    global userWin, msgbox
    curselectUser = userWin.lstboxUsers.curselection()
    curselectGroup = userWin.lstboxUsers.curselection()

    # initialize the msgbox
    msgbox = QtWidgets.QMessageBox()
    msgbox.setIcon = QtWidgets.QMessageBox.information

    if userWin.chbAddUser.checkbox.isChecked() and curselectUser != -1:
        global infoWin
        username = userWin.lstboxUsers.listbox.currentItem().text().split(',')[0].strip('"')
        if english:
            infoWin = UserInfo(title=f'Information about user {username}')
            infoWin.lblInfo.text = f'All expenses of the user {username}'
            infoWin.lblUsername.text = f'Username: {username}'
        elif german:
            infoWin = UserInfo(title=f'Informationen über den Benutzer {username}')
            infoWin.lblInfo.text = f'Alle Ausgaben des Benutzers {username}'
            infoWin.lblUsername.text = f'Benutzername: {username}'

        # insert every item that belongs to the user into the listbox
        for data in belongsToUser(username, dtbOnce.readFromDtb()):
            try:
                infoWin.lstbox.insertItems(0, '{1}, {0:.2f}{2}'.format(data[1], data[0], comboBoxCur.getText().split(" ")[1]))
            except IndexError:
                pass
        for data in belongsToUser(username, dtbMonth.readFromDtb()):
            try:
                infoWin.lstbox.insertItems(0, '{1}, {0:.2f}{2}'.format(data[1], data[0], comboBoxCur.getText().split(" ")[1]))
            except IndexError:
                pass
        infoWin.show()

    elif userWin.chbAddUserGroup.checkbox.isChecked() and curselectGroup != -1:
        groupname = userWin.lstboxUserGroup.listbox.currentItem().text().split(',')[0].strip('"')
        if english:
            infoWin = UserInfo(title=f'Information about the group {groupname}')
            infoWin.lblInfo.text = f'All users in group {groupname}'
            infoWin.lblUsername.text = f'Groupname: {groupname}'
        elif german:
            infoWin = UserInfo(title=f'Informationen über die Gruppe {groupname}')
            infoWin.lblInfo.text = f'Alle Benutzer in der Gruppe {groupname}'
            infoWin.lblUsername.text = f'Gruppenname: {groupname}'
        
        # insert groupnames into the listbox
        group = Group(groupname)
        for user in group.getUsersFromGroup():
            try:
                infoWin.lstbox.insertItems(0, user)
            except IndexError:
                pass
        infoWin.show()
    
    
def belongsToUser(username, dtbElements: list) -> list:
    """Returns all the elements that belong to the user"""

    results = []
    for element in dtbElements:
        if str(element[3]) == username:
            results.append(element)
    return results


#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
if __name__ == '__main__':
    global categoryType
    # Initialize main app
    # app = ApplicationContext()
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
    globalUser = 'global'
    categoryType = 'Expense'

    # Try to read from dirfile and set path = standart if it catches error
    try:
        _path = readFromTxtFile(dirfile, 'str')
        if _path is not None:
            path = _path
        else:
            path = 'C:/tmp/ExpenseTracker/'
    except:
        path = 'C:/tmp/ExpenseTracker/'

    isFirstTime = isFirstTime()
    # All the first Time things like creating files and entering config data
    if isFirstTime:
        createFiles()
        today = datetime.today()
        writeToTxtFile(path + 'LastOpened.txt', f'{str(today.month)};{str(today.year)}')
        writeToTxtFile(path + 'FirstTime.txt', 'False')
        writeToTxtFile(dirfile, path)

        name, msgboxUSER = QtWidgets.QInputDialog.getText(mainWin, 'User', 'Register or sign in if you already have an account.\nUsername: ')
        pw, msgboxPW = QtWidgets.QInputDialog.getText(mainWin, 'User', 'Password: ')

        # get all group names
        with open('C:/tmp/groups.json') as file:
            jsonGroups = json.load(file)

        groups = [key for key, _ in jsonGroups['groups'].items()]
    else:
        expenseDtbPath = path + 'Expenses.db'

    # Database
    dtbOnce = DataBase(expenseDtbPath, 'OneTimeExpenseTable')
    dtbMonth = DataBase(expenseDtbPath, 'MonthlyExpenseTable')
    dtbOldOnce = DataBase(path + 'OldExpenses.db', 'OneTimeExpenseTable')
    dtbTakings = DataBase(expenseDtbPath, 'OneTimeTakingsTable')
    dtbTakingsMonth = DataBase(expenseDtbPath, 'MonthlyTakingsTable')
    dtbUser = DataBase(path + 'User.db', 'User', enc='user')
    dtbExpCategory = DataBase(path + 'Category.db', 'ExpenseCategory', enc='category')
    dtbTakCategory = DataBase(path + 'Category.db', 'TakingsCategory', enc='category')

    expCategories = dtbExpCategory.readFromCategoryDtb()
    takCategories = dtbTakCategory.readFromCategoryDtb()
    expCat = Category('All')
    takCat = Category('All', exp=False)

    if isFirstTime:
        user = User(name, pw)
        user.balance = setBankBalance()

        dtbUser.cursor.execute('Update User SET BankBalance = ? WHERE Username = ?', (user.balance, user.username, ))
        dtbUser.conn.commit()
        user.balance = dtbUser.readUserDtb(user.username)[0][2]
    else:
        # get all group names
        with open('C:/tmp/groups.json') as file:
            jsonGroups = json.load(file)

        groups = [key for key, _ in jsonGroups['groups'].items()]

        # creating user
        name, msgboxUSER = QtWidgets.QInputDialog.getText(mainWin, 'User', 'Register or sign in if you already have an account.\nUsername: ')
        if msgboxUSER:
            pw, msgboxPW = QtWidgets.QInputDialog.getText(mainWin, 'User', 'Password: ')
        else:
            exit()
        if msgboxPW and msgboxUSER:
            user = User(name, pw)
        else:
            exit()

    # set user balance
    if user.username != globalUser:
        user.balance = dtbUser.readUserDtb(user.username)[0][2]

    # Drop down menu for currency
    comboBoxCur = ComboBox(mainWin, x=800, y=100, height=40, width=80, fontsize=11)
    comboBoxCur.addItems('Euro €', 'Dollar $', 'Pound £')
    comboBoxLang = ComboBox(mainWin, x=1120, y=0, width=80, height=40, fontsize=11)
    comboBoxLang.addItems('English', 'Deutsch')

    # Check wether the month has ended
    if monthEnd():
        user.balance = dtbUser.readUserDtb(user.username)[0][2]
    
    #listbox insertion
    dataOnce = []
    dataMonth = []
    dataTakings = []
    dataTakingsMonth = []
    if user.username in groups:
        for grp in groups:
            if user.username == grp:
                group = Group(grp)
                usersInGroup = group.getUsersFromGroup()
                for usr in usersInGroup:
                    users = dtbUser.readUserDtb()
                    for us in users:
                        if us[0] == group.groupName:
                            users = us
                    
                    for data in belongsToUser(usr, dtbOnce.readFromDtb()):
                        dataOnce.append(data)
                    for data in belongsToUser(usr, dtbMonth.readFromDtb()):
                        dataMonth.append(data)
                    for data in belongsToUser(usr, dtbTakings.readFromDtb()):
                        dataTakings.append(data)
                    for data in belongsToUser(usr, dtbTakingsMonth.readFromDtb()):
                        dataTakingsMonth.append(data)

    else:
        for data in belongsToUser(user.username, dtbOnce.readFromDtb()):
            dataOnce.append(data)
        for data in belongsToUser(user.username, dtbMonth.readFromDtb()):
            dataMonth.append(data)
        for data in belongsToUser(user.username, dtbTakings.readFromDtb()):
            dataTakings.append(data)
        for data in belongsToUser(user.username, dtbTakingsMonth.readFromDtb()):
            dataTakingsMonth.append(data)

    for data in dataOnce:
        try:
            lstbox.insertItems(0, '{1}, {0:.2f}{2}'.format(data[1], data[0], comboBoxCur.getText().split(" ")[1]))
        except IndexError:
            pass
    for data in dataMonth:
        try:
            lstboxMonth.insertItems(0, '{1}, {0:.2f}{2}'.format(data[1], data[0], comboBoxCur.getText().split(" ")[1]))
        except IndexError:
            pass
    for data in dataTakings:
        try:
            lstboxTakings.insertItems(0, '{1}, {0:.2f}{2}'.format(data[1], data[0], comboBoxCur.getText().split(" ")[1]))
        except IndexError:
            pass
    for data in dataTakingsMonth:
        try:
            lstboxTakingsMonth.insertItems(0, '{1}, {0:.2f}{2}'.format(data[1], data[0], comboBoxCur.getText().split(" ")[1]))
        except IndexError:
            pass
        
    # Textboxes
    expNameTxt = TextBox(mainWin, x=350, y=100, width=220, height=40, fontsize=16, placeHolder='Name')
    expPriceTxt = TextBox(mainWin, x=590, y=100, width=210, height=40, fontsize=16, placeHolder='Price')
    mainWin.setTabOrder(expNameTxt, expPriceTxt) #! not working! "QWidget::setTabOrder: 'first' and 'second' must be in the same window"

    # SpinBox for Multiplier
    expMultiTxt = SpinBox(mainWin, text=1, x=350, y=190, width=70, height=30, mincount=1)

    # Extra Info Text
    expInfo = PlainText(mainWin, text='', x=350, y=250, width=510, height=100, fontsize=11, placeHolder='Write more info about your expense here...')

    # Category input Text
    catInptTxt = ComboBox(mainWin, x=450, y=190, width=129, height=30, fontsize=11, isEditable=True)
    for catg in expCategories:
        catInptTxt.addItems(catg)

    # Labels
    totalIncome = calculateIncome()
    totalexp = calculateResult()
    totalBank = calculateBank()
    lblInfoCatInpt = Label(mainWin, x=450, y=170, width=200, fontsize=13, height=20, text='Enter Category')
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
    delBtn = Button(mainWin, text='Delete', command=delSelectedItem, x=230, y=140, height=35, width=90, key='Delete')
    dupBtn = Button(mainWin, text='Duplicate', command=dupSelectedItem, x=230, y=180, height=35, width=90, key='Ctrl+D')
    editBtn = Button(mainWin, text='Edit', command=edit, x=230, y=240, height=35, width=90, key='Ctrl+E')
    dirBtn = Button(mainWin, text='Select\nDirec-\ntory', command=selectDirMoveFiles, x=1150, y=530, height=70, width=50)
    clearBtn = Button(mainWin, text='Clear List', command=clearD, x=230, y=280, height=35, width=90, key='Ctrl+C')
    moreInfoBtn = Button(mainWin, text='More Info', command=showExpenseInfo, x=230, y=340, height=35, width=90, key='Ctrl+F')
    showExpGraph_30 = Button(mainWin, text='30-Day-Graph', command=showMonthGraph, x=230, y=440, height=35, width=90)
    showExpGraph_365 = Button(mainWin, text='1-Year-Graph', command=showYearGraph, x=230, y=480, height=35, width=90)

    # If the global User is called, then display editUserBtn
    if user.username not in groups:
        setBankBtn = Button(mainWin, text='Set Balance', command=setBankBalanceBtn, x=230, y=540, height=35, width=90)
    elif user.username != globalUser:
        pass
    else:
        editUserBtn = Button(mainWin, text='Edit Users', command=userEdit, x=230, y=540, height=35, width=90)
    
    userOriginBtn = Button(mainWin, text='See user', command=showUserToExpense, x=230, y=380, height=35, width=90)

    # start the app
    mainWin.show()
    # sys.exit(app.app.exec_())
    sys.exit(app.exec_())
