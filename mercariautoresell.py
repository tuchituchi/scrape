#######importやfromの書かれた内容はいじらないこと#######
import time
import random
from abc import ABCMeta,abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.alert import Alert
import subprocess
import requests
import logging
import os

# ログの出力名を設定（1）
logger = logging.getLogger('LoggingTest')

# ログのコンソール出力の設定（2）
sh = logging.StreamHandler()
logger.addHandler(sh)

# ログのファイル出力先を設定（4）
fh = logging.FileHandler('./cron.log')
logger.addHandler(fh)

logger.log(20, 'info')
logger.log(30, 'warning')
logger.log(100, 'test')
 

# Chromeを起動
chrome_command = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--remote-debugging-port=9223",
    "--profile-directory=Default"
]
subprocess.Popen(chrome_command)

time.sleep(5)

chrome_url = "http://localhost:9223"

# 待機ループ
while True:
    try:
        # ChromeへのHTTPリクエストを送信
        response = requests.get(chrome_url)
        print("reponse")
        print(response)
        
        # 応答があれば、ループを終了
        if response.status_code == 200:
            break
    except requests.ConnectionError:
        # 接続エラーが発生した場合は無視して継続
        pass
    # Chromeが起動するのを待つために1秒間スリープ
    time.sleep(1)

print("Chromeが起動しました。")




#resellcountは再出品の個数、アカウントの強さや出品数に応じて値を設定する
# resellcount = int(input())
resellcount = 3

#フリマクラス
class FreeMarket(metaclass = ABCMeta):
    #ウェブドライバーやChromeを開く際のポート番号を指定
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--remote-debugging-port=9222")
        # ヘッドレスモードを有効化
        self.options.headless = True
        self.options.add_argument("--window-size=400,300")  # ウィンドウサイズを極小に設定
        self.driver = webdriver.Chrome(options=self.options)
    #各サイトのログイン情報を保持しながら指定したURLのサイトを開く
    def open_window(self,URL):
        self.driver.execute_script("window.open()")
        time.sleep(1)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(URL)  
    #商品の再出品
    def resell(self,item,resellcount,cssselector):
        #古い20個を再出品
        for i in reversed(range(len(item)-resellcount,len(item))):
            clone_item = item[i].find_element(By.CSS_SELECTOR,cssselector)
            self.driver.execute_script("arguments[0].scrollIntoView(false);", clone_item)
            clone_item.click()
            time.sleep(random.uniform(20,25))
    #古い商品がある場所まで遷移する挙動を定義
    @abstractmethod
    def move_to_lastpage(self):
        pass
    @abstractmethod
    def get_items(self):
        pass
    @abstractmethod
    def item_delete(self,cssselector):
        pass

class Mercari(FreeMarket):
    def move_to_lastpage(self):
        #もっと見るボタンを押す
        while True:
            try:
                more_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[contains(@class, "merButton") and contains(@class, "sc-bcb083e9-0")]//button'))
                )
            except TimeoutException:
                print("Timeout")
                break
            time.sleep(random.uniform(2,3))
            more_button.click()
            time.sleep(random.uniform(2,3))
    
    def get_items(self):
        #各商品のmeritemobjを取得
        currentListing = self.driver.find_element(By.ID, 'currentListing')
        meritemobj = []
        sellitemcount = 0
        while True:
            try:
                item = currentListing.find_element(By.XPATH,'//*[@id="currentListing"]/div/div['+str(sellitemcount+1)+']')
                meritemobj.append(item)
                sellitemcount += 1
            except NoSuchElementException:
                print("NoSuchElementException.finish get")
                break
        return meritemobj
    
    def item_delete(self,cssselector):
        meritemobj = self.get_items()
        for i in reversed(range(len(meritemobj)-resellcount,len(meritemobj))):
            #画面外のオブジェクトをクリックしないように、スクロール移動
            delete_item = meritemobj[i].find_element(By.CSS_SELECTOR,cssselector)
            self.driver.execute_script("arguments[0].scrollIntoView(false);", delete_item)
            delete_item.click()
            time.sleep(random.uniform(1,2))
            Alert(self.driver).accept()
            time.sleep(random.uniform(4,7)) 

#ラクマクラス
class Rakuma(FreeMarket):
    #古い商品がある場所まで遷移する挙動を定義
    def move_to_lastpage(self):
        try:
            last_content = WebDriverWait(self.driver,20).until(EC.presence_of_element_located((By.CLASS_NAME,"last")))
            WebDriverWait(self.driver,20).until(EC.element_to_be_clickable((By.CLASS_NAME,"last")))
        except TimeoutException:
            try:
                while True:
                    i=2
                    last_content = WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="selling-bottom-pagination"]/nav/span['+str(i)+']/a')))
                    i = i+1
            except TimeoutException:
                if(i==2):
                    last_content = self.driver.find_element(By.XPATH,'//*[@id="selling-bottom-pagination"]/nav/span[1]')
                    WebDriverWait(self.driver,20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="selling-bottom-pagination"]/nav/span[1]')))
                else:
                    last_content = self.driver.find_element(By.XPATH,'//*[@id="selling-bottom-pagination"]/nav/span'+str(i-1)+']/a')
                    WebDriverWait(self.driver,20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="selling-bottom-pagination"]/nav/span'+str(i-1)+']/a')))
        finally:
            time.sleep(20)
            print("lastcontent")
            print(last_content)
            self.driver.execute_script("arguments[0].scrollIntoView(false);", last_content)
            time.sleep(3)
            print(WebDriverWait(self.driver, 30).until(EC.visibility_of(last_content)))
            print("1")
            print(last_content.is_displayed())
            print("2")
            print(last_content.is_enabled())
            time.sleep(3)
            last_content.click()
        
    def get_items(self):
        information_pane = self.driver.find_element(By.XPATH,'//*[@id="selling-container"]')
        item = information_pane.find_elements(By.CLASS_NAME,'media')
        return item
    
    # 古い20個を削除
    def item_delete(self,cssselector):
        deletecount = 0
        while True:
            last_content=self.move_to_lastpage()
            time.sleep(30)
            item = self.get_items()
            #画面外のオブジェクトをクリックしないように、スクロール移動
            delete_item = item[len(item)-1].find_element(By.CSS_SELECTOR,cssselector)
            self.driver.execute_script("arguments[0].scrollIntoView(false);", delete_item)
            delete_item.click()
            time.sleep(2)
            alert = self.driver.switch_to.alert
            alert.accept()
            time.sleep(random.uniform(4,7)) 
            deletecount+=1
            if(deletecount ==resellcount):
                break

def main_mercari():
    makeclass = Mercari()
    makeclass.open_window('https://jp.mercari.com/mypage/listings')
    makeclass.move_to_lastpage()
    item = makeclass.get_items()
    makeclass.resell(makeclass.get_items(),resellcount,'#clone-item')
    makeclass.item_delete('#item-delete')



def main_rakuma():
    makeclass=Rakuma()
    makeclass.open_window('https://fril.jp/sell')
    makeclass.move_to_lastpage()
    time.sleep(30)
    makeclass.resell(makeclass.get_items(),resellcount,'#clone-item')
    makeclass.open_window('https://fril.jp/sell')
    print("再出品終わり")
    makeclass.item_delete('#ga_click_delete')

main_mercari()
main_rakuma()
print("success")

