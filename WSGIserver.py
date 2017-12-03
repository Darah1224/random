#WSGI allows developers to seperate choice of a Web Framework from choice of a Web server.
#The web server implement the server side of of WSGI interface
import errno
import os
import socket
import StringIO
import sys
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from os import curdir, sep

class myHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        #define the default page
        if self.path == '/':
            self.path = "/index.html"
            sendReply = True
        try:
            #Check the file extension required and
            #set the right mime type

            sendReply = False
            if self.path.endswith(".html"):
                mimetype = 'text/html'
                sendReply = True
            elif self.path.endswith(".jpg"):
                mimetype = 'image/jpg'
                sendReply = True
            elif self.path.endswith(".gif"):
                mimetype = 'image/gif'
                sendReply = True
            elif self.path.endswith(".png"):
                mimetype = 'image/png'
                sendReply = True
            elif self.path.endswith(".js"):
                mimetype = 'application/javascript'
                sendReply = True
            elif self.path.endswith(".css"):
                mimetype = 'text/css'
                sendReply = True

            if sendReply == True:
                #open the static file requested and send it
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-Type', mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

class WSGIServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5

    def __init__(self, server_address):
        #Creating a listening socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )

        #Allow to reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        #bind
        listen_socket.bind(server_address)
        #Activate
        listen_socket.listen(self.request_queue_size)
        #Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        #Return headers set by Web framework/Web Application
        #This is where an application/framework stores
        #an HTTP status and HTTP response headers for the server
        # to transmit to the client
        self.headers_set = []

    def set_app(self, application):
        self.application = application

    #def grim_reaper(signum, frame):
    #    while True:
    #        try:
    #            pid, status = os.waitpid(
    #                -1, # Wait for any child process
    #                os.WNOHANG  # Do not block and return EWOULDBLOCK error
    #            )
    #        except OSError:
    #            return

    #        if pid == 0: #no more zombies
    #            return

    def serve_forever(self):
        listen_socket = self.listen_socket
        #signal.signal(signal.SIGCHLD, self.grim_reaper)
        while True:
            #New client connection
            try:
                self.client_connection, client_address = listen_socket.accept()
            except IOError as e:
                code, msg = e.args
                # restart 'accept' if it was interrupted
                if code == errno.EINTR:
                    continue
                else:
                    raise

            try:
                pid = os.fork()
                if pid == 0: #child
                    listen_socket.close() #close child copy
                    #Handle one request and close the client connection
                    #Then loop over to wait for another client connection
                    self.handle_one_request()
                    self.client_connection.close()
                    os._exit(0)

            except socket.error:
                pass
            self.client_connection.close() #close parent copy and loop over

    def handle_one_request(self):
        self.request_data = request_data = self.client_connection.recv(1024)
        #Print formatted request data
        print(''.join(
            '< {line}\n'.format(line=line)
            for line in request_data.splitlines()
        ))

        if request_data != '':
            self.parse_request(request_data)

        #construct environment dictionary using request data
        #env = self.get_environ()

        #Call the application callable and
        #get a result that will become HTTP response body

        #The server invokes the 'application' callable
        #for each request it receives from an HTTP client
        #It passes a dictionary 'environ' containing WSGI/CGI variables
        #and a 'start_response' callable as arguments to the 'application' callable

        #result = self.application(env, self.start_response)
        #self.start_response()

        #Construct a response and send it back to the client
        #self.finish_response(result)
        self.respond()


    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')
        #Break down the request line into components
        (self.request_method, #GET or POST
        self.path,           #Path of the application/script
        self.request_version #HTTP/1.1
        ) = request_line.split()

    def get_environ(self):
        env = {}

        #Required WSGI variables
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = StringIO.StringIO(self.request_data)
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False

        #Required CGI variables
        env['REQUEST_METHOD'] = self.request_method #GET
        env['PATH_INFO'] = self.path #path of the application
        env['SERVER_NAME'] = self.server_name #Name of the server e.g. localhost
        env['SERVER_PORT'] = str(self.server_port)
        return env

    def start_response(self):#, status, response_headers, exc_info=None):
        #The framework/application generates an HTTP status and HTTP response header
        #and passes them to the 'start_response' callable for the server to store them
        #The framework/application also returns a response body.

        #Add necessary server headers
        time = str(datetime.now())
        server_headers = [
            ('Date', time),
            ('Server', 'WSGIServer 0.2'),
        ]

        #The server combines the status, the response headers,
        #and the response body into an HTTP response and transmits it to the client
        self.headers_set = [status, response_headers + server_headers]
        #print self.headers_set
        #To adhere to WSGI specification
        #The start_response must return a 'write' callable.
        #return self.headers_set

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 {status}\r\n'.format(status=status)
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data

            #print formatted response data
            print(''.join(
                '> {line}\n'.format(line = line)
                for line in response.splitlines()
            ))
            self.client_connection.sendall(response)
        finally:
            self.client_connection.close()

    def respond(self):
        if self.path == '/':
            self.path = 'index.html'
        #try:
            #Check the file extension required and
            #set the right mime type

            sendReply = False
            if self.path.endswith(".html"):
                mimetype = 'text/html'
                sendReply = True
            elif self.path.endswith(".jpg"):
                mimetype = 'image/jpg'
                sendReply = True
            elif self.path.endswith(".gif"):
                mimetype = 'image/gif'
                sendReply = True
            elif self.path.endswith(".js"):
                mimetype = 'application/javascript'
                sendReply = True
            elif self.path.endswith(".css"):
                mimetype = 'text/css'
                sendReply = True

            #if sendReply == True:
                #open the static file requested and send it

                #with open(path, 'rb') as fc:
                #    file_size = len(fc.read())

                #print file_size
                #response = 'HTTP/1.1 200 OK\r\n'
                #self.client_connection.send(response)
                #response = 'Server: WSGIServer 0.2' #can change to text/html etc.
                #self.client_connection.send(response)


        #path = os.path.abspath("."+self.path)
        #path = "." + self.path
        #print path
        #with open(path, 'rb') as f:
        #    sum = 0
        #    while response:
        #        response = f.read()
                #print response
        #        sum = sum + len(response)
        #        self.client_connection.sendall(response)

        #print sum
        #f.close()


SERVER_ADDRESS = (HOST, PORT) = '', 8888

def make_server(server_address):#, application):
    server = WSGIServer(server_address)
    #server.set_app(application)
    return server

if __name__ == '__main__':
    #if len(sys.argv) < 2:
        #sys.exit('Provide a WSGI application object as module: callable')

    #app_path = sys.argv[1]

    #The framework provides an 'application' callable (The WSGI specification
    #doesn't prescibe how that should be implemented)
    #module, application = app_path.split(':')
    #print 'module:', module, 'application:', application
    #module = __import__(module)
    #application = getattr(module, application)

    #httpd = make_server(SERVER_ADDRESS)#, application)

    server = HTTPServer(('', PORT), myHandler)
    print('WSGIServer: Serving HTTP on port {port} ...\n'.format(port=PORT))
    #httpd.serve_forever()

    server.serve_forever()
