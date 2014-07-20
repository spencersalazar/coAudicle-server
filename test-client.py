#!/usr/bin/python

import sys, types, uuid, json, hashlib, os
import urllib, urllib2

SERVER='localhost'
PORT=8080
ACTIONS={}

def url(path):
    return 'http://%s:%d%s' % (SERVER, PORT, path)

def makeAction(name):
    def doit(fun):
        ACTIONS[name] = fun
    return doit

@makeAction("listrooms")
def listrooms():
    result = urllib2.urlopen(url('/rooms')).read()
    print result

@makeAction("showroom")
def showroom(roomID):
    result = urllib2.urlopen(url('/rooms/%s' % roomID)).read()
    print result

@makeAction("join")
def joinroom(roomID, userID, userName):
    data = urllib.urlencode({ 'user_id': userID, 'user_name': userName })
    result = urllib2.urlopen(url('/rooms/%s/join' % roomID), data).read()
    print result

@makeAction("leave")
def leaveroom(roomID, userID):
    data = urllib.urlencode({ 'user_id': userID })
    result = urllib2.urlopen(url('/rooms/%s/leave' % roomID), data).read()
    print result

@makeAction("join")
def joinroom(roomID, userID, userName):
    data = urllib.urlencode({ 'user_id': userID, 'user_name': userName })
    result = urllib2.urlopen(url('/rooms/%s/join' % roomID), data).read()
    print result

@makeAction("new")
def joinroom(userID, filepath):
    filepath = os.path.abspath(filepath)
    with open(filepath, 'r') as f:
        code = f.read()
    code_name = os.path.basename(code_name)
    code_id = hashlib.sha256(filepath).hexdigest()
    data = urllib.urlencode({ 'user_id': userID, 'user_name': userName })
    result = urllib2.urlopen(url('/rooms/%s/join' % roomID), data).read()
    print result

action = sys.argv[1]
args = sys.argv[2:]

ACTIONS[action](*args)
