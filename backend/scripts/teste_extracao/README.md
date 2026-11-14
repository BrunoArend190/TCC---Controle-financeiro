# Teste de extração (Seção 3.7.7 e Quadro 16 do relatório)

Avalia a extração do sistema (a mesma função `extrair` usada pela API) com 24 comprovantes **fictícios**:
8 comprovantes (supermercado, farmácia, posto, restaurante, padaria, cinema, conta de energia e clínica)
em 3 condições cada.

- `limpo`: imagem nítida, como um comprovante digital.
- `foto`: foto simulada, com fundo, rotação, desfoque e ruído.
- `baixa_resolucao`: imagem reduzida a 35% do tamanho.

| Arquivo | Conteúdo |
|---|---|
| `gerar_comprovantes.py` | Gera as imagens e o `gabarito.json`. A semente é fixa, então as imagens saem sempre iguais (usa fontes do Windows). |
| `medir.py` | Roda a extração em cada imagem e compara valor, data, estabelecimento e categoria com o gabarito. Mede o tempo de cada leitura (a primeira com o modelo descarregado) e a memória da GPU. |
| `comprovantes/` | As 24 imagens e o `gabarito.json` usados no teste do relatório. |
| `resultados/` | Resultado da execução de 14/11/2026 (`resultados.json` e a saída do terminal em `saida.txt`). |

## Como rodar

Na pasta `backend`, com o Ollama aberto:

```
.venv/Scripts/python.exe scripts/teste_extracao/gerar_comprovantes.py
.venv/Scripts/python.exe scripts/teste_extracao/medir.py > scripts/teste_extracao/resultados/saida.txt
```

O primeiro comando é opcional, pois as imagens já estão em `comprovantes/`. O segundo sobrescreve os resultados
registrados. Os tempos dependem da GPU: os do relatório foram medidos na GPU do computador de desenvolvimento.
