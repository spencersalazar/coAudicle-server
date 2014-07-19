
from twisted.web import server, resource
from twisted.internet import reactor
import types, uuid, json, cgi

class Site(server.Site):
    def getResourceFor(self, request):
        request.setHeader('Content-Type', 'application/json')
        return server.Site.getResourceFor(self, request)

# shorthand convenience method
bind = types.MethodType

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
        def join_POST(self, request):
            user_id = request.args['id'][0]
            name = request.args['name'][0]
            self._members.append({ 'name': name, 'id': user_id })
            return ''
        
        join = resource.Resource()
        join.render_POST = bind(join_POST, self)
        self.putChild('join', join)
        
        # submit action
        def submit_POST(self, request):
            user_id = request.args['id'][0]
            action = json.loads(request.args['action'][0])
            
            if not self.isMember(user_id):
                request.setResponseCode(403)
                request.setHeader('Content-Type', 'text/plain')
                return '403 Forbidden'
            
            action['user_id'] = user_id
            action['id'] = len(self._actions)
            self._actions.append(action)
            
            return ''
        
        submit = resource.Resource()
        submit.render_POST = bind(submit_POST, self)
        self.putChild('submit', submit)
        
        # retrieve action(s)
        def actions_GET(self, request):            
            if 'after' in request.args:
                last = int(request.args['after'][0])
                return json.dumps(self._actions[last+1:])
                
            else:
                return json.dumps(self._actions)
        
        actions = resource.Resource()
        actions.render_GET = bind(actions_GET, self)
        self.putChild('actions', actions)
    
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

