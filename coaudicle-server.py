
from twisted.web import server, resource
from twisted.internet import reactor, defer
from twisted.python import log
from twisted.web.server import NOT_DONE_YET

import types, uuid, json, cgi, datetime
import ago # pip install ago

class Site(server.Site):
    def getResourceFor(self, request):
        request.setHeader('Content-Type', 'application/json')
        return server.Site.getResourceFor(self, request)

# shorthand convenience method
bind = types.MethodType

def bindPOST(parent, path):
    def doit(f):
        r = resource.Resource()
        r.render_POST = bind(f, parent)
        parent.putChild(path, r)
    return doit

def bindGET(parent, path):
    def doit(f):
        r = resource.Resource()
        r.render_GET = bind(f, parent)
        parent.putChild(path, r)
    return doit

def validateAction(action):
    return True

def sanitizeAction(action):
    return action

class Room(resource.Resource):
    isLeaf = False
    
    def __init__(self, name, uuid=None):
        resource.Resource.__init__(self)
        
        self._start = datetime.datetime.today()
        self._members = []
        self._name = name
        if uuid == None:
            uuid = uuid.uuid4().hex
        self._uuid = uuid
        self._actions = []
        self._defers = []
        
        # join action
        @bindPOST(self, 'join')
        def join_POST(self, request):
            user_id = request.args['user_id'][0]
            name = request.args['user_name'][0]
            if not self.isMember(user_id):
                self._members.append({ 'user_name': name, 'user_id': user_id })
                self.postAction({ 'user_id': user_id, 'type': 'join', 'user_name': name })
            return json.dumps({'status': 200, 'msg': 'OK'})
        
        # leave action
        @bindPOST(self, 'leave')
        def leave_POST(self, request):
            user_id = request.args['user_id'][0]
            for member in self._members:
                if member['user_id'] == user_id:
                    self._members.remove(member)
                    self.postAction({ 'user_id': user_id, 'type': 'leave' })
            return json.dumps({'status': 200, 'msg': 'OK'})
                
        # submit action
        @bindPOST(self, 'submit')
        def submit_POST(self, request):
            user_id = request.args['user_id'][0]
            action = json.loads(request.args['action'][0])
            
            if not self.isMember(user_id):
                request.setResponseCode(401)
                return json.dumps({'status': 401, 'msg': 'Unauthorized'})
            
            if not validateAction(action):
                request.setResponseCode(400)
                return json.dumps({'status': 400, 'msg': 'Bad request'})
            
            action = sanitizeAction(action)
            
            action['user_id'] = user_id
            self.postAction(action)
            
            return json.dumps({'status': 200, 'msg': 'OK'})
        
        # retrieve action(s)
        @bindGET(self, 'actions')
        def actions_GET(self, request):            
            if 'after' in request.args:
                after = int(request.args['after'][0])
                if after+1 < len(self._actions):
                    return self.renderActions(request, after)
                else:
                    d = defer.Deferred()
                    d.request = request
                    d.addCallback(self.renderActions, after, True)
                    self._defers.append(d)
                    
                    return NOT_DONE_YET
                
            else:
                return self.renderActions(request)
    
    def renderActions(self, request, after=None, async=False):
        if after is not None:
            data = json.dumps(self._actions[after+1:])
        else:
            data = json.dumps(self._actions)
        
        if async:
            request.write(data)
            request.finish()
        else:
            return data
    
    def postAction(self, action):
        action['aid'] = len(self._actions)
        self._actions.append(action)
        for defer in self._defers:
            defer.callback(defer.request)
        del self._defers[:]
    
    def isMember(self, user_id):
        for member in self._members:
            if member['user_id'] == user_id:
                return True
        return False
    
    def render_GET(self, request):
        # just list room members
        arr = []
        for member in self._members:
            arr.append({ 'user_name': member['user_name'] })
        return json.dumps(arr)
    
    def __str__(self):
        return '%d %s - active %s' % (len(self._members), "member" if len(self._members) == 1 else "members", ago.human(datetime.datetime.today() - self._start, 1, past_tense = '{0}',))


class Rooms(resource.Resource):
    isLeaf = False
    
    def __init__(self):
        resource.Resource.__init__(self)
        
        self._rooms = []
    
    def addRoom(self, name, uuid=None):
        room = Room(name, uuid)
        self._rooms.append(room)
        self.putChild(room._uuid, room)
    
    def render_GET(self, request):
        arr = []
        for room in self._rooms:
            arr.append({ 'name': room._name, 'uuid': room._uuid, 'info': str(room) })
        return json.dumps(arr)

root = resource.Resource()

rooms = Rooms()
rooms.addRoom('global', 'global')

root.putChild('rooms', rooms)

site = Site(root)
reactor.listenTCP(8080, site)
reactor.run()

