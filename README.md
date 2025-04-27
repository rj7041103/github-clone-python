# Guía de Usuario del Programa de Control de Versiones

Esta guía proporciona una referencia completa de los comandos disponibles en el programa para gestionar repositorios, ramas, staging y commits.

---

## **Comandos Básicos**

### **Inicializar un Repositorio**
```bash
init proyect 
```
Repositorio proyect inicializado.

### **Inicializar una nueva Rama**
```bash
branch -b nuevaRama
```
Rama nuevaRama creada

### **Cambio a la Rama Creada**
```bash
checkout nuevaRama
```
Cambiado a rama 'nuevaRama'

### **Agregar archivos**
```bash
add test.js
```
Archivos añadidos: test.js

### **Comando para ejecutar commits**
```bash
commit -m "test prueba"
```
Commit creado: 0910430cd2

### **Comando para crear un Pr**
```bash
pr create nuevaRama main
```
PR#1 creado: nuevaRama -> main

### **Comando para hacer la revision del Pr**
```bash
pr review 1 "Verificar compatibilidad"
```
PR#1 en revisión. Comentario añadido.

### **Comando para saber el status del Pr**
```bash
pr status
```

Estado de Pull Requests:
PR#1 [en_revision] nuevaRama->main
Autor: user@example.com | Creado: 2025-03-23 20:37:09
Etiquetas:
--------------------------------------------------

### **Comando para poner un tag de seguimiento al Pr**
```bash
pr tag 1 "critico"
```
Etiqueta '"critico"' añadida al PR#1

### **Comando para aprobar el Pr**
```bash
ppr approve 1
```
PR#1 aprobado y fusionado en main

### **Cambiamos a main**
```bash
checkout main
```
Cambiado a rama 'main'

### **Comando para ver el historial de Commits **
```bash
log
```
Historial de commits:
Commit: 0910430cd2
Autor: user@example.com
Fecha: 2025-03-23 20:36:48
Rama: nuevaRama
Mensaje: -m
Archivos: test.js
Padre: None
--------------------------------------------------
### **Camando para listar toda la lista de pr que hay en la cola**
```bash
pr list
```
Cola de Pull Requests:
ID    Estado       Origen->Destino Autor      Creado               Etiquetas

PRs cerrados:
1     merged       nuevaRama->main user@example.com 2025-03-23 20:39:00  "critico"

### **Intentamos aprobar una pr con un numero inexistente**
```bash
pr approve 99
```
Error: PR#99 no encontrado

### **Intentamos rechazar el pr con el numero 1**
```bash
pr reject 1
```
### **Comprobamos que no se pueda hacer pr a ramas inexistentes**
```bash
pr create no-existo main
```
Error: Rama no-existo no existe

### **Comprobamos que no haya algun elemento en la cola que siga**
```bash
pr next
```
No hay PRs pendientes en la cola

### **Limpiamos toda la cola de pr**
```bash
pr clear
```
Cola de PRs limpiada

### **Listamos los pr que se han hecho de las ramas**
```bash
pr list
```
Cola de Pull Requests:
ID    Estado       Origen->Destino Autor      Creado               Etiquetas

PRs cerrados:
1     merged       nuevaRama->main user@example.com 2025-03-23 20:39:00  "critico"

> branch -b testRama
Rama testRama creada

> checkout testRama
Cambiado a rama 'testRama'

> add text2.txt text3.txt
Archivos añadidos: text2.txt, text3.txt

### **Comando para listar todos los archivos que estan en la pila cuando se ejecuta el comando de add**
```bash
stage list
```
> stage list
[ ] [M] test.js
[ ] [A] text2.txt
[ ] [A] text3.txt
### **Comando para seleccionar aquellos archivos que se quieren subir al repoitorio**
```bash
stage toggle test.js
```
Archivo test.js actualizado

### **Comprobamos aquel archivo que elejimos que se haya marcado**
```bash
stage list
```
[X] [M] test.js
[ ] [A] text2.txt
[ ] [A] text3.txt

### **Repetimos el proceso con otro de los archivos**
```bash
stage toggle text3.txt
```
Archivo text3.txt actualizado

### **Ejecutamos el comando log para ver todo el historial**
```bash
log
```
Historial de commits:
Commit: 0910430cd2
Autor: user@example.com
Fecha: 2025-03-23 20:50:28
Rama: testRama
Mensaje: -m
Archivos: test.js, text3.txt
Padre: 0910430cd2
--------------------------------------------------
Commit: 0910430cd2
Autor: user@example.com
Fecha: 2025-03-23 20:36:48
Rama: nuevaRama
Mensaje: -m
Archivos: test.js
Padre: None
--------------------------------------------------

### Nueva parte del Programa de simulacion de Github
### **Inicializar un Repositorio**
```bash
init proyect 
```
### **Crea una nueva rama**
```bash
branch -b newRama
```
### **Elimina una nueva rama**
```bash
branch -d newRama
```
### **Muestra la lista de las ramas qeu hay**
```bash
branch --list
```
### **Cambia a una rama previamente creada**
```bash
#Se ejecuta antes branch -b newRama2
checkout newRama2
```
### **Une los archivos que se cargan de una rama de origen a otra de destino**
```bash
merge newRama newRama2
```
### **Muestra la lista de colaboradores ordenada alfabéticamente**
```bash
contributors
```
### **Agrega un nuevo colaborador en la estructura en 
el repositorio**
```bash
add-contributor Pedro
```
### **Elimina al colaborar con todos sus permisos**
```bash
remove-contributor Pedro
```
### **Encuentra a un colaborador dentro del repositorio**
```bash
find-contributor Pedro
```
### **Agrega los roles a correos de usuarios dentro del repositorio**
```bash
role add user1@gmail.com Admin push pull
```
### **Actualiza los roles y los permisos de la acciones que puede hacer un usuario dentro del repositorio**
```bash
role update user1@gmail.com Admin merge
```
### **Verifica los permisos de accion que tiene un usuario dentro del repositorio**
```bash
role check user1@gmail.com pull
```
### **Elimina de la lista al usuario con permisos de acciones que porte el email escrito **
```bash
role remove user1@gmail.com 
```
### **Muestra el rol y los grados de permisos de acciones que puede hacer en el repositorio**
```bash
role show user1@gmail.com 
```
### **Muestra toda la lista de usuarios con permisos de accion dentro del repositorio**
```bash
role list
```
