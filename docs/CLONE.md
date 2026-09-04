# Clonar y preparar proyectos existentes

`wslaragon site clone` trae un repositorio a `~/web`, detecta su tecnología y
crea el dominio `.test`, certificado HTTPS, virtual host Nginx, base de datos y
proxy necesarios. Las tareas que modifican el proyecto son opcionales.

## Modo guiado y detección

```bash
wslaragon site clone
```

El asistente solicita URL Git, dominio y stack; después ofrece preparar `.env`,
instalar, compilar, iniciar PM2 y migrar. La detección busca, en orden:
`artisan` (Laravel), WordPress, Astro, SvelteKit, Vite, `package.json` (Node),
archivos PHP y finalmente contenido estático. Por eso Laravel con Vite continúa
siendo Laravel. Puede forzarse con `--stack laravel`, `--stack node`, etc.

## Opciones

| Opción | Acción |
| --- | --- |
| `--env` | Copia `.env.example` solo si `.env` no existe; configura el Laravel recién creado. |
| `--install` | Ejecuta `composer install` y/o `pnpm install` según los archivos encontrados. |
| `--build` | Ejecuta `pnpm build` para Vite, Astro, SvelteKit o Laravel con frontend. |
| `--start` | Inicia PM2 solamente para un sitio con proxy, usando `app.js`, `pnpm start` o `main.py`. |
| `--import-db archivo.sql` | Importa un respaldo en la base MySQL asignada al sitio. |
| `--migrate` | Ejecuta `php artisan migrate`; nunca ocurre sin solicitarlo. |
| `--branch nombre` | Clona únicamente la rama o etiqueta indicada. |
| `--no-mysql` | Evita la base que Laravel y WordPress crean por defecto. |

Un `.env` existente se conserva completamente. Si Composer, pnpm, el build,
PM2 o una migración fallan, el repositorio y el sitio se conservan para poder
corregir la tarea pendiente.

## Ejemplos

```bash
# Laravel con base nueva y assets
wslaragon site clone URL app --stack laravel --env --install --build --migrate

# Laravel restaurado desde SQL, sin migraciones
wslaragon site clone URL app --stack laravel --database app_local \
  --env --install --build --import-db ~/backups/app.sql

# Node/SvelteKit mediante Nginx y PM2
wslaragon site clone URL frontend --install --build --start

# Sitio estático o PHP sin preparación adicional
wslaragon site clone URL landing
```

## Verificación y prueba futura

```bash
wslaragon site list
wslaragon site fix-permissions app --check
wslaragon node list
wslaragon status
```

Abre `https://<nombre>.test`. Las credenciales externas, VPN, seeders y demás
pasos propios del repositorio siguen siendo responsabilidad del proyecto.

Cuando haya un repositorio disponible, puede probarse primero con un nombre y
base temporales, sin migraciones:

```bash
wslaragon site clone URL prueba-clone --env --install --build
wslaragon site delete prueba-clone --remove-database
```

