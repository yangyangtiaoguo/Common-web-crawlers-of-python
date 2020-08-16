import requests
import os
from bs4 import BeautifulSoup
import re

# 初始地址
all_url = 'http://www.7160.com/rentiyishu/'
#保存路径
path = "D:/data_sex/7160/"
# 请求头
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 UBrowser/6.1.2107.204 Safari/537.36'
}

#################################开始请求（多列表）#################################
html = requests.get(all_url,headers = header)
start_html = html.text.encode('iso-8859-1').decode('gbk')  # 将gb2312转为UTF-8格式
#################################开始解析#################################
soup = BeautifulSoup(start_html,'lxml')
#查找最大页码
page = 255

# 同一路径
same_url = 'http://www.7160.com/rentiyishu/'

for n in range(1,int(page)+1):
    if n==8:#第八网页出错跳过
        continue
    print(all_url)
    ul = same_url + 'list_1_' + str(n) + '.html'
    print(ul)
    ####################开始请求（单列表多元素）###############
    html = requests.get(ul,headers = header)
    start_html = html.text.encode('iso-8859-1').decode('gbk')

    ########################开始解析##########################
    soup = BeautifulSoup(start_html,'lxml')
    if len(soup) < 2:#说明这个页面有问题，没有成为一个页面足够的数据
        print("第"+n+"页爆炸乐！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！")
        continue
    all_a = soup.find('div',class_ ='news_bom-left').find_all('a',target = '_blank')
    print(all_a)
    for a in all_a:
        title = a.get_text()
        if title != '':
            ########################创建目录##########################
            #win不能创建带？的目录
            if (os.path.exists(path + title.strip().replace('?', ''))):
                # print('目录已存在')
                flag = 1
            else:
                os.makedirs(path + title.strip().replace('?', ''))
                flag = 0
            os.chdir(path + title.strip().replace('?', ''))
            ######################### END ###########################

            ###################开始请求（单元素）###############
            print('准备爬取:' + title)
            hrefs = a['href']
            print(hrefs)
            in_url = 'http://www.7160.com'
            href = in_url + hrefs
            print("href=",href)
            htmls = requests.get(href,headers = header)
            html = htmls.text.encode('iso-8859-1').decode('gbk')
            #######################开始解析######################
            try:
                mess = BeautifulSoup(html,'lxml')
                titles = mess.find('h1').text
                print(titles)
            #print(mess.find('div',class_ = 'itempage').find_all('a'))
                pic_max = mess.find('div',class_ = 'itempage').find_all('a')[-2].text # 最大页数
            except:
                print("error,跳过")
                continue
            print(pic_max)
            if (flag == 1 and len(os.listdir(path + title.strip().replace('?', ''))) >= int(pic_max)):
                print(path + title.strip().replace('?', ''))
                print('已经保存完毕，跳过')
                continue
            for num in range(1,int(pic_max)+1):
                href = a['href']
                #print(href)
                hrefs = re.findall(r'.{18}',href)
                #print(hrefs)
                href = "".join(hrefs)
                #print(href)
                if num == 1:
                    #html = in_url + href + '.html'
                    html = in_url + href
                    #print("html="+html)
                else:
                    html = in_url + href + 'index_' + str(num) + ".html"
                    #print("html=" + html)

                ###################开始请求（单元素里的子元素）###############
                try:
                    htmls = requests.get(html,headers = header)
                    html = htmls.text.encode('iso-8859-1').decode('gbk')
                except:
                    print("error")
                    continue

                #######################开始解析######################
                mess = BeautifulSoup(html,'lxml')
                pic_url = mess.find('img',alt = titles)
                try:
                    print(pic_url['src'])
                except:
                    print(pic_url)
                    continue
                #########################开始下载#####################
                try:
                    html = requests.get(pic_url['src'],headers = header)
                    filename = pic_url['src'].split(r'/')[-1]
                except:
                    continue
                f = open(filename,'wb')
                f.write(html.content)
                f.close()
            print('完成')
    print('第',n,'页完成')