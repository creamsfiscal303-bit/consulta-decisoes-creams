PUBLICAÇÃO DO PAINEL CREA-MS NO STREAMLIT COMMUNITY CLOUD

IMPORTANTE: este pacote não inclui a base local de 2.539 documentos, porque ela está no seu computador. Use preparar_publicacao.bat na pasta do projeto local para copiar a base existente sem refazer a coleta.

PREPARAR
1. Copie preparar_publicacao.bat e README_PUBLICACAO.txt para:
   C:\Users\anderson.silva\Desktop\consulta_decisoes_creams_v2
2. Execute preparar_publicacao.bat.
3. Será criada a pasta publicar_streamlit com painel.py, requirements.txt e dados\documentos.csv.
4. Confira o tamanho do CSV. Se for maior que 100 MB, não envie ao GitHub sem otimizar ou usar armazenamento externo.
5. Não envie .venv nem dados\pdfs.

GITHUB
1. Entre em https://github.com/
2. Clique + > New repository.
3. Nome: consulta-decisoes-creams
4. Selecione Public e crie o repositório.
5. Use Add file > Upload files.
6. Envie os arquivos que estão DENTRO de publicar_streamlit (incluindo a pasta dados).
7. Clique Commit changes.

STREAMLIT CLOUD
1. Entre em https://share.streamlit.io/
2. Conecte/autorize o GitHub, se solicitado.
3. Clique Create app.
4. Selecione o repositório consulta-decisoes-creams, branch main e arquivo painel.py.
5. Opcional: escolha um subdomínio disponível.
6. Clique Deploy e aguarde.
7. Em App settings > Sharing, deixe a aplicação pública.
8. Copie o endereço streamlit.app e compartilhe.

CUIDADOS
A aplicação pública pode ser acessada por qualquer pessoa. Não publique dados pessoais ou internos. A base é um índice de documentos públicos e texto extraído; confirme sempre o ato no link oficial. A triagem por palavras-chave não confirma juridicamente que um auto foi anulado.
