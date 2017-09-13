from twisted.application import service, strports
from twisted.internet import protocol, defer
from twisted.protocols import basic


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


class FingerSetterProtocol(basic.LineReceiver):
    def connectionMade(self):
        self.lines = []

    def lineReceived(self, line):
        self.lines.append(line)

    def connectionLost(self, reason):
        user = self.lines[0]
        status = self.lines[1]
        self.factory.setUser(user, status)


class FingerService(service.Service):
    def __init__(self, users):
        self.users = users

    def getUser(self, user):
        return defer.succeed(self.users.get(user, b'No such user.'))

    def setUser(self, user, status):
        self.fingerFactory.users[user] = status

    def getFingerFactory(self):
        f = protocol.ServiceFactory()
        f.protocol = FingerProtocol
        f.getUser = self.getUser
        return f

    def getFingerSetterFactory(self):
        f = protocol.ServiceFactory()
        f.protocol = FingerSetterProtocol
        f.setUser = self.setUser
        return f


application = service.Application('finger', uid=0, gid=0)
f = FingerService({b'ad': b'Go to Hell!'})
serviceCollection = service.IServiceCollection(application)
strports.service("tcp:79", f.getFingerFactory()). \
    setServiceParent(serviceCollection)
strports.service("tcp:1079", f.getFingerSetterFactory()). \
    setServiceParent(serviceCollection)
