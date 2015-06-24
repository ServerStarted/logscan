#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
监控日志文件，匹配到给定的正则，发邮件报警
'''

import datetime
import subprocess
import smtplib  
from email.mime.text import MIMEText  
from email.header import Header
import inspect
import os
import json
import time, os, sched 

inc = 300   # 定时扫描log 的时间周期

smtp = smtplib.SMTP()

# get hostname
hostname = os.popen("hostname").read().strip().strip('\n')

def load_setting():
    # get the directory path of this script
    this_file = inspect.stack()[0][1]
    path = os.path.abspath(os.path.dirname(this_file))
    file = open(path+"/setting.json", 'r')
    
    setting_str = ""
    for line in file:
        str = line.strip(' ').strip('\n')
        setting_str += str
    
    obj = json.loads(setting_str)
    
    # validate setting
    
    return obj

def login_smtp(sender_mail):
    global smtp
    if sender_mail.has_key('port') and sender_mail["port"] > 0:
        smtp.connect(sender_mail['host'], sender_mail["port"])
    else:
        smtp.connect( sender_mail['host'])
    smtp.login(sender_mail['username'], sender_mail['password'])
    
    return smtp

def send_mail(subject, content, sender, mail_receivers):    
    global smtp
    # 包含ip
    subject = hostname + '-' + subject
    print 'send mail, subject: ', subject
    msg = MIMEText(content, _charset='utf-8')   
    msg['Subject'] = Header(subject, 'utf-8')  
    msg['From'] = sender
    msg['To'] = ";".join(mail_receivers) 
      
    smtp.sendmail(sender, mail_receivers, msg.as_string())
    
def quit_smtp():
    global smtp
    smtp.quit()

def scan_file(log, sender_mail):
    # get interval
    interval = 5
    if log.has_key('interval'):
        interval = log['interval']
    
    # get time
    end_date_time = datetime.datetime.now() - datetime.timedelta(seconds = 1)
    start_date_time = datetime.datetime.now() - datetime.timedelta(minutes = interval)
        
    start_hour = start_date_time.hour
    start_min = start_date_time.minute
    start_second = 0
    
    end_hour = end_date_time.hour
    end_min = end_date_time.minute
    end_second = 59
    
    # count all request
    start_time = str(start_hour) + ":" + str(start_min) + ":" + str(start_second)
    end_time = str(end_hour) + ":" + str(end_min) + ":" + str(end_second)
    # for test
    #start_time = '13:15:00'
    #end_time = '13:20:00'
    
    print '# start: ' + start_time + ' end: ' + end_time
    
    log_file = log['file']
    regxs = log['regxs']
    receiver_mails = log['receiver_mails']
    interval_str = str(interval)+'m'
    
    # scan log file
    for regx in regxs:
        logscan_cmd = ['/usr/bin/logscan', log_file, '-c', "%Y-%m-%d %H:%M:%S", '-t', start_time, '-p', interval_str]
        grep_cmd = ['grep', regx]
        print '# logscan_cmd: ', logscan_cmd
        print '# grep_cmd: ', grep_cmd
        
        logscan_p = subprocess.Popen(logscan_cmd, stdout=subprocess.PIPE)
        grep_p = subprocess.Popen(grep_cmd, stdin=logscan_p.stdout, stdout=subprocess.PIPE)
    
        out = ''
        try:
            out = grep_p.stdout.read()
        except:
            print "grep stdout read error:"
            continue
    
        if not out is None and len(out) > 0:
            send_mail(log_file + '-' + regx, out, sender_mail['username'], receiver_mails)

def do_monitor():
    # 循环调用   
    schedule.enter(inc, 0, do_monitor, ())

    #  初始化
    print '-------------------- logscan start --------------------'
    # 加载配置
    setting = load_setting()
    sender_mail = setting["sender_mail"]
    login_smtp(sender_mail)
    
    # 扫描文件
    logs = setting['logs']
    for log in logs:
        scan_file(log, sender_mail)
        
    quit_smtp()
    print '-------------------- logscan end --------------------'
    print ''
    
if __name__ == "__main__":


    # 定时执行monitor
    schedule = sched.scheduler(time.time, time.sleep) 
    
    schedule.enter(0, 0, do_monitor, ())
    schedule.run() 
    