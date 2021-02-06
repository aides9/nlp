"""
Created on Tue Aug 18 20:56:22 2020
@author: Bac
"""
from PyQt5.QtGui import QTextCursor, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import *
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.uic import loadUi
from cfset import ConfusionSet
from ngram import NGramProb
import pandas as pd


class CheckingThread(QtCore.QThread):
    taskFinished = QtCore.pyqtSignal(list)

    def __init__(self, text, cf_set, ngram_prob):
        super(CheckingThread, self).__init__()
        self.text = text
        self.cf_set = cf_set
        self.ngram_prob = ngram_prob

    def run(self):
        split_list = self.text.split()
        first_word = split_list[0]
        last_word = split_list[-1]
        list_error = []
        print("[Info] Start spell checking process")
        # Checking non-word error for the first word
        if self.cf_set.is_nonword_error(input_string=first_word):
            list_error.append(0)
        # Checking non-word error for the last word
        if self.cf_set.is_nonword_error(last_word):
            position_cursor = len(self.text) - len(last_word)
            list_error.append(position_cursor)
        if len(self.text) >= 3:
            trigrams = list(zip(split_list, split_list[1:], split_list[2:]))
            current_position = len(first_word) + 1
            for idx, trigram in enumerate(trigrams):
                word_consider = trigram[1]
                # if word_consider in string.punctuation:
                #     continue
                if self.cf_set.is_nonword_error(word_consider):
                    list_error.append(current_position)
                    print('Non-word error: ', word_consider)
                    print('Position: ', current_position)
                else:
                    sentence = trigram[0] + ' ' + word_consider + ' ' + trigram[2]
                    prob = self.ngram_prob.ngram_cal(sentence, 2)
                    if prob == 0:
                        list_error.append(current_position)
                        print('Real-word error: ', word_consider)
                        print('Position: ', current_position)
                current_position += 1 + len(word_consider)
        self.taskFinished.emit(list_error)


class LoadDictThread(QtCore.QThread):

    def __init__(self, listWidget, cf_set):
        super(LoadDictThread, self).__init__()
        self.listWidget = listWidget
        self.cf_set = cf_set

    def run(self):
        self.listWidget.addItems(self.cf_set.get_vocabularies())


class FilterDictThread(QtCore.QThread):

    def __init__(self, listWidget, cf_set, keyword):
        super(FilterDictThread, self).__init__()
        self.listWidget = listWidget
        self.dict = cf_set.get_vocabularies()
        self.keyword = keyword

    def run(self):
        if self.keyword == '':
            self.listWidget.clear()
            self.listWidget.addItems(self.dict)
        else:
            filteredList = [word for word in self.dict if self.keyword.lower() in word]
            self.listWidget.clear()
            self.listWidget.addItems(filteredList)


class MainWindow(QMainWindow):

    def __init__(self):
        self.cf_set = ConfusionSet()
        self.ngram_prob = NGramProb()
        # Message Box
        self.msgBox = QMessageBox()
        self.msgBox.setWindowTitle("Spell checking in process....")
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText("Spell checking in progress")
        self.msgBox.setModal(False)
        QMainWindow.__init__(self)
        loadUi("mainWindow.ui", self)
        self.cursor = self.textEdit.textCursor()
        self.format = QtGui.QTextCharFormat()
        self.format.setBackground(QtGui.QBrush(QtGui.QColor("red")))
        self.textEdit.textChanged.connect(self.onTextChanged)
        self.mTimer = QTimer()
        self.mTimer.setSingleShot(True)
        self.mTimer.timeout.connect(self.process_text)
        # Add custom context menu to text edit
        self.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.textEdit.customContextMenuRequested.connect(self.generate_context_menu)
        # Add item to list view
        loadDictThread = LoadDictThread(self.listWidget, self.cf_set)
        loadDictThread.run()
        # Filter
        self.lineEdit.textChanged.connect(self.keywordChange)
        self.mTimerKeyword = QTimer()
        self.mTimerKeyword.setSingleShot(True)
        self.mTimerKeyword.timeout.connect(self.filter)

    def onTextChanged(self):
        self.mTimer.start(1000)

    def process_text(self):
        text = self.textEdit.toPlainText()
        if len(text) == 0:
            return
        self.textEdit.blockSignals(True)
        self.msgBox.show()
        taskThread = CheckingThread(text, self.cf_set, self.ngram_prob)
        taskThread.taskFinished.connect(self.finish_checking)
        taskThread.run()

    def finish_checking(self, list_error):
        self.cursor.select(QtGui.QTextCursor.Document)
        self.cursor.setCharFormat(QtGui.QTextCharFormat())
        self.cursor.clearSelection()
        for error_position in list_error:
            self.cursor.setPosition(error_position, QTextCursor.MoveAnchor)
            self.cursor.movePosition(QtGui.QTextCursor.EndOfWord, 1)
            self.cursor.setCharFormat(self.format)
        print("[Info] End spell checking process")
        self.msgBox.hide()
        self.textEdit.blockSignals(False)

    def generate_context_menu(self, location):
        menu = self.textEdit.createStandardContextMenu()
        menu.exec(self.mapToGlobal(location))

    def replace(self):
        tc = self.textEdit.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        tc.insertText('misa');
        print(tc.selectedText())

    def keywordChange(self):
        self.mTimerKeyword.start(500)

    def filter(self):
        keyword = self.lineEdit.text()
        filterDictThread = FilterDictThread(self.listWidget, self.cf_set, keyword)
        filterDictThread.run()


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
