TIPO_PROCEDIMENTO_CONSULTA = "consulta"
TIPO_PROCEDIMENTO_AMBULATORIAL = "procedimento-ambulatorial"
TIPO_PROCEDIMENTO_CIRURGIA = "cirurgia"
TIPO_PROCEDIMENTO_ANATOMIA_PATOLOGICA = "anatomia-patologica"
TIPO_PROCEDIMENTO_ALERGOLOGIA = "alergologia"
TIPO_PROCEDIMENTO_ELETROENCEFALOGRAFIA = "eletroencefalografia"
TIPO_PROCEDIMENTO_FISIOTERAPIA = "fisioterapia"
TIPO_PROCEDIMENTO_HEMOTERAPIA = "hemoterapia"
TIPO_PROCEDIMENTO_ENDOSCOPIA_PERORAL = "endoscopia-peroral"
TIPO_PROCEDIMENTO_MEDICINA_NUCLEAR = "medicina-nuclear"
TIPO_PROCEDIMENTO_PATOLOGIA_CLINICA = "patologia-clinica"
TIPO_PROCEDIMENTO_RADIODIAGNOSTICO = "radiodiagnostico"
TIPO_PROCEDIMENTO_RADIOTERAPIA = "radioterapia"
TIPO_PROCEDIMENTO_CARDIOLOGIA = "cardiologia"
TIPO_PROCEDIMENTO_GENETICA = "genetica"
TIPO_PROCEDIMENTO_ENDOSCOPIA_DIGESTIVA = "endoscopia-digestiva"
TIPO_PROCEDIMENTO_TISIOPNEUMOLOGIA = "tisiopneumologia"
TIPO_PROCEDIMENTO_QUIMIOTERAPIA_CANCER = "quimioterapia-cancer"
TIPO_PROCEDIMENTO_ULTRASSONOGRAFIA = "ultrassonografia"
TIPO_PROCEDIMENTO_TOMOGRAFIA_COMPUTADORIZADA = "tomografia-computadorizada"
TIPO_PROCEDIMENTO_RESSONANCIA_MAGNETICA = "ressonancia-magnetica"
TIPO_PROCEDIMENTO_ECOCARDIOGRAMA_DOPPLER = "ecocardiograma-doppler"
TIPO_PROCEDIMENTO_FONOAUDIOLOGIA = "fonoaudiologia"
TIPO_PROCEDIMENTO_EXAMES_ESPECIFICOS = "exames-especificos"
TIPO_PROCEDIMENTO_TESTES_DIAGNOSTICO = "testes-diagnostico"
TIPO_PROCEDIMENTO_OUTROS_DIAGNOSTICOS_TERAPEUTICOS = "outros-diagnosticos-terapeuticos"
TIPO_PROCEDIMENTO_OUTROS = "outros"
TIPO_PROCEDIMENTO_NAO_INFORMADO = "nao-informado"

CODIGOS_TUSS_CONSULTA_EXATOS = {"5001"}
FAIXAS_TUSS_CONSULTA = ((10000000, 19999999),)
CODIGOS_TUSS_VISIVEIS_MEDICO_EXTRAS = {"41301307", "41301471"}
CODIGOS_TUSS_PREVENTIVO = {"41301099", "41301102"}

TIPO_PROCEDIMENTO_LABELS = {
    TIPO_PROCEDIMENTO_CONSULTA: "Consultas",
    TIPO_PROCEDIMENTO_AMBULATORIAL: "Procedimentos ambulatoriais",
    TIPO_PROCEDIMENTO_CIRURGIA: "Cirurgias",
    TIPO_PROCEDIMENTO_ANATOMIA_PATOLOGICA: "Anatomia Patológica",
    TIPO_PROCEDIMENTO_ALERGOLOGIA: "Alergologia",
    TIPO_PROCEDIMENTO_ELETROENCEFALOGRAFIA: "Eletroencefalografia",
    TIPO_PROCEDIMENTO_FISIOTERAPIA: "Fisioterapia",
    TIPO_PROCEDIMENTO_HEMOTERAPIA: "Hemoterapia",
    TIPO_PROCEDIMENTO_ENDOSCOPIA_PERORAL: "Endoscopia Peroral",
    TIPO_PROCEDIMENTO_MEDICINA_NUCLEAR: "Medicina Nuclear",
    TIPO_PROCEDIMENTO_PATOLOGIA_CLINICA: "Patologia Clínica",
    TIPO_PROCEDIMENTO_RADIODIAGNOSTICO: "Radiodiagnóstico",
    TIPO_PROCEDIMENTO_RADIOTERAPIA: "Radioterapia",
    TIPO_PROCEDIMENTO_CARDIOLOGIA: "Cardiologia",
    TIPO_PROCEDIMENTO_GENETICA: "Genética",
    TIPO_PROCEDIMENTO_ENDOSCOPIA_DIGESTIVA: "Endoscopia Digestiva",
    TIPO_PROCEDIMENTO_TISIOPNEUMOLOGIA: "Tisiopneumologia",
    TIPO_PROCEDIMENTO_QUIMIOTERAPIA_CANCER: "Quimioterapia do Câncer",
    TIPO_PROCEDIMENTO_ULTRASSONOGRAFIA: "Ultrassonografia",
    TIPO_PROCEDIMENTO_TOMOGRAFIA_COMPUTADORIZADA: "Tomografia Computadorizada",
    TIPO_PROCEDIMENTO_RESSONANCIA_MAGNETICA: "Ressonância Magnética",
    TIPO_PROCEDIMENTO_ECOCARDIOGRAMA_DOPPLER: "Ecocardiograma com Doppler",
    TIPO_PROCEDIMENTO_FONOAUDIOLOGIA: "Fonoaudiologia",
    TIPO_PROCEDIMENTO_EXAMES_ESPECIFICOS: "Exames Específicos",
    TIPO_PROCEDIMENTO_TESTES_DIAGNOSTICO: "Testes para Diagnósticos",
    TIPO_PROCEDIMENTO_OUTROS_DIAGNOSTICOS_TERAPEUTICOS: "Outros Procedimentos Diagnósticos/Terapêuticos",
    TIPO_PROCEDIMENTO_OUTROS: "Outros",
    TIPO_PROCEDIMENTO_NAO_INFORMADO: "Não informado",
}

TIPOS_PROCEDIMENTO_VALIDOS = set(TIPO_PROCEDIMENTO_LABELS.keys())
TIPOS_PROCEDIMENTO_EXAME = {
    TIPO_PROCEDIMENTO_ALERGOLOGIA,
    TIPO_PROCEDIMENTO_ELETROENCEFALOGRAFIA,
    TIPO_PROCEDIMENTO_FISIOTERAPIA,
    TIPO_PROCEDIMENTO_ENDOSCOPIA_PERORAL,
    TIPO_PROCEDIMENTO_CARDIOLOGIA,
    TIPO_PROCEDIMENTO_GENETICA,
    TIPO_PROCEDIMENTO_ENDOSCOPIA_DIGESTIVA,
    TIPO_PROCEDIMENTO_TISIOPNEUMOLOGIA,
    TIPO_PROCEDIMENTO_ANATOMIA_PATOLOGICA,
    TIPO_PROCEDIMENTO_MEDICINA_NUCLEAR,
    TIPO_PROCEDIMENTO_PATOLOGIA_CLINICA,
    TIPO_PROCEDIMENTO_RADIODIAGNOSTICO,
    TIPO_PROCEDIMENTO_ULTRASSONOGRAFIA,
    TIPO_PROCEDIMENTO_TOMOGRAFIA_COMPUTADORIZADA,
    TIPO_PROCEDIMENTO_RESSONANCIA_MAGNETICA,
    TIPO_PROCEDIMENTO_ECOCARDIOGRAMA_DOPPLER,
    TIPO_PROCEDIMENTO_FONOAUDIOLOGIA,
    TIPO_PROCEDIMENTO_EXAMES_ESPECIFICOS,
    TIPO_PROCEDIMENTO_TESTES_DIAGNOSTICO,
}

CODIGOS_TUSS_ALERGOLOGIA_EXATOS = {
    "40307255",  # IgE, grupo específico
    "40307263",  # IgE, por alérgeno
    "40307905",  # Alérgenos - perfil antigênico
}

CODIGOS_TUSS_TISIOPNEUMOLOGIA_EXATOS = {
    "40101061",  # Ergoespirometria/teste cardiopulmonar de exercício completo
}

CODIGOS_TUSS_ENDOSCOPIA_PERORAL_EXATOS = {
    "40201031",  # Broncoscopia com biópsia transbrônquica
    "40201058",  # Broncoscopia com ou sem aspirado/lavado brônquico
    "40201198",  # Videoendoscopia do esfíncter velo-palatino flexível
    "40201201",  # Videoendoscopia do esfíncter velo-palatino rígida
    "40201210",  # Videoendoscopia naso-sinusal flexível
    "40201228",  # Videoendoscopia naso-sinusal rígida
    "40201236",  # Video-laringo-estroboscopia flexível
    "40201244",  # Video-laringo-estroboscopia rígida
    "40201252",  # Video-faringo-laringoscopia flexível
    "40201260",  # Video-faringo-laringoscopia rígida
    "40201309",  # Avaliação endoscópica da deglutição (FEES)
    "40201325",  # Videoquimografia laríngea
    "40202011",  # Aritenoidectomia microcirúrgica endoscópica
    "40202054",  # Broncoscopia com biópsia transbrônquica com RX
    "40202100",  # Cateter para braquiterapia endobrônquica
    "40202127",  # Prótese traqueal ou brônquica
    "40202151",  # Desobstrução brônquica com laser/eletrocautério
    "40202160",  # Desobstrução brônquica por broncoaspiração
    "40202178",  # Dilatação laringo-traqueo-brônquica
    "40202364",  # Laringoscopia com microscopia
    "40202372",  # Laringoscopia com retirada de corpo estranho
    "40202399",  # Laringoscopia/traqueoscopia com exérese
    "40202429",  # Laringoscopia/traqueoscopia diagnóstica
    "40202437",  # Laringoscopia/traqueoscopia diagnóstica com aparelho flexível
    "40202445",  # Laringoscopia/traqueoscopia para intubação
    "40202488",  # Nasofibrolaringoscopia diagnóstica
    "40202585",  # Retirada de corpo estranho no brônquio
    "40202593",  # Retirada de tumor/papiloma por broncoscopia
    "40202623",  # Traqueostomia por punção percutânea
    "40202631",  # Tratamento endoscópico de hemoptise
    "40202763",  # Laringoscopia/traqueoscopia com laser
}

CODIGOS_TUSS_QUIMIOTERAPIA_CANCER_EXATOS = {
    "40813908",  # Quimioterapia por cateter de tumor de cabeça e pescoço
    "40813924",  # Quimioterapia por cateter intra-arterial
}

CODIGOS_TUSS_ECOCARDIOGRAMA_DOPPLER_EXATOS = {
    "40901050",
    "40901068",
    "40901076",
    "40901084",
    "40901092",
    "40901106",
    "40902072",
    "40902080",
}

CODIGOS_TUSS_FONOAUDIOLOGIA_EXATOS = {
    "40103013",
    "40103048",
    "40103064",
    "40103072",
    "40103080",
    "40103099",
    "40103102",
    "40103110",
    "40103153",
    "40103161",
    "40103269",
    "40103285",
    "40103404",
    "40103412",
    "40103420",
    "40103439",
    "40103455",
    "40103463",
    "40103480",
    "40103498",
    "40103501",
    "40103552",
    "40103579",
    "40103641",
    "40103650",
    "40103668",
    "40103676",
    "40103722",
    "40103749",
    "40103765",
}

CODIGOS_TUSS_EXAMES_ESPECIFICOS_EXATOS = {
    "40103021",
    "40103030",
    "40103137",
    "40103242",
    "40103250",
    "40103447",
    "40103633",
}

CODIGOS_TUSS_TIPOS_EXATOS = {
    **{codigo: TIPO_PROCEDIMENTO_ALERGOLOGIA for codigo in CODIGOS_TUSS_ALERGOLOGIA_EXATOS},
    **{codigo: TIPO_PROCEDIMENTO_TISIOPNEUMOLOGIA for codigo in CODIGOS_TUSS_TISIOPNEUMOLOGIA_EXATOS},
    **{codigo: TIPO_PROCEDIMENTO_ENDOSCOPIA_PERORAL for codigo in CODIGOS_TUSS_ENDOSCOPIA_PERORAL_EXATOS},
    **{codigo: TIPO_PROCEDIMENTO_QUIMIOTERAPIA_CANCER for codigo in CODIGOS_TUSS_QUIMIOTERAPIA_CANCER_EXATOS},
    **{codigo: TIPO_PROCEDIMENTO_ECOCARDIOGRAMA_DOPPLER for codigo in CODIGOS_TUSS_ECOCARDIOGRAMA_DOPPLER_EXATOS},
    **{codigo: TIPO_PROCEDIMENTO_FONOAUDIOLOGIA for codigo in CODIGOS_TUSS_FONOAUDIOLOGIA_EXATOS},
    **{codigo: TIPO_PROCEDIMENTO_EXAMES_ESPECIFICOS for codigo in CODIGOS_TUSS_EXAMES_ESPECIFICOS_EXATOS},
}

FAIXAS_TUSS_ESPECIFICAS = (
    (40101000, 40101999, TIPO_PROCEDIMENTO_CARDIOLOGIA),
    (40102000, 40102999, TIPO_PROCEDIMENTO_ENDOSCOPIA_DIGESTIVA),
    (40103000, 40103999, TIPO_PROCEDIMENTO_ELETROENCEFALOGRAFIA),
    (40104000, 40104999, TIPO_PROCEDIMENTO_FISIOTERAPIA),
    (40105000, 40105999, TIPO_PROCEDIMENTO_TISIOPNEUMOLOGIA),
    (40810000, 40810999, TIPO_PROCEDIMENTO_CARDIOLOGIA),
)

FAIXAS_TUSS = (
    (*FAIXAS_TUSS_CONSULTA[0], TIPO_PROCEDIMENTO_CONSULTA),
    (20000000, 29999999, TIPO_PROCEDIMENTO_AMBULATORIAL),
    (30000000, 39999999, TIPO_PROCEDIMENTO_CIRURGIA),
    (40100000, 40199999, TIPO_PROCEDIMENTO_ELETROENCEFALOGRAFIA),
    (40200000, 40299999, TIPO_PROCEDIMENTO_ENDOSCOPIA_DIGESTIVA),
    (40300000, 40399999, TIPO_PROCEDIMENTO_PATOLOGIA_CLINICA),
    (40400000, 40499999, TIPO_PROCEDIMENTO_HEMOTERAPIA),
    (40500000, 40599999, TIPO_PROCEDIMENTO_GENETICA),
    (40600000, 40699999, TIPO_PROCEDIMENTO_ANATOMIA_PATOLOGICA),
    (40700000, 40799999, TIPO_PROCEDIMENTO_MEDICINA_NUCLEAR),
    (40800000, 40899999, TIPO_PROCEDIMENTO_RADIODIAGNOSTICO),
    (40900000, 40999999, TIPO_PROCEDIMENTO_ULTRASSONOGRAFIA),
    (41000000, 41099999, TIPO_PROCEDIMENTO_TOMOGRAFIA_COMPUTADORIZADA),
    (41100000, 41199999, TIPO_PROCEDIMENTO_RESSONANCIA_MAGNETICA),
    (41200000, 41299999, TIPO_PROCEDIMENTO_RADIOTERAPIA),
    (41300000, 41399999, TIPO_PROCEDIMENTO_EXAMES_ESPECIFICOS),
    (41400000, 41499999, TIPO_PROCEDIMENTO_TESTES_DIAGNOSTICO),
    (41500000, 41599999, TIPO_PROCEDIMENTO_OUTROS_DIAGNOSTICOS_TERAPEUTICOS),
)


def normalizar_codigo_tuss(valor):
    if valor is None:
        return ""

    texto = str(valor).strip()
    if not texto:
        return ""

    try:
        codigo = int(valor)
    except (TypeError, ValueError):
        try:
            codigo = int(float(texto.replace(",", ".")))
        except (TypeError, ValueError):
            return ""

    if codigo <= 0:
        return ""

    return str(codigo)


def tipo_procedimento_codigo(codigo):
    codigo_texto = normalizar_codigo_tuss(codigo)
    if not codigo_texto:
        return TIPO_PROCEDIMENTO_NAO_INFORMADO

    codigo_int = int(codigo_texto)
    if codigo_texto in CODIGOS_TUSS_CONSULTA_EXATOS:
        return TIPO_PROCEDIMENTO_CONSULTA

    tipo_exato = CODIGOS_TUSS_TIPOS_EXATOS.get(codigo_texto)
    if tipo_exato:
        return tipo_exato

    for inicio, fim, tipo in FAIXAS_TUSS_ESPECIFICAS:
        if inicio <= codigo_int <= fim:
            return tipo

    for inicio, fim, tipo in FAIXAS_TUSS:
        if inicio <= codigo_int <= fim:
            return tipo

    return TIPO_PROCEDIMENTO_OUTROS


def e_tipo_procedimento_exame(tipo):
    return tipo in TIPOS_PROCEDIMENTO_EXAME


def e_procedimento_exame(codigo):
    return e_tipo_procedimento_exame(tipo_procedimento_codigo(codigo))


def codigo_tuss_visivel_medico(codigo):
    codigo_texto = normalizar_codigo_tuss(codigo)
    if not codigo_texto:
        return False

    return (
        codigo_texto in CODIGOS_TUSS_VISIVEIS_MEDICO_EXTRAS
        or tipo_procedimento_codigo(codigo_texto) == TIPO_PROCEDIMENTO_CONSULTA
    )


def label_tipo_procedimento(tipo):
    return TIPO_PROCEDIMENTO_LABELS.get(tipo, TIPO_PROCEDIMENTO_LABELS[TIPO_PROCEDIMENTO_NAO_INFORMADO])


TIPO_ATENDIMENTO_SPDATA_TIPOS = {
    "Anatomia Patologica": TIPO_PROCEDIMENTO_ANATOMIA_PATOLOGICA,
    "Cardiologia": TIPO_PROCEDIMENTO_CARDIOLOGIA,
    "Endoscopia Digestiva": TIPO_PROCEDIMENTO_ENDOSCOPIA_DIGESTIVA,
    "Exames Especificos": TIPO_PROCEDIMENTO_EXAMES_ESPECIFICOS,
    "Medicina Nuclear": TIPO_PROCEDIMENTO_MEDICINA_NUCLEAR,
    "Patologia Clinica": TIPO_PROCEDIMENTO_PATOLOGIA_CLINICA,
    "Radiodiagnostico": TIPO_PROCEDIMENTO_RADIODIAGNOSTICO,
    "Ressonancia Magnetica": TIPO_PROCEDIMENTO_RESSONANCIA_MAGNETICA,
    "Testes para diagnosticos": TIPO_PROCEDIMENTO_TESTES_DIAGNOSTICO,
    "Tomografia Computadorizada": TIPO_PROCEDIMENTO_TOMOGRAFIA_COMPUTADORIZADA,
    "Ultrassonografia": TIPO_PROCEDIMENTO_ULTRASSONOGRAFIA,
}


def tipo_procedimento_tipo_atendimento(nome_tipo_atendimento):
    """
    Agenda de imagem usa codigos internos alfanumericos do SPDATA (USO1, USP1)
    que nao sao TUSS. nesses casos a modalidade vem de TBTABATO.
    """
    if not nome_tipo_atendimento:
        return TIPO_PROCEDIMENTO_NAO_INFORMADO

    nome = str(nome_tipo_atendimento).strip().casefold()
    for chave, tipo in TIPO_ATENDIMENTO_SPDATA_TIPOS.items():
        if chave.casefold() == nome:
            return tipo

    return TIPO_PROCEDIMENTO_NAO_INFORMADO
