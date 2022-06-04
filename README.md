# Building

Must have [pyinstaller](https://pyinstaller.org/en/stable/index.html) installed to build.

```bash
pip install pyinstaller
```

## Generate spec file

A clean spec file is already present as `Idle Breakout.spec`. Alternativley, use the below commands to generate a new one.

### MacOS

```bash
pyi-makespec --onefile --windowed --add-data "images:./images" --name "Idle Breakout" --icon "icon.icns" main.py
```

### Windows (Untested)

```bash
pyi-makespec --onefile --windowed --add-data "images;./images" --name "Idle Breakout" --icon "icon.icns" main.py
```

## Build app

```bash
pyinstaller --noconfirm Idle\ Breakout.spec
```
