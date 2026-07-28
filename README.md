## Problem statement/Task description:
To work with PDFs more quickly and efficiently, we need to colour them green following a specific procedure. 
To do this, all predefined network names must be identified and highlighted in green. The whole thing is to be
 implemented using a Python script with a small Graphical User Interface (GUI).
## Procedure/How to use the GUI:
A list (e.g. a text file) of all networks is to be imported, the PDF to be edited as well. 
These networks are then to be identified in the PDF to be edited and highlighted in green.
The result is then to be exported as a new PDF file.
*Note*: It is important to note that only complete network names may be selected, not just parts of them!

## Extra task:
As an extra feature, you could also let users choose which colour to apply to the whole thing. In addition, test point numbers can also be imported via
the text file and added to the respective network.


## Note to self:
- add a requirements.txt, LICENSE

## Commands
init:
    pip install -r requirements.txt

test:
    py.test tests