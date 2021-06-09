'''
Configuration file and global variables
'''

# imports
from nltk.stem import WordNetLemmatizer
import spacy
from spacy.matcher import DependencyMatcher

# files

# filename = "android-mileage#3.1.1_53"
# filename = "gnucash-android#2.1.1_615"
# filename = "gnucash-android#2.1.3_620"
# filename = "gnucash-android#2.2.0_699"
# filename = "gnucash-android#2.2.0_701"

extention = ".xml"
resultExtention = ".txt"
# directories
# originalDir = "data/0_original_bug_reports/" + filename + extention
# parsedDir = "data/parsed_bug_reports/" + filename + extention
# identifiedStepsDir = "data/identified_s2r_in_bug_reports/" + filename + extention
# resultDir = "data/result_bug_reports/" + filename + resultExtention
originalDir = "data/0_original_bug_reports/"
parsedDir = "data/parsed_bug_reports/"
identifiedStepsDir = "data/identified_s2r_in_bug_reports/"
resultDir = "data/result_bug_reports/"

# action groups
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

# special actions
specialClickActions = ["choose", "select", "pick", "go", "create", "add", "check"]

# nlp
nlp = spacy.load("en_core_web_sm")

# dependency matcher
dep_matcher = DependencyMatcher(vocab=nlp.vocab)

# wordnet lemmatizer
lemmatizer = WordNetLemmatizer()







