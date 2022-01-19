from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer


def application(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b"Welcome to WSGI!\n"]


container = WSGIContainer(application)
server = HTTPServer(container)
server.listen(8081)
print("Listening")
IOLoop.current().start()