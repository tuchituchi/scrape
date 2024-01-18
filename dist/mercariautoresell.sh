#!/bin/bash

# resellcountを直接指定
resellcount=2  # 任意の値に変更してください

# sleep_time=$((RANDOM % 5))
# sleep $sleep_time

# PyInstallerで作成した実行可能ファイルを実行
/Users/tasshihonsaeko/scrape/dist/mercariautoresell <<EOF
$resellcount
EOF
