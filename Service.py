from Repository import Repository
from config import nlp, allGroups, allGroupsCheck, specialClickActions, dep_matcher, lemmatizer, originalDir, parsedDir, \
    identifiedStepsDir, resultDir, resultExtension, extension

import nltk
import nltk.corpus
from nltk.tokenize import word_tokenize
from nltk.stem import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import re



class Service:
    def __init__(self):
        self.repository = Repository()
        self.originalDir = originalDir
        self.parsedDir = parsedDir
        self.identifiedStepsDir = identifiedStepsDir
        self.resultDir = resultDir
        self.extension = extension
        self.resultExtension = resultExtension

    def getWordnetPosTag(self, word):
        """
        Map POS tag to first character lemmatize() accepts
        :param word: string
        :return: tag_dict - dictionary with (key:string , value:string) pairs
        """
        tag = nltk.pos_tag([word])[0][1][0].upper()
        tag_dict = {"J": wordnet.ADJ,
                    "N": wordnet.NOUN,
                    "V": wordnet.VERB,
                    "R": wordnet.ADV}
        return tag_dict.get(tag, wordnet.NOUN)

    def verifyWordLemma(self, keyWords, word):
        """
        Verify if a list contains a certain element
        :param keyWords: list of strings
        :param word: string
        :return: boolean
        """
        if word in keyWords:
            return True
        else:
            return False


    def identifyS2RSentences(self, paragraphs):
        """
        Determine the sentences that contains steps to reproduce
        :param paragraphs: dictionary with key - integer and value - list of strings
        :return: s2rSentences - dictionary with key - integer and value - list of strings
                keywords - list of strings
        """
        s2rSentences = {}
        sentences = []
        lematizer = WordNetLemmatizer()
        kewwords = []
        for key in paragraphs:
            for value in paragraphs[key]:
                count = 0
                aux_kewwords = []
                wordTokenizedSentence = word_tokenize(value)
                for word in wordTokenizedSentence:
                    lemmatizedWord = lematizer.lemmatize(word, self.getWordnetPosTag(word))
                    if self.verifyWordLemma(allGroups, lemmatizedWord.lower()):
                        count += 1
                        aux_kewwords.append(word)
                if count > 0:
                    sentences.append(value)
                if len(aux_kewwords) != 0:
                    kewwords.append(aux_kewwords)
            if len(sentences) != 0:
                s2rSentences[key] = sentences
                sentences = []
        return s2rSentences, kewwords

    def getKeysList(self, dict):
        """
        Returns a list with the keys of a dictionary
        :param dict: dictionary
        :return: list - list of integer
        """
        list = []
        for key in dict.keys():
            list.append(key)
        return list

    def getDependencyMatches(self, doc, dependecyMatcher, dependencyPattern):
        """
        Determine dependency matches for a sequence of tokens (relation extraction)
        :param doc: list of strings - tokens sequence
        :param dependecyMatcher: object of spacy Matcher class
        :param dependencyPattern: list of dictionaries with key - string, value - string or another dictionary
        :return: list of tuples
        """
        dependecyMatcher.add('verb_obj', patterns=[dependencyPattern])
        dep_matches = dependecyMatcher(doc)
        return dep_matches


    def getIndividualS2RSpecialCharacters(self, s2rSentence, regex, keywordList):
        """
        Determine and return step to reproduce which is present in a step to reproduce
        sentence that contains special characters
        :param s2rSentence: string
        :param regex: string
        :param keywordList: list(list(string))
        :return: list of strings
        """
        individualS2R = []
        sentences = re.split(regex, s2rSentence)
        for splitedsentence in sentences:
            aux_regex = '[.*]*[)]'
            if len(splitedsentence) != 0:
                aux_sentences = re.split(aux_regex, splitedsentence)
                if len(aux_sentences) != 1:
                    for s in aux_sentences:
                        for keyword in keywordList:
                            if keyword in s:
                                individualS2R.append(s)
                            break
                else:
                    individualS2R.append(aux_sentences[0])
        return individualS2R

    def getIndividualS2RPattern(self, s2rSentence, dependencyMatcher, keywordList):
        """
        Determine and return step to reproduce from a sentence which matches with a pattern
        :param s2rSentence: string
        :param dependencyMatcher: object of spacy matcher class
        :param keywordList: list(list(string))
        :return: list of strings
        """
        individualS2R = []
        dep_pattern = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'TEXT': {'IN': keywordList}}},
                         {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'object1', 'RIGHT_ATTRS': {'IS_ALPHA': True}},
                         {'LEFT_ID': 'object1', 'REL_OP': '>', 'RIGHT_ID': 'preposition', 'RIGHT_ATTRS': {'DEP': 'prep'}},
                         {'LEFT_ID': 'preposition', 'REL_OP': '>', 'RIGHT_ID': 'object2', 'RIGHT_ATTRS': {'IS_ALPHA': True}}
                     ]
        doc = nlp(s2rSentence)
        dependencyMatches = self.getDependencyMatches(doc, dependencyMatcher, dep_pattern)
        if len(dependencyMatches) != 0:
            for match in dependencyMatches:
                matches = match[1]
                found_s2r = ""
                for i in range(len(matches)):
                    found_s2r = found_s2r + str(doc[matches[i]]) + " "
                individualS2R.append(found_s2r)
        return individualS2R

    def getIndividualS2RFinal(self, s2rSentences, keywords):
        """
        Determine and set the final steps to reproduce from a text
        :param s2rSentences: dictionary with key - integer and value - list of strings
        :param keywords: list(list(string))
        :return: list of strings
        """
        individualS2RFinal = []
        startDigitRegex = r'[0-9]+\..*'
        enumerationRegex = '[->]'
        keys = self.getKeysList(s2rSentences)
        index = 0
        for key in keys:
            for sentence in s2rSentences[key]:
                keywordList = keywords[index]
                match = re.match(startDigitRegex, sentence)
                if bool(match):
                    individualS2RFinal.append(sentence)
                elif "->" in sentence or ">" in sentence:
                    s2rSpecialChar = self.getIndividualS2RSpecialCharacters(sentence, enumerationRegex, keywordList)
                    individualS2RFinal = individualS2RFinal + s2rSpecialChar
                else:
                    s2rSpecialChar = self.getIndividualS2RPattern(sentence, dep_matcher, keywordList)
                    individualS2RFinal = individualS2RFinal + s2rSpecialChar
                index += 1
        return individualS2RFinal

    def iterateAllActionGroups(self, allActionGroups, word):
        """
        Iterate a list and return a new list of string with name of group which contains a certain term
        :param allActionGroups: list(list(string))
        :param word: string
        :return: list of strings
        """
        resultGroups = []
        for actionGroup in allActionGroups:
            if word in actionGroup:
                resultGroups.append(actionGroup[0].upper())
        return resultGroups

    def checkExistInKeywords(self, keywords, word):
        """
        Chech if a string is in a list and return a boolean value True if list contains term and False othewise
        :param keywords: list(list(string))
        :param word: string
        :return: boolean
        """
        for keys in keywords:
            if word in keys:
                return True
        return False

    def determineActionGroup(self, allActionGroups, keyWords, reproduceStep, lemmatizer):
        """
        Return a list with action group of step to reproduce (string) and specific action from that sentence
        :param allActionGroups: list(list(string))
        :param keyWords: list(list(string))
        :param reproduceStep: string
        :param lemmatizer: object of WordNetLemmatizer class
        :return: resultGroups: list of string
                foundedAction: string
        """
        docS2R = nlp(reproduceStep)
        sentences = list(docS2R.sents)
        resultGroups = []
        foundedAction = ""
        for sentence in sentences:
            root = str(sentence.root)
            if self.checkExistInKeywords(keyWords, root):
                rootLemma = lemmatizer.lemmatize(root, self.getWordnetPosTag(root))
                resultGroups = self.iterateAllActionGroups(allActionGroups, rootLemma.lower())
                foundedAction = root
                break
            else:
                for child in sentence.root.children:
                    if self.checkExistInKeywords(keyWords, str(child)):
                        childLemma = lemmatizer.lemmatize(str(child), self.getWordnetPosTag(str(child)))
                        resultGroups = self.iterateAllActionGroups(allActionGroups, childLemma.lower())
                        foundedAction = str(child)
                        break
                break
        return resultGroups, foundedAction

    def getObjectsFromDependency(self, doc, dependencyMatches):
        """
        Get only specific words from step to reproduce, represented as dependency mathces
        :param doc: list of strings - tokens sequence
        :param dependencyMatches: list of tuples
        :return: list of string
        """
        s2rObjects = []
        for match in dependencyMatches:
            matches = match[1]
            s2r = ""
            for i in range(len(matches)):
                s2r = s2r + str(doc[matches[i]]) + " "
            s2rObjects.append(s2r)
            if len(dependencyMatches) > 1:
                break
        return s2rObjects

    def getDependencyMatchesObjects(self, doc, dependecyMatcher, dependencyPattern):
        """
        Determine and return a list with all founded dependency in a sentence represented as
        sequence of words, which match the pattern
        :param doc: list of strings - tokens sequence
        :param dependecyMatcher: object of spacy matcher class
        :param dependencyPattern: list of dictionaries with key - string, value - string or another dictionary
        :return: list of tuples
        """
        dep_matches = []
        dependecyMatcher.add('nsubj_verb_dobj', patterns=[dependencyPattern])
        dep_full_matches = dependecyMatcher(doc)
        indexes = []
        if len(dep_full_matches) != 0:
            for dep in dep_full_matches:
                indexes.append(dep[1])
            min_length = min(map(len, indexes))
            for el in dep_full_matches:
                if len(el[1]) == min_length:
                    dep_matches.append(el)
        return dep_matches

    def getObjectsOfS2R(self, actionWord, s2rSentence, dependencyMatcher):
        """
        Make a list with action and objects of a sentence
        :param actionWord: string
        :param s2rSentence: string
        :param dependencyMatcher: object of spacy matcher class
        :return: list of strings
        """
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
        s2rObjects = []
        dependencyMatchesFull = self.getDependencyMatchesObjects(docObj, dependencyMatcher, dep_patternFull)
        if len(dependencyMatchesFull) != 0:
            s2rObjects = self.getObjectsFromDependency(docObj, dependencyMatchesFull)
        else:
            dependencyMatchesObj2 = self.getDependencyMatchesObjects(docObj, dependencyMatcher, dep_patternObj2)
            if len(dependencyMatchesObj2) != 0:
                s2rObjects = self.getObjectsFromDependency(docObj, dependencyMatchesObj2)
            else:
                dependencyMatchesObj1 = self.getDependencyMatchesObjects(docObj, dependencyMatcher, dep_patternObj1)
                if len(dependencyMatchesObj1) != 0:
                    s2rObjects = self.getObjectsFromDependency(docObj, dependencyMatchesObj1)
                else:
                    s2rObjects.append(s2rSentence)
        return s2rObjects

    def translateOpenGroup(self, s2rSentence, s2rObjects):
        """
        Return open group's event for a specific sentence (step to reproduce)
        :param s2rSentence: string
        :param s2rObjects: list of strings
        :return: string
        """
        openEvent = "Open app"
        tapEvent = "Tap"
        appwords = ["app", "application"]
        for word in appwords:
            if word in s2rSentence:
                return openEvent
        docS2R = nlp(s2rObjects[0])
        if len(docS2R.ents) != 0:
            return openEvent
        if len([chunk.text for chunk in docS2R.noun_chunks]) != 0:
            return openEvent
        return tapEvent

    def translateClickGroup(self, s2rSentence, s2rObjects, action, specialActions, lemmatizer):
        """
        Return click group's event for a sentence (step to reproduce)
        :param s2rSentence: string
        :param s2rObjects: list of strings
        :param action: string
        :param specialActions: list of strings
        :param lemmatizer: object of WordNetLemmatizer class
        :return: string
        """
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
        actionLemma = lemmatizer.lemmatize(str(action), self.getWordnetPosTag(str(action)))
        for spAction in specialActions:
            if actionLemma.lower() == spAction:
                tapEvent += " to " + spAction
                return tapEvent
        return tapEvent

    def translateSwipeGroup(self, s2rSentence, s2rObjects):
        """
        Return swipe group's event for a sentence (step to reproduce)
        :param s2rSentence: string
        :param s2rObjects: lsit of strings
        :return: string
        """
        event = "Siwpe "
        directionKeywords = ["up", "down", "right", "left"]
        for direction in directionKeywords:
            if direction in s2rObjects or direction in s2rSentence:
                event += direction
                return event
        return event

    def translateRotateGroup(self, s2rSentence, s2rObjects):
        """
        Return rotate group's event for a sentence (step to reproduce)
        :param s2rSentence: string
        :param s2rObjects: list of strings
        :return: string
        """
        event = "Rotate to"
        directionKeywords = ["landscape", "portait"]
        for word in directionKeywords:
            if word in s2rObjects or word in s2rSentence:
                event += word
                event += " orientation"
                return event
        return event

    def translateGroupToEvent(self, s2rSentence, action, actionGroup, s2rObjects):
        """
        Translate an action group to an string event
        :param s2rSentence: string
        :param action: string
        :param actionGroup: list of string
        :param s2rObjects: list of strings
        :return: string
        """
        event = ""
        if len(actionGroup) > 1 or len(actionGroup) == 0:
            event = "Tap to " + action.lower()
        elif actionGroup[0] == "OPEN":
            event = self.translateOpenGroup(s2rSentence, s2rObjects)
            print(event)
        elif actionGroup[0] == "CLICK":
            event = self.translateClickGroup(s2rSentence, s2rObjects, action, specialClickActions, lemmatizer)
        elif actionGroup[0] == "LONG_CLICK":
            event = "Long tap"
        elif actionGroup[0] == "TYPE":
            event = "Type"
        elif actionGroup[0] == "SWIPE":
            event = self.translateSwipeGroup(s2rSentence, s2rObjects)
        elif actionGroup[0] == "ROTATE":
            event = self.translateRotateGroup(s2rSentence, s2rObjects)
        return event

    def modifyAction(self, s2rSentence, action, event):
        """
        Replace original action from a sentence with specific event
        Return modified sentence
        :param s2rSentence: string
        :param action: string
        :param event: string
        :return: string
        """
        specialEvents = ["Tap back button", "Tap menu button"]
        if event in specialEvents:
            s2rModifiedSentence = s2rSentence.replace(s2rSentence, event, 1)
        else:
            s2rModifiedSentence = s2rSentence.replace(action, event, 1)
        return s2rModifiedSentence

    def removeCharacters(self, step):
        """
        Delete all useless characters from start of a sentence up to first letter or number
        :param step: string
        :return: string
        """
        contor = 0
        for c in step:
            if c.isalpha() == False:
                contor += 1
            else:
                break
        result = step[contor:]
        return result

    def getFinalSteps(self, stepSentences, dependencyMatcher, keywords):
        """
        Determine and return all step to reproduce sentences from a text
        :param stepSentences: list of strings
        :param dependencyMatcher: object of spacy matcher class
        :param keywords: list(lsit(string))
        :return: list of strings
        """
        finalSteps = []
        for step in stepSentences:
            clearStep = self.removeCharacters(step)
            actionGroup, action = self.determineActionGroup(allGroupsCheck, keywords, clearStep, lemmatizer)
            s2rObject = self.getObjectsOfS2R(action, clearStep, dependencyMatcher)
            event = self.translateGroupToEvent(clearStep, action, actionGroup, s2rObject)
            modifiedStep = self.modifyAction(clearStep, action, event)
            finalSteps.append(modifiedStep)
        return finalSteps

    def checkSentence(self, sentence):
        """
        Check if a substring appears in a string
        Return True if string contains substring, False value othewise
        :param sentence: string
        :return: boolean
        """
        sen = "steps to reproduce"
        if sen in sentence.lower():
            return True
        return False


    def onlySpecialCharacters(self, sentence):
        """
        Check if a string consints of only special characters
        Return False if string is null or string consists of only special characters, otherwise return True
        :param sentence: string
        :return: boolean
        """
        regex = "[a-zA-Z0-9]+"
        p = re.compile(regex)
        if (len(sentence) == 0):
            return False
        if (re.search(p, sentence)):
            return True
        else:
            return False


    def getFinalData(self, idData, titleData, descriptionParagraphs, individualSteps, finalSteps):
        """
        Compute final report
        :param idData: string
        :param titleData: string
        :param descriptionParagraphs: dictionary with key - integer and value - list of strings
        :param individualSteps: list of strings
        :param finalSteps: list of strings
        :return: id_title_final_data: lsit of strings
                description_final_data: dictionary with key - integer and value - list of strings
        """
        id_title_final_data = []
        description_final_data = {}
        id = "Bug ID: " + idData
        title = "Bug title: " + titleData
        id_title_final_data.append(id)
        id_title_final_data.append(title)
        counter = 0
        flag = False
        s = []
        for key in descriptionParagraphs:
            for sentence in descriptionParagraphs[key]:
                if not self.onlySpecialCharacters(sentence):
                    continue
                if sentence not in individualSteps:
                    clearSentence = self.removeCharacters(sentence)
                    s.append(clearSentence)
                    aux = sentence
                else:
                    if flag == False:
                        if self.checkSentence(aux) == False:
                            s.append("Steps to reproduce:")
                            flag = True
                    step = str(counter + 1) + ". " + finalSteps[counter]
                    s.append(step)
                    counter += 1
            if len(s) != 0:
                description_final_data[key] = s
            s = []
        return id_title_final_data, description_final_data

    def getStepsToReproduceForGui(self, steps):
        """
        Compute all step to reproduce sentences for displaying on interface
        :param steps: list of strings
        :return: list of strings
        """
        result = []
        index = 0
        result.append("Steps to reproduce:")
        for step in steps:
            index += 1
            aux_sentence = str(index) + ". " + step
            result.append(aux_sentence)
        return result

    def getFilesName(self, filename):
        """
        Create name of files base on input from user
        :param filename: string - file name
        :return: originalFile: string - original bug report file
                parsedFile: string - splitted file by paragraphs
                identifiedStepsFile: string - file with identified step to reproduce sentences
                resultFile: string - final bug report file
        """
        originalFile = self.originalDir + str(filename) + self.extension
        parsedFile = self.parsedDir + str(filename) + self.extension
        identifiedStepsFile = self.identifiedStepsDir + str(filename) + self.extension
        resultFile = self.resultDir + str(filename) + self.resultExtension
        return originalFile, parsedFile, identifiedStepsFile, resultFile





