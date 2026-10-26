import os
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

TEMPLATE_DIR = os.path.join("templates", "docx")
os.makedirs(TEMPLATE_DIR, exist_ok=True)

LOGO_PATH = os.path.join(TEMPLATE_DIR, "logo_perso.png")


def ajuster_marges_page(doc):
  """Réduit les marges de la page A4 pour faire remonter le contenu."""
  for section in doc.sections:
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    # Ajout du pied de page officiel
    footer = section.footer
    p_footer = (
        footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    )
    p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_footer = p_footer.add_run(
        "Atelier Mobile Mécanique Générale — Adresse : Zone du PK9 derrière le"
        " lycée Classique, BP 129\n"
        "Tél. : (+241) 62.70.55.62 / 77.93.98.66 — N° RCCM :"
        " GA-LBV-01-2020-A10-02435 — N° NIF : 315548 R\n"
        "UBA N° : 80901600302 — Capital : 2.000.000 F CFA — Site Internet :"
        " mobileateliermou.wixsite.com/website"
    )
    run_footer.font.name = "Times New Roman"
    run_footer.font.size = Pt(8.5)
    run_footer.font.color.rgb = RGBColor(80, 80, 80)


def ajouter_logo_et_en_tete(doc):
  """Logo à gauche et uniquement la Date à droite."""
  header_table = doc.add_table(rows=1, cols=2)
  header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
  header_table.autofit = False

  cell_left, cell_right = header_table.rows[0].cells
  cell_left.width = Inches(3.5)
  cell_right.width = Inches(3.0)

  p_left = cell_left.paragraphs[0]
  p_left.paragraph_format.space_before = Pt(0)
  p_left.paragraph_format.space_after = Pt(0)

  if os.path.exists(LOGO_PATH):
    p_left.add_run().add_picture(LOGO_PATH, width=Inches(1.8))
  else:
    p_left.add_run("[VOTRE LOGO]").bold = True

  p_right = cell_right.paragraphs[0]
  p_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
  p_right.paragraph_format.space_before = Pt(0)
  p_right.paragraph_format.space_after = Pt(0)

  run_date = p_right.add_run("Date : {{ date_facture }}")
  run_date.bold = True


def ajouter_titre_centre(doc):
  """Affiche le titre dynamique (ex: FACTURE N° : 1400500)."""
  p_titre = doc.add_paragraph()
  p_titre.alignment = WD_ALIGN_PARAGRAPH.CENTER
  p_titre.paragraph_format.space_before = Pt(10)
  p_titre.paragraph_format.space_after = Pt(10)

  run_titre = p_titre.add_run("{{ titre_principal }}")
  run_titre.font.size = Pt(18)
  run_titre.font.bold = True
  run_titre.font.color.rgb = RGBColor(31, 78, 121)


def ajouter_bloc_client(doc):
  p = doc.add_paragraph()
  p.paragraph_format.space_before = Pt(6)
  p.paragraph_format.space_after = Pt(4)

  p.add_run("Client : ").bold = True
  p.add_run("{{ client_nom }}\n")
  p.add_run("NIF : ").bold = True
  p.add_run("{{ client_nif }}\n")
  p.add_run("BP : ").bold = True
  p.add_run("{{ client_bp }}\n")
  p.add_run("Ville : ").bold = True
  p.add_run("{{ client_ville }}\n")

  p_obj = doc.add_paragraph()
  p_obj.paragraph_format.space_before = Pt(4)
  p_obj.paragraph_format.space_after = Pt(6)
  p_obj.add_run("Objet : ").bold = True
  p_obj.add_run("{{ objet }}")


def ajouter_bas_de_page_responsable(doc):
  doc.add_paragraph(
      "\nArrêté la présente facture à la somme de : {{ net_en_lettres }}"
  )

  p_resp = doc.add_paragraph()
  p_resp.paragraph_format.space_before = Pt(18)
  p_resp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
  run_resp = p_resp.add_run("Le Responsable\n\n\n")
  run_resp.bold = True
  run_resp.font.size = Pt(12)


def generer_template_service():
  doc = Document()
  ajuster_marges_page(doc)

  ajouter_logo_et_en_tete(doc)
  ajouter_titre_centre(doc)
  ajouter_bloc_client(doc)

  table = doc.add_table(rows=1, cols=4)
  table.style = "Table Grid"

  hdr = table.rows[0].cells
  hdr[0].text = "Désignation"
  hdr[1].text = "Nombre de jours / Période"
  hdr[2].text = "Prix journalier / Taux"
  hdr[3].text = "Prix total"

  row = table.add_row().cells
  row[0].text = "{% for item in prestations %}{{ item.designation }}"
  row[1].text = "{{ item.periode }}"
  row[2].text = "{{ item.taux }}"
  row[3].text = "{{ item.total }}{% endfor %}"

  table.add_row().cells[0].text = "MONTANT TTC"
  table.rows[-1].cells[3].text = "{{ montant_ttc }}"

  r1 = table.add_row().cells
  r1[0].text = (
      "{% if has_prelevement %}Prélèvement ({{ taux_prelevement }}%){% endif %}"
  )
  r1[3].text = "{% if has_prelevement %}{{ prelevement }}{% endif %}"

  r2 = table.add_row().cells
  r2[0].text = "{% if has_avance %}Avance{% endif %}"
  r2[3].text = "{% if has_avance %}{{ avance }}{% endif %}"

  r3 = table.add_row().cells
  r3[0].text = "{% if has_regule %}Régule{% endif %}"
  r3[3].text = "{% if has_regule %}{{ regule }}{% endif %}"

  r4 = table.add_row().cells
  r4[0].text = "{% if has_autre_option %}{{ autre_option_label }}{% endif %}"
  r4[3].text = "{% if has_autre_option %}{{ autre_option_montant }}{% endif %}"

  r_net = table.add_row().cells
  r_net[0].text = "NET À PAYER"
  r_net[3].text = "{{ net_a_payer }}"

  ajouter_bas_de_page_responsable(doc)

  filepath = os.path.join(TEMPLATE_DIR, "Facture_Atelier_Mobile.docx")
  doc.save(filepath)
  print(f"Template Service mis à jour : {filepath}")


def generer_template_produit():
  doc = Document()
  ajuster_marges_page(doc)

  ajouter_logo_et_en_tete(doc)
  ajouter_titre_centre(doc)
  ajouter_bloc_client(doc)

  table = doc.add_table(rows=1, cols=4)
  table.style = "Table Grid"

  hdr = table.rows[0].cells
  hdr[0].text = "Désignation"
  hdr[1].text = "Quantité"
  hdr[2].text = "Prix Unitaire"
  hdr[3].text = "Total HT"

  row = table.add_row().cells
  row[0].text = "{% for item in prestations %}{{ item.designation }}"
  row[1].text = "{{ item.quantite }}"
  row[2].text = "{{ item.prix_unitaire }}"
  row[3].text = "{{ item.total }}{% endfor %}"

  table.add_row().cells[0].text = "MONTANT TTC"
  table.rows[-1].cells[3].text = "{{ montant_ttc }}"

  r1 = table.add_row().cells
  r1[0].text = (
      "{% if has_prelevement %}Prélèvement ({{ taux_prelevement }}%){% endif %}"
  )
  r1[3].text = "{% if has_prelevement %}{{ prelevement }}{% endif %}"

  r2 = table.add_row().cells
  r2[0].text = "{% if has_avance %}Avance{% endif %}"
  r2[3].text = "{% if has_avance %}{{ avance }}{% endif %}"

  r3 = table.add_row().cells
  r3[0].text = "{% if has_regule %}Régule{% endif %}"
  r3[3].text = "{% if has_regule %}{{ regule }}{% endif %}"

  r4 = table.add_row().cells
  r4[0].text = "{% if has_autre_option %}{{ autre_option_label }}{% endif %}"
  r4[3].text = "{% if has_autre_option %}{{ autre_option_montant }}{% endif %}"

  r_net = table.add_row().cells
  r_net[0].text = "NET À PAYER"
  r_net[3].text = "{{ net_a_payer }}"

  ajouter_bas_de_page_responsable(doc)

  filepath = os.path.join(TEMPLATE_DIR, "Facture_Vente_Atelier_Mobile.docx")
  doc.save(filepath)
  print(f"Template Produit mis à jour : {filepath}")


if __name__ == "__main__":
  generer_template_service()
  generer_template_produit()