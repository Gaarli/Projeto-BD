/* =======================================================================================
   CONSULTA 1: DIVISÃO RELACIONAL DE MATERIAIS CRÍTICOS
   
   Justificativa de Negócio:
   Atua como um filtro de certificação e auditoria. Em logística reversa, 
   materiais críticos (ex: Lítio, Cobalto) apresentam alto risco ambiental 
   e valor financeiro. Identificar quais centros processam TODOS esses 
   materiais permite o direcionamento logístico seguro de lotes complexos.
   
   Eficiência (Como e Por que):
   Implementa a Divisão Relacional puramente via duplo NOT EXISTS. 
   Isso ativa a lógica de "curto-circuito" do PostgreSQL: ao encontrar um único
   material que o Centro não processou, ele aborta a verificação daquele Centro,
   poupando I/O. É vastamente superior ao uso de GROUP BY com COUNT(DISTINCT), 
   pois evita a criação de pesadas tabelas temporárias na memória.
======================================================================================= */
-- Identificar os Centros de Reciclagem que já processaram TODOS os tipos de materiais 'Críticos'
SELECT CR.CNPJ, CR.Nome, CR.Cidade, CR.Estado
FROM CentroReciclagem CR
-- O primeiro NOT EXISTS aciona o "curto-circuito": verifica se há algum material crítico que o centro NÃO processou
WHERE NOT EXISTS (
    SELECT 1 FROM Material M
    WHERE M.TipoMaterial = 'Critico'
    -- O segundo NOT EXISTS cruza o histórico de processamento do centro com o material específico avaliado
    AND NOT EXISTS (
        SELECT 1
        FROM TransporteTriReciclagem TTR
        -- Junções em cadeia para mapear o rastreio do transporte até o material final processado
        JOIN LoteTriado          LT  ON TTR.codRastreio       = LT.TransporteTriReciclagem
        JOIN ProcessoReciclagem  PR  ON LT.LoteColeta         = PR.LoteColeta
                                    AND LT.pinLoteTri         = PR.PinLoteTri
        JOIN MaterialProcessado  MP  ON PR.DataProcessamento  = MP.DataProcessamento
                                    AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
        -- Otimização: A restrição de cruzamento ocorre diretamente via chaves estrangeiras, explorando índices
        WHERE TTR.CentroReciclagem = CR.CNPJ AND MP.Material = M.Nome
    )
)
ORDER BY CR.Nome;


/* =======================================================================================
   CONSULTA 2: MONITORAMENTO DE GARGALOS OPERACIONAIS (ANTI-JOIN)
   
   Justificativa de Negócio:
   Monitora Lotes Pendentes. O tempo de pátio em um Centro de Triagem é um KPI
   crucial. Esta consulta é um painel de alerta que revela remessas estagnadas 
   (chegaram, mas não geraram lote triado), permitindo à gestão atuar 
   diretamente nos gargalos operacionais e evitar acúmulo de inventário.
   
   Eficiência (Como e Por que):
   Utiliza a técnica de Anti-Join (LEFT JOIN + IS NULL). O planejador do PostgreSQL 
   reconhece essa estrutura e frequentemente aplica um algoritmo de "Hash Anti Join",
   resolvendo a exclusão de dados em uma varredura veloz. Elimina os riscos de 
   produtos cartesianos comuns no uso de subqueries com NOT IN.
======================================================================================= */
-- consulta 2
SELECT
    LC.IdLote     AS id_lote,
    LC.DataColeta AS data_coleta,
    LC.Cidade     AS cidade_origem,
    CT.Nome       AS centro_triagem,
    T.DataChegada AS chegada_ao_centro
FROM LoteColeta LC
    -- As junções iniciais constroem a trilha de dados do lote cru até a sua chegada no centro de triagem
    JOIN TransporteColetaTri TCT
        ON LC.Transporte = TCT.codRastreio
    JOIN Transporte T
        ON TCT.codRastreio = T.codRastreio
    JOIN CentroTriagem CT
        ON TCT.CentroTriagem = CT.CNPJ
    -- Aplicação do OUTER JOIN: Força o banco a trazer todos os lotes, incluindo os que não têm correspondência na triagem
    LEFT JOIN LoteTriado LT
        ON LC.IdLote = LT.LoteColeta
-- Filtramos apenas os registros onde o lado direito do JOIN (LoteTriado) veio vazio, isolando os atrasos (Anti-Join)
WHERE LT.LoteColeta IS NULL
ORDER BY T.DataChegada;


/* =======================================================================================
   CONSULTA 3: DESEMPENHO E CAPACIDADE DOS CENTROS DE RECICLAGEM
   
   Justificativa de Negócio:
   Ranqueamento logístico e compliance. Filtra estritamente os centros regulares 
   (com Licença Ambiental) e identifica parceiros de alta performance (acima da 
   média nacional de volume processado). Fundamental para direcionar investimentos 
   e renegociar contratos na cadeia de reciclagem.
======================================================================================= */
-- Calcula o volume total processado por centro e filtra os que estão acima da média nacional
WITH VolumePorCentro AS (
    -- A CTE atua como uma tabela virtual em memória, pré-agrupando os volumes para evitar duplo processamento
    SELECT 
        CR.CNPJ,
        CR.Nome,
        CR.LicencaAmbiental,
        SUM(LT.PesoExato) AS VolumeTotal
    FROM CentroReciclagem CR
    JOIN TransporteTriReciclagem TTR ON CR.CNPJ = TTR.CentroReciclagem
    JOIN LoteTriado LT ON TTR.codRastreio = LT.TransporteTriReciclagem
    -- O filtro IS NOT NULL antecipado descarta entidades irregulares antes da agregação, reduzindo a carga de memória
    WHERE CR.LicencaAmbiental IS NOT NULL 
    GROUP BY CR.CNPJ, CR.Nome, CR.LicencaAmbiental
)
SELECT 
    CNPJ,
    Nome,
    LicencaAmbiental,
    VolumeTotal
FROM VolumePorCentro
-- A média escalar é calculada varrendo a CTE de forma leve, eliminando a necessidade de subconsultas correlacionadas pesadas
WHERE VolumeTotal > (SELECT AVG(VolumeTotal) FROM VolumePorCentro)
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


/* =======================================================================================
   CONSULTA 4: RASTREABILIDADE GEOGRÁFICA DE MATERIAIS (MINERAÇÃO URBANA)
   
   Justificativa de Negócio:
   Inteligência geográfica para captação de resíduos. Se o valor de um metal
   como Cobre ou Ouro subir, a gestão consegue mapear exatamente quais cidades
   e bairros fornecem dispositivos ricos nestes elementos, otimizando o ROI 
   (Retorno sobre Investimento) das campanhas de coleta.
======================================================================================= */
-- Identificar os pontos de coleta que forneceram dispositivos que geraram um material específico
SELECT DISTINCT
    PC.Rua    AS rua,
    PC.Cidade AS cidade,
    PC.CEP    AS cep,
    PC.Estado AS estado
FROM PontoColeta PC
    -- A junção por chaves compostas (Rua, Cidade, CEP, Estado) garante uso de Index Scans para alta velocidade de busca
    JOIN LoteColeta LC
        ON PC.Rua    = LC.Rua
       AND PC.Cidade = LC.Cidade
       AND PC.CEP    = LC.CEP
       AND PC.Estado = LC.Estado
    -- Salto estrutural (Bypass): Conecta o lote bruto à reciclagem diretamente, pulando intermediários como centros de triagem
    JOIN ProcessoReciclagem PR
        ON LC.IdLote = PR.LoteColeta
    JOIN MaterialProcessado MP
        ON PR.DataProcessamento   = MP.DataProcessamento
       AND PR.TipoDeProcessamento = MP.TipoDeProcessamento
-- A injeção parametrizada (%s) resolve o filtro antes das junções complexas, aplicando a redução de dados no momento mais oportuno do plano
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


/* =======================================================================================
   CONSULTA 5: AUDITORIA DE SLA DE TRANSPORTE (TEMPO MÉDIO DE TRÂNSITO)
   
   Justificativa de Negócio:
   Rastreia a velocidade logística da frota parceira. Medir o tempo de trânsito
   dos lotes permite identificar transportadoras ineficientes, reduzindo os 
   riscos de sinistros em rodovias (roubo/acidente com material tóxico) e 
   garantindo previsibilidade para a chegada dos lotes no centro de triagem.
======================================================================================= */
-- Calcula o tempo médio em dias das viagens de coleta para triagem por transportadora
SELECT
    Tr.CNPJ AS cnpj,
    Tr.Nome AS nome,
    -- A matemática de datas (DataChegada - DataEnvio) extrai o tempo em dias nativamente, sem funções externas custosas
    ROUND(
        AVG(T.DataChegada - T.DataEnvio),
        2
    ) AS media_dias
FROM Transportadora Tr
    JOIN Transporte T
        ON Tr.CNPJ = T.Transportadora
    -- O INNER JOIN com a tabela especializada TransporteColetaTri atua de forma implícita filtrando tipos incorretos de transporte
    JOIN TransporteColetaTri TCT
        ON T.codRastreio = TCT.codRastreio
-- O SGBD utiliza o HashAggregate nesta etapa para agrupar em memória os identificadores textuais, evitando sobrecarga no disco
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