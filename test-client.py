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

def postAction(roomID, userID, action):
    data = urllib.urlencode({ 'user_id': userID, 'action': json.dumps(action) })
    result = urllib2.urlopen(url('/rooms/%s/submit' % roomID), data).read()
    return result

normpath = os.path.abspath

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
def new(roomID, userID, filepath):
    filepath = normpath(filepath)
    with open(filepath, 'r') as f:
        code = f.read()
    code_name = os.path.basename(filepath)
    code_id = hashlib.sha256(filepath).hexdigest()
    print postAction(roomID, userID, { 'user_id': userID, 'type': 'new', 'code_id': code_id, 'name': code_name, 'code': code })

@makeAction("delete")
def delete(roomID, userID, filepath):
    filepath = normpath(filepath)
    code_id = hashlib.sha256(filepath).hexdigest()
    print postAction(roomID, userID, { 'user_id': userID, 'type': 'delete', 'code_id': code_id })

@makeAction("add")
def add(roomID, userID, filepath):
    filepath = normpath(filepath)
    code_id = hashlib.sha256(filepath).hexdigest()
    print postAction(roomID, userID, { 'user_id': userID, 'type': 'add', 'code_id': code_id })

@makeAction("replace")
def replace(roomID, userID, filepath):
    filepath = normpath(filepath)
    code_id = hashlib.sha256(filepath).hexdigest()
    print postAction(roomID, userID, { 'user_id': userID, 'type': 'replace', 'code_id': code_id })

@makeAction("remove")
def remove(roomID, userID, filepath):
    filepath = normpath(filepath)
    code_id = hashlib.sha256(filepath).hexdigest()
    print postAction(roomID, userID, { 'user_id': userID, 'type': 'remove', 'code_id': code_id })

@makeAction("actions")
def actions(roomID, after=-1):
    if after >= 0: query = '?after=%i' % after
    else: query = ''
    result = urllib2.urlopen(url('/rooms/%s/actions%s' % (roomID, query))).read()
    print result

action = sys.argv[1]
args = sys.argv[2:]

ACTIONS[action](*args)
