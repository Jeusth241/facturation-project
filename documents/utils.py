import os
from django.conf import settings
from num2words import num2words
from pypdf import PdfReader, PdfWriter
import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}

def generer_pdf_document(document_id):
    from .models import Document
    doc_obj = Document.objects.get(id=document_id)

    temp_pdf = os.path.join(settings.MEDIA_ROOT, f"temp_{doc_obj.id}.pdf")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    # Configuration du document ReportLab
    doc = SimpleDocTemplate(
        temp_pdf,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=60,  # Marge haute augmentée pour faire descendre l'ensemble
        bottomMargin=60
    )

    story = []
    styles = getSampleStyleSheet()
    
    style_titre = ParagraphStyle(
        'TitreDoc',
        parent=styles['Heading1'],
        fontName='Times-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1F4E79'),
        alignment=1, # Centré
        spaceAfter=15
    )
    
    style_texte = ParagraphStyle(
        'TexteNormal',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14
    )

    # Espace additionnel pour positionner le contenu bien au centre sur le filigrane
    story.append(Spacer(1, 25))

    # 1. En-tête : Logo à gauche, Date soulignée à droite
    logo_path = os.path.join(settings.BASE_DIR, "templates", "docx", "logo_perso.png")
    date_doc = getattr(doc_obj, "date_creation", None)
    if date_doc:
        mois_nom = MOIS_FR.get(date_doc.month, "")
        date_formatted = f"{date_doc.day:02d} {mois_nom} {date_doc.year}"
    else:
        date_formatted = ""

    header_data = [
        [
            Paragraph(f'<img src="{logo_path}" width="120" height="50"/>' if os.path.exists(logo_path) else "<b>ATELIER MOBILE</b>", style_texte),
            Paragraph(f"<u><b>Date</b></u> : {date_formatted}", ParagraphStyle('RightDate', parent=style_texte, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[240, 280])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. Titre Principal Dynamique & Souligné
    if hasattr(doc_obj, "get_type_document_display"):
        type_doc_str = doc_obj.get_type_document_display().upper()
    else:
        type_doc_str = str(getattr(doc_obj, "type_document", "FACTURE")).upper()

    if "DEVIS" in type_doc_str:
        titre_principal = f"<u>DEVIS N°</u> : {doc_obj.numero}"
        label_initiateur = "Initiateur du devis"
    elif "LIVRAISON" in type_doc_str or "BON" in type_doc_str:
        titre_principal = f"<u>BON DE LIVRAISON N°</u> : {doc_obj.numero}"
        label_initiateur = "Initiateur du bon de livraison"
    else:
        titre_principal = f"<u>FACTURE N°</u> : {doc_obj.numero}"
        label_initiateur = "Initiateur de la facture"

    story.append(Paragraph(titre_principal, style_titre))
    story.append(Spacer(1, 5))

    # Récupération de l'initiateur
    initiateur_nom = (
        doc_obj.initiateur
        or getattr(doc_obj.user, "get_full_name", lambda: "")()
        or getattr(doc_obj.user, "username", "")
    ).upper()

    # 3. Informations Initiateur & Client dynamiques (avec condition NIF et BP)
    client_obj = getattr(doc_obj, "client", None)
    client_nom = str(client_obj) if client_obj else ""
    
    # Construction dynamique des lignes client
    client_lines = [
        f"<b>{label_initiateur} :</b> {initiateur_nom}",
        f"<b>Client :</b> {client_nom}"
    ]
    
    # Ajout conditionnel du NIF s'il est renseigné et non vide
    if getattr(doc_obj, "nif", None) and str(doc_obj.nif).strip():
        client_lines.append(f"<b>NIF :</b> {doc_obj.nif}")
        
    # Ajout conditionnel de la BP si elle est renseignée et non vide
    if getattr(doc_obj, "bp", None) and str(doc_obj.bp).strip():
        client_lines.append(f"<b>BP :</b> {doc_obj.bp}")
        
    client_lines.append("<b>Ville :</b> Libreville")
    client_lines.append(f"<br/><b>Objet :</b> {doc_obj.objet or ''}")

    client_text = "<br/>".join(client_lines)
    story.append(Paragraph(client_text, style_texte))
    story.append(Spacer(1, 15))

    # 4. Tableau des prestations / produits
    table_data = [["Désignation", "Quantité / Période", "Prix Unitaire / Taux", "Prix total"]]
    
    total_brut = 0
    for ligne in doc_obj.lignes.all():
        qte = ligne.quantite or 0
        pu = ligne.prix_unitaire or 0
        total_ligne = ligne.prix_total or (qte * pu)
        total_brut += total_ligne
        
        qte_str = f"{qte:g}" if qte else (ligne.periode or "")
        pu_str = f"{pu:,.0f}".replace(",", " ") if pu else ""
        tot_str = f"{total_ligne:,.0f} FCFA".replace(",", " ")

        table_data.append([
            Paragraph(ligne.designation or "", style_texte),
            Paragraph(qte_str, style_texte),
            Paragraph(pu_str, ParagraphStyle('R', parent=style_texte, alignment=2)),
            Paragraph(tot_str, ParagraphStyle('R', parent=style_texte, alignment=2))
        ])

    table_data.append(["MONTANT TTC", "", "", f"{total_brut:,.0f} FCFA".replace(",", " ")])

    taux_p = doc_obj.taux_prelevement or 0
    if taux_p > 0:
        montant_p = (total_brut * taux_p) / 100
        table_data.append([f"Prélèvement ({taux_p}%)", "", "", f"-{montant_p:,.0f} FCFA".replace(",", " ")])
        total_brut -= montant_p

    val_avance = doc_obj.avance or 0
    if val_avance > 0:
        table_data.append(["Avance", "", "", f"-{val_avance:,.0f} FCFA".replace(",", " ")])
        total_brut -= val_avance

    val_regule = doc_obj.regule or 0
    if val_regule > 0:
        table_data.append(["Régule", "", "", f"-{val_regule:,.0f} FCFA".replace(",", " ")])
        total_brut -= val_regule

    net_a_payer = total_brut
    table_data.append(["NET À PAYER", "", "", f"{net_a_payer:,.0f} FCFA".replace(",", " ")])

    t = Table(table_data, colWidths=[160, 130, 105, 125])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F2F2F2')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # 5. Arrêté en lettres et Signature
    net_en_lettres = num2words(net_a_payer, lang="fr").capitalize() + " francs FCFA"
    story.append(Paragraph(f"<b>Arrêté la présente facture à la somme de :</b> {net_en_lettres}", style_texte))
    story.append(Spacer(1, 30))

    signature_data = [
        ["", Paragraph("<b>Le Responsable</b>", ParagraphStyle('Resp', parent=style_texte, alignment=2))]
    ]
    sig_table = Table(signature_data, colWidths=[300, 220])
    sig_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(sig_table)

    # Fonction pour dessiner le pied de page centré en bas
    def ajouter_pied_de_page(canvas_obj, doc_instance):
        canvas_obj.saveState()
        canvas_obj.setFont("Times-Roman", 7.5)
        canvas_obj.setFillColor(colors.HexColor("#505050"))
        
        lignes_footer = [
            "Atelier Mobile Mécanique Générale — Adresse : Zone du PK9 derrière le lycée Classique, BP 129",
            "Tél. : (+241) 62.70.55.62 / 77.93.98.66 — N° RCCM : GA-LBV-01-2020-A10-02435 — N° NIF : 315548 R",
            "UBA N° : 80901600302 — Capital : 2.000.000 F CFA — Site Internet : mobileateliermou.wixsite.com/website"
        ]
        
        y_pos = 35
        for ligne in reversed(lignes_footer):
            canvas_obj.drawCentredString(A4[0] / 2.0, y_pos, ligne)
            y_pos += 10
            
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=ajouter_pied_de_page, onLaterPages=ajouter_pied_de_page)

    # 6. Application du filigrane positionné au centre derrière le tableau
    watermark_file = os.path.join(settings.BASE_DIR, "static", "watermark.png")
    if os.path.exists(watermark_file):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        img_width = 420
        img_height = 250
        x = (A4[0] - img_width) / 2
        y = 265  # Ajusté pour caler les véhicules exactement derrière le tableau descendu
        can.drawImage(watermark_file, x, y, width=img_width, height=img_height, mask="auto", preserveAspectRatio=True)
        can.save()
        packet.seek(0)

        watermark_pdf = PdfReader(packet)
        original_pdf = PdfReader(temp_pdf)
        writer = PdfWriter()

        for page in original_pdf.pages:
            background = PdfReader(io.BytesIO(packet.getvalue())).pages[0]
            background.merge_page(page)
            writer.add_page(background)

        with open(temp_pdf, "wb") as f:
            writer.write(f)

    return temp_pdf