import requests
import re
from mysql import cursor,connect
from bs4 import BeautifulSoup
from selenium import webdriver
from ipproxy import get_profile,get_ip_list,get_random_ip
from time import sleep
import datetime
import time

def incre_cmt(hotel_id,done_list):
    starttime = datetime.datetime.now()
    # profile = get_profile()
    driver = webdriver.Firefox()
    time_mark = 1
    i=1
    for id, s in hotel_id:
        if id not in done_list:
            sql_comments = "insert into dzdp_hotel_comments VALUES"
            url = "http://www.dianping.com/shop/" + id
            nowtime = datetime.datetime.now()
            timeminus = ((nowtime - starttime).seconds) / 60
            if (timeminus > 5 * time_mark):
                profile = get_profile()
                driver = webdriver.Firefox(profile)
                time_mark = time_mark + 1
            flag = True
            while flag:
                url_comment = url + '/review_more_latest?pageno=' + str(i)
                print(url_comment)
                try:
                    driver.get(url_comment)
                except Exception:
                    driver.execute_script("window.stop()")
                comment_soup = BeautifulSoup(driver.page_source, 'lxml')
                print(comment_soup)
                try:
                    comment_list = comment_soup.find('div', {'class': 'comment-list'})
                    contents = comment_list.find_all('div', {'class': 'content'})
                except Exception:
                    # driver.close()
                    break
                pattern = re.compile('[\r\n]+')
                for content in contents:
                    content_text = content.find('div', {'class': 'J_brief-cont'}).text.replace(' ', '')
                    comment_clean = pattern.sub('', content_text).replace('\'', '').replace('\\', '')
                    comment_id = content.find('div', {'class': 'misc-info'})['id'].split('_')[1]
                    day = content.find('span', {'class': 'time'}).text.split('  ')[0]
                    if len(day) < 7:
                        day = '2017-' + day
                    sql_comments = sql_comments + "('%s','%s','%s','%s')," % (id, comment_id, day, comment_clean)
                    print(sql_comments)
                i=i+1

def get_hotel_comment(hotel_id,done_list):
    starttime = datetime.datetime.now()
    profile = get_profile()
    time_mark = 1
    for id,s in hotel_id:
      if id not in done_list:
        sql_details = "insert into dzdp_hotel_details VALUES "
        sql_comments = "insert into dzdp_hotel_comments VALUES"
        url = "http://www.dianping.com/shop/"+id
        nowtime = datetime.datetime.now()
        timeminus = ((nowtime - starttime).seconds) / 60
        if (timeminus > 5 * time_mark):
            profile = get_profile()
            time_mark = time_mark +1
        driver = webdriver.Firefox(profile)
        driver.set_page_load_timeout(6)
        try:
            driver.get(url)
        except Exception:
            driver.execute_script("window.stop()")
        soup = BeautifulSoup(driver.page_source,'lxml')
        try:
            level = soup.find('div',{'class':'crumb'}).find_all('a')[2].text
        except Exception:
            level = soup.find('div', {'class': 'crumb'}).find_all('a')[1].text
        hotel_name = soup.find('div',{'class':'hotel-title clearfix'}).find('h1').text
        addr = soup.find('span',{'class':'hotel-address'}).text
        jw_patt = re.compile('"lat":([0-9]+).([0-9]+),"lng":([0-9]+).([0-9]+),')
        jw = jw_patt.findall(driver.page_source)[0]
        weidu = jw[0]+'.'+jw[1]
        jingdu = jw[2]+'.'+jw[3]
        sql_details =sql_details + "('%s','%s','%s','%s','%s','%s','%s')" % (id,s,hotel_name,level,addr,jingdu,weidu)
        i=1
        while True:
                url_comment = url + '/review_more_latest?pageno='+str(i)
                try:
                    driver.get(url_comment)
                except Exception:
                    driver.execute_script("window.stop()")
                comment_soup = BeautifulSoup(driver.page_source, 'lxml')
                if i ==1:
                    try:
                        pagenum = comment_soup.find_all('div', {'class': 'Pages'})[1].find_all('a')[-2].text
                        print(pagenum)
                    except Exception:
                        pagenum='1'
                try:
                    comment_list = comment_soup.find('div', {'class': 'comment-list'})
                    contents = comment_list.find_all('div', {'class': 'content'})
                except Exception:
                    dianping_pattr = re.compile('网友点评</a><em class="col-exp">\(([0-9]+)\)</em>')
                    zero_comment = dianping_pattr.findall(driver.page_source)
                    if zero_comment[0] == '0':
                        cursor.execute(sql_details)
                        sql_comments= sql_comments +"('%s','%s','%s','%s')" % (id,'',time.strftime('%Y-%m-%d',time.localtime(time.time())),'no comment')
                        cursor.execute(sql_comments)
                        connect.commit()
                        print('insert no comment')
                    driver.close()
                    break
                pattern = re.compile('[\r\n]+')
                for content in contents:
                    content_text = content.find('div',{'class':'J_brief-cont'}).text.replace(' ','')
                    comment_clean = pattern.sub('', content_text).replace('\'','').replace('\\','')
                    comment_id = content.find('div',{'class':'misc-info'})['id'].split('_')[1]
                    day = content.find('span',{'class':'time'}).text.split('  ')[0]
                    if len(day)<7:
                        day = '2017-'+day
                    sql_comments = sql_comments + "('%s','%s','%s','%s')," % (id,comment_id,day,comment_clean)
                if str(i)==pagenum:
                    cursor.execute(sql_comments[:-1])
                    cursor.execute(sql_details)
                    connect.commit()
                    print(sql_details)
                    driver.close()
                    break
                i = i + 1





def get_hotel_id():
    shi = ['chaozhou', 'shenzhen', 'guangzhou', 'dongguan', 'foshan', 'zhongshan', 'zhuhai', 'shantou', 'qingyuan',
           'heyuan',
           'zhaoqing', 'yunfu', 'shaoguan'
        , 'meizhou', 'jiangmen', 'maoming', 'yangjiang', 'zhanjiang', 'huizhou', 'shanwei', 'jieyang']
    pattern_yema = 'data-ga-page="([0-9]+)"'
    yema_pattern = re.compile(pattern_yema)
    pattern_hotel_id = 'data-shop-url="([0-9]+)"'
    hotel_id_pattern = re.compile(pattern_hotel_id)
    for s in shi:
        sql = "insert into dzdp_hotel_id(dzdp_hotel_id,shi) VALUES "
        url_shouye = "https://www.dianping.com/" + s + "/hotel/"
        html = requests.get(url_shouye)
        yema = yema_pattern.findall(html.text)[-2]
        for i in range(1, int(yema) + 1):
            print(i)
            url_yema = url_shouye + "p" + str(i)
            html_id = requests.get(url_yema)
            hotel_id = hotel_id_pattern.findall(html_id.text)
            for id in set(hotel_id):
                sql = sql + "('" + id + "','" + s + "')" + ","
        sql = sql[:-1]
        cursor.execute(sql)
        connect.commit()
        print('成功插入', cursor.rowcount, '条数据')

if __name__ == '__main__':
    # sql1 = 'select distinct(hotel_name),shi from dzdp_hotel_id'
    # sql2 = 'select distinct(hotel_id) from dzdp_hotel_details'
    # cursor.execute(sql1)
    # list1 = []
    # for row in cursor.fetchall():
    #     list1.append(list(row))
    # cursor.execute(sql2)
    # list2 = []
    # for row in cursor.fetchall():
    #     list2.append(row[0])
    # list1 = [['58127153','foshan']]
    # get_hotel_comment(list1,[])
    incre_cmt([['58127153','foshan']],[])



