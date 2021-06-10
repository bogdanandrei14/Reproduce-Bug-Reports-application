from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget
from PyQt5.uic import loadUi
from Service import Service
from config import dep_matcher


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.service = Service()
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
        originalFile, parsedFile, identifiedStepsFile, resultFile = self.service.getFilesName(filename)
        isFileNameOK = self.service.repository.validateFilename(originalFile)
        nullFilename = self.service.repository.isNullFilename(filename)
        if not nullFilename:
            message = "Numele fisierului introdus nu poate fi nul!"
            self.incorrectExecution(message)
            return
        if not isFileNameOK:
            message = "Numele fisierului introdus este incorect!"
            self.incorrectExecution(message)
            return
        idData, titleData, descriptionData = self.service.repository.readData(originalFile)
        paragraphs = self.service.repository.splitData(descriptionData)
        if self.service.repository.writeDataParsedBugReport(parsedFile, idData, titleData, paragraphs):
            self.correctParsedReportExecution()
        else:
            self.incorrectParsedReportExecution()
            message = "Eroare la executie"
            self.incorrectExecution(message)
            return
        s2rsentences, keywords = self.service.identifyS2RSentences(paragraphs)
        if self.service.repository.writeDataIdentifiedS2RSentences(identifiedStepsFile, idData, titleData, paragraphs, s2rsentences):
            self.correctStepsReportExecution()
        else:
            self.incorrectStepsReportExecution()
            message = "Eroare la executie"
            self.incorrectExecution(message)
            return
        individualSteps = self.service.getIndividualS2RFinal(s2rsentences, keywords)
        finalSteps = self.service.getFinalSteps(individualSteps, dep_matcher, keywords)
        final_id_title_data, final_description_data = self.service.getFinalData(idData, titleData, paragraphs, individualSteps, finalSteps)
        if self.service.repository.writeFinalReport(resultFile, final_id_title_data, final_description_data):
            self.correctFinalReportExecution()
        else:
            self.incorrectFinaldReportExecution()
            message = "Eroare la executie"
            self.incorrectExecution(message)
            return
        uiSteps = self.service.getStepsToReproduceForGui(finalSteps)
        # give feedback for succesful execution
        self.verifyResultLabel.setVisible(True)
        self.verifyResultIcon.setVisible(True)
        self.verifyResultLabel.setText("Executie cu succes!")
        self.verifyResultLabel.setStyleSheet("color: #ffffff")
        self.verifyResultIcon.setPixmap(QPixmap("icons/correctIcon.png"))
        self.verifyResultIcon.setScaledContents(True)
        # display steps to reproduce and generated bug report
        self.label_stepsToReproduce.setText("\n".join(uiSteps))
        self.importBugReport(resultFile)

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
                self.label_bugReport.setText("".join(data))

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
