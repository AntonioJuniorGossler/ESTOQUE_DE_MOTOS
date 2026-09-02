import socket
import time
import re
import threading


# ============================================================
# CONFIGURAÇÃO DOS LEITORES RFID
# ============================================================

LEITORES = [
    {
        "nome": "LEITOR 01",
        "ip": "192.168.0.101",
        "porta": 6000,
        "local": "MONTAGEM"
    },
    {
        "nome": "LEITOR 02",
        "ip": "192.168.0.102",
        "porta": 6000,
        "local": "CONSÓRCIO"
    },
    {
        "nome": "LEITOR 03",
        "ip": "192.168.0.103",
        "porta": 6000,
        "local": "QUALIDADE"
    },
    {
        "nome": "LEITOR 04",
        "ip": "192.168.0.104",
        "porta": 6000,
        "local": "EXPEDIÇÃO"
    }
]

# ============================================================
# CONFIGURAÇÕES
# ============================================================

TIMEOUT = 5
BUFFER_SIZE = 4096

# Tempo mínimo para aceitar novamente a mesma TAG
# no mesmo leitor
TEMPO_ANTIREPETICAO = 3


# ============================================================
# CONECTAR AO LEITOR
# ============================================================

def conectar_leitor(leitor):

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(TIMEOUT)

        sock.connect(
            (
                leitor["ip"],
                leitor["porta"]
            )
        )

        print(
            f"[RFID] {leitor['nome']} conectado "
            f"{leitor['ip']}:{leitor['porta']} "
            f"-> {leitor['local']}"
        )

        return sock

    except Exception as erro:

        print(
            f"[RFID] {leitor['nome']} "
            f"erro ao conectar: {erro}"
        )

        return None


# ============================================================
# LIMPAR TAG RECEBIDA
# ============================================================

def limpar_tag(dados):

    if not dados:
        return None

    try:

        texto = dados.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        texto = str(dados)

    texto = texto.strip()

    if not texto:
        return None

    print(
        f"[RFID] Dados recebidos: {repr(texto)}"
    )

    # ========================================================
    # PROCURA NÚMEROS ENTRE 1 E 10
    # ========================================================

    numeros = re.findall(
        r"\b\d+\b",
        texto
    )

    for numero in numeros:

        try:

            tag = int(numero)

            if 1 <= tag <= 10:

                return tag

        except ValueError:

            continue

    return None


# ============================================================
# MONITORAR UM LEITOR
# ============================================================

def monitorar_leitor(leitor, callback):

    nome = leitor["nome"]
    ip = leitor["ip"]
    porta = leitor["porta"]
    local = leitor["local"]

    ultima_tag = None
    ultima_leitura = 0

    print()
    print("=" * 60)
    print(f"INICIANDO {nome}")
    print(f"IP:     {ip}")
    print(f"PORTA:  {porta}")
    print(f"LOCAL:  {local}")
    print("=" * 60)

    while True:

        sock = conectar_leitor(leitor)

        # ====================================================
        # SE NÃO CONSEGUIU CONECTAR
        # ====================================================

        if sock is None:

            print(
                f"[RFID] {nome} tentando novamente "
                f"em 5 segundos..."
            )

            time.sleep(5)

            continue

        # ====================================================
        # LEITURA CONTÍNUA
        # ====================================================

        try:

            while True:

                dados = sock.recv(
                    BUFFER_SIZE
                )

                # =================================================
                # LEITOR FECHOU A CONEXÃO
                # =================================================

                if not dados:

                    print(
                        f"[RFID] {nome} encerrou a conexão."
                    )

                    break

                # =================================================
                # TENTA IDENTIFICAR A TAG
                # =================================================

                tag = limpar_tag(dados)

                if tag is None:

                    continue

                agora = time.time()

                # =================================================
                # EVITA REPETIÇÃO DA MESMA TAG
                # =================================================

                if (
                    tag == ultima_tag
                    and
                    agora - ultima_leitura
                    < TEMPO_ANTIREPETICAO
                ):

                    continue

                ultima_tag = tag
                ultima_leitura = agora

                # =================================================
                # TAG DETECTADA
                # =================================================

                print()
                print("=" * 60)
                print(">>> TAG RFID DETECTADA <<<")
                print(f"LEITOR: {nome}")
                print(f"TAG:    {tag}")
                print(f"LOCAL:  {local}")
                print("=" * 60)

                # =================================================
                # ENVIA PARA O SISTEMA
                # =================================================

                callback(
                    tag,
                    local,
                    nome
                )

        except socket.timeout:

            print(
                f"[RFID] {nome}: "
                f"tempo de conexão esgotado."
            )

        except ConnectionResetError:

            print(
                f"[RFID] {nome}: "
                f"conexão perdida."
            )

        except Exception as erro:

            print(
                f"[RFID] {nome}: "
                f"erro durante leitura: {erro}"
            )

        finally:

            try:

                sock.close()

            except Exception:

                pass

        # ====================================================
        # RECONEXÃO
        # ====================================================

        print(
            f"[RFID] {nome}: "
            f"reconectando em 3 segundos..."
        )

        time.sleep(3)


# ============================================================
# INICIAR TODOS OS LEITORES
# ============================================================

def iniciar_leitores(callback):

    print()
    print("=" * 60)
    print("       SISTEMA DE MONITORAMENTO RFID")
    print("=" * 60)
    print()
    print(
        f"Quantidade de leitores: {len(LEITORES)}"
    )
    print()

    # ========================================================
    # CRIA UMA THREAD PARA CADA LEITOR
    # ========================================================

    for leitor in LEITORES:

        thread = threading.Thread(
            target=monitorar_leitor,
            args=(
                leitor,
                callback
            ),
            daemon=True
        )

        thread.start()

        time.sleep(0.5)

    print()
    print("=" * 60)
    print("TODOS OS LEITORES FORAM INICIADOS")
    print("Aguardando TAGs RFID...")
    print("=" * 60)
    print()


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    def teste(tag, local, leitor):

        print()
        print("############################################")
        print("#          MOVIMENTAÇÃO RFID")
        print("############################################")
        print(f"# TAG:    {tag}")
        print(f"# LEITOR: {leitor}")
        print(f"# LOCAL:  {local}")
        print("############################################")
        print()

    iniciar_leitores(
        teste
    )

    # ========================================================
    # MANTÉM O PROGRAMA RODANDO
    # ========================================================

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print("Sistema RFID encerrado.")