
import socket
import threading
import json

# Configuracion del servidor
HOST = "127.0.0.1"
PORT = 59420

# Diccionario de usuarios conectados
clientes = {}
lock = threading.Lock()


def enviar(conexion, datos):
    mensaje = json.dumps(datos, ensure_ascii=False) + "\n"
    conexion.sendall(mensaje.encode("utf-8"))


def enviar_a_usuario(nombre, datos):
    with lock:
        cliente = clientes.get(nombre)

    if cliente:
        try:
            with cliente["lock"]:
                enviar(cliente["socket"], datos)
            return True
        except OSError:
            return False

    return False


def actualizar_usuarios():
    with lock:
        usuarios = list(clientes.keys())
        conexiones = list(clientes.values())

    for cliente in conexiones:
        try:
            with cliente["lock"]:
                enviar(cliente["socket"], {
                    "tipo": "usuarios",
                    "lista": usuarios
                })
        except OSError:
            pass


def atender_cliente(conexion, direccion):
    nombre = None
    archivo = conexion.makefile("r", encoding="utf-8")

    try:
        primera_linea = archivo.readline()

        if not primera_linea:
            return

        datos = json.loads(primera_linea)

        if datos.get("tipo") != "login":
            return

        nombre = datos.get("nombre", "").strip()

        if not nombre:
            return

        with lock:
            if nombre in clientes:
                enviar(conexion, {
                    "tipo": "error",
                    "texto": "Ese usuario ya esta conectado."
                })
                return

            clientes[nombre] = {
                "socket": conexion,
                "lock": threading.Lock()
            }

        print(f'Usuario "{nombre}" conectado desde {direccion}')

        enviar(conexion, {
            "tipo": "bienvenida",
            "texto": f"Bienvenido, {nombre}"
        })

        actualizar_usuarios()

        for linea in archivo:
            datos = json.loads(linea)
            tipo = datos.get("tipo")

            if tipo == "mensaje":
                destino = datos.get("destino", "").strip()
                texto = datos.get("texto", "").strip()

                if not destino or not texto:
                    continue

                if destino == nombre:
                    enviar(conexion, {
                        "tipo": "error",
                        "texto": "No puedes enviarte mensajes a ti mismo."
                    })
                    continue

                enviado = enviar_a_usuario(destino, {
                    "tipo": "mensaje",
                    "origen": nombre,
                    "texto": texto
                })

                if enviado:
                    enviar(conexion, {
                        "tipo": "confirmacion",
                        "texto": f"Mensaje enviado a {destino}"
                    })
                else:
                    enviar(conexion, {
                        "tipo": "error",
                        "texto": f"El usuario {destino} no esta conectado."
                    })

            elif tipo == "usuarios":
                actualizar_usuarios()

            elif tipo == "salir":
                break

    except (OSError, json.JSONDecodeError) as error:
        print(f"Error con el cliente {nombre}: {error}")

    finally:
        if nombre:
            with lock:
                clientes.pop(nombre, None)

            print(f'El usuario "{nombre}" abandono el chat.')
            actualizar_usuarios()

        archivo.close()
        conexion.close()


def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    servidor.bind((HOST, PORT))
    servidor.listen()

    print("===================================")
    print("       SERVIDOR DE CHAT TCP")
    print("===================================")
    print(f"Servidor iniciado en {HOST}:{PORT}")
    print("Esperando conexiones de clientes...")

    try:
        while True:
            conexion, direccion = servidor.accept()

            hilo = threading.Thread(
                target=atender_cliente,
                args=(conexion, direccion),
                daemon=True
            )

            hilo.start()

    except KeyboardInterrupt:
        print("\nCerrando servidor...")

    finally:
        servidor.close()


if __name__ == "__main__":
    iniciar_servidor()
