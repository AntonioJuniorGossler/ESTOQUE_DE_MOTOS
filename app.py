from flask import Flask, render_template, request, redirect, flash, send_file
from config import Config
import csv
import io

from database import (
    db,
    Moto,
    MotoImportada,
    Leitura,
    HistoricoMoto
)

from utils.exportador import exportar_txt
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from io import BytesIO

# Simulador RFID
from leitores.simulador import ler_tag


app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = "rfidmotos123"

db.init_app(app)


# ==========================================
# CRIA O BANCO
# NÃO APAGA MAIS OS DADOS
# ==========================================
with app.app_context():
    db.create_all()


# ==========================================
# PÁGINA INICIAL
# ==========================================
@app.route('/')
def index():

    motos = Moto.query.order_by(
        Moto.id.desc()
    ).all()

    return render_template(
        'index.html',
        motos=motos
    )


# ==========================================
# CADASTRAR MOTO
# ==========================================
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():

    if request.method == 'POST':

        # ------------------------------------------
        # PEGA OS DADOS DO FORMULÁRIO
        # ------------------------------------------
        tag_texto = request.form.get(
            "tag",
            ""
        ).strip()

        chassi = request.form.get(
            "chassi",
            ""
        ).strip()

        modelo_digitado = request.form.get(
            "modelo",
            ""
        ).strip()

        cor_digitada = request.form.get(
            "cor",
            ""
        ).strip()

        ano_digitado = request.form.get(
            "ano",
            ""
        ).strip()

        placa = request.form.get(
            "placa",
            ""
        ).strip()

        montador = request.form.get(
            "montador",
            ""
        ).strip()


        # ------------------------------------------
        # VERIFICA TAG
        # ------------------------------------------
        try:

            tag = int(tag_texto)

        except ValueError:

            flash(
                "A TAG RFID deve ser um número.",
                "erro"
            )

            return redirect("/cadastrar")


        if tag < 1 or tag > 10:

            flash(
                "A TAG RFID deve estar entre 1 e 10.",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # VERIFICA SE A TAG JÁ ESTÁ CADASTRADA
        # ------------------------------------------
        if Moto.query.filter_by(
            tag_rfid=tag
        ).first():

            flash(
                "Esta TAG RFID já está cadastrada.",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # VERIFICA CAMPOS OBRIGATÓRIOS
        # ------------------------------------------
        if not chassi:

            flash(
                "Informe o chassi da moto.",
                "erro"
            )

            return redirect("/cadastrar")


        if not modelo_digitado:

            flash(
                "Informe o modelo da moto.",
                "erro"
            )

            return redirect("/cadastrar")


        if not cor_digitada:

            flash(
                "Informe a cor da moto.",
                "erro"
            )

            return redirect("/cadastrar")


        if not ano_digitado:

            flash(
                "Informe o ano da moto.",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # PROCURA O CHASSI NO ARQUIVO IMPORTADO
        # ------------------------------------------
        moto_importada = MotoImportada.query.filter_by(
            chassi=chassi
        ).first()


        if moto_importada is None:

            flash(
                "Chassi não encontrado no arquivo importado.",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # VERIFICA SE O CHASSI JÁ FOI CADASTRADO
        # ------------------------------------------
        if Moto.query.filter_by(
            chassi=moto_importada.chassi
        ).first():

            flash(
                "Esta moto já foi cadastrada.",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # COMPARA MODELO
        # ------------------------------------------
        if (
            modelo_digitado.upper()
            != moto_importada.modelo.strip().upper()
        ):

            flash(
                f"Modelo incorreto para este chassi. "
                f"Modelo correto: {moto_importada.modelo}",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # COMPARA COR
        # ------------------------------------------
        if (
            cor_digitada.upper()
            != moto_importada.cor.strip().upper()
        ):

            flash(
                f"Cor incorreta para este chassi. "
                f"Cor correta: {moto_importada.cor}",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # COMPARA ANO
        # ------------------------------------------
        if (
            ano_digitado
            != moto_importada.ano.strip()
        ):

            flash(
                f"Ano incorreto para este chassi. "
                f"Ano correto: {moto_importada.ano}",
                "erro"
            )

            return redirect("/cadastrar")


        # ------------------------------------------
        # CRIA A MOTO
        # ------------------------------------------
        nova = Moto(

            tag_rfid=tag,

            chassi=moto_importada.chassi,

            modelo=moto_importada.modelo,

            cor=moto_importada.cor,

            ano=moto_importada.ano,

            placa=placa,

            montador=montador,

            local_atual="MONTAGEM",

            status="AGUARDANDO"
        )


        db.session.add(nova)

        db.session.commit()


        flash(
            "Moto cadastrada com sucesso!",
            "sucesso"
        )

        return redirect("/")


    return render_template(
        "cadastrar.html"
    )


# ==========================================
# SIMULAR LEITURA
# ==========================================
@app.route('/ler')
def ler():

    tag = request.args.get(
        "tag",
        type=int
    )


    if tag is None:

        return "Informe uma TAG."


    moto = Moto.query.filter_by(
        tag_rfid=tag
    ).first()


    if moto is None:

        return f"TAG {tag} não cadastrada."


    setor = "MONTAGEM"

    moto.local_atual = setor


    leitura = Leitura(

        tag_rfid=tag,

        setor=setor,

        data_hora=datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

    )


    db.session.add(leitura)

    db.session.commit()


    exportar_txt(moto)


    return render_template(
        "resultado.html",
        moto=moto
    )


# ==========================================
# DESVINCULAR MOTO
# ==========================================
@app.route("/desvincular/<int:id>")
def desvincular(id):

    moto = Moto.query.get_or_404(id)


    historico = HistoricoMoto(

        tag_rfid=moto.tag_rfid,

        chassi=moto.chassi,

        modelo=moto.modelo,

        cor=moto.cor,

        ano=moto.ano,

        placa=moto.placa,

        montador=moto.montador

    )


    db.session.add(historico)


    leitura = Leitura(

        tag_rfid=moto.tag_rfid,

        setor="MOTO ENTREGUE",

        data_hora=datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

    )


    db.session.add(leitura)

    db.session.delete(moto)

    db.session.commit()


    return redirect("/")


# ==========================================
# LEITURAS
# ==========================================
@app.route('/leituras')
def leituras():

    lista = Leitura.query.order_by(
        Leitura.id.desc()
    ).all()


    return render_template(
        'leituras.html',
        leituras=lista
    )


# ==========================================
# IMPORTAR ARQUIVO TXT / CSV
# ==========================================
@app.route("/importar", methods=["GET", "POST"])
def importar():

    if request.method == "POST":

        arquivo = request.files.get(
            "arquivo"
        )


        # ------------------------------------------
        # VERIFICA SE FOI SELECIONADO UM ARQUIVO
        # ------------------------------------------
        if (
            arquivo is None
            or arquivo.filename == ""
        ):

            flash(
                "Nenhum arquivo foi selecionado.",
                "erro"
            )

            return redirect("/importar")


        try:

            # ------------------------------------------
            # LÊ O ARQUIVO
            # ------------------------------------------
            conteudo = arquivo.read().decode(
                "utf-8-sig"
            )


            # ------------------------------------------
            # IDENTIFICA O SEPARADOR
            # ------------------------------------------
            primeira_linha = conteudo.splitlines()[0]


            if ";" in primeira_linha:

                separador = ";"

            else:

                separador = ","


            leitor = csv.DictReader(

                io.StringIO(conteudo),

                delimiter=separador

            )


            importadas = 0

            duplicadas = 0


            # ------------------------------------------
            # IMPORTA OS REGISTROS
            # ------------------------------------------
            for linha in leitor:

                chassi = linha.get(
                    "CHASSI",
                    ""
                ).strip()


                modelo = linha.get(
                    "MODELO",
                    ""
                ).strip()


                cor = linha.get(
                    "COR",
                    ""
                ).strip()


                ano = linha.get(
                    "ANO",
                    ""
                ).strip()


                # Ignora linha vazia
                if not chassi:

                    continue


                # ------------------------------------------
                # VERIFICA SE O CHASSI JÁ EXISTE
                # ------------------------------------------
                existente = MotoImportada.query.filter_by(
                    chassi=chassi
                ).first()


                if existente:

                    duplicadas += 1

                    continue


                # ------------------------------------------
                # NOVA MOTO IMPORTADA
                # ------------------------------------------
                nova = MotoImportada(

                    chassi=chassi,

                    modelo=modelo,

                    cor=cor,

                    ano=ano

                )


                db.session.add(nova)

                importadas += 1


            db.session.commit()


            # ------------------------------------------
            # MENSAGEM
            # ------------------------------------------
            flash(

                f"Arquivo importado com sucesso! "
                f"{importadas} novo(s) registro(s) adicionado(s). "
                f"{duplicadas} registro(s) já existia(m).",

                "sucesso"

            )


            return redirect(
                "/importar"
            )


        except Exception as erro:

            db.session.rollback()


            flash(

                f"Erro ao importar o arquivo: {erro}",

                "erro"

            )


            return redirect(
                "/importar"
            )


    return render_template(
        "importar.html"
    )


# ==========================================
# RELATÓRIOS
# ==========================================
@app.route("/relatorios")
def relatorios():

    return render_template(
        "relatorios.html"
    )

# ==========================================
# EXPORTAR RELATÓRIO PARA EXCEL
# COM FILTRO DE DATA
# ==========================================
@app.route("/relatorios/exportar")
def exportar_relatorio():

    # ------------------------------------------
    # RECEBE AS DATAS INFORMADAS PELO USUÁRIO
    # ------------------------------------------
    data_inicial_texto = request.args.get(
        "data_inicial",
        ""
    ).strip()

    data_final_texto = request.args.get(
        "data_final",
        ""
    ).strip()

    # ------------------------------------------
    # VERIFICA SE AS DATAS FORAM INFORMADAS
    # ------------------------------------------
    if not data_inicial_texto or not data_final_texto:

        flash(
            "Informe a data inicial e a data final.",
            "erro"
        )

        return redirect("/relatorios")

    # ------------------------------------------
    # CONVERTE AS DATAS
    # ------------------------------------------
    try:

        data_inicial = datetime.strptime(
            data_inicial_texto,
            "%Y-%m-%d"
        )

        # Coloca o final do dia na data final
        data_final = datetime.strptime(
            data_final_texto,
            "%Y-%m-%d"
        ).replace(
            hour=23,
            minute=59,
            second=59
        )

    except ValueError:

        flash(
            "Data inválida.",
            "erro"
        )

        return redirect("/relatorios")

    # ------------------------------------------
    # VERIFICA SE A DATA INICIAL É MAIOR
    # QUE A DATA FINAL
    # ------------------------------------------
    if data_inicial > data_final:

        flash(
            "A data inicial não pode ser maior que a data final.",
            "erro"
        )

        return redirect("/relatorios")

    # ------------------------------------------
    # BUSCA AS MOTOS NO PERÍODO INFORMADO
    # ------------------------------------------
    motos = Moto.query.filter(
        Moto.data_cadastro >= data_inicial,
        Moto.data_cadastro <= data_final
    ).order_by(
        Moto.data_cadastro.asc()
    ).all()

    # ------------------------------------------
    # CRIA PLANILHA EXCEL
    # ------------------------------------------
    wb = Workbook()

    ws = wb.active

    ws.title = "Relatório de Motos"

    # ------------------------------------------
    # CABEÇALHO
    # ------------------------------------------
    cabecalho = [

        "DATA DO CADASTRO",

        "TAG RFID",

        "CHASSI",

        "MODELO",

        "COR",

        "ANO",

        "PLACA",

        "MONTADOR",

        "LOCAL ATUAL",

        "STATUS"

    ]

    ws.append(cabecalho)

    # ------------------------------------------
    # ESTILO DO CABEÇALHO
    # ------------------------------------------
    for celula in ws[1]:

        celula.font = Font(
            bold=True
        )

        celula.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # ------------------------------------------
    # ADICIONA AS MOTOS
    # ------------------------------------------
    for moto in motos:

        data_cadastro = ""

        if moto.data_cadastro:

            data_cadastro = moto.data_cadastro.strftime(
                "%d/%m/%Y %H:%M:%S"
            )

        ws.append([

            data_cadastro,

            moto.tag_rfid,

            moto.chassi,

            moto.modelo,

            moto.cor,

            moto.ano,

            moto.placa,

            moto.montador,

            moto.local_atual,

            moto.status

        ])

    # ------------------------------------------
    # LARGURA DAS COLUNAS
    # ------------------------------------------
    larguras = {

        "A": 22,
        "B": 12,
        "C": 25,
        "D": 20,
        "E": 20,
        "F": 15,
        "G": 15,
        "H": 25,
        "I": 20,
        "J": 20

    }

    for coluna, largura in larguras.items():

        ws.column_dimensions[
            coluna
        ].width = largura

    # ------------------------------------------
    # CONGELA O CABEÇALHO
    # ------------------------------------------
    ws.freeze_panes = "A2"

    # ------------------------------------------
    # ALINHAMENTO
    # ------------------------------------------
    for linha in ws.iter_rows(
        min_row=2
    ):

        linha[0].alignment = Alignment(
            horizontal="center"
        )

        linha[1].alignment = Alignment(
            horizontal="center"
        )

        linha[5].alignment = Alignment(
            horizontal="center"
        )

        linha[6].alignment = Alignment(
            horizontal="center"
        )

    # ------------------------------------------
    # GERA O EXCEL NA MEMÓRIA
    # ------------------------------------------
    arquivo = BytesIO()

    wb.save(arquivo)

    arquivo.seek(0)

    # ------------------------------------------
    # NOME DO ARQUIVO
    # ------------------------------------------
    nome_arquivo = (

        "relatorio_motos_"

        + data_inicial.strftime("%d-%m-%Y")

        + "_a_"

        + data_final.strftime("%d-%m-%Y")

        + ".xlsx"

    )

    # ------------------------------------------
    # DOWNLOAD
    # ------------------------------------------
    return send_file(

        arquivo,

        as_attachment=True,

        download_name=nome_arquivo,

        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

    )
# ==========================================
# SIMULAR TAG ESPECÍFICA (1 A 10)
# ==========================================
@app.route('/ler/<int:tag>')
def ler_manual(tag):

    if tag < 1 or tag > 10:

        return "TAG inválida."

    moto = Moto.query.filter_by(
        tag_rfid=tag
    ).first()

    if moto is None:

        return f"TAG {tag} não cadastrada."

    moto.local_atual = "MONTAGEM"

    if hasattr(
        moto,
        "status"
    ):

        moto.status = "EM PROCESSO"

    leitura = Leitura(

        tag_rfid=tag,

        setor="MONTAGEM",

        data_hora=datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

    )
    db.session.add(leitura)
    db.session.commit()

    exportar_txt(moto)
    return render_template(
        "resultado.html",
        moto=moto
    )

# ==========================================
# INICIA O SERVIDOR
# ==========================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )