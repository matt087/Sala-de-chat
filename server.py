import socket
from threading import Thread

class Server(Thread):
    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.socketConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketConnection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socketConnection.bind((self.ip, self.port))
        self.socketConnection.listen(5)

        self.usuariosConectados = {}
        self.historialChat = []
        print(f'Servidor corriendo en el puerto: {port}')

    def run(self):
        while True:
            try:
                conexion, direccion = self.socketConnection.accept()
                print(f"Conexión establecida desde: {direccion}")
                conexion.send('#NICK#'.encode())  # Solicitar nickname
                nick = self.iniciarChat(conexion)
                if nick is not None:
                    cliente = Thread(target=self.escucharClientes, args=(nick, conexion,))
                    cliente.start()
            except Exception as e:
                print(f"Error al aceptar conexiones: {e}")

    def iniciarChat(self, conexion):
        try:
            nickname = self.obtenerNick(conexion)
            if nickname is None:
                return None
            elif nickname == 'exit':
                self.errorCliente(conexion, 'No se pudo realizar la conexión')
                return None
            else:
                self.usuariosConectados[nickname] = conexion
                self.historialChat.append(f'El usuario {nickname} se ha conectado')
                self.historialCliente()
            return nickname
        except Exception as e:
            print(f"Error al iniciar chat: {e}")
            conexion.close()
            return None

    def escucharClientes(self, nickname, conexion):
        while True:
            try:
                message = conexion.recv(1024).decode()
                if not message:
                    # Si no hay mensaje, la conexión se cerró
                    self.desconectarCliente(nickname, conexion)
                    break
                # Manejo de mensajes recibidos
                if message == 'exit':
                    self.desconectarCliente(nickname, conexion)
                    break
                elif message.startswith('#MSG#'):
                    message = message[5:]
                    self.historialChat.append(f'{nickname}: {message}')
                    self.historialCliente()
            except Exception as e:
                print(f"Error al recibir mensaje de {nickname}: {e}")
                self.desconectarCliente(nickname, conexion)
                break
    
    def desconectarCliente(self, nickname, conexion):
        print(f"Desconectando a {nickname}")
        if nickname in self.usuariosConectados:
            del self.usuariosConectados[nickname]
        self.historialChat.append(f'{nickname} ha abandonado la sala.')
        self.historialClienteExcepcion(conexion)
        conexion.close()

    def errorCliente(self, conexion, text):
        try:
            conexion.sendall(('#ERROR#' + text).encode())
        except:
            print(f"No se pudo enviar el mensaje de error a {conexion}")

    def historialCliente(self):
        lista_users = list(self.usuariosConectados.values())
        chat = '\n'.join(self.historialChat)
        for user in lista_users:
            try:
                user.sendall(('#CHAT#' + chat).encode())
            except Exception as e:
                print(f"Error al enviar historial a un usuario: {e}")

    def historialClienteExcepcion(self, conexion):
        lista_users = list(self.usuariosConectados.values())
        chat = '\n'.join(self.historialChat)
        for user in lista_users:
            if user != conexion:
                try:
                    user.sendall(('#CHAT#' + chat).encode())
                except Exception as e:
                    print(f"Error al enviar historial durante desconexión: {e}")

    def obtenerNick(self, conexion):
        try:
            nick = conexion.recv(1024).decode()
            return nick
        except Exception as e:
            print(f"Error al recibir el nickname: {e}")
            return None

if __name__ == '__main__':
    server = Server('', 9999)
    server.start()
