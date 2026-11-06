
import socket
import threading
import json


def enviar(conexion, datos):
    mensaje = json.dumps(datos, ensure_ascii=False) + "\n"
    conexion.sendall(mensaje.encode("utf-8"))


def recibir_mensajes(conexion):
    archivo = conexion.makefile("r", encoding="utf-8")

    try:
        for linea in archivo:
            datos = json.loads(linea)
            tipo = datos.get("tipo")

            if tipo == "bienvenida":
                print("\n" + datos["texto"])

            elif tipo == "usuarios":
                print("\n========== USUARIOS CONECTADOS ==========")
                for usuario in datos["lista"]:
                    print(" -", usuario)
                print("=========================================")

            elif tipo == "mensaje":
                print(f"\n[{datos['origen']}] : {datos['texto']}")

            elif tipo == "confirmacion":
                print("\n" + datos["texto"])

            elif tipo == "error":
                print("\nERROR:", datos["texto"])

    except (OSError, json.JSONDecodeError):
        pass

    finally:
        archivo.close()
        print("\nConexion con el servidor finalizada.")


def iniciar_cliente():
    print("===================================")
    print("          CLIENTE DE CHAT")
    print("===================================")

    ip = input("IP del servidor [127.0.0.1]: ").strip()
    if not ip:
        ip = "127.0.0.1"

    puerto = int(input("Puerto [59420]: ").strip() or "59420")
    nombre = input("Escriba su nombre de usuario: ").strip()

    if not nombre:
        print("Debe ingresar un nombre.")
        return

    conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        conexion.connect((ip, puerto))

        enviar(conexion, {
            "tipo": "login",
            "nombre": nombre
        })

        hilo = threading.Thread(
            target=recibir_mensajes,
            args=(conexion,),
            daemon=True
        )
        hilo.start()

        destinatario = None

        print("\nComandos disponibles:")
        print("/usuarios       Ver usuarios conectados")
        print("/chat nombre    Seleccionar destinatario")
        print("chao            Abandonar el chat\n")

        while True:
            texto = input(f"{nombre}> ").strip()

            if not texto:
                continue

            if texto.lower() in ("chao", "/salir"):
                enviar(conexion, {"tipo": "salir"})
                break

            elif texto.lower() == "/usuarios":
                enviar(conexion, {"tipo": "usuarios"})

            elif texto.lower().startswith("/chat "):
                destinatario = texto[6:].strip()

                if destinatario:
                    print(f"Conversacion seleccionada: {destinatario}")
                else:
                    print("Escriba el nombre del destinatario.")

            else:
                if destinatario is None:
                    print("Primero seleccione un usuario con /chat nombre")
                    continue

                enviar(conexion, {
                    "tipo": "mensaje",
                    "destino": destinatario,
                    "texto": texto
                })

    except ConnectionRefusedError:
        print("No se pudo conectar. Verifique que el servidor este iniciado.")

    except (OSError, ValueError) as error:
        print("Error:", error)

    finally:
        conexion.close()
        print("Cliente desconectado.")


if __name__ == "__main__":
    iniciar_cliente()
