'''
###########################################################################
##                                                                       ##
##                Centre for Development of Advanced Computing           ##
##                               Mumbai                                  ##
##                         Copyright (c) 2024                            ##
##                        All Rights Reserved.                           ##
##                                                                       ##
##  Permission is hereby granted, free of charge, to use and distribute  ##
##  this software and its documentation without restriction, including   ##
##  without limitation the rights to use, copy, modify, merge, publish,  ##
##  distribute, sublicense, and/or sell copies of this work, and to      ##
##  permit persons to whom this work is furnished to do so, subject to   ##
##  the following conditions:                                            ##
##   1. The code must retain the above copyright notice, this list of    ##
##      conditions and the following disclaimer.                         ##
##   2. Any modifications must be clearly marked as such.                ##
##   3. Original authors' names are not deleted.                         ##
##   4. The authors' names are not used to endorse or promote products   ##
##      derived from this software without specific prior written        ##
##      permission.                                                      ##
##                                                                       ##
##                                                                       ##
###########################################################################
##                                                                       ##
##                       Multilingual Chatbot                            ##
##                                                                       ##
##            Designed and Developed by Language Computing Group         ##
##          		       Date:  April 2023                             ##
##                                                                       ## 
###########################################################################
'''

from flask import Flask,request,jsonify
import os
import json
import base64
import requests
from langcodes import *
from datetime import datetime
import sqlite3

from flask_cors import CORS,cross_origin

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

AUDIO_UPLOAD_PATH = "YOUR_WAV_PATH"
ASR_API = "https://asr.iitm.ac.in/asr/v2/decode"
CDAC_ASR_API = "https://speechindia.in/asr/transcribe"
TTS_API = "https://asr.iitm.ac.in/ttsv2/tts"
RASA_API = "http://0.0.0.0:9000/webhooks/rest/webhook"
AUDIO_PATH = "/var/www/html/chatbot/multilingual"
VIDEO_PATH = "/var/www/html/chatbot/multilingual_avatar"
LOG_PATH = "YOUR_LOG_PATH"
MODEL_PATH = "../models/combined_new"

# import logging

# logging.basicConfig(filename='example.log', level=logging.DEBUG)

@app.route('/recognize_cdac', methods=['POST'])
@cross_origin()
def upload_static_file_for_cdac_api():
    client_data = request.get_json()

    # print(client_data)

    file = client_data["file_name"]
    lang = client_data["language"]
    audio = client_data["audio"]

    language = (Language.make(language=lang).display_name()).lower()
    
    file_path = os.path.join(AUDIO_UPLOAD_PATH, language)
    os.makedirs(file_path, exist_ok=True)

    wav_file = open(file_path, "wb")
    decode_string = base64.b64decode(audio)
    wav_file.write(decode_string)

    r = requests.post(CDAC_ASR_API, json={"lang": language, "audio": audio})

    json_text = json.loads(r.text)

    resp = {"success": True, "response": json_text["text"]}
    print("RESPONSE :: ", resp)

    return jsonify(resp), 200


@app.route('/recognize_iitm', methods=['POST'])
@cross_origin()
def upload_static_file_for_iitm_api():
    print(request.files)
    f = request.files['audio']
    lang = request.form.get('language')
    filename = request.form.get('filename')
    language = (Language.make(language=lang).display_name()).lower()
    # asr_lang =  language.lower()
    print("REQUEST :: Language : ",language)
    audio_file_path = os.path.join(AUDIO_UPLOAD_PATH, language)
    os.makedirs(audio_file_path, exist_ok=True)
    f.save(os.path.join(audio_file_path, filename))

    print("LANGUAGE", language)

    payload={'vtt': 'false', 'language': language}
    print(payload)
    wav_path = os.path.join(audio_file_path, filename)
    files=[('file',(filename, open(wav_path,'rb'),'application/octet-stream'))]
    headers = {}

    print ("SENDING: ", " request :", ASR_API)
    response = requests.request("POST", ASR_API, headers=headers, data=payload, files=files)

    print("RECEIVED : ",response.text)
    resp = {"success": True, "response": response.text}
    print("RESPONSE :: ", resp)

    return jsonify(resp), 200

@app.route('/synthesize_iitm', methods=['POST'])
@cross_origin()
def get_audio_file():
    content = request.get_json()
    print("REQUEST : ", content)
    language = content["language"]
    message = content["message"]
    # print("REQUEST :: Language : ",language)
    language = Language.make(language=language).display_name()

    payload = json.dumps({
		"input": message,
		"gender": "female",
		"lang": language,
		"alpha": 1.0,
		"segmentwise":"False"
    })

    print("REQUEST :: TTS : ",payload)

    headers = {'Content-Type': 'application/json'}

    response = requests.request("POST", TTS_API , headers=headers, data=payload)
    # print("RECEIVED : ",response.text)
    resp = {"success": True, "response": response.text}
    # print("RESPONSE :: ", resp)

    return jsonify(resp), 200


@app.route('/synthesize_iitm_local', methods=['POST'])
def get_audio_file_local():
    content = request.get_json()
    print("REQUEST : ", content)
    language = content["language"]
    message = content["message"]
    # print("REQUEST :: Language : ",language)
    audio_file_path = os.path.join(AUDIO_PATH , "synth")

    path = "empty"

    file = open(os.path.join(audio_file_path, "metadata.txt"),encoding="utf-8")
    lines = file.readlines()
    for line in lines:
        text = line.split("\t")
        # print("Compare : ",text,message)
        if(text[0] == message):
            path = text[1]
            path = path.replace("\n","")
    
    resp = {"success": True, "response": path}
    print("RESPONSE :: ", resp)
    return jsonify(resp), 200

@app.route('/get_aavtar', methods=['POST'])
def get_aavtar_local():
    content = request.get_json()
    print("REQUEST : ", content)
    language = content["language"]
    message = content["message"]
    # print("REQUEST :: Language : ",language)
    video_file_path = os.path.join(VIDEO_PATH, "aavtar_videos")

    path = "empty"

    file = open(os.path.join(video_file_path, "metadata_aavtar.txt"),encoding="utf-8")
    lines = file.readlines()
    for line in lines:
        text = line.split("\t")
        # print("Compare : ",text,message)
        if(text[0] == message):
            path = text[1]
            path = path.replace("\n","")
    
    resp = {"success": True, "response": path}
    print("RESPONSE :: ", resp)
    return jsonify(resp), 200
    
@app.route('/send_to_bot', methods=['POST'])
@cross_origin()
def get_message():
    content = request.get_json()
    print("Content: ",content)
    language = content["lang"]
    time_taken = content["time_taken"]
    isASR = content["isASR"]
    # print("data : ", content)
    del content['lang']
    send_to_rasa = json.dumps(request.get_json())
    # print("LNAG : ", language)
    # print("obj : ", send_to_rasa)

    # app.logger.info('%s logged in successfully', "uusername")

    f_log = open(LOG_PATH, 'a')

    msg = json.loads(send_to_rasa)
    f_log.write(str(datetime.now()) + " USER # " + language + " # ID # " + str(msg["sender"]) + " # Time Taken: " + str((time_taken/1000)%60) + "s # is ASR: " + str(isASR) + " # # # # " + str(msg["message"].encode('utf-8')) + "\n")
    
    r = requests.post(url = RASA_API, data = send_to_rasa)
    print("RESPONSE :: ", r.text)

    msg = json.loads(r.text)
    if msg:
        intent, confidence, isFallback = getConfidence(msg[0]["recipient_id"], "user")
        # log file : timestamp BOT language sender_id fallback intent confidence message
        f_log.write(str(datetime.now()) + " BOT # " + language + " # ID # " + msg[0]["recipient_id"] + " # Fallback:" + str(isFallback) + " # intent: " + intent + " # " + str(round(confidence, 2)) + " # " + str(msg[0]["text"].encode('utf-8')) + "\n")
    else:
        f_log.write(str(datetime.now()) + " BOT # " + language + " EMPTY RESPONSE " + "\n")
    return jsonify(r.text), 200


def getConfidence(sender_id, user):
    con = sqlite3.connect(os.path.join(MODEL_PATH, "logs.db"))
    cur = con.cursor()
    res = cur.execute('SELECT data FROM events where sender_id = ? and type_name = ?', (sender_id, user))

    isFallback = False
    
    json_data = json.loads(res.fetchone()[0])
    intent_ranking = json_data["parse_data"]["intent_ranking"]
    first_rank = intent_ranking[0]["name"]
    confidence = intent_ranking[0]["confidence"]

    if (first_rank == "nlu_fallback"):
        print("fallback!")
        isFallback = True
        first_rank = intent_ranking[1]["name"]
        confidence = intent_ranking[1]["confidence"]

    return first_rank, confidence, isFallback

if __name__ == '__main__':
   app.run()
