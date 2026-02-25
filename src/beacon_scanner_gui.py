import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import asyncio
import threading
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv

from beacon_scanner import BeaconScanner

MAX_PLOT_HISTORY = 3600 

class BeaconApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Radar BLE - Escaner de Beacons")
        self.root.geometry("1200x850") # Um pouco maior para respirar bem
        
        # Define um fundo cinza muito claro para a janela toda (moderno)
        self.root.configure(bg="#F0F2F5")

        self.history = {}
        self.last_known_beacons = []
        self.is_scanning = False 
        self.export_data = [] 
        
        self.sort_col = "rssi"
        self.sort_reverse = True
        self.col_names = {
            "mac": "Endereço MAC", 
            "status": "Status", 
            "rssi": "Sinal (RSSI)", 
            "nome": "Nome"
        }
        
        self.custom_title = None
        self.custom_xlabel = None
        self.custom_ylabel = None
        self.custom_legends = {} 
        
        self.scanner = BeaconScanner()
        
        self.setup_styles()
        self.setup_ui()
        
        self.loop = asyncio.new_event_loop()
        self.bg_thread = threading.Thread(target=self.start_asyncio_thread, daemon=True)
        self.bg_thread.start()

        self.root.after(1000, self.update_ui)

    def setup_styles(self):
        """Configura os estilos globais da aplicação (Cores, Fontes e Temas)"""
        self.style = ttk.Style()
        
        # Usa um tema mais liso (flat) se disponível no OS
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
            
        # Fontes
        self.default_font = ("Segoe UI", 10)
        self.bold_font = ("Segoe UI", 10, "bold")
        self.header_font = ("Segoe UI", 11, "bold")

        # Configurações gerais de Frames
        self.style.configure("TFrame", background="#F0F2F5")
        self.style.configure("Card.TFrame", background="#FFFFFF", relief="flat", borderwidth=1)
        self.style.configure("Card.TLabel", background="#FFFFFF", font=self.default_font)
        self.style.configure("Header.TLabel", background="#FFFFFF", font=self.header_font, foreground="#333333")
        self.style.configure("Status.TLabel", background="#FFFFFF", font=("Segoe UI", 10, "italic"), foreground="#6c757d")

        # Configurações de Botões (Modernos)
        self.style.configure("TButton", font=self.default_font, padding=6)
        
        # Estilos Customizados de Botões baseados no TK padrão para melhor controle de cor de fundo
        self.btn_configs = {
            "primary": {"bg": "#0D6EFD", "fg": "white", "activebackground": "#0b5ed7", "activeforeground": "white", "relief": "flat", "font": self.bold_font, "bd": 0, "padx": 15, "pady": 8},
            "success": {"bg": "#198754", "fg": "white", "activebackground": "#157347", "activeforeground": "white", "relief": "flat", "font": self.bold_font, "bd": 0, "padx": 15, "pady": 8},
            "danger":  {"bg": "#DC3545", "fg": "white", "activebackground": "#bb2d3b", "activeforeground": "white", "relief": "flat", "font": self.bold_font, "bd": 0, "padx": 15, "pady": 8},
            "warning": {"bg": "#FFC107", "fg": "black", "activebackground": "#ffca2c", "activeforeground": "black", "relief": "flat", "font": self.bold_font, "bd": 0, "padx": 15, "pady": 8},
            "secondary": {"bg": "#6C757D", "fg": "white", "activebackground": "#5c636a", "activeforeground": "white", "relief": "flat", "font": self.default_font, "bd": 0, "padx": 10, "pady": 6},
            "light":   {"bg": "#F8F9FA", "fg": "#212529", "activebackground": "#e2e6ea", "activeforeground": "#212529", "relief": "flat", "font": self.default_font, "bd": 1, "padx": 10, "pady": 5}
        }

        # Configuração da Tabela
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=25, borderwidth=0)
        self.style.configure("Treeview.Heading", font=self.bold_font, background="#E9ECEF", foreground="#495057", borderwidth=1)
        self.style.map("Treeview", background=[('selected', '#0D6EFD')], foreground=[('selected', 'white')])

    def create_button(self, parent, text, style_name, command, state=tk.NORMAL):
        """Helper para criar botões com visual moderno"""
        cfg = self.btn_configs[style_name]
        btn = tk.Button(parent, text=text, command=command, state=state, cursor="hand2", **cfg)
        return btn

    def setup_ui(self):
        # --- HEADER / PAINEL DE CONTROLO ---
        top_bar = ttk.Frame(self.root, style="Card.TFrame")
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(15, 10))
        
        # Margem interna do card
        top_bar_inner = ttk.Frame(top_bar, style="Card.TFrame")
        top_bar_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Grupo 1: Controles do Radar
        scan_group = ttk.Frame(top_bar_inner, style="Card.TFrame")
        scan_group.pack(side=tk.LEFT)
        
        ttk.Label(scan_group, text="Controles do Scanner", style="Header.TLabel").pack(side=tk.TOP, anchor="w", pady=(0, 5))
        btn_frame1 = ttk.Frame(scan_group, style="Card.TFrame")
        btn_frame1.pack(side=tk.TOP, anchor="w")
        
        self.btn_start = self.create_button(btn_frame1, "▶ Iniciar", "success", self.action_start)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_pause = self.create_button(btn_frame1, "⏸ Pausar", "warning", self.action_pause, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5)
        self.btn_stop = self.create_button(btn_frame1, "⏹ Parar", "danger", self.action_stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=(5, 15))

        # Divisor visual
        ttk.Separator(top_bar_inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Grupo 2: Dados
        data_group = ttk.Frame(top_bar_inner, style="Card.TFrame")
        data_group.pack(side=tk.LEFT, padx=15)
        
        ttk.Label(data_group, text="Gestão de Dados", style="Header.TLabel").pack(side=tk.TOP, anchor="w", pady=(0, 5))
        btn_frame2 = ttk.Frame(data_group, style="Card.TFrame")
        btn_frame2.pack(side=tk.TOP, anchor="w")
        
        self.btn_import = self.create_button(btn_frame2, "📂 Importar CSV", "secondary", self.action_import)
        self.btn_import.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_export = self.create_button(btn_frame2, "💾 Exportar CSV", "secondary", self.action_export, state=tk.DISABLED)
        self.btn_export.pack(side=tk.LEFT, padx=5)

        # Status à direita
        status_group = ttk.Frame(top_bar_inner, style="Card.TFrame")
        status_group.pack(side=tk.RIGHT, fill=tk.Y)
        self.lbl_status = ttk.Label(status_group, text="Status: Parado", style="Status.TLabel")
        self.lbl_status.pack(side=tk.BOTTOM, anchor="e")

        # --- ÁREA PRINCIPAL DIVIDIDA (PANED WINDOW) ---
        # Isso permite ao usuário redimensionar o gráfico vs tabela!
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # --- 1. PAINEL SUPERIOR: TABELA E FILTROS ---
        table_container = ttk.Frame(self.paned_window, style="Card.TFrame")
        self.paned_window.add(table_container, weight=1) # Weight 1 = pega menos espaço padrão
        
        # Barra superior da tabela (Filtros e Título)
        table_header = ttk.Frame(table_container, style="Card.TFrame")
        table_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        ttk.Label(table_header, text="Dispositivos Identificados", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Filtros alinhados à direita na barra da tabela
        filter_frame = ttk.Frame(table_header, style="Card.TFrame")
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Potência Mínima:", style="Card.TLabel").pack(side=tk.LEFT)
        self.rssi_var = tk.IntVar(value=-100)
        self.spin_rssi = ttk.Spinbox(filter_frame, from_=-100, to=0, textvariable=self.rssi_var, width=5, command=self.apply_filter)
        self.spin_rssi.pack(side=tk.LEFT, padx=(5, 15))
        self.spin_rssi.bind("<Return>", lambda e: self.apply_filter())
        
        btn_clear = self.create_button(filter_frame, "Limpar Seleção", "light", self.clear_selection)
        btn_clear.pack(side=tk.LEFT)

        # Treeview (Tabela) com Scrollbar!
        tree_frame = ttk.Frame(table_container)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ("mac", "status", "rssi", "nome")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=tree_scroll.set, selectmode="extended")
        tree_scroll.config(command=self.tree.yview)
        
        for col in columns:
            self.tree.heading(col, text=self.get_heading_text(col), command=lambda c=col: self.action_sort(c))
        
        self.tree.column("mac", width=160, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("rssi", width=100, anchor="center")
        self.tree.column("nome", width=300, anchor="w")
        
        self.tree.tag_configure("online", foreground="#212529")
        self.tree.tag_configure("offline", foreground="#ADB5BD")
        self.tree.tag_configure("importado", foreground="#0D6EFD") 

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.update_plot())

        # --- 2. PAINEL INFERIOR: GRÁFICO ---
        graph_container = ttk.Frame(self.paned_window, style="Card.TFrame")
        self.paned_window.add(graph_container, weight=2) # Weight 2 = pega mais espaço padrão

        # Barra de ferramentas do Gráfico
        graph_tools = ttk.Frame(graph_container, style="Card.TFrame")
        graph_tools.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        ttk.Label(graph_tools, text="Análise de Telemetria (RSSI)", style="Header.TLabel").pack(side=tk.LEFT)
        
        graph_actions = ttk.Frame(graph_tools, style="Card.TFrame")
        graph_actions.pack(side=tk.RIGHT)
        
        ttk.Label(graph_actions, text="Exibir últimos:", style="Card.TLabel").pack(side=tk.LEFT)
        self.time_window_var = tk.StringVar(value="60s")
        self.combo_time = ttk.Combobox(graph_actions, textvariable=self.time_window_var, values=["30s", "60s", "120s", "300s", "Tudo"], width=6, state="readonly")
        self.combo_time.pack(side=tk.LEFT, padx=(5, 15))
        self.combo_time.bind("<<ComboboxSelected>>", lambda e: self.update_plot())
        
        self.create_button(graph_actions, "⚙️ Personalizar", "secondary", self.action_config_plot).pack(side=tk.LEFT, padx=5)
        self.create_button(graph_actions, "🖼️ Salvar", "primary", self.action_save_plot).pack(side=tk.LEFT)

        # Área do Canvas do Matplotlib
        graph_frame = ttk.Frame(graph_container)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_title("Potência do Sinal (RSSI) ao longo do tempo")
        self.ax.set_xlabel("Leituras")
        self.ax.set_ylabel("RSSI (dBm)")
        self.ax.set_ylim(-100, -20)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.fig.tight_layout() # Melhora as margens do gráfico

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ==========================================
    # LÓGICA DE INTERFACE E BOTÕES
    # ==========================================
    # NOTA: O restante do código (lógica, sorts, actions, threads, etc)
    # permanece o mesmo da versão anterior, apenas substituí tk.Button pelos meus helper config.

    def get_heading_text(self, col):
        base_name = self.col_names[col]
        if self.sort_col == col:
            seta = " ▼" if self.sort_reverse else " ▲"
            return f"{base_name}{seta}"
        return base_name

    def action_sort(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False if col in ['nome', 'mac'] else True
        
        for c in self.tree["columns"]:
            self.tree.heading(c, text=self.get_heading_text(c))
            
        if self.last_known_beacons:
            self.refresh_table(self.last_known_beacons)

    def apply_filter(self):
        if self.last_known_beacons:
            self.refresh_table(self.last_known_beacons)

    def action_start(self):
        if not self.is_scanning:
            asyncio.run_coroutine_threadsafe(self.scanner.start(), self.loop)
            self.is_scanning = True
            
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            self.lbl_status.config(text="Status: Escaneando ao vivo...", foreground="#198754") # Verde

    def action_pause(self):
        if self.is_scanning:
            asyncio.run_coroutine_threadsafe(self.scanner.stop(), self.loop)
            self.is_scanning = False
            
            self.btn_start.config(state=tk.NORMAL, text="▶ Continuar")
            self.btn_pause.config(state=tk.DISABLED)
            self.lbl_status.config(text="Status: Pausado", foreground="#FFC107") # Amarelo

    def action_stop(self):
        if len(self.export_data) > 0:
            resposta = messagebox.askyesnocancel("Atenção - Perda de Dados", "Você possui dados coletados na memória. Se parar agora, o histórico será apagado.\n\nDeseja EXPORTAR os dados antes de limpar?")
            if resposta is None: return
            elif resposta is True:
                sucesso = self.action_export()
                if not sucesso: return 

        if self.is_scanning:
            asyncio.run_coroutine_threadsafe(self.scanner.stop(), self.loop)
            self.is_scanning = False
        
        self.history.clear()
        self.last_known_beacons.clear()
        self.export_data.clear() 
        self.scanner.beacons.clear()
        
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        self.update_plot()
        
        self.btn_start.config(state=tk.NORMAL, text="▶ Iniciar")
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_export.config(state=tk.DISABLED)
        self.lbl_status.config(text="Status: Parado e Limpo", foreground="#DC3545") # Vermelho

    def action_export(self):
        if not self.export_data:
            messagebox.showwarning("Aviso", "Não há dados coletados para exportar.")
            return False

        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")], title="Salvar leitura de Beacons")
        if not filepath: return False 
            
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(["Timestamp", "MAC", "Nome", "RSSI"])
                writer.writerows(self.export_data)
                
            messagebox.showinfo("Sucesso", f"Dados exportados com sucesso!\n{len(self.export_data)} registos salvos.")
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")
            return False

    def action_import(self):
        if self.is_scanning:
            messagebox.showwarning("Aviso", "Por favor, pause ou pare o radar ao vivo antes de importar um histórico.")
            return

        if len(self.export_data) > 0:
            resposta = messagebox.askyesnocancel("Atenção", "Existem dados atualmente na memória. Importar um arquivo irá substituí-listos.\n\nDeseja EXPORTAR os dados atuais antes de prosseguir?")
            if resposta is None: return
            elif resposta is True:
                if not self.action_export(): return 

        filepath = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")], title="Importar leitura")
        if not filepath: return

        try:
            self.history.clear()
            self.export_data.clear()
            latest_beacons_dict = {}

            with open(filepath, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=',')
                header = next(reader, None) 
                for row in reader:
                    if len(row) < 4: continue 
                    timestamp, mac, nome, rssi_str = row
                    try: rssi = int(rssi_str)
                    except ValueError: continue 

                    self.export_data.append(row)

                    if mac not in self.history:
                        self.history[mac] = {'nome': nome, 'rssi_history': deque(maxlen=MAX_PLOT_HISTORY), 'is_imported': True}
                    self.history[mac]['rssi_history'].append(rssi)
                    latest_beacons_dict[mac] = {'mac': mac, 'nome': nome, 'rssi': rssi, 'is_active': True, 'is_imported': True}

            self.last_known_beacons = list(latest_beacons_dict.values())
            self.refresh_table(self.last_known_beacons)
            self.update_plot()
            
            self.btn_export.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            self.lbl_status.config(text="Status: Visualizando Arquivo Importado", foreground="#0D6EFD")
            messagebox.showinfo("Sucesso", f"Arquivo carregado com sucesso!\n{len(self.export_data)} leituras importadas.")

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o ficheiro CSV.\n\nDetalhes: {e}")

    def action_save_plot(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png", 
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf"), ("SVG", "*.svg")], 
            title="Salvar Imagem do Gráfico"
        )
        if not filepath: return 
        try:
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Sucesso", "Imagem do gráfico salva com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar a imagem:\n{e}")

    def action_config_plot(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Personalizar Gráfico")
        dialog.geometry("480x500")
        dialog.configure(bg="#F0F2F5")
        dialog.transient(self.root) 
        dialog.grab_set() 

        frame_titulos = ttk.LabelFrame(dialog, text="Títulos dos Eixos", padding=10)
        frame_titulos.pack(fill=tk.X, padx=15, pady=10)

        ttk.Label(frame_titulos, text="Título:").grid(row=0, column=0, sticky="w", pady=5)
        ent_title = ttk.Entry(frame_titulos, width=40)
        ent_title.insert(0, self.custom_title if self.custom_title else "")
        ent_title.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(frame_titulos, text="Eixo X:").grid(row=1, column=0, sticky="w", pady=5)
        ent_xlabel = ttk.Entry(frame_titulos, width=40)
        ent_xlabel.insert(0, self.custom_xlabel if self.custom_xlabel else "")
        ent_xlabel.grid(row=1, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(frame_titulos, text="Eixo Y:").grid(row=2, column=0, sticky="w", pady=5)
        ent_ylabel = ttk.Entry(frame_titulos, width=40)
        ent_ylabel.insert(0, self.custom_ylabel if self.custom_ylabel else "")
        ent_ylabel.grid(row=2, column=1, sticky="w", pady=5, padx=5)

        frame_legendas = ttk.LabelFrame(dialog, text="Legendas (Beacons Selecionados)", padding=10)
        frame_legendas.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        macs_selecionados = [self.tree.item(item)['values'][0] for item in self.tree.selection()]
        
        legend_entries = {}
        if not macs_selecionados:
            ttk.Label(frame_legendas, text="Selecione dispositivos na tabela\npara editar seus nomes.", foreground="#6c757d", justify=tk.CENTER).pack(pady=20)
        else:
            for idx, mac in enumerate(macs_selecionados):
                if mac in self.history:
                    default_name = f"{self.history[mac]['nome']} ({mac[-5:]})"
                    ttk.Label(frame_legendas, text=f"MAC {mac[-5:]}:").grid(row=idx, column=0, sticky="w", pady=5)
                    ent_leg = ttk.Entry(frame_legendas, width=35)
                    ent_leg.insert(0, self.custom_legends.get(mac, default_name))
                    ent_leg.grid(row=idx, column=1, sticky="w", pady=5, padx=5)
                    legend_entries[mac] = ent_leg

        frame_botoes = ttk.Frame(dialog)
        frame_botoes.pack(fill=tk.X, padx=15, pady=15)

        def salvar():
            self.custom_title = ent_title.get()
            self.custom_xlabel = ent_xlabel.get()
            self.custom_ylabel = ent_ylabel.get()
            for m, entry_widget in legend_entries.items():
                val = entry_widget.get()
                if val: self.custom_legends[m] = val
            self.update_plot()
            dialog.destroy()

        def limpar():
            self.custom_title = None; self.custom_xlabel = None; self.custom_ylabel = None; self.custom_legends.clear()
            self.update_plot()
            dialog.destroy()

        self.create_button(frame_botoes, "Salvar", "success", salvar).pack(side=tk.RIGHT, padx=5)
        self.create_button(frame_botoes, "Restaurar Padrão", "light", limpar).pack(side=tk.LEFT, padx=5)

    def clear_selection(self):
        for item in self.tree.selection(): self.tree.selection_remove(item)
        self.update_plot()

    def start_asyncio_thread(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def update_ui(self):
        if self.is_scanning:
            beacons_atuais = self.scanner.get_all_beacons(timeout=3.0)
            self.last_known_beacons = beacons_atuais
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for b in beacons_atuais:
                mac = b['mac']
                if mac not in self.history: self.history[mac] = {'nome': b['nome'], 'rssi_history': deque(maxlen=MAX_PLOT_HISTORY)}
                
                if b['is_active']:
                    self.history[mac]['rssi_history'].append(b['rssi'])
                    self.export_data.append([current_time_str, mac, b['nome'], b['rssi']])
                else:
                    self.history[mac]['rssi_history'].append(-100)

            if len(self.export_data) > 0 and self.btn_export['state'] == tk.DISABLED: self.btn_export.config(state=tk.NORMAL)
            self.refresh_table(beacons_atuais)

        self.root.after(1000, self.update_ui)

    def refresh_table(self, beacons_list):
        try: min_rssi = self.rssi_var.get()
        except tk.TclError: min_rssi = -100 
            
        filtered = [b for b in beacons_list if (b['rssi'] if b.get('is_active', False) else -100) >= min_rssi]
        
        def sort_key(b):
            if self.sort_col == 'nome': return b['nome'].lower() 
            elif self.sort_col == 'mac': return b['mac']
            elif self.sort_col == 'rssi': return b['rssi'] if b.get('is_active', False) else -999 
            elif self.sort_col == 'status': return (b.get('is_active', False), b['rssi']) 
            return 0

        sorted_beacons = sorted(filtered, key=sort_key, reverse=self.sort_reverse)
        selecionados = [self.tree.item(item)['values'][0] for item in self.tree.selection()]
        
        for row in self.tree.get_children(): self.tree.delete(row)

        for b in sorted_beacons:
            mac = b['mac']
            if b.get('is_imported', False): status_text, rssi_text, tag = "📘 Importado", f"{b['rssi']} dBm", "importado"
            elif b.get('is_active', False): status_text, rssi_text, tag = "🟢 Online", f"{b['rssi']} dBm", "online"
            else: status_text, rssi_text, tag = "🔴 Offline", "---", "offline"

            item_id = self.tree.insert("", tk.END, values=(mac, status_text, rssi_text, b['nome']), tags=(tag,))
            if mac in selecionados: self.tree.selection_add(item_id)

        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        window_selection = self.time_window_var.get()
        if window_selection == "Tudo": limit, default_xlabel = MAX_PLOT_HISTORY, "Leituras (Todo o histórico ativo)"
        else: limit, default_xlabel = int(window_selection.replace("s", "")), f"Leituras (últimos {window_selection})"

        self.ax.set_title(self.custom_title if self.custom_title else "Potência do Sinal (RSSI) ao longo do tempo")
        self.ax.set_xlabel(self.custom_xlabel if self.custom_xlabel else default_xlabel)
        self.ax.set_ylabel(self.custom_ylabel if self.custom_ylabel else "RSSI (dBm)")
        self.ax.set_ylim(-100, -20)
        self.ax.grid(True, linestyle='--', alpha=0.7)

        macs_selecionados = [self.tree.item(item)['values'][0] for item in self.tree.selection()]

        if not macs_selecionados:
            self.ax.text(0.5, 0.5, "Selecione dispositivos na tabela acima para visualizá-los aqui.", horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, color='gray')
        else:
            for mac in macs_selecionados:
                if mac in self.history:
                    dados = list(self.history[mac]['rssi_history'])[-limit:]
                    default_leg = f"{self.history[mac]['nome']} ({mac[-5:]})"
                    leg = self.custom_legends.get(mac, default_leg)
                    self.ax.plot(range(len(dados)), dados, label=leg, marker='o', markersize=3)
            self.ax.legend(loc="lower left")
        
        self.fig.tight_layout() # Previne textos cortados nas bordas do gráfico
        self.canvas.draw()

    def on_closing(self):
        if len(self.export_data) > 0:
            resposta = messagebox.askyesnocancel("Sair do Aplicativo", "Você possui dados coletados não salvos.\n\nDeseja EXPORTAR os dados antes de fechar o aplicativo?")
            if resposta is None: return 
            elif resposta is True:
                if not self.action_export(): return 

        print("A encerrar...")
        if self.is_scanning: asyncio.run_coroutine_threadsafe(self.scanner.stop(), self.loop)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BeaconApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
