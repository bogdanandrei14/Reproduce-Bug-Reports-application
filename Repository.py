import xml.etree.ElementTree as ET
import nltk
import nltk.corpus
import re
import os.path
from os import path


def readData(filename):
    """
    Read bug report data from xml file
    Return collected data
    :param filename: string - file name or full path of file
    :return: idData: string
            titleData: string
            descriptiondData: string
    """
    tree = ET.parse(filename)
    root = tree.getroot()
    id = root.find("id")
    idData = id.text
    title = root.find("title")
    titleData = title.text
    description = root.find("description")
    descriptionData = description.text
    return idData, titleData, descriptionData


def validateFilename(filename):
    """
    Check if file name or path exists
    Return True if file name is valid, otherwise False
    :param filename: string
    :return: boolean
    """
    return path.exists(filename)

def isNullFilename(filename):
    """
    Check if a string is null
    Return True if string is not null, otherwise False
    :param filename: string
    :return: boolean
    """
    if len(filename) != 0:
        return True
    return False

def splitData(text):
    """
    The function processes a text given as parametter and split it into paragraphs and sentences
    :param text:
    :return: dictionary with key - integer and value - list of strings
    """
    description = {}
    id = 1
    sentences = []
    match_line = []
    startDigitRegex = r'[0-9]+\..*'
    for line in text.splitlines():
        print("line: ", line)
        match = re.match(startDigitRegex, line)
        print("match: ", match)
        if bool(match):
            match_line.append(line)
            print("list de line:", match_line)
            sentences += match_line
            match_line = []
            print("sentencesssssss: ", sentences)
        # elif "->" in line or ">" in line:
        #     sentences += line
        elif len(line.strip()) != 0:
            aux_sentences = nltk.sent_tokenize(line)
            print("aux_sen: ", aux_sentences)
            sentences += aux_sentences
            print("sentenceessss 2: ", sentences)
        else:
            description[id] = sentences
            print("description: ",description)
            id += 1
            sentences = []
    if len(sentences) != 0:
        description[id] = sentences
    return description

def writeDataParsedBugReport(file, idData, titleData, paragraphs):
    """
    Write splitted data into paragraphs and sentences to xml file. If file doesn't exist it will be created.
    Return True if the execution is completed successfully and False if errors occur
    :param file: string
    :param idData: string
    :param titleData: string
    :param paragraphs: dictionary with key - integer and value - list of strings
    :return: boolean
    """
    try:
        # create the file structure
        bug = ET.Element('bug')
        id = ET.SubElement(bug, 'id')
        id.text = idData
        title = ET.SubElement(bug, 'title')
        title.text = titleData
        description = ET.SubElement(bug, 'description')
        for key in paragraphs:
            paragraph = ET.SubElement(description, 'paragraph')
            paragraph.set('id', str(key))
            idSentenceCounter = 1
            for value in paragraphs[key]:
                sentence = ET.SubElement(paragraph, 'sentence')
                sentence.set('id', str(key) + "." + str(idSentenceCounter))
                sentence.text = value
                idSentenceCounter += 1

        # create a new XML file with the results
        parsed_bug_report_data = ET.tostring(bug, encoding='UTF-8', xml_declaration=True)
        parsed_bug_report = open(file, "wb")
        parsed_bug_report.write(parsed_bug_report_data)
        return True
    except OSError or IOError:
        return False

def writeDataIdentifiedS2RSentences(file, idData, titleData, paragraphs, s2rParagraphs):
    """
    Write splitted data into paragraphs and sentences to xml file. If file doesn't exist it will be created.
    Add specific attribute "sr=x" to certain tags.
    Return True if the execution is completed successfully and False if errors occur
    :param file: string
    :param idData: string
    :param titleData: string
    :param paragraphs: dictionary with key - integer and value - list of strings
    :param s2rParagraphs: dictionary with key - integer and value - list of strings
    :return: boolean
    """
    try:
        # create the file structure
        bug = ET.Element('bug')
        id = ET.SubElement(bug, 'id')
        id.text = idData
        title = ET.SubElement(bug, 'title')
        title.text = titleData
        description = ET.SubElement(bug, 'description')
        for key in paragraphs:
            paragraph = ET.SubElement(description, 'paragraph')
            paragraph.set('id', str(key))
            idSentenceCounter = 1
            for value in paragraphs[key]:
                sentence = ET.SubElement(paragraph, 'sentence')
                print("val: ", value)
                print("s2rpar: ", list(s2rParagraphs.values()))
                for s2rValue in list(s2rParagraphs.values()):
                    if value in s2rValue:
                        print("in if da")
                        sentence.set('sr', 'x')
                sentence.set('id', str(key) + "." + str(idSentenceCounter))
                sentence.text = value
                idSentenceCounter += 1

        # create a new XML file with the results
        identified_s2r_in_bug_report_data = ET.tostring(bug, encoding='UTF-8', xml_declaration=True)
        identified_s2r_in_bug_report = open(file, "wb")
        identified_s2r_in_bug_report.write(identified_s2r_in_bug_report_data)
        return True
    except OSError or IOError:
        return False

def writeFinalReport(file, id_title_data, description_data):
    """
    Write processed data to txt file. If file doesn't exist it will be created.
    Return True if the execution is completed successfully and False if errors occur
    :param file: string
    :param id_title_data: string
    :param description_data: dictionary with key - integer and value - list of strings
    :return: boolean
    """
    try:
        with open(file, 'w') as f:
            for sentence in id_title_data:
                f.write(sentence)
                f.write('\n\n')
            for key in description_data:
                for sentence in description_data[key]:
                    f.write(sentence)
                    f.write('\n')
                f.write('\n')
        f.close()
        return True
    except OSError or IOError:
        return False


