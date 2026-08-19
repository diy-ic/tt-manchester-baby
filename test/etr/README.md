`mpremote mount .`
from within `/remote` you can do: `import test; test.main()` to run the test

to move to `/`:
`>>> import os; os.chdir("/")`

to edit files directly onboard:
`pip install rshell`

`rshell -e nano`

`edit /config.ini` -- don't edit `/pyboard/config.ini` (not sure if it's the correct file)

---

changes to config.ini:
- set default project to `tt_um_krisjdev_manchester_baby`
- added `clock_frequency = 0`
- aded own section for `tt_um_krisjdev_manchester_baby`