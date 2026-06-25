-- ==============================================================================
-- Arquivo: dados.sql
-- Descrição: Script de alimentação inicial (povoamento) da base de dados EletroReverso.
-- Requisito: Mínimo de 2 tuplas por tabela, respeitando as restrições de integridade.
-- SGBD: PostgreSQL
--
-- Estratégia de Inserção (Topological Sort): 
-- A ordem dos blocos abaixo foi projetada estritamente de acordo com a hierarquia 
-- das Chaves Estrangeiras (Foreign Keys - FK). Iniciamos pelas "Folhas/Raízes" 
-- (tabelas sem dependências) e avançamos para as tabelas relacionais de junção, 
-- garantindo que nenhuma violação de integridade referencial ocorra durante a carga.
-- ==============================================================================

-- ==============================================================================
-- 1. Inserção nas Tabelas Base (Sem dependência de chaves estrangeiras)
-- Como estas tabelas representam entidades independentes e domínios de referência, 
-- elas devem ser populadas primeiro para servir de base para o resto do sistema.
-- ==============================================================================

-- Categorias de dispositivos eletrônicos
-- Por que: Define o domínio de classificação usado na triagem para separar os lotes.
INSERT INTO Categoria (Nome, Descricao) VALUES 
('Linha Verde', 'Equipamentos de informática, celulares e tablets'),
('Linha Branca', 'Geladeiras, freezers, máquinas de lavar e micro-ondas'),
('Linha Marrom', 'Monitores, televisores e equipamentos de áudio e vídeo');

-- Pontos de Coleta físicos espalhados pelas cidades
-- Por que: Representa a origem geográfica do fluxo de logística reversa. A chave primária 
-- composta (Rua, Cidade, CEP, Estado) será referenciada na criação dos Lotes de Coleta.
INSERT INTO PontoColeta (Rua, Cidade, CEP, Estado, CapacidadeMax) VALUES 
('Av. Trabalhador Sao-carlense, 400', 'Sao Carlos', '13566590', 'SP', 500.00),
('Av. Paulista, 1000', 'Sao Paulo', '01310100', 'SP', 1500.00),
('Praca da Savassi, S/N', 'Belo Horizonte', '30140000', 'MG', 800.00);

-- Centros de Triagem (Responsáveis por separar as categorias)
INSERT INTO CentroTriagem (CNPJ, Nome, Rua, Cidade, CEP, Estado) VALUES 
('11111111000111', 'Triagem Central Interior SC', 'Rua Alfa, 10', 'Sao Carlos', '13560000', 'SP'),
('22222222000122', 'EcoTriagem Capital SP', 'Rua Beta, 20', 'Sao Paulo', '01000000', 'SP');

-- Centros de Reciclagem (Responsáveis pelo refino e processamento, exigem Licença Ambiental)
-- Como: A inserção da Licença Ambiental valida o filtro (IS NOT NULL) utilizado na 
-- consulta de cálculo de volume acima da média nacional.
INSERT INTO CentroReciclagem (CNPJ, Nome, Rua, Cidade, CEP, Estado, LicencaAmbiental) VALUES 
('33333333000133', 'Recicla Tudo Industrial', 'Rua Gama, 30', 'Campinas', '13000000', 'SP', 'LIC-REC-001-SP'),
('44444444000144', 'Metais Verdes Processamento', 'Rua Delta, 40', 'Guarulhos', '07000000', 'SP', 'LIC-REC-002-SP');

-- Transportadoras logísticas
INSERT INTO Transportadora (CNPJ, Nome, NroLicenca) VALUES 
('55555555000155', 'Logistica Reversa Express', 'ANTT-12345'),
('66666666000166', 'EcoTrans Transportes Verdes', 'ANTT-67890');

-- Materiais de referência recuperados durante a reciclagem
-- Por que: Este é um ponto focal para a avaliação. A inclusão intencional dos materiais 
-- 'Litio', 'Cobalto' e 'Neodimio' com TipoMaterial = 'Critico' fornece os dados exatos 
-- necessários para testar e validar o sucesso da consulta de Divisão Relacional (Duplo NOT EXISTS).
INSERT INTO Material (Nome, TipoMaterial) VALUES 
('Cobre', 'Metal Comum'),
('Ouro', 'Metal Precioso'),
('Litio', 'Critico'),
('Cobalto', 'Critico'),
('Neodimio', 'Critico'),
('Plastico ABS', 'Polimero');

-- Organizações de Destino (Compradoras da matéria-prima recuperada)
-- Como: Representa o fim do ciclo (economia circular), fechando a cadeia da rastreabilidade.
INSERT INTO OrganizacaoDestino (CNPJ, Nome) VALUES 
('77777777000177', 'Industria Metalurgica S.A.'),
('88888888000188', 'Plasticos Renovaveis Ltda.');


-- ==============================================================================
-- 2. Inserção nas Tabelas de Nível 1 (Dependem das Tabelas Base)
-- ==============================================================================

-- Catálogo de Dispositivos Eletrônicos
-- Como: Depende da tabela Categoria. Mapeia as especificações teóricas dos produtos.
INSERT INTO DispositivoEletronico (Nome, PesoMedio, Categoria) VALUES 
('Smartphone Generico', 0.20, 'Linha Verde'),
('Notebook 15 polegadas', 2.00, 'Linha Verde'),
('Geladeira 2 Portas', 60.00, 'Linha Branca'),
('Monitor LCD 24 pol', 3.50, 'Linha Marrom');

-- Tabela genérica de Transporte (Superclasse)
-- Por que: Implementa o conceito de Generalização/Especialização no banco de dados.
-- Todas as viagens compartilham atributos comuns (Datas, Placa, Rastreio). A aritmética 
-- entre DataChegada e DataEnvio aqui inserida alimenta o relatório de SLA logístico (Média de Dias).
INSERT INTO Transporte (codRastreio, Transportadora, DataEnvio, DataChegada, Placa, TipoTransporte) VALUES 
('TR-001', '55555555000155', '2026-05-10', '2026-05-10', 'ABC1234', 'Coleta-Tri'),
('TR-002', '66666666000166', '2026-05-15', '2026-05-16', 'XYZ9876', 'Coleta-Tri'),
('TR-003', '55555555000155', '2026-05-20', '2026-05-21', 'ABC1234', 'Tri-Reciclagem'),
('TR-004', '66666666000166', '2026-05-22', '2026-05-23', 'XYZ9876', 'Tri-Reciclagem');


-- ==============================================================================
-- 3. Inserção nas Tabelas de Nível 2 (Especializações de Transporte e Origem)
-- ==============================================================================

-- Transportes Coleta -> Triagem (Subclasse)
-- Por que: Relaciona um código de rastreio genérico diretamente a um Centro de Triagem destino.
INSERT INTO TransporteColetaTri (codRastreio, CentroTriagem) VALUES 
('TR-001', '11111111000111'),
('TR-002', '22222222000122');

-- Transportes Triagem -> Reciclagem (Subclasse)
-- Como: Relaciona o transporte à etapa final (Reciclagem), atrelando o MTR obrigatório.
INSERT INTO TransporteTriReciclagem (codRastreio, CentroReciclagem, MTR) VALUES 
('TR-003', '33333333000133', 'MTR-SP-1001'),
('TR-004', '44444444000144', 'MTR-SP-1002');

-- Lotes de Coleta 
-- Como: Materializa a transição do armazenamento físico (PontoColeta) para a malha 
-- logística (TransporteColetaTri). Esta dependência dupla exige que o ponto e o transporte já existam.
INSERT INTO LoteColeta (IdLote, Rua, Cidade, CEP, Estado, DataColeta, Transporte) VALUES 
(1, 'Av. Trabalhador Sao-carlense, 400', 'Sao Carlos', '13566590', 'SP', '2026-05-08', 'TR-001'),
(2, 'Av. Paulista, 1000', 'Sao Paulo', '01310100', 'SP', '2026-05-12', 'TR-002');


-- ==============================================================================
-- 4. Inserção nas Tabelas de Nível 3 (Detalhes de Lotes e Triagem)
-- ==============================================================================

-- Tabela Associativa: QtdProdutoLote
-- Por que: Resolve o relacionamento N:M entre LoteColeta e DispositivoEletronico. 
-- Descreve a composição interna da carga antes de ela ser processada.
INSERT INTO QtdProdutoLote (Lote, DispositivoEletronico, Quantidade) VALUES 
(1, 'Smartphone Generico', 50),
(1, 'Notebook 15 polegadas', 10),
(2, 'Geladeira 2 Portas', 5),
(2, 'Smartphone Generico', 100);

-- Lotes Triados 
-- Por que: Representa a "bifurcação" física dos materiais. Um único LoteColeta (ex: Lote 2)
-- é dividido em vários PINS de Lotes Triados baseados na categoria, e vinculados ao transporte final.
INSERT INTO LoteTriado (LoteColeta, pinLoteTri, Categoria, PesoExato, DataTriagem, TransporteTriReciclagem) VALUES 
(1, 'PIN-1-VERDE', 'Linha Verde', 30.50, '2026-05-12', 'TR-003'),
(2, 'PIN-2-BRANCA', 'Linha Branca', 305.00, '2026-05-18', 'TR-004'),
(2, 'PIN-2-VERDE', 'Linha Verde', 20.20, '2026-05-18', 'TR-004');


-- ==============================================================================
-- 5. Inserção nas Tabelas de Nível 4 e 5 (Processamento e Destinação de Material)
-- ==============================================================================

-- Processos de Reciclagem realizados sobre os Lotes Triados
-- Como: O uso da Chave Primária Composta (LoteColeta, PinLoteTri) assegura que o 
-- processo só ocorra sobre um Lote Triado válido e específico.
INSERT INTO ProcessoReciclagem (DataProcessamento, TipoDeProcessamento, LoteColeta, PinLoteTri) VALUES 
('2026-05-22', 'Desmontagem Manual', 1, 'PIN-1-VERDE'),
('2026-05-23', 'Refino Quimico', 1, 'PIN-1-VERDE'),
('2026-05-25', 'Trituracao', 2, 'PIN-2-BRANCA');

-- Materiais salvos nos processos e despachados para organizações parceiras
-- Por que: É o nó final da rastreabilidade. Repare que os materiais críticos (Lítio, 
-- Cobalto e Neodímio) foram atrelados ao Lote 1, que passou pelo 'TR-003', direcionado 
-- ao CentroReciclagem '33333333000133'. Isso garante que a Consulta de Divisão Relacional 
-- (Duplo NOT EXISTS) identifique este Centro como o processador completo de Materiais Críticos.
INSERT INTO MaterialProcessado (Material, DataProcessamento, TipoDeProcessamento, QuantidadeObtida, DataDespacho, TipoDestinacao, OrganizacaoDestino) VALUES 
('Cobre', '2026-05-22', 'Desmontagem Manual', 5.00, '2026-05-26', 'Comercializacao', '77777777000177'),
('Litio', '2026-05-23', 'Refino Quimico', 0.50, '2026-05-27', 'Comercializacao', '77777777000177'),
('Cobalto', '2026-05-23', 'Refino Quimico', 0.20, '2026-05-27', 'Comercializacao', '77777777000177'),
('Neodimio', '2026-05-23', 'Refino Quimico', 0.10, '2026-05-27', 'Comercializacao', '77777777000177'),
('Plastico ABS', '2026-05-25', 'Trituracao', 50.00, '2026-05-28', 'Reutilizacao', '88888888000188');