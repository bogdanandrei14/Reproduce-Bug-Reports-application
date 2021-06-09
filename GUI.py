from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget
from PyQt5.uic import loadUi

from Repository import readData, splitData, validateFilename, writeDataParsedBugReport, writeDataIdentifiedS2RSentences, \
    writeFinalReport, isNullFilename
from Service import identifyS2RSentences, getIndividualS2RFinal, getFinalSteps, getFinalData, getStepsToReproduceForGui
from config import originalDir, extention, parsedDir, identifiedStepsDir, resultDir, resultExtention, dep_matcher


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("view/MainWindow.ui", self)
        self.initUi()

    def initUi(self):
        """
        Initialize UI elements
        """
        self.setWindow()
        self.setEvents()

    def setWindow(self):
        """
        Set window properties
        """
        self.setGeometry(100, 100, 1030, 535)
        self.setWindowTitle("Reproduce bug report")
        self.setWindowIcon(QIcon("icons/repairBug.png"))
        # centering the window
        # geometry of the main window
        qr = self.frameGeometry()
        # center point of screen
        cp = QDesktopWidget().availableGeometry().center()
        # move rectangle's center point to screen's center point
        qr.moveCenter(cp)
        # center
        self.move(qr.topLeft())
        # set progress bar visibility
        self.progressBar.setVisible(False)

    def setEvents(self):
        """
        Set button events
        """
        self.pushButton_run.clicked.connect(self.generateReport)
        self.pushButton_run.setCursor(QtCore.Qt.PointingHandCursor)
        self.pushButton_clearData.clicked.connect(self.refreshResultArea)
        self.pushButton_clearData.setCursor(QtCore.Qt.PointingHandCursor)

    def generateReport(self):
        """
        Generate modified bug report with better steps to reproduce
        """
        self.hideFeedback()
        self.progressBarAnimation()
        filename = self.lineEdit_filename.text()
        print("file: ", filename)
        originalFile, parsedFile, identifiedStepsFile, resultFile = self.getFilesName(filename)
        isFileNameOK = validateFilename(originalFile)
        nullFilename = isNullFilename(filename)
        if not nullFilename:
            message = "Numele fisierului introdus nu poate fi nul!"
            self.incorrectExecution(message)
            return
        if not isFileNameOK:
            message = "Numele fisierului introdus este incorect!"
            self.incorrectExecution(message)
            return
        idData, titleData, descriptionData = readData(originalFile)
        print("ID GUI: ", idData)
        print("TITLE GUI: ", titleData)
        paragraphs = splitData(descriptionData)
        print("PARAGRAPHS GUI: ", paragraphs)
        if writeDataParsedBugReport(parsedFile, idData, titleData, paragraphs):
            self.correctParsedReportExecution()
        else:
            self.incorrectParsedReportExecution()
            message = "Eroare la executie"
            self.incorrectExecution(message)
            return
        print("PRIMA SCRIERE GUI")
        s2rsentences, keywords = identifyS2RSentences(paragraphs)
        print("S2RSENTENCES GUI: ", s2rsentences)
        print("KEYWORDS GUI: ", keywords)
        if writeDataIdentifiedS2RSentences(identifiedStepsFile, idData, titleData, paragraphs, s2rsentences):
            self.correctStepsReportExecution()
        else:
            self.incorrectStepsReportExecution()
            message = "Eroare la executie"
            self.incorrectExecution(message)
            return
        print("A DOUA SCRIERE")
        individualSteps = getIndividualS2RFinal(s2rsentences, keywords)
        print("INDIVIDUAL STEPS GUI: ", individualSteps)
        finalSteps = getFinalSteps(individualSteps, dep_matcher, keywords)
        print("FINAL STEPS GUI: ", finalSteps)
        final_id_title_data, final_description_data = getFinalData(idData, titleData, paragraphs, individualSteps, finalSteps)
        print("FINAL ID TITLE GUI: ", final_id_title_data)
        print("FINAL DESCRIPTION GUI: ", final_description_data)
        if writeFinalReport(resultFile, final_id_title_data, final_description_data):
            self.correctFinalReportExecution()
        else:
            self.incorrectFinaldReportExecution()
            message = "Eroare la executie"
            self.incorrectExecution(message)
            return
        print("ULTIMA SCRIERE")
        uiSteps = getStepsToReproduceForGui(finalSteps)
        # give feedback for succesful execution
        self.verifyResultLabel.setVisible(True)
        self.verifyResultIcon.setVisible(True)
        self.verifyResultLabel.setText("Executie cu succes!")
        self.verifyResultLabel.setStyleSheet("color: #ffffff")
        self.verifyResultIcon.setPixmap(QPixmap("icons/correctIcon.png"))
        self.verifyResultIcon.setScaledContents(True)
        print("DUPA ICONITA GUI OK")
        # display steps to reproduce and generated bug report
        self.label_stepsToReproduce.setText("\n".join(uiSteps))
        print("DUPA PRINT PASI")
        self.importBugReport(resultFile)
        print("DUPA PRINT BUG REPORT GUI")


    def correctParsedReportExecution(self):
        """
        Set the feedback elements for the correct execution up to the first checkpoint:
        generate bug report splitted into paragraphs
        """
        self.verifyParsedReportLabel.setVisible(True)
        self.verifyParsedReportIcon.setVisible(True)
        self.verifyParsedReportLabel.setText("Generare raport impartit in paragrafe")
        self.verifyParsedReportLabel.setStyleSheet("color: #ffffff")
        self.verifyParsedReportIcon.setPixmap(QPixmap("icons/okIcon.png"))
        self.verifyParsedReportIcon.setScaledContents(True)

    def incorrectParsedReportExecution(self):
        """
        Set the feedback elements for the incorrect execution up to the first checkpoint:
        generate bug report splitted into paragraphs
        """
        self.verifyParsedReportLabel.setVisible(True)
        self.verifyParsedReportIcon.setVisible(True)
        self.verifyParsedReportLabel.setText("Eroare la generarea raportului impartit in paragrafe")
        self.verifyParsedReportLabel.setStyleSheet("color: #ffffff")
        self.verifyParsedReportIcon.setPixmap(QPixmap("icons/x.png"))
        self.verifyParsedReportIcon.setScaledContents(True)

    def correctStepsReportExecution(self):
        """
        Set the feedback elements for the correct execution up to the second checkpoint:
        generate bug report with identified step to reproduce sentences
        """
        self.verifyStepsReportLabel.setVisible(True)
        self.verifyStepsReportIcon.setVisible(True)
        self.verifyStepsReportLabel.setText("Generare raport cu propozitiile S2R identificate")
        self.verifyStepsReportLabel.setStyleSheet("color: #ffffff")
        self.verifyStepsReportIcon.setPixmap(QPixmap("icons/okIcon.png"))
        self.verifyStepsReportIcon.setScaledContents(True)

    def incorrectStepsReportExecution(self):
        """
        Set the feedback elements for the incorrect execution up to the second checkpoint:
        generate bug report with identified step to reproduce sentences
        """
        self.verifyStepsReportLabel.setVisible(True)
        self.verifyStepsReportIcon.setVisible(True)
        self.verifyStepsReportLabel.setText("Eroare la generarea raportului cu propozitiile S2R identificate")
        self.verifyStepsReportLabel.setStyleSheet("color: #ffffff")
        self.verifyStepsReportIcon.setPixmap(QPixmap("icons/x.png"))
        self.verifyStepsReportIcon.setScaledContents(True)

    def correctFinalReportExecution(self):
        """
        Set the feedback elements for the correct execution up to the final point:
        generate final bug report
        """
        self.verifyFinalReportLabel.setVisible(True)
        self.verifyFinalReportIcon.setVisible(True)
        self.verifyFinalReportLabel.setText("Generare raport final")
        self.verifyFinalReportLabel.setStyleSheet("color: #ffffff")
        self.verifyFinalReportIcon.setPixmap(QPixmap("icons/okIcon.png"))
        self.verifyFinalReportIcon.setScaledContents(True)

    def incorrectFinaldReportExecution(self):
        """
        Set negative feedback elements for the incorrect execution up to the final point:
        generate final bug report
        """
        self.verifyFinalReportLabel.setVisible(True)
        self.verifyFinalReportIcon.setVisible(True)
        self.verifyFinalReportLabel.setText("Eroare la generarea raportului final")
        self.verifyFinalReportLabel.setStyleSheet("color: #ffffff")
        self.verifyFinalReportIcon.setPixmap(QPixmap("icons/x.png"))
        self.verifyFinalReportIcon.setScaledContents(True)

    def hideFeedback(self):
        """
        Hide feedback elements
        """
        self.verifyResultIcon.setVisible(False)
        self.verifyResultLabel.setVisible(False)
        self.verifyParsedReportLabel.setVisible(False)
        self.verifyParsedReportIcon.setVisible(False)
        self.verifyStepsReportLabel.setVisible(False)
        self.verifyStepsReportIcon.setVisible(False)
        self.verifyFinalReportLabel.setVisible(False)
        self.verifyFinalReportIcon.setVisible(False)

    def incorrectExecution(self, message):
        """
        Set final feedback elements of incorrect execution
        :param message: string - error message
        """
        self.verifyResultLabel.setVisible(True)
        self.verifyResultIcon.setVisible(True)
        self.verifyResultLabel.setText(message)
        self.verifyResultLabel.setStyleSheet("color: #ffffff")
        self.verifyResultIcon.setPixmap(QPixmap("icons/incorrectIcon.png"))
        self.verifyResultIcon.setScaledContents(True)

    def importBugReport(self, filename):
        """
        Import and display generated bug report
        :param filename: string - file name of generated bug report
        """
        if filename.endswith('.txt'):
            with open(filename, 'r') as f:
                data = f.readlines()
                print("GUI DATA: ", data)
                self.label_bugReport.setText("".join(data))

    def getFilesName(self, filename):
        """
        Create name of files base on input from user
        :param filename: string - file name
        :return: originalFile: string - original bug report file
                parsedFile: string - splitted file by paragraphs
                identifiedStepsFile: string - file with identified step to reproduce sentences
                resultFile: string - final bug report file
        """
        originalFile = originalDir + str(filename) + extention
        parsedFile = parsedDir + str(filename) + extention
        identifiedStepsFile = identifiedStepsDir + str(filename) + extention
        resultFile = resultDir + str(filename) + resultExtention
        return originalFile, parsedFile, identifiedStepsFile, resultFile

    def refreshResultArea(self):
        """
        Clear fields in steps to reproduce area
        """
        self.label_stepsToReproduce.setText("")
        self.label_bugReport.setText("")
        self.lineEdit_filename.setText("")
        self.hideFeedback()

    def progressBarAnimation(self):
        """
        Create progress bar animation for loading effect
        """
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        completed = 0
        while completed < 100:
            completed += 0.0002
            self.progressBar.setValue(completed)
        self.progressBar.setVisible(False)
