from sys import stdout
import BaseHTTPServer
import os


class case_cgi_file(object):
    '''sth runable'''
    def test(self, handler):
        return os.path.isfile(handler.full_path) and \
            handler.full_path.endwith('.py')
    
    def act(self, handler):
        handler.run_cgi(handler.full_path)


class case_directory_index_file(object):
    """Server index.html page for a directory."""
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
            os.path.isfile(self.index_path(handler))
    
    def act(self, handler):
        handler.handle_file(self.index_path(handler))


class case_directory_no_index_file(object):
    '''Server listing for a directory without a index.html page'''

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path, 'index.html')
    
    def act(self, handler):
        handler.list_dir(handler.full_path)


class case_no_file(object):
    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException('{} not found'.format(handler.path))


class case_existing_file(object):
    def test(self, handler):
        return os.path.isfile(handler.full_path)
    
    def act(self, handler):
        handler.handle_file(handler.full_path)


class case_always_fail(object):
    def test(self, handler):
        return True

    def act(self, handler):
        return ServerException('Unknown object {}'.format(handler.path))

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    Handle HTTP request by returning a fixed 'page'
    """
    Listing_Page = '''\
        <html>
        <body>
        <ul>
        {0}
        </ul>
        </body>
        </html>
        '''

    def run_cgi(self, full_path):
        cmd = 'python ' + full_path
        child_stdin, child_stdout = os.popen2(cmd)
        child_stdin.close()
        data = child_stdout.read()
        child_stdout.close()
        self.send_content(data)
    
    def list_dir(self, full_path):
        try:
            entries = os.listdir(full_path)
            bullets = ['<li>{}</li}'.format(e) for e in entries if not e.startswith('.')]
            page = self.Listing_Page.format('\n'.join(bullets))
            self.send_content(page)
        except OSError as msg:
            msg = '[] cannot be listed {}'.format(self.path, msg)
            self.handle_error(msg)

    Cases = [
        case_existing_file(),
        case_always_fail(),
        case_no_file(),
        case_directory_index_file(),
    ]

    Page = '''\
<html>
<body>
<table>
<tr>  <td>Header</td>         <td>Value</td>          </tr>
<tr>  <td>Date and time</td>  <td>{date_time}</td>    </tr>
<tr>  <td>Client host</td>    <td>{client_host}</td>  </tr>
<tr>  <td>Client port</td>    <td>{client_port}s</td> </tr>
<tr>  <td>Command</td>        <td>{command}</td>      </tr>
<tr>  <td>Path</td>           <td>{path}</td>         </tr>
</table>
</body>
</html>
'''

    Error_Page = """\
<html>
<body>
<h1>Error accessing {path}</h1>
<p>{msg}</p>
</body>
</html> 
"""

    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content, 404)

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self. wfile.write(content)

    def create_page(self):
        values = {
            'date_time': self.date_time_string(),
            'client_host': self.client_address[0],
            'client_port': self.client_address[1],
            'command': self.command,
            'path': self.path,
        }
        page = self.Page.format(**values)
        return page

    def send_page(self, page):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header("Content-Length", str(len(self.Page)))
        self.end_headers()
        self.wfile.write(page)

    def do_GET(self):
        try:
            self.full_path = os.getcwd() + self.path

            for case in self.Cases:
                handler = case()
                if handler.test(self):
                    handler.act(self)
                    break

        except Exception as msg:
            self.handle_error(msg)

    def handle_file(self, full_path):
        try: 
            with open(full_path, 'rb') as reader :
                content = reader.read()
            self.send_content(content)
        except IOError as msg:
            msg = '{} cannot be read: {}'.format(self.path, msg)
            self.handle_error(msg)


class ServerException(Exception):
    pass



if __name__ == '__main__':
    server_address = ('', 8080)
    server = BaseHTTPServer.HTTPServer(server_address, RequestHandler)
    server.serve_forever()
