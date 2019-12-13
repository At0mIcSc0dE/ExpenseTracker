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

# pylint: disable=unused-argument
# pylint: disable=unused-variable
from tkinter import Button, Checkbutton, Label, Text, Listbox, Entry, Tk, Frame, END, BooleanVar, StringVar, CENTER, ANCHOR, sys, OptionMenu, Scrollbar, LEFT, Y, Toplevel
from tkinter.messagebox import showinfo
from tkinter.filedialog import askdirectory
from tkinter.simpledialog import askstring
from os import execl, mkdir
from os.path import exists
from shutil import move
from time import time
from datetime import datetime
from sqlite3 import connect
from matplotlib.pyplot import plot, legend, title, xlabel, ylabel, show
from concurrent.futures import ThreadPoolExecutor
from numpy import array


global budget, path, expenseDtbPath
class Application(Frame):
    def __init__(self, geometry: str, title: str):
        self.root = Tk()
        self.root.title(title)
        self.geometry = self.root.geometry(geometry)

        self.root.resizable(False, False)

        Frame.__init__(self, self.root)


    def start(self):
        self.root.mainloop()



class Editor:
    def __init__(self, geometry: str, title: str):
        self.toplevel = Toplevel(app.root)
        self.title = self.toplevel.title(title)
        self.geometry = self.toplevel.geometry(geometry)

        self.toplevel.resizable(False, False)


    def close(self):
        self.toplevel.destroy()


    @staticmethod
    def apply(selectionOnce: tuple, selectionMonth: tuple, n, p, info):
        def wrapper():
            name = n.getText()
            price = p.getText()
            moreInfo = info.get(1.0, END)
            if selectionOnce != ():
                lstbox.update(selectionOnce[0], name, price)
                dtbOnce.update(selectionOnce[0], name, price, moreInfo)
                lblNetto.update()
            elif selectionMonth != ():
                lstboxMonth.update(selectionMonth[0], name, price)
                dtbMonth.update(selectionMonth[0], name, price, moreInfo)
                lblNetto.update()
        return wrapper


    def cancel(self):
        self.close()



class DataBase:
    def __init__(self, databasePath: str, table: str):
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


    def getRowValuesById(self, rowid: int, *elemIndex: int) -> list:
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


    def dataEntry(self, price: float, expTime: str, exp: str, moreInfo: str = None):
        day, month, year = str(datetime.fromtimestamp(time()).strftime('%d-%m-%Y')).split('-')
        if expTime == 'once':
            self.cursor.execute(
                'INSERT INTO ' + self.table + ' (Expense, Price, MoreInfo, Day, Month, Year) VALUES (?, ?, ?, ?, ?, ?)',
                (exp, price, moreInfo.rstrip('\n'), day, month, year))
            self.conn.commit()
        elif expTime == 'month':
            self.cursor.execute(
                'INSERT INTO ' + self.table + ' (Expense, Price, MoreInfo, Day, Month, Year) VALUES (?, ?, ?, ?, ?, ?)',
                (exp, price, moreInfo.rstrip('\n'), day, month, year))
            self.conn.commit()
        else:
            raise ValueError


    def clearDtb(self):
        if chbOneTime.isChecked():
            self.cursor.execute('DELETE FROM ' + self.table)
            self.conn.commit()
            lstbox.listbox.delete(0, 'end')
            lblNetto.update()
        elif chbMonthly.isChecked():
            self.cursor.execute('DELETE FROM ' + self.table)
            self.conn.commit()
            lstboxMonth.listbox.delete(0, 'end')
            lblNetto.update()


    def removeFromDtb(self, currselect: tuple):
        self.cursor.execute('SELECT ID FROM ' + self.table)
        rws = self.cursor.fetchall()
        rws = rws[::-1]
        rw = rws[currselect[0]]
        self.cursor.execute('DELETE FROM ' + self.table + ' WHERE ID = ?', (str(rw[0]),))
        self.conn.commit()
        self.updateId()


    def updateId(self):
        self.cursor.execute('SELECT * FROM ' + self.table)
        rows = self.cursor.fetchall()

        r = []
        for row in range(len(rows)):
            r.append(row + 1)
        with ThreadPoolExecutor() as executor:
            executor.map(self._update, r, rows)


    def _update(self, index, row):
        self.cursor.execute('UPDATE ' + self.table + ' SET ID = ? WHERE ID = ?', (index, row[0]))
        self.conn.commit()


    def cal(self):
        self.cursor.execute('SELECT Price FROM ' + self.table)
        expenses = self.cursor.fetchall()
        totalExpense = 0
        for expense in expenses:
            totalExpense += float(expense[0])
        return totalExpense


    def readFromDtb(self):
        self.cursor.execute('SELECT Expense, Price FROM ' + self.table)
        rows = self.cursor.fetchall()
        for row in rows:
            row = array(row)
            if self == dtbOnce:
                lstbox.listbox.insert(0, f'{row[0]}, {row[1]}{varCur.get().split(" ")[1]}')
            elif self == dtbMonth:
                lstboxMonth.listbox.insert(0, f'{row[0]}, {row[1]}{varCur.get().split(" ")[1]}')
        return rows


    def getAllRecords(self):
        self.cursor.execute('SELECT * FROM ' + self.table)
        return self.cursor.fetchall()


    def update(self, rowid: int, name: str, price: float, moreInfo: str):
        self.cursor.execute('SELECT ID FROM ' + self.table)
        ids = self.cursor.fetchall()
        ids = ids[::-1]
        ids = ids[rowid][0]
        self.cursor.execute('UPDATE ' + self.table + ' SET Expense = ?, Price = ?, MoreInfo = ? WHERE ID = ?', (name, price, moreInfo, ids))
        self.conn.commit()



class Btn:
    def __init__(self, root, text: str, command, x: int, y: int, height: int, width: int, key: str = None):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.key = key
        self.button = Button(root, text=text, command=command, height=height, width=width)

        self.button.pack()
        self.button.place(x=self.x, y=self.y)

        if key is not None:
            root.bind(key, command)



class TxtBox:
    def __init__(self, root , x: int, y: int, font: tuple = ('Verdana', 16)):
        self.textbox = Entry(root, font=font)
        self.x = x
        self.y = y

        self.textbox.pack(ipady=100)
        self.textbox.place(x=self.x, y=self.y)


    def getText(self):
        return self.textbox.get()



class ListBox:
    def __init__(self, x: int, y: int, width: int, height: int, scrollbar: bool = False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        if scrollbar:
            scroll = Scrollbar(app.root)
            scroll.pack(side=LEFT, fill=Y)

            self.listbox = Listbox(app.root, width=self.width, height=self.height, yscrollcommand=scroll.set)
            scroll.config(command=self.listbox.yview)
        else:
            self.listbox = Listbox(app.root, width=self.width, height=self.height)

        self.listbox.pack()
        self.listbox.place(x=self.x, y=self.y)


    def remove(self, item: str):
        self.listbox.delete(item)


    def add(self, expenseTime, txt: str = None, currselect: tuple = None, index: int = 0):
        if isinstance(expenseTime, tuple):
            self.listbox.insert(index, txt)
            name = txt.split(',')[0]
            currency = varCur.get().split(' ')[1]
            price = txt.split(' ')[1].split(currency)[0]
            expTime = expenseTime[1]
            moreInfo = ''
            if expenseTime == ('dup', 'once'):
                moreInfo = dtbOnce.getRowValuesById(currselect[0], 3)
            elif expenseTime == ('dup', 'month'):
                moreInfo = dtbMonth.getRowValuesById(currselect[0], 3)
            addListToDtb(float(price), name, expTime, moreInfo[0])
            return True

        name = expNameTxt.getText()
        price = expPriceTxt.getText()
        moreInfo = expInfo.get('1.0', END)
        currency = varCur.get().split(' ')[1]
        multiplier = expMultiTxt.getText()

        # Check if valid price and multiplier input
        try:
            float(price)
            multiplier = int(multiplier)
        except:
            showinfo('Invalid Input', 'Invalid Input, try again!')
            return False

        if name and price != '':
            text = f'{name}, {price}{currency}'
            for _ in range(multiplier):
                self.listbox.insert(0, text)
                addListToDtb(price, name, expenseTime, moreInfo)
                expMultiTxt.textbox.delete(0, 'end')
                expMultiTxt.textbox.insert(END, 1)
            return True
        else:
            showinfo('Invalid Input', 'Invalid Input, try again!')
            return False


    def update(self, selection: int, name: str, price: float):
        self.listbox.delete(selection, selection+1)
        self.listbox.insert(selection, f'{name}, {price}{varCur.get().split(" ")[1]}')



class CheckBox:
    def __init__(self, root, text: str, x: int, y: int):
        self.varChecked = BooleanVar()
        self.text = text
        self.checkbox = Checkbutton(root, text=self.text, variable=self.varChecked, onvalue=True, offvalue=False)
        self.x = x
        self.y = y

        self.checkbox.pack()
        self.checkbox.place(x=self.x, y=self.y)


    @property
    def command(self):
        return self.command


    @command.setter
    def command(self, command):
        self.checkbox['command'] = command


    def isChecked(self):
        return True if self.varChecked.get() else False


    def check(self):
        self.checkbox.select()


    def uncheck(self):
        self.checkbox.deselect()



class MsgBox:
    def __init__(self, msgboxUsage: str, msgboxType: str):
        self.msgboxUsage = msgboxUsage
        self.msgboxtype = msgboxType


    def askstring(self, head, question):
        if self.msgboxtype == 'askstring': return askstring(head, question)


    def validInput(self, inpt):
        if self.msgboxUsage == 'Inflation' or 'Budget':
            try:
                float(inpt)
                return True
            except:
                return False



class Lbl:
    def __init__(self, root, text: str, x: int, y: int, height: int, width: int, font: tuple = ('Verdana', 12), center: bool = False):
        text = str(text)
        self.text = text
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.font = font
        self.strVar = StringVar(root)
        self.strVar.set(self.text)
        self.label = Label(root, height=self.height, width=self.width, font=self.font, textvariable=self.strVar)

        self.label.pack()

        if center:
            self.label.place(relx=0.5, y=self.y, anchor=CENTER)
        else:
            self.label.place(x=self.x, y=self.y)


    def getText(self):
        return self.label['text']


    def update(self):
        self.delLbl()
        makeLbl()


    def delLbl(self):
        self.label.destroy()



def delSelectedItem(event=None):
    currselectOnce = lstbox.listbox.curselection()
    if currselectOnce != ():
        dtbOnce.removeFromDtb(currselectOnce)
        lstbox.remove(ANCHOR)
        lblNetto.update()
        return
    currselectMonth = lstboxMonth.listbox.curselection()
    if currselectMonth != ():
        dtbMonth.removeFromDtb(currselectMonth)
        lstboxMonth.remove(ANCHOR)
        lblNetto.update()


def addItem(event=None):
    if chbOneTime.isChecked():
        if lstbox.add('once'):
            expNameTxt.textbox.delete(0, 'end')
            expPriceTxt.textbox.delete(0, 'end')
            expInfo.delete('1.0', END)
            lblNetto.update()
    elif chbMonthly.isChecked():
        if lstboxMonth.add('month'):
            expNameTxt.textbox.delete(0, 'end')
            expPriceTxt.textbox.delete(0, 'end')
            expInfo.delete('1.0', END)
            lblNetto.update()


def dupSelectedItem(event=None):
    currselectOnce = lstbox.listbox.curselection()
    currselectMonth = lstboxMonth.listbox.curselection()
    if currselectOnce != ():
        lstbox.add(('dup', 'once'), lstbox.listbox.get(ANCHOR), currselectOnce)
        lblNetto.update()
    elif currselectMonth != ():
        lstbox.add(('dup', 'month'), lstboxMonth.listbox.get(ANCHOR), currselectMonth)
        lblNetto.update()


def selectDirMoveFiles():
    global path
    newPath = askdirectory()
    if newPath is not path:
        dtbOnce.cursor.close()
        dtbOnce.conn.close()
        dtbMonth.cursor.close()
        dtbMonth.conn.close()
        dtbOldOnce.cursor.close()
        dtbOldOnce.conn.close()

        move(path, newPath)
        path = newPath
        writeToTxtFile(dirfile, path + '/ExpenseTracker/')
        restart()


def addListToDtb(price: float, exp: str, t: str, moreInfo: str = None):
    if t == 'once':
        dtbOnce.dataEntry(price, t, exp, moreInfo)
    elif t == 'month':
        dtbMonth.dataEntry(price, t, exp, moreInfo)
    else:
        raise ValueError


def isFirstTime():
    if exists(path + 'FirstTime.txt'):
        if readFromTxtFile(path + 'FirstTime.txt', 'str') == 'False':
            return False
        else:
            writeToTxtFile(path + 'FirstTime.txt', 'False')
            return True
    else:
        return True


def setBudget():
    msgbox = MsgBox('Budget', 'askstring')
    while True:
        inpt = msgbox.askstring('Monthly Budget', 'Please enter your monthly budget including taxes.')
        if msgbox.validInput(inpt):
            break
        else:
            exit()
    writeToTxtFile(path + 'Budget.txt', inpt)
    return inpt


def setBudgetBtn():
    setBudget()
    restart()


def restart():
    execl(sys.executable, sys.executable, *sys.argv)


def showExpenseInfo(event=None):
    while True:
        curselectOnce = lstbox.listbox.curselection()
        curselectMonth = lstboxMonth.listbox.curselection()
        try:
            infoOnce = dtbOnce.getRowValuesById(curselectOnce[0], 3)
            showinfo('Product Info', ''.join(infoOnce))
            break
        except:
            infoMonth = dtbMonth.getRowValuesById(curselectMonth[0], 3)
            showinfo('Product Info', ''.join(infoMonth))
            break


def readFromTxtFile(pa: str, typ: str):
    with open(pa, 'r') as f:
        if typ == 'float':
            return float(f.readline())
        elif typ == 'str':
            return f.readline()
        else:
            raise ValueError('Invalid type!')


def writeToTxtFile(pa: str, text: str):
    with open(pa, 'w') as f:
        f.write(str(text))


def calculateResult():
    return round(float(budget) - (dtbOnce.cal() + dtbMonth.cal()), 2)


def makeLbl():
    totexp = calculateResult()
    Lbl(app.root, text=f'Your monthly brutto budget: {budget}{varCur.get().split(" ")[1]}', x=455, y=20, height=3, width=40,
        center=True)
    Lbl(app.root, text=f'Your remaining budget: {totexp}{varCur.get().split(" ")[1]}', x=455, y=550, height=3, width=40,
        center=True)


def clearD():
    if chbOneTime.isChecked():
        dtbOnce.clearDtb()
    elif chbMonthly.isChecked():
        dtbMonth.clearDtb()


def isMonthEnd():
    lastDate = readFromTxtFile(path + 'LastOpened.txt', 'str')
    today = datetime.today()
    lastMonth, lastYear = lastDate.split(';')
    lastMonth = int(lastMonth)
    lastYear = int(lastYear)
    if today.month > lastMonth and today.year == lastYear:
        writeToTxtFile(path + 'LastOpened.txt', f'{str(today.month)};{str(today.year)}')
        return True
    elif today.year > lastYear:
        writeToTxtFile(path + 'LastOpened.txt', f'{str(today.month)};{str(today.year)}')
        return True
    return False


def monthEnd():
    if isMonthEnd():
        for data in dtbOnce.getAllRecords():
            dtbOldOnce.dataEntry(data[2], 'once', data[1], data[3])
            dtbOnce.clearDtb()
            showinfo('New Month', 'A new month has begun, all One-Time-Expenses were deleted!')


def initPlot(l1, l2, label: str, tile: str, xlabl: str, ylabl: str, linestyle: str = None):
    plot(l1, l2, marker='o', linestyle=linestyle, label=label, color='k')
    legend()
    title(tile)
    xlabel(xlabl)
    ylabel(ylabl)
    show()


def lstSum(lst: list) -> float:
    org = 0
    for elem in lst: org += elem
    return org


def showGraph(t: str, tile: str, xaxis: str, yaxis: str):
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

    p = []
    for value in valueLst:
        p.append(value[1])
        dic[value[0]] = round(lstSum(p), 2)

    initPlot(list(dic.keys()), list(dic.values()), 'One-Time Expenses', tile, xaxis, yaxis, linestyle='--')


def showYearGraph():
    showGraph('year', 'Expenses of the last year', 'month', 'price')


def showMonthGraph():
    showGraph('month', 'Expenses of the last month', 'days', 'price')


def createFiles():
    try:
        mkdir('C:/tmp/')
    except:
        pass
    try:
        mkdir(path)
    except:
        pass
    open(dirfile, 'w+')
    open(path + 'Budget.txt', 'w+')
    open(expenseDtbPath, 'w+')
    open(path + 'FirstTime.txt', 'w+')
    open(path + 'LastOpened.txt', 'w+')
    f = open(path + 'OldExpenses.db', 'w+')
    f.close()


def edit():
    currselectOnce = lstbox.listbox.curselection()
    currselectMonth = lstboxMonth.listbox.curselection()
    if currselectOnce or currselectMonth != ():
        editWin = Editor('800x400', 'Editor')

        # Textboxes
        expNameTxtEdit = TxtBox(editWin.toplevel, 10, 100)
        expPriceTxtEdit = TxtBox(editWin.toplevel, 330, 100)
        expInfoEdit = Text(editWin.toplevel, height=10, width=60)
        expInfoEdit.pack()
        expInfoEdit.place(x=10, y=165)

        #Info Labels
        lblinfoExpEdit = Lbl(editWin.toplevel, 'Expense name:', -7, 50, 2, 16)
        lblinfoPriceEdit = Lbl(editWin.toplevel, 'Price per piece: ', 317, 50, 2, 16)
        lblCur = Lbl(editWin.toplevel, varCur.get().split(' ')[1], 610, 100, 1, 1)

        #insert all texts
        if currselectOnce != ():
            values = dtbOnce.getRowValuesById(currselectOnce[0], 1, 2, 3, 4, 5, 6)
            expNameTxtEdit.textbox.insert(0, values[0])
            expPriceTxtEdit.textbox.insert(0, values[1])
            expInfoEdit.insert(1.0, values[2])
            lblDate = Lbl(editWin.toplevel, f'This expense was added on {values[3]}-{values[4]}-{values[5]}', 0, 10, 1, 35)

            editWin.apply = editWin.apply(currselectOnce, currselectMonth, expNameTxtEdit, expPriceTxtEdit, expInfoEdit)
        elif currselectMonth != ():
            values = dtbMonth.getRowValuesById(currselectMonth[0], 1, 2, 3, 4, 5, 6)
            expNameTxtEdit.textbox.insert(0, values[0])
            expPriceTxtEdit.textbox.insert(0, values[1])
            expInfoEdit.insert(1.0, values[2])
            lblDate = Lbl(editWin.toplevel, f'This expense was added on {values[3]}-{values[4]}-{values[5]}', 0, 10, 1, 35)

            editWin.apply = editWin.apply(currselectOnce, currselectMonth, expNameTxtEdit, expPriceTxtEdit, expInfoEdit)

        # Buttons
        cancelBtn = Btn(editWin.toplevel, text='Cancel', command=editWin.cancel, x=710, y=350, height=2, width=10)
        applyBtn = Btn(editWin.toplevel, text='Apply', command=editWin.apply, x=620, y=350, height=2, width=10)
        okBtn = Btn(editWin.toplevel, text='Ok', command=editWin.cancel, x=530, y=350, height=2, width=10)
        delBtnEdit = Btn(editWin.toplevel, text='Delete', command=delSelectedItem, x=10, y=350, height=2, width=10, key='<Delete>')



if __name__ == '__main__':
    # Initialize main app
    app = Application('1200x600', 'ExpenseTracker')
    lstbox = ListBox(20, 50, 35, 18, True)
    lstboxMonth = ListBox(20, 400, 35, 12)
    expenseDtbPath = 'C:/tmp/ExpenseTracker/Expenses.db'
    dirfile = 'C:/tmp/dir.txt'

    # Try to read from dirfile and set path = standart if it catches error
    try:
        path = readFromTxtFile(dirfile, 'str') if readFromTxtFile(dirfile, 'str') != '' else 'C:/tmp/ExpenseTracker/'
    except:
        path = 'C:/tmp/ExpenseTracker/'

    # All the first Time things like creating files and entering config data
    if isFirstTime():
        createFiles()
        writeToTxtFile(path + 'LastOpened.txt', str(datetime.today().month))
        writeToTxtFile(path + 'FirstTime.txt', 'False')
        writeToTxtFile(dirfile, path)
        budget = setBudget()
    else:
        expenseDtbPath = path + 'Expenses.db'
        budget = readFromTxtFile(path + 'Budget.txt', 'float')

    # Drop down menu for currency
    currencies = ['Dollar $', 'Euro €', 'Pound £']
    varCur = StringVar(app.root)
    varCur.set(currencies[1])
    optmenuCur = OptionMenu(app.root, varCur, *currencies)
    optmenuCur.pack()
    optmenuCur.place(x=850, y=100)

    # Database
    dtbOnce = DataBase(expenseDtbPath, 'OneTimeExpenseTable')
    dtbMonth = DataBase(expenseDtbPath, 'MonthlyExpenseTable')
    dtbOldOnce = DataBase(path + 'OldExpenses.db', 'OneTimeExpenseTable')
    dtbOnce.readFromDtb()
    dtbMonth.readFromDtb()

    # Textboxes
    expNameTxt = TxtBox(app.root, 250, 100)
    expPriceTxt = TxtBox(app.root, 570, 100)
    expMultiTxt = TxtBox(app.root, 350, 170, font=('Verdana', 10))
    expMultiTxt.textbox.insert(END, 1)

    # Extra Info Text
    expInfo = Text(app.root, height=15, width=60)
    expInfo.pack()
    expInfo.place(x=350, y=200)

    # Labels
    totalexp = calculateResult()
    lblBrutto = Lbl(app.root, text=f'Your monthly brutto budget: {budget}{varCur.get().split(" ")[1]}', x=455, y=20, height=3, width=40, center=True)
    lblNetto = Lbl(app.root, text=f'Your remaining budget: {totalexp}{varCur.get().split(" ")[1]}', x=455, y=550, height=3, width=40, center=True)
    lbloneTime = Lbl(app.root, 'One-Time-Expenses', 20, 5, 2, 16)
    lblmonthly = Lbl(app.root, 'Monthly-Expenses', 20, 350, 2, 16)
    lblinfoExp = Lbl(app.root, 'Expense name:', 234, 50, 2, 16)
    lblinfoPrice = Lbl(app.root, 'Price per piece: ', 555, 50, 2, 16)
    lblinfoMulti = Lbl(app.root, 'Multiplier:', 350, 145, 1, 10, font=('Verdana', 10))
    lblinfoControls = Lbl(app.root,
                          'Controls:\n\n Add to list:           "Enter"\n\n   Remove from list:  "Delete"\n\n       Show more info:    "Control-F"',
                          860, 200, 7, 30)

    # Checkboxes
    chbOneTime = CheckBox(app.root, 'One-Time-Expense', 1040, 95)
    chbMonthly = CheckBox(app.root, 'Monthly-Expense', 1040, 120)
    chbMonthly.command = chbOneTime.uncheck
    chbOneTime.command = chbMonthly.uncheck

    chbOneTime.check()

    # Check wether the month has ended
    monthEnd()

    # Buttons
    addBtn = Btn(app.root, text='Add', command=addItem, x=250, y=150, height=2, width=10, key='<Return>')
    delBtn = Btn(app.root, text='Delete', command=delSelectedItem, x=250, y=200, height=2, width=10, key='<Delete>')
    editBtn = Btn(app.root, text='Edit', command=edit, x=250, y=250, height=2, width=10, key='<Control-e>')
    dupBtn = Btn(app.root, text='Duplicate', command=dupSelectedItem, x=250, y=500, height=2, width=10, key='<Control-d>')
    dirBtn = Btn(app.root, text='Select Directory', command=selectDirMoveFiles, x=1040, y=550, height=2, width=20)
    clearBtn = Btn(app.root, text='Clear List', command=clearD, x=250, y=300, height=2, width=10)
    moreInfoBtn = Btn(app.root, text='More Info', command=showExpenseInfo, x=250, y=350, height=2, width=10, key='<Control-f>')
    updBrutto = Btn(app.root, text='Set Budget', command=setBudgetBtn, x=250, y=2, height=2, width=10)
    showExpGraph_30 = Btn(app.root, text='30-Day-Graph', command=showMonthGraph, x=250, y=400, height=2, width=10)
    showExpGraph_365 = Btn(app.root, text='1-Year-Graph', command=showYearGraph, x=250, y=450, height=2, width=10)

    app.start()