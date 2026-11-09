"""Converte um relatório em Markdown no JSON lido por gerar_pdf.py.

Uso:
    python3 md_para_json.py <relatorio.md> <saida.json>
    python3 gerar_pdf.py <saida.json> <saida.pdf>

Só usa a biblioteca padrão do Python 3. Veja o README para o que é suportado.
"""
import json
import os
import re
import sys

# Caracteres que cabem numa linha de título: o gerar_pdf.py não quebra título.
LIMITE_H1 = 33
LIMITE_H2 = 50
CODIFICACAO_PDF = "cp1252"

TITULO = re.compile(r"^(#{1,3})\s+(.*)$")
IMAGEM = re.compile(r"^!\[[^\]]*\]\(<?([^>)]+)>?\)$")
LISTA = re.compile(r"^(\s*)(-|\d+\.)\s+(.*)$")


def limpar(texto):
    """Tira as marcas de negrito e de código e confere que o PDF consegue escrever o texto."""
    limpo = texto.replace("**", "").replace("`", "").strip()
    limpo.encode(CODIFICACAO_PDF)
    return limpo


def itens_de_titulo(tipo, texto):
    """Título longo é dividido no primeiro ' (': o começo vira título e o resto, um parágrafo."""
    limite = LIMITE_H1 if tipo == "h1" else LIMITE_H2
    titulo, separador, complemento = texto.partition(" (")
    if len(texto) <= limite or not separador:
        titulo, complemento = texto, ""
    else:
        complemento = "(" + complemento
    if len(titulo) > limite:
        print(f"Aviso: título com {len(titulo)} caracteres pode passar da margem: {titulo}",
              file=sys.stderr)
    itens = [{"tipo": tipo, "texto": limpar(titulo)}]
    if complemento:
        itens.append({"tipo": "p", "texto": limpar(complemento)})
    return itens


def celulas(linha):
    return [celula.strip() for celula in linha.strip().strip("|").split("|")]


def itens_de_tabela(linhas):
    """O gerar_pdf.py não desenha tabela: cada linha vira 'rótulo: coluna: valor; ...'."""
    cabecalho = celulas(linhas[0])
    itens = []
    for linha in linhas[2:]:
        valores = celulas(linha)
        colunas = [f"{nome}: {valor}" for nome, valor in zip(cabecalho[1:], valores[1:])]
        texto = f"{valores[0]}: " + "; ".join(colunas)
        itens.append({"tipo": "li", "nivel": 1, "texto": limpar(texto)})
    return itens


def item_de_lista(linha):
    indentacao, marcador, texto = LISTA.match(linha).groups()
    if marcador != "-":
        texto = f"{marcador} {texto}"
    nivel = 2 if len(indentacao) >= 2 else 1
    return {"tipo": "li", "nivel": nivel, "texto": limpar(texto)}


class Conversor:
    """Lê o Markdown linha a linha e monta os itens do JSON.

    A imagem vai para o fim da seção: o gerar_pdf.py joga a imagem para a página
    seguinte quando ela não cabe e deixaria o título sozinho no fim da página.
    """

    def __init__(self, linhas):
        self.linhas = linhas
        self.posicao = 0
        self.itens = []
        self.imagens_da_secao = []

    def converter(self):
        while self.posicao < len(self.linhas):
            inicio = self.posicao
            try:
                self._ler_bloco()
            except UnicodeEncodeError as erro:
                sys.exit(f"Linha {inicio + 1}: caractere fora do Windows-1252: "
                         f"{erro.object[erro.start]!r}")
        self._fechar_secao()
        return self.itens

    def _ler_bloco(self):
        linha = self.linhas[self.posicao].rstrip()
        self.posicao += 1
        if not linha or linha == "---":
            return
        if linha.startswith("|"):
            self._ler_tabela(linha)
        elif TITULO.match(linha):
            self._abrir_secao(*TITULO.match(linha).groups())
        elif IMAGEM.match(linha):
            self.imagens_da_secao.append({"tipo": "img", "arquivo": IMAGEM.match(linha).group(1)})
        elif LISTA.match(linha):
            self.itens.append(item_de_lista(linha))
        else:
            self.itens.append({"tipo": "p", "texto": limpar(linha)})

    def _ler_tabela(self, primeira_linha):
        tabela = [primeira_linha]
        while self.posicao < len(self.linhas) and self.linhas[self.posicao].startswith("|"):
            tabela.append(self.linhas[self.posicao].rstrip())
            self.posicao += 1
        self.itens.extend(itens_de_tabela(tabela))

    def _abrir_secao(self, marcas, texto):
        self._fechar_secao()
        self.itens.extend(itens_de_titulo("h1" if len(marcas) == 1 else "h2", texto))

    def _fechar_secao(self):
        self.itens.extend(self.imagens_da_secao)
        self.imagens_da_secao.clear()


def titulo_do_documento(linhas):
    for linha in linhas:
        if linha.startswith("# "):
            return limpar(linha[2:])
    return "Documento"


def ler_linhas(caminho):
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return arquivo.read().splitlines()
    except OSError as erro:
        sys.exit(f"Não consegui ler {caminho}: {erro.strerror}")


def gravar_json(caminho, conteudo):
    try:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(conteudo, arquivo, ensure_ascii=False, indent=1)
    except OSError as erro:
        sys.exit(f"Não consegui gravar {caminho}: {erro.strerror}")


def main():
    if len(sys.argv) != 3:
        sys.exit("Uso: python3 md_para_json.py <relatorio.md> <saida.json>")
    origem, destino = sys.argv[1], sys.argv[2]
    if os.path.exists(destino):
        sys.exit(f"{destino} já existe: apague o arquivo ou escolha outro nome.")
    linhas = ler_linhas(origem)
    itens = Conversor(linhas).converter()
    pasta_do_md = os.path.dirname(os.path.abspath(origem))
    pasta_do_json = os.path.dirname(os.path.abspath(destino))
    gravar_json(destino, {
        "titulo": titulo_do_documento(linhas),
        "pasta_imagens": os.path.relpath(pasta_do_md, pasta_do_json),
        "itens": itens,
    })
    print(f"ok: {len(itens)} itens")


if __name__ == "__main__":
    main()
