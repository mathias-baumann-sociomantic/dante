#!/usr/bin/env python

from collections import deque
import string, random, sys, os, re, imp
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

cp = imp.find_module('cPickle')
cPickle = imp.load_module('cPickle', cp[0], cp[1], cp[2])

MAXGEN=1000 # Max number of words to generate
NONWORD = '\n' # Use as start- and endmarkers
TARGET = '<TARGET>'
OTHER  = '<OTHER>'

CHATTINESS = 0.02

SAVECOUNT = 30

crontable = []
outputs = []
savecounter = 0
users = {}
active = deque([], 10)

nickname = "dante"

print "Markov init"
dict = cPickle.load(open("markov.state", 'r'))

def replace_smart(word):
#if string.lower(word) == "who":
#       return OTHER

    return word

#def handle_pubmsg(self, connection, event):
def process_message(data):
    global users
    global active
    spoken = 0
    addressed = 0
    directly_addressed = 0
    chainable = 1
    try:
        users = data['users']
        whonick = next(i for i in users if i.id == data['user']).name
    except:
        return

    active.append(whonick)

    message = data['text']; 
    if re.search(string.lower(nickname),
                 string.lower(message)):
        addressed = 1

    if message == "%s, status?" % nickname:
        outputs.append([data['channel'], "I know %s phrases" %
                           str(len(dict.keys()))])
        return


#message = self.strip_nick(message, whonick)
    message = strip_shit(message)

    if chainable and whonick != "hugo":
        print "Learning"
        input(message)


    if not spoken:
        splitmsg = string.split(message, ' ')
        try:
            if len(splitmsg) >= 1 and \
               string.strip(splitmsg[0], ",:") == nickname:
               splitmsg.pop(0)
               directly_addressed = 1 

               print "input: " + message
            if len(splitmsg) >= 2:
                text = string.strip(output(whonick, \
                            replace_smart(replace_name(splitmsg[0])),   \
                            replace_smart(replace_name(splitmsg[1]))))

            tries = 10

            while text == string.join(splitmsg) and tries > 0:
                print "Found equal, retrying", tries, text
                text = string.strip(output(whonick, 
                            replace_smart(replace_name(splitmsg[0])),
                            replace_smart(replace_name(splitmsg[len(splitmsg)-1]))))
                print "New: ", text
                tries = tries - 1
                if tries == 0:
                    text = string.strip(output(whonick))
        except:
            text = string.strip(output(whonick))

    if directly_addressed \
        and not text.startswith(".") \
        and not text.startswith(whonick) \
        and not text.startswith(":") \
        and not whonick == "hugo":
        outputs.append([data['channel'], whonick + ", " + text])
    elif addressed or random.random() < CHATTINESS:
        outputs.append([data['channel'], text])

def strip_nick(message, sender):
    return string.replace(string.strip(message),
                          nickname, sender)

def strip_shit(message):
    index = 0 
    for char in string.lower(message):
        if char in [',']:
            index = index + 1
        else:
            break
    return string.strip(message[index:])

    
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
        print "target replaced with", speaker
        return speaker
    elif word == OTHER:
#        r = "ruport"
        r = active[0]
        print OTHER + " OTHER replaced with", r
        return r
    else:
        return word

def replace_name(word):
    stripped = string.lower(string.strip(word, ",:><|?!.()\\/{}[]"))

    print "stripped name: " + stripped
    print "nickname: " + nickname
    if stripped == string.lower(nickname):
        print "myself replaced with mark"
        return TARGET
    elif stripped in users:
        print "name, replaced with mark"
        return OTHER
        
    return word

def output(speaker, word1=NONWORD, word2=NONWORD):
    #word1,word2 = NONWORD, NONWORD # Start at beginning

    print "gen output for input " + word1 + word2

    output = replace_mark(word1, speaker) + " " + \
             replace_mark(word2, speaker)

    try:
        for i in range(MAXGEN):
            successorList = dict[(word1,word2)]
            word3 = random.choice(successorList)
            if word3 == NONWORD:
                break
            output = output + " "  + replace_mark(word3, speaker)

            word1, word2 = word2, word3
    except:
        return output(speaker)
        pass

    return output

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

        
    
