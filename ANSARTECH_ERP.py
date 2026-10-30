#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   ANSARTECH ERP PRO V2.2 - VERSION CORRIGÉE                  ║
║           Gestion Intégrée: Stock, Ventes, Factures, Comptabilité            ║
║     Solution Professionnelle avec PDF Factures & Stock Professionnel          ║
║                         VERSION OPTIMISÉE 2025                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from typing import Dict, Optional
import os

# ════════════════════════════════════════════════════════════════════════════
# THÈME MODERNE PROFESSIONNEL
# ════════════════════════════════════════════════════════════════════════════

class ModernTheme:
    PRIMARY_DARK = "#0D47A1"
    PRIMARY = "#1976D2"
    PRIMARY_LIGHT = "#42A5F5"
    ACCENT = "#FF6B35"
    SUCCESS = "#28A745"
    WARNING = "#FFC107"
    DANGER = "#DC3545"
    INFO = "#17A2B8"
    
    BG_DARK = "#0F1419"
    BG_LIGHT = "#F8F9FA"
    CARD_BG = "#FFFFFF"
    BORDER = "#E0E0E0"
    TEXT_DARK = "#212121"
    TEXT_LIGHT = "#6C757D"
    TEXT_WHITE = "#FFFFFF"
    HOVER_BG = "#F5F5F5"

# ════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ════════════════════════════════════════════════════════════════════════════

class Database:
    """Gestionnaire de base de données SQLite"""
    
    def __init__(self, db_path: str = "ansartech_erp_v2.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # Table des entreprises
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                country TEXT,
                phone TEXT,
                email TEXT,
                siret TEXT,
                vat_number TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'admin',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des produits - AMÉLIORÉE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                reference TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                unit_price REAL NOT NULL DEFAULT 0,
                vat_rate REAL DEFAULT 18,
                stock_quantity INTEGER DEFAULT 0,
                stock_min INTEGER DEFAULT 5,
                stock_max INTEGER DEFAULT 100,
                category TEXT,
                supplier TEXT,
                last_restock_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des mouvements de stock
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                movement_type TEXT,
                quantity INTEGER,
                reason TEXT,
                reference_doc TEXT,
                created_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        
        # Table des clients
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                country TEXT,
                tax_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des factures - AMÉLIORÉE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_address TEXT,
                customer_email TEXT,
                customer_phone TEXT,
                total_ht REAL DEFAULT 0,
                total_vat REAL DEFAULT 0,
                total_ttc REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'pending',
                invoice_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        """)
        
        # Table des lignes de facture
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_lines (
                id INTEGER PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price_ht REAL NOT NULL,
                vat_rate REAL NOT NULL,
                line_total_ht REAL NOT NULL,
                line_vat REAL NOT NULL,
                line_total_ttc REAL NOT NULL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        
        conn.commit()
        conn.close()

# ════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR PDF CORRIGÉ
# ════════════════════════════════════════════════════════════════════════════

class InvoicePDFGenerator:
    """Générateur de factures PDF professionnel avec gestion d'erreurs robuste"""
    
    @staticmethod
    def generate_invoice_pdf(filename: str, invoice_data: Dict, company_info: Dict):
        """
        Génère une facture PDF complète
        
        Args:
            filename: Chemin du fichier PDF à créer
            invoice_data: Dict contenant les données de facture
            company_info: Dict contenant les infos entreprise
            
        Returns:
            True si succès
            
        Raises:
            Exception avec message d'erreur détaillé
        """
        try:
            # Validation des données
            if not filename:
                raise ValueError("Le nom du fichier est requis")
            if not invoice_data or not invoice_data.get('invoice_number'):
                raise ValueError("Les données de facture incomplètes")
            if not invoice_data.get('customer_name'):
                raise ValueError("Le nom du client est requis")
            
            # Créer le document
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # Créer des styles personnalisés
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor("#1976D2"),
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=11,
                textColor=colors.HexColor("#0D47A1"),
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )
            
            normal_style = styles['Normal']
            
            # ===== EN-TÊTE =====
            story.append(Paragraph("FACTURE", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Informations entreprise et client
            company_text = f"""
<b>{company_info.get('name', 'ANSARTECH')}</b><br/>
{company_info.get('address', '')}<br/>
{company_info.get('city', '')}<br/>
Tél: {company_info.get('phone', '')}<br/>
Email: {company_info.get('email', '')}
            """
            
            client_text = f"""
<b>CLIENT:</b><br/>
<b>{invoice_data.get('customer_name', 'Client')}</b><br/>
{invoice_data.get('customer_address', '')}<br/>
{invoice_data.get('customer_email', '')}<br/>
{invoice_data.get('customer_phone', '')}
            """
            
            info_data = [
                [Paragraph(company_text, normal_style), Paragraph(client_text, normal_style)]
            ]
            info_table = Table(info_data, colWidths=[3*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('BORDER', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Détails facture
            story.append(Paragraph("DÉTAILS FACTURE", heading_style))
            
            details_data = [
                ['Numéro:', invoice_data.get('invoice_number', 'N/A'), 'Date:', invoice_data.get('invoice_date', '')],
                ['Statut:', str(invoice_data.get('payment_status', 'pending')).upper(), 'Échéance:', invoice_data.get('due_date', '')]
            ]
            
            details_table = Table(details_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E3F2FD")),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 0.2*inch))
            
            # ===== LIGNES DE FACTURE =====
            story.append(Paragraph("ARTICLES", heading_style))
            
            lines_data = [['Description', 'Qty', 'P.U. HT', 'TVA', 'Total HT']]
            
            for line in invoice_data.get('lines', []):
                try:
                    qty = float(line.get('quantity', 0))
                    price = float(line.get('unit_price_ht', 0))
                    vat = float(line.get('vat_rate', 0))
                    total = float(line.get('line_total_ht', 0))
                    
                    lines_data.append([
                        str(line.get('description', '')),
                        f"{qty:.2f}",
                        f"{price:.0f}",
                        f"{vat:.0f}%",
                        f"{total:.0f}"
                    ])
                except (ValueError, TypeError):
                    continue
            
            # Si pas de lignes, ajouter une ligne vide
            if len(lines_data) == 1:
                lines_data.append(['', '0', '0', '0%', '0'])
            
            lines_table = Table(lines_data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 0.7*inch, 1.2*inch])
            lines_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1976D2")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")])
            ]))
            story.append(lines_table)
            story.append(Spacer(1, 0.2*inch))
            
            # ===== RÉSUMÉ FINANCIER =====
            ht = float(invoice_data.get('total_ht', 0))
            tva = float(invoice_data.get('total_vat', 0))
            ttc = float(invoice_data.get('total_ttc', 0))
            
            summary_data = [
                ['Total HT:', f"{ht:,.0f} GNF"],
                ['TVA:', f"{tva:,.0f} GNF"],
                ['TOTAL TTC:', f"{ttc:,.0f} GNF"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 2), 10),
                ('FONTSIZE', (0, 2), (-1, 2), 12),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#E3F2FD")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Notes
            if invoice_data.get('notes'):
                story.append(Paragraph("NOTES", heading_style))
                notes = str(invoice_data['notes']).replace('\n', '<br/>')
                story.append(Paragraph(notes, normal_style))
            
            # Pied de page
            story.append(Spacer(1, 0.3*inch))
            footer_text = "Merci pour votre confiance | Facture générée le " + datetime.now().strftime("%d/%m/%Y %H:%M")
            story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
            
            # Construction du PDF
            doc.build(story)
            return True
            
        except FileNotFoundError as e:
            raise Exception(f"Erreur d'accès fichier: {str(e)}")
        except PermissionError as e:
            raise Exception(f"Permissions insuffisantes: {str(e)}")
        except Exception as e:
            raise Exception(f"Erreur génération PDF: {str(e)}")

# ════════════════════════════════════════════════════════════════════════════
# BOUTON MODERNE
# ════════════════════════════════════════════════════════════════════════════

class ModernButton(tk.Button):
    def __init__(self, parent, text, command=None, style_type="primary", **kwargs):
        colors_map = {
            "primary": (ModernTheme.PRIMARY, ModernTheme.TEXT_WHITE),
            "accent": (ModernTheme.ACCENT, ModernTheme.TEXT_WHITE),
            "success": (ModernTheme.SUCCESS, ModernTheme.TEXT_WHITE),
            "danger": (ModernTheme.DANGER, ModernTheme.TEXT_WHITE),
            "info": (ModernTheme.INFO, ModernTheme.TEXT_WHITE),
        }
        bg_color, fg_color = colors_map.get(style_type, colors_map["primary"])
        
        super().__init__(
            parent, text=text, command=command,
            bg=bg_color, fg=fg_color,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, padx=15, pady=8,
            cursor="hand2", **kwargs
        )
        
        self.bind("<Enter>", lambda e: self.config(relief=tk.RAISED))
        self.bind("<Leave>", lambda e: self.config(relief=tk.FLAT))

# ════════════════════════════════════════════════════════════════════════════
# MODULE GESTION DU STOCK - COMPLÈTEMENT REFONDÉ
# ════════════════════════════════════════════════════════════════════════════

class StockManagementModule:
    """Module de gestion du stock professionnel"""
    
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.selected_product_id = None
        self.build_ui()
    
    def build_ui(self):
        """Construit l'interface de gestion du stock"""
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ===== SECTION AJOUT PRODUIT =====
        add_product_frame = ttk.LabelFrame(main_frame, text="➕ AJOUTER UN PRODUIT", padding=10)
        add_product_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Référence produit
        ttk.Label(add_product_frame, text="Référence:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ref_entry = ttk.Entry(add_product_frame, width=25)
        self.ref_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Nom produit
        ttk.Label(add_product_frame, text="Nom du Produit:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.name_entry = ttk.Entry(add_product_frame, width=25)
        self.name_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Catégorie
        ttk.Label(add_product_frame, text="Catégorie:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.category_entry = ttk.Entry(add_product_frame, width=25)
        self.category_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Fournisseur
        ttk.Label(add_product_frame, text="Fournisseur:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.supplier_entry = ttk.Entry(add_product_frame, width=25)
        self.supplier_entry.grid(row=1, column=3, padx=5, pady=5)
        
        # Quantité en stock
        ttk.Label(add_product_frame, text="Quantité Stock:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(add_product_frame, width=15)
        self.quantity_entry.insert(0, "0")
        self.quantity_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Prix unitaire
        ttk.Label(add_product_frame, text="Prix Unitaire (GNF):").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.price_entry = ttk.Entry(add_product_frame, width=15)
        self.price_entry.insert(0, "0")
        self.price_entry.grid(row=2, column=3, padx=5, pady=5)
        
        # TVA
        ttk.Label(add_product_frame, text="TVA (%):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.vat_entry = ttk.Entry(add_product_frame, width=15)
        self.vat_entry.insert(0, "18")
        self.vat_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Stock minimum
        ttk.Label(add_product_frame, text="Stock Min:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.stock_min_entry = ttk.Entry(add_product_frame, width=15)
        self.stock_min_entry.insert(0, "5")
        self.stock_min_entry.grid(row=3, column=3, padx=5, pady=5)
        
        # Stock maximum
        ttk.Label(add_product_frame, text="Stock Max:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.stock_max_entry = ttk.Entry(add_product_frame, width=15)
        self.stock_max_entry.insert(0, "100")
        self.stock_max_entry.grid(row=4, column=1, padx=5, pady=5)
        
        # Description
        ttk.Label(add_product_frame, text="Description:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
        self.desc_entry = ttk.Entry(add_product_frame, width=25)
        self.desc_entry.grid(row=4, column=3, padx=5, pady=5)
        
        # Bouton ajouter
        button_frame = ttk.Frame(add_product_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=15)
        ModernButton(button_frame, "✓ AJOUTER PRODUIT", command=self.add_product, style_type="success").pack()
        
        # ===== SECTION TABLEAU DES PRODUITS =====
        table_frame = ttk.LabelFrame(main_frame, text="📊 INVENTAIRE DES PRODUITS", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview avec colonnes améliorées
        self.tree = ttk.Treeview(
            table_frame,
            columns=('ref', 'nom', 'categorie', 'quantite', 'prix_unitaire', 'prix_total', 'stock_min', 'stock_max', 'fournisseur'),
            height=12,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)
        
        # Configuration des colonnes
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.column('ref', anchor=tk.W, width=80, heading='Référence')
        self.tree.column('nom', anchor=tk.W, width=120, heading='Nom Produit')
        self.tree.column('categorie', anchor=tk.W, width=90, heading='Catégorie')
        self.tree.column('quantite', anchor=tk.CENTER, width=80, heading='Quantité')
        self.tree.column('prix_unitaire', anchor=tk.RIGHT, width=100, heading='P.U. (GNF)')
        self.tree.column('prix_total', anchor=tk.RIGHT, width=110, heading='Valeur Total')
        self.tree.column('stock_min', anchor=tk.CENTER, width=70, heading='Min')
        self.tree.column('stock_max', anchor=tk.CENTER, width=70, heading='Max')
        self.tree.column('fournisseur', anchor=tk.W, width=100, heading='Fournisseur')
        
        # En-tête
        self.tree.heading('#0', text='', anchor=tk.W)
        self.tree.heading('ref', text='Référence', anchor=tk.W)
        self.tree.heading('nom', text='Nom Produit', anchor=tk.W)
        self.tree.heading('categorie', text='Catégorie', anchor=tk.W)
        self.tree.heading('quantite', text='Quantité', anchor=tk.CENTER)
        self.tree.heading('prix_unitaire', text='P.U. (GNF)', anchor=tk.RIGHT)
        self.tree.heading('prix_total', text='Valeur Total', anchor=tk.RIGHT)
        self.tree.heading('stock_min', text='Min', anchor=tk.CENTER)
        self.tree.heading('stock_max', text='Max', anchor=tk.CENTER)
        self.tree.heading('fournisseur', text='Fournisseur', anchor=tk.W)
        
        # Style alternée
        self.tree.tag_configure('oddrow', background='#F0F0F0')
        self.tree.tag_configure('evenrow', background='white')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.edit_product)
        
        # ===== SECTION ACTIONS =====
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ModernButton(action_frame, "✏️ MODIFIER", command=self.edit_selected_product, style_type="info").pack(side=tk.LEFT, padx=5)
        ModernButton(action_frame, "❌ SUPPRIMER", command=self.delete_selected_product, style_type="danger").pack(side=tk.LEFT, padx=5)
        ModernButton(action_frame, "🔄 MOUVEMENTS STOCK", command=self.show_stock_movements, style_type="primary").pack(side=tk.LEFT, padx=5)
        ModernButton(action_frame, "📄 RAPPORT STOCK", command=self.export_stock_report, style_type="accent").pack(side=tk.LEFT, padx=5)
        
        # Charger les produits
        self.refresh_product_list()
    
    def add_product(self):
        """Ajoute un nouveau produit"""
        try:
            # Récupérer et valider les données
            ref = self.ref_entry.get().strip()
            name = self.name_entry.get().strip()
            
            if not ref or not name:
                messagebox.showerror("Erreur", "Référence et nom du produit sont obligatoires")
                return
            
            # Valider et convertir les valeurs numériques
            try:
                quantity = int(self.quantity_entry.get() or 0)
                price = float(self.price_entry.get() or 0)
                vat = float(self.vat_entry.get() or 18)
                stock_min = int(self.stock_min_entry.get() or 5)
                stock_max = int(self.stock_max_entry.get() or 100)
            except ValueError:
                messagebox.showerror("Erreur", "Format numérique invalide")
                return
            
            if price < 0:
                messagebox.showerror("Erreur", "Le prix ne peut pas être négatif")
                return
            
            if quantity < 0:
                messagebox.showerror("Erreur", "La quantité ne peut pas être négative")
                return
            
            # Ajouter à la base de données
            conn = self.db.get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO products 
                (reference, name, description, unit_price, vat_rate, stock_quantity, 
                 stock_min, stock_max, category, supplier, last_restock_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ref, name, self.desc_entry.get().strip() or None, 
                price, vat, quantity,
                stock_min, stock_max,
                self.category_entry.get().strip() or None, 
                self.supplier_entry.get().strip() or None,
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("✓ Succès", f"Produit '{name}' ajouté avec succès!")
            self.clear_form()
            self.refresh_product_list()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", f"Cette référence existe déjà!\nChoisissez une autre référence.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {str(e)}")
    
    def clear_form(self):
        """Réinitialise le formulaire"""
        self.ref_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.supplier_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.quantity_entry.insert(0, "0")
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, "0")
        self.desc_entry.delete(0, tk.END)
    
    def refresh_product_list(self):
        """Actualise la liste des produits"""
        # Supprimer tous les éléments
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, reference, name, category, stock_quantity, unit_price, 
                       stock_min, stock_max, supplier 
                FROM products 
                ORDER BY category, name
            """)
            
            products = cursor.fetchall()
            
            for idx, row in enumerate(products):
                try:
                    product_id, ref, name, category, qty, price, min_stock, max_stock, supplier = row
                    
                    # Sécuriser les valeurs
                    qty = int(qty or 0)
                    price = float(price or 0)
                    total_value = qty * price
                    
                    # Déterminer la couleur de ligne
                    tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
                    
                    # Ajouter à la liste
                    self.tree.insert('', tk.END, iid=product_id, values=(
                        ref or '', 
                        name or '', 
                        category or '', 
                        qty, 
                        f"{price:.2f}", 
                        f"{total_value:.2f}",
                        min_stock or 0, 
                        max_stock or 0, 
                        supplier or ''
                    ), tags=(tag,))
                except (ValueError, TypeError) as e:
                    print(f"Erreur ligne {idx}: {e}")
                    continue
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des produits: {str(e)}")
    
    def edit_selected_product(self):
        """Édite le produit sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un produit")
            return
        
        self.edit_product(None, selection[0])
    
    def edit_product(self, event, product_id=None):
        """Édite un produit spécifique"""
        if product_id is None and event:
            item = self.tree.selection()[0]
            product_id = item
        else:
            product_id = product_id
        
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            conn.close()
            
            if not product:
                messagebox.showerror("Erreur", "Produit introuvable")
                return
            
            # Fenêtre d'édition
            edit_window = tk.Toplevel(self.parent)
            edit_window.title(f"Éditer: {product['name']}")
            edit_window.geometry("600x400")
            
            frame = ttk.Frame(edit_window, padding=15)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Formulaire d'édition
            ttk.Label(frame, text="Référence:").grid(row=0, column=0, sticky=tk.W, pady=5)
            ref_edit = ttk.Entry(frame, width=30)
            ref_edit.insert(0, product['reference'])
            ref_edit.grid(row=0, column=1, pady=5)
            
            ttk.Label(frame, text="Nom:").grid(row=1, column=0, sticky=tk.W, pady=5)
            name_edit = ttk.Entry(frame, width=30)
            name_edit.insert(0, product['name'])
            name_edit.grid(row=1, column=1, pady=5)
            
            ttk.Label(frame, text="Quantité Stock:").grid(row=2, column=0, sticky=tk.W, pady=5)
            qty_edit = ttk.Entry(frame, width=30)
            qty_edit.insert(0, str(product['stock_quantity']))
            qty_edit.grid(row=2, column=1, pady=5)
            
            ttk.Label(frame, text="Prix Unitaire:").grid(row=3, column=0, sticky=tk.W, pady=5)
            price_edit = ttk.Entry(frame, width=30)
            price_edit.insert(0, str(product['unit_price']))
            price_edit.grid(row=3, column=1, pady=5)
            
            ttk.Label(frame, text="TVA (%):").grid(row=4, column=0, sticky=tk.W, pady=5)
            vat_edit = ttk.Entry(frame, width=30)
            vat_edit.insert(0, str(product['vat_rate']))
            vat_edit.grid(row=4, column=1, pady=5)
            
            def save_changes():
                try:
                    conn = self.db.get_conn()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE products SET name=?, stock_quantity=?, unit_price=?, vat_rate=?, updated_at=CURRENT_TIMESTAMP
                        WHERE id=?
                    """, (name_edit.get(), int(qty_edit.get()), float(price_edit.get()), float(vat_edit.get()), product_id))
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("✓ Succès", "Produit mise à jour!")
                    edit_window.destroy()
                    self.refresh_product_list()
                except Exception as e:
                    messagebox.showerror("Erreur", str(e))
            
            ModernButton(frame, "✓ ENREGISTRER", command=save_changes, style_type="success").grid(row=5, column=0, columnspan=2, pady=20)
            
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
    
    def delete_selected_product(self):
        """Supprime le produit sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un produit")
            return
        
        if messagebox.askyesno("Confirmation", "Êtes-vous sûr?"):
            try:
                product_id = selection[0]
                conn = self.db.get_conn()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("✓ Succès", "Produit supprimé!")
                self.refresh_product_list()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
    
    def show_stock_movements(self):
        """Affiche les mouvements de stock"""
        messagebox.showinfo("Mouvements", "Module en développement")
    
    def export_stock_report(self):
        """Exporte un rapport de stock"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt")],
                initialfile=f"Rapport_Stock_{datetime.now().strftime('%Y%m%d')}.txt"
            )
            
            if filename:
                conn = self.db.get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT reference, name, stock_quantity, unit_price, category FROM products ORDER BY category, name")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 100 + "\n")
                    f.write(f"RAPPORT D'INVENTAIRE - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                    f.write("=" * 100 + "\n\n")
                    
                    total_value = 0
                    for row in cursor.fetchall():
                        ref, name, qty, price, category = row
                        value = qty * price
                        total_value += value
                        f.write(f"{ref:15} | {name:30} | Qté: {qty:5} | P.U: {price:10.2f} GNF | Valeur: {value:15.2f} GNF | Catégorie: {category}\n")
                    
                    f.write("\n" + "=" * 100 + "\n")
                    f.write(f"VALEUR TOTALE DE L'INVENTAIRE: {total_value:,.2f} GNF\n")
                    f.write("=" * 100 + "\n")
                
                conn.close()
                messagebox.showinfo("✓ Succès", f"Rapport exporté: {filename}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

# ════════════════════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ════════════════════════════════════════════════════════════════════════════

class ANSARTECHERP:
    """Application ERP principale"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ANSARTECH ERP V2.2 - Gestion Professionnelle")
        self.root.geometry("1400x800")
        self.root.configure(bg=ModernTheme.BG_LIGHT)
        
        # Initialiser la base de données
        self.db = Database()
        
        # Initialiser les données d'exemple si la BD est vide
        self.init_sample_data()
        
        # Créer l'interface
        self.create_main_interface()
    
    def init_sample_data(self):
        """Initialise les données d'exemple si nécessaire"""
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            conn.close()
            
            # Si la table est vide, ajouter des données d'exemple
            if count == 0:
                self.add_sample_products()
        except:
            pass
    
    def add_sample_products(self):
        """Ajoute des produits d'exemple"""
        products = [
            ('REF-001', 'Ordinateur Portable HP', 'Ordinateur portable 15" HP', 850000, 18, 5, 2, 20, 'Informatique', 'HP Distribution'),
            ('REF-002', 'Souris Logitech', 'Souris sans fil ergonomique', 35000, 18, 50, 10, 100, 'Accessoires', 'Logitech'),
            ('REF-003', 'Clavier Mécanique', 'Clavier RGB avec touches mécaniques', 150000, 18, 12, 5, 50, 'Accessoires', 'Corsair'),
            ('REF-004', 'Écran 27 pouces 4K', 'Moniteur IPS 27" 4K', 450000, 18, 8, 3, 30, 'Écrans', 'Dell'),
            ('REF-005', 'Disque Dur 2TB', 'Stockage externe USB 3.0', 120000, 18, 25, 5, 100, 'Stockage', 'Western Digital'),
        ]
        
        try:
            conn = self.db.get_conn()
            cursor = conn.cursor()
            
            for ref, name, desc, price, vat, qty, min_stk, max_stk, cat, supplier in products:
                cursor.execute("""
                    INSERT OR IGNORE INTO products 
                    (reference, name, description, unit_price, vat_rate, stock_quantity, 
                     stock_min, stock_max, category, supplier, last_restock_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ref, name, desc, price, vat, qty, min_stk, max_stk, cat, supplier, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erreur initialisation données: {e}")
    
    def create_main_interface(self):
        """Crée l'interface principale"""
        # Barre de titre avec logo
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(
            header_frame, 
            text="🚀 ANSARTECH ERP V2.2 - Gestion Professionnelle",
            font=("Segoe UI", 16, "bold"),
            fg=ModernTheme.PRIMARY,
            bg=ModernTheme.BG_LIGHT
        )
        title_label.pack(anchor=tk.W)
        
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Notebook (onglets)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Stock
        stock_frame = ttk.Frame(self.notebook)
        self.notebook.add(stock_frame, text="📦 GESTION DU STOCK")
        self.stock_module = StockManagementModule(stock_frame, self.db)
        
        # Onglet Factures
        invoice_frame = ttk.Frame(self.notebook)
        self.notebook.add(invoice_frame, text="📄 FACTURES")
        self.create_invoice_tab(invoice_frame)
    
    def show_about(self):
        """Affiche la fenêtre À propos"""
        messagebox.showinfo(
            "À propos",
            "ANSARTECH ERP V2.2\n\n"
            "Solution professionnelle de gestion\n"
            "Stock • Factures • Comptabilité\n\n"
            "Développé par: ANSARTECH Solutions\n"
            "Contact: support@ansartech.com"
        )
    
    def show_stock_management(self):
        """Affiche la gestion du stock"""
        self.notebook.select(0)
    
    def show_invoices(self):
        """Affiche les factures"""
        self.notebook.select(1)
    
    def create_invoice_tab(self, parent):
        """Crée l'onglet factures"""
        frame = ttk.Frame(parent, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Gestion des Factures", font=("Segoe UI", 14, "bold")).pack()
        ttk.Label(frame, text="Module en développement...").pack(pady=20)
        
        ModernButton(frame, "➕ NOUVELLE FACTURE", command=lambda: messagebox.showinfo("Info", "Fonction en développement"), style_type="success").pack()

# ════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = ANSARTECHERP(root)
    root.mainloop()
