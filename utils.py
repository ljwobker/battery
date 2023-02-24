#!/usr/bin/python

import logging
import sys

def getBasicLogger(name: str) -> logging.Logger :
    logging.basicConfig(level=logging.DEBUG, 
                        style='{', 
                        # datefmt='%Y-%m-%d %H:%M:%S', 
                        datefmt='%H:%M:%S', 
                        # format='{asctime} {levelname} {filename}:{lineno}: {message}',
                        format='{asctime} {levelname} ln {lineno:>4}:: {message}',
                        )
    return logging.getLogger(name)
