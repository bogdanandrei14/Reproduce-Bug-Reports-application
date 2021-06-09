import xml.etree.ElementTree as ET
from typing import List

import nltk
import os
import nltk.corpus
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

import fasttext
import os

# import pattern
# from pattern.en import lemma, lexeme
from word_forms.word_forms import get_word_forms

from nltk.tag import pos_tag, map_tag

from nltk.tokenize import LineTokenizer
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from lxml import etree
import spacy
from spacy.matcher import DependencyMatcher
from spacy.matcher import Matcher
import re
import textacy
import os

# filename = "android-mileage#3.1.1_53"
# filename = "gnucash-android#2.1.1_615"
# filename = "gnucash-android#2.1.3_620"
filename = "gnucash-android#2.2.0_699"
# filename = "gnucash-android#2.2.0_701"


originalDir = "data/0_original_bug_reports/" + filename + ".xml"
print(originalDir)
parsedDir = "data/parsed_bug_reports/" + filename + ".xml"
print(parsedDir)
identifiedStepsDir = "data/identified_s2r_in_bug_reports/" + filename + ".xml"
print(identifiedStepsDir)
resultDir = "data/result_bug_reports/" + filename + ".txt"
print(resultDir)


def readData(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    id = root.find("id")
    idData = id.text
    title = root.find("title")
    titleData = title.text
    description = root.find("description")
    descriptionData = description.text
    return idData, titleData, descriptionData


def splitData(text):
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

idData, titleData, descriptionData = readData(originalDir)
p = splitData(descriptionData)
print("titledata: ",titleData)
print("descrdata: ", descriptionData)
print("p: ", p)



def writeDataParsedBugReport(file, idData, titleData, paragraphs):
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

writeDataParsedBugReport(parsedDir, idData, titleData, p)


# define action groups

OPEN = ["open", "start", "launch", "run", "unlock", "begin", "initiate", "commence", "execute"]
LONG_CLICK = ["long click", "long tap", "hold", "long tap", "tap and hold", "keep", "maintain", "touch", "long press"]
SWIPE = ["swipe", "swipe up", "swipe down", "swipe left", "swipe right", "move", "drag"]
CLICK = ["click", "snap", "tap", "tick", "hit", "touch", "choose", "select", "pick", "press", "go", "create", "add", "check", "edit", "set"]
TYPE = ["type", "edit", "input", "enter", "insert", "write", "fill", "change", "set", "out"]
ROTATE = ["rotate", "twist", "wheel", "twist", "revolve", "turn", "go around", "change"]
allGroups = OPEN + CLICK + LONG_CLICK + TYPE + ROTATE + SWIPE
allGroupsCheck = []
allGroupsCheck.append(OPEN)
allGroupsCheck.append(LONG_CLICK)
allGroupsCheck.append(SWIPE)
allGroupsCheck.append(CLICK)
allGroupsCheck.append(TYPE)
allGroupsCheck.append(ROTATE)
print(allGroupsCheck)
# print(allGroups)

def defineActionGroups(originalActions):
    result = []
    for action in originalActions:
        for synonym in wordnet.synsets(action):
            for lemmaWord in synonym.lemmas():
                result.append(lemmaWord.name())
    return set(result)

# result = defineActionGroups(original_OPEN)
# print(result)

# OPEN = defineActionGroups(original_OPEN)
# LONG_CLICK = defineActionGroups(original_LONG_CLICK)
# CLICK = defineActionGroups(original_CLICK)
# SWIPE = defineActionGroups(original_SWIPE)
# TYPE = defineActionGroups(original_TYPE)
# ROTATE = defineActionGroups(original_ROTATE)
# print("open: ",OPEN)
# print("click: ",CLICK)

# stemming
# lemmatization



# Lemmatize with POS Tag

def getWordnetPosTag(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)


# # 1. Init Lemmatizer
# lemmatizer = WordNetLemmatizer()
#
# # 2. Lemmatize Single Word with the appropriate POS tag
# word = 'best'
# print(lemmatizer.lemmatize(word, getWordnetPosTag(word)))
#
# # 3. Lemmatize a Sentence with the appropriate POS tag
# print("postaaaags: ", [lemmatizer.lemmatize(w, getWordnetPosTag(w)) for w in nltk.word_tokenize(s)])

def verifyWordLemma(keyWords, word):
    if word in keyWords:
        return True
    else:
        return False


def identifyS2RSentences(paragraphs):
    s2rSentences = {}
    sentences = []
    lematizer = WordNetLemmatizer()
    exist = "existS2R"
    kewwords = []
    for key in paragraphs:
        for value in paragraphs[key]:
            count = 0
            print("value: ", value)
            aux_kewwords = []
            wordTokenizedSentence = word_tokenize(value)
            for word in wordTokenizedSentence:
                print("word: ", word)
                lemmatizedWord = lematizer.lemmatize(word, getWordnetPosTag(word))
                if verifyWordLemma(allGroups, lemmatizedWord.lower()):
                    print("verif: ", verifyWordLemma(allGroups, lemmatizedWord.lower()))
                    count += 1
                    aux_kewwords.append(word)
            if count > 0:
                print("key: ", key)
                print("valueok: ", value)
                print("par: ", paragraphs[key])
                sentences.append(value)
            if len(aux_kewwords) != 0:
                kewwords.append(aux_kewwords)
        if len(sentences) != 0:
            s2rSentences[key] = sentences
            sentences = []
    return s2rSentences, kewwords

s2rsentences, keywords = identifyS2RSentences(p)
print("s2rSen: ", s2rsentences)
print("keywords: ", keywords)
print("pfinal: ", p)


def writeDataIdentifiedS2RSentences(file, idData, titleData, paragraphs, s2rParagraphs):
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

writeDataIdentifiedS2RSentences(identifiedStepsDir, idData, titleData, p, s2rsentences)

# main
nlp = spacy.load("en_core_web_sm")
# doc = nlp("Action sequence: (Dictionary already loaded) Start app -> MENU -> Click on Dictionaries -> Long click on any dictionary -> change orientation when dictionary is being verified i.e popup window is still visible")
# for token in doc:
#     print("{2}({3}-{6}, {0}-{5})".format(token.text, token.tag_, token.dep_, token.head.text, token.head.tag_, token.i+1, token.head.i+1))

# main
# DEPENDENCY MATCHER USED
dep_matcher = DependencyMatcher(vocab=nlp.vocab)
# dep_pattern_2 = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'POS': 'VERB'}, 'LEMMA': {"IN": }},
#                  {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'd_object', 'RIGHT_ATTRS': {'DEP': 'dobj'}},
#                  {'LEFT_ID': 'd_object', 'REL_OP': '>', 'RIGHT_ID': 'preposition', 'RIGHT_ATTRS': {'DEP': 'prep'}},
#                  {'LEFT_ID': 'preposition', 'REL_OP': '>', 'RIGHT_ID': 'object2', 'RIGHT_ATTRS': {'DEP': 'pobj'}}
#                 ]

def getKeysList(dict):
    list = []
    for key in dict.keys():
        list.append(key)
    return list

def getDependencyMatches(doc, dependecyMatcher, dependencyPattern):
    dependecyMatcher.add('nsubj_verb_dobj', patterns=[dependencyPattern])
    dep_matches = dependecyMatcher(doc)
    return dep_matches


def getIndividualS2RSpecialCharacters(s2rSentence, regex, keywordList):
    individualS2R = []
    # startDigitRegex = '/^[0-9]/./'
    # enumerationRegex = '[->]'
    # keys = getKeysList(s2rSentences)
    # print("keys: ", keys)
    # for key in keys:
    #     for sentence in s2rSentences[key]:
    #         print("sentence: ", sentence)
    #         if sentence.startswith(startDigitRegex):
    #             individualS2R.append(sentence)
    #         elif "->" in sentence or ">" in sentence:
    print("sent to split: ", s2rSentence)
    print("keywordList: ", keywordList)
    sentences = re.split(regex, s2rSentence)
    for splitedsentence in sentences:
        print("splitted: ", splitedsentence)
        aux_regex = '[.*]*[)]'
        if len(splitedsentence) != 0:
            aux_sentences = re.split(aux_regex, splitedsentence)
            print("aux_sent: ", aux_sentences)
            if len(aux_sentences) != 1:
                for s in aux_sentences:
                    for keyword in keywordList:
                        if keyword in s:
                            individualS2R.append(s)
                        break
            else:
                individualS2R.append(aux_sentences[0])
    print("returned s2r specChar:", individualS2R)
    return individualS2R

def getIndividualS2RPattern(s2rSentence, dependencyMatcher, keywordList):
    individualS2R = []
    # keys = getKeysList(s2rSentences)
    # print("keys: ", keys)
    # for key in keys:
    # for sentence in s2rSentences[key]:
    print("sentence pattern: ", s2rSentence)
    # for el in keywords:
    print("keywordList: ", keywordList)
    dep_pattern = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'TEXT': {'IN': keywordList}}},
                     {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'object1', 'RIGHT_ATTRS': {'IS_ALPHA': True}},
                     {'LEFT_ID': 'object1', 'REL_OP': '>', 'RIGHT_ID': 'preposition', 'RIGHT_ATTRS': {'DEP': 'prep'}},
                     {'LEFT_ID': 'preposition', 'REL_OP': '>', 'RIGHT_ID': 'object2', 'RIGHT_ATTRS': {'IS_ALPHA': True}}
                 ]
    doc = nlp(s2rSentence)
    for token in doc:
        print("{2}({3}-{6}, {0}-{5})".format(token.text, token.tag_, token.dep_, token.head.text,
                                             token.head.tag_, token.i + 1, token.head.i + 1))
    dependencyMatches = getDependencyMatches(doc, dependencyMatcher, dep_pattern)
    print("depMathes: ", dependencyMatches)
    if len(dependencyMatches) != 0:
        for match in dependencyMatches:
            matches = match[1]
            found_s2r = ""
            for i in range(len(matches)):
                found_s2r = found_s2r + str(doc[matches[i]]) + " "
            individualS2R.append(found_s2r)
    return individualS2R

def getIndividualS2RFinal(s2rSentences, keywords):
    individualS2RFinal = []
    startDigitRegex = r'[0-9]+\..*'
    enumerationRegex = '[->]'
    keys = getKeysList(s2rSentences)
    print("keys: ", keys)
    index = 0
    for key in keys:
        for sentence in s2rSentences[key]:
            keywordList = keywords[index]
            print("sen to fct: ", sentence)
            match = re.match(startDigitRegex, sentence)
            print("match: ", match)
            if bool(match):
                individualS2RFinal.append(sentence)
            elif "->" in sentence or ">" in sentence:
                s2rSpecialChar = getIndividualS2RSpecialCharacters(sentence, enumerationRegex, keywordList)
                individualS2RFinal = individualS2RFinal + s2rSpecialChar
            else:
                s2rSpecialChar = getIndividualS2RPattern(sentence, dep_matcher, keywordList)
                individualS2RFinal = individualS2RFinal + s2rSpecialChar
            index += 1
    return individualS2RFinal


def displayIndividualS2R(doc, dependencyMatches):
    for match in dependencyMatches:
        print("match: ", match)
        pattern_name = match[0]
        matches = match[1]
        if len(matches) > 2:
            verb, dobject, preposition, object2 = matches[0], matches[1], matches[2], matches[3]
            print(nlp.vocab[pattern_name].text, '\t', doc[verb], doc[dobject], doc[preposition], doc[object2])
        else:
            verb, dobject = matches[0], matches[1]
            print(nlp.vocab[pattern_name].text, '\t', '...', doc[verb])

# dependecyMatches = getDependencyMatches(doc, dep_matcher)
individualS2RFinal = getIndividualS2RFinal(s2rsentences, keywords)
for s2r in individualS2RFinal:
    print("s2r: ",s2r)


# PANA AICI  MERGE BINEEEE


def getPosTag(text):
    wordTokens = nltk.word_tokenize(text)
    posTagged = pos_tag(wordTokens)
    print("pastag: ", posTagged)
    simplifiedTags = [(word, map_tag('en-ptb', 'universal', tag)) for word, tag in posTagged]
    print(simplifiedTags)

# getPosTag("Add a split")

# doctree = nlp("Add a split")
# for token in doctree:
#     print("{2}({3}-{6}, {0}-{5})".format(token.text, token.tag_, token.dep_, token.head.text, token.head.tag_, token.i+1, token.head.i+1))


def iterateAllActionGroups(allActionGroups, word):
    resultGroups = []
    for actionGroup in allActionGroups:
        print("action grup: ", actionGroup)
        if word in actionGroup:
            resultGroups.append(actionGroup[0].upper())
            print("resultGroups: ", resultGroups)
    return resultGroups

def checkExistInKeywords(keywords, word):
    for keys in keywords:
        if word in keys:
            return True
    return False

def determineActionGroup(allActionGroups, keyWords, reproduceStep, lemmatizer):
    docS2R = nlp(reproduceStep)
    sentences = list(docS2R.sents)
    resultGroups = []
    foundedAction = ""
    for sentence in sentences:
        print("sent: ", sentence)
        root = str(sentence.root)
        print("root: ", root)
        print(keywords)

        # print(keys)
        if checkExistInKeywords(keyWords, root):
            print("exista root in keywords: ", root)
            rootLemma = lemmatizer.lemmatize(root, getWordnetPosTag(root))
            print("rootLemma: " , rootLemma)
            resultGroups = iterateAllActionGroups(allActionGroups, rootLemma.lower())
            foundedAction = root
            break
        else:
            for child in sentence.root.children:
                print("child: ", child)
                if checkExistInKeywords(keyWords, str(child)):
                    childLemma = lemmatizer.lemmatize(str(child), getWordnetPosTag(str(child)))
                    resultGroups = iterateAllActionGroups(allActionGroups, childLemma.lower())
                    foundedAction = str(child)
                    break
            break
    return resultGroups, foundedAction


lemmatizer = WordNetLemmatizer()
print("allgrous: ", allGroupsCheck)
# resultActionGroups, foundedAction = determineActionGroup(allGroupsCheck, keywords, "Add a split", lemmatizer)
# print("resultActionGroups: ", resultActionGroups)
# print("foundedAction: ", foundedAction)


def getObjectsFromDependency(doc, dependencyMatches):
    s2rObjects = []
    for match in dependencyMatches:
        matches = match[1]
        # if len(matches) == len(set(matches)):
        print("matches: ", matches)
        s2r = ""
        for i in range(len(matches)):
            print("s2rpartial1: ", s2r)
            s2r = s2r + str(doc[matches[i]]) + " "
            print("s2rpartial2: ", s2r)

        s2rObjects.append(s2r)
        if len(dependencyMatches) > 1:
            break
    print("s2rObjFct: ", s2rObjects)
    return s2rObjects

def getDependencyMatchesObjects(doc, dependecyMatcher, dependencyPattern):
    dep_matches = []
    dependecyMatcher.add('nsubj_verb_dobj', patterns=[dependencyPattern])
    print(len(dependecyMatcher))
    dep_full_matches = dependecyMatcher(doc)
    print("dep_full: ", dep_full_matches)
    indexes = []
    if len(dep_full_matches) != 0:
        for dep in dep_full_matches:
            indexes.append(dep[1])
            print("indexes: ", indexes)
        min_length = min(map(len, indexes))
        print("min: ", min_length)
        for el in dep_full_matches:
            if len(el[1]) == min_length:
                dep_matches.append(el)
    return dep_matches

def getObjectsOfS2R(actionWord, s2rSentence, dependencyMatcher):
    dep_patternFull = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'TEXT': actionWord}},
                       # {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'Optionalpreposition', 'RIGHT_ATTRS': {'DEP': 'prep'}, 'OP': '*'},
                       {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'object1', 'RIGHT_ATTRS': {'DEP': 'dobj'}},
                      {'LEFT_ID': 'object1', 'REL_OP': '>', 'RIGHT_ID': 'preposition', 'RIGHT_ATTRS': {'DEP': 'prep'}},
                      {'LEFT_ID': 'preposition', 'REL_OP': '>', 'RIGHT_ID': 'object2', 'RIGHT_ATTRS': {'DEP': 'pobj'}}]

    dep_patternObj1 = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'TEXT': actionWord}},
                       # {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'Optionalpreposition', 'RIGHT_ATTRS': {'DEP': 'prep'}, 'OP': '*'},
                       {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'object1', 'RIGHT_ATTRS': {'DEP': 'dobj'}}]

    dep_patternObj2 = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'TEXT': actionWord}},
                      {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'preposition', 'RIGHT_ATTRS': {'DEP': 'prep'}},
                      {'LEFT_ID': 'preposition', 'REL_OP': '>', 'RIGHT_ID': 'object2', 'RIGHT_ATTRS': {'DEP': {'IN': ['pobj']}}}]

    docObj = nlp(s2rSentence)
    # for token in doc:
    #     print("{2}({3}-{6}, {0}-{5})".format(token.text, token.tag_, token.dep_, token.head.text,
    #                                          token.head.tag_, token.i + 1, token.head.i + 1))
    s2rObjects = []
    dependencyMatchesFull = getDependencyMatchesObjects(docObj, dependencyMatcher, dep_patternFull)
    print("depMathesFull: ", dependencyMatchesFull)
    if len(dependencyMatchesFull) != 0:
        s2rObjects = getObjectsFromDependency(docObj, dependencyMatchesFull)
    else:
        dependencyMatchesObj2 = getDependencyMatchesObjects(docObj, dependencyMatcher, dep_patternObj2)
        print("depMathesObj2: ", dependencyMatchesObj2)
        if len(dependencyMatchesObj2) != 0:
            s2rObjects = getObjectsFromDependency(docObj, dependencyMatchesObj2)
        else:
            dependencyMatchesObj1 = getDependencyMatchesObjects(docObj, dependencyMatcher, dep_patternObj1)
            print("depMathesObj1: ", dependencyMatchesObj1)
            if len(dependencyMatchesObj1) != 0:
                s2rObjects = getObjectsFromDependency(docObj, dependencyMatchesObj1)
            else:
                s2rObjects.append(s2rSentence)
    return s2rObjects

# s2rObjects = getObjectsOfS2R(foundedAction, "Add a split", dep_matcher)
# print("s2rObjects: ", s2rObjects)


def translateOpenGroup(s2rSentence, s2rObjects):
    openEvent = "Open app"
    tapEvent = "Tap"
    appwords = ["app", "application"]
    for word in appwords:
        if word in s2rSentence:
            return openEvent
    docS2R = nlp(s2rObjects[0])
    print("Noun phrases:", [chunk.text for chunk in docS2R.noun_chunks])
    if len(docS2R.ents) != 0:
        return openEvent
    if len([chunk.text for chunk in docS2R.noun_chunks]) != 0:
        return openEvent
    return tapEvent

specialClickActions = ["choose", "select", "pick", "go", "create", "add", "check"]

def translateClickGroup(s2rSentence, s2rObjects, action, specialActions, lemmatizer):
    tapEvent = "Tap"
    clickEvent = "Click"
    tapBackEvent = "Tap back button"
    tapMenuEvent = "Tap menu button"
    backTerms = ["back", "leave", "return", "return to"]
    menuTerms = ["menu", "more options", "option", "options", "three dots", "3 dots", "settings"]
    for term in backTerms:
        if term in s2rObjects or term in s2rSentence:
            return tapBackEvent
    for term in menuTerms:
        if term in s2rObjects or term in s2rSentence:
            return tapMenuEvent
    if clickEvent.lower() in s2rSentence.lower():
        return clickEvent
    print("Action: ", action)
    actionLemma = lemmatizer.lemmatize(str(action), getWordnetPosTag(str(action)))
    print("actLemaa: ", actionLemma)
    for spAction in specialActions:
        print("speAction: ", spAction)
        if actionLemma.lower() == spAction:
            print("in iffff")
            tapEvent += " to " + spAction
            print("tapev: ", tapEvent)
            return tapEvent
    return tapEvent

def translateSwipeGroup(s2rSentence, s2rObjects):
    event = "Siwpe "
    directionKeywords = ["up", "down", "right", "left"]
    for direction in directionKeywords:
        if direction in s2rObjects or direction in s2rSentence:
            event += direction
            return event
    return event

def translateRotateGroup(s2rSentence, s2rObjects):
    event = "Rotate to"
    directionKeywords = ["landscape", "portait"]
    for word in directionKeywords:
        if word in s2rObjects or word in s2rSentence:
            event += word
            event += " orientation"
            return event
    return event

def translateGroupToEvent(s2rSentence, action, actionGroup, s2rObjects):
    event = ""
    if len(actionGroup) > 1 or len(actionGroup) == 0:
        event = "Tap to " + action.lower()
    elif actionGroup[0] == "OPEN":
        event = translateOpenGroup(s2rSentence, s2rObjects)
        print(event)
    elif actionGroup[0] == "CLICK":
        event = translateClickGroup(s2rSentence, s2rObjects, action, specialClickActions, lemmatizer)
    elif actionGroup[0] == "LONG_CLICK":
        event = "Long tap"
    elif actionGroup[0] == "TYPE":
        event = "Type"
    elif actionGroup[0] == "SWIPE":
        event = translateSwipeGroup(s2rSentence, s2rObjects)
    elif actionGroup[0] == "ROTATE":
        event = translateRotateGroup(s2rSentence, s2rObjects)
    return event

# event = translateGroupToEvent("Add a split", resultActionGroups, s2rObjects)
# print("event: ", event)

def modifyAction(s2rSentence, action, event):
    specialEvents = ["Tap back button", "Tap menu button"]
    if event in specialEvents:
        s2rModifiedSentence = s2rSentence.replace(s2rSentence, event, 1)
    else:
        print("in modifica actiune: ", action, "   ", event)
        s2rModifiedSentence = s2rSentence.replace(action, event, 1)

    return s2rModifiedSentence

# modifiedS2R = modifyAction("Add a split", foundedAction, event)
# print("s2rReplace: ", modifiedS2R)

def removeCharacters(step):
    contor = 0
    for c in step:
        print("c: ",c)
        if c.isalpha() == False:
            contor += 1
            print("contor: ",contor)
        else:
            break
    result = step[contor:]
    print("rez: ",result)
    return result
# removeCharacters("#####Click on existing transaction")



def getFinalSteps(stepSentences, dependencyMatcher):
    finalSteps = []
    # startDigitRegex = r'[0-9]+\..*'
    for step in stepSentences:
        print("Step: ", step)
        # match = re.match(startDigitRegex, step)
        # print("match: ", match)
        # if bool(match):
        clearStep = removeCharacters(step)
        print("clearStep: ", clearStep)
        actionGroup, action = determineActionGroup(allGroupsCheck, keywords, clearStep, lemmatizer)
        print("group: ", actionGroup)
        print("action: ", action)
        s2rObject = getObjectsOfS2R(action, clearStep, dependencyMatcher)
        print("object: ", s2rObject)
        event = translateGroupToEvent(clearStep, action, actionGroup, s2rObject)
        print("evveeent: ", event)
        modifiedStep = modifyAction(clearStep, action, event)
        print("modifiedStep: ", modifiedStep)
        finalSteps.append(modifiedStep)
        print("finalSteps: ", finalSteps)
    return finalSteps

finalSteps = getFinalSteps(individualS2RFinal, dep_matcher)

print("individual: ", individualS2RFinal)
print("finalStepcheck: ", finalSteps)

def checkSentence(sentence):
    sen = "steps to reproduce"
    if sen in sentence.lower():
        return True
    return False


def onlySpecialCharacters(sentence):
    regex = "[a-zA-Z0-9]+"
    p = re.compile(regex)
    if (len(sentence) == 0):
        return False
    if (re.search(p, sentence)):
        return True
    else:
        return False


def getFinalData(idData, titleData, descriptionParagraphs, individualSteps, finalSteps):
    id_title_final_data = []
    description_final_data = {}
    id = "Bug ID: " + idData
    print("id: ", id)
    title = "Bug title: " + titleData
    print("title: ", title)
    id_title_final_data.append(id)
    id_title_final_data.append(title)
    print("id_title_final_data: ", id_title_final_data)
    counter = 0
    flag = False
    s = []
    for key in descriptionParagraphs:
        print("key: ", key)
        for sentence in descriptionParagraphs[key]:
            print("sentence: ", sentence)
            if not onlySpecialCharacters(sentence):
                continue
            if sentence not in individualSteps:
                clearSentence = removeCharacters(sentence)
                s.append(clearSentence)
                # finalData.append(clearSentence)
                print("finalData 2: ", s)
                aux = sentence
                print("aux: ", aux)
            else:
                if flag == False:
                    if checkSentence(aux) == False:
                        s.append("Steps to reproduce:")
                        # finalData.append("Steps to reproduce:")
                        print("finalData aux: ", s)
                        flag = True

                step = str(counter + 1) + ". " + finalSteps[counter]
                print("step: ", step)
                s.append(step)
                # finalData.append(step)
                print("finalData 3: ", s)
                counter += 1
        if len(s) != 0:
            description_final_data[key] = s
        print("mhmmmm: ", description_final_data)
        s = []
    print("finalData 4: ", description_final_data)
    return id_title_final_data, description_final_data

final_id_title_data, final_description_data = getFinalData(idData, titleData, p, individualS2RFinal, finalSteps)


def writeFinalReport(file, id_title_data, description_data):
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


writeFinalReport(resultDir, final_id_title_data, final_description_data)




# # 1. Init Lemmatizer
# lemmatizer = WordNetLemmatizer()
#
# # 2. Lemmatize Single Word with the appropriate POS tag
# word = 'best'
# print(lemmatizer.lemmatize(word, getWordnetPosTag(word)))
#
# # 3. Lemmatize a Sentence with the appropriate POS tag
# print("postaaaags: ", [lemmatizer.lemmatize(w, getWordnetPosTag(w)) for w in nltk.word_tokenize(s)])



# from nltk.parse.stanford import StanfordDependencyParser

# path_to_jar = 'C:/Users/Bogdan Andrei/Downloads/stanford-parser-4.2.0/stanford-parser-full-2020-11-17/stanford-parser.jar'
# path_to_models_jar = 'C:/Users/Bogdan Andrei/Downloads/stanford-corenlp-latest/stanford-corenlp-4.2.1/stanford-corenlp-4.2.1-models.jar'
#
# dependency_parser = nltk.parse.corenlp.CoreNLPDependencyParser()
#
# result = dependency_parser.raw_parse('I shot an elephant in my sleep')
# dep = result.next()
#
# list(dep.triples())


# about_talk_text = ('When i create an entry for a purchase'
#                    ' the autocomplete list shows up')
#
# pattern = r'(<VERB><NOUN><PREPOSITION><NOUN>)'
# pattern2 = r'<VERB>*<ADV>*<VERB>+<PART>*'
# about_talk_doc = textacy.make_spacy_doc(about_talk_text,
#                                          lang='en_core_web_sm')
# verb_phrases = textacy.extract.pos_regex_matches(about_talk_doc, pattern2)
# # Print all Verb Phrase
# for chunk in verb_phrases:
#     print(chunk.text)



# from nltk.parse.corenlp import CoreNLPServer
#
# # The server needs to know the location of the following files:
# #   - stanford-corenlp-X.X.X.jar
# #   - stanford-corenlp-X.X.X-models.jar
# STANFORD = os.path.join("models", "stanford-corenlp-full-2018-02-27")
#
# # Create the server
# server = CoreNLPServer(
#    os.path.join('C:/Users/Bogdan Andrei/Downloads/stanford-parser-4.2.0/stanford-parser-full-2020-11-17', "stanford-parser.jar"),
#    os.path.join('C:/Users/Bogdan Andrei/Downloads/stanford-corenlp-latest/stanford-corenlp-4.2.1', "stanford-corenlp-4.2.1-models.jar"),
# )
#
# # Start the server in the background
# server.start()
#
# from nltk.parse.corenlp import CoreNLPDependencyParser
#
# parser = CoreNLPDependencyParser()
# parse = next(parser.raw_parse("I put the book in the box on the table."))

# import corenlp
#
# text = "Chris wrote a simple sentence that he parsed with Stanford CoreNLP."
#
# # We assume that you've downloaded Stanford CoreNLP and defined an environment
# # variable $CORENLP_HOME that points to the unzipped directory.
# # The code below will launch StanfordCoreNLPServer in the background
# # and communicate with the server to annotate the sentence.
# with corenlp.CoreNLPClient(annotators="tokenize ssplit pos lemma ner depparse".split()) as client:
#   ann = client.annotate(text)
#
# # You can access annotations using ann.
# sentence = ann.sentence[0]
#
# # The corenlp.to_text function is a helper function that
# # reconstructs a sentence from tokens.
# assert corenlp.to_text(sentence) == text
#
# # You can access any property within a sentence.
# print(sentence.text)
#
# # Likewise for tokens
# token = sentence.token[0]
# print(token.lemma)
#
# # Use tokensregex patterns to find who wrote a sentence.
# pattern = '([ner: PERSON]+) /wrote/ /an?/ []{0,3} /sentence|article/'
# matches = client.tokensregex(text, pattern)
# # sentences contains a list with matches for each sentence.
# assert len(matches["sentences"]) == 1
# # length tells you whether or not there are any matches in this
# assert matches["sentences"][0]["length"] == 1
# # You can access matches like most regex groups.
# matches["sentences"][1]["0"]["text"] == "Chris wrote a simple sentence"
# matches["sentences"][1]["0"]["1"]["text"] == "Chris"
#
# # Use semgrex patterns to directly find who wrote what.
# pattern = '{word:wrote} >nsubj {}=subject >dobj {}=object'
# matches = client.semgrex(text, pattern)
# # sentences contains a list with matches for each sentence.
# assert len(matches["sentences"]) == 1
# # length tells you whether or not there are any matches in this
# assert matches["sentences"][0]["length"] == 1
# # You can access matches like most regex groups.
# matches["sentences"][1]["0"]["text"] == "wrote"
# matches["sentences"][1]["0"]["$subject"]["text"] == "Chris"
# matches["sentences"][1]["0"]["$object"]["text"] == "sentence"
#





#
#
# def saveLoadPretrainedModel(filename):
#     savedOldModel = fasttext.load_model(filename)
#     lines = []
#     # get all words from model
#     words = savedOldModel.get_words()
#     with open("savedModel.vec", 'w') as file_out:
#         # the first line must contain number of total words and vector dimension
#         file_out.write(str(len(words)) + " " + str(savedOldModel.get_dimension()) + "\n")
#
#         # line by line, you append vectors to VEC file
#         for w in words:
#             v = savedOldModel.get_word_vector(w)
#             vstr = ""
#             for vi in v:
#                 vstr += " " + str(vi)
#             try:
#                 file_out.write(w + vstr + '\n')
#             except:
#                 pass
#
#
#
# def trainSkipgramModel():
#     modelCount = 1
#     directory = 'bug_reports_dataset'
#     savedDirectory = 'savedModels'
#     skipgramModel = fasttext.train_supervised('bug_reports_dataset/accumulo/bug-reports.json')
#     print("1:", skipgramModel.get_words())
#     skipgramModel.save_model(savedDirectory + '/' + "savedModel" + str(modelCount) + ".bin")
#     # saveLoadPretrainedModel("savedModel.bin")
#     sentence = "Start application. Tap on menu button."
#     skipgramModel.predict(sentence)
#     print(sentence)
#     for root, subdirectories, files in os.walk(directory):
#         for file in files:
#             modelCount += 1
#             print(root)
#             print(file)
#             skipgramModel = fasttext.train_unsupervised(root + "/" + file, model='skipgram')
#             print("2:", skipgramModel.get_words())
#             skipgramModel.save_model(savedDirectory + '/' + "savedModel" + str(modelCount) + ".bin")
#             # saveLoadPretrainedModel("savedModel.bin")
#     # return skipgramModel
# # trainSkipgramModel()








# # Init InferSent Model
# infer_sent_model = InferSent()
# infer_sent_model.load_state_dict(torch.load(dest_dir + dest_file))
# # Setup Word Embedding Model
# infer_sent_model.set_w2v_path(word_embs_model_path)
# # Build Vocab for InferSent model
# model.build_vocab(sentences, tokenize=True)
# # Encode sentence to vectors
# model.encode(sentences, tokenize=True)


# word_lem = WordNetLemmatizer()
# for w in original_OPEN:
#     print(word_lem.lemmatize(w))
#     print(get_word_forms(w))
#     for values in get_word_forms(w).values():
#         print(values)






# p = splitData("""Window leak on orientation change when a selected Dictionary is being verified.
# Action sequence: (Dictionary already loaded) Start app -&gt; MENU -&gt; Click on Dictionaries -&gt; Long click on any dictionary -&gt; change orientation when dictionary is being verified i.e popup window is still visible
#
# logcat stack trace:
#
# E/WindowManager(919): android.view.WindowLeaked: Activity aarddict.android.DictionariesActivity has leaked window com.android.internal.policy.impl.PhoneWindow$DecorView@411814d0 that was originally added here
# E/WindowManager(919): at android.view.ViewRootImpl.&lt;init&gt;(ViewRootImpl.java:343)
# E/WindowManager(919): at android.view.WindowManagerImpl.addView(WindowManagerImpl.java:245)
# E/WindowManager(919): at android.view.WindowManagerImpl.addView(WindowManagerImpl.java:193)
# E/WindowManager(919): at android.view.WindowManagerImpl$CompatModeWrapper.addView(WindowManagerImpl.java:118)
# E/WindowManager(919): at android.view.Window$LocalWindowManager.addView(Window.java:537)
# E/WindowManager(919): at android.app.Dialog.show(Dialog.java:274)
# E/WindowManager(919): at aarddict.android.DictionariesActivity$DictListAdapter.verify(DictionariesActivity.java:383)
# E/WindowManager(919): at aarddict.android.DictionariesActivity$DictListAdapter.onItemLongClick(DictionariesActivity.java:336)
# E/WindowManager(919): at android.widget.AbsListView.performLongPress(AbsListView.java:2580)
# E/WindowManager(919): at android.widget.AbsListView$CheckForLongPress.run(AbsListView.java:2530)
# E/WindowManager(919): at android.os.Handler.handleCallback(Handler.java:605)
# E/WindowManager(919): at android.os.Handler.dispatchMessage(Handler.java:92)
# E/WindowManager(919): at android.os.Looper.loop(Looper.java:137)
# E/WindowManager(919): at android.app.ActivityThread.main(ActivityThread.java:4340)
# E/WindowManager(919): at java.lang.reflect.Method.invokeNative(Native Method)
# E/WindowManager(919): at java.lang.reflect.Method.invoke(Method.java:511)
# E/WindowManager(919): at com.android.internal.os.ZygoteInit$MethodAndArgsCaller.run(ZygoteInit.java:784)
# E/WindowManager(919): at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:551)
# E/WindowManager(919): at dalvik.system.NativeStart.main(Native Method)""")

