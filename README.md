
![](img/dice_chase_1024_500.png)

# About

This fun little game was developed using [Kivy](https://kivy.org/), an open source cross-platform App development framework in the Python programming language.

Click on the dice to increase your score by the value shown. More dice will appear over time - increasing the fun - but also the chaos! Can you beat the high score?

High scores are saved locally, so you can close the application and come back later to try and beat your high score. 

The background music credits go to me - I hope you enjoy it!

# How to run the Kivy app in a Python environment

Clone the repo, optionally create a virtual environment, and ensure you have the Kivy package installed alongside Python. Then run in a terminal using `python main.py`

# I don't have time for Python, I have to play now!

For users on Windows (x64) you can download [build.zip](build.zip) which contains a packaged exe file with the dependencies in a folder.

# Packaging for Windows, macOS or Linux

If you want to package it yourself (or you're not using Windows), you can use [PyInstaller](https://pyinstaller.org/en/stable/index.html) to bundle a Python application and its dependencies into a single package. This can be done on Windows, macOS and Linux, but must be done on the same type of platform you plan to run it on.

You can run [build.bat](build.bat) if you're using Windows. I've also created (but not yet tested) [build.sh](build.sh) for Linux/macOS users. These call pyinstaller which will create a build working folder and .spec file along with a dist folder which contains the dicechase.exe file as well as dependencies in the _internal folder.

# Packaging as an Android or iPad App

It's possible - I managed to do it using [Buildozer](https://buildozer.readthedocs.io/en/latest/) - but it's non-trivial, particularly for the iPad. Even if you get it working in developer mode, there's more hoops to actually get it into a store. At some point I might do a blog post about it, but for now, if you don't already know how to do this just know that it might be a bit of a journey. 
