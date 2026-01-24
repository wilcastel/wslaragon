# 🔒 SSL y Base de Datos

Esta sección detalla los aspectos más importantes para que tus sitios funcionen con el candado verde y cómo se gestiona la base de datos MariaDB.

## 1. Confianza SSL en Windows (Candado Verde)

WSLaragon usa `mkcert` para generar certificados. Para que tu navegador en Windows confíe en ellos, debes seguir estos pasos:

### Paso A: Obtener el Certificado Raíz
Desde tu terminal WSL, copia el certificado raíz a tus Descargas de Windows:

```bash
cp $(mkcert -CAROOT)/rootCA.pem /mnt/c/Users/TuUsuario/Downloads/cert_wslaragon.crt
```
*(Reemplaza `TuUsuario` por tu nombre de usuario en Windows).*

### Paso B: Importar en Windows
1.  Presiona **Windows + R** y escribe `certlm.msc`.
2.  Busca la carpeta **Entidades de certificación raíz de confianza** -> **Certificados**.
3.  Borra cualquier certificado antiguo que diga `mkcert` o `Laragon`.
4.  Haz clic derecho en la carpeta -> **Todas las tareas** -> **Importar...** y selecciona el archivo `.crt` de tus Descargas.
5.  **Reinicia el navegador** completamente.

## 2. MariaDB (MySQL)

### Configuración del Usuario Root
WSLaragon usa el usuario `root` para crear bases de datos. Asegúrate de que el método de autenticación sea mediante contraseña y no `unix_socket`.

Para sincronizar la contraseña con tu `.env`:
```bash
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'tu_contraseña_del_env'; FLUSH PRIVILEGES;"
```

### Bases de Datos de Sitios
Cuando creas un sitio con `--mysql`, WSLaragon:
1.  Crea una base de datos con el nombre `{site_name}_db`.
2.  Asegura que el juego de caracteres sea `utf8mb4_unicode_ci`.

---

> [!TIP]
> Si tienes problemas de conexión, verifica que el servicio esté corriendo con `wslaragon service status`.
