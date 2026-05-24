"""
Done!
"""

from configparser import ConfigParser
import os
from dotenv import load_dotenv

load_dotenv()

def config(filename='info.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')

    return db

def load_config():
    db_config = config()
    return db_config
