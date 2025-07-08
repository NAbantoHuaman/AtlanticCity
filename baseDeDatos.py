import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyodbc
from pyodbc import Error
import csv
import json
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import os
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class ModernButton(QPushButton):
    def __init__(self, text, icon=None, primary=False):
        super().__init__(text)
        self.setMinimumHeight(35)
        self.setCursor(Qt.PointingHandCursor)
        
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f3f2f1;
                    color: #323130;
                    border: 1px solid #d2d0ce;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #edebe9;
                    border-color: #c7c6c4;
                }
                QPushButton:pressed {
                    background-color: #e1dfdd;
                }
            """)
        
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(16, 16))

class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(35)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d2d0ce;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                outline: none;
            }
        """)

class ModernComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(35)
        self.setStyleSheet("""
            QComboBox {
                border: 2px solid #d2d0ce;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iIzMyMzEzMCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
        """)

class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(0, 0, 255))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'TABLE', 'INDEX', 'VIEW', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'DATABASE', 'SCHEMA',
            'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'ON', 'AS', 'AND', 'OR', 'NOT',
            'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'NULL', 'ORDER', 'BY', 'GROUP', 'HAVING',
            'DISTINCT', 'TOP', 'LIMIT', 'OFFSET', 'UNION', 'INTERSECT', 'EXCEPT', 'CASE', 'WHEN',
            'THEN', 'ELSE', 'END', 'IF', 'WHILE', 'FOR', 'BEGIN', 'DECLARE', 'SET'
        ]
        for keyword in keywords:
            pattern = QRegExp(r'\b' + keyword + r'\b')
            pattern.setCaseSensitivity(Qt.CaseInsensitive)
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(128, 0, 128))
        function_format.setFontWeight(QFont.Bold)
        functions = [
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'LEN', 'SUBSTRING', 'UPPER', 'LOWER',
            'LTRIM', 'RTRIM', 'REPLACE', 'CONVERT', 'CAST', 'GETDATE', 'DATEADD', 'DATEDIFF'
        ]
        for function in functions:
            pattern = QRegExp(r'\b' + function + r'\b')
            pattern.setCaseSensitivity(Qt.CaseInsensitive)
            self.highlighting_rules.append((pattern, function_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(0, 128, 0))
        self.highlighting_rules.append((QRegExp("'[^']*'"), string_format))
        self.highlighting_rules.append((QRegExp('"[^"]*"'), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(128, 128, 128))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp('--[^\n]*'), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(255, 0, 0))
        self.highlighting_rules.append((QRegExp(r'\b\d+(\.\d+)?\b'), number_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

class DataManager(QDialog):
    def __init__(self, connection, parent=None):
        super().__init__(parent)
        self.connection = connection
        self.current_table = None
        self.current_record_id = None
        self.identity_columns = {}
        self.setup_ui()
        self.load_tables()
    
    def setup_ui(self):
        self.setWindowTitle("Gestor de Datos")
        self.setGeometry(200, 200, 1200, 800)
        self.setStyleSheet("""
            QDialog {
                background-color: #faf9f8;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d2d0ce;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QHBoxLayout(self)
        
        # Panel izquierdo - Lista de tablas
        left_panel = QGroupBox("Tablas")
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        self.table_list = QListWidget()
        self.table_list.itemClicked.connect(self.on_table_selected)
        left_layout.addWidget(self.table_list)
        
        layout.addWidget(left_panel)
        
        # Panel derecho - Datos y formulario
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        self.new_btn = ModernButton("➕ Nuevo", primary=True)
        self.edit_btn = ModernButton("✏️ Editar")
        self.save_btn = ModernButton("💾 Guardar", primary=True)
        self.delete_btn = ModernButton("🗑️ Eliminar")
        self.cancel_btn = ModernButton("❌ Cancelar")
        
        self.new_btn.clicked.connect(self.new_record)
        self.edit_btn.clicked.connect(self.edit_record)
        self.save_btn.clicked.connect(self.save_record)
        self.delete_btn.clicked.connect(self.delete_record)
        self.cancel_btn.clicked.connect(self.cancel_edit)
        
        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        right_layout.addLayout(button_layout)
        
        # Splitter para datos y formulario
        splitter = QSplitter(Qt.Vertical)
        
        # Tabla de datos
        self.data_table = QTableWidget()
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.itemSelectionChanged.connect(self.on_select)
        self.data_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d2d0ce;
                background-color: white;
                alternate-background-color: #f8f7f6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #edebe9;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QHeaderView::section {
                background-color: #f3f2f1;
                padding: 8px;
                border: 1px solid #d2d0ce;
                font-weight: bold;
            }
        """)
        splitter.addWidget(self.data_table)
        
        # Formulario de edición
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self.form_fields = {}
        splitter.addWidget(form_widget)
        
        splitter.setSizes([400, 200])
        right_layout.addWidget(splitter)
        
        layout.addWidget(right_panel)
        
        self.set_edit_mode(False)
    
    def load_tables(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                self.table_list.addItem(table[0])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar tablas: {str(e)}")
    
    def on_table_selected(self, item):
        self.current_table = item.text()
        self.load_data()
        self.create_form_fields()
        self.set_edit_mode(False)
    
    def get_identity_columns(self, table_name):
        if table_name not in self.identity_columns:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ? AND COLUMNPROPERTY(OBJECT_ID(TABLE_SCHEMA+'.'+TABLE_NAME), COLUMN_NAME, 'IsIdentity') = 1
                """, table_name)
                identity_cols = [row[0] for row in cursor.fetchall()]
                self.identity_columns[table_name] = identity_cols
            except:
                self.identity_columns[table_name] = []
        return self.identity_columns[table_name]
    
    def is_date_field(self, data_type):
        date_types = ['date', 'datetime', 'datetime2', 'smalldatetime', 'time', 'timestamp']
        return any(dt in data_type.lower() for dt in date_types)
    
    def load_data(self):
        if not self.current_table:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM [{self.current_table}]")
            
            # Obtener información de columnas
            columns = [desc[0] for desc in cursor.description]
            identity_cols = self.get_identity_columns(self.current_table)
            
            # Configurar tabla
            self.data_table.setColumnCount(len(columns))
            self.data_table.setHorizontalHeaderLabels(columns)
            
            # Configurar estilos de columnas
            header = self.data_table.horizontalHeader()
            for i, col in enumerate(columns):
                if col in identity_cols:
                    self.data_table.setColumnWidth(i, 80)
                elif self.is_date_field(str(cursor.description[i][1])):
                    self.data_table.setColumnWidth(i, 150)
                else:
                    self.data_table.setColumnWidth(i, 120)
            
            # Cargar datos
            rows = cursor.fetchall()
            self.data_table.setRowCount(len(rows))
            
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    # Formatear IDs con ceros a la izquierda
                    if columns[col_idx] in identity_cols and value is not None:
                        display_value = f"{int(value):03d}"
                    else:
                        display_value = str(value) if value is not None else ""
                    
                    item = QTableWidgetItem(display_value)
                    
                    # Alineación según tipo
                    if columns[col_idx] in identity_cols:
                        item.setTextAlignment(Qt.AlignCenter)
                    elif self.is_date_field(str(cursor.description[col_idx][1])):
                        item.setTextAlignment(Qt.AlignCenter)
                    elif isinstance(value, (int, float)):
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    
                    self.data_table.setItem(row_idx, col_idx, item)
            
            header.setStretchLastSection(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {str(e)}")
    
    def create_form_fields(self):
        # Limpiar formulario anterior
        for i in reversed(range(self.form_layout.count())):
            self.form_layout.itemAt(i).widget().setParent(None)
        self.form_fields.clear()
        
        if not self.current_table:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, self.current_table)
            
            columns = cursor.fetchall()
            identity_cols = self.get_identity_columns(self.current_table)
            
            for col in columns:
                col_name, data_type, is_nullable, max_length = col
                
                if col_name in identity_cols:
                    # Campo de solo lectura para columnas identity
                    field = ModernLineEdit()
                    field.setReadOnly(True)
                    field.setStyleSheet(field.styleSheet() + """
                        QLineEdit {
                            background-color: #f3f2f1;
                            color: #605e5c;
                        }
                    """)
                    label_text = f"{col_name} (Auto)"
                elif self.is_date_field(data_type):
                    field = QDateTimeEdit()
                    field.setDateTime(QDateTime.currentDateTime())
                    field.setStyleSheet("""
                        QDateTimeEdit {
                            border: 2px solid #d2d0ce;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-size: 14px;
                            background-color: white;
                        }
                        QDateTimeEdit:focus {
                            border-color: #0078d4;
                        }
                    """)
                    label_text = col_name
                elif 'text' in data_type.lower() or (max_length and max_length > 255):
                    field = QTextEdit()
                    field.setMaximumHeight(100)
                    field.setStyleSheet("""
                        QTextEdit {
                            border: 2px solid #d2d0ce;
                            border-radius: 6px;
                            padding: 8px 12px;
                            font-size: 14px;
                            background-color: white;
                        }
                        QTextEdit:focus {
                            border-color: #0078d4;
                        }
                    """)
                    label_text = col_name
                else:
                    field = ModernLineEdit()
                    label_text = col_name
                
                # Marcar campos requeridos
                if is_nullable == 'NO' and col_name not in identity_cols:
                    label_text += " *"
                
                self.form_fields[col_name] = field
                self.form_layout.addRow(label_text, field)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear formulario: {str(e)}")
    
    def on_select(self):
        current_row = self.data_table.currentRow()
        if current_row >= 0:
            identity_cols = self.get_identity_columns(self.current_table)
            
            for col_idx in range(self.data_table.columnCount()):
                col_name = self.data_table.horizontalHeaderItem(col_idx).text()
                item = self.data_table.item(current_row, col_idx)
                value = item.text() if item else ""
                
                # Convertir IDs formateados de vuelta a números
                if col_name in identity_cols and value:
                    try:
                        value = str(int(value))
                        if not hasattr(self, 'current_record_id') or not self.current_record_id:
                            self.current_record_id = int(value)
                    except ValueError:
                        pass
                
                if col_name in self.form_fields:
                    field = self.form_fields[col_name]
                    if isinstance(field, QDateTimeEdit):
                        if value:
                            try:
                                dt = QDateTime.fromString(value, Qt.ISODate)
                                if not dt.isValid():
                                    dt = QDateTime.fromString(value, "yyyy-MM-dd hh:mm:ss")
                                if dt.isValid():
                                    field.setDateTime(dt)
                            except:
                                pass
                    elif isinstance(field, QTextEdit):
                        field.setPlainText(value)
                    else:
                        field.setText(value)
    
    def set_edit_mode(self, editing):
        self.new_btn.setEnabled(not editing)
        self.edit_btn.setEnabled(not editing and self.data_table.currentRow() >= 0)
        self.save_btn.setEnabled(editing)
        self.delete_btn.setEnabled(not editing and self.data_table.currentRow() >= 0)
        self.cancel_btn.setEnabled(editing)
        
        # Habilitar/deshabilitar campos del formulario
        identity_cols = self.get_identity_columns(self.current_table) if self.current_table else []
        for col_name, field in self.form_fields.items():
            if col_name not in identity_cols:
                field.setEnabled(editing)
    
    def new_record(self):
        self.current_record_id = None
        identity_cols = self.get_identity_columns(self.current_table)
        
        # Limpiar formulario
        for col_name, field in self.form_fields.items():
            if col_name in identity_cols:
                field.setText("(Auto)")
            elif isinstance(field, QDateTimeEdit):
                field.setDateTime(QDateTime.currentDateTime())
            elif isinstance(field, QTextEdit):
                field.setPlainText("")
            else:
                field.setText("")
        
        self.set_edit_mode(True)
    
    def edit_record(self):
        if self.data_table.currentRow() >= 0:
            self.set_edit_mode(True)
    
    def save_record(self):
        if not self.current_table:
            return
        
        try:
            cursor = self.connection.cursor()
            identity_cols = self.get_identity_columns(self.current_table)
            
            # Obtener información de columnas
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, self.current_table)
            columns_info = cursor.fetchall()
            
            values = []
            columns = []
            
            # Validar campos requeridos y recopilar valores
            for col_name, data_type, is_nullable in columns_info:
                if col_name in identity_cols:
                    continue  # Saltar columnas identity
                
                field = self.form_fields.get(col_name)
                if not field:
                    continue
                
                # Obtener valor del campo
                if isinstance(field, QDateTimeEdit):
                    value = field.dateTime().toString(Qt.ISODate)
                elif isinstance(field, QTextEdit):
                    value = field.toPlainText().strip()
                else:
                    value = field.text().strip()
                
                # Auto-llenar fechas vacías
                if not value and self.is_date_field(data_type):
                    if 'datetime' in data_type.lower():
                        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        value = datetime.now().strftime('%Y-%m-%d')
                
                # Validar campos requeridos (excluyendo identity)
                if is_nullable == 'NO' and not value:
                    QMessageBox.warning(self, "Campo Requerido", f"El campo '{col_name}' es requerido.")
                    return
                
                columns.append(col_name)
                values.append(value if value else None)
            
            if self.current_record_id:
                # Actualizar registro existente
                set_clause = ", ".join([f"[{col}] = ?" for col in columns])
                primary_key = identity_cols[0] if identity_cols else columns[0]
                sql = f"UPDATE [{self.current_table}] SET {set_clause} WHERE [{primary_key}] = ?"
                cursor.execute(sql, values + [self.current_record_id])
            else:
                # Insertar nuevo registro
                columns_clause = ", ".join([f"[{col}]" for col in columns])
                values_clause = ", ".join(["?" for _ in values])
                sql = f"INSERT INTO [{self.current_table}] ({columns_clause}) VALUES ({values_clause})"
                cursor.execute(sql, values)
            
            self.connection.commit()
            self.load_data()
            self.set_edit_mode(False)
            QMessageBox.information(self, "Éxito", "Registro guardado correctamente.")
            
        except Exception as e:
            self.connection.rollback()
            QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")
    
    def delete_record(self):
        current_row = self.data_table.currentRow()
        if current_row < 0:
            return
        
        reply = QMessageBox.question(self, "Confirmar", "¿Está seguro de eliminar este registro?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                cursor = self.connection.cursor()
                identity_cols = self.get_identity_columns(self.current_table)
                primary_key = identity_cols[0] if identity_cols else self.data_table.horizontalHeaderItem(0).text()
                
                # Obtener ID del registro
                id_item = self.data_table.item(current_row, 0)
                record_id = id_item.text()
                
                # Convertir ID formateado de vuelta a número si es necesario
                if primary_key in identity_cols:
                    record_id = int(record_id)
                
                sql = f"DELETE FROM [{self.current_table}] WHERE [{primary_key}] = ?"
                cursor.execute(sql, record_id)
                self.connection.commit()
                
                self.load_data()
                QMessageBox.information(self, "Éxito", "Registro eliminado correctamente.")
                
            except Exception as e:
                self.connection.rollback()
                QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")
    
    def cancel_edit(self):
        self.set_edit_mode(False)
        if self.data_table.currentRow() >= 0:
            self.on_select()  # Restaurar valores originales

class DatabaseGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.connection = None
        self.query_history = []
        self.sql_templates = {
            "SELECT básico": "SELECT * FROM tabla WHERE condicion;",
            "INSERT": "INSERT INTO tabla (columna1, columna2) VALUES (valor1, valor2);",
            "UPDATE": "UPDATE tabla SET columna1 = valor1 WHERE condicion;",
            "DELETE": "DELETE FROM tabla WHERE condicion;",
            "CREATE TABLE": "CREATE TABLE nueva_tabla (\n    id INT PRIMARY KEY IDENTITY(1,1),\n    nombre NVARCHAR(100) NOT NULL,\n    fecha DATETIME DEFAULT GETDATE()\n);",
            "JOIN": "SELECT t1.*, t2.columna\nFROM tabla1 t1\nINNER JOIN tabla2 t2 ON t1.id = t2.tabla1_id;"
        }
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        self.setWindowTitle("SQL Server Database Manager Pro - PyQt5")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel izquierdo
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        # Panel de conexión
        self.create_connection_panel(left_layout)
        
        # Explorador de BD
        self.create_db_explorer(left_layout)
        
        main_splitter.addWidget(left_panel)
        
        # Panel derecho
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Toolbar
        self.create_toolbar(right_layout)
        
        # Área de consultas
        self.create_query_area(right_layout)
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([350, 1050])
        
        # Menú
        self.create_menu()
        
        # Barra de estado
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Listo")
    
    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #faf9f8;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d2d0ce;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTreeWidget {
                border: 1px solid #d2d0ce;
                border-radius: 6px;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTextEdit {
                border: 2px solid #d2d0ce;
                border-radius: 6px;
                background-color: white;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #0078d4;
            }
            QTableWidget {
                gridline-color: #d2d0ce;
                background-color: white;
                alternate-background-color: #f8f7f6;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #edebe9;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QHeaderView::section {
                background-color: #f3f2f1;
                padding: 8px;
                border: 1px solid #d2d0ce;
                font-weight: bold;
            }
        """)
    
    def create_connection_panel(self, layout):
        conn_group = QGroupBox("Conexión SQL Server")
        conn_layout = QFormLayout(conn_group)
        
        # Campos de conexión
        self.server_edit = ModernLineEdit("NESTOR\\NESTOR23")
        self.server_edit.setText("NESTOR\\NESTOR23")
        conn_layout.addRow("Servidor:", self.server_edit)
        
        self.auth_combo = ModernComboBox()
        self.auth_combo.addItems(["Windows", "SQL Server"])
        self.auth_combo.currentTextChanged.connect(self.on_auth_change)
        conn_layout.addRow("Autenticación:", self.auth_combo)
        
        self.user_edit = ModernLineEdit("Usuario")
        self.user_edit.setEnabled(False)
        conn_layout.addRow("Usuario:", self.user_edit)
        
        self.password_edit = ModernLineEdit("Contraseña")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setEnabled(False)
        conn_layout.addRow("Contraseña:", self.password_edit)
        
        self.database_combo = ModernComboBox()
        conn_layout.addRow("Base de Datos:", self.database_combo)
        
        # Botones de conexión
        btn_layout = QHBoxLayout()
        self.connect_btn = ModernButton("🔗 Conectar", primary=True)
        self.disconnect_btn = ModernButton("🔌 Desconectar")
        self.test_btn = ModernButton("🧪 Probar")
        
        self.connect_btn.clicked.connect(self.connect_database)
        self.disconnect_btn.clicked.connect(self.disconnect_database)
        self.test_btn.clicked.connect(self.test_connection)
        
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        btn_layout.addWidget(self.test_btn)
        
        conn_layout.addRow(btn_layout)
        
        # Estado de conexión
        self.status_label = QLabel("❌ Desconectado")
        self.status_label.setStyleSheet("color: #d13438; font-weight: bold;")
        conn_layout.addRow("Estado:", self.status_label)
        
        layout.addWidget(conn_group)
    
    def create_db_explorer(self, layout):
        explorer_group = QGroupBox("Explorador de BD")
        explorer_layout = QVBoxLayout(explorer_group)
        
        self.db_tree = QTreeWidget()
        self.db_tree.setHeaderLabel("Objetos de Base de Datos")
        self.db_tree.itemDoubleClicked.connect(self.on_db_item_double_click)
        explorer_layout.addWidget(self.db_tree)
        
        layout.addWidget(explorer_group)
    
    def create_toolbar(self, layout):
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Botones principales
        self.execute_btn = ModernButton("▶️ Ejecutar", primary=True)
        self.stop_btn = ModernButton("⏹️ Detener")
        self.save_btn = ModernButton("💾 Guardar")
        self.open_btn = ModernButton("📁 Abrir")
        self.export_btn = ModernButton("📊 Exportar")
        self.templates_btn = ModernButton("🔧 Plantillas")
        self.diagram_btn = ModernButton("🗺️ Diagrama")
        self.data_manager_btn = ModernButton("📝 Gestionar Datos")
        
        self.execute_btn.clicked.connect(self.execute_current_query)
        self.stop_btn.clicked.connect(self.stop_query)
        self.save_btn.clicked.connect(self.save_sql_file)
        self.open_btn.clicked.connect(self.open_sql_file)
        self.export_btn.clicked.connect(self.export_results)
        self.templates_btn.clicked.connect(self.show_sql_templates)
        self.diagram_btn.clicked.connect(self.show_database_diagram)
        self.data_manager_btn.clicked.connect(self.show_data_manager)
        
        toolbar_layout.addWidget(self.execute_btn)
        toolbar_layout.addWidget(self.stop_btn)
        toolbar_layout.addWidget(QFrame())  # Separador
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addWidget(self.open_btn)
        toolbar_layout.addWidget(QFrame())  # Separador
        toolbar_layout.addWidget(self.export_btn)
        toolbar_layout.addWidget(self.templates_btn)
        toolbar_layout.addWidget(QFrame())  # Separador
        toolbar_layout.addWidget(self.diagram_btn)
        toolbar_layout.addWidget(self.data_manager_btn)
        toolbar_layout.addStretch()
        
        layout.addWidget(toolbar_widget)
    
    def create_query_area(self, layout):
        # Tabs para múltiples consultas
        self.query_tabs = QTabWidget()
        self.query_tabs.setTabsClosable(True)
        self.query_tabs.tabCloseRequested.connect(self.close_query_tab)
        
        # Crear primera pestaña
        self.new_query_tab()
        
        layout.addWidget(self.query_tabs)
    
    def new_query_tab(self, title=None):
        if title is None:
            title = f"Consulta {self.query_tabs.count() + 1}"
        
        # Widget de la pestaña
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # Splitter vertical
        splitter = QSplitter(Qt.Vertical)
        
        # Editor SQL
        query_group = QGroupBox("Editor SQL")
        query_layout = QVBoxLayout(query_group)
        
        query_editor = QTextEdit()
        query_editor.setMinimumHeight(200)
        
        # Aplicar resaltado de sintaxis
        highlighter = SqlHighlighter(query_editor.document())
        
        query_layout.addWidget(query_editor)
        splitter.addWidget(query_group)
        
        # Resultados
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout(results_group)
        
        results_table = QTableWidget()
        results_table.setAlternatingRowColors(True)
        results_layout.addWidget(results_table)
        
        splitter.addWidget(results_group)
        splitter.setSizes([200, 300])
        
        tab_layout.addWidget(splitter)
        
        # Guardar referencias
        tab_widget.query_editor = query_editor
        tab_widget.results_table = results_table
        
        # Agregar pestaña
        index = self.query_tabs.addTab(tab_widget, title)
        self.query_tabs.setCurrentIndex(index)
        
        return tab_widget
    
    def close_query_tab(self, index):
        if self.query_tabs.count() > 1:
            self.query_tabs.removeTab(index)
    
    def create_menu(self):
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("Archivo")
        
        new_action = QAction("Nueva Consulta", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_query_tab)
        file_menu.addAction(new_action)
        
        open_action = QAction("Abrir Script SQL", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_sql_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Guardar Script", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_sql_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Exportar Resultados", self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu("Herramientas")
        
        templates_action = QAction("Plantillas SQL", self)
        templates_action.triggered.connect(self.show_sql_templates)
        tools_menu.addAction(templates_action)
        
        diagram_action = QAction("Diagrama de BD", self)
        diagram_action.triggered.connect(self.show_database_diagram)
        tools_menu.addAction(diagram_action)
        
        data_manager_action = QAction("Gestionar Datos", self)
        data_manager_action.triggered.connect(self.show_data_manager)
        tools_menu.addAction(data_manager_action)
    
    def on_auth_change(self, auth_type):
        sql_auth = auth_type == "SQL Server"
        self.user_edit.setEnabled(sql_auth)
        self.password_edit.setEnabled(sql_auth)
    
    def connect_database(self):
        try:
            server = self.server_edit.text()
            database = self.database_combo.currentText()
            
            if self.auth_combo.currentText() == "Windows":
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
            else:
                user = self.user_edit.text()
                password = self.password_edit.text()
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={user};PWD={password};"
            
            self.connection = pyodbc.connect(conn_str)
            self.status_label.setText("✅ Conectado")
            self.status_label.setStyleSheet("color: #107c10; font-weight: bold;")
            self.status_bar.showMessage(f"Conectado a {server} - {database}")
            
            self.load_databases()
            self.load_database_schema()
            
            QMessageBox.information(self, "Éxito", "Conexión establecida correctamente")
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexión", f"No se pudo conectar a la base de datos:\n{str(e)}")
    
    def disconnect_database(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.status_label.setText("❌ Desconectado")
            self.status_label.setStyleSheet("color: #d13438; font-weight: bold;")
            self.status_bar.showMessage("Desconectado")
            self.db_tree.clear()
    
    def test_connection(self):
        try:
            server = self.server_edit.text()
            
            if self.auth_combo.currentText() == "Windows":
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};Trusted_Connection=yes;"
            else:
                user = self.user_edit.text()
                password = self.password_edit.text()
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};UID={user};PWD={password};"
            
            test_conn = pyodbc.connect(conn_str)
            test_conn.close()
            
            QMessageBox.information(self, "Prueba de Conexión", "✅ Conexión exitosa")
            
        except Exception as e:
            QMessageBox.critical(self, "Prueba de Conexión", f"❌ Error de conexión:\n{str(e)}")
    
    def load_databases(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name")
            databases = cursor.fetchall()
            
            self.database_combo.clear()
            for db in databases:
                self.database_combo.addItem(db[0])
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar bases de datos: {str(e)}")
    
    def load_database_schema(self):
        if not self.connection:
            return
        
        try:
            self.db_tree.clear()
            cursor = self.connection.cursor()
            
            # Cargar tablas
            tables_item = QTreeWidgetItem(self.db_tree, ["📋 Tablas"])
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                table_item = QTreeWidgetItem(tables_item, [f"📄 {table[0]}"])
                
                # Cargar columnas de la tabla
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """, table[0])
                columns = cursor.fetchall()
                
                for column in columns:
                    col_name, data_type, nullable = column
                    nullable_text = "NULL" if nullable == "YES" else "NOT NULL"
                    QTreeWidgetItem(table_item, [f"🔹 {col_name} ({data_type}, {nullable_text})"])
            
            # Cargar vistas
            views_item = QTreeWidgetItem(self.db_tree, ["👁️ Vistas"])
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.VIEWS
                ORDER BY TABLE_NAME
            """)
            views = cursor.fetchall()
            
            for view in views:
                QTreeWidgetItem(views_item, [f"👁️ {view[0]}"])
            
            # Cargar procedimientos almacenados
            procs_item = QTreeWidgetItem(self.db_tree, ["⚙️ Procedimientos"])
            cursor.execute("""
                SELECT ROUTINE_NAME 
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_TYPE = 'PROCEDURE'
                ORDER BY ROUTINE_NAME
            """)
            procedures = cursor.fetchall()
            
            for proc in procedures:
                QTreeWidgetItem(procs_item, [f"⚙️ {proc[0]}"])
            
            self.db_tree.expandAll()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar esquema: {str(e)}")
    
    def on_db_item_double_click(self, item, column):
        text = item.text(0)
        if text.startswith("📄"):
            table_name = text.replace("📄 ", "")
            self.insert_table_query(table_name)
    
    def insert_table_query(self, table_name):
        current_tab = self.query_tabs.currentWidget()
        if current_tab:
            query = f"SELECT * FROM [{table_name}];"
            current_tab.query_editor.setPlainText(query)
    
    def execute_current_query(self):
        current_tab = self.query_tabs.currentWidget()
        if not current_tab or not self.connection:
            QMessageBox.warning(self, "Advertencia", "No hay conexión o consulta para ejecutar")
            return
        
        query = current_tab.query_editor.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Advertencia", "No hay consulta para ejecutar")
            return
        
        try:
            self.status_bar.showMessage("Ejecutando consulta...")
            QApplication.processEvents()
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Si es una consulta SELECT, mostrar resultados
            if query.upper().strip().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Configurar tabla de resultados
                results_table = current_tab.results_table
                results_table.setColumnCount(len(columns))
                results_table.setHorizontalHeaderLabels(columns)
                results_table.setRowCount(len(rows))
                
                for row_idx, row in enumerate(rows):
                    for col_idx, value in enumerate(row):
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        results_table.setItem(row_idx, col_idx, item)
                
                results_table.resizeColumnsToContents()
                self.status_bar.showMessage(f"Consulta ejecutada. {len(rows)} filas devueltas.")
            else:
                # Para INSERT, UPDATE, DELETE, etc.
                self.connection.commit()
                affected_rows = cursor.rowcount
                self.status_bar.showMessage(f"Consulta ejecutada. {affected_rows} filas afectadas.")
                
                # Limpiar tabla de resultados
                current_tab.results_table.setRowCount(0)
                current_tab.results_table.setColumnCount(0)
            
            # Agregar a historial
            self.query_history.append(query)
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Consulta", f"Error al ejecutar la consulta:\n{str(e)}")
            self.status_bar.showMessage("Error en la consulta")
    
    def stop_query(self):
        # Implementar cancelación de consulta si es necesario
        self.status_bar.showMessage("Consulta detenida")
    
    def save_sql_file(self):
        current_tab = self.query_tabs.currentWidget()
        if not current_tab:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Script SQL", "", "Archivos SQL (*.sql)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(current_tab.query_editor.toPlainText())
                QMessageBox.information(self, "Éxito", "Archivo guardado correctamente")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar archivo: {str(e)}")
    
    def open_sql_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir Script SQL", "", "Archivos SQL (*.sql)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Crear nueva pestaña con el contenido
                tab = self.new_query_tab(os.path.basename(file_path))
                tab.query_editor.setPlainText(content)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al abrir archivo: {str(e)}")
    
    def export_results(self):
        current_tab = self.query_tabs.currentWidget()
        if not current_tab:
            return
        
        results_table = current_tab.results_table
        if results_table.rowCount() == 0:
            QMessageBox.warning(self, "Advertencia", "No hay resultados para exportar")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Resultados", "", "Archivos CSV (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Escribir encabezados
                    headers = []
                    for col in range(results_table.columnCount()):
                        headers.append(results_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Escribir datos
                    for row in range(results_table.rowCount()):
                        row_data = []
                        for col in range(results_table.columnCount()):
                            item = results_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Éxito", "Resultados exportados correctamente")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")
    
    def show_sql_templates(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Plantillas SQL")
        dialog.setGeometry(300, 300, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Lista de plantillas
        template_list = QListWidget()
        for template_name in self.sql_templates.keys():
            template_list.addItem(template_name)
        
        # Área de vista previa
        preview_area = QTextEdit()
        preview_area.setReadOnly(True)
        
        def on_template_selected():
            current_item = template_list.currentItem()
            if current_item:
                template_name = current_item.text()
                preview_area.setPlainText(self.sql_templates[template_name])
        
        template_list.itemClicked.connect(on_template_selected)
        
        # Botones
        button_layout = QHBoxLayout()
        use_btn = ModernButton("Usar Plantilla", primary=True)
        cancel_btn = ModernButton("Cancelar")
        
        def use_template():
            current_item = template_list.currentItem()
            if current_item:
                template_name = current_item.text()
                current_tab = self.query_tabs.currentWidget()
                if current_tab:
                    current_tab.query_editor.setPlainText(self.sql_templates[template_name])
                dialog.accept()
        
        use_btn.clicked.connect(use_template)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(use_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        
        layout.addWidget(QLabel("Selecciona una plantilla:"))
        layout.addWidget(template_list)
        layout.addWidget(QLabel("Vista previa:"))
        layout.addWidget(preview_area)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def show_database_diagram(self):
        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(self, "Advertencia", "Matplotlib no está disponible para mostrar diagramas")
            return
        
        if not self.connection:
            QMessageBox.warning(self, "Advertencia", "No hay conexión a la base de datos")
            return
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            import networkx as nx
            
            # Crear ventana del diagrama
            diagram_dialog = QDialog(self)
            diagram_dialog.setWindowTitle("Diagrama de Base de Datos")
            diagram_dialog.setGeometry(100, 100, 1000, 700)
            
            layout = QVBoxLayout(diagram_dialog)
            
            # Crear figura de matplotlib
            fig = Figure(figsize=(12, 8), dpi=100)
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)
            
            ax = fig.add_subplot(111)
            ax.set_title("Diagrama de Relaciones de Base de Datos", fontsize=16, fontweight='bold')
            
            # Obtener información de tablas y relaciones
            cursor = self.connection.cursor()
            
            # Obtener tablas
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Obtener relaciones (foreign keys)
            cursor.execute("""
                SELECT 
                    fk.TABLE_NAME as child_table,
                    pk.TABLE_NAME as parent_table,
                    fk.COLUMN_NAME as child_column,
                    pk.COLUMN_NAME as parent_column
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk 
                    ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk 
                    ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
                ORDER BY fk.TABLE_NAME, pk.TABLE_NAME
            """)
            relationships = cursor.fetchall()
            
            if not tables:
                ax.text(0.5, 0.5, 'No se encontraron tablas en la base de datos', 
                       horizontalalignment='center', verticalalignment='center', 
                       transform=ax.transAxes, fontsize=14)
                canvas.draw()
                diagram_dialog.exec_()
                return
            
            # Crear grafo para posicionamiento automático
            G = nx.Graph()
            G.add_nodes_from(tables)
            
            # Agregar aristas basadas en relaciones
            for rel in relationships:
                G.add_edge(rel[0], rel[1])  # child_table -> parent_table
            
            # Calcular posiciones usando layout de spring
            if len(tables) > 1:
                pos = nx.spring_layout(G, k=3, iterations=50)
            else:
                pos = {tables[0]: (0.5, 0.5)}
            
            # Escalar posiciones para mejor visualización
            for node in pos:
                pos[node] = (pos[node][0] * 8, pos[node][1] * 6)
            
            # Dibujar tablas como rectángulos
            table_boxes = {}
            for table in tables:
                x, y = pos[table]
                
                # Obtener columnas de la tabla
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, 
                           COLUMNPROPERTY(OBJECT_ID(TABLE_SCHEMA+'.'+TABLE_NAME), COLUMN_NAME, 'IsIdentity') as IS_IDENTITY
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """, table)
                columns = cursor.fetchall()
                
                # Calcular tamaño del rectángulo basado en número de columnas
                box_height = max(0.8, len(columns) * 0.15 + 0.3)
                box_width = max(2.0, len(table) * 0.08 + 0.5)
                
                # Dibujar rectángulo de la tabla
                rect = patches.Rectangle((x - box_width/2, y - box_height/2), 
                                       box_width, box_height, 
                                       linewidth=2, edgecolor='#0078d4', 
                                       facecolor='#f3f2f1', alpha=0.8)
                ax.add_patch(rect)
                
                # Título de la tabla
                ax.text(x, y + box_height/2 - 0.1, table, 
                       horizontalalignment='center', verticalalignment='top',
                       fontsize=10, fontweight='bold', color='#323130')
                
                # Listar columnas
                for i, col in enumerate(columns[:8]):  # Limitar a 8 columnas para evitar sobrecarga
                    col_name = col[0]
                    col_type = col[1]
                    is_identity = col[3]
                    
                    # Formatear texto de columna
                    if is_identity:
                        col_text = f"🔑 {col_name} ({col_type})"
                        color = '#d13438'  # Rojo para claves primarias
                    else:
                        col_text = f"   {col_name} ({col_type})"
                        color = '#605e5c'  # Gris para columnas normales
                    
                    ax.text(x - box_width/2 + 0.05, y + box_height/2 - 0.3 - i*0.12, 
                           col_text, horizontalalignment='left', verticalalignment='top',
                           fontsize=8, color=color)
                
                if len(columns) > 8:
                    ax.text(x - box_width/2 + 0.05, y + box_height/2 - 0.3 - 8*0.12, 
                           f"   ... y {len(columns)-8} más", 
                           horizontalalignment='left', verticalalignment='top',
                           fontsize=8, color='#a19f9d', style='italic')
                
                table_boxes[table] = (x, y, box_width, box_height)
            
            # Dibujar relaciones
            for rel in relationships:
                child_table, parent_table = rel[0], rel[1]
                if child_table in pos and parent_table in pos:
                    x1, y1 = pos[child_table]
                    x2, y2 = pos[parent_table]
                    
                    # Dibujar línea de relación
                    ax.plot([x1, x2], [y1, y2], 'r-', linewidth=1.5, alpha=0.7)
                    
                    # Agregar flecha
                    dx, dy = x2 - x1, y2 - y1
                    length = (dx**2 + dy**2)**0.5
                    if length > 0:
                        dx_norm, dy_norm = dx/length, dy/length
                        arrow_x = x2 - dx_norm * 0.3
                        arrow_y = y2 - dy_norm * 0.3
                        ax.annotate('', xy=(x2, y2), xytext=(arrow_x, arrow_y),
                                   arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
            
            # Configurar ejes
            ax.set_xlim(-1, 9)
            ax.set_ylim(-1, 7)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Agregar leyenda
            legend_elements = [
                patches.Patch(color='#f3f2f1', label='Tabla'),
                plt.Line2D([0], [0], color='red', lw=2, label='Relación FK'),
                plt.Line2D([0], [0], marker='o', color='#d13438', label='Clave Primaria', 
                          markersize=8, linestyle='None')
            ]
            ax.legend(handles=legend_elements, loc='upper right')
            
            # Agregar información adicional
            info_text = f"Base de Datos: {self.database_combo.currentText()}\n"
            info_text += f"Tablas: {len(tables)}\n"
            info_text += f"Relaciones: {len(relationships)}"
            
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            canvas.draw()
            
            # Botón para cerrar
            button_layout = QHBoxLayout()
            close_btn = ModernButton("Cerrar")
            close_btn.clicked.connect(diagram_dialog.accept)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            diagram_dialog.exec_()
            
        except ImportError:
            QMessageBox.critical(self, "Error", "NetworkX no está disponible. Instale con: pip install networkx")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar diagrama: {str(e)}")
    
    def show_data_manager(self):
        if not self.connection:
            QMessageBox.warning(self, "Advertencia", "No hay conexión a la base de datos")
            return
        
        data_manager = DataManager(self.connection, self)
        data_manager.exec_()

def main():
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Configurar paleta de colores moderna
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(250, 249, 248))
    palette.setColor(QPalette.WindowText, QColor(50, 49, 48))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(248, 247, 246))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(50, 49, 48))
    palette.setColor(QPalette.Text, QColor(50, 49, 48))
    palette.setColor(QPalette.Button, QColor(243, 242, 241))
    palette.setColor(QPalette.ButtonText, QColor(50, 49, 48))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(0, 120, 212))
    palette.setColor(QPalette.Highlight, QColor(0, 120, 212))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    # Crear y mostrar la ventana principal
    window = DatabaseGUI()
    window.show()
    
    # Ejecutar la aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()