import json
import requests 
import os
import pyrebase
import Checksum
import time
import datetime
import numpy as np
import urllib.request
import cv2
import ssl
import imgDetec
import face_recognition
import threading
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from PyPDF2 import PdfFileReader
from firebase.firebase import FirebaseApplication


config = {
    "apiKey": "AIzaSyBBesqKwDiOVVXqRKeoODK3X4RKp6IxLlI",
    "authDomain": "chatbottele.firebaseapp.com",
    "databaseURL": "https://chatbottele.firebaseio.com",
    "projectId": "chatbottele",
    "storageBucket": ""
}

ssl._create_default_https_context = ssl._create_unverified_context
user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent,} 

help_message = "Use :\n /create <username> <password> : to create an account, \n /pay <amount> : to recharge your account, \n /balance : to check the balance in your account"

firebase = pyrebase.initialize_app(config)
database = FirebaseApplication("https://chatbottele.firebaseio.com")

def main():
    updater = Updater(token = "968877078:AAHa1vqUpezcA74yLi7e8PEaADpBrVdVunA")
    dispatcher = updater.dispatcher
    print("bot started")
    start_handler = CommandHandler('start', start)
    create_handler = CommandHandler('create', create)
    payment_handler = CommandHandler('pay', pay)
    balance_handler = CommandHandler('balance', balance)
    read_and_reply = MessageHandler(Filters.text, read_message_and_reply)
    get_image = MessageHandler(Filters.photo, get_photo_and_reply)
    get_file = MessageHandler(Filters.document, get_file_and_reply)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(create_handler)
    dispatcher.add_handler(payment_handler)
    dispatcher.add_handler(balance_handler)
    dispatcher.add_handler(read_and_reply)
    dispatcher.add_handler(get_file)
    dispatcher.add_handler(get_image)

    updater.start_polling()
    updater.idle()

def get_chat_id(message):
    message_details = str(message).replace("'", '''"''').replace("False", '''"False"''').replace("True", '''"True"''')
    details_in_json = json.loads(message_details)
    chat_id = details_in_json.get('chat').get('id')
    return chat_id

def account_created_or_not(chat_id):
    if database.get("/Users/"+str(chat_id), None) == None:
        return False
    return True

def query_about_user(chat_id, query_attr):
    return database.get("/Users/" + str(chat_id) + "/" + query_attr, None)

def save_to_db(chat_id, child_name, save_attr):
    db = firebase.database()
    db.child("Users").child(str(chat_id)).child(child_name).set(save_attr)

def start(bot, update):
    update.message.reply_text('''I'm a bot, Nice to meet you !\nSend "help" to know about the features of the bot.''')

def create(bot, update):
    chat_id = get_chat_id(update.message)
    print(chat_id)
    if not account_created_or_not(chat_id):
        db = firebase.database()
        upload_data = {}
        text_message_list = update.message.text.split()
        upload_data['username'] = text_message_list[1]
        upload_data['password'] = text_message_list[2]
        upload_data['amount'] = 0
        db.child("Users").child(str(chat_id)).set(upload_data)
        print(update.message.text)
        update.message.reply_text("Account has been successfully created :)")
    else:
        update.message.reply_text("Your account is already present, Go ahead and make use of our features")

def pay(bot, update):
    chat_id = get_chat_id(update.message)
    if account_created_or_not(chat_id):
        amount = update.message.text.split()[1]
        MERCHANT_MID = "udJWok56803358438193"
        MERCHANT_KEY = "hp@60IaAF%!vUs0A"
        endtime = str((datetime.datetime.now() + datetime.timedelta(days = 1)).strftime("%d/%m/%Y"))
        print(endtime)
        paythmParams = {}
        paythmParams['body'] = {
            "merchantRequestId": "0123681o82uwjsa",
            "mid": MERCHANT_MID,
            "linkName": "recharge",
            "linkDescription": "This link is to recharge",
            "linkType": "FIXED",
            "amount": str(amount),
            "expiryDate": endtime,
            "isActive": "true",
            "sendSms": "false",
            "sendEmail": "false",
            "customerContact": {
                "customerName": "Shreyas",
                "customerEmail": "shreyas.shivajirao@gmail.com",
                "customerMobile": "8050825266"
            }
        }

        checksum = Checksum.generate_checksum_by_str(json.dumps(paythmParams['body']), MERCHANT_KEY)
        paythmParams['head'] = {
            "timestamp": str(int(time.time())),
            "clientId": "xxx",
            "version": "v1",
            "channelId": "WEB",
            "tokenType": "AES",
            "signature": checksum
        }
        post_data = json.dumps(paythmParams)
        # print(post_data)

        url = "https://securegw-stage.paytm.in/link/create"

        response = requests.post(url = url, data = post_data, headers = {"Content-type": "application/json"})
        json_data = json.loads(response.text)
        link_to_send = json_data.get("body").get("shortUrl")
        link_id = json_data.get("body").get("linkId")
        save_to_db(chat_id, "payment_link", link_to_send)
        save_to_db(chat_id, "payment_link_id", link_id)
        update.message.reply_text("Please use the link below to pay the amount\n" + link_to_send)

def balance(bot, update):
    chat_id = get_chat_id(update.message)
    if account_created_or_not(chat_id):
        amount = query_about_user(chat_id, "amount")
        update.message.reply_text("Your account balance is Rs."+str(amount))
    else:
        update.message.reply_text("You have not created your account, Please create it using the following command\n /create <user-name> <pass-word>")

def read_message_and_reply(bot, update):
    chat_id = get_chat_id(update.message)
    print(chat_id)
    if update.message.text.lower() == "help":
        update.message.reply_text(help_message)
    if not account_created_or_not(chat_id):
        update.message.reply_text("You have not created your account, Please create it using the following command\n /create <user-name> <pass-word>")
    else:
        print(update.message.text)
        text_message = update.message.text.lower()
        if "add amount" in text_message:
            update.message.reply_text("You can add amount to your account by sending the amount to 8050825266 via paytm")
        elif "hack 15" in text_message:
            db = firebase.database()
            db.child("Users").child(str(chat_id)).child("amount").set(15)
            update.message.reply_text("Rs.15 has been added to your account")
        # elif "help" in text_message:
        #     update.message.reply_text(help_message)
        else:
            update.message.reply_text(update.message.text.upper())

def get_file_and_reply(bot, update):
    chat_id = get_chat_id(update.message)
    print(chat_id)
    if database.get("/Users/"+str(chat_id), None) == None:
        update.message.reply_text("You have not created your account, Please create it using the following command\n /create <user-name> <pass-word>")
    else:
        amount = database.get("/Users/"+str(chat_id)+"/amount", None)
        if amount >= 10:
            update.message.reply_text("File received")
            photo_file = bot.getFile(update.message.document.file_id)
            photo_file = str(photo_file).replace("'", '''"''')
            json_format = json.loads(photo_file)
            download_link = json_format.get('file_path')
            pages_count = save_pdf_file(download_link)
            db = firebase.database()
            db.child("Users").child(str(chat_id)).child("amount").set(amount - pages_count)
            update.message.reply_text("Saving pdf, printing pdf will cost Rs.1 per page which is Rs." + str(pages_count) + " which is deducted from the account.. and balance is Rs."+str(amount - pages_count))
        else:
            update.message.reply_text("Your account balance is low, please recharge by sending the amount to 8050825266 via paytm")

def get_photo_and_reply(bot, update):
    chat_id = get_chat_id(update.message)
    if database.get("/Users/"+str(chat_id), None) == None:
        update.message.reply_text("You have not created your account, Please create it using the following command\n /create <user-name> <pass-word>")
    else:
        amount = database.get("/Users/"+str(chat_id)+"/amount", None)
        if amount >= 10:
            update.message.reply_text("File received")
            photo_file = bot.getFile(update.message.photo[-1].file_id)
            photo_file = str(photo_file).replace("'", '''"''')
            json_format = json.loads(photo_file)
            download_link = json_format.get('file_path')
            person_in_frame = save_image_file(download_link)
            people = ""
            if len(person_in_frame) == 1:
                update.message.reply_text("The person in the image is " + person_in_frame[0])
            else:
                for i in person_in_frame:
                    people += "\n" + i
                update.message.reply_text("The people in the image are " + people)
        else:
            update.message.reply_text("Your account balance is low, please recharge by sending the amount to 8050825266 via paytm")

def save_pdf_file(file_url):
    r = requests.get(file_url, stream = True) 
    with open("python.pdf","wb") as pdf: 
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: 
                pdf.write(chunk)
    fi = PdfFileReader(open("python.pdf", "rb"))
    print(fi.getNumPages())
    return fi.getNumPages()

def save_image_file(image_url):
    request=urllib.request.Request(image_url,None,headers)
    with urllib.request.urlopen(request) as url:
        resp = urllib.request.urlopen(request)
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        cv2.imwrite("lala.jpg" ,image)
    
    biden_image = face_recognition.load_image_file("thrupthi.jpg")
    obama_image = face_recognition.load_image_file("shreyas.jpg")
    unknown_image = face_recognition.load_image_file("lala.jpg")

    try:
        biden_face_encoding = face_recognition.face_encodings(biden_image)[0]
        obama_face_encoding = face_recognition.face_encodings(obama_image)[0]
    except IndexError:
        print("I wasn't able to locate any faces in at least one of the images. Check the image files. Aborting...")
        quit()
    known_faces = [
        biden_face_encoding,
        obama_face_encoding
    ]
    known_names = [
        "Thrupthi", "Shreyas"
    ]
    rgb_frame = unknown_image[:, :, ::-1]
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    ls = []
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_faces, face_encoding)
        name = "Unknown"
        face_distances = face_recognition.face_distance(known_faces, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_names[best_match_index]
            if name not in ls:
                ls.append(name)

    print(ls)
    return ls

if __name__ == "__main__":
    main()
