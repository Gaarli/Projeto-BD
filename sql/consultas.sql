-- Identificar os Centros de Reciclagem que já processaram TODOS os tipos de materiais 'Críticos'
SELECT CR.CNPJ, CR.Nome, CR.Cidade, CR.Estado
FROM CentroReciclagem CR
WHERE NOT EXISTS (
    SELECT 1 FROM Material M
    WHERE M.TipoMaterial = 'Critico'
    AND NOT EXISTS (
        SELECT 1
        FROM TransporteTriReciclagem TTR
        JOIN LoteTriado          LT  ON TTR.codRastreio       = LT.TransporteTriReciclagem
        JOIN ProcessoReciclagem  PR  ON LT.LoteColeta         = PR.LoteColeta
                                    AND LT.pinLoteTri         = PR.PinLoteTri
        JOIN MaterialProcessado  MP  ON PR.DataProcessamento  = MP.DataProcessamento
                                    AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
        WHERE TTR.CentroReciclagem = CR.CNPJ AND MP.Material = M.Nome
    )
)
ORDER BY CR.Nome
-- consulta 2
SELECT
    LC.IdLote     AS id_lote,
    LC.DataColeta AS data_coleta,
    LC.Cidade     AS cidade_origem,
    CT.Nome       AS centro_triagem,
    T.DataChegada AS chegada_ao_centro
FROM LoteColeta LC
    JOIN TransporteColetaTri TCT
        ON LC.Transporte = TCT.codRastreio
    JOIN Transporte T
        ON TCT.codRastreio = T.codRastreio
    JOIN CentroTriagem CT
        ON TCT.CentroTriagem = CT.CNPJ
    -- Aplicação do OUTER JOIN
    LEFT JOIN LoteTriado LT
        ON LC.IdLote = LT.LoteColeta
-- Filtramos apenas os registros onde o lado direito do JOIN (LoteTriado) veio vazio
WHERE LT.LoteColeta IS NULL
ORDER BY T.DataChegada;



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
ORDER BY VolumeTotal DESC;

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
    PC.Rua    AS rua,
    PC.Cidade AS cidade,
    PC.CEP    AS cep,
    PC.Estado AS estado
FROM PontoColeta PC
    JOIN LoteColeta LC
        ON PC.Rua    = LC.Rua
       AND PC.Cidade = LC.Cidade
       AND PC.CEP    = LC.CEP
       AND PC.Estado = LC.Estado
    JOIN ProcessoReciclagem PR
        ON LC.IdLote = PR.LoteColeta
    JOIN MaterialProcessado MP
        ON PR.DataProcessamento   = MP.DataProcessamento
       AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
WHERE MP.Material = %s -- O parâmetro do material é inserido no lugar de %s, ex.: "Cobre"
ORDER BY
    PC.Cidade,
    PC.Rua;

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
    Tr.CNPJ AS cnpj,
    Tr.Nome AS nome,
    ROUND(
        AVG(T.DataChegada - T.DataEnvio),
        2
    ) AS media_dias
FROM Transportadora Tr
    JOIN Transporte T
        ON Tr.CNPJ = T.Transportadora
    JOIN TransporteColetaTri TCT
        ON T.codRastreio = TCT.codRastreio
GROUP BY
    Tr.CNPJ,
    Tr.Nome
ORDER BY
    media_dias;

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


