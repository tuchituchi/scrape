# !/bin/sh
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --profile-directory="Default" 

echo "First argument: "  $1

# 待機ループを追加してChromeが起動するのを待つ
while ! curl http://localhost:9222 &>/dev/null; 
do
    sleep 1
done

python3 mercariautoresell.py $1 