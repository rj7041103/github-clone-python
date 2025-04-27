# -*- coding: utf-8 -*-
"""
Simulador de Sistema de Control de Versiones Simplificado (SCVS)

Este módulo implementa una simulación básica de un sistema de control de versiones
con funcionalidades como commits, ramas, staging area, pull requests (simulados),
gestión de roles/permisos y colaboradores. Utiliza diversas estructuras de datos
como listas, deques, árboles BST y AVL para gestionar la información.
"""

import json
import hashlib
from datetime import datetime
from collections import deque
import difflib
import traceback # Para mejor depuración de errores
import os # Necesario para ciertas simulaciones o futuras expansiones

# --- Definiciones Globales de Roles y Permisos ---

# Define los permisos permitidos para cada rol. Usar sets para eficiencia.
ROLE_PERMISSIONS = {
    'admin': {
         'pull', 'push', 'merge'
    },
    'maintainer': {
        'push', 'merge'
    },
    'developer': {
        'push'
    },
    'guest': {
        'pull'
    }
}

VALID_ROLES = list(ROLE_PERMISSIONS.keys())

# --- Clases de Datos Fundamentales ---

class Commit:
    """Representa un único commit en el historial del repositorio."""
    def __init__(self, message, author, parent_hash=None, branch="main"):
        """
        Inicializa un objeto Commit.

        Args:
            message (str): El mensaje descriptivo del commit.
            author (str): El nombre o email del autor del commit.
            parent_hash (str | list | None): El hash del commit padre.
                                             Puede ser None (inicial), str (un padre),
                                             o list[str] (múltiples padres para merge).
            branch (str): El nombre de la rama donde se creó este commit.
        """
        hash_data = message + author
        if parent_hash:
           parent_str = ""
           if isinstance(parent_hash, list):
               if parent_hash: parent_str = parent_hash[0] # Usa primer padre para hash inicial
           elif isinstance(parent_hash, str): parent_str = parent_hash
           hash_data += parent_str
        self.hash = self.generate_hash(hash_data) # Hash único del commit
        self.message = message
        self.author = author
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Fecha y hora de creación
        self.parent_hash = parent_hash # Referencia a los padres
        self.files = [] # Lista de nombres de archivo incluidos en este commit
        self.branch = branch # Rama de origen

    def generate_hash(self, data):
        """
        Genera un hash SHA-1 basado en datos y timestamp para unicidad.

        Args:
            data (str): Datos base para generar el hash.

        Returns:
            str: El hash SHA-1 hexadecimal completo.
        """
        timestamp = datetime.now().isoformat()
        return hashlib.sha1((data + timestamp).encode()).hexdigest()

    def to_dict(self):
        """
        Convierte el objeto Commit a un diccionario serializable para JSON.

        Returns:
            dict: Representación del commit en formato diccionario.
        """
        return {
            'hash': self.hash, 'message': self.message, 'author': self.author,
            'date': self.date, 'parent_hash': self.parent_hash,
            'files': self.files, 'branch': self.branch
        }

class StagingArea:
    """
    Representa el área de "staging" o "index" donde se preparan los
    cambios antes de hacer un commit. Utiliza una lista para almacenar
    información sobre los archivos añadidos.
    """
    def __init__(self):
        """Inicializa un Staging Area vacío."""
        self.staged_files = [] # Lista de diccionarios [ {'filename':.., 'status':.., ...}, ... ]
        self.last_commit_hash = None # Referencia opcional al último commit relacionado

    def add_file(self, filename, status='A'):
        """
        Añade o actualiza un archivo en el staging area.
        Simula la generación de un checksum para detectar cambios.

        Args:
            filename (str): El nombre del archivo a añadir/actualizar.
            status (str): El estado del archivo (ej. 'A' para añadido, 'M' modificado).
                          Actualmente simplificado a 'A'.
        """
        try:
            # Simulación simple de checksum basado en nombre y tiempo
            content_sim = f"{filename}-{datetime.now().timestamp()}"
            checksum = hashlib.sha1(content_sim.encode()).hexdigest()[:10]
        except Exception as e:
             checksum = self.generate_checksum(filename) # Fallback
             print(f"Error al generar checksum para '{filename}': {e}. Usando fallback.")

        file_data = {
            'filename': filename, 'status': status, 'checksum': checksum,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'selected': False # Flag para selección explícita para commit
        }

        # Busca si el archivo ya está en staging
        existing_index = next((i for i, f in enumerate(self.staged_files) if f['filename'] == filename), -1)

        if existing_index != -1:
            # Si existe, actualiza si el checksum es diferente
            if self.staged_files[existing_index]['checksum'] != file_data['checksum']:
                file_data['selected'] = self.staged_files[existing_index]['selected'] # Conserva selección
                self.staged_files[existing_index] = file_data
        else:
            # Si no existe, lo añade
            self.staged_files.append(file_data)

    def generate_checksum(self, filename):
        """
        Genera un checksum SHA-1 simulado basado únicamente en el nombre.

        Args:
            filename (str): Nombre del archivo.

        Returns:
            str: Checksum hexadecimal corto.
        """
        return hashlib.sha1(filename.encode()).hexdigest()[:10]

    def toggle_selection(self, filename):
        """
        Alterna el estado de selección de un archivo en el staging area.

        Args:
            filename (str): Nombre del archivo cuya selección se alternará.

        Returns:
            bool: True si el archivo se encontró y se actualizó, False si no.
        """
        for file_info in self.staged_files:
            if file_info['filename'] == filename:
                file_info['selected'] = not file_info['selected']
                print(f"Selección de '{filename}' cambiada a: {file_info['selected']}")
                return True
        print(f"Error: Archivo '{filename}' no encontrado en staging.")
        return False

    def get_selected_files(self):
        """
        Obtiene una lista de nombres de los archivos seleccionados.

        Returns:
            list[str]: Lista de nombres de archivo seleccionados.
        """
        return [file_info['filename'] for file_info in self.staged_files if file_info['selected']]

    def get_selected_file_info(self):
        """
        Obtiene la información completa (diccionarios) de los archivos seleccionados.

        Returns:
            list[dict]: Lista de diccionarios de los archivos seleccionados.
        """
        return [file_info for file_info in self.staged_files if file_info['selected']]

    def clear_selected(self):
        """Elimina del staging solo los archivos que están marcados como seleccionados."""
        initial_count = len(self.staged_files)
        self.staged_files = [file_info for file_info in self.staged_files if not file_info['selected']]
        removed_count = initial_count - len(self.staged_files)
        if removed_count > 0: print(f"{removed_count} archivos seleccionados eliminados del staging.")
        else: print("No había archivos seleccionados para limpiar.")

    def clear(self):
        """Elimina todos los archivos del staging area."""
        count = len(self.staged_files)
        self.staged_files = []
        if count > 0: print(f"Staging area limpiada ({count} archivos eliminados).")
        else: print("Staging area ya estaba vacío.")


    def get_staged_files(self, selected_only=False):
        """
        Obtiene la información de los archivos en staging.

        Args:
            selected_only (bool): Si True, devuelve solo los archivos seleccionados.
                                  Si False, devuelve todos los archivos.

        Returns:
            list[dict]: Una copia de la lista de información de archivos.
        """
        if selected_only: return self.get_selected_file_info()
        return self.staged_files.copy() # Copia para evitar modificaciones externas

    def update_last_commit_reference(self, commit_hash):
        """
        Actualiza la referencia al hash del último commit (uso opcional).

        Args:
            commit_hash (str): Hash del último commit.
        """
        self.last_commit_hash = commit_hash

class PullRequestQueue:
    """
    Gestiona una cola de Pull Requests (PRs) pendientes y una lista de PRs cerrados.
    Utiliza una `deque` para la cola FIFO de PRs activos.
    NOTA: La persistencia de PRs no está implementada actualmente.
    """
    def __init__(self):
        """Inicializa la cola de PRs."""
        self.queue = deque() # PRs activos
        self.closed_prs = [] # PRs merged o rejected
        self.pr_count = 0 # Contador para IDs únicos

    def enqueue(self, pr):
        """Añade un PR al final de la cola (uso interno o directo)."""
        self.queue.append(pr)

    def dequeue(self):
        """
        Elimina y devuelve el PR más antiguo de la cola (para procesamiento).

        Returns:
            dict | None: El diccionario del PR si la cola no está vacía, sino None.
        """
        if self.queue:
            return self.queue.popleft()
        return None

    def create_pr(self, source_branch, target_branch, author, repo):
        """
        Crea un nuevo Pull Request y lo añade a la cola.

        Args:
            source_branch (str): Nombre de la rama de origen.
            target_branch (str): Nombre de la rama de destino.
            author (str): Identificador del autor del PR.
            repo (Repository): Referencia al repositorio para validaciones.

        Returns:
            dict | None: El diccionario del PR creado si es exitoso, sino None.
        """
        self.pr_count += 1
        pr_id = self.pr_count
        # Validaciones básicas
        if source_branch not in repo.branches.nodes:
            print(f"Error PR: Rama origen '{source_branch}' no existe.")
            return None
        if target_branch not in repo.branches.nodes:
            print(f"Error PR: Rama destino '{target_branch}' no existe.")
            return None
        if source_branch == target_branch:
            print("Error PR: Origen y destino iguales.")
            return None

        # Crear el diccionario del PR
        pr = {
            'id': pr_id, 'title': f"PR #{pr_id}: Merge {source_branch} into {target_branch}",
            'description': "", 'status': 'pending', # Estados: pending, in_review, approved, rejected, merged
            'source': source_branch, 'target': target_branch, 'author': author,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'commits': [], # Placeholder: Lista de hashes de commit (requiere diff)
            'modified_files': [], # Placeholder: Lista de nombres de archivo (requiere diff)
            'reviewers': [], 'closed_at': None, 'tags': [], 'comments': []
        }
        self.queue.append(pr)
        print(f"Pull Request #{pr_id} creado: '{pr['title']}' por {author}.")
        return pr

    def find_pr(self, pr_id):
        """
        Busca un PR por su ID en la cola activa y en los cerrados.

        Args:
            pr_id (int): El ID del PR a buscar.

        Returns:
            dict | None: El diccionario del PR si se encuentra, sino None.
        """
        for pr in self.queue:
            if pr['id'] == pr_id:
                return pr
        for pr in self.closed_prs:
            if pr['id'] == pr_id:
                return pr
        return None

    def update_status(self, pr_id, new_status):
        """
        Actualiza el estado de un PR. Si el estado es de cierre ('merged', 'rejected'),
        mueve el PR de la cola activa a la lista de cerrados.

        Args:
            pr_id (int): ID del PR a actualizar.
            new_status (str): El nuevo estado (debe ser uno de los válidos).

        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        pr = self.find_pr(pr_id)
        if not pr:
            print(f"Error: PR #{pr_id} no encontrado.")
            return False
        # Evitar cambiar estado si ya está cerrado
        if pr['status'] in ['merged', 'rejected']:
            print(f"Error: PR #{pr_id} ya cerrado ({pr['status']}).")
            return False
        # Validar el nuevo estado
        valid_statuses = ['pending', 'in_review', 'approved', 'rejected', 'merged']
        if new_status not in valid_statuses:
            print(f"Error: Estado '{new_status}' inválido.")
            return False

        print(f"Actualizando PR #{pr_id}: '{pr['status']}' -> '{new_status}'.")
        pr['status'] = new_status

        # Mover a cerrados si corresponde
        if new_status in ['merged', 'rejected']:
            pr['closed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Intentar remover de la cola activa y añadir a cerrados
            initial_len = len(self.queue)
            self.queue = deque([item for item in self.queue if item['id'] != pr_id])
            moved = len(self.queue) < initial_len
            # Añadir a cerrados solo si no estaba ya (seguridad)
            if pr not in self.closed_prs:
                self.closed_prs.append(pr)
                if moved:
                    print(f"PR #{pr_id} movido a cerrados.")
        return True

    def add_comment(self, pr_id, comment_text, author):
        """
        Añade un comentario a un PR específico.

        Args:
            pr_id (int): ID del PR.
            comment_text (str): Contenido del comentario.
            author (str): Autor del comentario.

        Returns:
            bool: True si se añadió el comentario, False si el PR no se encontró.
        """
        pr = self.find_pr(pr_id)
        if pr:
            comment = {'author': author, 'text': comment_text, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            pr.setdefault('comments', []).append(comment) # Usar setdefault por seguridad
            print(f"Comentario añadido a PR #{pr_id} por {author}.")
            return True
        print(f"Error: No se pudo añadir comentario, PR #{pr_id} no encontrado.")
        return False

    def add_reviewer(self, pr_id, reviewer_email):
        """
        Añade un revisor a la lista de un PR.

        Args:
            pr_id (int): ID del PR.
            reviewer_email (str): Email o identificador del revisor.

        Returns:
            bool: True si se añadió, False si ya existía o el PR no se encontró.
        """
        pr = self.find_pr(pr_id)
        if pr:
            reviewers = pr.setdefault('reviewers', [])
            if reviewer_email not in reviewers:
                reviewers.append(reviewer_email)
                print(f"Revisor '{reviewer_email}' añadido a PR #{pr_id}.")
                return True
            else:
                print(f"'{reviewer_email}' ya es revisor de PR #{pr_id}.")
                return False
        print(f"Error: No se pudo añadir revisor, PR #{pr_id} no encontrado.")
        return False

    def add_tag(self, pr_id, tag):
        """
        Añade una etiqueta a un PR.

        Args:
            pr_id (int): ID del PR.
            tag (str): La etiqueta a añadir.

        Returns:
            bool: True si se añadió, False si ya existía o el PR no se encontró.
        """
        pr = self.find_pr(pr_id)
        if pr:
            tags = pr.setdefault('tags', [])
            if tag not in tags:
                tags.append(tag)
                print(f"Etiqueta '{tag}' añadida a PR #{pr_id}.")
                return True
            else:
                print(f"Etiqueta '{tag}' ya existe en PR #{pr_id}.")
                return False
        print(f"Error: No se pudo añadir etiqueta, PR #{pr_id} no encontrado.")
        return False

# --- Estructuras de Datos del Repositorio ---

class BranchTreeNode:
    """Representa un nodo en el árbol de ramas (estructura n-aria)."""
    def __init__(self, name, commit_hash=None, parent=None):
        """
        Inicializa un nodo de rama.

        Args:
            name (str): Nombre de la rama.
            commit_hash (str, optional): Hash del último commit en esta rama. Defaults to None.
            parent (BranchTreeNode, optional): Nodo padre en el árbol. Defaults to None.
        """
        self.name = name
        self.commit_hash = commit_hash
        self.parent = parent
        self.children = [] # Lista de nodos hijos

class BranchTree:
    """
    Representa la jerarquía de ramas como un árbol n-ario.
    Mantiene un diccionario para acceso rápido a los nodos por nombre.
    """
    def __init__(self):
        """Inicializa el árbol con la rama 'main' por defecto."""
        self.root = BranchTreeNode("main", None) # 'main' es la raíz
        self.nodes = {"main": self.root} # Acceso rápido a nodos

    def add_branch(self, branch_name, parent_name="main"):
        """
        Añade una nueva rama como hija de una rama existente.

        Args:
            branch_name (str): Nombre de la nueva rama.
            parent_name (str): Nombre de la rama padre. Defaults to "main".

        Returns:
            BranchTreeNode: El nodo de la nueva rama creada.

        Raises:
            ValueError: Si la rama ya existe o el padre no existe.
        """
        if branch_name in self.nodes:
            raise ValueError(f"Rama '{branch_name}' ya existe.")
        parent_node = self.nodes.get(parent_name)
        if not parent_node:
            raise ValueError(f"Rama padre '{parent_name}' no existe.")
        # Nueva rama apunta al mismo commit que el padre inicialmente
        new_node = BranchTreeNode(branch_name, parent_node.commit_hash, parent_node)
        parent_node.children.append(new_node)
        self.nodes[branch_name] = new_node
        return new_node

    def update_branch_commit(self, branch_name, commit_hash):
        """
        Actualiza el hash del último commit asociado a una rama.

        Args:
            branch_name (str): Nombre de la rama a actualizar.
            commit_hash (str): Nuevo hash del último commit.
        """
        if branch_name in self.nodes:
            self.nodes[branch_name].commit_hash = commit_hash
        else:
            # Esto podría pasar si un commit se carga antes que la rama en deserialize, aunque es raro
            print(f"Advertencia: Intento de actualizar commit en rama inexistente '{branch_name}'.")

    def delete_branch(self, branch_name):
        """
        Elimina una rama del árbol. No se puede eliminar 'main' ni ramas con hijas.

        Args:
            branch_name (str): Nombre de la rama a eliminar.

        Returns:
            bool: True si la eliminación fue exitosa.

        Raises:
            ValueError: Si la rama es 'main', no existe, o tiene ramas hijas.
        """
        if branch_name == "main":
            raise ValueError("No se puede eliminar la rama 'main'.")
        if branch_name not in self.nodes:
            raise ValueError(f"Rama '{branch_name}' no existe.")
        node_to_delete = self.nodes[branch_name]
        if node_to_delete.children:
            raise ValueError(f"Rama '{branch_name}' tiene ramas hijas y no puede ser eliminada.")
        parent_node = node_to_delete.parent
        # Eliminar referencia del padre
        if parent_node:
            parent_node.children = [c for c in parent_node.children if c.name != branch_name]
        # Eliminar del diccionario de nodos
        del self.nodes[branch_name]
        return True

    def get_branches(self):
        """Retorna una lista con los nombres de todas las ramas existentes."""
        return list(self.nodes.keys())

    def get_commit_hash(self, branch_name):
        """
        Obtiene el hash del último commit de una rama específica.

        Args:
            branch_name (str): Nombre de la rama.

        Returns:
            str | None: El hash del commit si la rama existe y tiene commits, sino None.
        """
        node = self.nodes.get(branch_name)
        return node.commit_hash if node else None

    def get_preorder_lines(self):
        """
        Genera una representación textual del árbol de ramas en recorrido preorden.

        Returns:
            list[str]: Lista de strings, cada una representando una rama en el árbol.
        """
        lines = []
        self._preorder_recursive(self.root, 0, lines)
        return lines

    def _preorder_recursive(self, node, level, lines):
        """Función auxiliar recursiva para el recorrido preorden."""
        if node:
            prefix = "  " * level + "└─ "
            commit_info = f"({node.commit_hash[:7]})" if node.commit_hash else "(vacía)"
            lines.append(f"{prefix}{node.name} {commit_info}")
            # Ordenar hijos alfabéticamente para una visualización consistente
            sorted_children = sorted(node.children, key=lambda x: x.name)
            for child in sorted_children:
                self._preorder_recursive(child, level + 1, lines)

    def serialize(self):
        """
        Serializa el estado del árbol de ramas a un diccionario apto para JSON.
        Guarda información esencial para reconstruir la estructura.

        Returns:
            dict: Diccionario donde las claves son nombres de rama y los valores
                  son diccionarios con 'name', 'commit_hash' y 'parent_name'.
        """
        return {name: {'name': node.name,
                       'commit_hash': node.commit_hash,
                       'parent_name': node.parent.name if node.parent else None}
                for name, node in self.nodes.items()}

    @classmethod
    def deserialize(cls, nodes_data):
        """
        Deserializa y reconstruye un BranchTree desde datos previamente serializados.

        Args:
            nodes_data (dict): El diccionario serializado obtenido de `serialize()`.

        Returns:
            BranchTree: La instancia reconstruida del árbol de ramas.
        """
        tree = cls()
        tree.nodes = {}
        temp_nodes = {} # Iniciar vacío

        # 1. Crear todos los nodos temporalmente
        for name, data in nodes_data.items():
            if not data: continue # Ignorar entradas corruptas/vacías
            node = BranchTreeNode(name, data.get('commit_hash'))
            temp_nodes[name] = node
            if name == "main": tree.root = node # Identificar la raíz

        # Manejar caso donde 'main' no está o no es la raíz encontrada
        if not hasattr(tree, 'root') or not tree.root: # Verificar si root fue asignado
             if "main" in temp_nodes:
                 tree.root = temp_nodes["main"]
             else:
                 print("Advertencia Crítica: Rama 'main' no encontrada al deserializar. Creando una vacía.")
                 tree.root = BranchTreeNode("main", None)
                 temp_nodes["main"] = tree.root

        # 2. Establecer relaciones padre/hijo y llenar diccionario final
        for name, data in nodes_data.items():
            if name not in temp_nodes: continue # Saltar si el nodo no se creó
            current_node = temp_nodes[name]
            parent_name = data.get('parent_name')
            if parent_name and parent_name in temp_nodes:
                parent_node = temp_nodes[parent_name]
                current_node.parent = parent_node
                # Añadir como hijo si no estaba ya (para evitar duplicados por si acaso)
                if current_node not in parent_node.children:
                    parent_node.children.append(current_node)
            elif name != "main" and not parent_name:
                 # Una rama que no es main y no tiene padre podría ser un error o estado inesperado
                 print(f"Advertencia: Rama '{name}' cargada sin padre definido (y no es 'main').")
            tree.nodes[name] = current_node # Añadir al diccionario final

        # Asegurar que la raíz esté en el diccionario de nodos
        if tree.root and tree.root.name not in tree.nodes:
            tree.nodes[tree.root.name] = tree.root

        return tree

class CollaboratorNode:
    """Nodo para el Árbol Binario de Búsqueda (BST) de Colaboradores."""
    def __init__(self, name, role):
        """
        Inicializa un nodo de colaborador.

        Args:
            name (str): Nombre único del colaborador (usado como clave).
            role (str): Rol asignado al colaborador (ej. "Contributor").
        """
        self.name = name
        self.role = role
        self.left = None
        self.right = None

class CollaboratorBST:
    """
    Árbol Binario de Búsqueda (BST) para gestionar colaboradores por nombre.
    Permite inserción, búsqueda, eliminación y listado ordenado.
    """
    def __init__(self):
        """Inicializa un BST vacío."""
        self.root = None

    def insert(self, name, role):
        """
        Inserta un nuevo colaborador o actualiza el rol si ya existe.

        Args:
            name (str): Nombre del colaborador (clave).
            role (str): Rol a asignar/actualizar.

        Returns:
            bool: True si se insertó un nuevo colaborador, False si se actualizó uno existente.
        """
        if not self.root:
            self.root = CollaboratorNode(name, role)
            return True
        else:
            return self._insert_recursive(self.root, name, role)

    def _insert_recursive(self, node, name, role):
        """Función auxiliar recursiva para insertar/actualizar."""
        if name == node.name:
            node.role = role # Actualizar rol
            return False # Indica actualización
        elif name < node.name:
            if node.left:
                return self._insert_recursive(node.left, name, role)
            else:
                node.left = CollaboratorNode(name, role)
                return True # Insertado
        else: # name > node.name
            if node.right:
                return self._insert_recursive(node.right, name, role)
            else:
                node.right = CollaboratorNode(name, role)
                return True # Insertado

    def find(self, name):
        """
        Busca un colaborador por su nombre.

        Args:
            name (str): Nombre del colaborador a buscar.

        Returns:
            CollaboratorNode | None: El nodo si se encuentra, None si no.
        """
        return self._find_recursive(self.root, name)

    def _find_recursive(self, node, name):
        """Función auxiliar recursiva para buscar."""
        if node is None or node.name == name:
            return node
        elif name < node.name:
            return self._find_recursive(node.left, name)
        else:
            return self._find_recursive(node.right, name)

    def remove(self, name):
        """
        Elimina un colaborador del árbol BST manteniendo la estructura.

        Args:
            name (str): Nombre del colaborador a eliminar.
        """
        self.root = self._remove_recursive(self.root, name)

    def _remove_recursive(self, node, name):
        """Función auxiliar recursiva para eliminar."""
        if node is None:
            return node # No encontrado o árbol vacío

        # Buscar el nodo a eliminar
        if name < node.name:
            node.left = self._remove_recursive(node.left, name)
        elif name > node.name:
            node.right = self._remove_recursive(node.right, name)
        else: # Nodo encontrado
            # Caso 1: Nodo con 0 o 1 hijo
            if node.left is None:
                return node.right # Devuelve el hijo derecho (o None)
            elif node.right is None:
                return node.left # Devuelve el hijo izquierdo
            # Caso 2: Nodo con 2 hijos
            else:
                # Encontrar el sucesor inorden (el nodo más pequeño en el subárbol derecho)
                temp = self._find_min_value_node(node.right)
                # Copiar los datos del sucesor al nodo actual
                node.name = temp.name
                node.role = temp.role
                # Eliminar el sucesor inorden del subárbol derecho
                node.right = self._remove_recursive(node.right, temp.name)
        return node # Devuelve el nodo (posiblemente modificado o el reemplazo)

    def _find_min_value_node(self, node):
        """Encuentra el nodo con el valor mínimo (más a la izquierda) en un subárbol."""
        current = node
        while current and current.left is not None:
            current = current.left
        return current

    def get_all_contributors_sorted(self):
        """
        Realiza un recorrido inorden para obtener una lista de todos los
        colaboradores ordenados alfabéticamente por nombre.

        Returns:
            list[tuple[str, str]]: Lista de tuplas (nombre, rol).
        """
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node, result_list):
        """Función auxiliar recursiva para recorrido inorden."""
        if node is not None:
            self._inorder_recursive(node.left, result_list)
            result_list.append((node.name, node.role)) # Añadir tupla (nombre, rol)
            self._inorder_recursive(node.right, result_list)

    def serialize(self):
        """
        Serializa el árbol BST a una estructura de diccionarios anidados (JSON).

        Returns:
            dict | None: Representación serializada del árbol.
        """
        return self._serialize_node(self.root)

    def _serialize_node(self, node):
        """Función auxiliar recursiva para serializar."""
        if node is None:
            return None
        return {'name': node.name, 'role': node.role,
                'left': self._serialize_node(node.left),
                'right': self._serialize_node(node.right)}

    @classmethod
    def deserialize(cls, data):
        """
        Deserializa y reconstruye un CollaboratorBST desde datos JSON.

        Args:
            data (dict): Datos serializados del árbol.

        Returns:
            CollaboratorBST: La instancia reconstruida del BST.
        """
        bst = cls()
        bst.root = cls._deserialize_node(data)
        return bst

    @classmethod
    def _deserialize_node(cls, data):
        """Función auxiliar recursiva para deserializar."""
        if data is None:
            return None
        node = CollaboratorNode(data['name'], data['role'])
        node.left = cls._deserialize_node(data.get('left'))
        node.right = cls._deserialize_node(data.get('right'))
        return node

# --- Árboles AVL para Roles y Permisos Detallados ---
class AVLTree:
    """
    Implementación de un Árbol AVL auto-balanceado genérico.
    Usado aquí para almacenar conjuntos de permisos de forma eficiente.
    """
    class AVLNode:
        """Nodo interno del árbol AVL."""
        def __init__(self, key):
            self.key = key
            self.left = None
            self.right = None
            self.height = 1

    def __init__(self):
        """Inicializa un árbol AVL vacío."""
        self.root = None

    def _height(self, node):
        """Calcula la altura de un nodo (0 si es None)."""
        return node.height if node else 0

    def _balance_factor(self, node):
        """Calcula el factor de balance de un nodo."""
        return self._height(node.left) - self._height(node.right) if node else 0

    # --- Rotaciones AVL ---
    def _rotate_left(self, z):
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2
        z.height = 1 + max(self._height(z.left), self._height(z.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        return y

    def _rotate_right(self, z):
        y = z.left
        T3 = y.right
        y.right = z
        z.left = T3
        z.height = 1 + max(self._height(z.left), self._height(z.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        return y

    def _balance(self, node):
        """
        Verifica el balance del nodo y realiza las rotaciones necesarias
        para mantener la propiedad AVL.

        Args:
            node (AVLNode): El nodo a balancear.

        Returns:
            AVLNode: La raíz del subárbol balanceado.
        """
        if node is None:
            return node
        # Actualizar altura
        node.height = 1 + max(self._height(node.left), self._height(node.right))
        balance = self._balance_factor(node)
        # Casos de desbalance y rotaciones
        if balance > 1 and self._balance_factor(node.left) >= 0: # Izq-Izq
            return self._rotate_right(node)
        if balance > 1 and self._balance_factor(node.left) < 0: # Izq-Der
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and self._balance_factor(node.right) <= 0: # Der-Der
            return self._rotate_left(node)
        if balance < -1 and self._balance_factor(node.right) > 0: # Der-Izq
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        return node # No necesita rotación

    def insert(self, key):
        """
        Inserta una nueva clave en el árbol AVL, manteniendo el balance.
        No inserta duplicados.

        Args:
            key: La clave a insertar (en este caso, un string de permiso).
        """
        self.root = self._insert_recursive(self.root, key)

    def _insert_recursive(self, node, key):
        """Auxiliar recursivo para insertar y balancear."""
        if not node:
            return self.AVLNode(key)
        if key < node.key:
            node.left = self._insert_recursive(node.left, key)
        elif key > node.key:
            node.right = self._insert_recursive(node.right, key)
        else:
             return node # Clave ya existe, no hacer nada
        return self._balance(node) # Balancear el camino de vuelta

    def contains(self, key):
        """
        Verifica si una clave existe en el árbol.

        Args:
            key: La clave a buscar.

        Returns:
            bool: True si la clave existe, False si no.
        """
        return self._contains_recursive(self.root, key)

    def _contains_recursive(self, node, key):
        """Auxiliar recursivo para buscar."""
        if not node:
            return False
        if key == node.key:
            return True
        elif key < node.key:
            return self._contains_recursive(node.left, key)
        else:
            return self._contains_recursive(node.right, key)

    def get_all_keys(self):
        """
        Realiza un recorrido inorden para obtener todas las claves ordenadas.

        Returns:
            list: Lista ordenada de las claves en el árbol.
        """
        keys = []
        self._inorder_traversal(self.root, keys)
        return keys

    def _inorder_traversal(self, node, keys_list):
        """Auxiliar recursivo para recorrido inorden."""
        if node:
            self._inorder_traversal(node.left, keys_list)
            keys_list.append(node.key)
            self._inorder_traversal(node.right, keys_list)

    def serialize(self):
        """
        Serializa el árbol AVL a una lista ordenada de sus claves.
        Simple pero pierde la estructura exacta, se reconstruye balanceado.

        Returns:
            list: Lista ordenada de claves.
        """
        return self.get_all_keys()

    @classmethod
    def deserialize(cls, keys_list):
        """
        Deserializa y reconstruye un árbol AVL balanceado desde una lista de claves.
        Para mejor eficiencia, asume que la lista podría estar ordenada y
        construye el árbol de forma balanceada directamente.

        Args:
            keys_list (list): Lista de claves a insertar.

        Returns:
            AVLTree: La instancia reconstruida del árbol AVL.
        """
        tree = cls()
        # Construir desde lista ordenada es más eficiente si keys_list viene de serialize()
        if keys_list:
            # Asumiendo que keys_list ya podría estar ordenada
            unique_sorted_keys = sorted(list(set(keys_list))) # Asegurar unicidad y orden
            tree.root = cls._build_balanced_from_sorted(unique_sorted_keys)
        return tree

    @classmethod
    def _build_balanced_from_sorted(cls, sorted_keys):
        """Construye recursivamente un árbol AVL balanceado desde una lista ordenada."""
        n = len(sorted_keys)
        if n == 0:
            return None
        def build_recursive(start, end):
            if start > end:
                return None
            mid = (start + end) // 2
            node = cls.AVLNode(sorted_keys[mid])
            node.left = build_recursive(start, mid - 1)
            node.right = build_recursive(mid + 1, end)
            # Calcular altura después de construir hijos
            node.height = 1 + max(AVLTree._height_static(node.left), AVLTree._height_static(node.right))
            return node
        return build_recursive(0, n - 1)

    @staticmethod
    def _height_static(node): # Versión estática para usar en classmethod
        """Calcula la altura de un nodo (0 si es None)."""
        return node.height if node else 0

class RoleAVL:
    """
    Árbol AVL para gestionar Roles de usuario. La clave principal es el email.
    Cada nodo contiene un árbol AVL anidado (`permissions`) para los permisos
    específicos de ese usuario/rol.
    """
    class RoleNode:
        """Nodo interno del árbol de Roles."""
        def __init__(self, email, role):
            self.email = email.lower() # Clave (insensible a mayúsculas)
            self.role = role # Nombre del rol (ej. 'developer')
            self.permissions = AVLTree() # Árbol AVL de permisos asociados
            self.left = None
            self.right = None
            self.height = 1

    def __init__(self):
        """Inicializa un árbol de Roles vacío."""
        self.root = None

    # Métodos auxiliares AVL (_height, _balance_factor, _rotate_left, _rotate_right, _balance)
    # Son idénticos a los de AVLTree, pero operan sobre RoleNode.
    def _height(self, node):
        return node.height if node else 0

    def _balance_factor(self, node):
        return self._height(node.left) - self._height(node.right) if node else 0

    def _rotate_left(self, z):
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2
        z.height = 1 + max(self._height(z.left), self._height(z.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        return y

    def _rotate_right(self, z):
        y = z.left
        T3 = y.right
        y.right = z
        z.left = T3
        z.height = 1 + max(self._height(z.left), self._height(z.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        return y

    def _balance(self, node):
        if node is None:
            return node
        node.height = 1 + max(self._height(node.left), self._height(node.right))
        balance = self._balance_factor(node)
        if balance > 1 and self._balance_factor(node.left) >= 0:
            return self._rotate_right(node)
        if balance > 1 and self._balance_factor(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and self._balance_factor(node.right) <= 0:
            return self._rotate_left(node)
        if balance < -1 and self._balance_factor(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        return node

    def insert(self, email, role, permissions):
        """
        Inserta un nuevo usuario/rol o actualiza uno existente.
        Añade los permisos especificados al árbol de permisos del nodo.
        NOTA: La validación de si los permisos son válidos para el rol
              debe hacerse *antes* de llamar a este método (en los comandos).

        Args:
            email (str): Email del usuario (clave).
            role (str): Nombre del rol a asignar/actualizar.
            permissions (iterable): Colección de strings de permisos a añadir.
        """
        email_lower = email.lower()
        self.root = self._insert_recursive(self.root, email_lower, role, permissions)

    def _insert_recursive(self, node, email, role, permissions):
        """Auxiliar recursivo para insertar/actualizar y balancear."""
        if not node:
            # Crear nuevo nodo y añadirle los permisos
            new_node = self.RoleNode(email, role)
            for perm in permissions:
                new_node.permissions.insert(perm)
            return new_node

        if email < node.email:
            node.left = self._insert_recursive(node.left, email, role, permissions)
        elif email > node.email:
            node.right = self._insert_recursive(node.right, email, role, permissions)
        else: # Email encontrado -> Actualizar
            node.role = role
            # Añadir solo los permisos que no tenga ya
            for perm in permissions:
                if not node.permissions.contains(perm):
                    node.permissions.insert(perm)
            # Nota: Esto no elimina permisos si se pasan menos en una actualización.

        return self._balance(node) # Balancear en el camino de vuelta

    def _find_node(self, email):
        """
        Busca el nodo correspondiente a un email (insensible a mayúsculas).

        Args:
            email (str): Email a buscar.

        Returns:
            RoleNode | None: El nodo si se encuentra, None si no.
        """
        email_lower = email.lower()
        return self._find_recursive(self.root, email_lower)

    def _find_recursive(self, node, email):
        """Auxiliar recursivo para buscar por email."""
        if not node or node.email == email:
            return node
        elif email < node.email:
            return self._find_recursive(node.left, email)
        else:
            return self._find_recursive(node.right, email)

    def has_permission(self, email, permission):
        """
        Verifica si un usuario tiene un permiso específico.

        Args:
            email (str): Email del usuario.
            permission (str): Permiso a verificar.

        Returns:
            bool: True si el usuario existe y tiene el permiso, False si no.
        """
        node = self._find_node(email)
        # Verifica que el nodo exista Y que su árbol de permisos contenga la clave
        return node is not None and node.permissions.contains(permission)

    def update_role(self, email, new_role, new_permissions):
        """
        Actualiza el rol y AÑADE nuevos permisos para un usuario existente.
        Reutiliza la lógica de `insert`.
        NOTA: La validación de permisos vs rol debe hacerse antes.

        Args:
            email (str): Email del usuario a actualizar.
            new_role (str): Nuevo rol a asignar.
            new_permissions (iterable): Permisos adicionales a añadir.

        Returns:
            bool: True si el usuario existía y se actualizó, False si no existía.
        """
        node = self._find_node(email)
        if node:
            self.insert(email, new_role, new_permissions) # insert maneja la actualización
            return True
        return False # Usuario no encontrado

    def _min_value_node(self, node):
        """Encuentra el nodo con el menor email en un subárbol (sucesor inorden)."""
        current = node
        while current and current.left:
            current = current.left
        return current

    def remove_role(self, email):
        """
        Elimina un usuario (y sus roles/permisos asociados) del árbol AVL.

        Args:
            email (str): Email del usuario a eliminar.
        """
        email_lower = email.lower()
        self.root = self._remove_recursive(self.root, email_lower)

    def _remove_recursive(self, node, email):
        """Auxiliar recursivo para eliminar y rebalancear."""
        if not node:
            return node # No encontrado

        # Buscar nodo
        if email < node.email:
            node.left = self._remove_recursive(node.left, email)
        elif email > node.email:
            node.right = self._remove_recursive(node.right, email)
        else: # Nodo encontrado
            # Caso 1: 0 o 1 hijo
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            # Caso 2: 2 hijos
            else:
                temp = self._min_value_node(node.right) # Sucesor inorden
                # Copiar datos del sucesor
                node.email = temp.email
                node.role = temp.role
                node.permissions = temp.permissions
                # Eliminar el sucesor del subárbol derecho
                node.right = self._remove_recursive(node.right, temp.email)

        # Si el subárbol quedó vacío
        if not node:
             return node

        # Balancear el nodo actual (o su reemplazo)
        return self._balance(node)

    def get_all_roles_info(self):
        """
        Obtiene una lista con la información de todos los roles/usuarios
        en el árbol, ordenada por email (debido al recorrido inorden).

        Returns:
            list[dict]: Lista de diccionarios, cada uno con 'email', 'role', 'permissions'.
        """
        roles_info = []
        self._inorder_collect(self.root, roles_info)
        return roles_info

    def _inorder_collect(self, node, info_list):
        """Auxiliar recursivo para recolectar info en recorrido inorden."""
        if node:
            self._inorder_collect(node.left, info_list)
            info_list.append({
                'email': node.email,
                'role': node.role,
                'permissions': node.permissions.get_all_keys() # Obtener lista de permisos
            })
            self._inorder_collect(node.right, info_list)

    def serialize(self):
        """
        Serializa el árbol de Roles completo a una estructura JSON anidada.

        Returns:
            dict | None: Representación serializada del árbol.
        """
        return self._serialize_node(self.root)

    def _serialize_node(self, node):
        """Auxiliar recursivo para serializar RoleNode y su árbol de permisos."""
        if not node:
            return None
        return {
            'email': node.email, 'role': node.role,
            'permissions': node.permissions.serialize(), # Serializa el AVLTree de permisos
            'left': self._serialize_node(node.left),
            'right': self._serialize_node(node.right),
            'height': node.height
        }

    @classmethod
    def deserialize(cls, data):
        """
        Deserializa y reconstruye un árbol de Roles desde datos JSON.

        Args:
            data (dict): Los datos serializados.

        Returns:
            RoleAVL: La instancia reconstruida del árbol.
        """
        avl = cls()
        avl.root = cls._deserialize_node(data)
        # Opcional: Podríamos verificar/rebalancear todo el árbol aquí si fuera necesario
        return avl

    @classmethod
    def _deserialize_node(cls, data):
        """Auxiliar recursivo para deserializar RoleNode."""
        if not data:
            return None
        # Crear nodo y restaurar atributos básicos
        node = cls.RoleNode(data['email'], data['role'])
        node.height = data.get('height', 1)
        # Deserializar el árbol de permisos anidado
        permissions_data = data.get('permissions', [])
        node.permissions = AVLTree.deserialize(permissions_data) # Llama a deserialize de AVLTree
        # Deserializar hijos recursivamente
        node.left = cls._deserialize_node(data.get('left'))
        node.right = cls._deserialize_node(data.get('right'))
        # Nota: No rebalanceamos aquí, asumimos que los datos guardados son válidos.
        return node

# Clase principal del repositorio
class Repository:
    """
    Representa un repositorio de SCVS. Contiene el historial de commits,
    el estado del staging area, la estructura de ramas, colaboradores,
    roles/permisos y la cola de Pull Requests.
    Maneja la carga y guardado de su estado en un archivo JSON.
    """
    def __init__(self, name):
        """
        Inicializa un nuevo repositorio con estructuras de datos vacías.

        Args:
            name (str): El nombre del repositorio (usado para el archivo).
        """
        self.name = name
        self.commits = []
        self.staging = StagingArea()
        self.branches = BranchTree()
        self.collaborators = CollaboratorBST()
        self.pr_queue = PullRequestQueue()
        self.roles = RoleAVL()
        self.current_branch = 'main'

    def create_initial_commit(self):
        """Opcional: Crea un commit inicial si el repositorio está vacío."""
        if not self.commits:
            initial_commit = Commit("Initial commit", "System", None, "main")
            initial_commit.files = []
            self.add_commit(initial_commit)
            print("Commit inicial creado.")

    def add_commit(self, commit_obj):
        """
        Añade un objeto Commit al historial del repositorio.
        Actualiza el puntero de la rama correspondiente.

        Args:
            commit_obj (Commit): El objeto Commit a añadir.
        """
        if any(c.hash == commit_obj.hash for c in self.commits):
            print(f"Advertencia: Commit {commit_obj.hash} ya existe.")
            return
        self.commits.append(commit_obj)
        self.branches.update_branch_commit(commit_obj.branch, commit_obj.hash)
        self.staging.update_last_commit_reference(commit_obj.hash)

    def get_commit(self, commit_hash):
        """
        Busca un commit en el historial por su hash completo.

        Args:
            commit_hash (str): El hash del commit a buscar.

        Returns:
            Commit | None: El objeto Commit si se encuentra, None si no.
        """
        return next((c for c in self.commits if c.hash == commit_hash), None)

    @staticmethod
    def load(name):
        """
        Carga el estado de un repositorio desde su archivo JSON correspondiente.

        Args:
            name (str): Nombre del repositorio a cargar.

        Returns:
            Repository | None: La instancia cargada o None si falla.
        """
        filename = f'{name}.json'
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            if "name" not in data or data["name"] != name:
                raise ValueError(f"Inconsistencia nombre en {filename}")
            repo = Repository(data["name"])
            repo.current_branch = data.get("current_branch", "main")
            branches_data = data.get("branches")
            repo.branches = BranchTree.deserialize(branches_data) if branches_data else BranchTree()
            if repo.current_branch not in repo.branches.nodes:
                print(f"Adv: Rama actual '{repo.current_branch}' no encontrada. Usando 'main'.")
                repo.current_branch = "main"
            if "main" not in repo.branches.nodes:
                print("Err: 'main' no encontrada.")
                repo.branches = BranchTree()
                repo.current_branch = "main"
            collaborators_data = data.get('collaborators')
            repo.collaborators = CollaboratorBST.deserialize(collaborators_data) if collaborators_data else CollaboratorBST()
            commits_data = data.get("commits", [])
            repo.commits = []
            for commit_dict in commits_data:
                if not commit_dict: continue
                try:
                    c = Commit(commit_dict.get('m','?'), commit_dict.get('a','?'), commit_dict.get('p'), commit_dict.get('b'))
                    c.hash=commit_dict.get('h',c.hash)
                    c.date=commit_dict.get('d')
                    c.files=commit_dict.get('f',[])
                    repo.commits.append(c)
                except Exception as e:
                    print(f"Err cargar commit: {commit_dict}. {e}.")
            staging_data = data.get("staging", {})
            repo.staging = StagingArea()
            repo.staging.staged_files = staging_data.get('staged_files', [])
            repo.staging.last_commit_hash = staging_data.get('last_commit_hash')
            roles_data = data.get('roles')
            repo.roles = RoleAVL.deserialize(roles_data) if roles_data else RoleAVL()
            return repo
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            print(f"Error: '{filename}' JSON inválido.")
            return None
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error: Formato inválido/clave faltante en '{filename}': {e}")
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"Error inesperado al cargar '{name}': {e}")
            traceback.print_exc()
            return None

    def save(self):
        """
        Guarda el estado actual completo del repositorio en un archivo JSON.
        """
        filename = f'{self.name}.json'
        print(f"Guardando '{self.name}' en {filename}...")
        try:
            commits_save = []
            for c in self.commits:
                commits_save.append({'h':c.hash, 'm':c.message, 'a':c.author, 'd':c.date, 'p':c.parent_hash, 'f':c.files, 'b':c.branch})
            data = {"name": self.name, 'current_branch': self.current_branch, 'branches': self.branches.serialize(),
                    'collaborators': self.collaborators.serialize(), 'commits': commits_save,
                    "staging": {'staged_files': self.staging.staged_files, 'last_commit_hash': self.staging.last_commit_hash},
                    'roles': self.roles.serialize()}
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"'{self.name}' guardado.")
        except Exception as e:
            print(f"Err Crítico al guardar '{self.name}': {e}")
            traceback.print_exc()

# Clase principal del sistema de control de versiones
class VersionControlSystem:
    """Gestiona múltiples repositorios y el repositorio activo."""
    def __init__(self):
        """Inicializa el VCS."""
        self.repositories = {}
        self.current_repo = None

    def init_repo(self, name):
        """Inicializa o carga un repositorio y lo activa."""
        if name in self.repositories:
            print(f"Repo '{name}' ya cargado.")
            self.current_repo = self.repositories[name]
            return self.current_repo
        repo = Repository.load(name)
        if repo:
            print(f"Repo '{name}' cargado.")
        else:
            print(f"Repo '{name}' no encontrado. Creando.")
            repo = Repository(name)
            repo.save()
            print(f"Repo '{name}' inicializado.")
        self.repositories[name] = repo
        self.current_repo = repo
        return repo

    def switch_repo(self, name):
        """Cambia el repositorio activo."""
        if name in self.repositories:
            self.current_repo = self.repositories[name]
            print(f"Cambiado a repo '{name}'.")
            return True
        else:
            print(f"Repo '{name}' no cargado. Cargando...")
            repo = self.init_repo(name)
            return repo is not None

# --- Implementación del Patrón Command ---
class Command:
    """Clase base abstracta para comandos SCVS."""
    def execute(self, vcs, args):
        """Ejecuta la lógica del comando, validando repo activo."""
        is_init_or_help = isinstance(self, (InitCommand, HelpCommand))
        if not vcs.current_repo and not is_init_or_help:
            print("Error: No hay repositorio activo. Usa 'init <nombre>'.")
            return False
        return True

class InitCommand(Command):
    """Comando: init <repo_name>"""
    def execute(self, vcs, args):
        if not args:
            print("Uso: init <nombre>")
            return
        vcs.init_repo(args[0])

class AddCommand(Command):
    """Comando: add <file1> [file2...]"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        if not args:
            print("Uso: add <archivo...>")
            return
        repo = vcs.current_repo
        added = []
        for f in args:
            repo.staging.add_file(f)
            added.append(f)
        print(f"Archivos añadidos/actualizados en staging: {', '.join(added)}")
        repo.save()

class CommitCommand(Command):
    """Comando: commit "message" """
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        repo = vcs.current_repo
        staged_info = repo.staging.get_selected_file_info()
        clear_all = False
        if not staged_info:
            staged_info = repo.staging.get_staged_files()
            if not staged_info:
                print("Error: No hay archivos en staging.")
                return
            clear_all = True
            print("Info: Incluyendo todos en staging.")
        files = [f['filename'] for f in staged_info]
        if not args:
            print("Uso: commit \"<mensaje>\"")
            return
        msg = " ".join(args)
        author = "user@example.com"
        branch = repo.current_branch
        parent = repo.branches.get_commit_hash(branch)
        commit = Commit(msg, author, parent, branch)
        commit.files = files
        repo.add_commit(commit)
        if clear_all:
            repo.staging.clear()
        else:
            repo.staging.clear_selected()
        repo.save()
        print(f"Commit {commit.hash[:7]} en '{branch}'. Archivos: {', '.join(files)}")

class StatusCommand(Command):
    """Comando: status"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        repo = vcs.current_repo
        print(f"En rama: '{repo.current_branch}'")
        last_commit = repo.branches.get_commit_hash(repo.current_branch)
        print(f"Último commit: {last_commit[:7]}" if last_commit else "Sin commits.")
        staged = repo.staging.get_staged_files()
        if not staged:
            print("\nStaging vacío.\n(usa 'add <archivo...>')")
        else:
            print("\nCambios listos para commit (Staging):\n(usa 'commit <msg>' o 'stage ...')")
            sel_count = 0
            for f in staged:
                print(f"  {'[X]' if f['selected'] else '[ ]'} {f['filename']:<30} ({f['status']}) Ck: {f['checksum']}")
                sel_count += f['selected']
            print(f"\n({sel_count} archivos seleccionados)" if sel_count else "\n(Ningún archivo seleccionado)")

class LogCommand(Command):
    """Comando: log"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        repo = vcs.current_repo
        print(f"\nHistorial - Rama '{repo.current_branch}':")
        curr_hash = repo.branches.get_commit_hash(repo.current_branch)
        if not curr_hash:
            print("Sin commits.")
            return
        visited = set()
        count = 0
        limit = 20
        while curr_hash and count < limit:
            if curr_hash in visited:
                print("...(Ciclo/Límite)")
                break
            commit = repo.get_commit(curr_hash)
            if not commit:
                print(f"Err: Commit {curr_hash[:7]} no encontrado.")
                break
            visited.add(curr_hash)
            count += 1
            print("-" * 60)
            print(f"commit {commit.hash}")
            if isinstance(commit.parent_hash, list):
                print(f"Merge: {', '.join([p[:7] for p in commit.parent_hash])}")
            print(f"Author: {commit.author}\nDate:   {commit.date}\nBranch: {commit.branch}\n\n    {commit.message}\n")
            if commit.files:
                print(f"    Archivos: {', '.join(commit.files)}")
            print("-" * 60)
            parent = commit.parent_hash
            curr_hash = (parent[0] if parent else None) if isinstance(parent, list) else parent
        if count == 0 and not curr_hash:
            print("Sin commits.")
        elif count >= limit:
            print(f"...(Últimos {limit})")

class CheckoutCommand(Command):
    """Comando: checkout <branch_name>"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        repo = vcs.current_repo
        if not args:
            print("Uso: checkout <rama>")
            return
        branch = args[0]
        if branch == repo.current_branch:
            print(f"Ya en '{branch}'.")
            return
        if branch in repo.branches.nodes:
            repo.current_branch = branch
            print(f"Cambiado a '{branch}'.")
            repo.save()
        else:
            print(f"Error: Rama '{branch}' no existe.")
            print("Usa 'branch' o 'branch -b <nombre>'")

class StageCommand(Command):
    """Comando: stage [list|toggle <f>|clear|clear_selected]"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        repo = vcs.current_repo
        if not args:
            print("Uso: stage <list|toggle <f>|clear|clear_selected>")
            return
        subcmd = args[0].lower()
        subcmd_args = args[1:]
        if subcmd == "list":
            staged = repo.staging.get_staged_files()
            if not staged:
                print("Staging vacío.")
                return
            print("Staging:")
            for f in staged:
                 print(f"  {'[X]' if f['selected'] else '[ ]'} {f['filename']:<30}({f['status']}) Ck:{f['checksum']}")
        elif subcmd == "toggle":
            if not subcmd_args:
                print("Uso: stage toggle <archivo>")
                return
            if repo.staging.toggle_selection(subcmd_args[0]):
                repo.save()
        elif subcmd == "clear":
            repo.staging.clear()
            repo.save()
        elif subcmd == "clear_selected":
            repo.staging.clear_selected()
            repo.save()
        else:
            print(f"Subcomando '{subcmd}' no reconocido.")
            self.execute(vcs, [])

class BranchCommand(Command):
    """Comando: branch [--list] | [-b <n> [p]] | [-d <n>]"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        repo = vcs.current_repo
        if not args or "--list" in args:
            print("Ramas:")
            curr = repo.current_branch
            branches = sorted(repo.branches.get_branches())
            for n in branches:
                p = "* " if n == curr else "  "
                node=repo.branches.nodes[n]
                c=f"({node.commit_hash[:7]})" if node.commit_hash else "(v)"
                print(f"{p}{n:<25} {c}")
            if "--list" in args:
                print("\nÁrbol (Preorden):\n" + "\n".join(repo.branches.get_preorder_lines() or ["(vacío)"]))
            return
        opt = args[0]
        b_args = args[1:]
        if opt == "-b":
            if not b_args:
                print("Uso: branch -b <nombre> [padre]")
                return
            n = b_args[0]
            p = b_args[1] if len(b_args) > 1 else repo.current_branch
            try:
                repo.branches.add_branch(n, p)
                print(f"Rama '{n}' creada desde '{p}'.")
                repo.save()
            except ValueError as e:
                print(f"Error: {e}")
        elif opt == "-d":
            if not b_args:
                print("Uso: branch -d <nombre>")
                return
            d = b_args[0]
            if d == repo.current_branch:
                print(f"Error: No puedes eliminar rama actual '{d}'.")
                return
            try:
                repo.branches.delete_branch(d)
                print(f"Rama '{d}' eliminada.")
                repo.save()
            except ValueError as e:
                print(f"Error: {e}")
        else:
            print(f"Opción '{opt}' inválida.")
            print("Uso: branch [--list] | -b <n> [p] | -d <n>")

# --- Comandos de Pull Request (PR) ---
class PRCommand(Command):
     """Comando base para subcomandos PR."""
     def execute(self, vcs, args):
         if not super().execute(vcs, args):
             return
         subs = {'create': PRCreateCommand(), 'list': PRListCommand(), 'status': PRStatusCommand(), 'review': PRReviewCommand(), 'approve': PRApproveCommand(), 'reject': PRRejectCommand(), 'merge': PRMergeCommand(), 'tag': PRTagCommand()}
         if not args:
             print("Subcomandos PR: " + ", ".join(subs.keys()) + "\nUso: pr <subcmd> ...")
             return
         sub, s_args = args[0].lower(), args[1:]
         if sub in subs:
             subs[sub].execute(vcs, s_args)
         else:
             print(f"Subcomando '{sub}' inválido.")
             self.execute(vcs, [])

class PRCreateCommand(Command):
    """Subcomando: pr create <origen> <destino>"""
    def execute(self, vcs, args):
        if len(args) < 2:
            print("Uso: pr create <origen> <destino>")
            return
        repo = vcs.current_repo
        author = "user@example.com"
        repo.pr_queue.create_pr(args[0], args[1], author, repo)

class PRListCommand(Command):
    """Subcomando: pr list"""
    def execute(self, vcs, args):
        repo=vcs.current_repo
        prq=repo.pr_queue
        print("\n--- PRs Pendientes ---")
        if not prq.queue:
            print("(Ninguno)")
        else:
            print("{:<5} {:<12} {:<25} {:<15} {:<15}".format("ID","E","Título","O","D"))
            print("-" * 75)
            for p in prq.queue:
                 print(f"{p['id']:<5} {p['status']:<12} {p['title'][:23]+('..' if len(p['title'])>23 else ''):<25} {p['source']:<15} {p['target']:<15}")
        print("\n--- PRs Cerrados ---")
        if not prq.closed_prs:
            print("(Ninguno)")
        else:
            print("{:<5} {:<12} {:<25} {:<15} {:<15} {:<20}".format("ID","E","Título","O","D","Cerrado"))
            print("-" * 100)
            for p in sorted(prq.closed_prs, key=lambda x: x.get('closed_at',''), reverse=True):
                 print(f"{p['id']:<5} {p['status']:<12} {p['title'][:23]+('..' if len(p['title'])>23 else ''):<25} {p['source']:<15} {p['target']:<15} {p.get('closed_at','N/A'):<20}")

class PRStatusCommand(Command):
     """Subcomando: pr status <pr_id>"""
     def execute(self, vcs, args):
          if not args:
              print("Uso: pr status <id>")
              return
          repo=vcs.current_repo
          try:
              pr_id = int(args[0])
          except ValueError:
              print(f"ID '{args[0]}' inválido.")
              return
          pr = repo.pr_queue.find_pr(pr_id)
          if not pr:
              print(f"PR {pr_id} no encontrado.")
              return
          print(f"\n--- PR #{pr_id} ---")
          for k,v in pr.items():
              if k not in ['comments','commits','modified_files']:
                   print(f"{k.replace('_',' ').title():<12}: {v}")
          comments = pr.get('comments',[])
          print("\nComs:")
          if not comments:
              print("(No)")
          else:
              print("\n".join([f" [{i+1}]({c.get('timestamp','N/A')}) {c.get('author','?')}:{c.get('text','')}" for i,c in enumerate(comments)]))
          print("-"*(len(f"--- PR #{pr_id} ---")+1))

class PRReviewCommand(Command):
    """Subcomando: pr review <pr_id> "comment" """
    def execute(self, vcs, args):
        if len(args) < 2:
            print("Uso: pr review <id> \"<comentario>\"")
            return
        repo=vcs.current_repo
        try:
            pr_id = int(args[0])
        except ValueError:
            print(f"ID '{args[0]}' inválido.")
            return
        pr = repo.pr_queue.find_pr(pr_id)
        if not pr:
            print(f"PR {pr_id} no encontrado.")
            return
        if pr['status'] in ['merged','rejected']:
            print("PR cerrado.")
            return
        cmt = " ".join(args[1:])
        author = "rev@ex.com"
        if repo.pr_queue.add_comment(pr_id, cmt, author):
             if pr['status'] == 'pending':
                 repo.pr_queue.update_status(pr_id, 'in_review')

class PRApproveCommand(Command):
    """Subcomando: pr approve <pr_id>"""
    def execute(self, vcs, args):
        if not args:
            print("Uso: pr approve <id>")
            return
        repo=vcs.current_repo
        try:
            pr_id = int(args[0])
        except ValueError:
            print(f"ID '{args[0]}' inválido.")
            return
        pr = repo.pr_queue.find_pr(pr_id)
        if not pr:
            print(f"PR {pr_id} no encontrado.")
            return
        if pr['status'] in ['approved','merged','rejected']:
            print(f"PR ya {pr['status']}.")
            return
        if repo.pr_queue.update_status(pr_id, 'approved'):
            print(f"PR #{pr_id} aprobado.")

class PRRejectCommand(Command):
    """Subcomando: pr reject <pr_id> ["reason"]"""
    def execute(self, vcs, args):
        if not args:
            print("Uso: pr reject <id> [\"razón\"]")
            return
        repo=vcs.current_repo
        try:
            pr_id = int(args[0])
        except ValueError:
            print(f"ID '{args[0]}' inválido.")
            return
        pr = repo.pr_queue.find_pr(pr_id)
        if not pr:
            print(f"PR {pr_id} no encontrado.")
            return
        if pr['status'] in ['merged','rejected']:
            print(f"PR ya {pr['status']}.")
            return
        reason = " ".join(args[1:]) or "Rechazado"
        author = "rev@ex.com"
        repo.pr_queue.add_comment(pr_id, f"Rechazado: {reason}", author)
        if repo.pr_queue.update_status(pr_id, 'rejected'):
            print(f"PR #{pr_id} rechazado.")

class PRTagCommand(Command):
    """Subcomando: pr tag <pr_id> <tag>"""
    def execute(self, vcs, args):
        if len(args) < 2:
            print("Uso: pr tag <id> <etiqueta>")
            return
        repo=vcs.current_repo
        try:
            pr_id = int(args[0])
        except ValueError:
            print(f"ID '{args[0]}' inválido.")
            return
        tag = args[1]
        if not tag:
            print("Etiqueta vacía.")
            return
        repo.pr_queue.add_tag(pr_id, tag)

# --- Comando Merge (Ahora acepta Origen y Destino) ---
class MergeCommand(Command):
    """
    Comando para fusionar cambios de una rama origen en una rama destino.
    Uso: merge <rama_origen> <rama_destino>
    Implementa simulación básica de fast-forward y merge de 3 vías.
    NOTA: No maneja conflictos de contenido. Actualiza la rama destino.
    """
    def execute(self, vcs, args):
        """Args: [source_branch, target_branch]"""
        if not super().execute(vcs, args): # Validar repo activo
             return

        repo = vcs.current_repo # Necesitamos repo para acceder a ramas

        # --- Validar DOS argumentos ---
        if len(args) != 2:
            print("Error: Se requieren ramas origen y destino.")
            print("Uso: merge <rama_origen> <rama_destino>")
            return

        source_branch = args[0]
        target_branch = args[1] # Tomar destino del segundo argumento

        # --- Validación de ramas ---
        if source_branch not in repo.branches.nodes:
            print(f"Error: La rama origen '{source_branch}' no existe.")
            return
        if target_branch not in repo.branches.nodes:
            print(f"Error: La rama destino '{target_branch}' no existe.")
            return
        if source_branch == target_branch:
            print("Error: No puedes fusionar una rama consigo misma.")
            return

        # --- Lógica de Merge (Actualiza target_branch) ---
        print(f"Iniciando fusión simulada de '{source_branch}' en '{target_branch}'...")
        source_hash = repo.branches.get_commit_hash(source_branch)
        target_hash = repo.branches.get_commit_hash(target_branch) # Hash de la rama destino especificada

        if not source_hash:
            print(f"Advertencia: Rama origen '{source_branch}' sin commits. Nada que fusionar.")
            return

        # Comprobación Fast-Forward (destino es ancestro de origen)
        is_fast_forward = False
        temp_h = source_hash
        visited = set()
        while temp_h and temp_h not in visited and temp_h != target_hash:
            visited.add(temp_h)
            commit = repo.get_commit(temp_h)
            if not commit: break # Error en historial
            parent = commit.parent_hash
            temp_h = parent[0] if isinstance(parent, list) and parent else parent
        if temp_h == target_hash:
            is_fast_forward = True

        if is_fast_forward:
            print("Fusión 'Fast-forward' posible.")
            # Actualizar el puntero de la rama DESTINO especificada
            repo.branches.update_branch_commit(target_branch, source_hash)
            print(f"Rama '{target_branch}' actualizada para apuntar a commit {source_hash[:7]}.")
            repo.save()
            return

        # Merge de 3 vías (Simulado)
        print("Realizando merge de 3 vías (simulado)...")
        if not target_hash: # Si destino no tiene commits, es como FF
             print(f"Adv: Rama destino '{target_branch}' sin commits. Actualizando como fast-forward.")
             repo.branches.update_branch_commit(target_branch, source_hash)
             print(f"Rama '{target_branch}' actualizada a {source_hash[:7]}.")
             repo.save()
             return

        parents = [target_hash, source_hash] # Padres: [destino, origen]
        msg = f"Merge branch '{source_branch}' into {target_branch}"
        author = "merger@ex.com"
        # El commit de merge se crea EN la rama destino
        merge_commit = Commit(msg, author, parents, target_branch)

        # Simular archivos (unión simple)
        s_commit = repo.get_commit(source_hash)
        t_commit = repo.get_commit(target_hash)
        files = set()
        if s_commit and s_commit.files: files.update(s_commit.files)
        if t_commit and t_commit.files: files.update(t_commit.files)
        merge_commit.files = sorted(list(files))

        # Añadir commit (actualiza puntero de target_branch) y guardar
        repo.add_commit(merge_commit)
        repo.save()
        print(f"Merge completado en '{target_branch}'. Commit: {merge_commit.hash[:7]}. Archivos(sim): {', '.join(merge_commit.files)}")

class PRMergeCommand(Command):
     """Subcomando para intentar fusionar un PR aprobado."""
     def execute(self, vcs, args):
          """Args: [pr_id]"""
          if not args:
              print("Uso: pr merge <id>")
              return
          repo=vcs.current_repo
          try:
              pr_id = int(args[0])
          except ValueError:
              print(f"ID '{args[0]}' inválido.")
              return
          pr = repo.pr_queue.find_pr(pr_id)
          if not pr:
              print(f"PR {pr_id} no encontrado.")
              return
          if pr['status'] != 'approved':
              print(f"PR #{pr_id} no aprobado ({pr['status']}).")
              return
          source = pr['source']
          target = pr['target']
          print(f"Fusionando PR #{pr_id} ('{source}' -> '{target}')...")
          # --- Usar el nuevo MergeCommand con origen y destino ---
          merge_cmd = MergeCommand()
          # Ejecutar merge especificando origen y destino del PR
          # Guardamos la rama actual por si MergeCommand la cambiara (aunque ahora no debería)
          current_branch_before = repo.current_branch
          merge_cmd.execute(vcs, [source, target])
          # Restaurar rama actual si cambió (por si acaso)
          if repo.current_branch != current_branch_before:
              print(f"(Restaurando rama activa a '{current_branch_before}')")
              checkout_cmd = CheckoutCommand()
              checkout_cmd.execute(vcs, [current_branch_before])

          # --- Verificación heurística de éxito ---
          last_commit = repo.get_commit(repo.branches.get_commit_hash(target))
          merge_ok = False
          if last_commit and isinstance(last_commit.parent_hash, list):
              source_hash = repo.branches.get_commit_hash(source)
              if source_hash in last_commit.parent_hash:
                  merge_ok = True
          if last_commit and f"Merge branch '{source}'" in last_commit.message:
              merge_ok = True

          if merge_ok:
              print(f"Merge de PR #{pr_id} completado.")
              repo.pr_queue.update_status(pr_id, 'merged')
          else:
              print(f"Merge de PR #{pr_id} falló o no creó commit esperado.")

# --- Comandos de Roles (Role) ---
class RoleCommand(Command):
    """Comando base para subcomandos de gestión de Roles/Permisos."""
    def execute(self, vcs, args):
        """Args: [subcommand [subcommand_args...]]"""
        if not super().execute(vcs, args):
            return # No hay repo activo
        subs = {'add': RoleAddCommand(), 'update': RoleUpdateCommand(), 'remove': RoleRemoveCommand(), 'show': RoleShowCommand(), 'list': RoleListCommand(), 'check': RoleCheckCommand()}
        if not args:
             print("Subcomandos Role disponibles: " + ", ".join(subs.keys()))
             print(f"Roles válidos: {', '.join(VALID_ROLES)}")
             print("Uso: role <subcmd> ...");
             return
        sub, s_args = args[0].lower(), args[1:]
        if sub in subs:
            success = subs[sub].execute(vcs, s_args)
            if success is not False: # Guardar si el comando no falló explícitamente
                vcs.current_repo.save()
        else:
            print(f"Subcomando '{sub}' inválido.")
            self.execute(vcs, []) # Muestra ayuda

class RoleAddCommand(Command):
    """Subcomando: role add <email> <rol> [permiso1,permiso2,...]"""
    def execute(self, vcs, args):
        if len(args) < 2:
            print("Uso: role add <email> <rol> [permisos...]")
            return False # Indica fallo para no guardar
        repo = vcs.current_repo
        email = args[0]
        role = args[1].lower()
        req_perms = set()
        if len(args) > 2:
            req_perms = {p.strip() for p in " ".join(args[2:]).replace(',', ' ').split() if p.strip()}
        if role not in VALID_ROLES:
            print(f"Err: Rol '{role}' inválido. Roles: {', '.join(VALID_ROLES)}")
            return False
        allowed = ROLE_PERMISSIONS[role]
        if not req_perms.issubset(allowed):
            invalid = req_perms - allowed
            print(f"Err: Permisos inválidos p/rol '{role}': {', '.join(invalid)}\nPermitidos: {', '.join(sorted(list(allowed))) or 'Ninguno'}")
            return False
        repo.roles.insert(email, role, req_perms)
        print(f"Rol '{role}' asignado a '{email}'. Perms: {', '.join(sorted(list(req_perms))) or 'Ninguno'}")
        return True # Indica éxito

class RoleUpdateCommand(Command):
    """Subcomando: role update <email> <nuevo_rol> [permisos_a_añadir...]"""
    def execute(self, vcs, args):
        if len(args) < 2:
            print("Uso: role update <email> <n_rol> [perms_a_añadir...]")
            return False
        repo=vcs.current_repo
        email = args[0]
        new_role = args[1].lower()
        add_perms = set()
        if len(args) > 2:
            add_perms = {p.strip() for p in " ".join(args[2:]).replace(',', ' ').split() if p.strip()}
        if not repo.roles._find_node(email):
            print(f"Err: Usuario '{email}' no encontrado.")
            return False
        if new_role not in VALID_ROLES:
            print(f"Err: Rol '{new_role}' inválido. Roles: {', '.join(VALID_ROLES)}")
            return False
        allowed = ROLE_PERMISSIONS[new_role]
        if not add_perms.issubset(allowed):
            invalid = add_perms - allowed
            print(f"Err: Permisos inválidos p/rol '{new_role}': {', '.join(invalid)}\nPermitidos: {', '.join(sorted(list(allowed))) or 'Ninguno'}")
            return False
        repo.roles.update_role(email, new_role, add_perms)
        print(f"Rol '{email}' -> '{new_role}'. Perms añadidos: {', '.join(sorted(list(add_perms))) or 'Ninguno'}")
        return True

class RoleRemoveCommand(Command):
    """Subcomando: role remove <email>"""
    def execute(self, vcs, args):
        if not args:
            print("Uso: role remove <email>")
            return False
        repo = vcs.current_repo
        email = args[0]
        if not repo.roles._find_node(email):
            print(f"Usuario '{email}' no encontrado.")
            return False
        repo.roles.remove_role(email)
        print(f"Rol eliminado para '{email}'.")
        return True

class RoleShowCommand(Command):
    """Subcomando: role show <email>"""
    def execute(self, vcs, args):
        if not args:
            print("Uso: role show <email>")
            return False
        repo = vcs.current_repo
        email = args[0]
        node = repo.roles._find_node(email)
        if not node:
            print(f"Usuario '{email}' no encontrado.")
            return False
        print(f"\n--- Rol Info: {email} ---")
        print(f"Rol: {node.role}")
        perms = node.permissions.get_all_keys()
        print(f"Permisos: {', '.join(sorted(perms)) or 'Ninguno'}")
        print("-"*(len(f"--- Rol Info: {email} ---")+1))
        return True

class RoleListCommand(Command):
    """Subcomando: role list"""
    def execute(self, vcs, args):
        repo = vcs.current_repo
        roles_info = repo.roles.get_all_roles_info()
        if not roles_info:
            print("No hay roles.")
            return True # No es un error, simplemente no hay nada que listar
        print("\n--- Roles y Permisos (Orden Email) ---")
        print("{:<30} {:<15} {:<45}".format("Email","Rol","Permisos"))
        print("-" * 95)
        for i in roles_info:
             print(f"{i['email']:<30} {i['role']:<15} {(', '.join(sorted(i['permissions'])) or 'Ninguno')[:43]:<45}")
        print("-" * 95)
        return True

class RoleCheckCommand(Command):
    """Subcomando: role check <email> <permiso>"""
    def execute(self, vcs, args):
        if len(args) != 2:
            print("Uso: role check <email> <permiso>")
            return False
        repo = vcs.current_repo
        email = args[0]
        perm = args[1]
        if repo.roles.has_permission(email, perm):
            print(f"Sí, '{email}' tiene permiso '{perm}'.")
        else:
            if repo.roles._find_node(email):
                print(f"No, '{email}' NO tiene permiso '{perm}'.")
            else:
                print(f"Usuario '{email}' no existe.")
        return True

# --- Comandos de Colaboradores ---
class ContributorsListCommand(Command):
    """Comando: contributors"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        repo = vcs.current_repo
        contribs = repo.collaborators.get_all_contributors_sorted()
        if not contribs:
            print("No hay colaboradores.")
            return
        print("\n--- Colaboradores (Orden Alfabético) ---")
        print("{:<30} {:<20}".format("Nombre", "Rol"))
        print("-" * 55)
        for n, r in contribs:
             print(f"{n:<30} {r:<20}")
        print("-" * 55)

class ContributorAddCommand(Command):
    """Comando: add-contributor <name>"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        if not args:
            print("Uso: add-contributor <nombre>")
            return
        repo = vcs.current_repo
        name = args[0]
        role = "Contributor"
        if repo.collaborators.insert(name, role):
            print(f"Colaborador '{name}' añadido (Rol: {role}).")
        else:
            print(f"Rol de '{name}' actualizado a '{role}'.")
        repo.save()

class ContributorRemoveCommand(Command):
    """Comando: remove-contributor <name>"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        if not args:
            print("Uso: remove-contributor <nombre>")
            return
        repo = vcs.current_repo
        name = args[0]
        if repo.collaborators.find(name):
            repo.collaborators.remove(name)
            print(f"Colaborador '{name}' eliminado.")
            repo.save()
        else:
            print(f"Error: Colaborador '{name}' no encontrado.")

class ContributorFindCommand(Command):
    """Comando: find-contributor <name>"""
    def execute(self, vcs, args):
        if not super().execute(vcs, args):
            return
        if not args:
            print("Uso: find-contributor <nombre>")
            return
        repo = vcs.current_repo
        name = args[0]
        node = repo.collaborators.find(name)
        if node:
            print(f"Encontrado: Nombre='{node.name}', Rol='{node.role}'")
        else:
            print(f"Colaborador '{name}' no encontrado.")

# --- Comando de Ayuda ---
class HelpCommand(Command):
     """Comando: help"""
     def execute(self, vcs, args):
          print("\n--- SCVS Ayuda ---")
          print("Uso General: <comando> [argumentos...]")
          print("\nRepositorio y Archivos:")
          print("  init <repo>        : Inicializa/Carga repositorio.")
          print("  add <arch...>      : Añade archivos al staging.")
          print("  commit <\"msg\">   : Guarda cambios del staging.")
          print("  status             : Muestra estado actual.")
          print("  log                : Muestra historial.")
          print("\nRamas y Fusión:")
          print("  branch [--list]    : Lista ramas (y árbol con --list).")
          print("  branch -b <n> [p]  : Crea rama <n> desde [p] (o actual).")
          print("  branch -d <rama>   : Elimina rama.")
          print("  checkout <rama>    : Cambia a rama.")
          print("  merge <origen> <destino> : Fusiona rama origen en destino (simulado).") # <-- ACTUALIZADO
          print("\nStaging Area:")
          print("  stage list         : Muestra archivos en staging.")
          print("  stage toggle <arch>: (Des)Selecciona archivo.")
          print("  stage clear / clear_selected : Limpia staging.")
          print("\nPull Requests (Simulado):")
          print("  pr list            : Lista PRs.")
          print("  pr status <id>     : Muestra detalles de un PR.")
          print("  pr create <o> <d>  : Crea PR de rama <o> a <d>.")
          print("  pr review <id> \"c\" : Añade comentario a PR.")
          print("  pr approve <id>    : Aprueba PR.")
          print("  pr reject <id> [r] : Rechaza PR (con razón opcional).")
          print("  pr merge <id>      : Fusiona PR aprobado (usa 'merge' interno).")
          print("  pr tag <id> <tag>  : Añade etiqueta a PR.")
          print("\nRoles y Permisos:")
          print("  role list          : Lista usuarios y roles.")
          print("  role show <email>  : Muestra detalles de un usuario.")
          print("  role add <e> <r> [p]: Añade usuario con rol y permisos (validados).")
          print("  role update <e> <nr> [p]: Actualiza rol y añade permisos (validados).")
          print("  role remove <email>: Elimina usuario.")
          print("  role check <e> <p> : Verifica si usuario tiene permiso.")
          print(f"  (Roles válidos: {', '.join(VALID_ROLES)})")
          print("\nColaboradores (Simplificado):")
          print("  contributors       : Lista colaboradores (ordenado).")
          print("  add-contributor <n>: Añade colaborador (rol 'Contributor').")
          print("  remove-contributor <n>: Elimina colaborador.")
          print("  find-contributor <n>: Busca colaborador.")
          print("\nOtros:")
          print("  help               : Muestra esta ayuda.")
          print("  exit               : Sale del programa.")

# Manejador de comandos
class CommandHandler:
    """Procesa entrada y delega a objetos Command."""
    def __init__(self, vcs):
        """Inicializa con VCS y registra comandos."""
        self.vcs = vcs
        self.commands = {
            'init': InitCommand(), 'add': AddCommand(), 'commit': CommitCommand(), 'status': StatusCommand(),
            'log': LogCommand(), 'checkout': CheckoutCommand(), 'stage': StageCommand(), 'branch': BranchCommand(),
            'merge': MergeCommand(), 'help': HelpCommand(), 'pr': PRCommand(), 'role': RoleCommand(),
            'contributors': ContributorsListCommand(), 'add-contributor': ContributorAddCommand(),
            'remove-contributor': ContributorRemoveCommand(), 'find-contributor': ContributorFindCommand(),
        }
    def process_command(self, command_input):
        """Parsea y ejecuta el comando."""
        parts = command_input.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]
        if cmd in self.commands:
            self.commands[cmd].execute(self.vcs, args)
        else:
            print(f"Error: Comando '{cmd}' no reconocido. Usa 'help'.")

# Función principal
def main():
    """Punto de entrada y bucle principal de la CLI."""
    vcs = VersionControlSystem()
    handler = CommandHandler(vcs)
    print("Bienvenido a SCVS (Simulador Control de Versiones)")
    print("Escribe 'help' para ayuda.")
    while True:
        repo_name = f" [{vcs.current_repo.name}]" if vcs.current_repo else ""
        branch_name = f" ({vcs.current_repo.current_branch})" if vcs.current_repo else ""
        prompt = f"scvs{repo_name}{branch_name}> "
        try:
            cmd_in = input(prompt)
            print() # <-- Salto de línea
            if cmd_in.lower() == 'exit':
                print("Saliendo...")
                break
            handler.process_command(cmd_in)
        except EOFError:
            print("\nSaliendo (EOF)...")
            break
        except KeyboardInterrupt:
            print("\nInterrumpido. Usa 'exit' para salir.")
        except Exception as e:
            print("\n¡ERROR INESPERADO!")
            print(f"T:{type(e).__name__} M:{e}")
            print("---TB---")
            traceback.print_exc()
            print("--------")

if __name__ == "__main__":
    main()