import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import itertools

# settings
DriverPath = "./chromedriver"
Jsonf = "cost-367613-bc44eae614f5.json"
SpreadSheetKey = "1Wcx_-jWGREn2PXhOkK0XyAP76kqkauPABWQxHxyNzjc"
EditSheetName = '商品到着後単価確定表'
RakumartUserName = '09042464159'
RakumartPassword = '122300ab'
# 代行手数料
Commission = 4.8
# 振込手数料
furikomiComission = 52
AwaitTime = 1
#国際送料の書かれたシートID
PordID = "2023072619564952-25632"
#注文書のシートID,array形式
OrderIDs = ["E20230528083533-25632"]


def main():
    # updateSpreadSheetTest()
    driver = initLogin()

    driverToPord(driver)
    time.sleep(AwaitTime)
    # こっちのページにいる間に必要な情報は取っておく
    d = float(getFromID(driver, "shiji"))
    d += getBurden()
    writeList = getWriteList(driver)
    # 下のリストのやつの更新
    updateSpreadSheet(writeList)
    # 上の値段のやつの計算と更新
    updatePriceSpreadSheet(driver, d)
    driver.quit()


def initLogin():
    service = Service(executable_path=DriverPath)
    driver = webdriver.Chrome(service=service)
    driver.get('https://www.rakumart.com/index.php?mod=user&act=login')

    username_element = driver.find_element(By.ID, "username")
    username_element.send_keys(RakumartUserName)
    userpass_element = driver.find_element(By.ID, 'password')
    userpass_element.send_keys(RakumartPassword)
    userremember_element = driver.find_element(By.ID, "remember")
    userremember_element.click()
    usersubmit_element = driver.find_element(By.NAME, "sub")
    usersubmit_element.click()
    time.sleep(3)
    return driver


def getWriteList(driver):
    pricelist = getpricelist(driver)
    sendlist = getsendlist(driver)
    return connectArray(pricelist, sendlist)


def updateSpreadSheetTest():
    updateSpreadSheet([1, 2, 3, 4])


def driverToOrd(driver, ordID):
    driver.get(
        'https://www.rakumart.com/index.php?mod=user&act=user_tradelist_1&ordno='+str(ordID))


def driverToPord(driver):
    driver.get(
        'https://www.rakumart.com/index.php?mod=user&act=p_tradelist&pordno=P'+str(PordID))


def getCommission(val):
    # 手数料の入った値段から手数料を計算
    # val値段, xが手数料前の値段
    # val = x * (100+com)/100, 求めるのはval-x
    # x = 100/(100+com)*val
    x = val * (100 / (100.0+Commission))
    return val - x


def getArriveList(driver):
    return getListFromClass(driver, "tocyaku")


def getOrderList(driver):
    return getListFromClass(driver, "txt")


def getPriceGenList(driver):
    return getListFromClass(driver, "price1")


def getShippingCost(driver):
    return getFromID(driver, "d")


def getCostAndRate(driver):
    # (元,円,円/元 換算レート)取得
    gen = getFromID(driver, "g")
    yen = getFromID(driver, "h")
    return gen, yen, yen / gen


def getTrueCost(gen, driver):
    # 到着した奴だけ考慮したトータルの値段
    order = getOrderList(driver)
    arrive = getArriveList(driver)
    price = getPriceGenList(driver)
    if len(arrive) != len(price):
        raise ValueError("get True Cost len is not same arrive price")
    if len(arrive) != len(order):
        raise ValueError("get True Cost len is not same arrive order")
    for i in range(len(arrive)):
        val = (order[i] - arrive[i]) * price[i]
        val += val * (Commission / 100.0)
        gen -= val
    return gen


def getListFromClass(driver, name):
    # list取得の共通(数値型限定)
    res = []
    class_elements = driver.find_elements(By.CLASS_NAME, name)
    for elem in class_elements:
        res.append(float(elem.text))
    return res


def getFromID(driver, id):
    # id取得の共通(数値型限定)
    return float(driver.find_element(By.ID, id).text)


def getpricelist(driver):
    # 中国→日本へ送った商品の単価
    class_elements = driver.find_elements(By.CLASS_NAME, "tr")
    returnlist = []
    for elem in range(len(class_elements)):
        td_elements = class_elements[elem].find_elements(By.TAG_NAME, "td")
        returnlist.append(float(td_elements[9].text))
    # print(type(returnlist))
    # print(returnlist)
    return returnlist


def getsendlist(driver):
    # 中国→日本へ送った商品の個数(出荷数)
    class_elements = driver.find_elements(
        By.CSS_SELECTOR, ".fasongfasong.comf")
    returnlist = []
    # print(type(class_elements))
    for elem in range(len(class_elements)):
        readable_elements = class_elements[elem].text
        returnlist.append(int(readable_elements))
    # print(type(returnlist))
    # print(returnlist)
    return returnlist

# spread sheet系


def getBurden():
    # 関税消費税+通関手数料+振込手数料
    ws = connect_gspread(Jsonf, SpreadSheetKey)
    cellList = ws.range('H1:H4')
    res = 0.0
    for i in range(len(cellList)):
        res += float(cellList[i].value)
    return res


def updateSpreadSheet(writeList):
    if len(writeList) == 0:
        return
    ws = connect_gspread(Jsonf, SpreadSheetKey)
    low = 8
    row = 2  # [A,B]なら2, [A,C]なら3みたいにする
    hi = low + len(writeList) // row - 1   # (ws.rangeは閉区間)
    cellList = ws.range('A'+str(low)+':B'+str(hi))
    for i in range(len(cellList)):
        cellList[i].value = writeList[i]
    ws.update_cells(cellList)


def updatePriceSpreadSheet(driver, d):
    # orderのURLのやつ全網羅してspread sheet更新
    updlist = [0, 0, 0, d]
    for i in range(len(OrderIDs)):
        # URL変更
        driverToOrd(driver, OrderIDs[i])
        time.sleep(AwaitTime)
        # _gen,_yenは仮値段
        _gen, _yen, rate = getCostAndRate(driver)
        gen = getTrueCost(_gen, driver)
        yen = gen * rate
        a, b = yen + furikomiComission, gen
        print("debug orderID", OrderIDs[i])
        print("debug _gen _yen rate gen yen",
              _gen, _yen, rate, gen, yen)
        c = getShippingCost(driver) + getCommission(gen)
        arr = [a, b, c]
        print("debug a, b, c", arr)
        for i in range(len(arr)):
            updlist[i] += arr[i]
    ws = connect_gspread(Jsonf, SpreadSheetKey)
    cellList = ws.range('A3:D3')
    for i in range(len(cellList)):
        cellList[i].value = updlist[i]
    ws.update_cells(cellList)


def connect_gspread(jsonf, key):
    # Google Spread Sheetにアクセス
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        jsonf, scope)
    gc = gspread.authorize(credentials)
    SPREADSHEET_KEY = key
    worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(EditSheetName)
    return worksheet


# A,B -> A1,B1,A2,B2の結合
def connectArray(li, li2):
    if len(li) != len(li2):
        raise ValueError("connectArray len is not same")
    return [y for x in zip(li, li2) for y in x]


if __name__ == "__main__":
    main()
