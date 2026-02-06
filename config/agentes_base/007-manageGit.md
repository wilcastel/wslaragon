---
name: git_staging_workflow
description: Flujo de trabajo estandarizado para desarrollar features, probarlas en servidor remoto (rama trycode) e integrarlas en develop.
---

# Git Staging & Deployment Bundle

Este skill define el protocolo estricto para gestionar cambios en el código, asegurando que todo sea probado en el entorno remoto (`trycode`) antes de llegar a la rama principal (`develop`).

## 1. Inicio de Desarrollo (Feature Start)
Siempre que se inicie una nueva funcionalidad o corrección:
1. Asegurar que estamos en `develop` actualizado.
2. Crear una rama descriptiva (`feature/nombre-tarea` o `fix/nombre-bug`).

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-descriptivo
```

## 2. Ciclo de Prueba Remota (Staging)
Cuando el código esté listo para probarse en el servidor remoto (pero no necesariamente listo para producción):
**NO mezclar en develop todavía.** Usaremos la rama `trycode`.

1. Guardar cambios en la rama actual (commit).
2. Cambiar a `trycode` y actualizarla.
3. Traer los cambios de la feature.
4. Subir `trycode` para que el servidor remoto pueda descargarla.

```bash
# Estando en feature/nombre-descriptivo
git add .
git commit -m "feat: descripción de cambios"

# Pasando a Staging
git checkout trycode
git pull origin trycode
git merge feature/nombre-descriptivo --no-edit
git push origin trycode
```
*Notificar al usuario: "Rama trycode actualizada. Puedes hacer pull en el servidor de pruebas."*

## 3. Corrección de Errores (Fixing)
Si la prueba en `trycode` falla:
1. **Volver a la rama feature** (`git checkout feature/...`).
2. Corregir el error.
3. Repetir el paso 2 (Ciclo de Prueba Remota).
   *Nunca hacer commits directos en trycode a menos que sea una emergencia extrema.*

## 4. Finalización e Integración (Release)
Solo cuando la funcionalidad está verificada al 100% en el servidor de pruebas:
1. Volver a `develop`.
2. Mezclar la rama `feature` (o `trycode` si se desea conservar el historial de pruebas, aunque se prefiere feature limpia).
3. Subir `develop`.
4. Eliminar la rama feature local.

```bash
git checkout develop
git pull origin develop
git merge feature/nombre-descriptivo
git push origin develop

# Limpieza opcional
git branch -d feature/nombre-descriptivo
```

## Comandos Rápidos (Cheatsheet)
- **Probar en remoto**: `git checkout trycode && git merge feature/actual && git push origin trycode && git checkout feature/actual`
- **Publicar oficial**: `git checkout develop && git merge feature/actual && git push origin develop`
