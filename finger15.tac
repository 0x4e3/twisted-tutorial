from twisted.application import service, strports
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic
from twisted.web import resource, server, static
import cgi


class FingerProtocol(basic.LineReceiver):
    def lineReceived(self, user):
        d = self.factory.getUser(user)

        def onError(err):
            return 'Internal server error.'
        d.addErrback(onError)

        def writeResponce(message):
            self.transport.write(message + b'\r\n')
            self.transport.loseConnection()
        d.addCallback(writeResponce)


class FingerResource(resource.Resource):
    def __init__(self, users):
        self.users = users
        resource.Resource.__init__(self)

    def getChild(self, username, request):
        messagevalue = self.users.get(username)
        if messagevalue:
            messagevalue = messagevalue.decode("ascii")
        if username:
            username = username.decode("ascii")
        if messagevalue is not None:
            messagevalue = cgi.escape(messagevalue)
            text = '<h1>{}</h1><p>{}</p>'.format(username, messagevalue)
        else:
            text = '<h1>{}</h1><p>No such user</p>'.format(username)
        text = text.encode("ascii")
        return static.Data(text, 'text/html')


class FingerService(service.Service):
    def __init__(self, filename):
        self.filename = filename
        self.users = {}

    def _read(self):
        self.users.clear()
        with open(self.filename, "rb") as f:
            for line in f:
                user, _, status = line.partition(b':')
                user = user.strip()
                status = status.strip()
                self.users[user] = status
        self.call = reactor.callLater(3, self._read)

    def getUser(self, user):
        return defer.succeed(self.users.get(user, b"No such user"))

    def getFingerFactory(self):
        f = protocol.ServerFactory()
        f.protocol = FingerProtocol
        f.getUser = self.getUser
        return f

    def getResource(self):
        r = FingerResource(self.users)
        return r

    def startService(self):
        self._read()
        service.Service.startService(self)

    def stopService(self):
        service.Service.stopService(self)
        self.call.cancel()


application = service.Application('finger', uid=0, gid=0)
f = FingerService('/etc/passwd')
serviceCollection = service.IServiceCollection(application)
f.setServiceParent(serviceCollection)

strports.service('tcp:79', f.getFingerFactory()). \
    setServiceParent(serviceCollection)
strports.service('tcp:8000', server.Site(f.getResource())). \
    setServiceParent(serviceCollection)
