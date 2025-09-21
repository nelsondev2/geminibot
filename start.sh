mkdir server
python3 -m http.server -d server &
python3 main.py import account_db.tar
python3 main.py link
python3 main.py serve
