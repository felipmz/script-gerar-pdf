# script-gerar-pdf

Gera um PDF simples (títulos, parágrafos, listas e imagens PNG/JPG) a partir de um arquivo JSON, ou de um relatório em Markdown (via `md_para_json.py`). Usa só a biblioteca padrão do Python 3: não precisa instalar nada, nem LibreOffice nem navegador.

## Usar

```bash
python3 gerar_pdf.py exemplo/conteudo.json saida.pdf
```

O script **não sobrescreve**: se `saida.pdf` já existir, ele para com erro. Apague o arquivo ou escolha outro nome.

## Formato do JSON

```json
{
  "titulo": "Título do documento (metadado do PDF)",
  "pasta_imagens": "imagens",
  "itens": [
    {"tipo": "h1", "texto": "Título grande"},
    {"tipo": "h2", "texto": "Subtítulo"},
    {"tipo": "p", "texto": "Parágrafo."},
    {"tipo": "li", "nivel": 1, "texto": "Item de lista"},
    {"tipo": "li", "nivel": 2, "texto": "Subitem"},
    {"tipo": "img", "arquivo": "print.png"}
  ]
}
```

- `tipo`: `h1`, `h2`, `p`, `li` ou `img`.
- `nivel` (só em `li`): `1` ou `2`. Padrão `1`.
- `img`: `arquivo` é o nome da imagem, procurada na pasta do JSON (ou em `pasta_imagens`, relativa à pasta do JSON, se informada). PNG precisa ser RGBA de 8 bits; JPG funciona direto.
- O texto aceita acentos e aspas “curvas”. Caracteres fora do Windows-1252 (como emojis) não são suportados.

## Do Markdown

`md_para_json.py` converte um relatório em Markdown no JSON acima, para não montar o JSON à mão.

```bash
python3 md_para_json.py exemplo/relatorio.md conteudo.json
python3 gerar_pdf.py conteudo.json saida.pdf
```

O que ele entende:

- `#`, `##` e `###` viram títulos (`###` vira o mesmo subtítulo de `##`). O título do PDF vem do primeiro `#`.
- Parágrafos, listas com `-` ou `1.` e uma sublista (recuada com 2 espaços ou mais).
- Imagens `![texto](arquivo.png)`, procuradas na pasta do `.md`.
- Tabelas: o `gerar_pdf.py` não desenha tabela, então cada linha vira um item de lista (`Linha: coluna: valor; coluna: valor`).
- Negrito (`**`) e código (`` ` ``) perdem a marcação.

Detalhes:

- O PDF não quebra título longo. Se o título passa de 33 caracteres (`#`) ou 50 (`##`), ele é dividido no primeiro ` (`: o começo vira o título e o resto, um parágrafo logo abaixo. Se mesmo assim passar da margem, o script avisa.
- As imagens vão para o fim da seção, para o título não ficar sozinho no fim da página.
- Os limites do `gerar_pdf.py` continuam: PNG RGBA de 8 bits (ou JPG) e só Windows-1252. Se achar emoji, seta ou outro caractere fora disso, o conversor para e diz a linha.
- Também não sobrescreve: se o `.json` já existir, ele para com erro.

## Exemplo

- `exemplo/conteudo.json` é um documento de teste, sem imagens, no formato JSON.
- `exemplo/relatorio.md` é o mesmo tipo de teste em Markdown, para o `md_para_json.py`.

## Não suba para este repositório

PDFs gerados e conteúdo real de relatórios. O `.gitignore` já ignora `*.pdf`.
