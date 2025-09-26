mkdir server
python3 -m http.server -d server &
python3 main.py import geminibot.tar
python3 main.py link
python3 main.py config skip_start_messages 1
python3 main.py config displayname GemImg
python3 main.py config selfavatar covers.png
python3 main.py serve
