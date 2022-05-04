# invoke-msvc-in-org-mode
Call the cl compiler in MSVC from org mode's babel in Emacs.

## Installation
Clone this repo to "your favourite bin directory".  Then, customize org-babel in Emacs:

```bash
    >M-x customize-variable
     org-babel-C++-compiler
```

Set the value to the Python call:

```bash
    python "your favourite bin directory"/invoke-msvc-in-org-mode/main.py
```

## Example
After installation, try the example org file.  Place the cursor in the middle of the C++
source code and press Ctrl-C Ctrl-C.  The results should be successfully placed under the
source code.

## Customizations
Compiler and linker options are read from the json files.  To customize your installation,
add or remove options to these json files.