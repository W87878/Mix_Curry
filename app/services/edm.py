from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
import codecs
import jinja2
import sys
import base64
import traceback
import dataset
import datetime
import time
import os
import random
import pymysql
pymysql.install_as_MySQLdb()
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import re

# 加载环境变量
load_dotenv()

# 紀錄程式執行狀況
logging.basicConfig(level=logging.INFO)

driver=None
SUPABASE_URL: str =  os.environ.get('SUPABASE_URL')
SUPABASE_KEY: str = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



if os.name == 'nt':
    rootdir='C:/Users/wangy/OneDrive/桌面/DataTeam/edm發信'
else:
    rootdir='/root/gmail_test'

sys.path.append(rootdir+'/gmaillib/')
from gmaillib.simplegmail import Gmail

#worker_no=random.randint(1,15)
worker_no=3


if len(sys.argv)>1:
    worker_no=int(sys.argv[1])
rootfolder=rootdir+'/edm/interview/'

if worker_no==1:
    current_me='choozmo2020@gmail.com'
    working_dir=rootdir+'/profiles/prof1'

if worker_no==2:
    current_me='choozmoservice@gmail.com'
    working_dir=rootdir+'/profiles/prof2'

if worker_no==3:
    current_me='steven@choozmo.com'
    working_dir=rootdir+'/profiles/prof3'

if worker_no==4:
    current_me='maltesers870223@gmail.com'
    working_dir=rootdir+'/profiles/prof4'

if worker_no==5:
    current_me='shuoxianw116@gmail.com'
    working_dir=rootdir+'/profiles/prof5'

if worker_no==6:
    current_me='b0930611685@gmail.com'
    working_dir=rootdir+'/profiles/prof6'

if worker_no==7:
    current_me='88wang23@gmail.com'
    working_dir=rootdir+'/profiles/prof7'

if worker_no==9998:
    current_me='verify@choozmo.com'
    working_dir=rootdir+'/profiles/verify'

if worker_no==9999:
    current_me='jared@choozmo.com'
    working_dir=rootdir+'/profiles/jared'


print(current_me)
campaign='20250206PROP' # 寄房地產 edm
prevent_dup=True

os.chdir(working_dir)

imgfolder=rootfolder+'images/'

# db = dataset.connect('postgresql://postgres:eyJhbGciOiJI@172.105.241.163:5432/postgres')

# 寄信
def send_msg(m_to,m_title,m_cid):
    global current_me
    global rootfolder
    global working_dir
    global campaign
    global table
    global imgfolder
    print('id:'+str(m_cid))
    msgRoot = MIMEMultipart('related')
    # msgRoot['Subject'] = '採訪邀約-'+m_title # 採訪邀約
    msgRoot['Subject'] = '致 '+m_title+'  房地產議題分析-算力傳媒&集仕多'
#    msgRoot['Subject'] = 'AI主播合作洽談-'+m_title + ' x 集仕多'

    msgRoot['From'] = current_me
    msgRoot['To'] = m_to
    display={}
    display['custname']=m_to
    display['client']=str(m_cid)
    display['email']=msgRoot['To']
    display['campaign']=campaign

    templateLoader = jinja2.FileSystemLoader(searchpath=rootfolder)
    templateEnv = jinja2.Environment(loader=templateLoader)
    # TEMPLATE_FILE = 'index.html'
    TEMPLATE_FILE = '限貸edm-v2.html'
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(display=display)
    content=outputText
    content=content.replace("<<<<TITLE>>>>",m_title)

    msgHtml = MIMEText(content, 'html')
    msgRoot.attach(msgHtml)
    msgRoot.add_header('reply-to', 'jared@choozmo.com')

    if TEMPLATE_FILE == 'index.html':
        image_paths=[imgfolder+'image-1.png',imgfolder+'image-2.png',imgfolder+'image-3.png',imgfolder+'image-4.png',imgfolder+'image-5.png',imgfolder+'image-6.png',imgfolder+'image-7.png',imgfolder+'image-8.png',imgfolder+'image-9.png']

        counter = 1
        for fp in image_paths:
            fp = open(fp, 'rb')
            msgImg = MIMEImage(fp.read(),'png')
            fp.close()
                # Define the image's ID as referenced above
            msgImg.add_header('Content-ID', '<image'+str(counter)+'>')
            msgImg.add_header('Content-Disposition', 'inline', filename=str(counter))
            msgRoot.attach(msgImg)
            counter += 1
        
    
    try:
        gmail = Gmail() # will open a browser window to ask you to log in and authenticate
        raw={"raw": base64.urlsafe_b64encode(msgRoot.as_string().encode()).decode()}
        gmail.send_raw(raw)
        print('Gmail send succesly.')
    except Exception as e:
        print(f'Error: {e}')
        return

    db3 = dataset.connect('mysql://choozmo:pAssw0rd@db.ptt.cx:3306/seo?charset=utf8mb4')
    table=db3['email_processed']
    try:
        table.insert({'email':m_to})
    except Exception as e:
        print(f'Error: {e}')
        return 



    try:
        table.insert({'email':m_to,'title':m_title,'client_id':str(m_cid),'campaign':campaign,'dt':datetime.datetime.now()})
        
        # 檢查 email 是否存在
        response = supabase.table('emaillog').select('email').eq('email', m_to).eq('campaign', campaign).execute()
        if response.data:
            return
        supabase.table('emaillog').insert({'email':m_to,'title':m_title,'client_id':str(m_cid),'campaign':campaign,'dt':str(datetime.datetime.now())}).execute()
        print('emaillog insert successly!')
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()


# 針對房地產行業
def get_list():
    # global db
    global prevent_dup
    final_list=[]
    table = 'emaillog'
    cursor = supabase.table(table).select('email').eq('campaign', campaign).execute()
    sent_list={}
    for c in cursor.data:
        sent_list[c['email'].strip()]=1
    print(sent_list)
    table2 = 'edm_blacklist'
    cursor2 = supabase.table(table2).select('email').execute()
    for c2 in cursor2.data:
        sent_list[c2['email'].strip()]=1
    print(sent_list)
    table3 = 'edm_industry_tag' # 不動產, 房地產, 房仲, 房產, 仲介, 房屋
    industry_tags = ['不動產', '房地產', '房仲', '房產', '仲介', '房屋']
    cursor_lst = []
    # 為每個 tag 使用 filter 組建條件
    for tag in industry_tags:
        cursor3 = supabase.table(table3).select('id,email,title').ilike('industry_tag', f"%{tag}%").order('id', desc=False).execute()
        for c3 in cursor3.data:
            if '人力仲介' in c3['title']:
                continue
            cursor_lst.append(c3)

    for c4 in cursor_lst:
        email=c4['email'].strip()
        if prevent_dup:
            if sent_list.get(email) is not None:
                continue
            else:
                sent_list[c4['email'].strip()]=1
                final_list.append(c4)

    print('count: '+str( len(final_list) ))
    return final_list


# 測試用
# sendlist="""
# jared,jared@choozmo.com,1
# 巴巴,steven@choozmo.com,2
# """
# final_list=[]
# for l in sendlist.split('\n'):
#     elmts=l.split(",")
#     if len(elmts) <=2:
#         continue
#     final_list.append({'title':elmts[0],'email':elmts[1],'id':1})
# #    print(elmts[1])
# print(final_list)


final_list=get_list()

for f in final_list:
    print(f['email'], end='\t')
    print(f['title'])
    try:
        send_msg(m_to=f['email'],m_title=f['title'],m_cid=f['id'])
        time.sleep(500)
    except:
        traceback.print_exc()
    print('sent')
