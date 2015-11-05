import BaseHTTPServer
import sys

HOST_NAME = 'localhost'

def get_content_type(filename):
    if filename.endswith('css'):
        return 'text/css'
    if filename.endswith('js'):
        return 'text/javascript'

    return "text/html; charset=utf8"

class HTMLHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    Simple web server that always sends all files (except css and javascript)
    as HTML files. This is provided to make it easier to contribute new code to this project.

    Using the regular web server, files ending with language code (as used by Apache mod_language)
    will be downloaded by the users browser instead of served as an HTML page.
    """
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

    def do_GET(s):
        try:
            with open(s.path[1:]) as f:
                s.send_response(200)
                s.send_header("Content-Type", get_content_type(s.path))
                s.end_headers()
                s.wfile.write(''.join(f.readlines()))
        except Exception as e:
            # Just send the error message if something goes wrong
            s.send_error(500, message=str(e))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8080
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, port), HTMLHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
