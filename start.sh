mkdir server
python3 -m http.server -d server &
python3 main.py import geminibot.tar
python3 main.py link
python3 main.py serve
