REM creates an .exe file in dist directory along with _internal file containing dependencies
pyinstaller --noconfirm --log-level=WARN ^
    --name=dicechase ^
    --add-data="dice.kv:." ^
    --add-data="audio:audio" ^
    --add-data="img\Alea_*:img" ^
    --add-data="img\cog_30.png:img" ^
    --add-data="img\dice_chase.ico:img" ^
    --collect-binaries=kivy_deps.sdl2 ^
    --collect-binaries=kivy_deps.glew ^
    --icon=img\dice_chase.ico ^
    --windowed ^
    main.py