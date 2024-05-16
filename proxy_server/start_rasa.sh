cd ../models/combined_new && nohup rasa run -m models --enable-api --cors "*" --port 9000 &> rasa_log.log &
