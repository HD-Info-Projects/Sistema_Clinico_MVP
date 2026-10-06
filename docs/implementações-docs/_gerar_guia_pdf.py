from pathlib import Path
import textwrap

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "imagens"
PDF_PATH = BASE_DIR / "guia-novas-funcionalidades-exames-laboratoriais-assistente-medico.pdf"


def font_path():
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


FONT = font_path()


def load_font(size, bold=False):
    if FONT:
        bold_path = FONT.with_name("DejaVuSans-Bold.ttf")
        path = bold_path if bold and bold_path.exists() else FONT
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_text(draw, xy, text, font, fill="#111827", max_width=None, line_spacing=8):
    x, y = xy
    if max_width is None:
        draw.text((x, y), text, font=font, fill=fill)
        return y + font.size + line_spacing

    avg = max(font.size * 0.55, 1)
    width_chars = max(int(max_width / avg), 12)
    lines = textwrap.wrap(text, width=width_chars)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_spacing
    return y


def create_canvas(title, subtitle):
    image = Image.new("RGB", (1600, 900), "#f3f4f6")
    draw = ImageDraw.Draw(image)
    title_font = load_font(44, bold=True)
    subtitle_font = load_font(24)
    small_font = load_font(20)

    rounded_rectangle(draw, (40, 35, 1560, 145), 28, "#0f766e")
    draw.text((78, 58), title, font=title_font, fill="white")
    draw.text((80, 112), subtitle, font=subtitle_font, fill="#d1fae5")
    draw.text((1270, 112), "Dados fictícios", font=small_font, fill="#ccfbf1")
    return image, draw


def draw_badge(draw, xy, text, color="#0ea5e9", fill="#e0f2fe"):
    x, y = xy
    font = load_font(20, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 34
    h = 38
    rounded_rectangle(draw, (x, y, x + w, y + h), 18, fill, color)
    draw.text((x + 17, y + 8), text, font=font, fill=color)
    return x + w + 10


def image_filter():
    image, draw = create_canvas(
        "Retenção de Exames",
        "Filtro Tipo de Exame com a opção Exames Laboratoriais"
    )
    label_font = load_font(22, bold=True)
    text_font = load_font(22)
    option_font = load_font(24)

    rounded_rectangle(draw, (70, 185, 1530, 820), 26, "white", "#e5e7eb", 2)
    draw.text((105, 220), "Filtros", font=load_font(30, bold=True), fill="#111827")

    fields = [
        ("Ano", "2026", 105, 285),
        ("Mês início", "Outubro", 390, 285),
        ("Convênio", "Todos", 675, 285),
        ("Status", "Todos", 960, 285),
    ]
    for label, value, x, y in fields:
        draw.text((x, y), label, font=label_font, fill="#374151")
        rounded_rectangle(draw, (x, y + 38, x + 235, y + 98), 14, "#f9fafb", "#d1d5db", 2)
        draw.text((x + 18, y + 55), value, font=text_font, fill="#111827")

    x, y = 105, 435
    draw.text((x, y), "Tipo de Exame", font=label_font, fill="#374151")
    rounded_rectangle(draw, (x, y + 38, x + 500, y + 98), 14, "#eef2ff", "#6366f1", 3)
    draw.text((x + 18, y + 55), "Exames Laboratoriais", font=text_font, fill="#111827")
    draw.text((x + 455, y + 55), "⌄", font=load_font(28, bold=True), fill="#4f46e5")

    rounded_rectangle(draw, (x, y + 106, x + 500, y + 370), 18, "white", "#c7d2fe", 2)
    options = ["Todos", "Exames Laboratoriais", "Cardiologia", "Radiodiagnóstico", "Ultrassonografia"]
    for index, option in enumerate(options):
        oy = y + 128 + index * 47
        if option == "Exames Laboratoriais":
            rounded_rectangle(draw, (x + 12, oy - 6, x + 488, oy + 36), 12, "#e0e7ff")
            draw.text((x + 28, oy), option, font=option_font, fill="#3730a3")
        else:
            draw.text((x + 28, oy), option, font=option_font, fill="#374151")

    rounded_rectangle(draw, (675, 458, 1260, 805), 22, "#ecfeff", "#06b6d4", 2)
    draw.text((715, 500), "O que este filtro traz?", font=load_font(30, bold=True), fill="#0e7490")
    notes = [
        "Anatomia Patológica",
        "Hemoterapia",
        "Patologia Clínica",
        "Genética",
    ]
    ny = 565
    for note in notes:
        draw.ellipse((720, ny + 8, 736, ny + 24), fill="#0891b2")
        draw.text((755, ny), note, font=load_font(25), fill="#111827")
        ny += 50

    rounded_rectangle(draw, (1300, 690, 1490, 755), 18, "#16a34a")
    draw.text((1328, 710), "Aplicar Filtros", font=load_font(23, bold=True), fill="white")
    image.save(IMAGES_DIR / "01-filtro-exames-laboratoriais.png")


def image_result():
    image, draw = create_canvas(
        "Resultado do Filtro",
        "Tabela mantém o tipo específico do exame"
    )
    rounded_rectangle(draw, (70, 185, 1530, 820), 26, "white", "#e5e7eb", 2)
    draw_badge(draw, (105, 220), "Filtro ativo: Exames Laboratoriais", "#4338ca", "#e0e7ff")

    headers = ["Paciente", "Exame", "Tipo de Exame", "Status"]
    widths = [300, 430, 330, 220]
    x0, y0 = 105, 305
    x = x0
    for header, width in zip(headers, widths):
        rounded_rectangle(draw, (x, y0, x + width, y0 + 58), 8, "#f9fafb", "#e5e7eb")
        draw.text((x + 16, y0 + 17), header, font=load_font(22, bold=True), fill="#374151")
        x += width

    rows = [
        ["Paciente exemplo 1", "Hemograma completo", "Patologia Clínica", "Pendente"],
        ["Paciente exemplo 2", "Tipagem sanguínea", "Hemoterapia", "Atendido"],
        ["Paciente exemplo 3", "Biópsia", "Anatomia Patológica", "Pendente"],
        ["Paciente exemplo 4", "Painel genético", "Genética", "Faltou"],
    ]
    y = y0 + 58
    colors = {"Pendente": "#ca8a04", "Atendido": "#16a34a", "Faltou": "#dc2626"}
    for row in rows:
        x = x0
        for index, (value, width) in enumerate(zip(row, widths)):
            fill = "#ffffff" if (y // 58) % 2 == 0 else "#f8fafc"
            rounded_rectangle(draw, (x, y, x + width, y + 68), 6, fill, "#e5e7eb")
            if index == 3:
                draw_badge(draw, (x + 16, y + 15), value, colors[value], "#fefce8" if value == "Pendente" else "#dcfce7" if value == "Atendido" else "#fee2e2")
            else:
                draw.text((x + 16, y + 22), value, font=load_font(21), fill="#111827")
            x += width
        y += 68

    rounded_rectangle(draw, (105, 635, 1450, 760), 22, "#f0fdf4", "#22c55e", 2)
    draw.text((140, 670), "Mensagem para treinamento:", font=load_font(26, bold=True), fill="#166534")
    draw.text((140, 712), "O filtro agrupa, mas a coluna continua detalhando Patologia Clínica, Hemoterapia, Anatomia Patológica ou Genética.", font=load_font(23), fill="#14532d")
    image.save(IMAGES_DIR / "02-resultado-exames-laboratoriais.png")


def image_assistant_form():
    image, draw = create_canvas(
        "Cadastro de Assistente Médico",
        "Admin > Assistentes"
    )
    rounded_rectangle(draw, (70, 185, 1530, 820), 26, "white", "#e5e7eb", 2)
    draw.text((105, 220), "Novo assistente", font=load_font(34, bold=True), fill="#111827")

    fields = [
        ("Nome completo", "Assistente exemplo", 105, 295, 520),
        ("E-mail de acesso", "assistente.exemplo@clinica.com", 680, 295, 620),
        ("Unidade", "Clínica principal", 105, 430, 520),
        ("Perfil de acesso", "Assistente", 680, 430, 300),
    ]
    for label, value, x, y, width in fields:
        draw.text((x, y), label, font=load_font(22, bold=True), fill="#374151")
        rounded_rectangle(draw, (x, y + 38, x + width, y + 98), 14, "#f9fafb", "#d1d5db", 2)
        draw.text((x + 18, y + 55), value, font=load_font(22), fill="#111827")

    x, y = 105, 570
    draw.text((x, y), "Médico que o assistente vai auxiliar", font=load_font(24, bold=True), fill="#374151")
    rounded_rectangle(draw, (x, y + 42, x + 890, y + 108), 16, "#eef2ff", "#6366f1", 3)
    draw.text((x + 20, y + 62), "Dra. Mariana Almeida - CRM 12345", font=load_font(24), fill="#111827")

    rounded_rectangle(draw, (1050, 610, 1450, 760), 22, "#fff7ed", "#f97316", 2)
    draw.text((1085, 640), "Atenção", font=load_font(30, bold=True), fill="#c2410c")
    draw_text(draw, (1085, 690), "Sem médico vinculado, o assistente não consegue visualizar corretamente a agenda do médico.", load_font(22), "#7c2d12", 320)
    image.save(IMAGES_DIR / "03-cadastro-assistente-medico.png")


def image_assistant_dashboard():
    image, draw = create_canvas(
        "Dashboard do Assistente Médico",
        "Acompanhar, chamar e atualizar status"
    )
    rounded_rectangle(draw, (70, 185, 1530, 820), 26, "white", "#e5e7eb", 2)
    draw.text((105, 220), "Bom dia, Assistente exemplo", font=load_font(34, bold=True), fill="#111827")
    draw_badge(draw, (1120, 220), "Sala: Consultório 2", "#0f766e", "#ccfbf1")

    cards = [("Pendentes", "8", "#f59e0b"), ("Atendidos", "14", "#16a34a"), ("Faltantes", "2", "#dc2626")]
    x = 105
    for title, value, color in cards:
        rounded_rectangle(draw, (x, 295, x + 380, 420), 22, "#f9fafb", "#e5e7eb", 2)
        draw.ellipse((x + 28, 322, x + 50, 344), fill=color)
        draw.text((x + 70, 315), title, font=load_font(24, bold=True), fill="#374151")
        draw.text((x + 70, 355), value, font=load_font(40, bold=True), fill="#111827")
        x += 430

    rounded_rectangle(draw, (105, 475, 1450, 760), 20, "#ffffff", "#e5e7eb", 2)
    headers = ["Horário", "Paciente", "Tipo", "Status", "Ações"]
    xs = [130, 285, 675, 950, 1135]
    for header, x in zip(headers, xs):
        draw.text((x, 505), header, font=load_font(22, bold=True), fill="#374151")

    rows = [
        ("08:20", "Paciente exemplo 1", "Ultrassonografia", "Pendente"),
        ("09:00", "Paciente exemplo 2", "Patologia Clínica", "Pendente"),
    ]
    y = 560
    for horario, paciente, tipo, status in rows:
        draw.text((130, y), horario, font=load_font(21), fill="#111827")
        draw.text((285, y), paciente, font=load_font(21), fill="#111827")
        draw_badge(draw, (675, y - 8), tipo, "#2563eb", "#dbeafe")
        draw_badge(draw, (950, y - 8), status, "#ca8a04", "#fef9c3")
        ax = draw_badge(draw, (1135, y - 8), "Chamar", "#0f766e", "#ccfbf1")
        ax = draw_badge(draw, (ax, y - 8), "Atendido", "#16a34a", "#dcfce7")
        draw_badge(draw, (ax, y - 8), "Faltou", "#dc2626", "#fee2e2")
        y += 78

    image.save(IMAGES_DIR / "04-dashboard-assistente-medico.png")


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, "Guia de Novas Funcionalidades - Sistema Clínico MVP", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-14)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, f"Página {self.page_no()}", align="C")


def add_wrapped(pdf, text, size=11, style="", color=(31, 41, 55), line_h=6):
    pdf.set_font("DejaVu", style, size)
    pdf.set_text_color(*color)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, line_h, text)
    pdf.ln(1)


def add_title(pdf, text):
    pdf.set_font("DejaVu", "B", 18)
    pdf.set_text_color(15, 118, 110)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def add_section(pdf, text):
    pdf.ln(4)
    pdf.set_font("DejaVu", "B", 14)
    pdf.set_text_color(17, 24, 39)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 8, text)
    pdf.ln(1)


def add_bullets(pdf, items):
    for item in items:
        pdf.set_font("DejaVu", "", 11)
        pdf.set_text_color(31, 41, 55)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, f"- {item}")
    pdf.ln(2)


def add_steps(pdf, items):
    for idx, item in enumerate(items, start=1):
        pdf.set_font("DejaVu", "", 11)
        pdf.set_text_color(31, 41, 55)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, f"{idx}. {item}")
    pdf.ln(2)


def add_image(pdf, filename, caption):
    path = IMAGES_DIR / filename
    pdf.ln(2)
    pdf.image(str(path), x=15, w=180)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(0, 5, caption, align="C")
    pdf.ln(2)


def build_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

    pdf.add_page()
    pdf.set_fill_color(15, 118, 110)
    pdf.rect(0, 0, 210, 55, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 22)
    pdf.set_xy(15, 18)
    pdf.multi_cell(180, 10, "Guia de Novas Funcionalidades")
    pdf.set_font("DejaVu", "", 13)
    pdf.set_x(15)
    pdf.multi_cell(180, 7, "Exames Laboratoriais e Assistente Médico")
    pdf.set_y(70)
    add_wrapped(pdf, "Sistema Clínico MVP", 13, "B", (17, 24, 39))
    add_wrapped(pdf, "Público-alvo: funcionários responsáveis por treinar médicos, assistentes e equipe operacional.")
    add_wrapped(pdf, "Data: 05 de outubro de 2026")
    add_wrapped(pdf, "Branch de referência: main")
    add_wrapped(pdf, "Observação: as imagens deste guia são ilustrativas e usam dados fictícios. Não representam dados reais de pacientes.", 10, "", (100, 116, 139))

    pdf.add_page()
    add_title(pdf, "1. Objetivo")
    add_wrapped(pdf, "Este guia orienta a equipe interna sobre duas funcionalidades: o agrupamento de Exames Laboratoriais no filtro Tipo de Exame da retenção de exames e o fluxo operacional do perfil Assistente Médico no dashboard.")
    add_bullets(pdf, [
        "Exames Laboratoriais: facilita localizar exames de Anatomia Patológica, Hemoterapia, Patologia Clínica e Genética em um único filtro.",
        "Assistente Médico: permite que um funcionário acompanhe a agenda de exames vinculada a um médico e execute ações operacionais no dashboard.",
    ])

    add_title(pdf, "2. Exames Laboratoriais no Filtro Tipo de Exame")
    add_section(pdf, "2.1 Onde acessar")
    add_wrapped(pdf, "Caminho: Recepção > Retenção de Exames. Rota técnica: /recepcao/retencao-exames.")
    add_section(pdf, "2.2 O que mudou")
    add_bullets(pdf, [
        "Os números e traços foram removidos dos nomes exibidos.",
        "O filtro Tipo de Exame agora possui a opção Exames Laboratoriais.",
        "Ao selecionar Exames Laboratoriais, o sistema traz apenas Anatomia Patológica, Hemoterapia, Patologia Clínica e Genética.",
        "A tabela continua exibindo o tipo específico de cada exame.",
    ])
    add_image(pdf, "01-filtro-exames-laboratoriais.png", "Figura 1 - Seleção da opção Exames Laboratoriais no filtro Tipo de Exame.")
    add_section(pdf, "2.3 Como ensinar o uso")
    add_steps(pdf, [
        "Entrar em Recepção > Retenção de Exames.",
        "Conferir o período e os demais filtros, se necessário.",
        "Abrir o campo Tipo de Exame.",
        "Selecionar Exames Laboratoriais.",
        "Aplicar os filtros.",
        "Conferir que a tabela mostra apenas os quatro tipos laboratoriais.",
        "Reforçar que a coluna Tipo de Exame continua mostrando o tipo específico.",
    ])
    add_image(pdf, "02-resultado-exames-laboratoriais.png", "Figura 2 - Resultado filtrado com tipo específico preservado na tabela.")

    pdf.add_page()
    add_title(pdf, "3. Assistente Médico")
    add_section(pdf, "3.1 Objetivo")
    add_wrapped(pdf, "O perfil Assistente permite que um funcionário acompanhe a agenda de exames vinculada a um médico específico e execute ações operacionais no dashboard, sem assumir o atendimento clínico completo do médico.")
    add_section(pdf, "3.2 Cadastro e vínculo")
    add_wrapped(pdf, "Caminho para cadastro: Admin > Assistentes. Rota técnica: /admin/assistentes.")
    add_bullets(pdf, [
        "O administrador cadastra o assistente com usuário, senha, unidade e perfil Assistente.",
        "O campo Médico que o assistente vai auxiliar é obrigatório para o fluxo funcionar corretamente.",
        "O assistente deve estar vinculado ao médico correto antes do treinamento operacional.",
    ])
    add_image(pdf, "03-cadastro-assistente-medico.png", "Figura 3 - Cadastro do assistente com vínculo ao médico auxiliado.")
    add_section(pdf, "3.3 Acesso e uso no dashboard")
    add_wrapped(pdf, "Após o login, o assistente acessa o dashboard operacional em /dashboard. O sistema carrega a agenda de exames relacionada ao médico vinculado e à unidade ativa.")
    add_bullets(pdf, [
        "Ver pacientes/exames do médico vinculado.",
        "Acompanhar indicadores do dia, como pendentes, atendidos e faltantes.",
        "Chamar paciente para a sala ou consultório configurado.",
        "Marcar item como Atendido.",
        "Marcar item como Faltou.",
        "Visualizar status e tipo de atendimento/exame.",
    ])
    add_image(pdf, "04-dashboard-assistente-medico.png", "Figura 4 - Dashboard operacional do assistente médico.")

    pdf.add_page()
    add_title(pdf, "4. Roteiro de Treinamento")
    add_section(pdf, "4.1 Exames Laboratoriais")
    add_wrapped(pdf, "Fala sugerida: Na tela de retenção de exames, os exames laboratoriais agora foram agrupados em um único filtro chamado Exames Laboratoriais. Quando selecionamos essa opção, o sistema traz somente Anatomia Patológica, Hemoterapia, Patologia Clínica e Genética. A tabela continua mostrando o tipo real do exame, para manter a informação detalhada.")
    add_section(pdf, "4.2 Assistente Médico")
    add_wrapped(pdf, "Fala sugerida: O assistente médico entra com o próprio usuário e acessa o dashboard operacional. Ele acompanha a agenda de exames do médico ao qual foi vinculado, pode chamar paciente, marcar como atendido ou faltou, mas não substitui o médico no atendimento clínico.")
    add_section(pdf, "4.3 Cuidados importantes")
    add_bullets(pdf, [
        "Verificar a unidade ativa antes de operar a agenda.",
        "Confirmar se o médico vinculado ao assistente está correto.",
        "Não compartilhar senha entre médico e assistente.",
        "Usar Faltou apenas quando houver confirmação operacional.",
        "Usar Atendido apenas após a conclusão do fluxo correspondente.",
    ])
    add_section(pdf, "4.4 Perguntas frequentes")
    add_bullets(pdf, [
        "Exames Laboratoriais inclui Anatomia Patológica, Hemoterapia, Patologia Clínica e Genética.",
        "A tabela não troca o tipo por Exames Laboratoriais; ela preserva o tipo específico.",
        "O assistente vê a agenda relacionada ao médico vinculado no cadastro.",
        "Se a agenda não aparecer, verificar unidade ativa, vínculo com médico e CRM/configuração do médico.",
    ])

    add_title(pdf, "5. Evidência técnica")
    add_bullets(pdf, [
        "frontend/app/pages/recepcao/retencao-exames.vue",
        "frontend/app/utils/tuss.ts",
        "backend/src/services/retencao_exames_service.py",
        "backend/src/utils/tuss.py",
        "frontend/app/pages/dashboard.vue",
        "frontend/app/pages/admin/assistentes.vue",
        "frontend/app/components/UsuarioFormModal.vue",
        "frontend/app/middleware/auth.global.ts",
        "backend/src/modules/agenda/routes.py",
        "backend/src/services/spdata_atendimentos_service.py",
    ])
    add_wrapped(pdf, "Validações executadas na implementação: testes backend focados passaram e o typecheck do frontend passou.", 10, "", (100, 116, 139))

    pdf.output(PDF_PATH)


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_filter()
    image_result()
    image_assistant_form()
    image_assistant_dashboard()
    build_pdf()
    print(PDF_PATH)


if __name__ == "__main__":
    main()
