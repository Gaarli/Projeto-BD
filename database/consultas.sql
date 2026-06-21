-- Identificar os Centros de Reciclagem que já processaram TODOS os tipos de materiais 'Críticos'
SELECT 
    CR.CNPJ, 
    CR.Nome
FROM CentroReciclagem CR
JOIN TransporteTriReciclagem TTR ON CR.CNPJ = TTR.CentroReciclagem
JOIN LoteTriado LT ON TTR.codRastreio = LT.TransporteTriReciclagem
JOIN ProcessoReciclagem PR ON LT.LoteColeta = PR.LoteColeta AND LT.pinLoteTri = PR.PinLoteTri
JOIN MaterialProcessado MP ON PR.DataProcessamento = MP.DataProcessamento AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
JOIN Material M ON MP.Material = M.Nome
WHERE M.TipoMaterial = 'Critico'
GROUP BY 
    CR.CNPJ, 
    CR.Nome
HAVING COUNT(DISTINCT M.Nome) = (
    -- Subconsulta que retorna o total de materiais críticos catalogados
    SELECT COUNT(*) 
    FROM Material 
    WHERE TipoMaterial = 'Critico'
);

-- Discussão sobre a eficiência
-- Otimização de Anti-Join (NOT EXISTS):
-- A utilização de NOT EXISTS permite que o otimizador do PostgreSQL
-- empregue estratégias eficientes como Hash Anti Join ou Nested Loop
-- Anti Join. Além disso, a busca é interrompida assim que um registro
-- correspondente é encontrado na tabela LoteTriado, evitando leituras
-- desnecessárias e reduzindo o custo de processamento e I/O.

-- Uso Direto de Chaves (Índices Físicos):
-- Os relacionamentos entre as tabelas LoteColeta, TransporteColetaTri
-- e Transporte são realizados por meio de chaves primárias e estrangeiras
-- (IdLote e codRastreio). Como essas colunas normalmente possuem índices
-- B-Tree, os acessos e cruzamentos são executados de forma eficiente,
-- mantendo bom desempenho mesmo em bases com grande volume de registros.

-- Identificar Lotes de Coleta que já chegaram a um Centro de Triagem, 
-- mas ainda não foram desmembrados em Lotes Triados.
SELECT 
    LC.IdLote,
    LC.DataColeta,
    TCT.CentroTriagem,
    T.DataChegada
FROM LoteColeta LC
-- Garante que o lote foi embarcado em um transporte de coleta para triagem
JOIN TransporteColetaTri TCT ON LC.Transporte = TCT.codRastreio
-- Traz os dados genéricos do transporte, como a data de chegada
JOIN Transporte T ON TCT.codRastreio = T.codRastreio
-- Filtra apenas os lotes que NÃO possuem registros correspondentes na tabela LoteTriado
WHERE NOT EXISTS (
    SELECT 1 
    FROM LoteTriado LT 
    WHERE LT.LoteColeta = LC.IdLote
);

-- Discussão sobre eficiência
-- Uso de CTEs (Cláusula WITH):
-- A CTE VolumePorCentro cria um conjunto intermediário de resultados que
-- pode ser otimizado pelo PostgreSQL por meio de inlining ou materialização,
-- conforme a estratégia mais eficiente definida pelo otimizador. Dessa forma,
-- os dados agregados são calculados uma única vez e reutilizados nas etapas
-- subsequentes da consulta.

-- Ausência de Subconsultas Correlacionadas:
-- A consulta evita recálculos repetitivos da média para cada registro
-- analisado. O valor retornado por AVG(VolumeTotal) é obtido uma única vez
-- após a agregação, permitindo que a filtragem final seja executada de forma
-- eficiente sobre o conjunto de dados já processado.

-- Agregação via Hash Aggregate:
-- A combinação de SUM(LT.PesoExato) com GROUP BY sobre identificadores
-- compactos, como CNPJ, permite ao PostgreSQL utilizar operações de
-- Hash Aggregate em memória, reduzindo a necessidade de ordenações em disco
-- e melhorando o desempenho da etapa de agregação.

-- Calcula o volume total processado por centro e filtra os que estão acima da média nacional
WITH VolumePorCentro AS (
    SELECT 
        CR.CNPJ,
        CR.Nome,
        CR.LicencaAmbiental,
        SUM(LT.PesoExato) AS VolumeTotal
    FROM CentroReciclagem CR
    JOIN TransporteTriReciclagem TTR ON CR.CNPJ = TTR.CentroReciclagem
    JOIN LoteTriado LT ON TTR.codRastreio = LT.TransporteTriReciclagem
    WHERE CR.LicencaAmbiental IS NOT NULL 
    GROUP BY CR.CNPJ, CR.Nome, CR.LicencaAmbiental
)
SELECT 
    CNPJ,
    Nome,
    LicencaAmbiental,
    VolumeTotal
FROM VolumePorCentro
WHERE VolumeTotal > (SELECT AVG(VolumeTotal) FROM VolumePorCentro);

-- Discussão sobre a eficiência:
-- Uso de CTE (Common Table Expression):
-- A cláusula WITH define um conjunto intermediário de resultados que pode
-- ser reutilizado ao longo da consulta. Dessa forma, o PostgreSQL realiza
-- a agregação dos volumes por centro apenas uma vez, aproveitando esse
-- resultado para os cálculos e filtros subsequentes.

-- Eliminação de Subconsultas Correlacionadas:
-- O cálculo da média é executado de forma global, retornando um único valor
-- escalar. Essa abordagem evita recálculos para cada linha processada,
-- reduzindo o custo computacional da consulta.

-- Agregação em Memória:
-- A operação GROUP BY sobre identificadores como CNPJ permite ao PostgreSQL
-- utilizar mecanismos de agregação em memória, como Hash Aggregate,
-- minimizando operações de ordenação em disco e melhorando o desempenho
-- no processamento dos dados agregados.


-- Identificar os pontos de coleta que forneceram dispositivos que geraram um material específico
SELECT DISTINCT 
    PC.Rua, 
    PC.Cidade, 
    PC.CEP, 
    PC.Estado
FROM PontoColeta PC
JOIN LoteColeta LC 
    ON PC.Rua = LC.Rua AND PC.Cidade = LC.Cidade AND PC.CEP = LC.CEP AND PC.Estado = LC.Estado
JOIN ProcessoReciclagem PR 
    ON LC.IdLote = PR.LoteColeta
JOIN MaterialProcessado MP 
    ON PR.DataProcessamento = MP.DataProcessamento AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
WHERE MP.Material = 'Cobre'; -- O parâmetro do material é injetado aqui

-- Discussão sobre a eficiência
-- Salto de Tabelas (Bypass):
-- A estrutura de relacionamentos permite conectar diretamente o processo
-- de reciclagem ao lote de coleta original por meio das chaves já existentes,
-- reduzindo a quantidade de junções necessárias e simplificando o plano
-- de execução da consulta.

-- Filtro Antecipado:
-- A condição de filtragem pelo material é aplicada nas etapas iniciais
-- da execução, diminuindo o conjunto de registros que participa das
-- operações de junção subsequentes e reduzindo o consumo de memória
-- e processamento.

-- Operador DISTINCT:
-- A utilização de DISTINCT elimina ocorrências duplicadas resultantes
-- de múltiplos relacionamentos envolvendo o mesmo ponto de coleta.
-- Isso reduz o volume de dados retornado ao cliente e evita redundâncias
-- no resultado final da consulta.

-- Calcula o tempo médio em dias das viagens de coleta para triagem por transportadora
SELECT 
    Tr.CNPJ,
    Tr.Nome,
    ROUND(AVG(T.DataChegada - T.DataEnvio), 2) AS MediaTempoDias
FROM Transportadora Tr
JOIN Transporte T ON Tr.CNPJ = T.Transportadora
JOIN TransporteColetaTri TCT ON T.codRastreio = TCT.codRastreio
GROUP BY 
    Tr.CNPJ, 
    Tr.Nome;

-- Observação sobre a eficiência
-- Filtro Implícito por Junção (Join):
-- Em vez de utilizar uma cláusula WHERE para filtrar o tipo de transporte,
-- o INNER JOIN direto com a tabela especialista TransporteColetaTri atua
-- como um filtro natural e indexado. Dessa forma, o SGBD processa apenas
-- os registros relacionados à etapa logística de coleta e triagem.

-- Aritmética Direta de Datas:
-- O PostgreSQL realiza a subtração entre colunas do tipo DATE de forma
-- nativa e otimizada, retornando diretamente a diferença em dias, sem a
-- necessidade de funções adicionais como EXTRACT ou conversões de formato.

-- Agregação Otimizada:
-- Ao agrupar pelos atributos textuais de identificação (CNPJ e Nome),
-- o PostgreSQL pode utilizar operações de HashAggregate em memória para
-- calcular a função AVG(), reduzindo acessos ao disco e melhorando o
-- desempenho da agregação.