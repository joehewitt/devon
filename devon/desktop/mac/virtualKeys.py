
from AppKit import *
from Carbon.Events import cmdKey, controlKey, shiftKey, optionKey

# Why Apple doesn't include this in their API I don't know - I found them here:
#   http://boredzo.org/blog/wp-content/uploads/2007/05/imtx-virtual-keycodes.png

virtualKeyCodes = {
    "esc": 53,
    ""
    "a": 0,
    "s": 1,
    "d": 2,
    "f": 3,
    "h": 4,
    "g": 5,
    "z": 6,
    "x": 7,
    "c": 8,
    "v": 9,
    "b": 11,
    "q": 12,
    "w": 13,
    "e": 14,
    "r": 15,
    "y": 16,
    "t": 17,
    "1": 18,
    "2": 19,
    "3": 20,
    "4": 21,
    "6": 22,
    "5": 23,
    "=": 24,
    "9": 25,
    "7": 26,
    "-": 27,
    "_": 27,
    "8": 28,
    "0": 29,
    "]": 30,
    "}": 30,
    "o": 31,
    "u": 32,
    "[": 33,
    "{": 33,
    "i": 34,
    "p": 35,
    "\n": 36,
    "l": 37,
    "j": 38,
    "'": 39,
    "\"": 39,
    "k": 40,
    ";": 41,
    ":": 41,
    "\\": 42,
    "|": 42,
    ",": 43,
    "<": 43,
    "/": 44,
    "n": 45,
    "m": 46,
    ".": 47,
    ">": 47,
    "\t": 48,
    " ": 49,
    "`": 50,
    "~": 50,
    "backspace": 51,
    "esc": 53,
    "command": 55,
    "shift": 56,
    "capslock": 57,
    "option": 58,
    "control": 59,
    "fN": 63,
    "f5": 96,
    "f6": 97,
    "f7": 98,
    "f3": 99,
    "f8": 100,
    "f9": 101,
    "f11": 103,
    "f13": 105,
    "f14": 107,
    "f10": 109,
    "f12": 111,
    "f15": 113,
    "help": 114,
    "home": 115,
    "pgup": 116,
    "del": 117,
    "f4": 118,
    "end": 119,
    "f2": 120,
    "pgdn": 121,
    "f1": 122,
    "left": 123,
    "right": 124,
    "down": 125,
    "up": 126
}

def hotKeyToVirtualCodes(name):
    flags = 0
    parts = name.split("+")
    for part in parts[0:-1]:
        if part == "cmd":
            flags |= cmdKey
        elif part == "ctrl":
            flags |= controlKey
        elif part == "shift":
            flags |= shiftKey
        elif part == "opt" or part == "alt":
            flags |= optionKey
    
    code = virtualKeyCodes[parts[-1].lower()]
    return code, flags

def hotKeyToPrettyName(name):
    flags = 0
    parts = name.split("+")
    for part in parts[0:-1]:
        if part == "cmd":
            flags |= NSCommandKeyMask
        elif part == "ctrl":
            flags |= NSControlKeyMask
        elif part == "shift":
            flags |= NSShiftKeyMask
        elif part == "opt" or part == "alt":
            flags |= NSOptionKeyMask
    
    char = parts[-1].upper()
    return char, flags
