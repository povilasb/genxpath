from textual_serve.server import Server

server = Server("python -m genxpath.gui", port=7003)
server.serve()
