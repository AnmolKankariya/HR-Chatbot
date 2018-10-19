import pymysql
from rasa_nlu.model import Metadata, Interpreter
from rasa_nlu.converters import load_data
from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Trainer
import warnings
import re
import random
import datetime
import sys
import warnings
from PIL import Image
    
bot_template = "BOT : {0}"

# Open database connection
db = pymysql.connect("localhost","root","526527492","hrbot")

# prepare a cursor object using cursor() method
cur = db.cursor()

# disconnect from server
#db.close()

# Create args dictionary
args = {"pipeline":"spacy_sklearn"}

# Create a configuration and trainer
config = RasaNLUConfig(cmdline_args=args)

trainer = Trainer(config)

# Load the training data
training_data = load_data("training.json")

# Create an interpreter by training the model
interpreter = trainer.train(training_data)

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

responses = {
"greet": ['Hello! how can i help you?'],
"goodbye": ['bbyee..:)','bye', 'farewell'],
"holiday":['{0}, You can take {1} leaves only.','{0}, Sorry! You cannot take any leave because you already had so many holidays.','See you on {}'],
"affirm":['yeah','Perfect!'],
"thankyou": ['You are welcome!'],
"recruitment":["{} Okay! Let's start the process.\nBOT : What's your name?",'tell me about yourself.',"Didn't find such position"]
}

keywords = {'greet': ['Hello!','Hello','Hi!','Hi','hello', 'hi', 'hey'],
            'goodbye': ['bbyee..','bye', 'farewell'],
            'thankyou': ['Thanks','Thank you','thank you','thanks', 'thx']
            }

patterns = {}

for intent, keys in keywords.items():
    # Create regular expressions and compile them into pattern objects
    # Use '|'.join(keys) to create regular expressions to match at least one of the keywords.
    patterns[intent] = re.compile('|'.join(keys))
    
def match_intent(message):
    matched_intent = None
    for intent, pattern in patterns.items():
        # Check if the pattern occurs in the message 
        if pattern.search(message):
            matched_intent = intent
    return matched_intent

def send_message(message):		
    # Get the bot's response to the message
    response = respond(message)
    # Print the bot template including the bot's response.
    print(bot_template.format(response))

warnings.filterwarnings("ignore")
def respond(message):
    intent = interpreter.parse(message)["intent"]['name']
    #print(intent)
    name = find_name(message)
    entity = interpreter.parse(message)["entities"]
    #print(entity)
    #print(entity)
    intent_greet = match_intent(message)
    #print(intent_greet)
    if intent == "affirm":
        return random.choice(responses["affirm"])
    elif intent == "holiday":
        print('BOT : Please give your id no. to check your record')
        print("USER :",end = " ")
        while True:
            try:
                id = int(input())
                cur.execute("SELECT `leave` from employees where Employee_Number = {0}".format(id))
                if cur.rowcount == 0:
                    return "Please register on the panel first."
                else:
                    leave = cur.fetchall()
                    leave = leave[0][0]
                    cur.execute("SELECT Employee_Name from employees where Employee_Number = {0}".format(id))
                    name = cur.fetchall()
                    name = name[0][0]
                    name = name.replace(',', '')
                    if leave == 0:
                        return responses["holiday"][1].format(name)
                    elif entity:
                        day = entity[0]['value']
                        now = datetime.datetime.now().date() 
                        coming_date = now + datetime.timedelta(days=int(day))
                        return responses["holiday"][2].format(coming_date)
                    else:
                        return responses["holiday"][0].format(name,leave)
            except ValueError:
                print("BOT : Please enter valid emp id")
                print("USER :",end = " ")
                continue
            else:
                break
    elif intent == "recruitment":                
        if entity:
            if entity[0]['entity'] == 'position':
                bot_templat = "BOT :"
                print(responses['recruitment'][0].format(bot_templat))
                print("USER :",end = " ")
                name = input()
                if name is not None:
                    return "Hello, {0}! {1}".format(name,responses['recruitment'][1])
                else:
                    return "Please use call me or name like: call me John OR My name is John"
            elif entity[0]['entity'] == 'name':
                print("BOT : I am saving your information and will let you know your status after sometime")
                for i in entity:
                    if i['entity'] is not None:
                        print("BOT : {}- {}".format(i['entity'],i['value']))                        
                return "You will recieve an SMS if you get selected for next round"
            else:
                return responses['recruitment'][2]
        else:
            return "Sorry! buddy, please have a seat, I'll get back to you."    
    elif intent_greet in responses:
        key = intent_greet
        return random.choice(responses[key])
    elif intent == "policy":
        image = Image.open('policy.jpg')
        image.show()
        return "Please look at image which contain full policy details."
    else:
        return "I'm sorry :( I couldn't find anything like that"

#message = "I am Anmol Kankariya from MP. I did B.Tech from Amity University with my gpa 6.97 and I was working with Analytixlabs from past 4 months as a Data Science intern."
#print(send_message(message))
#print(interpreter.parse(message))

print("USER :",end = " ")
message = input()
while True:
    send_message(message)
    if message != "bye":
        print("USER :",end = " ")
        message = input()
        continue
    else:
        break


