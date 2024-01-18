#!/bin/bash

# resellcountを直接指定
resellcount=2  # 任意の値に変更してください

# PyInstallerで作成した実行可能ファイルを実行
/Users/tasshihonsaeko/scrape/dist/mercariautoresell <<EOF
$resellcount
EOF
