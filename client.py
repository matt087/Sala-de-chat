import socket
from threading import Thread
import os
import sys

class Client(Thread):
    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.socketConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.historial = ""
        self.nickname = input("Ingrese su nickname: ")
        self.connection()

    def connection(self):
        try:
            self.socketConnection.connect((self.ip, self.port))
        except socket.error as r:
            print(f'Error al proceder con la conexión: {r}')
            sys.exit()

    def comunicarServer(self):
        while True:
            try:
                print(self.historial)  # Mostrar historial antes de cada mensaje
                msg = input("Mensaje: ").strip() 
                if msg == 'send':
                    self.socketConnection.sendall(('#FILE#').encode())
                elif msg == "exit":
                    self.socketConnection.sendall('exit'.encode())
                    self.socketConnection.close()
                    break
                elif msg:
                    self.socketConnection.sendall(('#MSG#' + msg).encode())
                else:
                    print("No se puede enviar un mensaje vacío.")  
                    input()
                    self.limpiarPantalla()
            except OSError:
                print("Error al enviar el mensaje. La conexión está cerrada.")
                break

    def recibirServer(self):
        while True:
            try:
                msg = self.socketConnection.recv(1024).decode()
                if not msg:
                    print("Conexión cerrada por el servidor.")
                    self.socketConnection.close()
                    break
                if msg.startswith('#MSG#'):
                    msg = msg[5:]
                    print(msg)
                elif msg.startswith('#ERROR#'):
                    msg = msg[7:]
                    print(msg)
                elif msg.startswith('#CHAT#'):
                    self.historial = msg[6:]
                    self.limpiarPantalla()  
                    print(self.historial)  
                    print("\nMensaje: ", end='', flush=True)  
                elif msg.startswith('#NICK#'):
                    self.socketConnection.sendall(self.nickname.encode())
            except OSError:
                print("Conexión cerrada.")
                break

    def limpiarPantalla(self):
        if os.name == 'nt':  
            os.system('cls')
        else:  
            os.system('clear')

    def run(self):
        hilo_recibir = Thread(target=self.recibirServer)
        hilo_recibir.start()

        hilo_escribir = Thread(target=self.comunicarServer)
        hilo_escribir.start()

if __name__ == '__main__':
    cliente = Client('localhost', 9999)
    cliente.start()
