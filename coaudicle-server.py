
from twisted.web import server, resource
from twisted.internet import reactor
import types, uuid, json, cgi

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
        
        self._members = []
        self._name = name
        if uuid == None:
            uuid = uuid.uuid4().hex
        self._uuid = uuid
        self._actions = []
        
        # join action
        @bindPOST(self, 'join')
        def join_POST(self, request):
            user_id = request.args['user_id'][0]
            name = request.args['user_name'][0]
            if not self.isMember(user_id):
                self._members.append({ 'name': name, 'id': user_id })
                self.postAction({ 'user_id': user_id, 'type': 'join', 'name': name })
            return json.dumps({'status': 200, 'msg': 'OK'})
        
        # leave action
        @bindPOST(self, 'leave')
        def leave_POST(self, request):
            user_id = request.args['user_id'][0]
            for member in self._members:
                if member['id'] == user_id:
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
                last = int(request.args['after'][0])
                return json.dumps(self._actions[last+1:])
                
            else:
                return json.dumps(self._actions)
    
    def postAction(self, action):
        action['id'] = len(self._actions)
        self._actions.append(action)
    
    def isMember(self, user_id):
        for member in self._members:
            if member['id'] == user_id:
                return True
        return False
    
    def render_GET(self, request):
        # just list room members
        arr = []
        for member in self._members:
            arr.append({ 'name': member['name'] })
        return json.dumps(arr)

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
            arr.append({ 'name': room._name, 'uuid': room._uuid })
        return json.dumps(arr)

root = resource.Resource()

rooms = Rooms()
rooms.addRoom('global', 'global')

root.putChild('rooms', rooms)

site = Site(root)
reactor.listenTCP(8080, site)
reactor.run()

