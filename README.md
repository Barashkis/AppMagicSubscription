# Project description
Repository contains files of AppMagicSubscription

This is one of my freelance projects. With this tool (Telegram bot) you can 
download .csv file with all information about apps on URL. One thing you must do is 
to pass URL with apps that you want to extract

**Important**: if you want to parse, for example, 1000 apps, a process will run about 
4-5 hours because AppMagic API is very sensible to requests. So this tool doesn't use 
any API and that's why speed isn't good. But it's only one way to pass through AppMagic 
security

This project uses Python libraries (version 3.8) such as:
+ selenium (104 version of Chrome, the project includes chromedriver with this version)
+ selenium-wire
+ aiogram
+ requests
+ undetected_chromedriver
+ bs4
+ etc

# Demonstration
![Alt Text](assets/demonstartion_1.png)
![Alt Text](assets/demonstration_2.PNG)
