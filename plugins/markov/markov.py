#!/usr/bin/env python

from collections import deque
import string, random, sys, os, re, imp
from pprint import pprint
import sys  
import traceback

reload(sys)  
sys.setdefaultencoding('utf8')

cp = imp.find_module('cPickle')
cPickle = imp.load_module('cPickle', cp[0], cp[1], cp[2])

MAXGEN=1000 # Max number of words to generate
NONWORD = '\n' # Use as start- and endmarkers
TARGET = '<TARGET>'
OTHER  = '<OTHER>'

CHATTINESS = 0.01

SAVECOUNT = 30

crontable = []
outputs = []
savecounter = 0
users = {}
active = deque([], 3)
clone_response_counter = 0

nickname = "dante"
myid = ""

print "Markov init"
dict = cPickle.load(open("markov.state", 'r'))

def replace_smart(word):
#if string.lower(word) == "who":
#       return OTHER

    return word

def extractUserName ( nick ):
    global users
    stripped = nick.strip("<,:>@").upper()

    for k, i in users.iteritems():
        if i.id == stripped:
            return i.name

    return nick 

def isName ( name ):
    nn = extractUserName(name)

    for k, i in users.iteritems():
        if i.name == nn:
            return True

    return False

#def handle_pubmsg(self, connection, event):
def process_message(data):
    global users
    global active
    global clone_response_counter
    global myid
    addressed = 0
    directly_addressed = 0
    chainable = 1
    whonick = ""
    message = ""


    print "================================"

    try:
        users = data['users']
        if 'user' in data:
            whonick = next(i for k, i in users.iteritems() if i.id == data['user']).name
    except Exception as inst:
        print "Exception: " + str(inst)
        traceback.print_exc()
        print "stopping."
        pprint(data)
        return

    # Find out our own id
    if users:
        if len(myid) == 0:
            myid = next(i for k, i in users.iteritems() if i.name == nickname).id

    active.append(whonick)

    if 'attachments' in data:
        if 'text' in data['attachments'][0]:
            message = data['attachments'][0]['text']
        else:
            return
    elif 'text' in data:
        message = data['text']; 

    print "input: " +  message

    if len(message) == 0:
        pprint(data)
        return

    if re.search(string.lower(nickname),
                 string.lower(message)) or \
            re.search(myid, message):
        addressed = 1

    if message == "%s, status?" % nickname:
        pprint(data)
        outputs.append([data['channel'], "I know %s phrases" %
                           str(len(dict.keys()))])
        return


#message = self.strip_nick(message, whonick)
    message = strip_shit(message)

    if chainable and whonick != "hugo" and whonick != nickname:
        print "Learning"
        input(message)

#    print data['channel']

    if data['channel'] != 'G0NKSTBEF':
        print "Ignoring non #reporting-team-private channel"
        return

    if whonick == nickname and addressed:
        clone_response_counter+=1
        print "Clone Response Counter at %s" % clone_response_counter

    if clone_response_counter > 5:
        print "Too much clone talk, ignoring..."
        clone_response_counter = 0
        return

    splitmsg = string.split(message, ' ')
    try:
        if len(splitmsg) >= 1:
            stripped = string.strip(splitmsg[0], ",:")
            if extractUserName(stripped) == nickname:
               splitmsg.pop(0)
               directly_addressed = 1

            text = ""

            if len(splitmsg) >= 2:
                chose = random.randint(1, len(splitmsg)-1)
                text = string.strip(output(whonick, \
                            replace_smart(replace_name(splitmsg[chose-1])),   \
                            replace_smart(replace_name(splitmsg[chose]))))

            max_tries = 10
            tries = 0

            text = string.strip(output(whonick))

            while (text == string.join(splitmsg) or \
                   len(text) == 0 or \
                   text.find("CRITICAL") > -1 or \
                   text.find("is OK") > -1 or \
                   text.find("This pull request has been rebased via") > -1 or \
                   text.find("://github.com/") > -1) \
                   and tries < max_tries:

                if tries + 1 >= len(splitmsg) or tries+1 == max_tries:
                    text = string.strip(output(whonick))
                    break

                print "Not accepted attempt ", tries, text
                text = string.strip(output(whonick,
                            replace_smart(replace_name(splitmsg[tries])),
                            replace_smart(replace_name(splitmsg[tries+1]))))
                tries = tries + 1

            print "Accepted:", text


    except Exception as inst:
        traceback.print_exc()
#print "Exception: " + str(inst)
        text = string.strip(output(whonick))

    if directly_addressed \
        and not text.startswith(".") \
        and text.find(whonick) == -1 \
        and not text.startswith(":") \
        and not whonick == "hugo":
        outputs.append([data['channel'], whonick + ", " + text])
    elif addressed or random.random() < CHATTINESS:
        outputs.append([data['channel'], text])

def strip_nick(message, sender):
    return string.replace(string.strip(message),
                          nickname, sender)

def has_nick(message, nick):
    return text.find(nick) == -1



def strip_shit(message):
    index = 0 
    for char in string.lower(message):
        if char in [',']:
            index = index + 1
        else:
            break
    return string.strip(message[index:], " <>")

    
def input(originalText):
    global savecounter
    word1, word2 = NONWORD, NONWORD
    wordList = string.split(originalText)
    for word3 in wordList: # Loop over rest of words

        word3 = replace_name(word3)

        if not dict.has_key( (word1,word2) ):
            dict[(word1,word2)] = [] #initialize to empty list
        dict[(word1, word2)].append(word3) # Add suffix for word-pair
        word1,word2 = word2, word3 # Shift in new words as dictionary keys
    dict[(word1,word2)] = [NONWORD] # Mark end of text
    savecounter = savecounter + 1        
    if savecounter >= SAVECOUNT:
        dumpdb()
        savecounter = 0

#print "debug: ", dict[("I", "am")]
        
def dumpdb():
    try:
        os.rename("markov.state.2", "markov.state.3")
    except:
        pass
    try:
        os.rename("markov.state.1", "markov.state.2")
    except:
        pass
    try:
        os.rename("markov.state", "markov.state.1")
    except:
        pass
    cPickle.dump(dict, open("markov.state", "w"))

def replace_mark(word, speaker = NONWORD):
    if word == TARGET:
#        print "target replaced with", speaker
        return speaker
    elif word == OTHER:
#        r = "ruport"
        r = active[0]
#        print OTHER + " OTHER replaced with", r
        return r
    else:
        return word

def replace_name(word):
    stripped = string.lower(string.strip(word, ",:><|?!.()\\/{}[]"))

    if extractUserName(stripped) == nickname.lower():
#       print "myself replaced with mark"
        return TARGET
    elif isName(stripped):
#print "name replaced with mark"
        return OTHER
    
    return word

def output(speaker, word1=NONWORD, word2=NONWORD):
    #word1,word2 = NONWORD, NONWORD # Start at beginning

    print "Gen Output from ", word1, ", ", word2;

    text = replace_mark(word1, speaker) + " " + \
             replace_mark(word2, speaker)

    for i in range(MAXGEN):
        if (word1,word2) not in dict:
            successorList = random.choice(dict.keys())
        else:
            successorList = dict[(word1,word2)]

        word3 = random.choice(successorList)

        if word3 == NONWORD:
            break

#        print "checking: " + extractUserName(word1) + " " + \
#                             extractUserName(word2)+ " " + \
#                             extractUserName(word3)
        if isName(word3) or isName(word2) or isName(word1) or \
           word3.startswith("**") or word1.startswith("CRITICAL"):
            print "output so far", text;
            print "removing (" + word1 + ", " + word2 + ") => " + word3
            del dict[(word1,word2)]
            continue

        text = text + " "  + string.strip(replace_mark(word3, speaker), "<>")

        word1, word2 = word2, word3

    return text

def clean_dict ( ):
    for key in dict.keys():
        word1 = key[0]
        word2 = key[1]
        if word1 in self.bot.interfaces["users"]() or \
           word2 in self.bot.interfaces["users"]() or \
            len(self.dict[(word1, word2)]) == 0:
            try:
                del self.dict[(word1, word2)]
                print "removed (", string.strip(word1), ", ", string.strip(word2), ")"
            except:
                print     "error: ", sys.exc_info()[0]
                pass
            
        else:
            for name in self.bot.interfaces["users"]():
                try:
                    self.dict[(word1,word2)].remove(name)
                    print "removed (", string.strip(word1), ", ", \
                            string.strip(word2), ").", string.strip(name)
                except:
                    pass

        
    
