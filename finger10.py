"""
Read username, output from factory interfacting to web, drop connections.
"""
from twisted.internet import protocol, reactor, endpoints
from twisted.protocols import basic
from twisted.web import client


class FingerProtocol(basic.LineReceiver):
    def lineReceived(self, user):
        d = self.factory.getUser(user)

        def onError(err):
            return b'Internal server error.'
        d.addErrback(onError)

        def writeResponce(message):
            self.transport.write(message + b'\r\n')
            self.transport.loseConnection()
        d.addCallback(writeResponce)


class FingerFactory(protocol.ServerFactory):
    protocol = FingerProtocol

    def __init__(self, prefix):
        self.prefix = prefix

    def getUser(self, user):
        return client.getPage(self.prefix + user)


fingerEndpoint = endpoints.serverFromString(reactor, 'tcp:1079')
fingerEndpoint.listen(FingerFactory(prefix=b'https://www.facebook.com'))
reactor.run()
