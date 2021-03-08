# SerialCommander
Send pre-defined commands over your serial (RS232) port to control devices like digital projectors, arduinos etc.

## How To Use
1. Download and install the `.deb` (recommended) or `.appimage` (for Linux), `.dmg` (for macOS) or `.exe` (for Windows) package from the [latest release](https://github.com/schorschii/SerialCommander/releases) on Github.
2. You can now start the GUI by executing the platform-specific executable. The `.deb` package installs a shortcut to the program in your start menu.
3. Load a config file (see `examples` directory). Please use a text editor to add or modify commands (the config is a simple `.json` format).

## Contributions
Please tell me if the example commands are working if you have an appropriate projector to test it. I would also be happy if you add some new examples.

| Projector | Successfully tested? |
| --------- | -------------------- |
| Acer      |                      |
| BenQ      | ✓                    |
| Epson     | ✓                    |
| Optoma    |                      |
| NEC       | ✓                    |
| Panasonic |                      |
| ViewSonic |                      |

## Projector RS232 Command Reference
- Acer:
  - https://global-download.acer.com/GDFiles/Document/User%20Manual/User%20Manual_Acer_1.0_A_A.zip?acerid=635303766533286084&Step1=PROJECTOR&Step2=P%20SERIES&Step3=P1283&OS=ALL&LC=en&BC=ACER&SC=PA_6
- BenQ:
  - https://benqimage.blob.core.windows.net/driver-us-file/RS232-commands_all%20Product%20Lines.pdf
- Epson:
  - ftp://download.epson-europe.com/pub/download/3211/epson321113eu.pdf
  - https://download.epson-europe.com/pub/download/3772/epson377222eu.XLSX
- Optoma:
  - https://www.optoma.de/uploads/RS232/DS309-RS232-en.pdf
- NEC:
  - https://www.sharpnecdisplays.eu/p/download/v/5e14a015e26cacae3ae64a422f7f8af4/cp/Products/Projectors/Shared/CommandLists/PDF-ExternalControlManual-english.pdf?fn=ExternalControlManual-english.pdf
- Panasonic:
  - https://na.panasonic.com/ns/9802_PT-RZ470RW430PT-FRZ370C__FRW330C.pdf
  - https://na.panasonic.com/ns/262931_vmz50_command_en_ja_cn.pdf
  - https://eww.pavc.panasonic.co.jp/projector/extranet/main/rs232c/D7KD3K_RS232C.pdf
- ViewSonic:
  - https://www.viewsonicglobal.com/public/products_download/97/Commercial_Displays_RS232.pdf?pass
