import json
import hashlib
from datetime import datetime
from collections import deque

# Clase para representar un commit
class Commit:
    def __init__(self, message, author, parent_hash=None, branch="main"):
        self.hash = self.generate_hash(message + author)
        self.message = message
        self.author = author
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.parent_hash = parent_hash
        self.files = []
        self.branch = branch

    def generate_hash(self, data):
        return hashlib.sha1(data.encode()).hexdigest()[:10]

    def to_dict(self):
        return {
            'hash': self.hash,
            'message': self.message,
            'author': self.author,
            'date': self.date,
            'parent_hash': self.parent_hash,
            'files': self.files,
            'branch': self.branch
        }

# Clase para el área de staging (usando pila)
class StagingArea:
    def __init__(self):
        self.staged_files = []  # Pila de archivos
        self.last_commit_hash = None  # Referencia al último commit
        
    def add_file(self, filename, status='A'):
        """Agrega un archivo a la pila de staging con verificación de cambios"""
        file_data = {
            'filename': filename,
            'status': status,
            'checksum': self.generate_checksum(filename),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'selected': False  # Nuevo campo para selección
        }
        
        # Verificar si el archivo ya existe en la pila
        existing = next((f for f in self.staged_files if f['filename'] == filename), None)
        if existing:
            if existing['checksum'] != file_data['checksum']:
                self.staged_files.remove(existing)
                self.staged_files.append(file_data)
        else:
            self.staged_files.append(file_data)
    
    def generate_checksum(self, filename):
        """Genera checksum SHA-1 del contenido del archivo (simulado)"""
        # En una implementación real se leería el contenido del archivo
        return hashlib.sha1(filename.encode()).hexdigest()[:10]
    
    #Esta funcion sirve para establecer en True el valor de selected que se incia como False y negando el False se obtiene que se eligio un archivo especifico dentro de la pila
    def toggle_selection(self, filename):
        """Alterna la selección de un archivo para commit"""
        for file in self.staged_files:
            if file['filename'] == filename:
                file['selected'] = not file['selected']
                return True
        return False
    
    def get_selected_files(self):
        """Obtiene los archivos seleccionados para commit"""
        return [file['filename'] for file in self.staged_files if file['selected']]
    
    def clear_selected(self):
        """Limpia solo los archivos seleccionados"""
        self.staged_files = [file for file in self.staged_files if not file['selected']]
    
    def clear(self):
        """Limpia toda la pila"""
        self.staged_files = []
    
    def get_staged_files(self, selected_only=False):
        """Obtiene archivos en staging con opción de filtrar seleccionados"""
        if selected_only:
            return [file for file in self.staged_files if file['selected']]
        return self.staged_files.copy()
    
    def update_last_commit_reference(self, commit_hash):
        """Actualiza la referencia al último commit relacionado"""
        self.last_commit_hash = commit_hash

# Clase para manejar pull requests (usando cola)
class PullRequestQueue:
    def __init__(self):
        self.queue = deque()  # Cola FIFO usando deque
        self.closed_prs = []  # PRs finalizados
        self.pr_count = 0
        
    def enqueue(self, pr):
        """Agrega un PR al final de la cola"""
        self.queue.append(pr)
        
    def dequeue(self):
        """Extrae el PR más antiguo de la cola"""
        if self.queue:
            return self.queue.popleft()
        return None
    
    def create_pr(self, source_branch, target_branch, author, repo):
        """Crea un nuevo PR con todos los metadatos requeridos"""
        self.pr_count += 1
        pr = {
            'id': self.pr_count,
            'title': f"PR{self.pr_count}",
            'description': "",
            'status': 'pending',
            'source': source_branch,
            'target': target_branch,
            'author': author,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'commits': self._get_commits_diff(repo, source_branch, target_branch),
            'modified_files': self._get_modified_files(repo, source_branch),
            'reviewers': [],
            'closed_at': None,
            'tags': [],
            'comments': []
        }
        self.queue.append(pr)
        return pr
    
    def _get_commits_diff(self, repo, source, target):
        """Obtiene los commits únicos de la rama fuente"""
        source_commits = []
        current_hash = repo.branches.get(source)
        
        while current_hash:
            commit = next((c for c in repo.commits if c.hash == current_hash), None)
            if not commit or commit.branch == target:
                break
            source_commits.append(commit.hash)
            current_hash = commit.parent_hash
        
        return source_commits
    
    def _get_modified_files(self, repo, branch):
        """Obtiene archivos modificados en la rama"""
        files = set()
        current_hash = repo.branches.get(branch)
        
        while current_hash:
            commit = next((c for c in repo.commits if c.hash == current_hash), None)
            if not commit:
                break
            files.update(commit.files)
            current_hash = commit.parent_hash
        
        return list(files)
    
    def find_pr(self, pr_id):
        """Busca un PR en la cola por ID"""
        for pr in self.queue:
            if pr['id'] == pr_id:
                return pr
        for pr in self.closed_prs:
            if pr['id'] == pr_id:
                return pr
        return None
    
    def update_status(self, pr_id, new_status):
        pr = self.find_pr(pr_id)
        if pr:
            pr['status'] = new_status
            if new_status in ['merged', 'rejected']:
                pr['closed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.queue.remove(pr)
                self.closed_prs.append(pr)
            return True
        return False
    
    def add_comment(self, pr_id, comment):
        pr = self.find_pr(pr_id)
        if pr:
            pr['comments'].append(comment)
            return True
        return False
    
    def add_reviewer(self, pr_id, reviewer):
        pr = self.find_pr(pr_id)
        if pr:
            pr['reviewers'].append(reviewer)
            return True
        return False
    
    def add_tag(self, pr_id, tag):
        pr = self.find_pr(pr_id)
        if pr:
            pr['tags'].append(tag)
            return True
        return False

# Clase principal del repositorio
class Repository:
    def __init__(self, name):
        self.name = name
        self.commits = []
        self.staging = StagingArea()
        self.branches = {'main': None}
        self.current_branch = 'main'
        self.pr_queue = PullRequestQueue()
        
    def add_commit(self, commit):
        self.commits.append(commit)
        self.branches[self.current_branch] = commit.hash
        #self.staging.clear()

# Clase principal del sistema de control de versiones
class VersionControlSystem:
    def __init__(self):
        self.repositories = []
        self.current_repo = None
        
    def create_repo(self, name):
        new_repo = Repository(name)
        self.repositories.append(new_repo)
        return new_repo

# Patrón de diseño Command
class Command:
    def execute(self, args):
        pass

class InitCommand(Command):
    def execute(self, vcs, args):
        repo_name = args[0] if args else 'new_repo'
        repo = vcs.create_repo(repo_name)
        vcs.current_repo = repo
        print(f"Repositorio {repo_name} inicializado.")
class PRCreateCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if len(args) < 2:
            print("Uso: pr create <rama_origen> <rama_destino>")
            return
            
        source = args[0]
        target = args[1]
        
        if source not in vcs.current_repo.branches:
            print(f"Error: Rama {source} no existe")
            return
            
        author = "user@example.com"
        pr = vcs.current_repo.pr_queue.create_pr(source, target, author, vcs.current_repo)
        print(f"PR#{pr['id']} creado: {source} -> {target}")

class PRStatusCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        print("\nEstado de Pull Requests:")
        for pr in vcs.current_repo.pr_queue.queue:
            print(f"PR#{pr['id']} [{pr['status']}] {pr['source']}->{pr['target']}")
            print(f"Autor: {pr['author']} | Creado: {pr['created_at']}")
            print(f"Etiquetas: {', '.join(pr['tags'])}")
            print("-" * 50)

class PRReviewCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if len(args) < 2:
            print("Uso: pr review <id_pr> <comentario>")
            return
            
        pr_id = int(args[0])
        comment = ' '.join(args[1:])
        
        pr = vcs.current_repo.pr_queue.find_pr(pr_id)
        if not pr:
            print(f"Error: PR#{pr_id} no encontrado")
            return
            
        vcs.current_repo.pr_queue.update_status(pr_id, 'en_revision')
        vcs.current_repo.pr_queue.add_comment(pr_id, comment)
        print(f"PR#{pr_id} en revisión. Comentario añadido.")
class PRNextCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        pr = vcs.current_repo.pr_queue.dequeue()
        if pr:
            pr['status'] = 'en_proceso'
            print(f"Procesando PR#{pr['id']}: {pr['title']}")
        else:
            print("No hay PRs pendientes en la cola")

class PRRejectCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if len(args) < 1:
            print("Uso: pr reject <id_pr> [razón]")
            return
            
        pr_id = int(args[0])
        pr = vcs.current_repo.pr_queue.find_pr(pr_id)
        
        if pr and pr in vcs.current_repo.pr_queue.queue:
            vcs.current_repo.pr_queue.queue.remove(pr)
            pr['status'] = 'rejected'
            pr['closed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            vcs.current_repo.pr_queue.closed_prs.append(pr)
            print(f"PR#{pr_id} rechazado")
        else:
            print(f"PR#{pr_id} no encontrado o no está en la cola")

class PRClearCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        vcs.current_repo.pr_queue.queue.clear()
        print("Cola de PRs limpiada")
class BranchCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if not args:
            # Listar ramas existentes
            print("Ramas disponibles:")
            for branch, commit_hash in vcs.current_repo.branches.items():
                print(f"- {branch} ({commit_hash[:6] if commit_hash else 'vacía'})")
            return
            
        if args[0] == "-b" and len(args) >= 2:
            # Crear nueva rama: branch -b <nombre_rama>
            new_branch = args[1]
            if new_branch in vcs.current_repo.branches:
                print(f"Error: La rama {new_branch} ya existe")
                return
                
            # Crear rama apuntando al commit actual
            current_hash = vcs.current_repo.branches[vcs.current_repo.current_branch]
            vcs.current_repo.branches[new_branch] = current_hash
            print(f"Rama {new_branch} creada")
        else:
            print("Comando no reconocido. Uso: branch -b <nombre_rama>")

class PRApproveCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if len(args) < 1:
            print("Uso: pr approve <id_pr>")
            return
            
        pr_id = int(args[0])
        
        pr = vcs.current_repo.pr_queue.find_pr(pr_id)
        if not pr:
            print(f"Error: PR#{pr_id} no encontrado")
            return
            
        # Realizar merge
        source_head = vcs.current_repo.branches[pr['source']]
        vcs.current_repo.branches[pr['target']] = source_head
        vcs.current_repo.pr_queue.update_status(pr_id, 'merged')
        print(f"PR#{pr_id} aprobado y fusionado en {pr['target']}")

class PRListCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        print("\nCola de Pull Requests:")
        print("{:<5} {:<12} {:<15} {:<10} {:<20} {:<15}".format(
            "ID", "Estado", "Origen->Destino", "Autor", "Creado", "Etiquetas"))
        
        # PRs activos en orden de cola
        for pr in vcs.current_repo.pr_queue.queue:
            print("{:<5} {:<12} {:<15} {:<10} {:<20} {:<15}".format(
                pr['id'],
                pr['status'],
                f"{pr['source']}->{pr['target']}",
                pr['author'],
                pr['created_at'],
                ', '.join(pr['tags'])
            ))
        
        # PRs cerrados
        if vcs.current_repo.pr_queue.closed_prs:
            print("\nPRs cerrados:")
            for pr in vcs.current_repo.pr_queue.closed_prs:
                print("{:<5} {:<12} {:<15} {:<10} {:<20} {:<15}".format(
                    pr['id'],
                    pr['status'],
                    f"{pr['source']}->{pr['target']}",
                    pr['author'],
                    pr['closed_at'],
                    ', '.join(pr['tags'])
                ))
class CheckoutCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if not args:
            print("Error: Se requiere un nombre de rama, ID de commit o parte del mensaje")
            return
            
        identifier = args[0]
        
        # Primero verificar si es un nombre de rama
        if identifier in vcs.current_repo.branches:
            self._switch_branch(vcs.current_repo, identifier)
            return
            
        # Si no es rama, buscar commit
        self._checkout_commit(vcs.current_repo, identifier)

    def _switch_branch(self, repo, branch_name):
        """Cambia a una rama existente"""
        repo.current_branch = branch_name
        commit_hash = repo.branches[branch_name]
        
        # Limpiar staging y cargar archivos del último commit de la rama
        repo.staging.clear()
        
        if commit_hash:
            # Buscar el commit correspondiente
            target_commit = next((c for c in repo.commits if c.hash == commit_hash), None)
            if target_commit:
                for file in target_commit.files:
                    repo.staging.add_file(file, status='M')
        
        print(f"Cambiado a rama '{branch_name}'")

    def _checkout_commit(self, repo, identifier):
        """Checkout a un commit específico"""
        target_commits = []
        identifier = identifier.lower()
        
        # Buscar coincidencias en hash o mensaje
        for commit in repo.commits:
            if (identifier in commit.hash.lower() or 
                identifier in commit.message.lower()):
                target_commits.append(commit)
                
        if not target_commits:
            print(f"Error: No se encontraron commits o ramas con '{identifier}'")
            return
            
        if len(target_commits) > 1:
            print("Múltiples commits coinciden:")
            for idx, commit in enumerate(target_commits, 1):
                print(f"{idx}. {commit.hash[:6]} - {commit.message}")
            print("Use un identificador más específico")
            return
            
        target_commit = target_commits[0]
        
        # Actualizar referencia de la rama actual
        repo.branches[repo.current_branch] = target_commit.hash
        repo.staging.clear()
        
        # Restaurar archivos
        for file in target_commit.files:
            repo.staging.add_file(file, status='M')
            
        print(f"Checkout exitoso a: {target_commit.hash[:6]} - {target_commit.message}")
class LogCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if not vcs.current_repo.commits:
            print("No hay commits en el historial")
            return
            
        print("\nHistorial de commits:")
        for commit in reversed(vcs.current_repo.commits):  # Mostrar del más reciente al más antiguo
            print(f"Commit: {commit.hash}")
            print(f"Autor: {commit.author}")
            print(f"Fecha: {commit.date}")
            print(f"Rama: {commit.branch}")
            print(f"Mensaje: {commit.message}")
            print(f"Archivos: {', '.join(commit.files)}")
            print(f"Padre: {commit.parent_hash}\n{'-'*50}")

class AddCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        for file in args:
            vcs.current_repo.staging.add_file(file)
        print(f"Archivos añadidos: {', '.join(args)}")

class CommitCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        # Obtener archivos seleccionados o todos si no hay selección
        selected_files = vcs.current_repo.staging.get_selected_files()
        clear_all = False
        
        # Si no hay archivos seleccionados, usar todos los archivos en staging
        if not selected_files:
            staged_files = vcs.current_repo.staging.get_staged_files()
            selected_files = [file['filename'] for file in staged_files]
            if not selected_files:
                print("Error: No hay archivos para commit")
                return
            clear_all = True  # Marcar para limpiar todo el staging
            
        message = args[0] if args else "Commit sin mensaje"
        author = "user@example.com"
        parent_hash = vcs.current_repo.branches[vcs.current_repo.current_branch]
        
        # Modificación clave: usar la rama actual
        new_commit = Commit(
            message=message,
            author=author,
            parent_hash=parent_hash,
            branch=vcs.current_repo.current_branch  # <- Aquí el cambio
        )
        
        new_commit.files = selected_files
        
        vcs.current_repo.add_commit(new_commit)
        
        # Limpiar solo los seleccionados o todo el staging
        if clear_all:
            vcs.current_repo.staging.clear()
        else:
            vcs.current_repo.staging.clear_selected()
            
        print(f"Commit creado: {new_commit.hash}")
class StatusCommand(Command):
    def execute(self, vcs, args):   
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        staged = vcs.current_repo.staging.get_staged_files()
        selected = vcs.current_repo.staging.get_selected_files()
        
        print("\nEstado actual del staging area:")
        print(f"Último commit relacionado: {vcs.current_repo.staging.last_commit_hash}")
        for file in staged:
            status = f"[{file['status']}]"
            selected_ind = "[X]" if file['selected'] else "[ ]"
            print(f"{selected_ind} {status} {file['filename']} - {file['checksum']}")
            
        print(f"\nArchivos seleccionados para commit: {', '.join(selected) if selected else 'Ninguno'}")

class StageCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if not args:
            print("Comandos disponibles:")
            print("stage list - Muestra archivos en staging")
            print("stage toggle <archivo> - Selecciona/deselecciona archivo")
            print("stage clear - Limpia todos los archivos")
            return
            
        subcmd = args[0]
        if subcmd == "list":
            staged = vcs.current_repo.staging.get_staged_files()
            if not staged:
                print("No hay archivos en staging")
                return
                
            for file in staged:
                status = f"[{file['status']}]"
                selected = "[X]" if file['selected'] else "[ ]"
                print(f"{selected} {status} {file['filename']}")
                
        elif subcmd == "toggle":
            if len(args) < 2:
                print("Error: Debes especificar un archivo")
                return
                
            filename = args[1]
            if vcs.current_repo.staging.toggle_selection(filename):
                print(f"Archivo {filename} actualizado")
            else:
                print(f"Error: Archivo {filename} no encontrado en staging")
                
        elif subcmd == "clear":
            vcs.current_repo.staging.clear()
            print("Staging area limpiada")
            
        else:
            print("Comando de staging no reconocido")
class PRTagCommand(Command):
    def execute(self, vcs, args):
        if not vcs.current_repo:
            print("Error: No hay repositorio activo")
            return
            
        if len(args) < 2:
            print("Uso: pr tag <id_pr> <etiqueta>")
            return
            
        try:
            pr_id = int(args[0])
            tag = args[1]
        except ValueError:
            print("Error: ID debe ser un número entero")
            return
            
        pr = vcs.current_repo.pr_queue.find_pr(pr_id)
        
        if pr:
            if vcs.current_repo.pr_queue.add_tag(pr_id, tag):
                print(f"Etiqueta '{tag}' añadida al PR#{pr_id}")
            else:
                print(f"Error: No se pudo añadir la etiqueta al PR#{pr_id}")
        else:
            print(f"Error: PR#{pr_id} no encontrado")
# Manejador de comandos
class CommandHandler:
    def __init__(self, vcs):
        self.vcs = vcs
        self.commands = {
            'init': InitCommand(),
            'add': AddCommand(),
            'commit': CommitCommand(),
            'status': StatusCommand(),
             'log': LogCommand(),
             'checkout': CheckoutCommand(),
             'stage': StageCommand(),
             'branch': BranchCommand(),
             'pr': {
                'create': PRCreateCommand(),
                'status': PRStatusCommand(),
                'review': PRReviewCommand(),
                'approve': PRApproveCommand(),
                'reject': PRRejectCommand(),
                'list': PRListCommand(),
                'next': PRNextCommand(),
                'clear': PRClearCommand(),
                'tag': PRTagCommand()
            }
        }
        
    def process_command(self, command_input):
        parts = command_input.split()
        if not parts:
            return
            
        # Manejar subcomandos para PR
        if parts[0] == 'pr' and len(parts) > 1:
            subcmd = parts[1]
            if subcmd in self.commands['pr']:
                self.commands['pr'][subcmd].execute(self.vcs, parts[2:])
            else:
                print(f"Comando PR desconocido: {subcmd}")
        else:
            if parts[0] in self.commands:
                self.commands[parts[0]].execute(self.vcs, parts[1:])
            else:
                print(f"Comando desconocido: {parts[0]}")

# Función principal
def main():
    vcs = VersionControlSystem()
    handler = CommandHandler(vcs)
    
    print("Bienvenido al sistema de control de versiones simplificado")
    print("Comandos disponibles: init, add, commit, status, branch, checkout, stage, log, exit")
    print("Comandos PR: create, status, review, approve, list, reject, cancel, next, tag, clear")
    while True:
        command = input("\n> ")
        if command.lower() == 'exit':
            break
        handler.process_command(command)

if __name__ == "__main__":
    main()