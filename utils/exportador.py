from datetime import datetime

def exportar_txt(moto):

    with open(
        "exports/registros.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n====================\n")

        f.write(f"DATA: {datetime.now()}\n")

        f.write(f"TAG: {moto.tag_rfid}\n")

        f.write(f"MODELO: {moto.modelo}\n")

        f.write(f"COR: {moto.cor}\n")

        f.write(f"ANO: {moto.ano}\n")

        f.write(f"CHASSI: {moto.chassi}\n")

        f.write("====================\n")