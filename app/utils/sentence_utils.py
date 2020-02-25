# -*- coding: utf-8 -*-

import re as regex


def is_user_story(txt):
    """ checks whether given sentence confirms to user-story template"""
    x = regex.findall("^As [an|a]", txt)
    y = regex.findall(", [Ii] want to", txt)
    if x and y:
        return True
    else:
        return False