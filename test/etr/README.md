`mpremote mount .`
from within `/remote` you can do: `import test; test.main()` to run the test

to move to `/`:
`>>> import os; os.chdir("/")`

to edit files directly onboard:
`pip install rshell`

`rshell -e nano`

`edit /pyboard/config.ini`