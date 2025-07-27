# ReqBot
Automatic requirements gathering tool from PDF Specifications files.
This Tool automatically extracts requirements from PDF files, assuming that those requirements are well-written 
using standard keywords (even if it is possible to customize the keyword dictionary)
NOTE: it is required Python 3.8 for issues related to PyQt5 LIB and also and Microsoft Build Tools 2022
then you can install a model LLM library with command line in the venv by:

pip install spacy==3.4.4 #version of spacy compatible with Python 3.8

python -m spacy download en_core_web_sm

This is because en_core_web_sm is not a standard pip-installable Python package. 
It's a pre-trained language model for spaCy, and spaCy models are installed using a 
different command, typically via spacy download.

It is another version of App GUI that is RequirementBotApp.py

