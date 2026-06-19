-- 1. Tabelas sem chaves estrangeiras (Base)
CREATE TABLE Categoria (
    Nome VARCHAR2(50) NOT NULL,
    Descricao VARCHAR2(255),
    CONSTRAINT PK_Categoria PRIMARY KEY (Nome)
);

CREATE TABLE PontoColeta (
    Rua VARCHAR2(100) NOT NULL,
    Cidade VARCHAR2(50) NOT NULL,
    CEP CHAR(8) NOT NULL,
    Estado CHAR(2) NOT NULL,
    CapacidadeMax NUMBER NOT NULL,
    CONSTRAINT PK_PontoColeta PRIMARY KEY (Rua, Cidade, CEP, Estado)
);

CREATE TABLE CentroTriagem (
    CNPJ CHAR(14) NOT NULL,
    Nome VARCHAR2(100) NOT NULL,
    Rua VARCHAR2(100) NOT NULL,
    Cidade VARCHAR2(50) NOT NULL,
    CEP CHAR(8) NOT NULL,
    Estado CHAR(2) NOT NULL,
    CONSTRAINT PK_CentroTriagem PRIMARY KEY (CNPJ)
);

CREATE TABLE CentroReciclagem (
    CNPJ CHAR(14) NOT NULL,
    Nome VARCHAR2(100) NOT NULL,
    Rua VARCHAR2(100) NOT NULL,
    Cidade VARCHAR2(50) NOT NULL,
    CEP CHAR(8) NOT NULL,
    Estado CHAR(2) NOT NULL,
    LicencaAmbiental VARCHAR2(50) NOT NULL,
    CONSTRAINT PK_CentroReciclagem PRIMARY KEY (CNPJ),
    CONSTRAINT UQ_LicencaAmbiental UNIQUE (LicencaAmbiental)
);

CREATE TABLE Transportadora (
    CNPJ CHAR(14) NOT NULL,
    Nome VARCHAR2(100) NOT NULL,
    NroLicenca VARCHAR2(50) NOT NULL,
    CONSTRAINT PK_Transportadora PRIMARY KEY (CNPJ),
    CONSTRAINT UQ_NroLicenca UNIQUE (NroLicenca)
);

CREATE TABLE Material (
    Nome VARCHAR2(50) NOT NULL,
    TipoMaterial VARCHAR2(50) NOT NULL,
    CONSTRAINT PK_Material PRIMARY KEY (Nome)
);

CREATE TABLE OrganizacaoDestino (
    CNPJ CHAR(14) NOT NULL,
    Nome VARCHAR2(100) NOT NULL,
    CONSTRAINT PK_OrganizacaoDestino PRIMARY KEY (CNPJ)
);

-- 2. Tabelas com dependências Nível 1
CREATE TABLE DispositivoEletronico (
    Nome VARCHAR2(100) NOT NULL,
    PesoMedio NUMBER NOT NULL,
    Categoria VARCHAR2(50) NOT NULL,
    CONSTRAINT PK_DispositivoEletronico PRIMARY KEY (Nome),
    CONSTRAINT FK_Disp_Categoria FOREIGN KEY (Categoria) REFERENCES Categoria(Nome)
);

CREATE TABLE Transporte (
    codRastreio VARCHAR2(50) NOT NULL,
    Transportadora CHAR(14) NOT NULL,
    DataEnvio DATE NOT NULL,
    DataChegada DATE NOT NULL,
    Placa CHAR(7) NOT NULL,
    TipoTransporte VARCHAR2(20) NOT NULL,
    CONSTRAINT PK_Transporte PRIMARY KEY (codRastreio),
    CONSTRAINT FK_Transp_Transportadora FOREIGN KEY (Transportadora) REFERENCES Transportadora(CNPJ)
);

-- 3. Especializações de Transporte e Dependências Nível 2
CREATE TABLE TransporteColetaTri (
    codRastreio VARCHAR2(50) NOT NULL,
    CentroTriagem CHAR(14) NOT NULL,
    CONSTRAINT PK_TransporteColetaTri PRIMARY KEY (codRastreio),
    CONSTRAINT FK_TranspCT_Transporte FOREIGN KEY (codRastreio) REFERENCES Transporte(codRastreio) ON DELETE CASCADE,
    CONSTRAINT FK_TranspCT_Centro FOREIGN KEY (CentroTriagem) REFERENCES CentroTriagem(CNPJ)
);

CREATE TABLE TransporteTriReciclagem (
    codRastreio VARCHAR2(50) NOT NULL,
    CentroReciclagem CHAR(14) NOT NULL,
    MTR VARCHAR2(50) NOT NULL,
    CONSTRAINT PK_TransporteTriReciclagem PRIMARY KEY (codRastreio),
    CONSTRAINT UQ_MTR UNIQUE (MTR),
    CONSTRAINT FK_TranspTR_Transporte FOREIGN KEY (codRastreio) REFERENCES Transporte(codRastreio) ON DELETE CASCADE,
    CONSTRAINT FK_TranspTR_Centro FOREIGN KEY (CentroReciclagem) REFERENCES CentroReciclagem(CNPJ)
);

CREATE TABLE LoteColeta (
    IdLote NUMBER NOT NULL,
    Rua VARCHAR2(100) NOT NULL,
    Cidade VARCHAR2(50) NOT NULL,
    CEP CHAR(8) NOT NULL,
    Estado CHAR(2) NOT NULL,
    DataColeta DATE NOT NULL,
    Transporte VARCHAR2(50),
    CONSTRAINT PK_LoteColeta PRIMARY KEY (IdLote),
    CONSTRAINT FK_Lote_PontoColeta FOREIGN KEY (Rua, Cidade, CEP, Estado) REFERENCES PontoColeta(Rua, Cidade, CEP, Estado),
    CONSTRAINT FK_Lote_Transporte FOREIGN KEY (Transporte) REFERENCES TransporteColetaTri(codRastreio) ON DELETE SET NULL
);

-- 4. Dependências de Lote Coleta (Nível 3)
CREATE TABLE QtdProdutoLote (
    Lote NUMBER NOT NULL,
    DispositivoEletronico VARCHAR2(100) NOT NULL,
    Quantidade NUMBER NOT NULL,
    CONSTRAINT PK_QtdProdutoLote PRIMARY KEY (Lote, DispositivoEletronico),
    CONSTRAINT FK_Qtd_Lote FOREIGN KEY (Lote) REFERENCES LoteColeta(IdLote) ON DELETE CASCADE,
    CONSTRAINT FK_Qtd_Dispositivo FOREIGN KEY (DispositivoEletronico) REFERENCES DispositivoEletronico(Nome)
);

CREATE TABLE LoteTriado (
    LoteColeta NUMBER NOT NULL,
    pinLoteTri VARCHAR2(50) NOT NULL,
    Categoria VARCHAR2(50) NOT NULL,
    PesoExato NUMBER NOT NULL,
    DataTriagem DATE NOT NULL,
    TransporteTriReciclagem VARCHAR2(50),
    CONSTRAINT PK_LoteTriado PRIMARY KEY (LoteColeta, pinLoteTri),
    CONSTRAINT FK_LoteTriado_LoteColeta FOREIGN KEY (LoteColeta) REFERENCES LoteColeta(IdLote) ON DELETE CASCADE,
    CONSTRAINT FK_LoteTriado_Categoria FOREIGN KEY (Categoria) REFERENCES Categoria(Nome),
    CONSTRAINT FK_LoteTriado_Transporte FOREIGN KEY (TransporteTriReciclagem) REFERENCES TransporteTriReciclagem(codRastreio) ON DELETE SET NULL
);

-- 5. Processamento e Materiais (Nível 4 e 5)
CREATE TABLE ProcessoReciclagem (
    DataProcessamento DATE NOT NULL,
    TipoDeProcessamento VARCHAR2(50) NOT NULL,
    LoteColeta NUMBER NOT NULL,
    PinLoteTri VARCHAR2(50) NOT NULL,
    CONSTRAINT PK_ProcessoReciclagem PRIMARY KEY (DataProcessamento, TipoDeProcessamento),
    CONSTRAINT FK_Processo_LoteTriado FOREIGN KEY (LoteColeta, PinLoteTri) REFERENCES LoteTriado(LoteColeta, pinLoteTri) ON DELETE CASCADE
);

CREATE TABLE MaterialProcessado (
    Material VARCHAR2(50) NOT NULL,
    DataProcessamento DATE NOT NULL,
    TipoDeProcessamento VARCHAR2(50) NOT NULL,
    QuantidadeObtida NUMBER NOT NULL,
    DataDespacho DATE,
    TipoDestinacao VARCHAR2(50),
    OrganizacaoDestino CHAR(14) NOT NULL,
    CONSTRAINT PK_MaterialProcessado PRIMARY KEY (Material, DataProcessamento, TipoDeProcessamento),
    CONSTRAINT FK_MatProc_Material FOREIGN KEY (Material) REFERENCES Material(Nome) ON DELETE CASCADE,
    CONSTRAINT FK_MatProc_Processo FOREIGN KEY (DataProcessamento, TipoDeProcessamento) REFERENCES ProcessoReciclagem(DataProcessamento, TipoDeProcessamento) ON DELETE CASCADE,
    CONSTRAINT FK_MatProc_Org FOREIGN KEY (OrganizacaoDestino) REFERENCES OrganizacaoDestino(CNPJ)
);