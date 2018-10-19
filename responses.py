import pickle
import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import numpy as np
import tflearn
import tensorflow as tf
import random
import pymysql
from PIL import Image
import warnings
import re

warnings.filterwarnings("ignore")

db = pymysql.connect("localhost","root","526527492","hrbot" )

# prepare a cursor object using cursor() method
cur = db.cursor()

# disconnect from server
#db.close()

bot_template = "BOT  :"

data = pickle.load( open( "training_data", "rb" ) )
words = data['words']
classes = data['classes']
train_x = data['train_x']
train_y = data['train_y']

# import our chat-bot intents file
import json
with open('intents.json') as json_data:
    intents = json.load(json_data)

# Build neural network
net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
net = tflearn.regression(net)

# Define model and setup tensorboard
model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')

def clean_up_sentence(sentence):
    # tokenize the pattern
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=False):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0]*len(words)  
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s: 
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)

    return(np.array(bag))


model.load('./model.tflearn')

context = {}

ERROR_THRESHOLD = 0.25
def classify(sentence):
    # generate probabilities from the model
    results = model.predict([bow(sentence, words)])[0]
    # filter out predictions below a threshold
    results = [[i,r] for i,r in enumerate(results) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append((classes[r[0]], r[1]))
    # return tuple of intent and probability
    return return_list

def leave():
    print('BOT  : Please give your id no. to check your record')
    print("USER :",end = " ")
    while True:
        try:
            id = int(input())
            cur.execute("SELECT `leave` from employees where Employee_Number = {0}".format(id))
            if cur.rowcount == 0:
                return print("BOT  : Please register on the panel first.")
            else:
                leave = cur.fetchall()
                leave = leave[0][0]
                cur.execute("SELECT Employee_Name from employees where Employee_Number = {0}".format(id))
                name = cur.fetchall()
                name = name[0][0]
                name = name.replace(',', '')
                if leave == 0:
                    if intents['intents'][6]['tag'] == 'leave':
                        return print(intents['intents'][6]["responses"][1].format(bot_template,name))
                else:
                    if intents['intents'][6]['tag'] == 'leave':
                            return print(intents['intents'][6]["responses"][0].format(bot_template,name,leave))
        except ValueError:
            print("BOT  : Please enter valid emp id")
            print("USER :",end = " ")
            continue
        else:
            break

def policy():
    image = Image.open('policy.jpg')
    image.show()
    return print("{} Please look at image which contain full policy details.".format(bot_template))

def find_name(message):
    name = None
    # Create a pattern for checking if the keywords occur
    name_keyword = re.compile(' |name|call')
    # Create a pattern for finding capitalized words
    name_pattern = re.compile('[A-Z]{1}[a-z]*')
    if name_keyword.search(message):
        # Get the matching words in the string
        name_words = name_pattern.findall(message)
        if len(name_words) > 0:
            # Return the name if the keywords are present
            name = ' '.join(name_words)
    return name

def recruitment():
    print(intents['intents'][3]["responses"][0].format(bot_template))
    print("USER :",end = " ")
    while True:
        try:
            name = input()
            name = find_name(name)
            if name is not None:
                return print("BOT  : Hello, {0}! {1}".format(name,intents['intents'][3]["responses"][1]))
            else:
                print("{} Please use call me or name like: call me John OR My name is John".format(bot_template))
                print("USER :",end = " ")
                continue
        except ValueError as e:
            print("Error:",e)          
        else:
            break


def response(sentence, userID='123', show_details=False):
    results = classify(sentence)
    #print("Results: ",results)
    # if we have a classification then find the matching intent tag
    if results:
        # loop as long as there are matches to process
        while results:
            for i in intents['intents']:
                # find a tag matching the first result
                if i['tag'] == results[0][0]:
                    # set context for this intent if necessary
                    if 'context_set' in i:
                        if show_details: print ('context:', i['context_set'])
                        context[userID] = i['context_set']

                    # check if this intent is contextual and applies to this user's conversation
                    if not 'context_filter' in i or (userID in context and 'context_filter' in i and i['context_filter'] == context[userID]):
                        if show_details: print ('tag:', i['tag'])
                        # a random response from the intent
                        elif results[0][0] == 'leave':
                            leave()
                        elif results[0][0] == 'policy':
                            policy()
                        elif results[0][0] == 'recruitment':
                            recruitment()
                        else:
                            return print("{0} {1}".format(bot_template,random.choice(i['responses'])))

            results.pop(0)


print("USER :",end = " ")
message = input()
while True:
    response(message)
    if message != "bye":
        print("USER :",end = " ")
        message = input()
        continue
    else:
        break
