import socket
from threading import Thread
import os

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
                conexion.send('#NICK#'.encode())  
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
                    self.desconectarCliente(nickname, conexion)
                    break
                if message == 'exit':
                    self.desconectarCliente(nickname, conexion)
                    break
                elif message.startswith('#MSG#'):
                    message = message[5:]
                    self.historialChat.append(f'{nickname}: {message}')
                    self.historialCliente()
                elif message.startswith("#FILE#"):
                    file_name = message[6:]
                    self.recibirArchivo(conexion, file_name, nickname)
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

    def recibirArchivo(self, conexion, file_name, nickname):
        try:
            print(f"Recibiendo archivo: {file_name}")
            file_size_data = b''
            while not file_size_data.endswith(b'^'):  
                file_size_data += conexion.recv(1)
            file_size_str = file_size_data.decode()[:-1] 
            if file_size_str.startswith("#SIZE#"):
                file_size_str = file_size_str[6:]
            if file_size_str.isdigit():
                file_size = int(file_size_str)
                print(f"Tamaño del archivo: {file_size} bytes")

                with open(file_name, 'wb') as f:
                    bytes_received = 0

                    while bytes_received < file_size:
                        file_data = conexion.recv(1024)
                        if not file_data:   
                            break
                        f.write(file_data)
                        bytes_received += len(file_data)

                f.close()

                print(f"Archivo {file_name} recibido y guardado.")
                self.transmitirArchivo(file_name, conexion, nickname)
            else:
                print(f"Error: Tamaño de archivo no válido: {file_size_str}")
        except Exception as e:
            print(f"Error al recibir el archivo: {e}")


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

    def transmitirArchivo(self, file_path, conexion, nickname):
        lista_users = list(self.usuariosConectados.values())
        for user in lista_users:
            try:
                if user != conexion:
                    if os.path.isfile(file_path):
                        user.sendall(('#FILE#' + file_path).encode())
                        
                        file_size = os.path.getsize(file_path)
                        user.sendall(f'#SIZE#{file_size}^'.encode())  
                        
                        with open(file_path, 'rb') as f:
                            bytes_sent = 0
                            while bytes_sent < file_size:
                                file_data = f.read(1024)
                                user.sendall(file_data)
                                bytes_sent += len(file_data)

                        f.close()
                        print(f"Archivo {file_path} enviado por {nickname}.")
                        self.historialChat.append(f"{nickname} ha enviado el archivo {file_path}")
                        self.historialCliente()
                    else:
                        print(f"El archivo {file_path} no existe.")
            except Exception as e:
                print(f"Error al enviar el archivo a {user}: {e}")

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
