# script-gerar-pdf

Gera um PDF simples (títulos, parágrafos, listas e imagens PNG/JPG) a partir de um arquivo JSON. Usa só a biblioteca padrão do Python 3: não precisa instalar nada, nem LibreOffice nem navegador.

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

## Exemplo

`exemplo/conteudo.json` é um documento de teste, sem imagens.

## Não suba para este repositório

PDFs gerados e conteúdo real de relatórios. O `.gitignore` já ignora `*.pdf`.
