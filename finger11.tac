"""
Read username, output from non-empty factory, drop connections.
Use deferreds, to minimize synchronicity assumptions.
Write application. Save in 'finger.tpy'.
"""
from twisted.application import service, strports
from twisted.internet import protocol, reactor, defer
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


class FingerFactory(protocol.ServerFactory):
    protocol = FingerProtocol

    def __init__(self, users):
        self.users = users

    def getUser(self, user):
        return defer.succeed(self.users.get(user, b'No such user.'))


application = service.Application('finger', uid=0, gid=0)
factory = FingerFactory({b'ad': b'Go to Hell!!!'})
strports.service('tcp:79', factory, reactor=reactor).setServiceParent(
    service.IServiceCollection(application))
