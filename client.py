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
        self.recepcion = '/home/emontenegro/Descargas/'
        #self.recepcion = 'C:/Users/emont/Desktop/SEXTO_SEMESTRE/Sistemas Distribuidos/Código/Sockets_archivos/a/'

    def connection(self):
        try:
            self.socketConnection.connect((self.ip, self.port))
        except socket.error as r:
            print(f'Error al proceder con la conexión: {r}')
            sys.exit()

    def comunicarServer(self):
        while True:
            try:
                print(self.historial)  
                msg = input("Mensaje: ").strip()    
                if msg == 'send':
                    file_path = input("Ingrese el path del archivo: ")
                    self.limpiarPantalla()
                    if os.path.isfile(file_path):
                        self.socketConnection.sendall(('#FILE#'+os.path.basename(file_path)).encode())
                        file_size = os.path.getsize(file_path)
                        self.socketConnection.sendall(f'#SIZE#{file_size}^'.encode())  
                        with open(file_path, 'rb') as f:
                            bytes_sent = 0
                            while bytes_sent < file_size:
                                file_data = f.read(1024)
                                self.socketConnection.sendall(file_data)
                                bytes_sent += len(file_data)
                        f.close()
                    else:
                        print("El archivo no existe.")
                        input()
                        self.limpiarPantalla()
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
                    self.historial += f'\n{msg}' 
                    print(self.historial)
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
                elif msg.startswith('#FILE#'):
                    try:
                        file_name = msg[6:]
                        file_size_data = b''
                        while not file_size_data.endswith(b'^'):  
                            file_size_data += self.socketConnection.recv(1)
                        file_size_str = file_size_data.decode()[:-1] 
                        if file_size_str.startswith("#SIZE#"):
                            file_size_str = file_size_str[6:]
                        if file_size_str.isdigit():
                            file_size = int(file_size_str)
                            with open(self.recepcion+file_name, 'wb') as f:
                                bytes_received = 0
                                while bytes_received < file_size:
                                    file_data = self.socketConnection.recv(1024)
                                    if not file_data:   
                                        break
                                    f.write(file_data)
                                    bytes_received += len(file_data)

                            f.close()
                        else:
                            print(f"Error: Tamaño de archivo no válido: {file_size_str}")
                    except Exception as e:
                        print(f"Error al recibir el archivo: {e}")
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
