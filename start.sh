mkdir server
python3 -m http.server -d server &
python3 main.py init geminiimg@chat.lylapol.com img123456789
python3 main.py link
python3 main.py serve
